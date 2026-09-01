"""Reperimento dati: yfinance (secondaria) + SEC EDGAR XBRL (primaria US).

DIP (spec Sez. 6-bis): [P] primario ufficiale, [V] >=2 fonti concordi,
[U] fonte singola. In bozza 1 il primario e' EDGAR (US/ADR); EDINET/DART/
MOPS/ESEF sono nello stack definitivo ma non ancora cablati (v. calibrazione
§9): fuori dagli US il tag resta [U] finche' non arrivano.
"""
from __future__ import annotations

import json
import logging
import os
import time
from datetime import date

import pandas as pd
import requests as std_requests

import config

log = logging.getLogger("fetchers")

# ---------------------------------------------------------------- sessione yf
_YF_SESSION = None


def yf_session():
    """Sessione curl_cffi compatibile con proxy aziendali (CA custom).

    Prova l'impersonation browser; se il proxy la rifiuta (reset TLS),
    ripiega su TLS standard. Mai disabilitare la verifica.
    """
    global _YF_SESSION
    if _YF_SESSION is not None:
        return _YF_SESSION
    from curl_cffi import requests as cr
    ca = os.environ.get("CURL_CA_BUNDLE") or os.environ.get("SSL_CERT_FILE") or True
    proxies = {}
    if os.environ.get("HTTPS_PROXY"):
        proxies = {"https": os.environ["HTTPS_PROXY"], "http": os.environ["HTTPS_PROXY"]}
    for imp in ("chrome", None):
        try:
            s = cr.Session(impersonate=imp, verify=ca, proxies=proxies or None)
            s.get("https://query1.finance.yahoo.com/", timeout=10)
            _YF_SESSION = s
            return s
        except Exception as e:
            log.debug("yf session impersonate=%s fallita: %s", imp, str(e)[:80])
    _YF_SESSION = cr.Session(impersonate=None, verify=ca, proxies=proxies or None)
    return _YF_SESSION


def _row(df: pd.DataFrame, names: list[str]) -> list[float | None]:
    """Serie annuale (piu' recente per prima) per la prima riga trovata."""
    if df is None or df.empty:
        return []
    for n in names:
        if n in df.index:
            vals = []
            for v in df.loc[n].tolist():
                try:
                    f = float(v)
                    vals.append(None if pd.isna(f) else f)
                except (TypeError, ValueError):
                    vals.append(None)
            return vals
    return []


