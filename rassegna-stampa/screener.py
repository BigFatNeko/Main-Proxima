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

# MVF v3.0 — modulo valutazione finanziaria
try:
    from . import mvf_valuation as mvf
    from . import filiere_screener as filiere_mod
except ImportError:
    import mvf_valuation as mvf
    import filiere_screener as filiere_mod

try:
    from finvizfinance.screener.overview import Overview as FinvizOverview
    FINVIZ_OK = True
except ImportError:
    FINVIZ_OK = False


# =============================================================================
# SEZIONE 1 — CONFIGURAZIONE
# =============================================================================

CONFIG: dict[str, Any] = {
    "min_market_cap_million": 300,   # abbassato da 500 → include small-cap 300M+
    "min_price_usd": 0.50,           # abbassato da 1.0 → cattura azioni < 1$ in EM
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
           "finland", "belgium", "ireland", "austria", "portugal",
           "poland", "turkey", "greece", "hungary", "czech_republic"],
    "ASIA": ["japan", "china", "hong_kong", "korea", "india",
             "singapore", "taiwan", "australia", "indonesia",
             "malaysia", "thailand", "vietnam", "philippines", "new_zealand"],
    "LATAM": ["brazil", "mexico", "chile", "colombia", "argentina"],
    "AFRICA_ME": ["south_africa", "saudi_arabia", "israel", "uae"],
}
TV_MARKETS["GLOBAL"] = (TV_MARKETS["US"] + TV_MARKETS["EU"] + TV_MARKETS["ASIA"]
                        + TV_MARKETS["LATAM"] + TV_MARKETS["AFRICA_ME"])

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
    # EM / frontier additions
    "WSE": ".WA",     # Poland Warsaw
    "BIST": ".IS",    # Turkey Istanbul
    "BMV": ".MX",     # Mexico
    "JSE": ".JO",     # South Africa
    "TASE": ".TA",    # Israel
    "TADAWUL": ".SR", # Saudi Arabia
    "NZX": ".NZ",     # New Zealand
    "SET": ".BK",     # Thailand Bangkok
    "IDX": ".JK",     # Indonesia
    "PSE": ".PSE",    # Philippines
    "HNX": ".HN",     # Vietnam Hanoi
    "HOSE": ".VN",    # Vietnam Ho Chi Minh
    "BCS": ".BA",     # Argentina Buenos Aires
    "BVL": ".LM",     # Peru Lima (bonus)
    "BCS_CL": ".SN",  # Chile Santiago
    "COLCAP": ".CL",  # Colombia
    "ATHEX": ".AT",   # Greece Athens
    "BUX": ".BD",     # Hungary Budapest
    "PSE_CZ": ".PR",  # Czech Republic Prague
    "DFM": ".DU",     # UAE Dubai
}

SPECIAL_SECTORS = {
    "Financial Services": "bank_or_insurance",
    "Real Estate": "reit",
    "Utilities": "utility",
    "Energy": "cyclical",
    "Basic Materials": "cyclical",
    "Healthcare": "pharma_or_biotech",
}

# Tier 2 — Speculative / Catalyst universe
SPEC_MIN_MCAP_M = 5        # $5M minimum (includes micro/nano-cap)
SPEC_MAX_MCAP_M = 500      # $500M maximum (small-cap ceiling)
SPEC_MIN_PRICE  = 0.10     # penny stock floor
SPEC_MAX_TV_PER_CHUNK = 300   # TV rows per chunk for speculative query

FILIERE_STRATEGIC: dict[str, str] = {
    "Semiconductors": "chip",
    "Semiconductor Equipment & Materials": "chip",
    "Electronic Components": "chip",
    "Oil & Gas Integrated": "energia",
    "Oil & Gas E&P": "energia",
    "Oil & Gas Midstream": "energia",
    "Oil & Gas Refining & Marketing": "energia",
    "Oil & Gas Equipment & Services": "energia",
    "Uranium": "uranio",
    "Aerospace & Defense": "difesa",
    "Waste Management": "gestione_rifiuti",
    "Environmental & Waste Services": "gestione_rifiuti",
    "Pollution & Treatment Controls": "gestione_rifiuti",
    "Food Distribution": "consumer_staples",
    "Packaged Foods": "consumer_staples",
    "Household & Personal Products": "consumer_staples",
    "Beverages—Non-Alcoholic": "consumer_staples",
    "Tobacco": "consumer_staples",
    "Industrial Metals & Mining": "rare_earth_metalli",
    "Other Precious Metals & Mining": "rare_earth_metalli",
    "Specialty Chemicals": "rare_earth_metalli",
    "Copper": "rare_earth_metalli",
    "Lithium & Battery Tech": "batterie_litio",
    "Auto Parts": "batterie_litio",
    "Electrical Equipment & Parts": "batterie_litio",
    "Industrial Distribution": "helium_gas_industriali",
}

# ETF per Market Context Layer (settori US + regioni globali + macro)
SECTOR_ETFS: dict[str, str] = {
    "US_Tech": "XLK", "US_Energy": "XLE", "US_Finance": "XLF",
    "US_Healthcare": "XLV", "US_Industrial": "XLI", "US_ConsStaples": "XLP",
    "US_ConsDisc": "XLY", "US_CommSvc": "XLC", "US_RealEstate": "XLRE",
    "US_Utilities": "XLU", "US_Materials": "XLB",
}
REGIONAL_ETFS: dict[str, str] = {
    "EuroStoxx": "FEZ", "UK": "EWU", "Germany": "EWG", "Italy": "EWI",
    "Japan": "EWJ", "China": "FXI", "India": "INDA", "Korea": "EWY",
    "EM_Broad": "VWO", "Brazil": "EWZ", "Australia": "EWA",
    "LatAm": "ILF", "EMEA": "EEMEA",
}
MACRO_INDICATORS: dict[str, str] = {
    "10Y_UST": "^TNX", "2Y_UST": "^IRX", "VIX": "^VIX",
    "Gold": "GC=F", "Oil_Brent": "BZ=F", "Dollar_Index": "DX-Y.NYB",
    "Copper": "HG=F", "IG_Credit": "LQD",
    # Indici principali per strip mercato nel briefing
    "SP500": "^GSPC", "FTSE_MIB": "FTSEMIB.MI", "Nikkei": "^N225", "EURUSD": "EURUSD=X",
}

# Tier 2 — Speculative / Catalyst universe
SPEC_MIN_MCAP_M = 5
SPEC_MAX_MCAP_M = 500
SPEC_MIN_PRICE  = 0.10
SPEC_MAX_TV_PER_CHUNK = 600   # alzato da 300 → più copertura small-cap


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
    # Valuation multiples (nuovi — per confronto inter-mercato)
    ev_ebitda: Optional[float] = None      # EV/EBITDA: <8 eccellente, >20 caro
    fcf_yield: Optional[float] = None      # FCF/Market cap: >8% forte
    pb_ratio: Optional[float] = None       # Price/Book: <1 sotto book
    ps_ratio: Optional[float] = None       # Price/Sales: <1 value, >5 caro


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
    piotroski_f: Optional[int] = None
    piotroski_factors: list[str] = field(default_factory=list)
    moat_score: Optional[float] = None
    moat_signals: list[str] = field(default_factory=list)
    dcf_upside_pct: Optional[float] = None
    filiera_tag: Optional[str] = None
    earnings_acceleration: Optional[float] = None
    # MVF v4.1 — valutazione completa
    instrument_class: str = "common"        # STEP 0 routing (Sez. 2)
    instrument_base: int = 280
    mvf_vote_1000: Optional[float] = None   # voto su base per classe, /1000
    mvf_vote_100: Optional[float] = None    # compat v3.0: voto/10
    mvf_engine_note: str = ""               # motivo se il motore non e' disponibile
    mvf_valuation: Optional[dict] = None
    mvf_red_flags: Optional[dict] = None
    quality_gates: Optional[dict] = None    # G1-G6 (Sez. 8-bis)
    iqi_score: Optional[dict] = None        # IQI -> guida il MoS (Sez. 7)
    mvf_iqi_reconciliation: Optional[dict] = None
    net_yield: Optional[dict] = None        # netto HOME vs ITALIA (Sez. 7)
    confidence_score: Optional[dict] = None
    variation_5y: Optional[dict] = None
    sector_median_pe: Optional[float] = None
    # Display fields per briefing (sintesi)
    intrinsic_value: Optional[float] = None
    relative_value_summary: Optional[dict] = None
    ideal_purchase_price_mos: Optional[float] = None
    margin_of_safety_pct: Optional[float] = None

    @property
    def passes_hard_filters(self) -> bool:
        return not any(asdict(self.hard_filters).values())

    @property
    def warning_count(self) -> int:
        return sum(asdict(self.soft_filters).values())


@dataclass
class CatalystSignals:
    volume_spike_3d: bool = False       # 3-day avg vol > 3× 30-day avg vol
    volume_spike_30d: bool = False      # 30-day avg vol > 2× 90-day avg vol
    momentum_30d_strong: bool = False   # price +20% in 30 days
    momentum_90d_strong: bool = False   # price +40% in 90 days
    near_52w_low: bool = False          # within 15% of 52-week low (coiled)
    revenue_acceleration: bool = False  # latest YoY revenue growth > prior year
    earnings_beat: bool = False         # last earnings surprise > 10%
    high_short_float: bool = False      # short float > 20% (squeeze potential)
    cash_rich: bool = False             # cash/market_cap > 0.50
    low_float: bool = False             # float shares < 10M (thin float)


@dataclass
class SpeculativeCandidate:
    ticker: str
    name: str
    sector: str
    industry: str
    market: str
    price: Optional[float]
    market_cap_million: Optional[float]
    signals: CatalystSignals = field(default_factory=CatalystSignals)
    signal_count: int = 0
    signal_labels: list[str] = field(default_factory=list)
    price_change_30d: Optional[float] = None
    price_change_90d: Optional[float] = None
    volume_ratio_3d: Optional[float] = None   # 3d avg vs 30d avg
    revenue_growth_yoy: Optional[float] = None
    short_float: Optional[float] = None
    speculative_score: float = 0.0
    notes: list[str] = field(default_factory=list)


@dataclass
class SpecialCandidate:
    """Tier 3: situazioni speciali — deep value, fallen angel, turnaround."""
    ticker: str
    name: str
    sector: str
    industry: str
    market: str
    price: Optional[float]
    market_cap_million: Optional[float]
    situation_type: str          # "deep_value_pe", "deep_value_pb", "fallen_angel", "turnaround"
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    div_yield: Optional[float] = None
    price_change_1y: Optional[float] = None
    piotroski_f: Optional[int] = None
    fcf_positive: bool = False
    situation_score: float = 0.0
    notes: list[str] = field(default_factory=list)


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


