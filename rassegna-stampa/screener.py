#!/usr/bin/env python3
"""
===============================================================================
MVF v3.0 — STOCK SCREENER (v2 — fully automated, zero file inputs)
===============================================================================

Costruisce l'universo AUTOMATICAMENTE via TradingView (60+ mercati globali).
Applica i criteri polarizzanti del prompt MVF v3.0.
Output JSON pronto per essere consumato da briefing.py.

NESSUN FILE DI INPUT RICHIESTO.

USO:
    python screener.py --region GLOBAL --strategy all --top 30
    python screener.py --region EU --strategy income
    python screener.py --region ASIA --strategy quality

DIPENDENZE:
    pip install tradingview-screener yfinance pandas numpy
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import warnings
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Any

import pandas as pd
import numpy as np
import yfinance as yf

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger("mvf_screener")

try:
    from tradingview_screener import Query, Column
    TV_OK = True
except ImportError:
    TV_OK = False
    log.warning("tradingview-screener non installato. pip install tradingview-screener")

try:
    from finvizfinance.screener.overview import Overview as FinvizOverview
    FINVIZ_OK = True
except ImportError:
    FINVIZ_OK = False


# =============================================================================
# SEZIONE 1 — CONFIGURAZIONE
# =============================================================================

CONFIG: dict[str, Any] = {
    "min_market_cap_million": 500,
    "min_price_usd": 1.0,
    "data_years": 5,
    "wacc_proxies": {
        "US": 0.085, "EU_core": 0.075, "IT": 0.090, "ES": 0.082,
        "UK": 0.085, "JP": 0.060, "EM": 0.105,
    },
    "rf_floor": 0.025,
    "g_terminal_max": 0.02,
    "g_perpetua_max": 0.04,
}

TV_MARKETS = {
    "US": ["america"],
    "EU": ["italy", "germany", "france", "spain", "netherlands",
           "switzerland", "uk", "sweden", "denmark", "norway",
           "finland", "belgium", "ireland", "austria", "portugal"],
    "ASIA": ["japan", "china", "hong_kong", "korea", "india",
             "singapore", "taiwan", "australia", "indonesia",
             "malaysia", "thailand"],
}
TV_MARKETS["GLOBAL"] = TV_MARKETS["US"] + TV_MARKETS["EU"] + TV_MARKETS["ASIA"]

# TradingView exchange prefix → yfinance suffix
TV_TO_YF_SUFFIX = {
    "BIT": ".MI", "XETR": ".DE", "FWB": ".F",
    "EURONEXT": ".PA", "AMEX": "", "NYSE": "", "NASDAQ": "",
    "LSE": ".L", "BME": ".MC", "AMS": ".AS",
    "EBS": ".SW", "SWX": ".SW",
    "TYO": ".T", "HKEX": ".HK", "KRX": ".KS",
    "NSE": ".NS", "BSE": ".BO", "SSE": ".SS", "SZSE": ".SZ",
    "SGX": ".SI", "ASX": ".AX",
    "OMXSTO": ".ST", "OMXCOP": ".CO", "OMXHEX": ".HE",
    "OSL": ".OL", "WBO": ".VI", "ELI": ".LS", "BVMF": ".SA",
}

SPECIAL_SECTORS = {
    "Financial Services": "bank_or_insurance",
    "Real Estate": "reit",
    "Utilities": "utility",
    "Energy": "cyclical",
    "Basic Materials": "cyclical",
    "Healthcare": "pharma_or_biotech",
}


# =============================================================================
# SEZIONE 2 — DATA CLASSES
# =============================================================================

@dataclass
class HardFilters:
    altman_z_below_1_23: bool = False
    fcf_negative_3y: bool = False
    debt_equity_above_3: bool = False
    net_margin_neg_2_of_3: bool = False
    goodwill_over_50_pct_equity: bool = False
    sbc_over_8_pct_revenue: bool = False


@dataclass
class SoftFilters:
    altman_z_grey_zone: bool = False
    fcf_negative_1_of_3: bool = False
    payout_above_100: bool = False
    revenue_decline_2y: bool = False
    roe_below_capm_r: bool = False
    accruals_above_0_10: bool = False
    ccr_below_0_5: bool = False
    share_dilution_above_3_pct: bool = False
    tax_rate_volatile_below_10: bool = False


@dataclass
class IntrinsicMetrics:
    gross_margin: Optional[float] = None
    ebitda_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    net_margin: Optional[float] = None
    fcf_margin: Optional[float] = None
    roic: Optional[float] = None
    roe: Optional[float] = None
    roa: Optional[float] = None
    debt_to_equity: Optional[float] = None
    debt_to_assets: Optional[float] = None
    altman_z: Optional[float] = None
    sbc_revenue: Optional[float] = None
    capex_revenue: Optional[float] = None
    capex_da: Optional[float] = None
    rd_revenue: Optional[float] = None
    dividend_yield: Optional[float] = None
    payout_ratio: Optional[float] = None
    dividend_growth_5y: Optional[float] = None
    buyback_yield: Optional[float] = None
    price_cagr_5y: Optional[float] = None
    tax_rate: Optional[float] = None
    accruals_ratio: Optional[float] = None
    cash_conversion_ratio: Optional[float] = None


@dataclass
class Candidate:
    ticker: str
    name: str
    sector: str
    industry: str
    market: str
    currency: str
    price: Optional[float]
    market_cap_million: Optional[float]
    pe_ratio: Optional[float]
    metrics: IntrinsicMetrics = field(default_factory=IntrinsicMetrics)
    hard_filters: HardFilters = field(default_factory=HardFilters)
    soft_filters: SoftFilters = field(default_factory=SoftFilters)
    strategy_tags: list[str] = field(default_factory=list)
    composite_score: Optional[float] = None
    notes: list[str] = field(default_factory=list)

    @property
    def passes_hard_filters(self) -> bool:
        return not any(asdict(self.hard_filters).values())

    @property
    def warning_count(self) -> int:
        return sum(asdict(self.soft_filters).values())


# =============================================================================
# SEZIONE 3 — UNIVERSE AUTO-BUILDER (zero file)
# =============================================================================

def tv_to_yf_ticker(tv_ticker: str) -> Optional[str]:
    """Converti 'BIT:ENI' -> 'ENI.MI', 'NASDAQ:NKLR' -> 'NKLR'."""
    if ":" not in tv_ticker:
        return tv_ticker
    exchange, symbol = tv_ticker.split(":", 1)
    suffix = TV_TO_YF_SUFFIX.get(exchange.upper())
    if suffix is None:
        return None
    return f"{symbol}{suffix}" if suffix else symbol


def build_universe_tradingview(region: str = "GLOBAL", min_mcap_m: int = 500,
                                min_price: float = 1.0, limit_per_market: int = 100,
                                sector_filter: Optional[str] = None) -> list[str]:
    """Auto-build universe da TradingView in formato yfinance."""
    if not TV_OK:
        log.error("tradingview-screener non installato.")
        return []
    markets = TV_MARKETS.get(region, ["america"])
    log.info("Universe TV: region=%s, mercati=%d", region, len(markets))

    all_tickers: list[str] = []
    failed = []

    # Spezza per regione per non saturare la query
    chunks = ([TV_MARKETS["US"], TV_MARKETS["EU"], TV_MARKETS["ASIA"]]
              if region == "GLOBAL" else [markets])

    for chunk in chunks:
        try:
            q = (Query()
                 .set_markets(*chunk)
                 .select("name", "close", "market_cap_basic",
                         "price_earnings_ttm", "sector", "dividends_yield")
                 .where(
                     Column("market_cap_basic") > min_mcap_m * 1_000_000,
                     Column("close") > min_price,
                 )
                 .order_by("market_cap_basic", ascending=False)
                 .limit(limit_per_market * len(chunk)))
            if sector_filter:
                q = q.where(Column("sector") == sector_filter)
            _count, df = q.get_scanner_data()
            if df is None or df.empty:
                continue
            for tv_tkr in df["ticker"].tolist():
                yf_tkr = tv_to_yf_ticker(tv_tkr)
                if yf_tkr is None:
                    failed.append(tv_tkr)
                    continue
                all_tickers.append(yf_tkr)
        except Exception as e:
            log.warning("TradingView query fallita per %s: %s", chunk, e)

    if failed:
        log.info("Exchange non mappati (skipped): %d (es. %s)",
                 len(failed), ", ".join(failed[:3]))
    deduped = list(dict.fromkeys(all_tickers))
    log.info("Universe finale: %d ticker unici", len(deduped))
    return deduped


def build_universe_finviz_fallback(min_mcap_m: int = 500,
                                    sector: Optional[str] = None,
                                    limit: int = 500) -> list[str]:
    """Fallback US-only se tradingview-screener non disponibile."""
    if not FINVIZ_OK:
        return []
    try:
        f = FinvizOverview()
        filters = {"Market Cap.": "+Small (over $300mln)", "Price": "Over $1"}
        if sector:
            filters["Sector"] = sector
        f.set_filter(filters_dict=filters)
        df = f.screener_view(order="Market Cap.", ascend=False, limit=limit)
        return df["Ticker"].tolist() if df is not None and not df.empty else []
    except Exception as e:
        log.error("finvizfinance error: %s", e)
        return []


# =============================================================================
# SEZIONE 4 — HELPERS yfinance
# =============================================================================

def safe_row(df: pd.DataFrame, row_name: str, col_index: int = 0) -> Optional[float]:
    if df is None or df.empty:
        return None
    aliases = {
        "Total Revenue": ["Total Revenue", "Revenue", "TotalRevenue"],
        "Gross Profit": ["Gross Profit", "GrossProfit"],
        "Operating Income": ["Operating Income", "OperatingIncome", "EBIT"],
        "Net Income": ["Net Income", "NetIncome", "Net Income Common Stockholders"],
        "EBITDA": ["EBITDA", "Normalized EBITDA"],
        "EBIT": ["EBIT", "Operating Income"],
        "Free Cash Flow": ["Free Cash Flow", "FreeCashFlow"],
        "Total Debt": ["Total Debt", "TotalDebt"],
        "Stockholders Equity": ["Stockholders Equity", "Common Stock Equity",
                                "Total Equity Gross Minority Interest"],
        "Total Assets": ["Total Assets", "TotalAssets"],
        "Current Assets": ["Current Assets", "Total Current Assets"],
        "Current Liabilities": ["Current Liabilities", "Total Current Liabilities"],
        "Retained Earnings": ["Retained Earnings", "RetainedEarnings"],
        "Total Liabilities": ["Total Liabilities Net Minority Interest", "Total Liab"],
        "Goodwill": ["Goodwill", "Goodwill And Other Intangible Assets"],
        "Stock Based Compensation": ["Stock Based Compensation"],
        "Capital Expenditure": ["Capital Expenditure", "CapitalExpenditure"],
        "Depreciation": ["Reconciled Depreciation", "Depreciation And Amortization", "Depreciation"],
        "Research Development": ["Research Development", "Research And Development"],
        "Tax Provision": ["Tax Provision", "Income Tax Expense"],
        "Pretax Income": ["Pretax Income", "Income Before Tax"],
        "Cash From Operations": ["Operating Cash Flow",
                                 "Cash Flow From Continuing Operating Activities"],
    }
    for key in aliases.get(row_name, [row_name]):
        try:
            if key in df.index:
                col = df.columns[col_index] if col_index < len(df.columns) else df.columns[-1]
                val = df.loc[key, col]
                if pd.notna(val):
                    return float(val)
        except Exception:
            continue
    return None


def history_series(df, row_name, n=3):
    if df is None or df.empty:
        return []
    aliases = {"Total Revenue": ["Total Revenue", "Revenue"],
               "Net Income": ["Net Income"], "Free Cash Flow": ["Free Cash Flow"]}
    for key in aliases.get(row_name, [row_name]):
        if key in df.index:
            return [float(v) for v in df.loc[key].head(n).tolist() if pd.notna(v)]
    return []


def detect_market(info):
    exchange = (info.get("exchange") or "").upper()
    country = (info.get("country") or "").upper()
    ccy = info.get("currency", "USD")
    if exchange in {"NYQ", "NMS", "NGM", "PCX", "ASE", "BTS"}:
        return "US", ccy
    if exchange == "LSE":
        return "UK", ccy
    if exchange in {"MIL", "BIT"}:
        return "IT", ccy
    if exchange in {"PAR", "AMS", "EBS", "EBR"}:
        return "EU_core", ccy
    if exchange == "MCE":
        return "ES", ccy
    if exchange in {"TYO", "JPX"}:
        return "JP", ccy
    if "ITALY" in country:
        return "IT", ccy
    return "EU_core", ccy


def compute_altman_z(bs, fin, mc):
    try:
        wc = (safe_row(bs, "Current Assets") or 0) - (safe_row(bs, "Current Liabilities") or 0)
        ta = safe_row(bs, "Total Assets")
        re_ = safe_row(bs, "Retained Earnings") or 0
        ebit = safe_row(fin, "EBIT") or safe_row(fin, "Operating Income")
        tl = safe_row(bs, "Total Liabilities")
        if tl is None and ta:
            tl = ta - (safe_row(bs, "Stockholders Equity") or 0)
        rev = safe_row(fin, "Total Revenue")
        if not all([ta, ebit, mc, tl, rev]) or ta == 0 or tl == 0:
            return None
        return (1.2 * wc / ta + 1.4 * re_ / ta + 3.3 * ebit / ta
                + 0.6 * mc / tl + 1.0 * rev / ta)
    except Exception:
        return None


def compute_dividend_growth(dividends, years=5):
    if dividends is None or dividends.empty:
        return None
    annual = dividends.groupby(dividends.index.year).sum()
    if len(annual) < 3:
        return None
    n = min(years, len(annual) - 1)
    first, last = annual.iloc[-n - 1], annual.iloc[-1]
    if first <= 0 or last <= 0:
        return None
    return (last / first) ** (1 / n) - 1


def compute_price_cagr(history, years=5):
    if history is None or history.empty:
        return None
    end = history["Close"].iloc[-1]
    cutoff = history.index[-1] - timedelta(days=years * 365)
    earlier = history[history.index >= cutoff]
    if earlier.empty:
        return None
    start = earlier["Close"].iloc[0]
    if start <= 0:
        return None
    actual = (history.index[-1] - earlier.index[0]).days / 365
    if actual < 1:
        return None
    return (end / start) ** (1 / actual) - 1


def compute_accruals(fin, bs, cf):
    ni = safe_row(fin, "Net Income")
    cfo = safe_row(cf, "Cash From Operations")
    ta1 = safe_row(bs, "Total Assets", 0)
    ta2 = safe_row(bs, "Total Assets", 1)
    if not all([ni is not None, cfo is not None, ta1, ta2]):
        return None
    avg = (ta1 + ta2) / 2
    return (ni - cfo) / avg if avg else None


# =============================================================================
# SEZIONE 5 — CALCOLO METRICHE
# =============================================================================

def fetch_data(ticker):
    try:
        t = yf.Ticker(ticker)
        info = t.info or {}
        if not info or info.get("marketCap") is None:
            return None
        return {"ticker": ticker, "info": info,
                "financials": t.financials, "balance_sheet": t.balance_sheet,
                "cashflow": t.cashflow, "dividends": t.dividends,
                "history": t.history(period="5y", auto_adjust=True),
                "earnings_dates": getattr(t, "earnings_dates", None)}
    except Exception:
        return None


def compute_metrics(data):
    info, fin, bs, cf = data["info"], data["financials"], data["balance_sheet"], data["cashflow"]
    m = IntrinsicMetrics()
    inter = {}
    rev = safe_row(fin, "Total Revenue")
    if rev and rev > 0:
        gp = safe_row(fin, "Gross Profit");          m.gross_margin = gp / rev if gp is not None else None
        eb = safe_row(fin, "EBITDA");                m.ebitda_margin = eb / rev if eb is not None else None
        oi = safe_row(fin, "Operating Income");      m.operating_margin = oi / rev if oi is not None else None
        ni = safe_row(fin, "Net Income");            m.net_margin = ni / rev if ni is not None else None
        fcf = safe_row(cf, "Free Cash Flow");        m.fcf_margin = fcf / rev if fcf is not None else None
        sbc = safe_row(cf, "Stock Based Compensation"); m.sbc_revenue = abs(sbc) / rev if sbc is not None else None
        cx = safe_row(cf, "Capital Expenditure");    m.capex_revenue = abs(cx) / rev if cx is not None else None
        rd = safe_row(fin, "Research Development"); m.rd_revenue = rd / rev if rd is not None else None
        tax = safe_row(fin, "Tax Provision");        ebt = safe_row(fin, "Pretax Income")
        if tax is not None and ebt and ebt > 0:
            m.tax_rate = tax / ebt
        if oi is not None and tax is not None and ebt and ebt > 0:
            nopat = oi * (1 - tax / ebt)
            eq_v = safe_row(bs, "Stockholders Equity") or 0
            d_v = safe_row(bs, "Total Debt") or 0
            inv = eq_v + d_v
            if inv > 0:
                m.roic = nopat / inv
    ni = safe_row(fin, "Net Income")
    eq = safe_row(bs, "Stockholders Equity")
    ta = safe_row(bs, "Total Assets")
    if ni is not None and eq and eq > 0:
        m.roe = ni / eq
    if ni is not None and ta and ta > 0:
        m.roa = ni / ta
    debt = safe_row(bs, "Total Debt")
    if debt is not None and eq and eq > 0:
        m.debt_to_equity = debt / eq
    if debt is not None and ta and ta > 0:
        m.debt_to_assets = debt / ta
    mc = info.get("marketCap")
    if mc:
        m.altman_z = compute_altman_z(bs, fin, mc)
    capex = safe_row(cf, "Capital Expenditure")
    da = safe_row(cf, "Depreciation")
    if capex is not None and da and da > 0:
        m.capex_da = abs(capex) / da
    m.dividend_yield = info.get("dividendYield")
    m.payout_ratio = info.get("payoutRatio")
    m.dividend_growth_5y = compute_dividend_growth(data["dividends"])
    sh_now = info.get("sharesOutstanding")
    sh_old = info.get("floatShares")
    if sh_now and sh_old and sh_old > sh_now:
        m.buyback_yield = (sh_old - sh_now) / sh_old
    m.price_cagr_5y = compute_price_cagr(data["history"])
    m.accruals_ratio = compute_accruals(fin, bs, cf)
    cfo = safe_row(cf, "Cash From Operations")
    if cfo is not None and ni and ni > 0:
        m.cash_conversion_ratio = cfo / ni
    inter["goodwill"] = safe_row(bs, "Goodwill") or 0
    inter["equity"] = eq
    inter["net_income_series"] = history_series(fin, "Net Income", 3)
    inter["revenue_series"] = history_series(fin, "Total Revenue", 3)
    inter["fcf_series"] = history_series(cf, "Free Cash Flow", 3)
    inter["sector"] = info.get("sector", "")
    inter["shares_change_pct"] = ((sh_now - sh_old) / sh_old) if (sh_now and sh_old) else None
    return m, inter


# =============================================================================
# SEZIONE 6 — RED FLAG MVF Sez. 8
# =============================================================================

def apply_hard_filters(m, inter, special):
    hf = HardFilters()
    if special not in {"bank_or_insurance", "reit"}:
        if m.altman_z is not None and m.altman_z < 1.23:
            hf.altman_z_below_1_23 = True
    fcf_s = inter.get("fcf_series", [])
    if len(fcf_s) >= 3 and all(v < 0 for v in fcf_s[:3]):
        hf.fcf_negative_3y = True
    if special != "bank_or_insurance":
        if m.debt_to_equity is not None and m.debt_to_equity > 3.0:
            hf.debt_equity_above_3 = True
    ni_s = inter.get("net_income_series", [])
    rev_s = inter.get("revenue_series", [])
    if len(ni_s) >= 3 and len(rev_s) >= 3:
        nm = [ni / r if r > 0 else 0 for ni, r in zip(ni_s, rev_s)]
        if sum(1 for v in nm[:3] if v < 0) >= 2:
            hf.net_margin_neg_2_of_3 = True
    gw = inter.get("goodwill", 0)
    eq = inter.get("equity")
    if gw and eq and eq > 0 and gw / eq > 0.5:
        hf.goodwill_over_50_pct_equity = True
    s = inter.get("sector", "")
    if ("Tech" in s or "Software" in s) and m.sbc_revenue and m.sbc_revenue > 0.08:
        hf.sbc_over_8_pct_revenue = True
    return hf


def apply_soft_filters(m, inter, wacc):
    sf = SoftFilters()
    if m.altman_z is not None and 1.23 <= m.altman_z <= 1.81:
        sf.altman_z_grey_zone = True
    fcf_s = inter.get("fcf_series", [])
    if len(fcf_s) >= 3 and sum(1 for v in fcf_s[:3] if v < 0) == 1:
        sf.fcf_negative_1_of_3 = True
    if m.payout_ratio is not None and m.payout_ratio > 1.0:
        sf.payout_above_100 = True
    rev_s = inter.get("revenue_series", [])
    if len(rev_s) >= 3 and rev_s[0] < rev_s[1] < rev_s[2]:
        sf.revenue_decline_2y = True
    if m.roe is not None and m.roe < wacc:
        sf.roe_below_capm_r = True
    if m.accruals_ratio is not None and m.accruals_ratio > 0.10:
        sf.accruals_above_0_10 = True
    if m.cash_conversion_ratio is not None and m.cash_conversion_ratio < 0.5:
        sf.ccr_below_0_5 = True
    ch = inter.get("shares_change_pct")
    if ch is not None and ch > 0.03:
        sf.share_dilution_above_3_pct = True
    if m.tax_rate is not None and m.tax_rate < 0.10:
        sf.tax_rate_volatile_below_10 = True
    return sf


# =============================================================================
# SEZIONE 7 — TILT STRATEGICI
# =============================================================================

def tag_strategy(cand, hist, earnings_dates):
    tags = []
    m = cand.metrics
    if (m.dividend_yield and m.dividend_yield > 0.04
            and m.payout_ratio is not None and m.payout_ratio < 0.80
            and cand.pe_ratio is not None and cand.pe_ratio < 18
            and m.net_margin is not None and m.net_margin > 0.05
            and (m.debt_to_equity is None or m.debt_to_equity < 1.5)):
        tags.append("income")
    if earnings_dates is not None and not earnings_dates.empty and hist is not None:
        try:
            ed = (earnings_dates.dropna(subset=["Surprise(%)"])
                  if "Surprise(%)" in earnings_dates.columns else None)
            if ed is not None and not ed.empty:
                last = ed.iloc[0]
                surp = last.get("Surprise(%)")
                date = last.name
                if surp is not None and abs(surp) > 5:
                    cutoff = pd.Timestamp(date).tz_localize(None) if hasattr(date, "tz_localize") else pd.Timestamp(date)
                    h2 = hist.copy()
                    h2.index = h2.index.tz_localize(None) if h2.index.tz else h2.index
                    post = h2[h2.index >= cutoff]
                    if len(post) >= 5:
                        move = (post["Close"].iloc[min(4, len(post)-1)] - post["Close"].iloc[0]) / post["Close"].iloc[0]
                        if surp > 5 and abs(move) < 0.03:
                            tags.append("post_news_bull")
                        elif surp < -5 and abs(move) < 0.03:
                            tags.append("post_news_bear")
        except Exception:
            pass
    if (m.operating_margin and m.operating_margin > 0.15 and m.roic and m.roic > 0.12
            and (m.debt_to_equity is None or m.debt_to_equity < 1.0)
            and cand.warning_count <= 1):
        tags.append("quality")
    return tags


def compute_composite_score(c):
    weights = {
        "gross_margin": (15, 0.5), "operating_margin": (25, 0.20),
        "net_margin": (18, 0.10), "fcf_margin": (22, 0.10),
        "roic": (15, 0.15), "roe": (3, 0.15), "roa": (5, 0.10),
        "dividend_yield": (16, 0.04), "buyback_yield": (5, 0.03),
        "price_cagr_5y": (5, 0.10),
    }
    tw = ts = 0
    for name, (w, target) in weights.items():
        v = getattr(c.metrics, name)
        if v is None:
            continue
        s = min(max(v / target, 0), 2) / 2
        ts += w * s
        tw += w
    if tw == 0:
        return 0.0
    raw = ts / tw * 100 - c.warning_count * 3
    return round(max(0, min(100, raw)), 1)


# =============================================================================
# SEZIONE 8 — PIPELINE
# =============================================================================

def screen_ticker(ticker):
    data = fetch_data(ticker)
    if data is None:
        return None
    info = data["info"]
    mc = info.get("marketCap")
    if not mc or mc < CONFIG["min_market_cap_million"] * 1e6:
        return None
    price = info.get("currentPrice") or info.get("regularMarketPrice")
    if price is None or price < CONFIG["min_price_usd"]:
        return None
    market, ccy = detect_market(info)
    sector = info.get("sector", "")
    special = SPECIAL_SECTORS.get(sector)
    m, inter = compute_metrics(data)
    hard = apply_hard_filters(m, inter, special)
    wacc = CONFIG["wacc_proxies"].get(market, 0.08)
    soft = apply_soft_filters(m, inter, wacc)
    c = Candidate(
        ticker=ticker, name=info.get("longName") or info.get("shortName") or ticker,
        sector=sector, industry=info.get("industry", ""),
        market=market, currency=ccy, price=price,
        market_cap_million=mc / 1e6, pe_ratio=info.get("trailingPE"),
        metrics=m, hard_filters=hard, soft_filters=soft,
    )
    c.strategy_tags = tag_strategy(c, data["history"], data["earnings_dates"])
    c.composite_score = compute_composite_score(c)
    if special:
        c.notes.append(f"settore speciale: {special} (vedi MVF v3.0 Sez. 9)")
    return c


def screen_universe(tickers, strategy="all", max_workers=30):
    from concurrent.futures import ThreadPoolExecutor, as_completed
    out = []
    n = len(tickers)
    log.info("Screening su %d ticker (workers=%d)...", n, max_workers)
    done = 0
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(screen_ticker, t): t for t in tickers}
        for fut in as_completed(futures):
            done += 1
            if done % 50 == 0:
                log.info("  elaborati %d/%d", done, n)
            try:
                c = fut.result(timeout=20)
            except Exception:
                continue
            if c is None or not c.passes_hard_filters:
                continue
            if strategy != "all":
                if not any(tag.startswith(strategy) for tag in c.strategy_tags):
                    continue
            out.append(c)
    return out


def output_results(cands, out_dir, top_n=30):
    cands.sort(key=lambda c: c.composite_score or 0, reverse=True)
    top = cands[:top_n]
    rows = []
    for c in top:
        rows.append({
            "ticker": c.ticker, "name": c.name, "sector": c.sector,
            "industry": c.industry, "market": c.market, "price": c.price,
            "market_cap_M": round(c.market_cap_million, 0) if c.market_cap_million else None,
            "pe": round(c.pe_ratio, 2) if c.pe_ratio else None,
            "composite_score": c.composite_score,
            "tags": ",".join(c.strategy_tags),
            "warnings": c.warning_count,
            "div_yield": round(c.metrics.dividend_yield, 4) if c.metrics.dividend_yield else None,
            "payout": round(c.metrics.payout_ratio, 3) if c.metrics.payout_ratio else None,
            "fcf_margin": round(c.metrics.fcf_margin, 3) if c.metrics.fcf_margin else None,
            "roic": round(c.metrics.roic, 3) if c.metrics.roic else None,
            "altman_z": round(c.metrics.altman_z, 2) if c.metrics.altman_z else None,
            "ccr": round(c.metrics.cash_conversion_ratio, 2) if c.metrics.cash_conversion_ratio else None,
            "debt_equity": round(c.metrics.debt_to_equity, 2) if c.metrics.debt_to_equity else None,
        })
    df = pd.DataFrame(rows)
    out_dir.mkdir(parents=True, exist_ok=True)
    date_tag = datetime.now().strftime("%Y-%m-%d")
    csv_path = out_dir / f"screener_{date_tag}.csv"
    json_path = out_dir / f"screener_{date_tag}.json"
    df.to_csv(csv_path, index=False)
    payload = {
        "date": date_tag, "n_screened": len(cands), "n_passing": len(top),
        "candidates": [{
            "ticker": c.ticker, "name": c.name, "sector": c.sector,
            "market": c.market, "tags": c.strategy_tags, "score": c.composite_score,
            "metrics": {k: v for k, v in asdict(c.metrics).items() if v is not None},
            "warnings": [k for k, v in asdict(c.soft_filters).items() if v],
            "notes": c.notes,
        } for c in top],
    }
    with open(json_path, "w") as f:
        json.dump(payload, f, indent=2, default=str)
    return csv_path, json_path


# =============================================================================
# SEZIONE 9 — CLI
# =============================================================================

def main():
    p = argparse.ArgumentParser(description="MVF v3.0 Stock Screener (auto-universe)")
    p.add_argument("--region", choices=["US", "EU", "ASIA", "GLOBAL"], default="GLOBAL")
    p.add_argument("--strategy", choices=["income", "post_news", "quality", "all"], default="all")
    p.add_argument("--min-mcap", type=int, default=CONFIG["min_market_cap_million"])
    p.add_argument("--top", type=int, default=30)
    p.add_argument("--limit-per-market", type=int, default=100)
    p.add_argument("--sector", default=None)
    p.add_argument("--output", type=Path, default=Path("./data/screener_results"))
    args = p.parse_args()

    CONFIG["min_market_cap_million"] = args.min_mcap

    tickers = build_universe_tradingview(
        region=args.region, min_mcap_m=args.min_mcap,
        min_price=CONFIG["min_price_usd"],
        limit_per_market=args.limit_per_market,
        sector_filter=args.sector,
    )
    if not tickers and args.region == "US" and FINVIZ_OK:
        log.warning("Tentativo fallback finvizfinance...")
        tickers = build_universe_finviz_fallback(args.min_mcap, args.sector, args.limit_per_market)
    if not tickers:
        log.error("Universe vuoto.")
        sys.exit(1)

    cands = screen_universe(tickers, strategy=args.strategy)
    log.info("Candidati che passano filtri: %d", len(cands))
    csv_path, json_path = output_results(cands, args.output, top_n=args.top)
    log.info("Output: %s | %s", csv_path, json_path)


if __name__ == "__main__":
    main()
