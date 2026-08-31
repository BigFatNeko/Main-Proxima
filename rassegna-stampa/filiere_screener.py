"""
Filiere strategiche — screener dedicato.

Per ciascuna filiera lancia una query TradingView mirata con criteri propri:
  - filtri per industry/sector specifici della filiera
  - cap market cap differenziato
  - ranking per metriche rilevanti (yield + value + momentum)

Filiere coperte (15):
  Classiche: semiconduttori, difesa, uranio_nucleare, energia_oilgas,
             rare_earth_metalli, batterie_litio_storage, gestione_rifiuti,
             consumer_staples, helium_gas_industriali
  Nuove (poco analizzate): agroalimentare_upstream, siderurgia_metalli_speciali,
             shipping_marittimo, infrastrutture_idriche,
             riassicurazione_specialty, packaging_foreste

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
        # TV industry: uranio è "Uranium" o dentro "Other Industrial Metals & Mining"
        "industries": ["Uranium", "Other Industrial Metals & Mining"],
        "sectors": [],
        "min_mcap_m": 50,
        "max_per_filiera": 25,
        "bottleneck_keywords": ["uranium", "nuclear", "fuel cycle"],
    },
    "energia_oilgas": {
        # TV industries: E&P, integrated, midstream, refining
        "industries": ["Oil & Gas E&P", "Oil & Gas Integrated",
                       "Oil & Gas Midstream", "Oil & Gas Refining & Marketing",
                       "Oil & Gas Drilling", "Oil & Gas Equipment & Services"],
        "sectors": [],
        "min_mcap_m": 300,
        "max_per_filiera": 35,
        "bottleneck_keywords": ["LNG", "midstream", "pipeline", "oil", "gas", "refin"],
    },
    "rare_earth_metalli": {
        # TV: metalli critici dentro "Other Industrial Metals & Mining" + "Specialty Chemicals"
        "industries": ["Other Industrial Metals & Mining", "Specialty Chemicals",
                       "Industrial Metals & Mining", "Copper"],
        "sectors": [],
        "min_mcap_m": 100,
        "max_per_filiera": 30,
        "bottleneck_keywords": ["rare earth", "neodymium", "lithium",
                                "cobalt", "tungsten", "nickel", "copper", "zinc"],
    },
    "batterie_litio_storage": {
        # TV: batterie → "Electronic Components"; EV → "Auto Manufacturers"; storage → "Specialty Chemicals"
        "industries": ["Electronic Components", "Specialty Chemicals",
                       "Auto Manufacturers", "Auto Parts"],
        "sectors": [],
        "min_mcap_m": 100,
        "max_per_filiera": 25,
        "bottleneck_keywords": ["battery", "lithium", "storage", "EV", "electric"],
    },
    "gestione_rifiuti": {
        # "Environmental & Waste Services" non è un'industria TV standard
        "industries": ["Waste Management",
                       "Pollution & Treatment Controls",
                       "Engineering & Construction"],
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
        # Air Products, Linde, Air Liquide, Messer → "Specialty Chemicals" in TV
        # Distributori gas industriali → "Industrial Distribution"
        "industries": ["Specialty Chemicals", "Industrial Distribution",
                       "Chemicals - Specialty"],
        "sectors": [],
        "min_mcap_m": 300,
        "max_per_filiera": 15,
        "bottleneck_keywords": ["helium", "industrial gas", "air", "gas", "linde",
                                "praxair", "liquid"],
    },

    # ── NUOVE FILIERE POCO ANALIZZATE ─────────────────────────────────────────

    "agroalimentare_upstream": {
        # Fertilizzanti/sementi/pesticidi → "Agricultural Inputs" in TV
        # Macchinari agricoli (Deere, AGCO, CNH) → "Agricultural & Farm Machinery" o "Farm & Heavy Construction Machinery"
        "industries": ["Agricultural Inputs",
                       "Agricultural & Farm Machinery",
                       "Farm & Heavy Construction Machinery",
                       "Farm Machinery"],
        "sectors": [],
        "min_mcap_m": 200,
        "max_per_filiera": 25,
        "bottleneck_keywords": ["fertilizer", "potash", "nitrogen", "seed",
                                "crop protection", "pesticide", "agro", "farm",
                                "harvest", "agricultural"],
    },

    "siderurgia_metalli_speciali": {
        # Acciaio, alluminio, metalli speciali (titanio, nichel, tungsteno).
        # Cicliche con forte pricing power in fasi di capex industriale.
        # Spesso scambiate a multipli bassi anche in peak cycle (value trap? no).
        # Nucor, Steel Dynamics, ArcelorMittal, Alcoa, Norsk Hydro.
        "industries": ["Steel", "Aluminum"],
        "min_mcap_m": 300,
        "max_per_filiera": 25,
        "bottleneck_keywords": ["steel", "aluminum", "stainless", "titanium",
                                "specialty steel", "flat rolled", "long products"],
    },

    "shipping_marittimo": {
        # Container, dry bulk, tankers. Settore massicciamente ciclico,
        # spesso scambiato a discount enorme sul NAV durante i bust.
        # Catalysts: rerouting Suez/Panama, domanda LNG, reshoring supply chain.
        # ZIM, Star Bulk, Nordic American Tankers, Hafnia, TORM.
        "industries": ["Marine Shipping"],
        "min_mcap_m": 100,
        "max_per_filiera": 20,
        "bottleneck_keywords": ["container", "bulk", "tanker", "LNG carrier",
                                "VLCC", "Panamax", "shipping", "fleet"],
    },

    "infrastrutture_idriche": {
        # TV industry per water utilities specifiche (non tutte le Utilities)
        "industries": ["Water Utilities", "Utilities - Regulated Water",
                       "Utilities—Regulated Water"],
        "sectors": [],
        "min_mcap_m": 200,
        "max_per_filiera": 20,
        "bottleneck_keywords": ["water", "wastewater", "desalination",
                                "purification", "treatment", "utility", "utilities"],
    },

    "riassicurazione_specialty": {
        # TV industries per insurance, separate per tipo (non il macro-settore Finance)
        "industries": ["Insurance—Reinsurance", "Insurance - Reinsurance",
                       "Reinsurance", "Insurance—Property & Casualty",
                       "Insurance - Property & Casualty",
                       "Insurance—Specialty", "Insurance—Life"],
        "sectors": [],
        "min_mcap_m": 500,
        "max_per_filiera": 20,
        "bottleneck_keywords": ["reinsurance", "insurance", "casualty",
                                "underwriting", "assurance", "life insurance"],
    },

    "packaging_foreste": {
        # TV industries: packaging, carta, legno — più specifici del macro-settore
        "industries": ["Packaging & Containers", "Containers & Packaging",
                       "Paper & Paper Products", "Paper Products",
                       "Lumber & Wood Production", "Forest Products"],
        "sectors": [],
        "min_mcap_m": 200,
        "max_per_filiera": 20,
        "bottleneck_keywords": ["packaging", "cardboard", "corrugated",
                                "paper", "lumber", "forest", "timber", "pulp"],
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
    """Lancia query TradingView per una filiera.

    Supporta sia filtro per industry (preciso) sia per sector (fallback robusto).
    Il dizionario definizione può avere:
      "industries": [...] → query per Column("industry") == val
      "sectors":    [...] → query per Column("sector")   == val
    Entrambe possono coesistere; i risultati vengono uniti e deduplicati.
    """
    if not TV_OK:
        return []

    from concurrent.futures import ThreadPoolExecutor, as_completed

    all_rows: list[dict] = []
    industries = definition.get("industries", [])
    sectors    = definition.get("sectors", [])
    min_mcap   = definition["min_mcap_m"] * 1_000_000

    def query_one(mkt: str, col: str, val: str) -> list[dict]:
        """col = 'industry' oppure 'sector'."""
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
                     Column(col) == val,
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
            log.warning("filiera=%s mkt=%s %s=%s err=%s",
                        filiera_name, mkt, col, val, e)
        return rows

    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = []
        for mkt in markets:
            for ind in industries:
                futs.append(ex.submit(query_one, mkt, "industry", ind))
            for sec in sectors:
                futs.append(ex.submit(query_one, mkt, "sector", sec))
        for fut in as_completed(futs):
            all_rows.extend(fut.result())

    log.info("Filiera %s: %d righe prima di dedup", filiera_name, len(all_rows))

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

    # Riepilogo finale — visibile in Actions
    ok = [f for f, v in result.items() if v]
    empty = [f for f, v in result.items() if not v]
    log.info("Filiere OK (%d): %s", len(ok), ", ".join(ok))
    if empty:
        log.warning("Filiere vuote (%d): %s", len(empty), ", ".join(empty))
    return result


if __name__ == "__main__":
    import argparse, json as _json
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        datefmt="%H:%M:%S")
    ap = argparse.ArgumentParser(description="Debug filiere screener standalone")
    ap.add_argument("--filiera", default=None, help="Testa solo questa filiera")
    ap.add_argument("--markets", default=None, nargs="+", help="Override mercati (default: tutti)")
    args = ap.parse_args()
    mkts = args.markets or FILIERE_MARKETS
    if args.filiera:
        if args.filiera not in FILIERE_DEFINITIONS:
            print(f"Filiera sconosciuta: {args.filiera}. Disponibili: {list(FILIERE_DEFINITIONS)}")
            raise SystemExit(1)
        defs = {args.filiera: FILIERE_DEFINITIONS[args.filiera]}
    else:
        defs = FILIERE_DEFINITIONS
    print(f"\n{'='*60}")
    print(f"TEST FILIERE  —  {len(defs)} filiere × {len(mkts)} mercati")
    print(f"{'='*60}\n")
    for fname, fdef in defs.items():
        cands = screen_filiera_tv(fname, fdef, mkts)
        status = "✓" if cands else "✗ VUOTA"
        print(f"  {status}  {fname}: {len(cands)} candidati")
        for c in cands[:3]:
            print(f"         {c['tv_ticker']:20s} {c['name'][:35]:35s} mcap=${c['market_cap']/1e9:.1f}B")
        print()