def _query_one_market(market: str, min_mcap_m: int, min_price: float,
                       limit: int, sector_filter: Optional[str]) -> list[dict]:
    """Query TV per un singolo mercato con pre-filtri qualità. Ritorna lista di row-dict.

    Pre-filtri TV (riducono significativamente l'universo prima di toccare yfinance):
    - PE > 0 AND PE < 80  → esclude loss-making e mega-growth costosi
    - volume > 10000      → esclude illiquidi che yfinance non sa gestire
    Questo porta l'universo da ~2500 a ~200-300 ticker dove yfinance non viene saturato.
    """
    rows: list[dict] = []
    try:
        q = (Query()
             .set_markets(market)
             .select("name", "close", "market_cap_basic",
                     "price_earnings_ttm", "sector", "dividends_yield",
                     "volume")
             .where(
                 Column("market_cap_basic") > min_mcap_m * 1_000_000,
                 Column("close") > min_price,
                 Column("price_earnings_ttm") > 0,
                 Column("price_earnings_ttm") < 80,
                 Column("volume") > 10000,
             )
             .order_by("market_cap_basic", ascending=False)
             .limit(limit))
        if sector_filter:
            q = q.where(Column("sector") == sector_filter)
        _count, df = q.get_scanner_data()
        if df is None or df.empty:
            return rows
        for _, row in df.iterrows():
            yf_tkr = tv_to_yf_ticker(row["ticker"])
            if yf_tkr is None:
                continue
            rows.append({
                "yf_ticker": yf_tkr,
                "market_cap": row.get("market_cap_basic") or 0,
                "pe": row.get("price_earnings_ttm"),
                "div_yield": row.get("dividends_yield") or 0,
            })
    except Exception as e:
        log.debug("TV query fallita market=%s: %s", market, e)
    return rows


def build_universe_tradingview(region: str = "GLOBAL", min_mcap_m: int = 500,
                                min_price: float = 1.0, limit_per_market: int = 100,
                                sector_filter: Optional[str] = None,
                                total_limit: Optional[int] = None) -> list[str]:
    """Auto-build universe da TradingView in formato yfinance.

    Query per singolo mercato in parallelo (ThreadPoolExecutor) — questo è
    critico: la query multi-mercato con set_markets(*many) ritorna solo i top
    globali per market cap (~200-300 totali). Le query per-mercato danno
    `limit_per_market` titoli locali per ciascun mercato, coprendo mid/small-cap
    che altrimenti verrebbero escluse.
    """
    if not TV_OK:
        log.error("tradingview-screener non installato.")
        return []
    markets = TV_MARKETS.get(region, ["america"])
    log.info("Universe TV: region=%s, %d mercati × %d righe = max %d ticker",
             region, len(markets), limit_per_market, len(markets) * limit_per_market)

    from concurrent.futures import ThreadPoolExecutor, as_completed
    all_rows: list[dict] = []

    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(_query_one_market, mkt, min_mcap_m, min_price,
                          limit_per_market, sector_filter): mkt
                for mkt in markets}
        ok, fail = 0, 0
        for fut in as_completed(futs):
            rows = fut.result()
            if rows:
                all_rows.extend(rows)
                ok += 1
            else:
                fail += 1

    log.info("TV: %d mercati OK, %d falliti, %d righe totali pre-dedup",
             ok, fail, len(all_rows))

    # Deduplica
    seen: set[str] = set()
    unique: list[dict] = []
    for r in all_rows:
        if r["yf_ticker"] not in seen:
            seen.add(r["yf_ticker"])
            unique.append(r)

    # Composite score: income + value, mid-cap preferita ma non esclusiva
    def tv_score(r: dict) -> float:
        s = 0.0
        dy = r["div_yield"]
        if dy > 0:
            s += min(dy * 10, 4.0)
        pe = r["pe"]
        if pe and 5 < pe < 40:
            s += (40 - pe) / 40 * 3.0
        mc = r["market_cap"]
        if 1e9 < mc <= 1e10:
            s += 1.0
        elif mc > 1e10:
            s += 0.5
        return s

    unique.sort(key=tv_score, reverse=True)

    if total_limit and len(unique) > total_limit:
        unique = unique[:total_limit]
        log.info("Universe cappato a %d ticker (composite score TV)", total_limit)

    tickers = [r["yf_ticker"] for r in unique]
    log.info("Universe finale: %d ticker unici", len(tickers))
    return tickers


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


def build_speculative_universe_tv(region: str = "GLOBAL") -> list[str]:
    """Tier 2: small-cap/penny universe da TradingView ordinato per relative volume.

    Cerca titoli 5M-500M market cap con attività di volume sopra la media —
    segnale che qualcosa sta succedendo (notizie, contratti, rumors, squeeze).
    Nessun filtro su PE, profittabilità o dividend yield.
    """
    if not TV_OK:
        log.error("tradingview-screener non installato.")
        return []

    markets = TV_MARKETS.get(region, ["america"])
    log.info("Speculative universe TV: region=%s, mercati=%d", region, len(markets))

    from concurrent.futures import ThreadPoolExecutor, as_completed

    def query_market(mkt: str) -> list[dict]:
        rows: list[dict] = []
        try:
            q = (Query()
                 .set_markets(mkt)
                 .select("name", "close", "market_cap_basic",
                         "relative_volume_10d_calc", "volume", "sector")
                 .where(
                     Column("market_cap_basic") > SPEC_MIN_MCAP_M * 1_000_000,
                     Column("market_cap_basic") < SPEC_MAX_MCAP_M * 1_000_000,
                     Column("close") > SPEC_MIN_PRICE,
                     Column("relative_volume_10d_calc") > 1.5,
                 )
                 .order_by("relative_volume_10d_calc", ascending=False)
                 .limit(150))
            _count, df = q.get_scanner_data()
            if df is None or df.empty:
                return rows
            for _, row in df.iterrows():
                yf_tkr = tv_to_yf_ticker(row["ticker"])
                if yf_tkr is None:
                    continue
                rows.append({
                    "yf_ticker": yf_tkr,
                    "market_cap": row.get("market_cap_basic") or 0,
                    "rel_vol": row.get("relative_volume_10d_calc") or 0,
                })
        except Exception as e:
            log.debug("Speculative TV market=%s fallito: %s", mkt, e)
        return rows

    all_rows: list[dict] = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(query_market, m): m for m in markets}
        for fut in as_completed(futs):
            all_rows.extend(fut.result())

    seen: set[str] = set()
    unique: list[dict] = []
    for r in all_rows:
        if r["yf_ticker"] not in seen:
            seen.add(r["yf_ticker"])
            unique.append(r)

    # Sort by relative volume (most active first = highest catalyst probability)
    unique.sort(key=lambda r: r["rel_vol"], reverse=True)
    tickers = [r["yf_ticker"] for r in unique]
    log.info("Speculative universe: %d ticker unici", len(tickers))
    return tickers


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

def fetch_info_only(ticker: str) -> Optional[dict]:
    """Fase 1: una sola chiamata HTTP — solo t.info."""
    try:
        t = yf.Ticker(ticker)
        info = t.info or {}
        if not info or info.get("marketCap") is None:
            return None
        return {"ticker": ticker, "info": info}
    except Exception:
        return None


def passes_quick_filter(info: dict) -> bool:
    """Filtro rapido MVF v3.0-aware: elimina solo i chiari rejects.

    Più permissivo della v2: lascia passare situazioni ambigue per analisi MVF.
    Hard rejects: prezzo < $0.50, market cap < $300M, perdite catastrofiche,
    debito/equity > 5 (zona Altman pericolosa), pension/healthcare obs.
    """
    price = info.get("currentPrice") or info.get("regularMarketPrice", 0) or 0
    if price < CONFIG["min_price_usd"]:
        return False
    mc = info.get("marketCap", 0) or 0
    if mc < CONFIG["min_market_cap_million"] * 1e6:
        return False
    # Elimina solo perdite estreme (> -75% net margin) — preserva turnaround
    margin = info.get("profitMargins")
    if margin is not None and margin < -0.75:
        return False
    # D/E catastrofico — elimina zombi finanziari evidenti
    de = info.get("debtToEquity")
    if de is not None and de > 800:  # debtToEquity yfinance è in %
        return False
    # Volume troppo basso → illiquido
    avg_vol = info.get("averageVolume10days") or 0
    if avg_vol > 0 and avg_vol < 5000:
        return False
    return True


def fetch_remaining(ticker: str, prefetched_info: dict) -> Optional[dict]:
    """Fase 2: fetch fondamentali — riusa info già scaricato in fase 1."""
    try:
        t = yf.Ticker(ticker)
        return {
            "ticker": ticker,
            "info": prefetched_info,
            "financials": t.financials,
            "balance_sheet": t.balance_sheet,
            "cashflow": t.cashflow,
            "dividends": t.dividends,
            "history": t.history(period="5y", auto_adjust=True),
            "earnings_dates": getattr(t, "earnings_dates", None),
            "quarterly_financials": t.quarterly_financials,
        }
    except Exception:
        return None


def fetch_data(ticker):
    """Compat: fetch completo in un'unica chiamata (usato standalone)."""
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

    # Valuation multiples
    mc_v = info.get("marketCap")
    ebitda_abs = info.get("ebitda") or safe_row(fin, "EBITDA")
    debt_v = safe_row(bs, "Total Debt") or 0
    cash_v = info.get("totalCash") or 0
    if mc_v and ebitda_abs and ebitda_abs > 0:
        ev = mc_v + debt_v - cash_v
        if ev > 0:
            m.ev_ebitda = ev / ebitda_abs
    fcf_abs = safe_row(cf, "Free Cash Flow")
    if fcf_abs is not None and mc_v and mc_v > 0:
        m.fcf_yield = fcf_abs / mc_v
    m.pb_ratio = info.get("priceToBook")
    m.ps_ratio = info.get("priceToSalesTrailing12Months")

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
# SEZIONE 6.5 — PIOTROSKI · MOAT · DCF · FILIERA · EARNINGS ACCEL
# =============================================================================

def compute_piotroski(info: dict, fin, bs, cf) -> tuple[int, list[str]]:
    """Piotroski F-Score (0-9). High score = improving fundamentals."""
    score = 0
    factors: list[str] = []

    ni = safe_row(fin, "Net Income")
    ta = safe_row(bs, "Total Assets")
    roa = (ni / ta) if (ni is not None and ta and ta > 0) else None
    if roa is not None and roa > 0:
        score += 1; factors.append("F1:ROA+")

    cfo = safe_row(cf, "Cash From Operations")
    if cfo is not None and cfo > 0:
        score += 1; factors.append("F2:CFO+")

    ni_p = safe_row(fin, "Net Income", 1)
    ta_p = safe_row(bs, "Total Assets", 1)
    roa_p = (ni_p / ta_p) if (ni_p is not None and ta_p and ta_p > 0) else None
    if roa is not None and roa_p is not None and roa > roa_p:
        score += 1; factors.append("F3:ROA↑")

    if cfo is not None and ta and ta > 0 and roa is not None:
        if cfo / ta > roa:
            score += 1; factors.append("F4:accruals_ok")

    d = safe_row(bs, "Total Debt"); d_p = safe_row(bs, "Total Debt", 1)
    ta_p2 = safe_row(bs, "Total Assets", 1)
    lev = d / ta if (d is not None and ta and ta > 0) else None
    lev_p = d_p / ta_p2 if (d_p is not None and ta_p2 and ta_p2 > 0) else None
    if lev is not None and lev_p is not None and lev < lev_p:
        score += 1; factors.append("F5:leverage↓")

    ca = safe_row(bs, "Current Assets"); cl = safe_row(bs, "Current Liabilities")
    ca_p = safe_row(bs, "Current Assets", 1); cl_p = safe_row(bs, "Current Liabilities", 1)
    cr = ca / cl if (ca is not None and cl and cl > 0) else None
    cr_p = ca_p / cl_p if (ca_p is not None and cl_p and cl_p > 0) else None
    if cr is not None and cr_p is not None and cr > cr_p:
        score += 1; factors.append("F6:curr_ratio↑")

    sh = info.get("sharesOutstanding"); sh_f = info.get("floatShares")
    if sh is not None and sh_f is not None and sh <= sh_f * 1.02:
        score += 1; factors.append("F7:no_dilution")

    rev = safe_row(fin, "Total Revenue"); gp = safe_row(fin, "Gross Profit")
    rev_p = safe_row(fin, "Total Revenue", 1); gp_p = safe_row(fin, "Gross Profit", 1)
    gm = gp / rev if (gp is not None and rev and rev > 0) else None
    gm_p = gp_p / rev_p if (gp_p is not None and rev_p and rev_p > 0) else None
    if gm is not None and gm_p is not None and gm > gm_p:
        score += 1; factors.append("F8:GM↑")

    at_ = rev / ta if (rev is not None and ta and ta > 0) else None
    at_p = rev_p / ta_p2 if (rev_p is not None and ta_p2 and ta_p2 > 0) else None
    if at_ is not None and at_p is not None and at_ > at_p:
        score += 1; factors.append("F9:asset_turn↑")

    return score, factors


