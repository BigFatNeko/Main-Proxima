"""Costruzione dell'universo del Tier 1: logica pura, senza rete.

Il vecchio universo prendeva le prime 50 societa' per capitalizzazione di
ogni mercato e poi ne teneva 600 per punteggio reddito/valore. Misurato il
29 ottobre 2026 su 600 titoli: 3 americani, 6 inglesi, 11 giapponesi, 59
nordici e 302 di mercati emergenti (scartati dal briefing). Gli Stati Uniti
hanno 3.045 titoli idonei e ne entravano 50; il Canada non era interrogato;
222 REIT americani e circa 370 banche non arrivavano mai a Yahoo.

Qui l'universo si costruisce cosi':
  1. solo mercati sviluppati (lista in TV_MERCATI_DM);
  2. ogni titolo riceve un punteggio di PRESELEZIONE calcolato dai soli dati
     TradingView, con formula propria per REIT e per banche/assicurazioni
     (per cui P/E e leva industriale non dicono nulla);
  3. la selezione e' STRATIFICATA per famiglia di settore, con tetti per
     paese, cosi' nessun settore sparisce e nessun paese domina.

La preselezione non e' un giudizio: decide solo chi merita le ~8 richieste a
Yahoo del Tier 1. Il giudizio e' del motore MVF.
"""

from __future__ import annotations

import re
from typing import Optional

import costi_italia as costi

# Mercati sviluppati (MSCI World / FTSE Developed) interrogabili su TradingView.
# Irlanda non e' un mercato valido su TradingView (AssertionError): le sue
# societa' quotano su LSE/Euronext e vengono dagli altri mercati.
TV_MERCATI_DM = [
    "america", "canada", "uk", "germany", "france", "italy", "spain",
    "netherlands", "switzerland", "sweden", "denmark", "norway", "finland",
    "belgium", "austria", "portugal", "japan", "australia", "hongkong",
    "singapore", "newzealand", "israel",
]

# Righe richieste a TradingView per mercato. Il punteggio sceglie poi fra
# tutte: il limite serve solo a non scaricare l'intera coda di microcap.
FETCH_PER_MERCATO = {
    "america": 1500, "japan": 900, "uk": 600, "canada": 600, "germany": 500,
    "australia": 450, "sweden": 350, "hongkong": 400,
}
FETCH_DEFAULT = 300

# ---------------------------------------------------------------------------
# Famiglie di settore
# ---------------------------------------------------------------------------

_INDUSTRY_BUCKET = {
    "Real Estate Investment Trusts": "reit",
    "Real Estate Development": "immobiliare",
    "Major Banks": "banche", "Regional Banks": "banche", "Savings Banks": "banche",
    "Life/Health Insurance": "assicurazioni", "Multi-Line Insurance": "assicurazioni",
    "Property/Casualty Insurance": "assicurazioni", "Specialty Insurance": "assicurazioni",
    "Insurance Brokers/Services": "assicurazioni",
    "Investment Banks/Brokers": "finanza", "Investment Managers": "finanza",
    "Finance/Rental/Leasing": "finanza", "Financial Conglomerates": "finanza",
    "Food: Major Diversified": "staples", "Food: Meat/Fish/Dairy": "staples",
    "Food: Specialty/Candy": "staples", "Beverages: Alcoholic": "staples",
    "Beverages: Non-Alcoholic": "staples", "Tobacco": "staples",
    "Household/Personal Care": "staples", "Agricultural Commodities/Milling": "staples",
    "Food Retail": "staples", "Drugstore Chains": "staples",
    "Food Distributors": "staples",
    "Investment Trusts/Mutual Funds": None,     # fondi chiusi: non sono societa'
    "Miscellaneous": None,
}

_SECTOR_BUCKET = {
    "Utilities": "utility",
    "Health Technology": "sanita", "Health Services": "sanita",
    "Electronic Technology": "tecnologia", "Technology Services": "tecnologia",
    "Producer Manufacturing": "industriali", "Industrial Services": "industriali",
    "Transportation": "industriali", "Commercial Services": "industriali",
    "Distribution Services": "industriali",
    "Energy Minerals": "energia",
    "Process Industries": "materiali", "Non-Energy Minerals": "materiali",
    "Consumer Durables": "consumi_ciclici", "Retail Trade": "consumi_ciclici",
    "Consumer Services": "consumi_ciclici",
    "Consumer Non-Durables": "consumi_ciclici",   # staples gia' tolti per industry
    "Communications": "telecom",
    "Finance": "finanza",
}

# Peso di ogni famiglia nell'universo. Normalizzati al cap richiesto.
QUOTE_FAMIGLIA = {
    "reit": 45, "immobiliare": 10, "banche": 50, "assicurazioni": 35,
    "finanza": 25, "staples": 65, "utility": 40, "sanita": 70,
    "tecnologia": 60, "industriali": 85, "energia": 35, "materiali": 40,
    "consumi_ciclici": 40, "telecom": 25,
}

