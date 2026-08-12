"""Percorso dati US SENZA yfinance: SEC EDGAR (fondamentali [P]) +
stockanalysis.com (prezzi). Serve quando yfinance e' irraggiungibile
(rate limit) e, in prospettiva, e' l'architettura corretta della spec:
EDGAR XBRL = ground truth [P] (Sez. 6-bis). Copre solo US-listed/ADR.

Assembla il dict `raw` nella stessa forma prodotta da fetchers.fetch_yf,
cosi' metrics/scoring/gate/iqi non cambiano.
"""
from __future__ import annotations

import json
import logging
import os
import time
from datetime import date

import requests as std_requests

import config
import fetchers

log = logging.getLogger("fetch_us")

# us-gaap concept candidates (primo che matcha vince)
CONCEPTS = {
    "revenue": ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues",
                "SalesRevenueNet", "RevenueFromContractWithCustomerIncludingAssessedTax"],
    "gross_profit": ["GrossProfit"],
    "operating_income": ["OperatingIncomeLoss"],
    "net_income": ["NetIncomeLoss"],
    "pretax_income": ["IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
                      "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments"],
    "tax_provision": ["IncomeTaxExpenseBenefit"],
    "diluted_eps": ["EarningsPerShareDiluted"],
    "interest_expense": ["InterestExpense", "InterestExpenseNonoperating",
                         "InterestIncomeExpenseNonoperatingNet"],
    "rd": ["ResearchAndDevelopmentExpense"],
    "da_cf": ["DepreciationDepletionAndAmortization", "DepreciationAmortizationAndAccretionNet",
              "DepreciationAndAmortization"],
    "total_assets": ["Assets"],
    "equity": ["StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"],
    "cash": ["CashAndCashEquivalentsAtCarryingValue",
             "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"],
    "current_assets": ["AssetsCurrent"],
    "current_liab": ["LiabilitiesCurrent"],
    "total_liab": ["Liabilities"],
    "retained": ["RetainedEarningsAccumulatedDeficit"],
    "goodwill": ["Goodwill"],
    "cfo": ["NetCashProvidedByUsedInOperatingActivities",
            "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"],
    "capex": ["PaymentsToAcquirePropertyPlantAndEquipment",
              "PaymentsToAcquireProductiveAssets"],
    "sbc": ["ShareBasedCompensation", "AllocatedShareBasedCompensationExpense"],
    "dividends_paid": ["PaymentsOfDividendsCommonStock", "PaymentsOfDividends"],
    "shares": ["WeightedAverageNumberOfDilutedSharesOutstanding",
               "WeightedAverageNumberOfSharesOutstandingBasic"],
    "ltd_noncurrent": ["LongTermDebtNoncurrent", "LongTermDebt"],
    "ltd_current": ["LongTermDebtCurrent", "DebtCurrent"],
    "dps": ["CommonStockDividendsPerShareDeclared", "CommonStockDividendsPerShareCashPaid"],
}
INSTANT = {"total_assets", "equity", "cash", "current_assets", "current_liab",
           "total_liab", "retained", "goodwill", "ltd_noncurrent", "ltd_current"}


def _companyfacts(cik: int) -> dict | None:
    cache = os.path.join(config.CACHE_DIR, f"facts_{cik}.json")
    if os.path.exists(cache) and time.time() - os.path.getmtime(cache) < 3 * 86400:
        return json.load(open(cache))
    facts = fetchers._edgar_get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json")
    if facts:
        os.makedirs(config.CACHE_DIR, exist_ok=True)
        json.dump(facts, open(cache, "w"))
    return facts


def _submission(cik: int) -> dict:
    cache = os.path.join(config.CACHE_DIR, f"sub_{cik}.json")
    if os.path.exists(cache) and time.time() - os.path.getmtime(cache) < 7 * 86400:
        return json.load(open(cache))
    data = fetchers._edgar_get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json") or {}
    if data:
        json.dump(data, open(cache, "w"))
    return data


def _concept_by_fy(facts: dict, names: list[str], instant: bool) -> dict[int, float]:
    """{fiscal_year: value} per il primo concept disponibile, prendendo il
    fatto FY con la data 'end' piu' recente per ciascun anno fiscale."""
    gaap = facts.get("facts", {}).get("us-gaap", {})
    merged: dict[int, float] = {}          # fy -> valore
    for c in names:                        # candidati in ordine di preferenza
        node = gaap.get(c)
        if not node:
            continue
        this: dict[int, tuple[str, float]] = {}
        for unit, entries in node.get("units", {}).items():
            if unit not in ("USD", "USD/shares", "shares"):
                continue
            for e in entries:
                if e.get("form") not in ("10-K", "20-F", "40-F"):
                    continue
                if e.get("fp") != "FY":
                    continue
                fy, en = e.get("fy"), e.get("end")
                if not fy or not en:
                    continue
                if not instant:
                    st = e.get("start")
                    if st:
                        try:
                            if (date.fromisoformat(en) - date.fromisoformat(st)).days < 300:
                                continue
                        except ValueError:
                            pass
                fy = int(fy)
                if fy not in this or en > this[fy][0]:
                    this[fy] = (en, float(e["val"]))
        for fy, (_, v) in this.items():    # primo candidato che copre l'anno vince
            merged.setdefault(fy, v)
    return merged