def compute_moat_score(m: IntrinsicMetrics) -> tuple[float, list[str]]:
    """Moat proxy (0-10): pricing power + capital efficiency + asset-light + R&D."""
    score = 0.0
    signals: list[str] = []
    if m.gross_margin is not None:
        if m.gross_margin > 0.60:
            score += 3.0; signals.append("GM>60%")
        elif m.gross_margin > 0.40:
            score += 2.0; signals.append("GM>40%")
        elif m.gross_margin > 0.25:
            score += 1.0
    if m.roic is not None:
        if m.roic > 0.25:
            score += 3.0; signals.append("ROIC>25%")
        elif m.roic > 0.15:
            score += 2.0; signals.append("ROIC>15%")
        elif m.roic > 0.08:
            score += 1.0
    if m.capex_revenue is not None:
        if m.capex_revenue < 0.03:
            score += 1.5; signals.append("asset-light")
        elif m.capex_revenue < 0.07:
            score += 0.5
    if m.rd_revenue is not None and 0.05 <= m.rd_revenue <= 0.20:
        score += 0.5; signals.append("R&D")
    total_ret = (m.dividend_yield or 0) + (m.buyback_yield or 0)
    if total_ret > 0.05:
        score += 1.0; signals.append("shareholder_ret")
    return round(min(score, 10.0), 1), signals


def compute_dcf_upside(m: IntrinsicMetrics, info: dict, wacc: float) -> Optional[float]:
    """Simple 5y DCF + terminal: returns % upside vs market cap. Crude but directional."""
    try:
        mc = info.get("marketCap")
        rev = info.get("totalRevenue") or info.get("revenue")
        if not mc or not rev or mc <= 0 or rev <= 0:
            return None
        if m.fcf_margin is None or m.fcf_margin <= 0:
            return None
        fcf = m.fcf_margin * rev
        g_est = min(abs(m.price_cagr_5y or 0.05), 0.15)
        g_term = min(CONFIG["g_terminal_max"], g_est * 0.30)
        if wacc <= g_term:
            return None
        pv = sum(fcf * (1 + g_est) ** yr / (1 + wacc) ** yr for yr in range(1, 6))
        terminal_pv = (fcf * (1 + g_est) ** 5 * (1 + g_term) / (wacc - g_term)) / (1 + wacc) ** 5
        return round((pv + terminal_pv - mc) / mc, 3)
    except Exception:
        return None


def compute_filiera_tag(sector: str, industry: str) -> Optional[str]:
    """Map sector/industry → strategic supply chain theme (filiera)."""
    combined = f"{industry} {sector}".lower()
    for key, tag in FILIERE_STRATEGIC.items():
        if key.lower() in combined:
            return tag
    return None


def compute_earnings_acceleration(quarterly_fin) -> Optional[float]:
    """YoY revenue growth: latest quarter vs prior quarter. Positive = accelerating."""
    if quarterly_fin is None or quarterly_fin.empty:
        return None
    try:
        for alias in ["Total Revenue", "Revenue"]:
            if alias in quarterly_fin.index:
                rev = quarterly_fin.loc[alias]
                if len(rev) >= 8:
                    vals = [float(v) if pd.notna(v) else None for v in rev.iloc[:8]]
                    r0, r4, r1, r5 = vals[0], vals[4], vals[1], vals[5]
                    if all(v and v > 0 for v in [r0, r4, r1, r5]):
                        yoy_now = (r0 - r4) / r4
                        yoy_prev = (r1 - r5) / r5
                        return round(yoy_now - yoy_prev, 4)
    except Exception:
        pass
    return None


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
    # Piotroski bonus/malus
    if c.piotroski_f is not None:
        if c.piotroski_f >= 8:
            raw += 10
        elif c.piotroski_f >= 6:
            raw += 5
        elif c.piotroski_f < 4:
            raw -= 5
    # Moat bonus (0-10 scale → max +15 pts)
    if c.moat_score is not None:
        raw += c.moat_score * 1.5
    # DCF upside bonus
    if c.dcf_upside_pct is not None and c.dcf_upside_pct > 0.10:
        raw += min(c.dcf_upside_pct * 20, 10)
    # Filiera strategica bonus
    if c.filiera_tag:
        raw += 5
    # Earnings acceleration bonus
    if c.earnings_acceleration is not None and c.earnings_acceleration > 0.05:
        raw += 5

    # EV/EBITDA: <8 = molto conveniente, >20 = caro
    ev_eb = c.metrics.ev_ebitda
    if ev_eb is not None and ev_eb > 0:
        if ev_eb < 8:
            raw += 8
        elif ev_eb < 12:
            raw += 4
        elif ev_eb > 20:
            raw -= 4

    # FCF yield: rendimento reale per l'azionista
    fcf_y = c.metrics.fcf_yield
    if fcf_y is not None:
        if fcf_y > 0.08:
            raw += 8
        elif fcf_y > 0.05:
            raw += 4
        elif fcf_y > 0.03:
            raw += 2
        elif fcf_y < 0:
            raw -= 3

    # P/B: sotto book = margine di sicurezza
    pb = c.metrics.pb_ratio
    if pb is not None and pb > 0:
        if pb < 1.0:
            raw += 6
        elif pb < 1.5:
            raw += 3
        elif pb > 4.0:
            raw -= 2

    # P/S: utile per growth e loss-making
    ps = c.metrics.ps_ratio
    if ps is not None and ps > 0:
        if ps < 1.0:
            raw += 4
        elif ps < 2.0:
            raw += 2
        elif ps > 8.0:
            raw -= 3

    return round(max(0, min(100, raw)), 1)


# =============================================================================
# SEZIONE 7.5 — MVF v3.0 VALUATION (5 modelli + scoring + confidence)
# =============================================================================

def _series_to_list(df, row_name, n: int = 5) -> list:
    """Estrae una serie storica da financials/cashflow come lista (ultimo→primo)."""
    if df is None or df.empty:
        return []
    aliases = {
        "Total Revenue": ["Total Revenue", "Revenue"],
        "Net Income": ["Net Income"],
        "Free Cash Flow": ["Free Cash Flow"],
        "Operating Income": ["Operating Income", "EBIT"],
        "Working Capital": ["Working Capital"],
    }
    for key in aliases.get(row_name, [row_name]):
        if key in df.index:
            vals = df.loc[key].head(n).tolist()
            return [float(v) if pd.notna(v) else None for v in vals]
    return []


_YF_SUFFIX_TO_COUNTRY = {
    ".MI": "IT", ".DE": "DE", ".F": "DE", ".PA": "FR", ".AS": "NL",
    ".BR": "BE", ".L": "UK", ".MC": "ES", ".SW": "CH", ".VX": "CH",
    ".T": "JP", ".HK": "CN", ".SS": "CN", ".SZ": "CN", ".KS": "KR",
    ".ST": "SE", ".CO": "DK", ".OL": "NO", ".HE": "FI", ".VI": "AT",
    ".LS": "PT", ".AX": "AU", ".NZ": "NZ", ".TO": "CA", ".V": "CA",
    ".IR": "IE", ".SA": "BR", ".MX": "MX",
}


def _country_for_tax(ticker: str, market: str) -> str:
    """Paese di ritenuta alla fonte, dal suffisso del ticker (MVF Sez. 7)."""
    t = (ticker or "").upper()
    if "." in t:
        suffix = "." + t.rsplit(".", 1)[1]
        if suffix in _YF_SUFFIX_TO_COUNTRY:
            return _YF_SUFFIX_TO_COUNTRY[suffix]
    # senza suffisso: quotazione USA
    return "US" if market in ("US", "") else market


