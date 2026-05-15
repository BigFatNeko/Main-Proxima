"""
Filiere strategiche — screener dedicato.

Per ciascuna filiera (semiconduttori, difesa, uranio, energia, batterie litio,
rare earth, gestione rifiuti, consumer staples, helium/gas industriali) lancia
una query TradingView mirata con criteri propri:
  - filtri per industry/sector specifici della filiera
  - cap market cap differenziato
  - ranking per metriche rilevanti (yield + value + momentum)

Output: candidati per filiera, ognuno con tag filiera + bottleneck score.
"""

from __future__ import annotations
import logging
from typing import Optional

log = logging.getLogger("filiere")

try:
    from tradingview_screener import Query, Column
    TV_OK = True
except ImportError:
    TV_OK = False


# Definizione filiere con industry TradingView e criteri specifici
FILIERE_DEFINITIONS = {
    "semiconduttori": {
        "industries": ["Semiconductors", "Semiconductor Equipment & Materials",
                       "Electronic Components"],
        "min_mcap_m": 500,
        "max_per_filiera": 40,
        "bottleneck_keywords": ["lithography", "EUV", "foundry", "fabless"],
    },
    "difesa": {
        "industries": ["Aerospace & Defense", "Defense"],
        "min_mcap_m": 300,
        "max_per_filiera": 30,
        "bottleneck_keywords": ["missile", "radar", "satellite", "drone"],
    },
    "uranio_nucleare": {
        "industries": ["Uranium", "Other Industrial Metals & Mining"],
        "min_mcap_m": 50,
        "max_per_filiera": 25,
        "bottleneck_keywords": ["uranium", "nuclear", "fuel cycle"],
    },
    "energia_oilgas": {
        "industries": ["Oil & Gas Integrated", "Oil & Gas E&P",
                       "Oil & Gas Midstream", "Oil & Gas Refining & Marketing",
                       "Oil & Gas Equipment & Services"],
        "min_mcap_m": 500,
        "max_per_filiera": 35,
        "bottleneck_keywords": ["LNG", "midstream", "pipeline"],
    },
    "rare_earth_metalli": {
        "industries": ["Other Precious Metals & Mining",
                       "Industrial Metals & Mining", "Specialty Chemicals",
                       "Copper"],
        "min_mcap_m": 100,
        "max_per_filiera": 30,
        "bottleneck_keywords": ["rare earth", "neodymium", "lithium",
                                "cobalt", "tungsten", "nickel"],
    },
    "batterie_litio_storage": {
        "industries": ["Lithium & Battery Tech", "Auto Parts",
                       "Electrical Equipment & Parts"],
        "min_mcap_m": 200,
        "max_per_filiera": 25,
        "bottleneck_keywords": ["battery", "lithium", "storage"],
    },
    "gestione_rifiuti": {
        "industries": ["Waste Management",
                       "Environmental & Waste Services",
                       "Pollution & Treatment Controls"],
        "min_mcap_m": 200,
        "max_per_filiera": 20,
        "bottleneck_keywords": ["landfill", "recycling", "hazardous"],
    },
    "consumer_staples": {
        "industries": ["Food Distribution", "Packaged Foods",
                       "Household & Personal Products",
                       "Beverages—Non-Alcoholic", "Tobacco"],
        "min_mcap_m": 500,
        "max_per_filiera": 30,
        "bottleneck_keywords": ["brand", "distribution"],
    },
    "helium_gas_industriali": {
        "industries": ["Industrial Distribution", "Specialty Industrial Machinery"],
        "min_mcap_m": 300,
        "max_per_filiera": 15,
        "bottleneck_keywords": ["helium", "industrial gas"],
    },
}


# Markets globali per le query filiere
FILIERE_MARKETS = [
    "america", "italy", "germany", "france", "spain", "netherlands",
    "switzerland", "uk", "sweden", "norway", "denmark", "japan", "china",
    "hong_kong", "korea", "australia", "canada"
]