def _sa_prices(ticker: str) -> dict[str, float]:
    """Serie prezzi (adjusted close) settimanale 5Y da stockanalysis.com."""
    base = ticker.split(".")[0]
    url = f"https://stockanalysis.com/api/symbol/s/{base}/history?range=5Y&period=Weekly"
    try:
        r = std_requests.get(url, timeout=20,
                             headers={"User-Agent": "Mozilla/5.0 Proxima"})
        if r.status_code != 200:
            return {}
        data = r.json().get("data", [])
        return {row["t"]: float(row.get("a") or row.get("c"))
                for row in data if row.get("t")}
    except Exception as e:
        log.debug("stockanalysis %s: %s", ticker, str(e)[:80])
        return {}


def build_raw_us(ticker: str) -> dict | None:
    """Ricostruisce `raw` (forma fetch_yf) da EDGAR + stockanalysis. None se
    il ticker non e' su EDGAR (non US-listed)."""
    cik = fetchers._cik_for(ticker)
    if not cik:
        return None
    facts = _companyfacts(cik)
    if not facts:
        return None
    raw_fy = {k: _concept_by_fy(facts, names, k in INSTANT)
              for k, names in CONCEPTS.items()}
    # asse temporale comune: anni fiscali di Assets (sempre presente), desc, max 6
    axis = sorted(raw_fy.get("total_assets", {}), reverse=True)[:6]
    if not axis:
        axis = sorted(raw_fy.get("net_income", {}), reverse=True)[:6]
    if not axis:
        return None

    def series(key):
        d = raw_fy.get(key, {})
        return [d.get(fy) for fy in axis]

    total_debt = []
    for fy in axis:
        nc = raw_fy.get("ltd_noncurrent", {}).get(fy)
        cu = raw_fy.get("ltd_current", {}).get(fy)
        total_debt.append((nc or 0) + (cu or 0) if (nc or cu) else None)

    da = series("da_cf")
    oi = series("operating_income")
    ebitda = [(o + d) if (o is not None and d is not None) else None
              for o, d in zip(oi, da)]

    sub = _submission(cik)
    name = sub.get("name") or ticker
    sic_desc = sub.get("sicDescription") or ""

    prices = _sa_prices(ticker)
    cur_price = None
    if prices:
        cur_price = prices[max(prices)]

    eps = series("diluted_eps")
    shares0 = series("shares")[0]
    market_cap = cur_price * shares0 if (cur_price and shares0) else None
    pe = (cur_price / eps[0]) if (cur_price and eps and eps[0] and eps[0] > 0) else None

    # dividendi: da DPS EDGAR [P]. Sintetizza dividends_series annuale.
    dps_by_fy = raw_fy.get("dps", {})
    dividends_series = {f"{fy}-07-01": v for fy, v in dps_by_fy.items() if v}

    info = {
        "symbol": ticker, "shortName": name, "longName": name,
        "sector": _sector_from_sic(sic_desc), "industry": sic_desc,
        "country": "United States", "currency": "USD",
        "currentPrice": cur_price, "regularMarketPrice": cur_price,
        "beta": None, "marketCap": market_cap, "trailingPE": pe,
        "sharesOutstanding": shares0,
    }
    raw = {
        "ticker": ticker, "info": info,
        "revenue": series("revenue"), "gross_profit": series("gross_profit"),
        "operating_income": oi, "ebit": oi, "ebitda": ebitda,
        "net_income": series("net_income"), "pretax_income": series("pretax_income"),
        "tax_provision": series("tax_provision"), "diluted_eps": eps,
        "interest_expense": series("interest_expense"), "rd": series("rd"),
        "da_income": da, "da_cf": da,
        "total_assets": series("total_assets"), "equity": series("equity"),
        "total_debt": total_debt, "cash": series("cash"),
        "current_assets": series("current_assets"), "current_liab": series("current_liab"),
        "total_liab": series("total_liab"), "retained": series("retained"),
        "working_capital": [], "goodwill": series("goodwill"),
        "shares": series("shares"), "cfo": series("cfo"), "capex": series("capex"),
        "fcf_yf": [], "sbc": series("sbc"), "dividends_paid": series("dividends_paid"),
        "buyback_cf": [],
        "dividends_series": dividends_series, "prices": prices,
        "_source": "edgar+stockanalysis",
    }
    return raw


SIC_SECTOR = [
    (("national commercial banks", "state commercial banks", "savings institution",
      "security brokers", "investment", "insurance", "finance"), "Financial Services"),
    (("real estate investment trusts", "real estate"), "Real Estate"),
    (("electric", "gas", "water supply", "utilit"), "Utilities"),
    (("pharmaceutical", "biological", "medicinal"), "Healthcare"),
    (("beverages", "food", "tobacco", "grocery", "retail-drug", "soap"), "Consumer Defensive"),
    (("semiconductor", "computer", "software", "services-prepackaged"), "Technology"),
    (("crude petroleum", "petroleum refining", "mining", "gold", "coal"), "Energy"),
    (("retail", "eating places", "apparel"), "Consumer Cyclical"),
    (("aircraft", "guided missiles", "industrial", "machinery"), "Industrials"),
]


def _sector_from_sic(sic_desc: str) -> str:
    s = sic_desc.lower()
    for keys, sector in SIC_SECTOR:
        if any(k in s for k in keys):
            return sector
    return ""