def apply_mvf_valuation(c, data: dict, market: str) -> None:
    """Applica MVF v4.1 a un candidato. Modifica c in-place.

    Catena v4.1:
      STEP 0  routing di classe -> se non common, nessun voto (motore dedicato
              non disponibile in regime S)
      1-7     WACC, 5 modelli, scenari, sensitivity, variation, CS
      8       Voto MVF /1000 su base 280 (metriche a bande incluse)
      9       Red flag + GATE di qualita' G1-G6
      10      IQI -> MoS_base, CS -> overlay, prezzo ideale
      11      Riconciliazione Voto <-> IQI, rendimento netto Italia
    """
    info = data["info"]
    fin = data["financials"]
    bs = data["balance_sheet"]
    cf = data["cashflow"]
    dividends = data["dividends"]
    hist = data["history"]

    notes = []

    # === STEP 0: routing di classe (MVF Sez. 2) ===
    routing = mvf.classify_instrument(
        c.sector, c.industry, c.name, c.ticker, info.get("quoteType"))
    c.instrument_class = routing.instrument_class
    c.instrument_base = routing.base
    if not routing.engine_available:
        # Classe rilevata ma motore dedicato non implementato in regime S.
        # Nessun voto: il motore common userebbe metriche non pertinenti.
        c.mvf_vote_1000 = None
        c.mvf_engine_note = routing.notes[0] if routing.notes else ""
        c.mvf_valuation = {
            "mvf_version": mvf.MVF_VERSION,
            "execution_regime": mvf.EXECUTION_REGIME,
            "instrument_class": routing.instrument_class,
            "base": routing.base,
            "engine_available": False,
            "notes": routing.notes,
        }
        return

    # === STEP 1: WACC via CAPM esteso ===
    beta = info.get("beta")
    re_, beta_used = mvf.compute_cost_of_equity(market, beta)
    mc = info.get("marketCap") or 0
    total_debt = safe_row(bs, "Total Debt") or 0
    interest_exp = safe_row(fin, "Interest Expense")
    if interest_exp is None:
        interest_exp = abs(safe_row(fin, "Interest Expense Non Operating") or 0)
    tax_rate = c.metrics.tax_rate
    wacc, rd_at = mvf.compute_wacc(mc, total_debt, interest_exp, tax_rate, re_)
    if wacc is None:
        wacc = re_  # fallback

    # === STEP 2: ROIC − WACC (Economic Spread) ===
    economic_spread = None
    es_neg_2y = False
    if c.metrics.roic is not None and wacc is not None:
        economic_spread = c.metrics.roic - wacc
        # Proxy 2y: se ROIC corrente < WACC E earnings_acceleration negativo
        # → assumiamo 2y negativi (proxy semplice senza riproiezione storica WACC)
        if economic_spread < 0 and (c.earnings_acceleration or 0) < 0:
            es_neg_2y = True

    # === STEP 3: Dati per modelli di valutazione ===
    shares = info.get("sharesOutstanding") or 1
    cash = safe_row(bs, "Cash And Cash Equivalents") or 0
    net_debt = total_debt - cash
    fcf_0 = safe_row(cf, "Free Cash Flow")
    fcf_series = _series_to_list(cf, "Free Cash Flow", 5)
    rev_series = _series_to_list(fin, "Total Revenue", 5)
    nm_series = []
    if rev_series:
        ni_series = _series_to_list(fin, "Net Income", 5)
        for i, ni in enumerate(ni_series):
            if i < len(rev_series) and rev_series[i] and rev_series[i] > 0 and ni is not None:
                nm_series.append(ni / rev_series[i])
            else:
                nm_series.append(None)
    eps = info.get("trailingEps")
    eps_5y_growth = None
    earnings_growth_info = info.get("earningsGrowth") or info.get("earningsQuarterlyGrowth")
    if earnings_growth_info is not None:
        eps_5y_growth = earnings_growth_info

    # Operating income normalizzato per EPV (media ultimi 5 anni)
    oi_series = _series_to_list(fin, "Operating Income", 5)
    clean_oi = [v for v in oi_series if v is not None and v > 0]
    oi_norm = sum(clean_oi) / len(clean_oi) if clean_oi else None

    # Dividendi
    d0 = info.get("trailingAnnualDividendRate") or 0
    has_div = d0 > 0
    g_div_5y = c.metrics.dividend_growth_5y
    # g sostenibile = ROE × (1 - payout)
    payout = c.metrics.payout_ratio
    g_sost = None
    if c.metrics.roe is not None and payout is not None:
        g_sost = c.metrics.roe * (1 - payout)
    g_div = None
    if g_div_5y is not None and g_sost is not None:
        g_div = min(g_div_5y, g_sost, 0.04)
    elif g_div_5y is not None:
        g_div = min(g_div_5y, 0.04)
    elif g_sost is not None:
        g_div = min(g_sost, 0.04)

    # === STEP 4: 5 modelli ===
    is_us = market == "US"
    val = mvf.MVFValuation()
    val.wacc = round(wacc, 4) if wacc else None
    val.cost_of_equity = round(re_, 4)
    val.cost_of_debt_at = round(rd_at, 4) if rd_at else None
    val.beta_used = round(beta_used, 2)
    val.economic_spread = round(economic_spread, 4) if economic_spread is not None else None
    val.economic_spread_negative_2y = es_neg_2y

    # Graham
    val.graham_fv = round(mvf.graham_fair_value(eps, eps_5y_growth, market, is_us) or 0, 2) or None
    if val.graham_fv == 0:
        val.graham_fv = None

    # DDM (solo se paga dividendi)
    if has_div and g_div is not None:
        val.ddm_1stage_fv = mvf.ddm_1stage(d0, g_div, re_)
        if val.ddm_1stage_fv:
            val.ddm_1stage_fv = round(val.ddm_1stage_fv, 2)
        if g_div_5y is not None:
            g1 = min(g_div_5y, 0.15)
            g2 = min(g_sost or 0.03, 0.04) if g_sost else 0.03
            val.ddm_2stage_fv = mvf.ddm_2stage(d0, g1, g2, re_)
            if val.ddm_2stage_fv:
                val.ddm_2stage_fv = round(val.ddm_2stage_fv, 2)

    # DCF 2-stage 10y
    g1_dcf = None
    if eps_5y_growth is not None:
        g1_dcf = min(max(eps_5y_growth, -0.05), 0.20)
    elif c.metrics.price_cagr_5y is not None:
        g1_dcf = min(max(c.metrics.price_cagr_5y * 0.7, -0.05), 0.15)
    else:
        g1_dcf = 0.05
    g_term = min(0.02, mvf.RISK_FREE_RATE.get(market, 0.04))

    if fcf_0 and fcf_0 > 0 and wacc and wacc > g_term:
        val.dcf_2stage_fv = mvf.dcf_2stage(fcf_0, g1_dcf, g_term, wacc, shares, net_debt)
        if val.dcf_2stage_fv:
            val.dcf_2stage_fv = round(val.dcf_2stage_fv, 2)
        # Sensitivity 5x5
        val.dcf_sensitivity = mvf.dcf_sensitivity_table(
            fcf_0, g1_dcf, wacc, g_term, shares, net_debt)
        # Scenari
        bull, base, bear, exp = mvf.scenario_analysis(
            fcf_0, g1_dcf, wacc, shares, net_debt, g_term)
        val.bull_fv = round(bull, 2) if bull else None
        val.base_fv = round(base, 2) if base else None
        val.bear_fv = round(bear, 2) if bear else None
        val.expected_fv = round(exp, 2) if exp else None
        # Reverse DCF
        val.reverse_dcf_implied_g = mvf.reverse_dcf_implied_growth(
            mc, net_debt, fcf_0, wacc, g_term)

    # EPV
    if oi_norm and wacc:
        val.epv_fv = mvf.epv_fair_value(oi_norm, tax_rate, wacc, shares, net_debt)
        if val.epv_fv:
            val.epv_fv = round(val.epv_fv, 2)

    # === STEP 5: Media ponderata + MoS + prezzo ideale ===
    sector_class = mvf.classify_sector_for_weights(
        c.sector, c.industry, has_div, fcf_0 is not None and fcf_0 < 0)
    val.weights_regime = sector_class
    model_fvs = {
        "graham": val.graham_fv,
        "ddm_1stage": val.ddm_1stage_fv,
        "ddm_2stage": val.ddm_2stage_fv,
        "dcf": val.dcf_2stage_fv,
        "epv": val.epv_fv,
    }
    wfv, model_weights, disp_info = mvf.weighted_fair_value(model_fvs, sector_class)
    val.weighted_fair_value = wfv
    val.model_weights = {k: round(v, 2) for k, v in model_weights.items()}
    val.model_dispersion_pct = disp_info.get("dispersion_pct")
    val.dispersion_flag = disp_info.get("flag", "")

    # check dispersione fair value
    clean_fvs = [v for v in [val.graham_fv, val.ddm_2stage_fv or val.ddm_1stage_fv,
                              val.dcf_2stage_fv, val.epv_fv] if v is not None and v > 0]
    if len(clean_fvs) >= 2:
        import statistics as st
        med = st.median(clean_fvs)
        if med > 0:
            max_dev = max(abs(v - med) / med for v in clean_fvs)
            if max_dev > 0.30:
                notes.append(f"divergenza fair value {max_dev:.0%}")

    # Upside vs current price
    if wfv and c.price and c.price > 0:
        val.upside_at_current_pct = round((wfv - c.price) / c.price, 4)

    val.notes = notes

    # === STEP 6: Variation % 5y per metriche chiave ===
    var = mvf.VariationMetrics()
    gp_series = _series_to_list(fin, "Gross Profit", 5)
    gm_series = []
    for i, gp in enumerate(gp_series):
        if i < len(rev_series) and rev_series[i] and rev_series[i] > 0 and gp is not None:
            gm_series.append(gp / rev_series[i])
        else:
            gm_series.append(None)
    var.gross_margin_var, _ = mvf.compute_variation_pct(gm_series)
    var.net_margin_var, var.years_used = mvf.compute_variation_pct(nm_series)
    # FCF margin series
    fcfm_series = []
    for i, fcfv in enumerate(fcf_series):
        if i < len(rev_series) and rev_series[i] and rev_series[i] > 0 and fcfv is not None:
            fcfm_series.append(fcfv / rev_series[i])
        else:
            fcfm_series.append(None)
    var.fcf_margin_var, _ = mvf.compute_variation_pct(fcfm_series)

    c.variation_5y = asdict(var)

    # === STEP 7: Confidence Score ===
    completeness = sum(1 for v in [c.metrics.gross_margin, c.metrics.operating_margin,
                                    c.metrics.net_margin, c.metrics.roic,
                                    c.metrics.fcf_margin, c.metrics.roe, eps,
                                    fcf_0, total_debt] if v is not None) / 9
    cs = mvf.compute_confidence_score(
        completeness, fcf_series, c.sector,
        [val.graham_fv, val.ddm_2stage_fv or val.ddm_1stage_fv,
         val.dcf_2stage_fv, val.epv_fv],
        has_quality_audit=True)
    c.confidence_score = asdict(cs)

    # === STEP 8: Voto MVF /1000 su base 280 ===
    metrics_dict = asdict(c.metrics)
    metrics_dict["altman_z"] = c.metrics.altman_z
    metrics_dict["earnings_quality"] = c.metrics.cash_conversion_ratio
    metrics_dict["moat_score"] = c.moat_score
    metrics_dict["insider_trading"] = info.get("heldPercentInsiders", 0) or 0
    ddm_used = val.ddm_2stage_fv is not None or val.ddm_1stage_fv is not None

    # Metriche a bande (MVF Sez. 3 B-bis) con i rispettivi guard
    eps_series = _series_to_list(fin, "Diluted EPS", 5)
    if not [v for v in eps_series if v is not None]:
        eps_series = _series_to_list(fin, "Basic EPS", 5)
    eps_cagr, _ = mvf.compute_cagr(eps_series)
    ni_series = _series_to_list(fin, "Net Income", 5)
    ni_cagr, _ = mvf.compute_cagr(ni_series)
    ni_flat_or_down = (ni_cagr is not None and eps_cagr is not None
                       and ni_cagr < 0.02 and eps_cagr > ni_cagr + 0.03)

    shares_series = _series_to_list(bs, "Ordinary Shares Number", 5)
    fcf_ps_series = []
    for i, f in enumerate(fcf_series):
        if (i < len(shares_series) and shares_series[i]
                and shares_series[i] > 0 and f is not None):
            fcf_ps_series.append(f / shares_series[i])
        else:
            fcf_ps_series.append(None)
    fcf_ps_cagr, _ = mvf.compute_cagr(fcf_ps_series)
    fcf_agg_cagr, _ = mvf.compute_cagr(fcf_series)
    fcf_agg_flat = (fcf_agg_cagr is not None and fcf_ps_cagr is not None
                    and fcf_agg_cagr < 0.02 and fcf_ps_cagr > fcf_agg_cagr + 0.03)

    pe_hist_median = None
    fwd_pe = info.get("forwardPE")
    trail_pe = c.pe_ratio
    if trail_pe and fwd_pe and fwd_pe > 0:
        pe_hist_median = (trail_pe + fwd_pe) / 2  # proxy grezzo, regime S
    pe_peer = getattr(c, "sector_median_pe", None)
    deteriorating = bool(
        (c.metrics.net_margin is not None and c.metrics.net_margin < 0)
        or (ni_cagr is not None and ni_cagr < -0.05))

    banded = {
        "eps_growth": mvf.eps_growth_band(eps_cagr, ni_flat_or_down),
        "eps_growth_raw": eps_cagr,
        "fcf_per_share_growth": mvf.fcf_per_share_growth_band(
            fcf_ps_cagr, fcf_agg_flat),
        "fcf_per_share_growth_raw": fcf_ps_cagr,
        "multiple_expansion": mvf.multiple_expansion_band(
            trail_pe, pe_hist_median, pe_peer,
            eps_stable_or_growing=(eps_cagr is not None and eps_cagr >= 0),
            fundamentals_deteriorating=deteriorating),
        "multiple_expansion_raw": trail_pe,
    }

    altman_exempt = sector_class in {"bank", "insurance", "reit", "utility"}
    mvf_vote, breakdown = mvf.compute_mvf_score(
        metrics_dict, has_div, ddm_used, c.metrics.altman_z, es_neg_2y,
        instrument_class=routing.instrument_class,
        altman_exempt=altman_exempt, banded_fractions=banded)
    c.mvf_vote_1000 = mvf_vote
    c.mvf_vote_100 = round(mvf_vote / 10, 1) if mvf_vote else None  # compat

    # === STEP 9: Red Flags ===
    goodwill = safe_row(bs, "Goodwill")
    equity = safe_row(bs, "Stockholders Equity")
    is_tech = "Technology" in (c.sector or "")
    wc_series = []
    ca_series = _series_to_list(bs, "Current Assets", 5)
    cl_series = _series_to_list(bs, "Current Liabilities", 5)
    for i in range(min(len(ca_series), len(cl_series))):
        if ca_series[i] is not None and cl_series[i] is not None:
            wc_series.append(ca_series[i] - cl_series[i])
        else:
            wc_series.append(None)
    sh_now = info.get("sharesOutstanding")
    sh_old = info.get("floatShares")
    share_dilution = ((sh_now - sh_old) / sh_old) if (sh_now and sh_old and sh_old > 0) else None
    rf = mvf.detect_red_flags(
        metrics=metrics_dict, altman_z=c.metrics.altman_z,
        fcf_series=fcf_series, net_margin_series=nm_series,
        economic_spread_neg_2y=es_neg_2y, goodwill=goodwill, equity=equity,
        is_tech=is_tech, revenue_series=rev_series,
        accruals=c.metrics.accruals_ratio, ccr=c.metrics.cash_conversion_ratio,
        share_dilution=share_dilution, payout=payout, roe=c.metrics.roe,
        cost_of_equity=re_, working_capital_series=wc_series)
    c.mvf_red_flags = {
        "critical": [k for k, v in asdict(rf).items() if v is True
                     and k in ["altman_z_danger", "fcf_negative_3y", "de_above_3",
                               "net_margin_negative_2y", "economic_spread_negative_2y",
                               "goodwill_over_50pct_equity", "sbc_over_8pct_tech"]],
        "warning": [k for k, v in asdict(rf).items() if v is True
                    and k in ["altman_z_grey", "fcf_negative_1y", "payout_above_100",
                              "revenue_decline_2y", "insider_selling",
                              "roe_below_capm", "accruals_above_10pct",
                              "ccr_below_05", "tax_rate_volatile_low",
                              "wc_growth_above_revenue", "share_dilution_above_3pct"]],
    }

    # === STEP 9-bis: GATE DI QUALITA' G1-G6 (MVF Sez. 8-bis) ===
    ebitda = safe_row(fin, "EBITDA") or safe_row(fin, "Normalized EBITDA")
    nde = (net_debt / ebitda) if (ebitda and ebitda > 0 and net_debt) else None
    ebit = safe_row(fin, "EBIT") or safe_row(fin, "Operating Income")
    int_cov = (abs(ebit) / abs(interest_exp)
               if (ebit and interest_exp and interest_exp != 0) else None)
    # secondo segnale per G5: conferma multi-segnale, mai un segnale isolato
    second_signal = bool(rf.fcf_negative_3y or rf.net_margin_negative_2y
                         or rf.de_above_3 or rf.economic_spread_negative_2y)
    is_saas = "software" in (c.industry or "").lower()
    gates = mvf.evaluate_quality_gates(
        fcf_series=fcf_series,
        economic_spread_history=None,
        economic_spread=economic_spread,
        net_debt_ebitda=nde,
        net_debt_ebitda_rising=False,
        interest_coverage=int_cov,
        share_dilution_3y=share_dilution,
        sbc_revenue=c.metrics.sbc_revenue,
        altman_z=c.metrics.altman_z,
        sector_class=sector_class,
        second_signal=second_signal,
        is_saas_growth=is_saas)
    c.quality_gates = asdict(gates)

    # === STEP 10: IQI -> MoS_base, CS -> overlay, prezzo ideale ===
    div_years = None
    if has_div:
        clean_div = [v for v in _series_to_list(fin, "Net Income", 5) if v]
        div_years = 5 if (c.metrics.dividend_growth_5y is not None) else 2
    moat_proxy = mvf.moat_proxy_score(
        c.metrics.operating_margin, c.metrics.roic, c.metrics.gross_margin,
        economic_spread)
    iqi = mvf.compute_iqi(
        metrics_dict, c.metrics.altman_z, economic_spread, wacc, moat_proxy,
        dividend_years=div_years,
        has_buyback=bool(c.metrics.buyback_yield and c.metrics.buyback_yield > 0),
        fcf_series=fcf_series, margin_series=nm_series,
        pe_current=trail_pe, pe_historical_median=pe_hist_median,
        pe_peer_median=pe_peer,
        tsr_forward=(val.upside_at_current_pct / 5
                     if val.upside_at_current_pct else None),
        growth_expected=eps_cagr, growth_from_buyback=ni_flat_or_down,
        interest_coverage=int_cov, net_debt_ebitda=nde,
        altman_exempt=altman_exempt, forward_is_estimate=True)
    c.iqi_score = asdict(iqi)

    mos, mos_detail = mvf.compute_final_mos(iqi, cs, gates)
    val.margin_of_safety_pct = mos
    val.mos_base_pct = mos_detail.get("mos_base")
    val.mos_overlay_pct = mos_detail.get("overlay")
    val.abstain = mos_detail.get("abstain", False)
    val.abstain_reason = mos_detail.get("reason", "")
    val.notes.extend(mos_detail.get("notes", []))
    if wfv and wfv > 0 and mos is not None:
        val.ideal_purchase_price = mvf.ideal_purchase_price(wfv, mos)

    # === STEP 11: riconciliazione Voto <-> IQI + rendimento netto Italia ===
    c.mvf_iqi_reconciliation = mvf.reconcile_mvf_iqi(mvf_vote, iqi.total)
    country = _country_for_tax(c.ticker, c.market)
    c.net_yield = asdict(mvf.compute_net_yield(
        c.metrics.dividend_yield, country, routing.instrument_class))

    val.instrument_class = routing.instrument_class
    val.base = routing.base
    c.mvf_valuation = asdict(val)
    c.intrinsic_value = wfv
    c.ideal_purchase_price_mos = val.ideal_purchase_price
    c.margin_of_safety_pct = mos