def fetch_yf(ticker: str) -> dict | None:
    """Scarica bilanci annuali, dividendi, prezzi e anagrafica da yfinance."""
    import yfinance as yf
    last_err = None
    for attempt in range(config.YF_MAX_RETRIES):
        try:
            t = yf.Ticker(ticker, session=yf_session())
            info = t.info or {}
            if not info.get("symbol") and not info.get("shortName"):
                raise RuntimeError("info vuoto")
            inc, bs, cf = t.income_stmt, t.balance_sheet, t.cashflow
            div = t.dividends
            hist = t.history(period="6y", auto_adjust=True)
            raw = {
                "ticker": ticker, "info": info,
                "revenue": _row(inc, ["Total Revenue", "Operating Revenue"]),
                "gross_profit": _row(inc, ["Gross Profit"]),
                "operating_income": _row(inc, ["Operating Income", "Total Operating Income As Reported", "EBIT"]),
                "ebit": _row(inc, ["EBIT", "Operating Income"]),
                "ebitda": _row(inc, ["EBITDA", "Normalized EBITDA"]),
                "net_income": _row(inc, ["Net Income", "Net Income Common Stockholders"]),
                "pretax_income": _row(inc, ["Pretax Income"]),
                "tax_provision": _row(inc, ["Tax Provision"]),
                "diluted_eps": _row(inc, ["Diluted EPS"]),
                "interest_expense": _row(inc, ["Interest Expense", "Interest Expense Non Operating"]),
                "rd": _row(inc, ["Research And Development"]),
                "da_income": _row(inc, ["Reconciled Depreciation"]),
                "total_assets": _row(bs, ["Total Assets"]),
                "equity": _row(bs, ["Stockholders Equity", "Common Stock Equity", "Total Equity Gross Minority Interest"]),
                "total_debt": _row(bs, ["Total Debt"]),
                "cash": _row(bs, ["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"]),
                "current_assets": _row(bs, ["Current Assets"]),
                "current_liab": _row(bs, ["Current Liabilities"]),
                "total_liab": _row(bs, ["Total Liabilities Net Minority Interest"]),
                "retained": _row(bs, ["Retained Earnings"]),
                "working_capital": _row(bs, ["Working Capital"]),
                "goodwill": _row(bs, ["Goodwill", "Goodwill And Other Intangible Assets"]),
                "shares": _row(bs, ["Ordinary Shares Number", "Share Issued"]),
                "cfo": _row(cf, ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities"]),
                "capex": _row(cf, ["Capital Expenditure"]),
                "fcf_yf": _row(cf, ["Free Cash Flow"]),
                "sbc": _row(cf, ["Stock Based Compensation"]),
                "dividends_paid": _row(cf, ["Cash Dividends Paid", "Common Stock Dividend Paid"]),
                "da_cf": _row(cf, ["Depreciation And Amortization", "Depreciation Amortization Depletion"]),
                "buyback_cf": _row(cf, ["Repurchase Of Capital Stock"]),
            }
            raw["dividends_series"] = ({str(k.date()): float(v) for k, v in div.items()}
                                       if div is not None and len(div) else {})
            raw["prices"] = ({str(k.date()): float(v) for k, v in hist["Close"].items()}
                             if hist is not None and not hist.empty else {})
            return raw
        except Exception as e:
            last_err = e
            wait = config.YF_BACKOFF_S * (attempt + 1)
            log.warning("yfinance %s tentativo %d fallito (%s), retry in %ds",
                        ticker, attempt + 1, str(e)[:80], wait)
            time.sleep(wait)
    log.error("yfinance %s: rinuncio (%s)", ticker, str(last_err)[:120])
    return None


# ------------------------------------------------------------------- EDGAR --
_CIK_MAP: dict[str, int] | None = None

EDGAR_CONCEPTS = {
    "revenue": ["RevenueFromContractWithCustomerExcludingAssessedTax",
                "Revenues", "SalesRevenueNet",
                "RevenueFromContractWithCustomerIncludingAssessedTax"],
    "net_income": ["NetIncomeLoss"],
    "cfo": ["NetCashProvidedByUsedInOperatingActivities"],
    "capex": ["PaymentsToAcquirePropertyPlantAndEquipment"],
    "total_assets": ["Assets"],
    "equity": ["StockholdersEquity"],
}


def _edgar_get(url: str) -> dict | None:
    try:
        r = std_requests.get(url, headers={"User-Agent": config.EDGAR_UA}, timeout=30)
        if r.status_code == 200:
            return r.json()
        log.debug("EDGAR %s -> %d", url, r.status_code)
    except Exception as e:
        log.debug("EDGAR errore %s: %s", url, str(e)[:80])
    return None


def _cik_for(ticker: str) -> int | None:
    global _CIK_MAP
    if _CIK_MAP is None:
        os.makedirs(config.CACHE_DIR, exist_ok=True)
        cache = os.path.join(config.CACHE_DIR, "company_tickers.json")
        data = None
        if os.path.exists(cache) and time.time() - os.path.getmtime(cache) < 7 * 86400:
            data = json.load(open(cache))
        else:
            data = _edgar_get("https://www.sec.gov/files/company_tickers.json")
            if data:
                json.dump(data, open(cache, "w"))
        _CIK_MAP = ({e["ticker"].upper(): int(e["cik_str"]) for e in data.values()}
                    if data else {})
    return _CIK_MAP.get(ticker.upper().split(".")[0])


def _fy_values(facts: dict, concepts: list[str]) -> dict[int, float]:
    gaap = facts.get("facts", {}).get("us-gaap", {})
    for c in concepts:
        node = gaap.get(c)
        if not node:
            continue
        out: dict[int, float] = {}
        for unit, entries in node.get("units", {}).items():
            if unit not in ("USD", "USD/shares"):
                continue
            for e in entries:
                if e.get("form") not in ("10-K", "20-F", "40-F") or e.get("fp") != "FY":
                    continue
                fy = e.get("fy")
                if not fy:
                    continue
                st, en = e.get("start"), e.get("end")
                if st and en:
                    try:
                        if (date.fromisoformat(en) - date.fromisoformat(st)).days < 300:
                            continue  # scarta i trimestrali dentro il 10-K
                    except ValueError:
                        pass
                out[int(fy)] = float(e["val"])
        if out:
            return out
    return {}


def fetch_edgar(ticker: str) -> dict[str, dict[int, float]]:
    """Fatti annuali [P] da EDGAR per i concetti di validazione. {} se non-US."""
    cik = _cik_for(ticker)
    if not cik:
        return {}
    os.makedirs(config.CACHE_DIR, exist_ok=True)
    cache = os.path.join(config.CACHE_DIR, f"facts_{cik}.json")
    facts = None
    if os.path.exists(cache) and time.time() - os.path.getmtime(cache) < 3 * 86400:
        facts = json.load(open(cache))
    else:
        facts = _edgar_get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json")
        if facts:
            json.dump(facts, open(cache, "w"))
    if not facts:
        return {}
    return {k: _fy_values(facts, v) for k, v in EDGAR_CONCEPTS.items()}


def cross_validate(raw: dict, edgar: dict) -> dict:
    """Confronta yfinance vs EDGAR sui fatti core e assegna la fiducia.

    Ritorna: {"tags": {fact: P|V|U}, "agree_ratio": float|None,
              "statement_trust": V|U}.
    Regola bozza 1: se >=4 fatti core concordano entro l'1% (tolleranza spec
    per le voci esatte), i bilanci yfinance si considerano cross-validati ->
    i fatti derivati non confrontati direttamente ereditano [V]; i fatti
    confermati direttamente sono [P]. Fuori EDGAR: tutto [U].
    """
    tags: dict[str, str] = {}
    if not edgar:
        return {"tags": tags, "agree_ratio": None, "statement_trust": "U"}
    checked = agreed = 0
    for fact, fys in edgar.items():
        serie = raw.get(fact) or []
        if not fys or not serie or serie[0] is None:
            continue
        edgar_latest = fys[max(fys)]
        yf_latest = serie[0]
        if fact == "capex":  # yfinance lo riporta negativo
            yf_latest = abs(yf_latest)
            edgar_latest = abs(edgar_latest)
        checked += 1
        denom = max(abs(edgar_latest), 1.0)
        if abs(yf_latest - edgar_latest) / denom <= 0.01:
            agreed += 1
            tags[fact] = "P"
        elif abs(yf_latest - edgar_latest) / denom <= 0.05:
            tags[fact] = "V"  # concordi a meno di normalizzazioni minori
        else:
            tags[fact] = "U"  # conflitto material -> [U] + CS giu' (spec 6-bis C)
    ratio = agreed / checked if checked else None
    trust = "V" if checked >= 4 and ratio is not None and ratio >= 0.75 else "U"
    return {"tags": tags, "agree_ratio": ratio, "statement_trust": trust}
