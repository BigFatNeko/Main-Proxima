"""Percorso dati UE via ESEF (fonte UFFICIALE [P], multi-anno) — T22.

ESEF = formato XBRL obbligatorio per le quotate UE dal 2021. filings.xbrl.org
espone i depositi in xBRL-JSON (come companyfacts SEC), gratis e senza chiave.
Catena: ticker -> LEI (GLEIF) -> depositi ESEF (filings.xbrl.org) -> fatti IFRS.

I fondamentali (conto economico, stato patrimoniale, rendiconto) vengono da
ESEF con tag [P] e profondita' multi-anno; i dati di MERCATO (prezzo, azioni,
market cap, dividendo, beta) non stanno nei bilanci -> si prendono da
TradingView e si innestano. Cosi' i titoli UE salgono da snapshot [U] a
[P] multi-anno.

NB: i file ESEF sono grandi (~10-15 MB) -> uso mirato (rosa/on-demand), non
sull'intero universo. Cache su disco.
"""
from __future__ import annotations

import json
import logging
import os
import time
from datetime import date

import requests as std_requests

import config
import fetch_tv

log = logging.getLogger("fetch_esef")

# LEI curati per i nomi UE piu' probabili (evita il fuzzy-match GLEIF).
LEI_MAP = {
    "ENI.MI": "BUCRF72VH5RBN7X3VL35", "ENEL.MI": "WOCMU6HgamA7SVYFFN63",
    "ISP.MI": "2W8N8UU78PMDQKZENC08", "UCG.MI": "549300TRUWO2CD2G5692",
    "RACE.MI": "8156007268CD8C4A0F60", "STLAM.MI": "AVUKW2Z9VOAA1FTG4885",
    "G.MI": "PL6VZ6D6D5R6VUFTT667", "ASML.AS": "724500Y6DUVHQD6OXN27",
    "PHIA.AS": "724500O5UN2VMFBBS618", "MC.PA": "969500Q2DGQCUQMHY740",
    "OR.PA": "529900S4RQU5NJ4LP136", "SAN.PA": "549300E9PC51EN656011",
    "AIR.PA": "MZI1DHDU2GGUBB5UU671", "SAP.DE": "529900D6BF99LW9R2E68",
    "SIE.DE": "W38RGI023A65DVUC0V80", "ALV.DE": "529900K9B0N5BT694847",
    "BAS.DE": "529900PM64WH8AF1E917", "DTE.DE": "549300V9QQ35F6GBZ574",
}
ESEF_UA = config.EDGAR_UA

# candidati IFRS per ogni voce (primo che copre l'anno vince)
IFRS = {
    "revenue": ["ifrs-full:RevenueFromContractsWithCustomers", "ifrs-full:Revenue"],
    "gross_profit": ["ifrs-full:GrossProfit"],
    "operating_income": ["ifrs-full:ProfitLossFromOperatingActivities"],
    "net_income": ["ifrs-full:ProfitLoss"],
    "pretax_income": ["ifrs-full:ProfitLossBeforeTax"],
    "tax_provision": ["ifrs-full:IncomeTaxExpenseContinuingOperations",
                      "ifrs-full:IncomeTaxExpenseBenefit"],
    "diluted_eps": ["ifrs-full:DilutedEarningsLossPerShare",
                    "ifrs-full:BasicEarningsLossPerShare"],
    "interest_expense": ["ifrs-full:FinanceCosts", "ifrs-full:InterestExpense"],
    "rd": ["ifrs-full:ResearchAndDevelopmentExpense"],
    "da_cf": ["ifrs-full:DepreciationAndAmortisationExpense",
              "ifrs-full:DepreciationAmortisationAndImpairmentLossReversalOfImpairmentLossRecognisedInProfitOrLoss"],
    "total_assets": ["ifrs-full:Assets"],
    "equity": ["ifrs-full:EquityAttributableToOwnersOfParent", "ifrs-full:Equity"],
    "cash": ["ifrs-full:CashAndCashEquivalents"],
    "current_assets": ["ifrs-full:CurrentAssets"],
    "current_liab": ["ifrs-full:CurrentLiabilities"],
    "total_liab": ["ifrs-full:Liabilities"],
    "retained": ["ifrs-full:RetainedEarnings"],
    "goodwill": ["ifrs-full:Goodwill", "ifrs-full:IntangibleAssetsAndGoodwill"],
    "cfo": ["ifrs-full:CashFlowsFromUsedInOperatingActivities"],
    "capex": ["ifrs-full:PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities"],
    "dividends_paid": ["ifrs-full:DividendsPaidClassifiedAsFinancingActivities",
                       "ifrs-full:DividendsPaid"],
    "ncur_borrow": ["ifrs-full:NoncurrentBorrowings", "ifrs-full:LongtermBorrowings"],
    "cur_borrow": ["ifrs-full:CurrentBorrowings", "ifrs-full:ShorttermBorrowings"],
}
INSTANT = {"total_assets", "equity", "cash", "current_assets", "current_liab",
           "total_liab", "retained", "goodwill", "ncur_borrow", "cur_borrow"}


def _get(url, **kw):
    try:
        r = std_requests.get(url, headers={"User-Agent": ESEF_UA}, timeout=45, **kw)
        if r.status_code == 200:
            return r
    except Exception as e:
        log.debug("GET %s: %s", url, str(e)[:80])
    return None


def _lei_for(ticker: str) -> str | None:
    t = ticker.upper()
    if t in LEI_MAP:
        return LEI_MAP[t]
    return None  # fuzzy GLEIF fallback: T22b (richiede matching robusto del nome)