# =============================================================================
# SEZIONE 8 — PIPELINE
# =============================================================================

def _refresh_yfinance_session() -> None:
    """Forza un nuovo crumb Yahoo Finance per evitare errori 401.

    Il crumb (cookie di sessione) viene invalidato dopo molte richieste
    parallele. yfinance lo cachea a livello di modulo — per resettarlo
    bisogna cancellare gli attributi interni del CrumbManager o del session
    manager. Come fallback, forza yf.download() che inizializza sempre
    una sessione pulita.
    """
    import time
    time.sleep(3)
    try:
        # Tentativo 1: reset interno CrumbManager (yfinance 0.2.x)
        import yfinance.utils as yf_utils
        for attr in ("_crumb", "_crumb_timestamp", "_CRUMB",
                     "_cookies", "_session"):
            if hasattr(yf_utils, attr):
                try:
                    setattr(yf_utils, attr, None)
                except Exception:
                    pass
        # Tentativo 2: reset via yf.base
        import yfinance.base as yf_base
        for attr in ("_crumb", "_session", "session"):
            if hasattr(yf_base, attr):
                try:
                    setattr(yf_base, attr, None)
                except Exception:
                    pass
    except Exception:
        pass
    try:
        # Trigger fresh session: yf.download forza sempre un nuovo handshake
        yf.download("AAPL", period="1d", progress=False, auto_adjust=True)
        log.info("yfinance session refreshed OK (download handshake)")
    except Exception as e:
        log.debug("yfinance session refresh warning: %s", e)


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