def screen_filiera_tv(filiera_name: str, definition: dict,
                       markets: list[str]) -> list[dict]:
    """Lancia query TradingView per una filiera, una per (mercato, industry)."""
    if not TV_OK:
        return []

    from concurrent.futures import ThreadPoolExecutor, as_completed

    all_rows: list[dict] = []
    industries = definition["industries"]
    min_mcap = definition["min_mcap_m"] * 1_000_000

    def query_one(mkt: str, industry: str) -> list[dict]:
        rows: list[dict] = []
        try:
            q = (Query()
                 .set_markets(mkt)
                 .select("name", "close", "market_cap_basic",
                         "price_earnings_ttm", "sector", "industry",
                         "dividends_yield", "relative_volume_10d_calc",
                         "price_target_average")
                 .where(
                     Column("market_cap_basic") > min_mcap,
                     Column("close") > 1.0,
                     Column("industry") == industry,
                 )
                 .order_by("market_cap_basic", ascending=False)
                 .limit(50))
            _count, df = q.get_scanner_data()
            if df is None or df.empty:
                return rows
            for _, row in df.iterrows():
                rows.append({
                    "tv_ticker": row["ticker"],
                    "name": row.get("name", ""),
                    "industry": row.get("industry", ""),
                    "sector": row.get("sector", ""),
                    "market_cap": row.get("market_cap_basic") or 0,
                    "price": row.get("close") or 0,
                    "pe": row.get("price_earnings_ttm"),
                    "div_yield": row.get("dividends_yield") or 0,
                    "rel_vol": row.get("relative_volume_10d_calc") or 1.0,
                    "price_target": row.get("price_target_average"),
                    "filiera": filiera_name,
                })
        except Exception as e:
            log.debug("filiera=%s mkt=%s industry=%s err=%s",
                      filiera_name, mkt, industry, e)
        return rows

    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = []
        for mkt in markets:
            for industry in industries:
                futs.append(ex.submit(query_one, mkt, industry))
        for fut in as_completed(futs):
            all_rows.extend(fut.result())

    # dedupe per ticker
    seen = set()
    unique = []
    for r in all_rows:
        if r["tv_ticker"] not in seen:
            seen.add(r["tv_ticker"])
            unique.append(r)

    # bottleneck score = blend market cap (proxy importanza filiera) + rel vol
    # + analyst upside
    def filiera_score(r):
        s = 0.0
        # Market cap log → 0-5
        mc = r["market_cap"]
        if mc > 0:
            import math
            s += min(math.log10(mc / 1e6), 5)
        # Relative volume > 1.5 → segnale attivo
        rv = r["rel_vol"]
        if rv > 2.0:
            s += 2.0
        elif rv > 1.5:
            s += 1.0
        # Analyst upside
        if r["price_target"] and r["price"] > 0:
            upside = (r["price_target"] - r["price"]) / r["price"]
            if upside > 0.20:
                s += 2.0
            elif upside > 0.10:
                s += 1.0
        # Dividend yield
        dy = r["div_yield"]
        if dy > 0.04:
            s += 1.0
        # PE moderato (5-25)
        pe = r["pe"]
        if pe and 5 < pe < 25:
            s += 1.0
        return s

    unique.sort(key=filiera_score, reverse=True)
    max_n = definition.get("max_per_filiera", 25)
    return unique[:max_n]


def run_all_filiere() -> dict:
    """Lancia screening per tutte le filiere. Ritorna dict filiera→[candidati]."""
    log.info("Filiere screener: avvio %d filiere su %d mercati",
             len(FILIERE_DEFINITIONS), len(FILIERE_MARKETS))
    result = {}
    for fname, fdef in FILIERE_DEFINITIONS.items():
        try:
            candidates = screen_filiera_tv(fname, fdef, FILIERE_MARKETS)
            result[fname] = candidates
            log.info("Filiera %s: %d candidati", fname, len(candidates))
        except Exception as e:
            log.warning("Filiera %s fallita: %s", fname, e)
            result[fname] = []
    return result