# Tetti di concentrazione per paese, in quota dell'universo. Sono MASSIMI,
# non quote: riflettono quanto conta ogni piazza per un risparmiatore italiano
# (liquidita' sul broker, costo dei dividendi, vicinanza del cambio). Senza,
# in prova, Australia, Hong Kong, Israele e Singapore prendevano il 40%
# dei posti perche' hanno moltissime societa' piccole con punteggi alti.
TETTI_PAESE = {
    "US": 0.38, "UK": 0.09, "DE": 0.07, "FR": 0.06, "IT": 0.06, "ES": 0.035,
    "NL": 0.035, "CH": 0.045, "BE": 0.02, "AT": 0.015, "PT": 0.015,
    "NORDICI": 0.06,                # SE NO DK FI insieme
    "CA": 0.06, "JP": 0.06, "AU": 0.035, "HK": 0.025, "SG": 0.02,
    "IL": 0.015, "NZ": 0.01,
}
TETTO_ALTRO_PAESE = 0.02

# Quota minima di titoli USA dentro ogni famiglia di settore, se esistono.
# Gli USA hanno i multipli piu' alti, quindi perdono la gara per punteggio
# a favore di mercati piu' economici: senza un minimo l'universo si svuota
# del mercato piu' liquido, col dividendo a 15% invece che a 25-35%.
MINIMO_USA_PER_FAMIGLIA = 0.30


def famiglia(settore: Optional[str], industria: Optional[str]) -> Optional[str]:
    """Famiglia di settore, o None se il titolo non va nell'universo."""
    if industria in _INDUSTRY_BUCKET:
        return _INDUSTRY_BUCKET[industria]
    return _SECTOR_BUCKET.get(settore or "")


# ---------------------------------------------------------------------------
# Punteggio di preselezione
# ---------------------------------------------------------------------------

def _lin(x: Optional[float], a: float, b: float) -> Optional[float]:
    """0 in `a`, 1 in `b`, lineare e saturato. None se manca il dato."""
    if x is None or x != x:
        return None
    if a == b:
        return None
    return max(0.0, min(1.0, (x - a) / (b - a)))


def _media_pesata(parti: list[tuple[Optional[float], float]],
                  penalizza_vuoti: bool = False) -> float:
    """Media pesata ignorando le componenti mancanti. 0 se manca tutto.

    Con `penalizza_vuoti` il risultato scala con la quota di peso coperta da
    dati veri: un titolo di cui TradingView conosce solo il rendimento non
    deve battere uno con quattro componenti su quattro. Senza, in prova, i
    primi posti erano tutti titoli di Hong Kong e Tel Aviv quasi senza dati.
    """
    num = den = tot = 0.0
    for v, w in parti:
        tot += w
        if v is None:
            continue
        num += v * w
        den += w
    if not den:
        return 0.0
    media = num / den
    return media * (0.35 + 0.65 * den / tot) if penalizza_vuoti else media


def _num(v) -> Optional[float]:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if f == f else None


def punteggio(r: dict, fam: str) -> float:
    """Punteggio 0-100 dai soli campi TradingView di una riga.

    Quattro idee, pesate diversamente per famiglia: QUALITA' (ROIC, margini),
    VALORE (multipli bassi), REDDITO (rendimento sostenibile) e SCONTO dai
    massimi a 52 settimane, che e' l'indizio piu' economico di un titolo
    sotto pressione (REIT oggi). Una componente senza dato non pesa.
    """
    dy = _num(r.get("dividends_yield_current"))
    if dy is None:
        dy = _num(r.get("dividends_yield"))
    payout = _num(r.get("dividend_payout_ratio_ttm"))
    anni_div = _num(r.get("continuous_dividend_payout")) or 0

    reddito = _lin(dy, 1.5, 6.0)
    if reddito is not None:
        if dy is not None and dy > 10:           # rendimenti da trappola
            reddito *= 0.4
        elif payout is not None and payout > 100 and fam != "reit":
            reddito *= 0.5
        if anni_div >= 10:
            reddito = min(1.0, reddito + 0.15)

    close, massimo = _num(r.get("close")), _num(r.get("price_52_week_high"))
    sconto = None
    if close and massimo and massimo > 0:
        sconto = _lin((massimo - close) / massimo, 0.10, 0.40)

    pb = _num(r.get("price_book_fq"))
    roe = _num(r.get("return_on_equity_fq"))

    if fam in ("banche", "assicurazioni", "finanza"):
        # P/B "giustificato": un ROE del 10% merita circa 1x il patrimonio.
        # Il rapporto ROE/10 diviso P/B dice se si paga poco per quel ROE.
        giust = None
        if roe is not None and pb is not None and pb > 0 and roe > 0:
            giust = _lin((roe / 10.0) / pb, 0.8, 1.6)
        qualita = _lin(roe, 6, 15)
        return 100 * _media_pesata([
            (qualita, 0.25), (giust, 0.30), (reddito, 0.30), (sconto, 0.15)],
            penalizza_vuoti=True)

    if fam in ("reit", "immobiliare"):
        valore_pb = None if pb is None or pb <= 0 else 1 - _lin(pb, 0.6, 2.0)
        nd, ebitda = _num(r.get("net_debt_fq")), _num(r.get("ebitda_ttm"))
        leva = None
        if nd is not None and ebitda and ebitda > 0:
            leva = 1 - _lin(nd / ebitda, 5, 10)
        return 100 * _media_pesata([
            (reddito, 0.35), (valore_pb, 0.25), (leva, 0.20), (sconto, 0.20)],
            penalizza_vuoti=True)

    roic = _num(r.get("return_on_invested_capital_fq"))
    opm = _num(r.get("operating_margin_ttm"))
    fcf = _num(r.get("free_cash_flow_ttm"))
    qualita = _media_pesata([
        (_lin(roic, 3, 15), 0.45), (_lin(opm, 5, 25), 0.35),
        (None if fcf is None else (1.0 if fcf > 0 else 0.0), 0.20)])
    pe = _num(r.get("price_earnings_ttm"))
    ev = _num(r.get("enterprise_value_ebitda_ttm"))
    v_pe = None if pe is None or pe <= 0 else 1 - _lin(pe, 8, 30)
    v_ev = None if ev is None or ev <= 0 else 1 - _lin(ev, 6, 18)
    valore = _media_pesata([(v_pe, 0.5), (v_ev, 0.5)])
    if fam == "utility":
        return 100 * _media_pesata([
            (reddito, 0.40), (valore, 0.25), (qualita, 0.15), (sconto, 0.20)],
            penalizza_vuoti=True)
    return 100 * _media_pesata([
        (qualita, 0.30), (valore, 0.25), (reddito, 0.25), (sconto, 0.20)],
        penalizza_vuoti=True)