def screen_universe(tickers, strategy="all", max_workers=8):
    """Screening a due fasi per minimizzare le chiamate HTTP totali.

    Fase 1: t.info per tutti (1 call/ticker) → quick filter → ~40% eliminati
    Fase 2: fondamentali completi solo sui superstiti (5 call/ticker)

    Workers a 8: Yahoo Finance blocca con >~50 req/sec sostenuti (crumb
    invalidato). Con pre-filtri TV l'universo è già ~300-600 ticker, quindi
    8 workers bilanciano velocità e stabilità (~40 req/s).
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    n = len(tickers)
    log.info("Fase 1/2: info fetch su %d ticker (%d workers)...", n, max_workers)

    phase1: list[tuple[str, dict]] = []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(fetch_info_only, t): t for t in tickers}
        for fut in as_completed(futs):
            try:
                result = fut.result()
            except Exception:
                continue
            if result and passes_quick_filter(result["info"]):
                phase1.append((result["ticker"], result["info"]))

    log.info("Fase 1/2: %d/%d passano il filtro rapido", len(phase1), n)

    # Refresh sessione yfinance per evitare 401 Unauthorized in Phase 2
    # (dopo migliaia di .info calls il crumb può essere invalidato).
    _refresh_yfinance_session()

    log.info("Fase 2/2: fondamentali su %d ticker...", len(phase1))
    out: list[Candidate] = []
    # Phase 2 ha 5 chiamate HTTP/ticker → ulteriore riduzione a 10 workers
    # per non saturare la nuova sessione Yahoo Finance.
    with ThreadPoolExecutor(max_workers=max(5, max_workers - 5)) as ex:
        futs = {ex.submit(fetch_remaining, tkr, inf): tkr for tkr, inf in phase1}
        for fut in as_completed(futs):
            try:
                data = fut.result()
            except Exception:
                continue
            if data is None:
                continue
            info = data["info"]
            mc = info.get("marketCap")
            if not mc or mc < CONFIG["min_market_cap_million"] * 1e6:
                continue
            price = info.get("currentPrice") or info.get("regularMarketPrice")
            if price is None or price < CONFIG["min_price_usd"]:
                continue
            market, ccy = detect_market(info)
            sector = info.get("sector", "")
            special = SPECIAL_SECTORS.get(sector)
            m, inter = compute_metrics(data)
            hard = apply_hard_filters(m, inter, special)
            wacc = CONFIG["wacc_proxies"].get(market, 0.08)
            soft = apply_soft_filters(m, inter, wacc)
            c = Candidate(
                ticker=data["ticker"],
                name=info.get("longName") or info.get("shortName") or data["ticker"],
                sector=sector, industry=info.get("industry", ""),
                market=market, currency=ccy, price=price,
                market_cap_million=mc / 1e6, pe_ratio=info.get("trailingPE"),
                metrics=m, hard_filters=hard, soft_filters=soft,
            )
            c.strategy_tags = tag_strategy(c, data["history"], data["earnings_dates"])
            c.piotroski_f, c.piotroski_factors = compute_piotroski(
                info, data["financials"], data["balance_sheet"], data["cashflow"])
            c.moat_score, c.moat_signals = compute_moat_score(c.metrics)
            c.dcf_upside_pct = compute_dcf_upside(c.metrics, info, wacc)
            c.filiera_tag = compute_filiera_tag(sector, info.get("industry", ""))
            c.earnings_acceleration = compute_earnings_acceleration(
                data.get("quarterly_financials"))
            c.composite_score = compute_composite_score(c)
            if special:
                c.notes.append(f"settore speciale: {special} (vedi MVF v3.0 Sez. 9)")
            if not c.passes_hard_filters:
                continue
            if strategy != "all" and not any(tag.startswith(strategy) for tag in c.strategy_tags):
                continue
            # === MVF v3.0: valutazione completa (5 modelli + scoring + CS + red flags) ===
            try:
                apply_mvf_valuation(c, data, market)
            except Exception as e:
                log.debug("MVF valuation fallita per %s: %s", c.ticker, e)
            out.append(c)

    return out


def passes_speculative_quick_filter(info: dict) -> bool:
    """Filtro rapido per Tier 2: molto più permissivo del Tier 1.
    Elimina solo ghost ticker e dati palesemente corrotti.
    """
    price = info.get("currentPrice") or info.get("regularMarketPrice", 0) or 0
    if price < SPEC_MIN_PRICE:
        return False
    mc = info.get("marketCap", 0) or 0
    if mc < SPEC_MIN_MCAP_M * 1e6:
        return False
    if mc > SPEC_MAX_MCAP_M * 1e6:
        return False
    # Elimina solo perdite catastrofiche (> -90% net margin) — growth pre-profit è OK
    margin = info.get("profitMargins")
    if margin is not None and margin < -0.90:
        return False
    return True


def fetch_speculative_data(ticker: str, prefetched_info: dict) -> Optional[dict]:
    """Fetch dati per analisi catalyst: history 1y + financials base."""
    try:
        t = yf.Ticker(ticker)
        return {
            "ticker": ticker,
            "info": prefetched_info,
            "financials": t.quarterly_financials,   # quarterly per revenue acceleration
            "cashflow": t.quarterly_cashflow,
            "history": t.history(period="1y", auto_adjust=True),
            "earnings_dates": getattr(t, "earnings_dates", None),
        }
    except Exception:
        return None


def detect_catalyst_signals(data: dict) -> tuple[CatalystSignals, dict]:
    """Analizza segnali catalyst su un titolo small-cap.

    Ritorna (CatalystSignals, extra_metrics) dove extra_metrics contiene
    valori numerici utili per il briefing (price change, volume ratio, ecc.).
    """
    info = data["info"]
    hist = data.get("history")
    fin = data.get("financials")
    sig = CatalystSignals()
    extra: dict = {}

    # ---- Volume analysis ----
    if hist is not None and not hist.empty and len(hist) >= 30:
        vols = hist["Volume"].values
        avg_3d  = float(np.mean(vols[-3:]))   if len(vols) >= 3  else None
        avg_30d = float(np.mean(vols[-30:]))  if len(vols) >= 30 else None
        avg_90d = float(np.mean(vols[-90:]))  if len(vols) >= 90 else None

        if avg_3d and avg_30d and avg_30d > 0:
            ratio_3d = avg_3d / avg_30d
            extra["volume_ratio_3d"] = round(ratio_3d, 2)
            if ratio_3d >= 3.0:
                sig.volume_spike_3d = True
        if avg_30d and avg_90d and avg_90d > 0:
            if avg_30d / avg_90d >= 2.0:
                sig.volume_spike_30d = True

    # ---- Price momentum ----
    if hist is not None and not hist.empty:
        closes = hist["Close"]
        last_price = float(closes.iloc[-1])
        if len(closes) >= 30:
            p30 = float(closes.iloc[-30])
            if p30 > 0:
                chg30 = (last_price - p30) / p30
                extra["price_change_30d"] = round(chg30, 4)
                if chg30 >= 0.20:
                    sig.momentum_30d_strong = True
        if len(closes) >= 63:
            p90 = float(closes.iloc[-63])
            if p90 > 0:
                chg90 = (last_price - p90) / p90
                extra["price_change_90d"] = round(chg90, 4)
                if chg90 >= 0.40:
                    sig.momentum_90d_strong = True

        # 52-week low proximity
        high52 = info.get("fiftyTwoWeekHigh")
        low52  = info.get("fiftyTwoWeekLow")
        if low52 and low52 > 0 and last_price > 0:
            if last_price <= low52 * 1.15:
                sig.near_52w_low = True

    # ---- Revenue acceleration (quarterly) ----
    if fin is not None and not fin.empty:
        try:
            rev_row = None
            for alias in ["Total Revenue", "Revenue"]:
                if alias in fin.index:
                    rev_row = fin.loc[alias]
                    break
            if rev_row is not None and len(rev_row) >= 8:
                # YoY: Q0 vs Q4, Q1 vs Q5 (4 quarters back)
                rev_q0 = float(rev_row.iloc[0]) if pd.notna(rev_row.iloc[0]) else None
                rev_q4 = float(rev_row.iloc[4]) if pd.notna(rev_row.iloc[4]) else None
                rev_q1 = float(rev_row.iloc[1]) if pd.notna(rev_row.iloc[1]) else None
                rev_q5 = float(rev_row.iloc[5]) if pd.notna(rev_row.iloc[5]) else None
                if all(v and v > 0 for v in [rev_q0, rev_q4, rev_q1, rev_q5]):
                    yoy_latest = (rev_q0 - rev_q4) / rev_q4
                    yoy_prior  = (rev_q1 - rev_q5) / rev_q5
                    extra["revenue_growth_yoy"] = round(yoy_latest, 4)
                    if yoy_latest > yoy_prior and yoy_latest > 0:
                        sig.revenue_acceleration = True
        except Exception:
            pass

    # ---- Earnings beat ----
    ed = data.get("earnings_dates")
    if ed is not None and not ed.empty:
        try:
            col = "Surprise(%)" if "Surprise(%)" in ed.columns else None
            if col:
                valid = ed.dropna(subset=[col])
                if not valid.empty:
                    surprise = float(valid.iloc[0][col])
                    extra["earnings_surprise_pct"] = round(surprise, 2)
                    if surprise > 10:
                        sig.earnings_beat = True
        except Exception:
            pass

    # ---- Short squeeze potential ----
    sf = info.get("shortPercentOfFloat") or info.get("shortRatio")
    if sf is not None:
        extra["short_float"] = round(float(sf), 4)
        if float(sf) > 0.20:
            sig.high_short_float = True

    # ---- Cash rich relative to market cap ----
    mc = info.get("marketCap") or 0
    cash = info.get("totalCash") or 0
    if mc > 0 and cash / mc >= 0.50:
        sig.cash_rich = True

    # ---- Low float (thin float = big moves possible) ----
    float_shares = info.get("floatShares")
    if float_shares is not None and float_shares < 10_000_000:
        sig.low_float = True

    return sig, extra


def _spec_score(sig: CatalystSignals, extra: dict) -> float:
    """Punteggio speculativo: segnali pesati per intensità catalyst."""
    score = 0.0
    # Volume spike è il segnale più affidabile che qualcosa sta succedendo
    if sig.volume_spike_3d:
        vol_ratio = extra.get("volume_ratio_3d", 3.0)
        score += min(vol_ratio * 5, 25)   # max 25pt, +5 per ogni X di volume
    if sig.volume_spike_30d:
        score += 10
    # Momentum conferma la direzione
    if sig.momentum_30d_strong:
        chg = extra.get("price_change_30d", 0.20)
        score += min(chg * 50, 20)        # max 20pt
    if sig.momentum_90d_strong:
        score += 15
    # Near 52w low: setup per reversal con catalyst
    if sig.near_52w_low:
        score += 8
    # Fondamentali catalyst
    if sig.revenue_acceleration:
        score += 12
    if sig.earnings_beat:
        score += 10
    # Squeeze / thin float
    if sig.high_short_float:
        score += 15
    if sig.low_float:
        score += 8
    if sig.cash_rich:
        score += 5
    return round(score, 1)


def screen_speculative_universe(tickers: list[str], max_workers: int = 8,
                                 top_n: int = 30) -> list[SpeculativeCandidate]:
    """Screening a due fasi per Tier 2 (small-cap / catalyst).

    Fase 1: t.info quick filter (lenient — solo elimina ghost ticker)
    Fase 2: history + quarterly financials per detect_catalyst_signals()
    Non applica hard filter MVF — questi titoli non devono essere "sani",
    devono avere un catalyst che giustifichi attenzione speculativa.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    n = len(tickers)
    log.info("Spec Fase 1/2: info fetch su %d ticker...", n)

    phase1: list[tuple[str, dict]] = []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(fetch_info_only, t): t for t in tickers}
        for fut in as_completed(futs):
            try:
                result = fut.result()
            except Exception:
                continue
            if result and passes_speculative_quick_filter(result["info"]):
                phase1.append((result["ticker"], result["info"]))

    log.info("Spec Fase 1/2: %d/%d passano il filtro rapido", len(phase1), n)

    log.info("Spec Fase 2/2: catalyst analysis su %d ticker...", len(phase1))
    out: list[SpeculativeCandidate] = []

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(fetch_speculative_data, tkr, inf): tkr for tkr, inf in phase1}
        for fut in as_completed(futs):
            try:
                data = fut.result()
            except Exception:
                continue
            if data is None:
                continue
            info = data["info"]
            sig, extra = detect_catalyst_signals(data)
            sig_dict = asdict(sig)
            active_signals = [k for k, v in sig_dict.items() if v]
            count = len(active_signals)
            if count == 0:
                continue   # nessun segnale, non interessa

            mc = info.get("marketCap", 0) or 0
            price = info.get("currentPrice") or info.get("regularMarketPrice")
            market, _ = detect_market(info)
            score = _spec_score(sig, extra)

            sc = SpeculativeCandidate(
                ticker=data["ticker"],
                name=info.get("longName") or info.get("shortName") or data["ticker"],
                sector=info.get("sector", ""),
                industry=info.get("industry", ""),
                market=market,
                price=price,
                market_cap_million=round(mc / 1e6, 2) if mc else None,
                signals=sig,
                signal_count=count,
                signal_labels=active_signals,
                price_change_30d=extra.get("price_change_30d"),
                price_change_90d=extra.get("price_change_90d"),
                volume_ratio_3d=extra.get("volume_ratio_3d"),
                revenue_growth_yoy=extra.get("revenue_growth_yoy"),
                short_float=extra.get("short_float"),
                speculative_score=score,
            )
            out.append(sc)

    out.sort(key=lambda c: c.speculative_score, reverse=True)
    log.info("Speculative candidati con signal>=1: %d", len(out))
    return out[:top_n]


# =============================================================================
# SEZIONE 8b — MARKET CONTEXT LAYER
# =============================================================================

