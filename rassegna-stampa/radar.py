"""Radar settoriale: chi entra nel briefing e perche'.

Il briefing prendeva i primi 40 titoli per Voto MVF. Il Voto pero' non e'
confrontabile fra classi (base 290 contro 365 e 370) e un REIT o una banca
con dati parziali finisce sempre sotto un'azienda industriale con tutte le
metriche: i settori "difficili" non uscivano mai.

Il radar rovescia il criterio. Ogni giorno guarda un gruppo ruotante di
famiglie di settore, cosi' ognuna compare ogni pochi giorni, e dentro ogni
famiglia ordina per quanto il titolo e' SCONTATO, non per quanto e' bello:

    punteggio = 0.5 x upside sul valore intrinseco (cap -30..+60)
              + 0.3 x sconto dai massimi a 52 settimane (cap 0..40)
              + 0.2 x IQI

Lo sconto dai massimi e' l'indizio piu' economico di un settore sotto
pressione (REIT col rialzo dei tassi, banche con le preoccupazioni sul
credito). Il valore intrinseco dice se lo sconto e' giustificato dai
fondamentali o e' una trappola: i due insieme separano il mispricing
dalla semplice discesa.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

import costi_italia as costi

# Ordine di rotazione: 14 famiglie, 4 al giorno, periodo di 7 giorni. Ogni
# famiglia compare esattamente due volte a settimana (verificato: 4 x 7 = 2 x 14).
FAMIGLIE = [
    "reit", "staples", "banche", "utility", "sanita", "assicurazioni",
    "industriali", "telecom", "tecnologia", "energia", "finanza",
    "consumi_ciclici", "materiali", "immobiliare",
]
PER_GIORNO = 4
PER_FAMIGLIA = 4

ETICHETTE = {
    "reit": "REIT", "staples": "Beni di consumo difensivi", "banche": "Banche",
    "utility": "Utility", "sanita": "Sanità", "assicurazioni": "Assicurazioni",
    "industriali": "Industriali e trasporti", "telecom": "Telecomunicazioni",
    "tecnologia": "Tecnologia", "energia": "Energia",
    "finanza": "Gestori e intermediari finanziari",
    "consumi_ciclici": "Consumi ciclici e retail", "materiali": "Materiali",
    "immobiliare": "Sviluppo e servizi immobiliari",
}


def famiglie_del_giorno(data_iso: str, n: int = PER_GIORNO) -> list[str]:
    try:
        y, m, d = (int(x) for x in data_iso.split("-"))
        ordinale = date(y, m, d).toordinal()
    except Exception:
        ordinale = date.today().toordinal()
    inizio = (ordinale * n) % len(FAMIGLIE)
    return [FAMIGLIE[(inizio + i) % len(FAMIGLIE)] for i in range(n)]


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _upside_pct(c: dict) -> Optional[float]:
    val = c.get("mvf_valuation") or {}
    up = val.get("upside_at_current_pct")
    if up is not None:
        return float(up)
    fv, px = c.get("intrinsic_value"), c.get("price")
    if fv and px and px > 0:
        return (fv / px - 1) * 100
    return None


# Sopra questa soglia un upside sul valore intrinseco e' quasi sempre un
# artefatto del modello (prezzo per azione minuscolo contro un valore calcolato
# su pochi numeri). Visto nel primo briefing reale: Mercedes +3.576%, Financial
# Partners +2.463%. L'ordinamento li metteva in cima perche' il tetto a +60 li
# faceva pari ai migliori.
UPSIDE_MAX_CREDIBILE = 100.0
VOTO_MINIMO = 400


def idoneo(c: dict) -> bool:
    """Un titolo entra nel radar solo se ha un voto, nessun blocco e una
    valutazione che regge."""
    if not c.get("mvf_vote_1000") or c["mvf_vote_1000"] < VOTO_MINIMO:
        return False
    up = _upside_pct(c)
    # sconto senza upside non e' un mispricing: e' una discesa che i fondamentali
    # giustificano (visto il 30 ottobre: JKHY -50%, WSO -0,5%)
    if up is None or up < 0 or up > UPSIDE_MAX_CREDIBILE:
        return False
    if (c.get("mvf_valuation") or {}).get("dispersion_flag") == "dispersione_alta":
        return False
    if (c.get("quality_gates") or {}).get("active"):
        return False
    if (c.get("confidence_score") or {}).get("gate_active"):
        return False
    if (c.get("mvf_valuation") or {}).get("abstain"):
        return False
    return True


def punteggio(c: dict) -> Optional[float]:
    up = _upside_pct(c)
    sconto = (c.get("tv") or {}).get("sconto_massimi_pct")
    iqi = (c.get("iqi_score") or {}).get("total")
    if up is None and sconto is None:
        return None
    return (0.5 * _clamp(up if up is not None else 0.0, -30, 60)
            + 0.3 * _clamp(sconto if sconto is not None else 0.0, 0, 40)
            + 0.2 * (iqi if iqi is not None else 40.0))


def riga(c: dict, gia_visti: dict) -> dict:
    sc = c.get("mvf_scoring") or {}
    ny = c.get("net_yield") or {}
    tv = c.get("tv") or {}
    tkr = c.get("ticker", "")
    att = costi.attrito(tkr, paese=((c.get("net_yield") or {}).get("country") or ""),
                        valuta=c.get("currency") or "")
    up = _upside_pct(c)
    return {
        "ticker": tkr,
        "nome": (c.get("name") or "")[:45],
        "classe": c.get("instrument_class"),
        "prezzo": c.get("price"),
        "valuta": c.get("currency"),
        "voto_mvf_1000": c.get("mvf_vote_1000"),
        "voto_parziale": bool(sc.get("voto_parziale")),
        "copertura_metriche_pct": round((sc.get("copertura") or 0) * 100),
        "metriche_omesse": sc.get("metriche_omesse", []),
        "iqi_100": (c.get("iqi_score") or {}).get("total"),
        "affidabilita_dati_100": (c.get("confidence_score") or {}).get("total"),
        "valore_intrinseco": c.get("intrinsic_value"),
        "upside_vs_valore_intrinseco_pct": None if up is None else round(up, 1),
        "sconto_dai_massimi_52w_pct": tv.get("sconto_massimi_pct"),
        "pe": tv.get("pe"), "pb": tv.get("pb"),
        "rendimento_lordo_pct": _pct(ny.get("gross_yield")),
        "rendimento_netto_italia_pct": _pct(ny.get("net_italy")),
        "rendimento_netto_con_rimborso_pct": _pct(ny.get("net_italy_refund")),
        "valuta_quotazione": att["valuta"],
        "ritenuta_trattenuta_pct": round(att["ritenuta_trattenuta"] * 100, 1),
        "nordico": att["nordico"],
        "moat": (sc.get("moat") or {}).get("rating"),
        "moat_test_numerico": (sc.get("moat") or {}).get("test_confermato"),
        "red_flag": (c.get("mvf_red_flags") or {}).get("critical", []),
        "gia_proposto_giorni": gia_visti.get(tkr.split(".")[0], 0),
    }


def _pct(x) -> Optional[float]:
    return None if x is None else round(float(x) * 100, 2)


def costruisci(tier1: list[dict], data_iso: str, gia_visti: dict,
               in_portafoglio: set, nordico_ammesso: set,
               famiglie: Optional[list[str]] = None,
               per_famiglia: int = PER_FAMIGLIA) -> dict:
    """{famiglia: [righe]} per le famiglie di oggi, piu' le etichette."""
    famiglie = famiglie or famiglie_del_giorno(data_iso)
    out: dict = {}
    for fam in famiglie:
        cand = []
        for c in tier1:
            if (c.get("tv") or {}).get("famiglia") != fam or not idoneo(c):
                continue
            tkr = c.get("ticker", "")
            if tkr.split(".")[0] in in_portafoglio:
                continue
            att = costi.attrito(tkr, paese=((c.get("net_yield") or {}).get("country") or ""),
                                valuta=c.get("currency") or "")
            if att["nordico"] and tkr not in nordico_ammesso:
                continue
            p = punteggio(c)
            if p is None:
                continue
            # un nome gia' proposto di recente scivola: la novita' conta
            p -= 4.0 * min(gia_visti.get(tkr.split(".")[0], 0), 5)
            cand.append((p, tkr, c))
        cand.sort(key=lambda x: (-x[0], x[1]))
        out[fam] = [riga(c, gia_visti) for _, _, c in cand[:per_famiglia]]
    return {"famiglie": famiglie, "etichette": {f: ETICHETTE[f] for f in famiglie},
            "titoli": out}
