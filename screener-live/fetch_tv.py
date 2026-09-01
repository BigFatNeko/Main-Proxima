"""Percorso dati NON-US via TradingView scanner (fonte aggregatore globale).

TradingView copre tutti i mercati (IT/DE/FR/UK/CH/JP/KR/TW/HK...) e da questo
IP risponde. Fornisce fondamentali CORRENTI (TTM/FQ) ma non le serie storiche
complete -> per i non-US si produce un MVF-S PARZIALE DICHIARATO ("snapshot").

DIP (spec Sez. 6-bis C): TradingView e' un AGGREGATORE. Un dato e' [V] solo se
un secondo aggregatore indipendente (yfinance) concorda dopo normalizzazione;
con la sola TradingView il tag e' [U]. La cross-validation con yfinance si
attiva quando yfinance e' raggiungibile (VPS di produzione); qui yfinance e'
rate-limited, quindi i non-US restano [U] finche' non arriva la seconda fonte.
"""
from __future__ import annotations

import logging

import requests as std_requests

log = logging.getLogger("fetch_tv")

# suffisso yfinance -> (endpoint scanner TradingView, prefisso borsa)
TV_MAP = {
    ".MI": ("italy", "MIL"), ".DE": ("germany", "XETR"), ".F": ("germany", "FWB"),
    ".PA": ("france", "EURONEXT"), ".AS": ("netherlands", "EURONEXT"),
    ".BR": ("belgium", "EURONEXT"), ".MC": ("spain", "BME"),
    ".L": ("uk", "LSE"), ".SW": ("switzerland", "SIX"),
    ".ST": ("sweden", "OMXSTO"), ".OL": ("norway", "OSL"),
    ".CO": ("denmark", "OMXCOP"), ".HE": ("finland", "OMXHEX"),
    ".VI": ("austria", "VIE"), ".LS": ("portugal", "EURONEXT"),
    ".IR": ("ireland", "EURONEXT"), ".T": ("japan", "TSE"),
    ".KS": ("korea", "KRX"), ".KQ": ("korea", "KRX"),
    ".TW": ("taiwan", "TWSE"), ".HK": ("hongkong", "HKEX"),
    ".SS": ("china", "SSE"), ".SZ": ("china", "SZSE"),
    ".TO": ("canada", "TSX"), ".AX": ("australia", "ASX"),
}
COUNTRY_MARKET = {   # endpoint TV -> codice mercato interno (config.MARKET_PARAMS)
    "italy": "IT", "germany": "EU_core", "france": "EU_core",
    "netherlands": "EU_core", "belgium": "EU_core", "spain": "ES",
    "uk": "UK", "switzerland": "CH", "sweden": "EU_core", "norway": "EU_core",
    "denmark": "EU_core", "finland": "EU_core", "austria": "EU_core",
    "portugal": "EU_core", "ireland": "EU_core", "japan": "JP",
    "korea": "KR", "taiwan": "TW", "hongkong": "CN", "china": "CN",
    "canada": "CA", "australia": "AU",
}
COUNTRY_NAME = {  # per il campo info["country"] (ritenute fiscali, pacchetti)
    "italy": "Italy", "germany": "Germany", "france": "France",
    "netherlands": "Netherlands", "belgium": "Belgium", "spain": "Spain",
    "uk": "United Kingdom", "switzerland": "Switzerland", "sweden": "Sweden",
    "norway": "Norway", "denmark": "Denmark", "finland": "Finland",
    "austria": "Austria", "portugal": "Portugal", "ireland": "Ireland",
    "japan": "Japan", "korea": "South Korea", "taiwan": "Taiwan",
    "hongkong": "Hong Kong", "china": "China", "canada": "Canada",
    "australia": "Australia",
}

COLS = ["name", "close", "currency", "market_cap_basic", "sector", "industry",
        "gross_margin_ttm", "operating_margin_ttm", "net_margin_ttm",
        "free_cash_flow_margin_ttm", "return_on_equity",
        "return_on_invested_capital", "return_on_assets", "debt_to_equity",
        "price_earnings_ttm", "dividend_yield_recent", "dividends_per_share_fq",
        "dividend_payout_ratio_ttm", "earnings_per_share_diluted_yoy_growth_ttm",
        "total_revenue_yoy_growth_ttm", "free_cash_flow_ttm", "total_revenue_ttm",
        "total_debt", "cash_n_short_term_invest_fq", "beta_1_year",
        "research_and_dev_ratio_ttm"]


