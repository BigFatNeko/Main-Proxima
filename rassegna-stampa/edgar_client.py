"""
SEC EDGAR — client per il controllo incrociato dei fondamentali (MVF Sez. 6-bis)
===============================================================================

Il DIP (Protocollo di Integrità dei Dati) della specifica MVF v4.1 impone una
gerarchia di reperimento primary-first: per US-listed, ADR e FPI la fonte di
riferimento è SEC EDGAR, con XBRL come ground truth.

Questo modulo porta i titoli US da [V] (aggregatore) a [P] (primario) quando
EDGAR conferma il dato, e li degrada a [U] quando lo contraddice — perché due
fonti in conflitto valgono meno di una sola non verificata (Sez. 6-bis C).

CARATTERISTICHE
  - Nessuna API key: SEC richiede solo uno User-Agent identificativo
  - Rate limiting rispettoso del limite dichiarato dalla SEC (10 req/s)
  - Cache su disco: i companyfacts sono file pesanti e cambiano di rado
  - Degradazione graziosa: qualunque errore lascia il pipeline sui dati
    yfinance, senza mai interrompere il run

COPERTURA
  Solo emittenti che depositano presso la SEC: US-listed, ADR, FPI
  (form 10-K, 10-Q, 20-F, 40-F). Fuori da questo perimetro il modulo
  restituisce "non coperto" e il tag resta [V].

USO
    from edgar_client import EdgarClient, cross_check_fundamentals

    client = EdgarClient()                       # legge EDGAR_USER_AGENT
    facts = client.get_fundamentals("AAPL")
    result = cross_check_fundamentals(yf_values, facts)
    if result.verdict == "agree":
        ...   # il dato sale a [P]

CONFIGURAZIONE (env)
    EDGAR_USER_AGENT   "Nome Cognome email@dominio.it"  (richiesto da SEC)
    EDGAR_CACHE_DIR    default: <script_dir>/data/edgar_cache
    EDGAR_ENABLED      "0" per disattivare il cross-check
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Any

log = logging.getLogger("edgar_client")

SCRIPT_DIR = Path(__file__).parent.absolute()

TICKER_MAP_URL = "https://www.sec.gov/files/company_tickers.json"
COMPANYFACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"

# La SEC dichiara un limite di 10 richieste al secondo. Restiamo sotto.
MIN_REQUEST_INTERVAL = 0.15   # ~6.7 req/s
REQUEST_TIMEOUT = 45

TICKER_MAP_TTL_DAYS = 7
COMPANYFACTS_TTL_DAYS = 7

# Tolleranze di riconciliazione (MVF Sez. 6-bis C)
TOLERANCE_ABSOLUTE = 0.01     # voci esatte: <= 1%
TOLERANCE_RATIO_PP = 0.01     # ratio: <= 1 punto percentuale
TOLERANCE_RATIO_REL = 0.02    # ratio: oppure <= 2% relativo


# =============================================================================
# MAPPATURA CONCETTI XBRL
# =============================================================================

# Un concetto contabile può essere depositato sotto tag diversi a seconda
# dell'emittente e dell'anno di tassonomia: si prova in ordine di preferenza.
XBRL_CONCEPTS: dict[str, list[str]] = {
    "revenue": [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
        "Revenues",
        "SalesRevenueNet",
        "SalesRevenueGoodsNet",
    ],
    "net_income": [
        "NetIncomeLoss",
        "ProfitLoss",
        "NetIncomeLossAvailableToCommonStockholdersBasic",
    ],
    "operating_income": [
        "OperatingIncomeLoss",
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
    ],
    "gross_profit": ["GrossProfit"],
    "assets": ["Assets"],
    "liabilities": ["Liabilities"],
    "equity": [
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    ],
    "cash": [
        "CashAndCashEquivalentsAtCarryingValue",
        "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
    ],
    "operating_cash_flow": [
        "NetCashProvidedByUsedInOperatingActivities",
        "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
    ],
    "capex": [
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "PaymentsToAcquireProductiveAssets",
    ],
    "long_term_debt": [
        "LongTermDebtNoncurrent",
        "LongTermDebt",
    ],
    "shares_outstanding": [
        "CommonStockSharesOutstanding",
        "WeightedAverageNumberOfDilutedSharesOutstanding",
        "WeightedAverageNumberOfSharesOutstandingBasic",
    ],
    "eps_diluted": ["EarningsPerShareDiluted"],
    "dividends_paid": [
        "PaymentsOfDividendsCommonStock",
        "PaymentsOfDividends",
    ],
}

ANNUAL_FORMS = {"10-K", "20-F", "40-F"}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class EdgarFundamentals:
    """Fondamentali annuali normalizzati estratti da XBRL."""
    ticker: str = ""
    cik: Optional[int] = None
    entity_name: str = ""
    fiscal_year: Optional[int] = None
    period_end: str = ""
    form: str = ""
    filed: str = ""
    values: dict = field(default_factory=dict)     # concetto -> valore
    derived: dict = field(default_factory=dict)    # ratio calcolati
    covered: bool = False
    error: str = ""

    @property
    def is_usable(self) -> bool:
        return self.covered and bool(self.values)


@dataclass
class CrossCheckResult:
    """Esito del confronto yfinance <-> EDGAR (MVF Sez. 6-bis C)."""
    verdict: str = "not_covered"   # agree | conflict | partial | not_covered
    checked: int = 0
    matched: int = 0
    mismatched: int = 0
    details: dict = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    @property
    def agrees(self) -> Optional[bool]:
        """True concorde, False in conflitto, None non verificabile."""
        if self.verdict == "agree":
            return True
        if self.verdict == "conflict":
            return False
        return None


# =============================================================================
# CLIENT
# =============================================================================

class EdgarClient:
    """Client EDGAR con cache su disco e rate limiting."""

    _lock = threading.Lock()
    _last_request = 0.0

    def __init__(self, user_agent: Optional[str] = None,
                 cache_dir: Optional[Path] = None):
        self.user_agent = user_agent or os.environ.get(
            "EDGAR_USER_AGENT",
            "Proxima Briefing Pipeline contact@proxima.local")
        self.cache_dir = Path(cache_dir or os.environ.get(
            "EDGAR_CACHE_DIR", SCRIPT_DIR / "data" / "edgar_cache"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._ticker_map: Optional[dict] = None
        self.enabled = os.environ.get("EDGAR_ENABLED", "1") != "0"

    # ---------------------------------------------------------------- HTTP
    def _throttle(self) -> None:
        """Rispetta il limite di richieste dichiarato dalla SEC."""
        with EdgarClient._lock:
            elapsed = time.monotonic() - EdgarClient._last_request
            if elapsed < MIN_REQUEST_INTERVAL:
                time.sleep(MIN_REQUEST_INTERVAL - elapsed)
            EdgarClient._last_request = time.monotonic()

    def _fetch_json(self, url: str) -> Optional[dict]:
        self._throttle()
        req = urllib.request.Request(url, headers={
            "User-Agent": self.user_agent,
            "Accept-Encoding": "gzip, deflate",
            "Host": url.split("/")[2],
        })
        try:
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as r:
                raw = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    import gzip
                    raw = gzip.decompress(raw)
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                log.debug("EDGAR 404 su %s (emittente non SEC)", url)
            else:
                log.debug("EDGAR HTTP %s su %s", e.code, url)
            return None
        except Exception as e:
            log.debug("EDGAR errore su %s: %s", url, e)
            return None

    def _cached_json(self, cache_name: str, url: str,
                     ttl_days: int) -> Optional[dict]:
        path = self.cache_dir / cache_name
        if path.exists():
            age = datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)
            if age < timedelta(days=ttl_days):
                try:
                    return json.loads(path.read_text())
                except Exception:
                    pass
        data = self._fetch_json(url)
        if data is not None:
            try:
                path.write_text(json.dumps(data))
            except Exception as e:
                log.debug("cache EDGAR non scritta (%s): %s", cache_name, e)
        return data

    # ------------------------------------------------------------- MAPPING
    def get_cik(self, ticker: str) -> Optional[int]:
        """Risolve il ticker in CIK. None se l'emittente non deposita SEC."""
        if not self.enabled or not ticker:
            return None
        # I ticker con suffisso di borsa non sono US-listed
        if "." in ticker and not ticker.endswith(".US"):
            return None
        if self._ticker_map is None:
            data = self._cached_json("company_tickers.json", TICKER_MAP_URL,
                                     TICKER_MAP_TTL_DAYS)
            if not data:
                self._ticker_map = {}
            else:
                self._ticker_map = {
                    str(v["ticker"]).upper(): int(v["cik_str"])
                    for v in data.values() if v.get("ticker")
                }
                log.debug("EDGAR ticker map: %d emittenti", len(self._ticker_map))
        return self._ticker_map.get(ticker.upper().replace(".US", ""))

    # -------------------------------------------------------- FUNDAMENTALS
    @staticmethod
    def _pick_annual(concept_data: dict,
                     fiscal_year: Optional[int] = None) -> Optional[dict]:
        """Estrae il fatto annuale più recente (o dell'esercizio richiesto).

        Preferisce i form annuali e i periodi di ~12 mesi; a parità sceglie il
        deposito più recente, che riflette eventuali restatement.
        """
        best = None
        for unit_facts in concept_data.get("units", {}).values():
            for f in unit_facts:
                if f.get("form") not in ANNUAL_FORMS:
                    continue
                start, end = f.get("start"), f.get("end")
                if start and end:
                    try:
                        d0 = datetime.strptime(start, "%Y-%m-%d")
                        d1 = datetime.strptime(end, "%Y-%m-%d")
                        if not (300 <= (d1 - d0).days <= 400):
                            continue   # non è un esercizio pieno
                    except ValueError:
                        continue
                if fiscal_year is not None and f.get("fy") != fiscal_year:
                    continue
                if best is None:
                    best = f
                    continue
                # più recente per fine periodo, poi per data di deposito
                if (f.get("end", ""), f.get("filed", "")) > \
                   (best.get("end", ""), best.get("filed", "")):
                    best = f
        return best

    def get_fundamentals(self, ticker: str,
                         fiscal_year: Optional[int] = None) -> EdgarFundamentals:
        """Fondamentali annuali normalizzati per un ticker US."""
        out = EdgarFundamentals(ticker=ticker)
        if not self.enabled:
            out.error = "EDGAR disattivato (EDGAR_ENABLED=0)"
            return out

        cik = self.get_cik(ticker)
        if cik is None:
            out.error = "emittente non presente nel registro SEC"
            return out
        out.cik = cik

        facts = self._cached_json(
            f"facts_{cik:010d}.json",
            COMPANYFACTS_URL.format(cik=cik),
            COMPANYFACTS_TTL_DAYS)
        if not facts:
            out.error = "companyfacts non recuperabili"
            return out

        out.entity_name = facts.get("entityName", "")
        gaap = facts.get("facts", {}).get("us-gaap", {})
        if not gaap:
            out.error = "nessun fatto us-gaap (possibile IFRS o filer minore)"
            return out

        for key, candidates in XBRL_CONCEPTS.items():
            for concept in candidates:
                if concept not in gaap:
                    continue
                fact = self._pick_annual(gaap[concept], fiscal_year)
                if fact is None:
                    continue
                out.values[key] = fact.get("val")
                if not out.period_end:
                    out.period_end = fact.get("end", "")
                    out.fiscal_year = fact.get("fy")
                    out.form = fact.get("form", "")
                    out.filed = fact.get("filed", "")
                break

        out.covered = bool(out.values)
        out.derived = self._derive_ratios(out.values)
        return out

    @staticmethod
    def _derive_ratios(v: dict) -> dict:
        """Ratio confrontabili con quelli calcolati dal pipeline."""
        d: dict[str, float] = {}
        rev = v.get("revenue")
        if rev:
            for key, num in (("net_margin", v.get("net_income")),
                             ("operating_margin", v.get("operating_income")),
                             ("gross_margin", v.get("gross_profit"))):
                if num is not None:
                    d[key] = num / rev
            ocf, capex = v.get("operating_cash_flow"), v.get("capex")
            if ocf is not None:
                fcf = ocf - abs(capex or 0)
                d["fcf"] = fcf
                d["fcf_margin"] = fcf / rev
        eq = v.get("equity")
        if eq and eq > 0:
            if v.get("net_income") is not None:
                d["roe"] = v["net_income"] / eq
            if v.get("long_term_debt") is not None:
                d["debt_to_equity"] = v["long_term_debt"] / eq
        assets = v.get("assets")
        if assets and assets > 0:
            if v.get("net_income") is not None:
                d["roa"] = v["net_income"] / assets
            if v.get("long_term_debt") is not None:
                d["debt_to_assets"] = v["long_term_debt"] / assets
        return d


