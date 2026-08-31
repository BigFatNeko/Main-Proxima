#!/usr/bin/env python3
"""
===============================================================================
PROXIMA BRIEFING — ORCHESTRATORE PIPELINE COMPLETA (Claude Code)
===============================================================================

Pipeline end-to-end del briefing mattutino, esecuzione daily via cron.
ZERO touch human. L'utente apre il browser e trova il briefing già pronto.

FLOW:
    1. screener.py       → JSON candidati pre-filtrati MVF v3.0
    2. legge portafogli locali, 70-azioni-immediate.md, briefing storici
    3. yfinance fetch market snapshot real-time
    4. chiama API Claude Opus 4.8 con adaptive thinking + prompt caching
    5. renderizza HTML newspaper-style via Jinja2
    6. apre nel browser + notifica Telegram (opzionale)

USO:
    python briefing_pipeline.py --user vale
    python briefing_pipeline.py --user alex --mode weekend
    python briefing_pipeline.py --user vale --dry-run        # no API call
    python briefing_pipeline.py --user alex --skip-screener  # solo Claude

CONFIG (env variables):
    ANTHROPIC_API_KEY          obbligatoria (eccetto --dry-run)
    BRIEFING_PORTFOLIO_DIR     default: ~/proxima/portafogli
    BRIEFING_OUTPUT_DIR        default: ~/proxima/briefings
    BRIEFING_TODO_FILE         default: ~/proxima/launch-strategy-180k/70-azioni-immediate.md
    TELEGRAM_BOT_TOKEN         opzionale
    TELEGRAM_CHAT_ID           opzionale
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
import webbrowser
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime as _parse_rfc2822
from pathlib import Path
from typing import Optional

try:
    import requests as _requests
except ImportError:
    _requests = None  # type: ignore

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger("briefing_pipeline")


# =============================================================================
# CONFIG
# =============================================================================

SCRIPT_DIR = Path(__file__).parent.absolute()

DEFAULT_PORTFOLIO_DIR = Path(os.environ.get(
    "BRIEFING_PORTFOLIO_DIR", "~/proxima/portafogli")).expanduser()
DEFAULT_OUTPUT_DIR = Path(os.environ.get(
    "BRIEFING_OUTPUT_DIR", "~/proxima/briefings")).expanduser()
DEFAULT_TODO_FILE = Path(os.environ.get(
    "BRIEFING_TODO_FILE",
    "~/proxima/launch-strategy-180k/70-azioni-immediate.md")).expanduser()

SCREENER_OUTPUT_DIR = SCRIPT_DIR / "data" / "screener_results"
SYSTEM_PROMPT_PATH = SCRIPT_DIR / "system_prompt.md"
TEMPLATE_PATH = SCRIPT_DIR / "newspaper_template.html"

CLAUDE_MODEL = "claude-opus-4-6"
CLAUDE_MAX_TOKENS = 24000


# =============================================================================
# STEP 1 — SCREENER
# =============================================================================

def run_screener(region="GLOBAL", strategy="all") -> Optional[Path]:
    """Esegue screener.py come subprocess e ritorna il path del JSON output."""
    date_tag = datetime.now().strftime("%Y-%m-%d")
    json_path = SCREENER_OUTPUT_DIR / f"screener_{date_tag}.json"

    # Cache giornaliera: se il JSON di oggi esiste già, riusalo
    if json_path.exists():
        log.info("Step 1/6: screener cache hit (%s), skip.", json_path.name)
        return json_path

    log.info("Step 1/6: lancio screener MVF v3.0 (region=%s, strategy=%s)...", region, strategy)
    cmd = [
        sys.executable, str(SCRIPT_DIR / "screener.py"),
        "--region", region, "--strategy", strategy,
        "--top", "500",            # MVF v3.0 completa su top 500
        "--top-speculative", "30",
        "--top-special", "20",
        # universe: pre-filtri TV (PE 0-80, vol>10k) × 50 righe/mercato → cap 600
        # Mantiene yfinance sotto la soglia di rate-limit (~600 req Phase 1)
        "--limit-per-market", "50",
        "--universe-cap", "600",
        "--output", str(SCREENER_OUTPUT_DIR),
    ]
    try:
        # NON cattura output: i log dello screener vanno direttamente
        # su stdout/stderr del processo padre → visibili in GitHub Actions.
        subprocess.run(cmd, check=True, timeout=7200)
    except subprocess.TimeoutExpired:
        log.error("Screener timeout (>2h).")
        return None
    except subprocess.CalledProcessError as e:
        log.error("Screener fallito (exit=%s)", e.returncode)
        return None
    if not json_path.exists():
        log.warning("Output screener non trovato.")
        return None
    log.info("Screener OK: %s", json_path)
    return json_path


# =============================================================================
# STEP 2 — LOAD LOCAL CONTEXT
# =============================================================================

# Users whose briefing narrative uses feminine Italian; all others default to maschile.
_FEMININE_USERS: frozenset[str] = frozenset()


def load_portfolio(user: str) -> dict:
    """Carica portafoglio utente da CSV locale."""
    gender = "femminile" if user.lower() in _FEMININE_USERS else "maschile"
    csv_path = DEFAULT_PORTFOLIO_DIR / f"{user.lower()}.csv"
    if not csv_path.exists():
        log.warning("Portfolio %s non trovato in %s", user, csv_path)
        return {"user": user, "positions": [], "cash": 0, "pac_monthly": 0, "gender": gender}
    import pandas as pd
    df = pd.read_csv(csv_path, comment="#")
    df = df.dropna(subset=["ticker"])
    positions, cash, pac = [], 0, 0
    for _, row in df.iterrows():
        ticker = str(row.get("ticker", "")).strip()
        if not ticker:
            continue
        shares = float(row.get("shares", 0) or 0)
        if ticker == "CASH":
            cash += shares
        elif ticker == "PAC":
            pac += shares
        else:
            positions.append({
                "ticker": ticker, "shares": shares,
                "currency": str(row.get("currency", "EUR")).strip(),
                "notes": str(row.get("notes", "")).strip() if "notes" in row else "",
            })
    return {"user": user, "positions": positions, "cash": cash, "pac_monthly": pac, "gender": gender}


def enrich_portfolio_prices(user_data: dict) -> dict:
    """Aggiunge prezzi live yfinance alle posizioni del portafoglio.

    Essenziale affinché Claude usi prezzi corretti invece della propria
    knowledge base (che può essere stantia di settimane o mesi).
    Parallelo con ThreadPoolExecutor — ~1-2s totali invece di 10-15s sequenziali.
    """
    try:
        import yfinance as yf
    except ImportError:
        log.warning("yfinance non disponibile: prezzi portafoglio non arricchiti")
        return user_data
    positions = user_data.get("positions", [])
    if not positions:
        return user_data

    import time as _time

    def _fetch_price(pos: dict) -> None:
        tkr = pos["ticker"]
        for attempt in range(3):
            try:
                t = yf.Ticker(tkr)
                fi = getattr(t, "fast_info", None)
                price = None
                if fi is not None:
                    price = getattr(fi, "last_price", None) or getattr(fi, "regularMarketPrice", None)
                if not price:
                    hist = t.history(period="3d")
                    if not hist.empty:
                        price = float(hist["Close"].dropna().iloc[-1])
                if price and price > 0:
                    pos["current_price"] = round(float(price), 2)
                    pos["market_value"] = round(float(price) * pos["shares"], 2)
                return
            except Exception as e:
                if attempt < 2:
                    _time.sleep(5 * (2 ** attempt))  # 5s poi 10s
                else:
                    log.debug("Prezzo %s non disponibile: %s", tkr, e)

    # Girando ora PRIMA dello screener la sessione è fresca: 8 thread su
    # poche decine di posizioni non la mettono in crisi.
    with ThreadPoolExecutor(max_workers=min(len(positions), 8)) as ex:
        list(ex.map(_fetch_price, positions))

    enriched = sum(1 for p in positions if "current_price" in p)

    # Rete di sicurezza: se non è arrivato nulla è quasi sempre la sessione
    # yfinance, non i ticker. Vale un rinnovo e un secondo giro — i prezzi
    # del portafoglio sono il dato più visibile dell'intero briefing.
    if enriched == 0 and positions:
        log.warning("Nessun prezzo ottenuto: rinnovo sessione yfinance e riprovo.")
        try:
            from yfinance.data import SingletonMeta
            SingletonMeta._instances.clear()
        except Exception as e:
            log.debug("reset sessione non riuscito: %s", e)
        _time.sleep(5)
        with ThreadPoolExecutor(max_workers=min(len(positions), 4)) as ex:
            list(ex.map(_fetch_price, positions))
        enriched = sum(1 for p in positions if "current_price" in p)

    if enriched == 0 and positions:
        log.error("Portfolio prices: 0/%d posizioni — la griglia del briefing "
                  "uscirà senza prezzi né P&L.", len(positions))
    elif enriched < len(positions):
        mancanti = [p["ticker"] for p in positions if "current_price" not in p]
        log.warning("Portfolio prices: %d/%d — senza prezzo: %s",
                    enriched, len(positions), ", ".join(mancanti))
    else:
        log.info("Portfolio prices enriched: %d/%d posizioni", enriched, len(positions))
    return user_data


def load_todo() -> str:
    if not DEFAULT_TODO_FILE.exists():
        return "(file 70-azioni-immediate.md non disponibile)"
    return DEFAULT_TODO_FILE.read_text()


def load_previous_briefings(user: str, days: int = 30) -> list[dict]:
    # docs/archivio/ persiste tra run (committato in git); briefings/ è effimero
    archive_dir = SCRIPT_DIR.parent / "docs" / "archivio"
    out = []
    for d in range(1, days + 1):
        date = (datetime.now() - timedelta(days=d)).strftime("%Y-%m-%d")
        # Controlla archivio HTML (persistente) poi output dir locale
        candidates = [
            archive_dir / f"{date}-{user.lower()}.html",
            DEFAULT_OUTPUT_DIR / f"{date}-{user.lower()}.html",
            DEFAULT_OUTPUT_DIR / f"{date}-{user.lower()}.md",
        ]
        for p in candidates:
            if p.exists():
                out.append({"date": date, "path": str(p)})
                break
    return out


def detect_mode_auto(previous: list[dict]) -> str:
    """Detect modalità da data + briefing precedenti."""
    today = datetime.now()
    weekday = today.weekday()  # 0=lun, 5=sab, 6=dom
    holidays = {(1, 1), (4, 25), (5, 1), (8, 15), (12, 25), (12, 26)}
    if (today.month, today.day) in holidays:
        return "festivo"
    if weekday in (5, 6):
        return "weekend"
    if not previous:
        return "onboarding"
    # Lunedì: preview settimana + rassegna weekend (gap weekend è fisiologico)
    if weekday == 0:
        return "lunedì"
    last_date = datetime.strptime(previous[0]["date"], "%Y-%m-%d")
    gap_days = (today - last_date).days
    if gap_days <= 1:
        return "daily"
    if gap_days <= 3:
        return "catchup"
    return "catchup_esteso"


# =============================================================================
# STEP 3 — MARKET SNAPSHOT
# =============================================================================

def fetch_market_snapshot() -> dict:
    try:
        import yfinance as yf
    except ImportError:
        log.warning("yfinance non installato, skip market snapshot")
        return {}
    indices = {
        "S&P 500": "^GSPC", "FTSE MIB": "FTSEMIB.MI", "Nikkei": "^N225",
        "Brent": "BZ=F", "EUR/USD": "EURUSD=X", "10Y UST": "^TNX",
    }
    snap = {}
    for label, tkr in indices.items():
        try:
            t = yf.Ticker(tkr)
            close = None
            # Try fast_info first (no crumb needed, works for most instruments)
            fi = getattr(t, "fast_info", None)
            if fi is not None:
                close = getattr(fi, "last_price", None) or getattr(fi, "regularMarketPrice", None)
            # Fallback: history with longer period for sparse instruments
            if not close:
                hist = t.history(period="5d")
                if not hist.empty:
                    close = hist["Close"].dropna().iloc[-1]
            if close:
                # For change_pct: use previousClose from fast_info or history
                prev = None
                if fi is not None:
                    prev = getattr(fi, "previous_close", None)
                if not prev:
                    hist = t.history(period="5d")
                    closes = hist["Close"].dropna()
                    if len(closes) >= 2:
                        prev = closes.iloc[-2]
                        close = closes.iloc[-1]
                change = (float(close) - float(prev)) / float(prev) * 100 if prev else 0
                snap[label] = {"value": round(float(close), 2),
                               "change_pct": round(float(change), 2)}
            else:
                snap[label] = {"value": None, "change_pct": None}
        except Exception as e:
            log.warning("market snapshot %s (%s) err: %s", label, tkr, e)
            snap[label] = {"value": None, "change_pct": None}
    return snap


def _market_from_context(ctx: dict) -> dict:
    """Costruisce market snapshot dai dati macro già fetchati dallo screener.

    Usa i dati pre-fetchati all'inizio della run dello screener (sessione fresca,
    prima del carico pesante su Yahoo Finance) per evitare rate-limit al momento
    del briefing.
    """
    macro = ctx.get("macro", {})
    mapping = [
        ("S&P 500",  "SP500"),
        ("FTSE MIB", "FTSE_MIB"),
        ("Nikkei",   "Nikkei"),
        ("Brent",    "Oil_Brent"),
        ("EUR/USD",  "EURUSD"),
        ("10Y UST",  "10Y_UST"),
    ]
    result = {}
    for label, key in mapping:
        rec = macro.get(key, {})
        last = rec.get("last")
        prev = rec.get("prev")
        if last:
            change = round((float(last) - float(prev)) / float(prev) * 100, 2) if prev and prev > 0 else 0.0
            result[label] = {"value": round(float(last), 2), "change_pct": change}
        else:
            result[label] = {"value": None, "change_pct": None}
    return result


# =============================================================================
# STEP 4 — CLAUDE API
# =============================================================================

def build_system_prompt() -> str:
    if not SYSTEM_PROMPT_PATH.exists():
        log.error("system_prompt.md non trovato in %s", SYSTEM_PROMPT_PATH)
        sys.exit(1)
    return SYSTEM_PROMPT_PATH.read_text()


def _mvf_synthesis(c: dict) -> dict:
    """Estrai i campi richiesti per il briefing — MVF v4.1.

    I 5 valori storici (voto, valore intrinseco, valore relativo, dividendi,
    prezzo ideale + MoS) piu' i campi nuovi della v4.1: IQI, gate di qualita',
    riconciliazione Voto<->IQI e rendimento netto Italia.
    """
    val = c.get("mvf_valuation") or {}
    metrics = c.get("metrics") or {}
    iqi = c.get("iqi_score") or {}
    gates = c.get("quality_gates") or {}
    cs = c.get("confidence_score") or {}
    ny = c.get("net_yield") or {}

    # Classe rilevata ma motore dedicato non disponibile: nessun voto emesso
    if val.get("engine_available") is False:
        return {
            "ticker": c.get("ticker"), "name": c.get("name"),
            "sector": c.get("sector"), "industry": c.get("industry"),
            "price": c.get("price"), "currency": c.get("currency"),
            "instrument_class": val.get("instrument_class"),
            "base": val.get("base"),
            "voto_mvf_1000": None,
            "analisi_non_disponibile": (
                f"Classe '{val.get('instrument_class')}' rilevata: motore dedicato "
                f"non disponibile in regime screening. Nessun voto emesso."),
        }

    return {
        "ticker": c.get("ticker"),
        "name": c.get("name"),
        "sector": c.get("sector"),
        "industry": c.get("industry"),
        "price": c.get("price"),
        "currency": c.get("currency"),
        "filiera": c.get("filiera_tag"),
        # Identita' e versionamento (Sez. 11F)
        "mvf_version": val.get("mvf_version"),
        "instrument_class": val.get("instrument_class"),
        "base": val.get("base"),
        # 1. VOTO FINALE — ora su 1000
        "voto_mvf_1000": c.get("mvf_vote_1000"),
        "voto_mvf_100": c.get("mvf_vote_100"),   # compat display
        "confidence_score_100": cs.get("total"),
        "confidence_reading": cs.get("reading"),
        "source_tag": cs.get("source_tag"),
        # 1-bis. IQI e catena del margine di sicurezza (v4.1)
        "iqi_100": iqi.get("total"),
        "iqi_blocco_a": iqi.get("blocco_a"),
        "iqi_blocco_b": iqi.get("blocco_b"),
        "dividend_tier": iqi.get("dividend_tier"),
        "riconciliazione_mvf_iqi": c.get("mvf_iqi_reconciliation"),
        # 1-ter. Gate di qualita' — NO-BUY strutturale
        "gate_attivi": gates.get("active", []),
        "gate_non_valutabili": gates.get("not_evaluable", []),
        "astensione": val.get("abstain", False),
        "motivo_astensione": val.get("abstain_reason", ""),
        # 4-bis. Rendimento netto post-imposte (Sez. 7)
        "rendimento_netto": {
            "lordo": ny.get("gross_yield"),
            "ritenuta_estera": ny.get("withholding_rate"),
            "netto_italia": ny.get("net_italy"),
            "drag_fiscale_totale": ny.get("effective_combined_rate"),
            "paese": ny.get("country"),
            "caso_speciale": ny.get("special_case"),
        },
        # 2. VALORE INTRINSECO (media ponderata 5 modelli)
        "valore_intrinseco": c.get("intrinsic_value"),
        "modelli_fair_value": {
            "graham": val.get("graham_fv"),
            "ddm": val.get("ddm_2stage_fv") or val.get("ddm_1stage_fv"),
            "dcf": val.get("dcf_2stage_fv"),
            "epv": val.get("epv_fv"),
        },
        # 3. VALORE RELATIVO (multipli vs settore)
        "valore_relativo": {
            "pe": metrics.get("ev_ebitda") and round(c.get("metrics", {}).get("ev_ebitda", 0), 2),
            "pe_ratio": c.get("metrics", {}).get("pe_ratio"),
            "ev_ebitda": metrics.get("ev_ebitda"),
            "fcf_yield": metrics.get("fcf_yield"),
            "pb": metrics.get("pb_ratio"),
            "ps": metrics.get("ps_ratio"),
        },
        # 4. DIVIDENDI
        "dividendi": {
            "yield": metrics.get("dividend_yield"),
            "payout": metrics.get("payout_ratio"),
            "growth_5y": metrics.get("dividend_growth_5y"),
            "buyback_yield": metrics.get("buyback_yield"),
        },
        # 5. PREZZO IDEALE DI ACQUISTO CON MoS
        "prezzo_ideale_acquisto": c.get("ideal_purchase_price_mos"),
        "margin_of_safety_pct": c.get("margin_of_safety_pct"),
        "upside_vs_current": val.get("upside_at_current_pct"),
        # Red flags critici (solo flag se presenti)
        "red_flags_critici": (c.get("mvf_red_flags") or {}).get("critical", []),
    }


# Feed verificati uno per uno. I precedenti erano in gran parte morti: i due
# feeds.reuters.com sono dismessi da anni, il vecchio endpoint CNBC risponde
# 403, quelli di Il Sole 24 Ore e MilanoFinanza 404. Restavano tre fonti vive
# su otto, e nessuna italiana.
NEWS_FEEDS: list[dict] = [
    {"label": "MarketWatch",         "url": "https://feeds.marketwatch.com/marketwatch/topstories/",   "lang": "en"},
    {"label": "FT Markets",          "url": "https://www.ft.com/markets?format=rss",                   "lang": "en"},
    {"label": "Bloomberg Markets",   "url": "https://feeds.bloomberg.com/markets/news.rss",            "lang": "en"},
    {"label": "Yahoo Finance",       "url": "https://finance.yahoo.com/news/rssindex",                 "lang": "en"},
    {"label": "CNBC Top News",       "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114", "lang": "en"},
    {"label": "ECB Press Releases",  "url": "https://www.ecb.europa.eu/rss/press.html",                "lang": "en"},
    {"label": "Fed Press Releases",  "url": "https://www.federalreserve.gov/feeds/press_all.xml",      "lang": "en"},
    {"label": "Il Sole 24 Ore",      "url": "https://www.ilsole24ore.com/rss/finanza.xml",             "lang": "it"},
    {"label": "Il Sole — Economia",  "url": "https://www.ilsole24ore.com/rss/economia.xml",            "lang": "it"},
    {"label": "ANSA Economia",       "url": "https://www.ansa.it/sito/notizie/economia/economia_rss.xml", "lang": "it"},
    {"label": "Repubblica Economia", "url": "https://www.repubblica.it/rss/economia/rss2.0.xml",       "lang": "it"},
]

_RSS_NS = {"atom": "http://www.w3.org/2005/Atom"}
_RSS_UA = {"User-Agent": "Mozilla/5.0 (compatible; ProximaBot/1.0)"}


def _txt(item, tag: str, default: str = "") -> str:
    # Attenzione all'`or`: un Element di ElementTree senza figli è FALSY, quindi
    # `item.find(tag) or item.find(f"atom:{tag}")` scartava il tag RSS trovato e
    # ripiegava sul namespace atom, che sui feed RSS non esiste. Risultato: _txt
    # tornava sempre "", ogni articolo veniva saltato da `if not title` e il
    # briefing girava con zero notizie senza un solo errore.
    el = item.find(tag)
    if el is None:
        el = item.find(f"atom:{tag}", _RSS_NS)
    return (el.text or "").strip() if el is not None else default


def _parse_pub_date(raw: str) -> Optional[datetime]:
    try:
        return _parse_rfc2822(raw).replace(tzinfo=None)
    except Exception:
        try:
            return datetime.fromisoformat(raw[:19])
        except Exception:
            return None


def _fetch_one_feed(feed: dict, max_per_feed: int, cutoff: datetime) -> list[dict]:
    if _requests is None:
        return []
    try:
        resp = _requests.get(feed["url"], timeout=10, headers=_RSS_UA)
        if resp.status_code != 200:
            log.warning("RSS %s: HTTP %s", feed["label"], resp.status_code)
            return []
        root = ET.fromstring(resp.content)
        items = root.findall(".//item") or root.findall(".//atom:entry", _RSS_NS)
        result = []
        for item in items[:max_per_feed]:
            title   = _txt(item, "title")
            summary = _txt(item, "description") or _txt(item, "summary") or _txt(item, "content")
            pub_raw = _txt(item, "pubDate") or _txt(item, "published") or _txt(item, "updated")
            if not title:
                continue
            pub_dt = _parse_pub_date(pub_raw) if pub_raw else None
            if pub_dt and pub_dt < cutoff:
                continue
            result.append({
                "source":    feed["label"],
                "lang":      feed["lang"],
                "title":     title,
                "summary":   " ".join(summary.split())[:200] if summary else "",
                "published": pub_dt.isoformat() if pub_dt else "",
            })
        return result
    except Exception as e:
        log.warning("RSS %s err: %s: %s", feed["label"], type(e).__name__, str(e)[:80])
        return []


def fetch_news_rss(max_per_feed: int = 8, max_age_hours: int = 36) -> list[dict]:
    if _requests is None:
        log.warning("requests non disponibile, skip news RSS")
        return []
    cutoff = datetime.now() - timedelta(hours=max_age_hours)
    all_items: list[dict] = []
    with ThreadPoolExecutor(max_workers=len(NEWS_FEEDS)) as ex:
        futs = [ex.submit(_fetch_one_feed, feed, max_per_feed, cutoff) for feed in NEWS_FEEDS]
        for fut in as_completed(futs):
            all_items.extend(fut.result())
    all_items.sort(key=lambda x: x["published"], reverse=True)
    vive = {i["source"] for i in all_items}
    log.info("News RSS: %d articoli da %d/%d feed", len(all_items),
             len(vive), len(NEWS_FEEDS))
    mute = [f["label"] for f in NEWS_FEEDS if f["label"] not in vive]
    if mute:
        log.warning("RSS senza articoli (%d/%d): %s",
                    len(mute), len(NEWS_FEEDS), ", ".join(mute))
    if not all_items:
        log.error("RSS: nessun articolo da nessun feed — il briefing girerà senza rassegna stampa.")
    return all_items


def build_user_prompt(user_data, screener_data, market, todo, previous, mode, news: list[dict] | None = None):
    tier1 = screener_data.get("candidates", [])
    tier2 = screener_data.get("speculative_candidates", [])
    tier3 = screener_data.get("special_situations", [])
    filiere = screener_data.get("filiere_strategiche", {})
    ctx   = screener_data.get("market_context", {})

    # Top 40 per la rassegna stampa (di 500 analizzati), in formato MVF v3.0 sintetico
    tier1_top = sorted(tier1, key=lambda c: c.get("mvf_vote_100") or 0, reverse=True)[:40]
    tier1_mvf = [_mvf_synthesis(c) for c in tier1_top]

    # Lookup Tier 1 per ticker symbol (per cross-reference filiere ↔ MVF)
    tier1_lookup: dict = {}
    for c in tier1:
        tkr = c.get("ticker", "")
        tier1_lookup[tkr] = c
        base = tkr.split(".")[0] if "." in tkr else tkr
        tier1_lookup[base] = c

    # Filiere: top 8 per filiera — MVF data dove disponibile, TV data altrimenti
    filiere_section = ""
    if filiere:
        fil_blocks = []
        for fname, candidates in filiere.items():
            if not candidates:
                continue
            top_per_fil = candidates[:8]
            fil_blocks.append(f"  {fname.upper()} ({len(candidates)} totali, top 8 mostrati):")
            for cand in top_per_fil:
                tv_tkr = cand.get("tv_ticker", "")
                # Extract base symbol: "NASDAQ:NVDA" → "NVDA", "LSE:SHEL" → "SHEL"
                base_sym = tv_tkr.split(":")[1] if ":" in tv_tkr else tv_tkr
                base_sym2 = base_sym.split(".")[0]
                t1 = tier1_lookup.get(base_sym) or tier1_lookup.get(base_sym2)
                if t1 and t1.get("mvf_vote_100"):
                    mvf = _mvf_synthesis(t1)
                    fil_blocks.append(
                        f"    - {tv_tkr} | {cand.get('name','')[:40]} | "
                        f"[MVF] voto={mvf['voto_mvf_100']}/100 | "
                        f"V.intrinseco={mvf['valore_intrinseco']} | "
                        f"prezzo_ideale={mvf['prezzo_ideale_acquisto']} | "
                        f"PE={cand.get('pe', 'n/a')} | DY={(cand.get('div_yield') or 0)*100:.1f}%"
                    )
                else:
                    price = cand.get("price") or 0
                    pt = cand.get("price_target") or 0
                    upside_str = (
                        f" | upside_analisti={((pt - price) / price * 100):.0f}%"
                        if pt > 0 and price > 0 else ""
                    )
                    fil_blocks.append(
                        f"    - {tv_tkr} | {cand.get('name','')[:40]} | "
                        f"[TV] mcap=${cand.get('market_cap', 0)/1e9:.1f}B | "
                        f"PE={cand.get('pe', 'n/a')} | DY={(cand.get('div_yield') or 0)*100:.1f}% | "
                        f"relvol={cand.get('rel_vol', 1):.1f}{upside_str}"
                    )
        filiere_section = "FILIERE STRATEGICHE (screener dedicato per settori cruciali):\n" + "\n".join(fil_blocks)

    # Market context: leaders/laggards + macro summary
    ctx_section = ""
    if ctx:
        leaders  = ctx.get("sector_leaders_1m", [])
        laggards = ctx.get("sector_laggards_1m", [])
        vix      = ctx.get("vix")
        spread   = ctx.get("yield_curve_spread_10y2y")
        macro    = ctx.get("macro", {})
        regions  = ctx.get("regions", {})
        ctx_section = f"""