def _fy_of(period: str, instant: bool) -> int | None:
    try:
        if instant:
            d = date.fromisoformat(period[:10])
            return d.year - 1 if (d.month == 1 and d.day <= 2) else d.year
        end = period.split("/")[1] if "/" in period else period
        d = date.fromisoformat(end[:10])
        return d.year - 1 if (d.month == 1 and d.day <= 2) else d.year
    except (ValueError, IndexError):
        return None


def _extract(facts: dict, out: dict) -> None:
    """Popola out[key][fy] = value dai fatti puliti (senza dimensioni di segmento)."""
    concept_to_key = {}
    for key, names in IFRS.items():
        for rank, n in enumerate(names):
            concept_to_key.setdefault(n, (key, rank))
    for f in facts.values():
        dim = f.get("dimensions", {})
        extra = [k for k in dim if k not in ("concept", "entity", "period", "unit", "language")]
        if extra:
            continue
        c = dim.get("concept", "")
        if c not in concept_to_key:
            continue
        key, rank = concept_to_key[c]
        fy = _fy_of(dim.get("period", ""), key in INSTANT)
        if fy is None:
            continue
        try:
            v = float(f.get("value"))
        except (TypeError, ValueError):
            continue
        slot = out.setdefault(key, {})
        # preferisci il candidato a rank piu' basso; a parita', non sovrascrivere
        prev = slot.get(fy)
        if prev is None or rank < prev[1]:
            slot[fy] = (v, rank)


def fetch_esef(ticker: str, max_filings: int = 4) -> dict | None:
    """Assembla `raw` con fondamentali ESEF [P] multi-anno + mercato TradingView."""
    lei = _lei_for(ticker)
    if not lei:
        return None
    flt = json.dumps([{"name": "entity.identifier", "op": "eq", "val": lei}])
    r = _get("https://filings.xbrl.org/api/filings",
             params={"filter": flt, "page[size]": max_filings, "sort": "-period_end"})
    if not r or not r.json().get("data"):
        return None
    filings = r.json()["data"]
    out: dict = {}
    got = 0
    for f in filings:
        ju = f["attributes"].get("json_url")
        if not ju:
            continue
        cache = os.path.join(config.CACHE_DIR, "esef_" + f["attributes"]["fxo_id"] + ".json")
        os.makedirs(config.CACHE_DIR, exist_ok=True)
        data = None
        if os.path.exists(cache) and time.time() - os.path.getmtime(cache) < 30 * 86400:
            try:
                data = json.load(open(cache))
            except Exception:
                data = None
        if data is None:
            fr = _get("https://filings.xbrl.org" + ju)
            if not fr:
                continue
            data = fr.json()
            json.dump(data, open(cache, "w"))
        _extract(data.get("facts", {}), out)
        got += 1
    if got == 0 or "net_income" not in out:
        return None

    years = sorted({fy for d in out.values() for fy in d}, reverse=True)[:6]

    def series(key):
        d = out.get(key, {})
        return [d[fy][0] if fy in d else None for fy in years]

    total_debt = []
    for fy in years:
        nc = out.get("ncur_borrow", {}).get(fy)
        cu = out.get("cur_borrow", {}).get(fy)
        total_debt.append((nc[0] if nc else 0) + (cu[0] if cu else 0) if (nc or cu) else None)
    da = series("da_cf")

    # mercato da TradingView (prezzo, azioni, market cap, dividendo, beta)
    tv = fetch_tv.fetch_tv(ticker) or {}
    tvi = tv.get("info", {})
    price = tvi.get("currentPrice")
    shares_mkt = tvi.get("sharesOutstanding")
    eps = series("diluted_eps")
    # azioni: da market cap/prezzo (mercato) — la serie storica azioni ESEF e' rara
    shares = [shares_mkt] + [None] * (len(years) - 1) if shares_mkt else []

    info = {
        "symbol": ticker, "shortName": tvi.get("shortName") or ticker,
        "longName": tvi.get("longName") or ticker,
        "sector": tvi.get("sector") or "", "industry": tvi.get("industry") or "",
        "country": tvi.get("country") or "", "currency": tvi.get("currency") or "EUR",
        "currentPrice": price, "regularMarketPrice": price,
        "beta": tvi.get("beta"), "marketCap": tvi.get("marketCap"),
        "trailingPE": tvi.get("trailingPE"), "sharesOutstanding": shares_mkt,
    }
    raw = {
        "ticker": ticker, "info": info,
        "revenue": series("revenue"), "gross_profit": series("gross_profit"),
        "operating_income": series("operating_income"), "ebit": series("operating_income"),
        "ebitda": [], "net_income": series("net_income"),
        "pretax_income": series("pretax_income"), "tax_provision": series("tax_provision"),
        "diluted_eps": eps, "interest_expense": series("interest_expense"),
        "rd": series("rd"), "da_income": da, "da_cf": da,
        "total_assets": series("total_assets"), "equity": series("equity"),
        "total_debt": total_debt, "cash": series("cash"),
        "current_assets": series("current_assets"), "current_liab": series("current_liab"),
        "total_liab": series("total_liab"), "retained": series("retained"),
        "working_capital": [], "goodwill": series("goodwill"), "shares": shares,
        "cfo": series("cfo"), "capex": [abs(v) if v is not None else None for v in series("capex")],
        "fcf_yf": [], "sbc": [], "dividends_paid": series("dividends_paid"),
        "buyback_cf": [], "dividends_series": tv.get("dividends_series", {}),
        "prices": {}, "_source": "esef+tradingview",
        "_esef_years": years,
        # solo dati di MERCATO da TV (yield/payout); crescita e ROIC/ROE dalle
        # serie ESEF multi-anno, non da TV.
        "_tv_direct": {k: (tv.get("_tv_direct") or {}).get(k)
                       for k in ("C19_yield", "C20_payout")},
    }
    return raw
