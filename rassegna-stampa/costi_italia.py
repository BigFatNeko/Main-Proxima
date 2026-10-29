"""Costo reale di un titolo estero per un risparmiatore italiano.

Tre voci, tutte indipendenti dal prezzo del titolo:

  1. RITENUTA ALLA FONTE sui dividendi. Quella che il paese trattiene davvero
     all'incasso e quella prevista dalla convenzione con l'Italia sono due
     numeri diversi: la differenza si recupera solo con una domanda di
     rimborso al fisco estero, con moduli, certificato di residenza e mesi di
     attesa. Per un portafoglio da poche migliaia di euro non succede. Per
     questo il rendimento "netto Italia" usa l'aliquota trattenuta, e il
     rendimento "con rimborso" e' riportato a parte.
  2. VALUTA. Non e' un costo fisso: e' un rischio piu' lo spread di
     conversione. La corona danese e' agganciata all'euro; svedese e
     norvegese no. Qui diventa una penalita' di ordinamento in punti
     percentuali di rendimento annuo, dichiarata come euristica.
  3. TASSE SULL'ACQUISTO (stamp duty / FTT), ammortizzate su 5 anni.

Le aliquote di ritenuta sono quelle non-residenti della tabella PwC
(taxsummaries.pwc.com, "Quick charts: withholding tax rates", riviste a
giugno-settembre 2026). Danimarca anche da Clearstream (27% trattenuto, 15%
convenzionale a rimborso). Le voci con `verificata=False` sono di conoscenza
generale e vanno confermate col commercialista prima di fidarsi dei decimali.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Ritenuta:
    fonte: float        # trattenuta all'incasso da un non residente
    trattato: float     # aliquota convenzionale con l'Italia (a rimborso)
    verificata: bool    # confermata su fonte ufficiale consultata


RITENUTE: dict[str, Ritenuta] = {
    # Nord America
    "US": Ritenuta(0.15, 0.15, True),    # con W-8BEN; 30% senza
    "CA": Ritenuta(0.25, 0.15, True),
    # Europa
    "UK": Ritenuta(0.00, 0.00, True),
    "NL": Ritenuta(0.15, 0.15, True),
    "DE": Ritenuta(0.26375, 0.15, False),  # 25% + soli
    "FR": Ritenuta(0.128, 0.128, True),    # persone fisiche non residenti
    "ES": Ritenuta(0.19, 0.15, True),
    "CH": Ritenuta(0.35, 0.15, False),
    "IE": Ritenuta(0.25, 0.15, True),
    "BE": Ritenuta(0.30, 0.15, True),
    "AT": Ritenuta(0.275, 0.15, True),
    "PT": Ritenuta(0.25, 0.15, True),
    "IT": Ritenuta(0.00, 0.00, True),      # titolo domestico
    # Nord Europa
    "DK": Ritenuta(0.27, 0.15, True),
    "SE": Ritenuta(0.30, 0.15, True),
    "NO": Ritenuta(0.25, 0.15, True),
    "FI": Ritenuta(0.35, 0.15, False),     # PwC: "varies case by case"
    # Asia-Pacifico e altri
    "JP": Ritenuta(0.15315, 0.15, False),
    "AU": Ritenuta(0.30, 0.15, True),      # dividendi non "franked"
    "NZ": Ritenuta(0.30, 0.15, True),
    "HK": Ritenuta(0.00, 0.00, True),
    "SG": Ritenuta(0.00, 0.00, True),
    "IL": Ritenuta(0.25, 0.15, False),
    "CN": Ritenuta(0.10, 0.10, False),
}
RITENUTA_DEFAULT = Ritenuta(0.25, 0.15, False)

# Paesi dove l'attrito (ritenuta alta e/o valuta non euro) e' strutturale.
NORDICI = frozenset({"SE", "NO", "DK", "FI"})

_SUFFISSO_PAESE = {
    "MI": "IT", "DE": "DE", "F": "DE", "PA": "FR", "AS": "NL", "BR": "BE",
    "L": "UK", "MC": "ES", "SW": "CH", "VX": "CH", "T": "JP", "HK": "HK",
    "SS": "CN", "SZ": "CN", "ST": "SE", "CO": "DK", "OL": "NO", "HE": "FI",
    "VI": "AT", "LS": "PT", "AX": "AU", "NZ": "NZ", "TO": "CA", "V": "CA",
    "NE": "CA", "CN": "CA", "IR": "IE", "SI": "SG", "TA": "IL",
}

_PAESE_VALUTA = {
    "IT": "EUR", "DE": "EUR", "FR": "EUR", "NL": "EUR", "BE": "EUR",
    "ES": "EUR", "AT": "EUR", "PT": "EUR", "IE": "EUR", "FI": "EUR",
    "UK": "GBP", "CH": "CHF", "DK": "DKK", "SE": "SEK", "NO": "NOK",
    "JP": "JPY", "AU": "AUD", "NZ": "NZD", "CA": "CAD", "HK": "HKD",
    "SG": "SGD", "IL": "ILS", "CN": "CNY", "US": "USD",
}

# Penalita' di ordinamento in punti percentuali di rendimento annuo.
# EURISTICA dichiarata, non un costo misurato: serve a non far salire in
# cima alla lista un titolo il cui vantaggio sta dentro il rumore del cambio.
_PEN_VALUTA_PP = {
    "EUR": 0.0,
    "DKK": 0.1,    # ERM II: oscilla pochissimo contro l'euro
    "USD": 0.3, "GBP": 0.3, "CHF": 0.3,
}
_PEN_VALUTA_ALTRE_PP = 0.6   # SEK NOK JPY AUD CAD HKD SGD NZD ILS ...

# Tassa sull'acquisto, % del controvalore. INDICATIVI, da verificare.
_TASSA_ACQUISTO_PCT = {
    "UK": 0.5,    # stamp duty reserve tax, solo azioni UK (non ETF/ADR)
    "FR": 0.4,    # FTT, grandi capitalizzazioni
    "IT": 0.1,    # FTT, capitalizzazione > 500 mln
    "ES": 0.2,
    "IE": 1.0,    # stamp duty
    "HK": 0.1,
}
_AMMORTAMENTO_ANNI = 5


def paese_da_ticker(ticker: str, mercato: str = "") -> str:
    """Paese di quotazione dal suffisso Yahoo. Senza suffisso: USA."""
    t = (ticker or "").upper()
    if "." in t:
        return _SUFFISSO_PAESE.get(t.rsplit(".", 1)[1], "")
    return "US" if mercato in ("US", "") else mercato


def ritenuta(paese: str) -> Ritenuta:
    return RITENUTE.get((paese or "").upper(), RITENUTA_DEFAULT)


def valuta_quotazione(paese: str) -> str:
    return _PAESE_VALUTA.get((paese or "").upper(), "")


def penalita_attrito_pp(paese: str) -> float:
    """Punti percentuali di rendimento annuo da sottrarre in ordinamento."""
    p = (paese or "").upper()
    val = valuta_quotazione(p)
    pen_val = _PEN_VALUTA_PP.get(val, _PEN_VALUTA_ALTRE_PP)
    tassa = _TASSA_ACQUISTO_PCT.get(p, 0.0) / _AMMORTAMENTO_ANNI
    return round(pen_val + tassa, 3)


def attrito(ticker: str, mercato: str = "") -> dict:
    """Riepilogo dei costi di un titolo, da allegare al contesto."""
    p = paese_da_ticker(ticker, mercato)
    r = ritenuta(p)
    return {
        "paese": p,
        "valuta": valuta_quotazione(p),
        "ritenuta_trattenuta": r.fonte,
        "ritenuta_convenzione": r.trattato,
        "tassa_acquisto_pct": _TASSA_ACQUISTO_PCT.get(p, 0.0),
        "penalita_ordinamento_pp": penalita_attrito_pp(p),
        "nordico": p in NORDICI,
    }


_TV_PREFISSO_PAESE = {"OMXSTO": "SE", "OMXCOP": "DK", "OSL": "NO", "OMXHEX": "FI"}


def paese_da_tv(tv_ticker: str) -> str:
    """Paese nordico da un ticker TradingView (OSL:EQNR); altrimenti ''."""
    if ":" not in (tv_ticker or ""):
        return ""
    return _TV_PREFISSO_PAESE.get(tv_ticker.split(":", 1)[0].upper(), "")


def limita_nordici(righe: list, ticker_di, massimo: int = 1,
                   ammessi: frozenset | set | None = None) -> list:
    """Tiene al massimo `massimo` titoli nordici, nell'ordine ricevuto.

    `righe` deve arrivare gia' ordinata dal migliore al peggiore: i nordici
    che sforano il tetto vengono scartati, non spostati in fondo. Se
    `ammessi` e' dato, un nordico passa solo se il suo ticker e' li' dentro:
    serve a far valere UN SOLO nordico per l'intero briefing su liste diverse.
    """
    visti = 0
    out = []
    for r in righe:
        tkr = ticker_di(r)
        if paese_da_ticker(tkr) in NORDICI:
            if ammessi is not None and tkr not in ammessi:
                continue
            visti += 1
            if visti > massimo:
                continue
        out.append(r)
    return out