MARKET CONTEXT (ETF settoriali + regionali + macro):
Settori US leaders 1m: {leaders}
Settori US laggards 1m: {laggards}
VIX: {vix} | Yield curve 10y-2y: {spread}
Macro: {json.dumps({k: v.get("1m") for k, v in macro.items()}, default=str)}
Regioni 1m%: {json.dumps({k: v.get("1m") for k, v in regions.items()}, default=str)}
"""

    spec_section = ""
    if tier2:
        spec_section = f"""
TIER 2 — CATALYST / SPECULATIVE (small-cap, segnali attivi):
Menziona solo titoli con ≥3 segnali nella sezione "Radar Speculativo".
{json.dumps(tier2[:20], indent=2, default=str)[:5000]}
"""

    special_section = ""
    if tier3:
        special_section = f"""
TIER 3 — SPECIAL SITUATIONS (deep value PE/PB + fallen angels):
Deep value = PE 2-8 oppure P/B<0.8. Fallen angel = yield >6%.
Inserisci 2-3 nella sezione "Filiere strategiche" se il Piotroski ≥5.
{json.dumps(tier3[:15], indent=2, default=str)[:4000]}
"""

    news_section = ""
    if news:
        lines = []
        for item in news[:60]:  # cap a 60 articoli nel prompt
            pub = f" [{item['published'][:16]}]" if item.get("published") else ""
            summ = f" — {item['summary']}" if item.get("summary") else ""
            lines.append(f"  [{item['source']}]{pub} {item['title']}{summ}")
        news_section = "NEWS FRESCHE (RSS ultimi 36h, usa queste come base per le sezioni notizie):\n" + "\n".join(lines)

    gender = user_data.get("gender", "maschile")
    gender_note = f"GENERE NARRATIVA: {user_data['user'].upper()} è {'un uomo' if gender == 'maschile' else 'una donna'} — usa il genere {gender} in tutta la narrativa italiana.\n"

    return f"""Genera il briefing per {user_data['user'].upper()} in data {datetime.now():%Y-%m-%d}.