# =============================================================================
# CONTROLLO INCROCIATO (MVF Sez. 6-bis C)
# =============================================================================

# Ratio: tolleranza in punti percentuali o relativa. Voci esatte: 1%.
_RATIO_FIELDS = {"net_margin", "operating_margin", "gross_margin",
                 "fcf_margin", "roe", "roa", "debt_to_equity",
                 "debt_to_assets"}


def _within_tolerance(field_name: str, a: float, b: float) -> bool:
    """Applica le tolleranze della specifica al singolo campo."""
    if a is None or b is None:
        return False
    if field_name in _RATIO_FIELDS:
        if abs(a - b) <= TOLERANCE_RATIO_PP:
            return True
        if abs(b) > 1e-9 and abs(a - b) / abs(b) <= TOLERANCE_RATIO_REL:
            return True
        return False
    if abs(b) < 1e-9:
        return abs(a) < 1e-9
    return abs(a - b) / abs(b) <= TOLERANCE_ABSOLUTE


# Soglie di verdetto: quanto disaccordo si tollera prima di dichiarare conflitto
MIN_FIELDS_FOR_VERDICT = 3
CONFLICT_RATIO = 0.34      # oltre un terzo di campi discordi -> conflitto
AGREE_RATIO = 0.80         # almeno l'80% concorde -> conferma