def build_market_context() -> dict:
    """Fetch ETF settoriali e regionali per contestualizzare lo screening.

    Ritorna: performance per settore US (11 SPDR), per regione (13 ETF),
    e macro indicators (VIX, yield curve, commodities).
    Claude usa questo contesto per capire quale mercato/settore è in momentum
    vs quale è in value territory.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    all_instruments = {**SECTOR_ETFS, **REGIONAL_ETFS, **MACRO_INDICATORS}
    results: dict[str, dict] = {}

    def fetch_etf(label: str, tkr: str) -> tuple[str, Optional[dict]]:
        try:
            t = yf.Ticker(tkr)
            h = t.history(period="1y", auto_adjust=True)
            if h.empty or len(h) < 20:
                return label, None
            closes = h["Close"]
            last = float(closes.iloc[-1])
            def pct(n):
                if len(closes) >= n:
                    p = float(closes.iloc[-n])
                    return round((last - p) / p * 100, 2) if p > 0 else None
                return None
            vols = h["Volume"]
            avg_vol_10 = float(vols.iloc[-10:].mean()) if len(vols) >= 10 else None
            avg_vol_30 = float(vols.iloc[-30:].mean()) if len(vols) >= 30 else None
            rel_vol = round(avg_vol_10 / avg_vol_30, 2) if (avg_vol_10 and avg_vol_30 and avg_vol_30 > 0) else None
            prev_close = round(float(closes.iloc[-2]), 3) if len(closes) >= 2 else None
            return label, {
                "ticker": tkr, "last": round(last, 3), "prev": prev_close,
                "1m": pct(22), "3m": pct(63), "6m": pct(126), "1y": pct(252),
                "rel_vol_10d": rel_vol,
            }
        except Exception:
            return label, None

    with ThreadPoolExecutor(max_workers=40) as ex:
        futs = {ex.submit(fetch_etf, lbl, tkr): lbl for lbl, tkr in all_instruments.items()}
        for fut in as_completed(futs):
            lbl, rec = fut.result()
            if rec:
                results[lbl] = rec

    # Classificazione settori US: leaders vs laggards su 1 mese
    sector_perf = {k: v.get("1m") or 0 for k, v in results.items() if k in SECTOR_ETFS}
    sorted_sectors = sorted(sector_perf.items(), key=lambda x: x[1], reverse=True)
    sector_leaders = [k for k, _ in sorted_sectors[:3]]
    sector_laggards = [k for k, _ in sorted_sectors[-3:]]

    # Yield curve: spread 10y-2y (>0 normale, <0 invertita)
    y10 = results.get("10Y_UST", {}).get("last")
    y2  = results.get("2Y_UST",  {}).get("last")
    yield_spread = round(y10 - y2, 3) if (y10 and y2) else None

    return {
        "sectors": {k: results[k] for k in SECTOR_ETFS if k in results},
        "regions": {k: results[k] for k in REGIONAL_ETFS if k in results},
        "macro": {k: results[k] for k in MACRO_INDICATORS if k in results},
        "sector_leaders_1m": sector_leaders,
        "sector_laggards_1m": sector_laggards,
        "yield_curve_spread_10y2y": yield_spread,
        "vix": results.get("VIX", {}).get("last"),
    }


# =============================================================================
# SEZIONE 8c — SECTOR-RELATIVE SCORING
# =============================================================================

def compute_sector_relative_scores(candidates: list) -> None:
    """Post-processing: aggiusta composite_score in base a valutazione relativa al settore.

    Un'azienda con PE molto sotto la mediana del suo settore ottiene un bonus,
    anche se in assoluto il PE non è bassissimo. Muta i candidati in-place.
    """
    from collections import defaultdict

    by_sector: dict[str, list] = defaultdict(list)
    for c in candidates:
        if c.sector:
            by_sector[c.sector].append(c)

    for sector, group in by_sector.items():
        if len(group) < 3:
            continue
        pes   = [c.pe_ratio for c in group if c.pe_ratio and 0 < c.pe_ratio < 100]
        fcf_y = [c.metrics.fcf_yield for c in group if c.metrics.fcf_yield]
        ev_eb = [c.metrics.ev_ebitda for c in group if c.metrics.ev_ebitda and c.metrics.ev_ebitda > 0]
        scores = [c.composite_score for c in group if c.composite_score]

        med_pe    = float(np.median(pes))    if pes    else None
        med_fcfy  = float(np.median(fcf_y))  if fcf_y  else None
        med_eveb  = float(np.median(ev_eb))  if ev_eb  else None
        med_score = float(np.median(scores)) if scores else None

        for c in group:
            bonus = 0.0
            reasons = []
            # PE 25% sotto la mediana del settore
            if med_pe and c.pe_ratio and 0 < c.pe_ratio < med_pe * 0.75:
                bonus += 5.0
                reasons.append(f"PE {c.pe_ratio:.1f}x vs settore {med_pe:.1f}x (-25%)")
            # FCF yield 30% sopra la mediana del settore
            if med_fcfy and c.metrics.fcf_yield and c.metrics.fcf_yield > med_fcfy * 1.30:
                bonus += 4.0
                reasons.append(f"FCF yield {c.metrics.fcf_yield:.1%} vs settore {med_fcfy:.1%}")
            # EV/EBITDA 20% sotto la mediana del settore
            if med_eveb and c.metrics.ev_ebitda and 0 < c.metrics.ev_ebitda < med_eveb * 0.80:
                bonus += 4.0
                reasons.append(f"EV/EBITDA {c.metrics.ev_ebitda:.1f}x vs settore {med_eveb:.1f}x (-20%)")
            # Score nel top 20% del settore
            if med_score and c.composite_score and c.composite_score > med_score * 1.20:
                bonus += 3.0
                reasons.append(f"Top performer {sector}")
            if bonus > 0:
                c.composite_score = round(min(100, (c.composite_score or 0) + bonus), 1)
                for r in reasons:
                    c.notes.append(r)


# =============================================================================
# SEZIONE 8d — TIER 3: SPECIAL SITUATIONS
# =============================================================================

def build_special_situations_tv(region: str = "GLOBAL") -> dict[str, list[str]]:
    """Tier 3: tre query TV separate per deep value e fallen angels.

    Ritorna dict con 3 bucket: deep_value_pe, deep_value_pb, fallen_angel.
    Ogni bucket è una lista di ticker yfinance-format.
    """
    if not TV_OK:
        return {}
    markets = TV_MARKETS.get(region, ["america"])

    buckets: dict[str, list[str]] = {
        "deep_value_pe": [], "deep_value_pb": [], "fallen_angel": []
    }
    failed: list[str] = []

    def query_market(mkt, filters, label):
        try:
            q = (Query()
                 .set_markets(mkt)
                 .select("name", "close", "market_cap_basic",
                         "price_earnings_ttm", "price_book_fq",
                         "dividends_yield")
                 .where(
                     Column("market_cap_basic") > CONFIG["min_market_cap_million"] * 1_000_000,
                     Column("close") > CONFIG["min_price_usd"],
                     *filters,
                 )
                 .order_by("market_cap_basic", ascending=False)
                 .limit(15))
            _count, df = q.get_scanner_data()
            if df is None or df.empty:
                return []
            tickers = []
            for _, row in df.iterrows():
                yf_tkr = tv_to_yf_ticker(row["ticker"])
                if yf_tkr is None:
                    failed.append(row["ticker"])
                    continue
                tickers.append(yf_tkr)
            return tickers
        except Exception as e:
            log.debug("Tier 3 query %s market=%s fallita: %s", label, mkt, e)
            return []

    from concurrent.futures import ThreadPoolExecutor, as_completed

    bucket_filters = {
        "deep_value_pe": [Column("price_earnings_ttm") > 2,
                          Column("price_earnings_ttm") < 8],
        "deep_value_pb": [Column("price_book_fq") > 0,
                          Column("price_book_fq") < 0.8],
        "fallen_angel": [Column("dividends_yield") > 6],
    }

    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {}
        for label, filters in bucket_filters.items():
            for mkt in markets:
                futs[ex.submit(query_market, mkt, filters, label)] = label
        for fut in as_completed(futs):
            label = futs[fut]
            buckets[label].extend(fut.result())

    if failed:
        log.info("Tier 3: %d ticker non mappati skipped", len(failed))

    # Dedup each bucket
    for k in buckets:
        seen: set[str] = set()
        unique = [t for t in buckets[k] if t not in seen and not seen.add(t)]  # type: ignore[func-returns-value]
        buckets[k] = unique
        log.info("Tier 3 bucket '%s': %d ticker", k, len(unique))

    return buckets


def screen_special_situations(buckets: dict[str, list[str]],
                               tier1_set: set[str],
                               tier2_set: set[str],
                               top_n: int = 15,
                               max_workers: int = 8) -> list[SpecialCandidate]:
    """Fase 2 Tier 3: fetch fondamentali e classifica special situations.

    Esclude ticker già presenti in Tier 1 o Tier 2 per evitare duplicati.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    # Unifica i bucket tenendo traccia del tipo
    all_tickers: list[tuple[str, str]] = []
    seen: set[str] = set()
    for bucket_name, tickers in buckets.items():
        for t in tickers:
            if t not in tier1_set and t not in tier2_set and t not in seen:
                all_tickers.append((t, bucket_name))
                seen.add(t)

    log.info("Tier 3 Fase 1/2: info fetch su %d ticker unici...", len(all_tickers))
    phase1: list[tuple[str, dict, str]] = []
    ticker_to_bucket = {t: b for t, b in all_tickers}

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(fetch_info_only, t): t for t, _ in all_tickers}
        for fut in as_completed(futs):
            try:
                result = fut.result()
            except Exception:
                continue
            if result is None:
                continue
            info = result["info"]
            # Filtro quick: deve avere dati base
            mc = info.get("marketCap", 0) or 0
            if mc < CONFIG["min_market_cap_million"] * 1e6:
                continue
            bucket = ticker_to_bucket.get(result["ticker"], "deep_value_pe")
            phase1.append((result["ticker"], info, bucket))

    log.info("Tier 3 Fase 2/2: fondamentali su %d ticker...", len(phase1))
    candidates: list[SpecialCandidate] = []

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(fetch_remaining, tkr, inf): (tkr, bkt)
                for tkr, inf, bkt in phase1}
        for fut in as_completed(futs):
            tkr, bkt = futs[fut]
            try:
                data = fut.result()
            except Exception:
                continue
            if data is None:
                continue
            info = data["info"]
            mc = info.get("marketCap", 0) or 0
            price = info.get("currentPrice") or info.get("regularMarketPrice")
            if not price:
                continue
            market, _ = detect_market(info)
            sector = info.get("sector", "")
            m, inter = compute_metrics(data)

            # Piotroski rapido
            pf, _ = compute_piotroski(info, data["financials"],
                                       data["balance_sheet"], data["cashflow"])

            # Price change 1y
            hist = data.get("history")
            pc_1y = None
            if hist is not None and not hist.empty and len(hist) >= 252:
                p_old = float(hist["Close"].iloc[-252])
                if p_old > 0:
                    pc_1y = round((price - p_old) / p_old, 4)

            # FCF positivo?
            fcf_pos = (m.fcf_margin is not None and m.fcf_margin > 0)

            # Scoring Tier 3
            score = 0.0
            if bkt == "deep_value_pe":
                pe = info.get("trailingPE")
                score += max(0, (8 - (pe or 8))) * 2  # max +16 con PE=0
                if pf and pf >= 6:
                    score += 10
                if fcf_pos:
                    score += 8
            elif bkt == "deep_value_pb":
                pb = m.pb_ratio
                if pb and pb < 0.8:
                    score += (0.8 - pb) * 50   # max 40 con P/B=0
                if pf and pf >= 6:
                    score += 10
                if m.roe and m.roe > 0.10:
                    score += 8
            elif bkt == "fallen_angel":
                dy = m.dividend_yield
                if dy and dy > 0.06:
                    score += dy * 100            # max ~15 con yield 15%
                if pf and pf >= 5:
                    score += 8                   # dividendo ancora coperto
                if fcf_pos:
                    score += 10                  # cash flow support

            sc = SpecialCandidate(
                ticker=data["ticker"],
                name=info.get("longName") or info.get("shortName") or data["ticker"],
                sector=sector, industry=info.get("industry", ""),
                market=market, price=price,
                market_cap_million=round(mc / 1e6, 1) if mc else None,
                situation_type=bkt,
                pe_ratio=info.get("trailingPE"),
                pb_ratio=m.pb_ratio,
                div_yield=m.dividend_yield,
                price_change_1y=pc_1y,
                piotroski_f=pf,
                fcf_positive=fcf_pos,
                situation_score=round(score, 1),
            )
            candidates.append(sc)

    candidates.sort(key=lambda c: c.situation_score, reverse=True)
    log.info("Tier 3 special situations: %d candidati", len(candidates))
    return candidates[:top_n]