def _resolve(ticker: str):
    for suf, (country, prefix) in TV_MAP.items():
        if ticker.upper().endswith(suf):
            base = ticker[:-len(suf)]
            return country, prefix, base
    return None, None, None


def fetch_tv(ticker: str) -> dict | None:
    """Assembla `raw` (forma fetch_yf) dai fondamentali correnti TradingView.
    Serie a 1 elemento (snapshot): trend neutro, crescite via override YoY.
    None se il mercato non e' mappato o il titolo non e' trovato."""
    country, prefix, base = _resolve(ticker)
    if not country:
        return None
    body = {"symbols": {"tickers": [f"{prefix}:{base}"], "query": {"types": []}},
            "columns": COLS}
    try:
        r = std_requests.post(f"https://scanner.tradingview.com/{country}/scan",
                              json=body, timeout=20)
        if r.status_code != 200 or not r.json().get("data"):
            log.debug("TV %s -> %s", ticker, r.status_code)
            return None
        vals = dict(zip(COLS, r.json()["data"][0]["d"]))
    except Exception as e:
        log.debug("TV %s errore: %s", ticker, str(e)[:80])
        return None

    def g(k):
        v = vals.get(k)
        return float(v) if isinstance(v, (int, float)) else None

    rev = g("total_revenue_ttm")
    price = g("close")
    mcap = g("market_cap_basic")
    pe = g("price_earnings_ttm")
    de = g("debt_to_equity")
    debt = g("total_debt")
    nm = g("net_margin_ttm")
    roa = g("return_on_assets")

    # ricostruzione delle voci di bilancio dalle percentuali TV (1 anno)
    def marg(mkey):
        m = g(mkey)
        return [m / 100 * rev] if (m is not None and rev) else []
    net_income = marg("net_margin_ttm")
    equity = [debt / de] if (debt and de and de > 0) else []
    total_assets = ([net_income[0] / (roa / 100)] if (net_income and roa) else [])
    eps = [price / pe] if (price and pe and pe > 0) else []
    shares = [mcap / price] if (mcap and price) else []
    dps_fq = g("dividends_per_share_fq")

    info = {
        "symbol": ticker, "shortName": vals.get("name") or base,
        "longName": vals.get("name") or base,
        "sector": vals.get("sector") or "", "industry": vals.get("industry") or "",
        "country": COUNTRY_NAME.get(country, ""), "currency": vals.get("currency") or "",
        "currentPrice": price, "regularMarketPrice": price,
        "beta": g("beta_1_year"), "marketCap": mcap, "trailingPE": pe,
        "sharesOutstanding": shares[0] if shares else None,
    }
    raw = {
        "ticker": ticker, "info": info,
        "revenue": [rev] if rev else [], "gross_profit": marg("gross_margin_ttm"),
        "operating_income": marg("operating_margin_ttm"), "ebit": marg("operating_margin_ttm"),
        "ebitda": [], "net_income": net_income, "pretax_income": [],
        "tax_provision": [], "diluted_eps": eps,
        "interest_expense": [], "rd": [], "da_income": [], "da_cf": [],
        "total_assets": total_assets, "equity": equity,
        "total_debt": [debt] if debt else [], "cash": [g("cash_n_short_term_invest_fq")],
        "current_assets": [], "current_liab": [], "total_liab": [], "retained": [],
        "working_capital": [], "goodwill": [], "shares": shares,
        "cfo": [], "capex": [], "fcf_yf": [g("free_cash_flow_ttm")],
        "sbc": [], "dividends_paid": [], "buyback_cf": [],
        "dividends_series": {"2025-07-01": dps_fq * 4} if dps_fq else {},
        "prices": {}, "_source": "tradingview",
        # override diretti (metriche che TV da' pronte, non ricavabili da 1 anno)
        "_tv_direct": {
            "C6": g("earnings_per_share_diluted_yoy_growth_ttm"),
            "C8_roic": g("return_on_invested_capital"),
            "C9_roe": g("return_on_equity"),
            "C10_roa": roa,
            "C20_payout": (g("dividend_payout_ratio_ttm") or 0) / 100 or None,
            "C19_yield": g("dividend_yield_recent"),
        },
    }
    return raw