def cross_check_fundamentals(yf_values: dict,
                             edgar: EdgarFundamentals) -> CrossCheckResult:
    """Confronta i valori yfinance con quelli EDGAR.

    yf_values: dizionario con le stesse chiavi di EdgarFundamentals.values
               e/o .derived (revenue, net_income, net_margin, roe, ...).

    Un conflitto material NON è neutro: degrada il dato a [U], perché due
    fonti che si contraddicono valgono meno di una sola non verificata.
    """
    res = CrossCheckResult()

    if not edgar.is_usable:
        res.verdict = "not_covered"
        res.notes.append(edgar.error or "EDGAR non copre questo emittente")
        return res

    reference = {**edgar.values, **edgar.derived}
    for key, yf_val in (yf_values or {}).items():
        ref_val = reference.get(key)
        if yf_val is None or ref_val is None:
            continue
        try:
            ok = _within_tolerance(key, float(yf_val), float(ref_val))
        except (TypeError, ValueError):
            continue
        res.checked += 1
        delta = None
        if abs(float(ref_val)) > 1e-9:
            delta = (float(yf_val) - float(ref_val)) / abs(float(ref_val))
        res.details[key] = {
            "yfinance": yf_val, "edgar": ref_val,
            "delta_pct": round(delta * 100, 2) if delta is not None else None,
            "match": ok,
        }
        if ok:
            res.matched += 1
        else:
            res.mismatched += 1

    if res.checked < MIN_FIELDS_FOR_VERDICT:
        res.verdict = "partial"
        res.notes.append(
            f"solo {res.checked} campi confrontabili: sotto il minimo di "
            f"{MIN_FIELDS_FOR_VERDICT} per un verdetto")
        return res

    mismatch_ratio = res.mismatched / res.checked
    match_ratio = res.matched / res.checked
    if mismatch_ratio > CONFLICT_RATIO:
        res.verdict = "conflict"
        worst = sorted(
            (k for k, v in res.details.items() if not v["match"]),
            key=lambda k: abs(res.details[k].get("delta_pct") or 0),
            reverse=True)[:3]
        res.notes.append(
            f"conflitto material: {res.mismatched}/{res.checked} campi fuori "
            f"tolleranza. Peggiori: {', '.join(worst)}")
        res.notes.append(
            "il dato NON è validato: degradato a [U] (Sez. 6-bis C)")
    elif match_ratio >= AGREE_RATIO:
        res.verdict = "agree"
        res.notes.append(
            f"confermato da EDGAR: {res.matched}/{res.checked} campi entro "
            f"tolleranza (form {edgar.form}, esercizio {edgar.fiscal_year})")
    else:
        res.verdict = "partial"
        res.notes.append(
            f"conferma parziale: {res.matched}/{res.checked} campi concordi")
    return res