def output_results(cands, out_dir, top_n=30,
                    speculative_cands: Optional[list] = None,
                    special_cands: Optional[list] = None,
                    market_context: Optional[dict] = None,
                    filiere_data: Optional[dict] = None):
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
            "mvf_vote_1000": c.mvf_vote_1000,
            "instrument_class": c.instrument_class,
            "iqi_100": (c.iqi_score or {}).get("total"),
            "gate_attivi": ",".join((c.quality_gates or {}).get("active", [])),
            "netto_italia": (c.net_yield or {}).get("net_italy"),
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

    spec_list = []
    if speculative_cands:
        for sc in speculative_cands:
            spec_list.append({
                "ticker": sc.ticker, "name": sc.name, "sector": sc.sector,
                "industry": sc.industry, "market": sc.market,
                "price": sc.price,
                "market_cap_M": sc.market_cap_million,
                "speculative_score": sc.speculative_score,
                "signal_count": sc.signal_count,
                "signals": sc.signal_labels,
                "price_change_30d": sc.price_change_30d,
                "price_change_90d": sc.price_change_90d,
                "volume_ratio_3d": sc.volume_ratio_3d,
                "revenue_growth_yoy": sc.revenue_growth_yoy,
                "short_float": sc.short_float,
                "notes": sc.notes,
            })

    special_list = []
    if special_cands:
        for sc in special_cands:
            special_list.append({
                "ticker": sc.ticker, "name": sc.name, "sector": sc.sector,
                "industry": sc.industry, "market": sc.market,
                "price": sc.price, "market_cap_M": sc.market_cap_million,
                "situation_type": sc.situation_type,
                "situation_score": sc.situation_score,
                "pe": sc.pe_ratio, "pb": sc.pb_ratio,
                "div_yield": sc.div_yield,
                "price_change_1y": sc.price_change_1y,
                "piotroski_f": sc.piotroski_f,
                "fcf_positive": sc.fcf_positive,
                "notes": sc.notes,
            })

    payload = {
        "date": date_tag, "n_screened": len(cands), "n_passing": len(top),
        "market_context": market_context or {},
        "candidates": [{
            "ticker": c.ticker, "name": c.name, "sector": c.sector,
            "industry": c.industry, "market": c.market, "currency": c.currency,
            "price": c.price, "market_cap_M": c.market_cap_million,
            "tags": c.strategy_tags, "score": c.composite_score,
            "metrics": {k: v for k, v in asdict(c.metrics).items() if v is not None},
            "warnings": [k for k, v in asdict(c.soft_filters).items() if v],
            "notes": c.notes,
            "piotroski_f": c.piotroski_f,
            "piotroski_factors": c.piotroski_factors,
            "moat_score": c.moat_score,
            "moat_signals": c.moat_signals,
            "dcf_upside_pct": c.dcf_upside_pct,
            "filiera_tag": c.filiera_tag,
            "earnings_acceleration": c.earnings_acceleration,
            # MVF v4.1
            "instrument_class": c.instrument_class,
            "instrument_base": c.instrument_base,
            "mvf_vote_1000": c.mvf_vote_1000,
            "mvf_vote_100": c.mvf_vote_100,
            "mvf_engine_note": c.mvf_engine_note,
            "mvf_valuation": c.mvf_valuation,
            "mvf_red_flags": c.mvf_red_flags,
            "quality_gates": c.quality_gates,
            "iqi_score": c.iqi_score,
            "mvf_iqi_reconciliation": c.mvf_iqi_reconciliation,
            "net_yield": c.net_yield,
            "confidence_score": c.confidence_score,
            "variation_5y": c.variation_5y,
            "intrinsic_value": c.intrinsic_value,
            "ideal_purchase_price_mos": c.ideal_purchase_price_mos,
            "margin_of_safety_pct": c.margin_of_safety_pct,
        } for c in top],
        "speculative_candidates": spec_list,
        "special_situations": special_list,
        "filiere_strategiche": filiere_data or {},
    }
    with open(json_path, "w") as f:
        json.dump(payload, f, indent=2, default=str)
    return csv_path, json_path


# =============================================================================
# SEZIONE 9 — CLI
# =============================================================================

def main():
    p = argparse.ArgumentParser(description="MVF v3.0 Stock Screener (tre tier + market context)")
    p.add_argument("--region",
                   choices=["US", "EU", "ASIA", "GLOBAL", "LATAM", "AFRICA_ME"],
                   default="GLOBAL")
    p.add_argument("--strategy", choices=["income", "post_news", "quality", "all"], default="all")
    p.add_argument("--min-mcap", type=int, default=CONFIG["min_market_cap_million"])
    p.add_argument("--top", type=int, default=500,
                   help="Top N candidati con valutazione MVF v3.0 completa (default 500)")
    p.add_argument("--top-speculative", type=int, default=25)
    p.add_argument("--top-special", type=int, default=15)
    p.add_argument("--limit-per-market", type=int, default=50,
                   help="Righe TV per singolo mercato dopo pre-filtri qualità (default 50)")
    p.add_argument("--universe-cap", type=int, default=600,
                   help="Cap finale universe Tier 1 prima di yfinance (default 600)")
    p.add_argument("--no-speculative", action="store_true")
    p.add_argument("--no-special", action="store_true")
    p.add_argument("--no-market-context", action="store_true")
    p.add_argument("--no-filiere", action="store_true",
                   help="Disattiva screener filiere strategiche dedicato")
    p.add_argument("--sector", default=None)
    p.add_argument("--output", type=Path, default=Path("./data/screener_results"))
    args = p.parse_args()

    CONFIG["min_market_cap_million"] = args.min_mcap

    # Inizializza sessione yfinance prima di qualsiasi chiamata
    log.info("Inizializzazione sessione yfinance...")
    _refresh_yfinance_session()

    # ---- Market Context Layer (in parallelo con Tier 1 TV fetch) ----
    market_ctx: dict = {}
    if not args.no_market_context:
        log.info("=== MARKET CONTEXT: fetch ETF settoriali e regionali ===")
        market_ctx = build_market_context()
        log.info("Market context: %d settori, %d regioni, %d macro",
                 len(market_ctx.get("sectors", {})),
                 len(market_ctx.get("regions", {})),
                 len(market_ctx.get("macro", {})))

    # ---- Tier 1: Quality/Income Universe ----
    log.info("=== TIER 1: Quality/Income Universe (mcap>%dM, limit/mkt=%d) ===",
             args.min_mcap, args.limit_per_market)
    tickers = build_universe_tradingview(
        region=args.region, min_mcap_m=args.min_mcap,
        min_price=CONFIG["min_price_usd"],
        limit_per_market=args.limit_per_market,
        sector_filter=args.sector,
        total_limit=args.universe_cap,
    )
    if not tickers and args.region in ("US", "GLOBAL") and FINVIZ_OK:
        log.warning("Tentativo fallback finvizfinance...")
        tickers = build_universe_finviz_fallback(args.min_mcap, args.sector, args.limit_per_market)
    if not tickers:
        log.error("Universe Tier 1 vuoto.")
        sys.exit(1)

    cands = screen_universe(tickers, strategy=args.strategy)
    log.info("Tier 1 candidati post-filtri: %d", len(cands))

    # Sector-relative scoring (aggiusta score in funzione del peer group)
    compute_sector_relative_scores(cands)
    log.info("Sector-relative scoring applicato")

    tier1_set = set(tickers)

    # Refresh sessione yfinance tra i tier per evitare 401 Unauthorized
    # (il crumb Yahoo Finance si invalida dopo molte richieste parallele)
    _refresh_yfinance_session()

    # ---- Tier 2: Speculative / Catalyst Universe ----
    spec_cands: list[SpeculativeCandidate] = []
    tier2_set: set[str] = set()
    if not args.no_speculative:
        log.info("=== TIER 2: Speculative/Catalyst Universe ===")
        spec_tickers = build_speculative_universe_tv(region=args.region)
        if spec_tickers:
            spec_tickers_new = [t for t in spec_tickers if t not in tier1_set]
            log.info("Tier 2: %d ticker nuovi (esclusi %d già in Tier 1)",
                     len(spec_tickers_new), len(spec_tickers) - len(spec_tickers_new))
            spec_cands = screen_speculative_universe(spec_tickers_new, top_n=args.top_speculative,
                                                      max_workers=15)
            tier2_set = {sc.ticker for sc in spec_cands}
            log.info("Tier 2 candidati: %d", len(spec_cands))
        else:
            log.warning("Tier 2 universe vuoto.")

    _refresh_yfinance_session()

    # ---- Tier 3: Special Situations ----
    special_cands: list[SpecialCandidate] = []
    if not args.no_special:
        log.info("=== TIER 3: Special Situations (deep value + fallen angels) ===")
        sp_buckets = build_special_situations_tv(region=args.region)
        if any(sp_buckets.values()):
            special_cands = screen_special_situations(
                sp_buckets, tier1_set, tier2_set, top_n=args.top_special,
                max_workers=15,
            )
            log.info("Tier 3 special situations: %d", len(special_cands))
        else:
            log.warning("Tier 3 universe vuoto.")

    # ---- Filiere strategiche (screener dedicato) ----
    filiere_data: dict = {}
    if not args.no_filiere:
        log.info("=== FILIERE STRATEGICHE: screener dedicato ===")
        try:
            filiere_data = filiere_mod.run_all_filiere()
            total_fil = sum(len(v) for v in filiere_data.values())
            log.info("Filiere screener: %d filiere, %d candidati totali",
                     len(filiere_data), total_fil)
        except Exception as e:
            log.warning("Filiere screener fallito: %s", e)

    # ---- Output ----
    csv_path, json_path = output_results(
        cands, args.output, top_n=args.top,
        speculative_cands=spec_cands,
        special_cands=special_cands,
        market_context=market_ctx,
        filiere_data=filiere_data,
    )
    log.info("Output: %s | %s", csv_path, json_path)
    log.info("TOTALE — T1:%d quality (MVF v3.0) | T2:%d catalyst | T3:%d special | filiere:%d | ctx:%s",
             min(len(cands), args.top), len(spec_cands), len(special_cands),
             sum(len(v) for v in filiere_data.values()) if filiere_data else 0,
             "ok" if market_ctx else "skip")


if __name__ == "__main__":
    main()