{gender_note}MODE: {mode}
{ctx_section}
{news_section}

PORTAFOGLIO:
{json.dumps(user_data, indent=2, default=str)}

MARKET SNAPSHOT (real-time):
{json.dumps(market, indent=2)}

TIER 1 — TOP 40 CANDIDATI MVF v3.0 (di 500 analizzati a fondo).
Per ogni titolo hai SOLO i 5 indicatori sintetici (per scelta dell'utente):
1) Voto finale MVF /100  2) Valore intrinseco (media ponderata 5 modelli)
3) Valore relativo (multipli)  4) Dividendi  5) Prezzo ideale di acquisto + MoS

REGOLA OUTPUT: nella rassegna stampa cita SOLO questi 5 valori per titolo
(non l'intera analisi MVF). Tutti gli altri dati MVF non vengono mostrati al
lettore — il calcolo è stato fatto, ma l'output è volutamente compatto.

{json.dumps(tier1_mvf, indent=2, default=str)[:15000]}
{spec_section}{special_section}
{filiere_section}

TODO DEL GIORNO:
{todo[:3000]}

BRIEFING PRECEDENTI ({len(previous)} disponibili):
{json.dumps([p['date'] for p in previous], indent=2)}

Produci markdown strutturato secondo le specifiche del system prompt.
Per la sezione "Occasioni in filiere strategiche e colli di bottiglia":
- Usa i candidati delle filiere strategiche sopra
- Identifica per ciascuna filiera 2-3 titoli più interessanti
- Spiega il "perché" della filiera (bottleneck, scarsità, posizionamento)
- Riporta multipli e momentum dei candidati

Usa il market context per contestualizzare (es. "in un mercato dove XLE +12% YTD...").
"""


def call_claude(system: str, user: str, dry_run: bool = False) -> str:
    if dry_run:
        log.info("DRY RUN: skip Claude API call")
        return (
            "# DRY RUN OUTPUT\n\n"
            f"System prompt: {len(system)} chars (~{len(system)//4} tokens)\n"
            f"User prompt: {len(user)} chars (~{len(user)//4} tokens)\n\n"
            "## Cosa avrebbe fatto Claude\n\n"
            "Generato briefing markdown completo seguendo system_prompt.md "
            "con dati passati nel user prompt.\n\n"
            "Per esecuzione reale: rimuovi --dry-run e imposta ANTHROPIC_API_KEY.\n"
        )
    try:
        from anthropic import Anthropic
    except ImportError:
        log.error("anthropic non installata. pip install anthropic")
        sys.exit(1)
    if not os.environ.get("ANTHROPIC_API_KEY"):
        log.error("ANTHROPIC_API_KEY non impostata.")
        sys.exit(1)
    client = Anthropic()
    log.info("Step 4/6: chiamata API Claude %s (cache, streaming)...", CLAUDE_MODEL)
    with client.messages.stream(
        model=CLAUDE_MODEL,
        max_tokens=CLAUDE_MAX_TOKENS,
        system=[{
            "type": "text", "text": system,
            "cache_control": {"type": "ephemeral"},
        }],
        messages=[{"role": "user", "content": user}],
    ) as stream:
        response = stream.get_final_message()
    usage = response.usage
    cache_read = getattr(usage, "cache_read_input_tokens", 0)
    cache_create = getattr(usage, "cache_creation_input_tokens", 0)
    log.info("Token usage: input=%d (cache_read=%d, cache_create=%d), output=%d",
             usage.input_tokens, cache_read, cache_create, usage.output_tokens)
    # Stima costi Opus 4.6 (input $15, cache_create $18.75, cache_read $1.50, output $75 /MTok)
    cost = (usage.input_tokens * 15 + cache_create * 18.75 + cache_read * 1.50
            + usage.output_tokens * 75) / 1_000_000
    log.info("Costo stimato: $%.4f", cost)
    return response.content[0].text


_GIORNI_IT = ["Lunedì","Martedì","Mercoledì","Giovedì","Venerdì","Sabato","Domenica"]
_MESI_IT   = ["","Gennaio","Febbraio","Marzo","Aprile","Maggio","Giugno",
               "Luglio","Agosto","Settembre","Ottobre","Novembre","Dicembre"]

def _format_date_it(dt: datetime) -> str:
    return f"{_GIORNI_IT[dt.weekday()]} {dt.day} {_MESI_IT[dt.month]} {dt.year}"


# =============================================================================
# STEP 5 — RENDER HTML
# =============================================================================

def render_html(markdown_briefing: str, user: str, mode: str,
                market_data: dict | None = None,
                user_data: dict | None = None) -> Path:
    log.info("Step 5/6: render HTML...")
    DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    date_tag = datetime.now().strftime("%Y-%m-%d")
    md_path = DEFAULT_OUTPUT_DIR / f"{date_tag}-{user}.md"
    md_path.write_text(markdown_briefing, encoding="utf-8")

    try:
        from jinja2 import Template
        import markdown as md_lib
    except ImportError:
        log.warning("jinja2/markdown non installati, salvo solo markdown")
        return md_path
    if not TEMPLATE_PATH.exists():
        log.warning("Template HTML non trovato, salvo solo markdown")
        return md_path

    body_html = md_lib.markdown(
        markdown_briefing,
        extensions=["tables", "fenced_code", "nl2br", "sane_lists"],
    )
    template = Template(TEMPLATE_PATH.read_text())
    html = template.render(
        title=f"Proxima Daily — {user.title()}",
        date=_format_date_it(datetime.now()),
        user=user, mode=mode, body=body_html,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        market=market_data or {},
        portfolio=user_data or {},
    )
    out = DEFAULT_OUTPUT_DIR / f"{date_tag}-{user}.html"
    out.write_text(html, encoding="utf-8")
    log.info("HTML salvato: %s", out)
    return out


# =============================================================================
# STEP 6 — DELIVERY
# =============================================================================

def deliver(output_path: Path, user: str):
    log.info("Step 6/6: delivery → %s", output_path)
    # Skip browser open su CI (GitHub Actions): runner headless, può hangare
    if not (os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS")):
        try:
            webbrowser.open(f"file://{output_path.absolute()}")
        except Exception:
            pass
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    tg_chat = os.environ.get("TELEGRAM_CHAT_ID")
    if tg_token and tg_chat:
        try:
            date_label = datetime.now().strftime("%d/%m/%Y")
            # Invia il file HTML vero (non solo testo) — apribile su iPad/mobile
            with open(output_path, "rb") as f:
                _requests.post(
                    f"https://api.telegram.org/bot{tg_token}/sendDocument",
                    data={"chat_id": tg_chat,
                          "caption": f"Proxima Daily — {user.title()} {date_label}"},
                    files={"document": (output_path.name, f, "text/html")},
                    timeout=30,
                )
            log.info("File HTML inviato via Telegram")
        except Exception as e:
            log.warning("Telegram fallito: %s", e)



# =============================================================================
# MAIN
# =============================================================================

def main():
    p = argparse.ArgumentParser(description="Proxima Briefing Pipeline")
    p.add_argument("--user", default=None, choices=["alex", "vale"])
    p.add_argument("--mode",
                   choices=["auto", "daily", "weekend", "lunedì", "catchup", "festivo", "onboarding"],
                   default="auto")
    p.add_argument("--region", default="GLOBAL", choices=["US", "EU", "ASIA", "GLOBAL"])
    p.add_argument("--skip-screener", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--test-snapshot", action="store_true",
                   help="Debug: stampa market snapshot e termina")
    args = p.parse_args()

    if args.test_snapshot:
        snap = fetch_market_snapshot()
        print(json.dumps(snap, indent=2))
        return

    if not args.user:
        p.error("--user è obbligatorio (eccetto --test-snapshot)")

    log.info("=== Proxima Briefing Pipeline ===")
    log.info("User: %s | Mode: %s | Region: %s", args.user, args.mode, args.region)

    # I prezzi del portafoglio si prendono PRIMA dello screener, non dopo.
    # Lo screener macina ~600 titoli e satura la sessione yfinance: quando
    # toccava al portafoglio il crumb era già invalidato e Alex usciva con
    # "0/23 posizioni" arricchite — cioè la griglia che apre il briefing,
    # la prima cosa che vede, senza prezzi né P&L. Vale invece i prezzi li
    # otteneva, perché gira dopo con la cache screener e sessione fresca:
    # è stato quel contrasto a identificare la causa.
    user_data = load_portfolio(args.user)
    log.info("Portfolio %s: %d posizioni, cash=%.0f, pac=%.0f",
             args.user, len(user_data["positions"]),
             user_data["cash"], user_data["pac_monthly"])
    if not args.dry_run:
        user_data = enrich_portfolio_prices(user_data)

    screener_data = {"candidates": []}
    if not args.skip_screener and not args.dry_run:
        sp = run_screener(region=args.region, strategy="all")
        if sp:
            screener_data = json.loads(sp.read_text())
    elif args.skip_screener:
        date_tag = datetime.now().strftime("%Y-%m-%d")
        existing = SCREENER_OUTPUT_DIR / f"screener_{date_tag}.json"
        if existing.exists():
            screener_data = json.loads(existing.read_text())
            log.info("Riuso screener output esistente: %s", existing)
    elif args.dry_run:
        log.info("DRY RUN: skip screener")

    todo = load_todo()
    previous = load_previous_briefings(args.user)
    mode = args.mode if args.mode != "auto" else detect_mode_auto(previous)
    log.info("Modalità: %s", mode)

    # Market snapshot: primary = dati già fetchati dallo screener (evita rate-limit)
    market = {}
    if not args.dry_run:
        ctx = screener_data.get("market_context", {})
        if ctx.get("macro"):
            market = _market_from_context(ctx)
            valid_ctx = sum(1 for v in market.values() if v.get("value"))
            log.info("Market snapshot da context screener: %d/6 indici", valid_ctx)
        # Fallback live fetch per indici mancanti
        missing = [k for k, v in market.items() if not v.get("value")]
        if not market or len(missing) > 2:
            log.info("Fallback: fetch live market snapshot (context ha %d/6 indici)", len(market) - len(missing))
            live = fetch_market_snapshot()
            for k, v in live.items():
                if k not in market or not market[k].get("value"):
                    market[k] = v
        valid = sum(1 for v in market.values() if v.get("value"))
        log.info("Market snapshot finale: %d/6 indici validi", valid)

    news = fetch_news_rss() if not args.dry_run else []

    system = build_system_prompt()
    user_prompt = build_user_prompt(user_data, screener_data, market, todo, previous, mode, news=news)
    log.info("Prompt — system: %d chars, user: %d chars",
             len(system), len(user_prompt))

    briefing_md = call_claude(system, user_prompt, dry_run=args.dry_run)
    if not briefing_md:
        log.error("Briefing vuoto. Esco.")
        sys.exit(1)

    html_path = render_html(briefing_md, args.user, mode,
                            market_data=market, user_data=user_data)
    if html_path and not args.dry_run:
        deliver(html_path, args.user)

    log.info("=== FATTO ===")
    log.info("Output: %s", html_path)


if __name__ == "__main__":
    main()