# =============================================================================
# HELPER DI INTEGRAZIONE
# =============================================================================

_default_client: Optional[EdgarClient] = None


def get_default_client() -> EdgarClient:
    global _default_client
    if _default_client is None:
        _default_client = EdgarClient()
    return _default_client


def verify_ticker(ticker: str, yf_values: dict) -> CrossCheckResult:
    """Verifica un ticker contro EDGAR. Non solleva mai: in caso di problema
    restituisce 'not_covered' e il pipeline prosegue sui dati yfinance."""
    try:
        client = get_default_client()
        facts = client.get_fundamentals(ticker)
        return cross_check_fundamentals(yf_values, facts)
    except Exception as e:
        res = CrossCheckResult()
        res.verdict = "not_covered"
        res.notes.append(f"cross-check non eseguito: {e}")
        return res


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s",
                        datefmt="%H:%M:%S")
    tickers = sys.argv[1:] or ["AAPL", "MSFT", "KO", "JNJ"]
    c = EdgarClient()
    for t in tickers:
        f = c.get_fundamentals(t)
        if not f.is_usable:
            print(f"{t:8} non coperto: {f.error}")
            continue
        print(f"{t:8} CIK {f.cik} | {f.entity_name[:34]:36} "
              f"{f.form} FY{f.fiscal_year} ({f.period_end})")
        for k in ("revenue", "net_income", "operating_income", "assets", "equity"):
            v = f.values.get(k)
            if v is not None:
                print(f"           {k:20} {v/1e9:12,.2f} mld")
        for k in ("net_margin", "operating_margin", "roe"):
            v = f.derived.get(k)
            if v is not None:
                print(f"           {k:20} {v:12.2%}")