# ---------------------------------------------------------------------------
# Selezione stratificata
# ---------------------------------------------------------------------------

_SUFFISSO_RE = re.compile(r"\.([A-Z]{1,3})$")


def paese_riga(r: dict) -> str:
    return costi.paese_da_ticker(r["yf_ticker"]) or "??"


def _gruppo_tetto(paese: str) -> str:
    if paese in costi.NORDICI:
        return "NORDICI"
    return paese


def _tetti(cap: int) -> dict[str, int]:
    return {g: int(cap * q) for g, q in TETTI_PAESE.items()}


def seleziona(righe: list[dict], cap: int) -> tuple[list[dict], dict]:
    """Sceglie `cap` righe: quote per famiglia, tetti per paese.

    Ogni riga porta gia' `famiglia` e `punteggio`. Prima passata: ogni
    famiglia riempie la propria quota coi migliori che rispettano i tetti.
    Seconda passata: le quote rimaste vuote (famiglia povera, es. solo 12
    REIT in un universo) vanno ai migliori avanzi di qualunque famiglia.

    Ritorna (selezione ordinata per punteggio decrescente, diagnostica).
    """
    tot_peso = sum(QUOTE_FAMIGLIA.values())
    quote = {f: max(1, round(cap * p / tot_peso)) for f, p in QUOTE_FAMIGLIA.items()}
    tetti = _tetti(cap)
    tetto_altro = int(cap * TETTO_ALTRO_PAESE)

    per_fam: dict[str, list[dict]] = {}
    for r in righe:
        per_fam.setdefault(r["famiglia"], []).append(r)
    for lst in per_fam.values():
        lst.sort(key=lambda r: (-r["punteggio"], r["yf_ticker"]))

    presi: list[dict] = []
    usati: set[str] = set()
    conta_paese: dict[str, int] = {}

    def prova(r: dict) -> bool:
        if r["yf_ticker"] in usati:
            return False
        g = _gruppo_tetto(paese_riga(r))
        limite = tetti.get(g, tetto_altro)
        if conta_paese.get(g, 0) >= limite:
            return False
        usati.add(r["yf_ticker"])
        conta_paese[g] = conta_paese.get(g, 0) + 1
        presi.append(r)
        return True

    riempimento: dict[str, int] = {}
    for fam, quota in quote.items():
        n = 0
        righe_fam = per_fam.get(fam, [])
        minimo_usa = round(quota * MINIMO_USA_PER_FAMIGLIA)
        for r in righe_fam:
            if n >= minimo_usa:
                break
            if paese_riga(r) == "US" and prova(r):
                n += 1
        for r in righe_fam:
            if n >= quota:
                break
            if prova(r):
                n += 1
        riempimento[fam] = n

    if len(presi) < cap:
        avanzi = [r for lst in per_fam.values() for r in lst
                  if r["yf_ticker"] not in usati]
        avanzi.sort(key=lambda r: (-r["punteggio"], r["yf_ticker"]))
        for r in avanzi:
            if len(presi) >= cap:
                break
            prova(r)

    presi.sort(key=lambda r: (-r["punteggio"], r["yf_ticker"]))
    diag = {
        "quote_richieste": quote,
        "riempimento_prima_passata": riempimento,
        "per_paese": dict(sorted(conta_paese.items(), key=lambda kv: -kv[1])),
        "candidati_totali": len(righe),
    }
    return presi, diag
