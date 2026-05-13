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
    4. chiama API Claude Sonnet 4.6 con prompt caching (90% sconto)
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
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

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

CLAUDE_MODEL = "claude-sonnet-4-6"
CLAUDE_MAX_TOKENS = 8000


# =============================================================================
# STEP 1 — SCREENER
# =============================================================================

def run_screener(region="GLOBAL", strategy="all") -> Optional[Path]:
    """Esegue screener.py come subprocess e ritorna il path del JSON output."""
    log.info("Step 1/6: lancio screener (region=%s, strategy=%s)...", region, strategy)
    cmd = [
        sys.executable, str(SCRIPT_DIR / "screener.py"),
        "--region", region, "--strategy", strategy, "--top", "30",
        "--output", str(SCREENER_OUTPUT_DIR),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        log.error("Screener timeout (>10min).")
        return None
    except subprocess.CalledProcessError as e:
        log.error("Screener fallito: %s", e.stderr[:500])
        return None
    date_tag = datetime.now().strftime("%Y-%m-%d")
    json_path = SCREENER_OUTPUT_DIR / f"screener_{date_tag}.json"
    if not json_path.exists():
        log.warning("Output screener non trovato.")
        return None
    log.info("Screener OK: %s", json_path)
    return json_path


# =============================================================================
# STEP 2 — LOAD LOCAL CONTEXT
# =============================================================================

def load_portfolio(user: str) -> dict:
    """Carica portafoglio utente da CSV locale."""
    csv_path = DEFAULT_PORTFOLIO_DIR / f"{user.lower()}.csv"
    if not csv_path.exists():
        log.warning("Portfolio %s non trovato in %s", user, csv_path)
        return {"user": user, "positions": [], "cash": 0, "pac_monthly": 0}
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
    return {"user": user, "positions": positions, "cash": cash, "pac_monthly": pac}


def load_todo() -> str:
    if not DEFAULT_TODO_FILE.exists():
        return "(file 70-azioni-immediate.md non disponibile)"
    return DEFAULT_TODO_FILE.read_text()


def load_previous_briefings(user: str, days: int = 7) -> list[dict]:
    out = []
    for d in range(1, days + 1):
        date = (datetime.now() - timedelta(days=d)).strftime("%Y-%m-%d")
        md_path = DEFAULT_OUTPUT_DIR / f"{date}-{user.lower()}.md"
        if md_path.exists():
            out.append({"date": date, "path": str(md_path)})
    return out


def detect_mode_auto(previous: list[dict]) -> str:
    """Detect modalità da data + briefing precedenti."""
    today = datetime.now()
    weekday = today.weekday()  # 5=sat, 6=sun
    holidays = {(1, 1), (4, 25), (5, 1), (8, 15), (12, 25), (12, 26)}
    if (today.month, today.day) in holidays:
        return "festivo"
    if weekday in (5, 6):
        return "weekend"
    if not previous:
        return "onboarding"
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
            hist = t.history(period="2d")
            if not hist.empty:
                close = hist["Close"].iloc[-1]
                prev = hist["Close"].iloc[-2] if len(hist) > 1 else close
                change = (close - prev) / prev * 100 if prev else 0
                snap[label] = {"value": round(float(close), 2),
                               "change_pct": round(float(change), 2)}
        except Exception:
            snap[label] = {"value": None, "change_pct": None}
    return snap


# =============================================================================
# STEP 4 — CLAUDE API
# =============================================================================

def build_system_prompt() -> str:
    if not SYSTEM_PROMPT_PATH.exists():
        log.error("system_prompt.md non trovato in %s", SYSTEM_PROMPT_PATH)
        sys.exit(1)
    return SYSTEM_PROMPT_PATH.read_text()


def build_user_prompt(user_data, screener_data, market, todo, previous, mode):
    return f"""Genera il briefing per {user_data['user'].upper()} in data {datetime.now():%Y-%m-%d}.

MODE: {mode}

PORTAFOGLIO:
{json.dumps(user_data, indent=2, default=str)}

MARKET SNAPSHOT:
{json.dumps(market, indent=2)}

SCREENER OUTPUT (top 30 candidati pre-filtrati MVF v3.0):
{json.dumps(screener_data, indent=2, default=str)[:10000]}

TODO DEL GIORNO:
{todo[:3000]}

BRIEFING PRECEDENTI ({len(previous)} disponibili):
{json.dumps([p['date'] for p in previous], indent=2)}

Produci markdown strutturato secondo le specifiche del system prompt.
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
    log.info("Step 4/6: chiamata API Claude %s (cache attivo)...", CLAUDE_MODEL)
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=CLAUDE_MAX_TOKENS,
        system=[{
            "type": "text", "text": system,
            "cache_control": {"type": "ephemeral"},
        }],
        messages=[{"role": "user", "content": user}],
    )
    usage = response.usage
    cache_read = getattr(usage, "cache_read_input_tokens", 0)
    cache_create = getattr(usage, "cache_creation_input_tokens", 0)
    log.info("Token usage: input=%d (cache_read=%d, cache_create=%d), output=%d",
             usage.input_tokens, cache_read, cache_create, usage.output_tokens)
    # Stima costi Sonnet 4.6
    cost = (usage.input_tokens * 3 + cache_create * 3.75 + cache_read * 0.30
            + usage.output_tokens * 15) / 1_000_000
    log.info("Costo stimato: $%.4f", cost)
    return response.content[0].text


# =============================================================================
# STEP 5 — RENDER HTML
# =============================================================================

def render_html(markdown_briefing: str, user: str, mode: str) -> Path:
    log.info("Step 5/6: render HTML...")
    DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    date_tag = datetime.now().strftime("%Y-%m-%d")
    md_path = DEFAULT_OUTPUT_DIR / f"{date_tag}-{user}.md"
    md_path.write_text(markdown_briefing)

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
        date=datetime.now().strftime("%A %d %B %Y").capitalize(),
        user=user, mode=mode, body=body_html,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )
    out = DEFAULT_OUTPUT_DIR / f"{date_tag}-{user}.html"
    out.write_text(html)
    log.info("HTML salvato: %s", out)
    return out


# =============================================================================
# STEP 6 — DELIVERY
# =============================================================================

def deliver(output_path: Path, user: str):
    log.info("Step 6/6: delivery → %s", output_path)
    try:
        webbrowser.open(f"file://{output_path.absolute()}")
    except Exception:
        pass
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    tg_chat = os.environ.get("TELEGRAM_CHAT_ID")
    if tg_token and tg_chat:
        try:
            import requests
            requests.post(
                f"https://api.telegram.org/bot{tg_token}/sendMessage",
                data={"chat_id": tg_chat,
                      "text": f"📰 Briefing {user} pronto: {output_path.name}"},
                timeout=10,
            )
            log.info("Notifica Telegram inviata")
        except Exception as e:
            log.warning("Telegram fallito: %s", e)


# =============================================================================
# MAIN
# =============================================================================

def main():
    p = argparse.ArgumentParser(description="Proxima Briefing Pipeline")
    p.add_argument("--user", required=True, choices=["alex", "vale"])
    p.add_argument("--mode",
                   choices=["auto", "daily", "weekend", "catchup", "festivo", "onboarding"],
                   default="auto")
    p.add_argument("--region", default="GLOBAL", choices=["US", "EU", "ASIA", "GLOBAL"])
    p.add_argument("--skip-screener", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    log.info("=== Proxima Briefing Pipeline ===")
    log.info("User: %s | Mode: %s | Region: %s", args.user, args.mode, args.region)

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

    user_data = load_portfolio(args.user)
    log.info("Portfolio %s: %d posizioni, cash=%.0f, pac=%.0f",
             args.user, len(user_data["positions"]),
             user_data["cash"], user_data["pac_monthly"])

    todo = load_todo()
    previous = load_previous_briefings(args.user)
    mode = args.mode if args.mode != "auto" else detect_mode_auto(previous)
    log.info("Modalità: %s", mode)

    market = fetch_market_snapshot() if not args.dry_run else {}
    if market:
        log.info("Market snapshot: %d indici",
                 sum(1 for v in market.values() if v.get("value")))

    system = build_system_prompt()
    user_prompt = build_user_prompt(user_data, screener_data, market, todo, previous, mode)
    log.info("Prompt — system: %d chars, user: %d chars",
             len(system), len(user_prompt))

    briefing_md = call_claude(system, user_prompt, dry_run=args.dry_run)
    if not briefing_md:
        log.error("Briefing vuoto. Esco.")
        sys.exit(1)

    html_path = render_html(briefing_md, args.user, mode)
    if html_path and not args.dry_run:
        deliver(html_path, args.user)

    log.info("=== FATTO ===")
    log.info("Output: %s", html_path)


if __name__ == "__main__":
    main()
