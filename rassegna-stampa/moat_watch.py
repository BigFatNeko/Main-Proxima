"""Moat Watch: chi ha un vantaggio competitivo, chi lo ha perso, a che prezzo.

Due elenchi, con due livelli di affidabilita' dichiarati nel contesto:

  WIDE  — rating Morningstar vero, ricavato dalle ricostituzioni trimestrali
          dell'indice Morningstar Wide Moat Focus (VanEck, vedi
          aggiorna_moat.py), con il rapporto prezzo / fair value di
          Morningstar. Ingressi e uscite sono quelli dell'indice: un titolo
          ENTRA quando, restando Wide, il prezzo scende abbastanza; ESCE per
          moat declassato (il segnale che conta), per prezzo salito, o per
          altro.
  NARROW — Morningstar non lo pubblica gratis. Non si finge: l'elenco e' il
          TEST NUMERICO del moat (ROIC sopra il costo del capitale in 4 anni
          su 5, margine operativo sopra la mediana, ROIC incrementale) sui
          titoli analizzati e privi di rating Wide, marcato [U]. Le novita'
          sono il confronto col giorno precedente. Se l'utente fornisce
          `dati/moat_manuale.csv` (export dal suo account Morningstar) i
          rating veri sostituiscono il test.
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

import costi_italia as costi

log = logging.getLogger("moat_watch")

FINESTRA_GIORNI = 120          # una ricostituzione e' trimestrale
FINESTRA_MOAT_GIORNI = 200     # un moat declassato resta una notizia piu' a lungo
SOGLIA_PFV_ACQUISTO = 0.85     # Morningstar: sotto, il titolo e' scontato
MAX_NARROW = 12


def _base(t: str) -> str:
    return (t or "").upper()


def _riga(tkr: str, voce: dict, c: Optional[dict], in_portafoglio: set) -> dict:
    sc = (c or {}).get("mvf_scoring") or {}
    val = (c or {}).get("mvf_valuation") or {}
    up = val.get("upside_at_current_pct")
    if up is None and c and c.get("intrinsic_value") and c.get("price"):
        up = (c["intrinsic_value"] / c["price"] - 1) * 100
    return {
        "ticker": tkr,
        "nome": (voce.get("nome") or (c or {}).get("name") or "")[:40],
        "p_fv_morningstar": voce.get("p_fv"),
        "p_fv_data": voce.get("data_pfv") or voce.get("data"),
        "stato_indice": voce.get("stato"),
        "analizzato_mvf": c is not None,
        "prezzo": (c or {}).get("price"),
        "voto_mvf_1000": (c or {}).get("mvf_vote_1000"),
        "iqi_100": ((c or {}).get("iqi_score") or {}).get("total"),
        "upside_vs_valore_intrinseco_pct": None if up is None else round(float(up), 1),
        "test_numerico": (sc.get("moat") or {}).get("test"),
        "test_numerico_confermato": (sc.get("moat") or {}).get("test_confermato"),
        "gate_attivi": ((c or {}).get("quality_gates") or {}).get("active", []),
        "in_portafoglio": tkr in in_portafoglio,
    }


def _carica_stato(percorso: Path) -> dict:
    try:
        return json.loads(percorso.read_text())
    except Exception:
        return {}


def costruisci(tier1: list[dict], archivio: dict, data_iso: str,
               in_portafoglio: set, percorso_stato: Optional[Path] = None,
               oggi: Optional[date] = None) -> dict:
    """Struttura per il contesto del briefing. Aggiorna il file di stato."""
    oggi = oggi or date.today()
    per_tkr = {c.get("ticker", "").upper(): c for c in tier1}
    titoli = archivio.get("titoli", {})
    movimenti = archivio.get("movimenti", [])
    def recenti(tipo: str, giorni: int = FINESTRA_GIORNI) -> list[dict]:
        limite = (oggi - timedelta(days=giorni)).isoformat()
        out = []
        for mv in movimenti:
            if mv["tipo"] == tipo and mv["data"] >= limite:
                tkr = mv["ticker"]
                voce = titoli.get(tkr) or {"nome": mv.get("nome"), "p_fv": mv.get("p_fv"),
                                           "data": mv["data"], "stato": tipo}
                r = _riga(tkr, voce, per_tkr.get(tkr), in_portafoglio)
                r["data_movimento"] = mv["data"]
                if mv.get("p_fv") is not None:
                    r["p_fv_morningstar"] = mv["p_fv"]
                out.append(r)
        return out

    ingressi = recenti("ingresso")
    uscite_moat = recenti("uscita_moat", FINESTRA_MOAT_GIORNI)
    uscite_prezzo = recenti("uscita_prezzo")

    # Wide scontati: P/FV Morningstar basso E valutazione MVF che non contraddice
    conferme, divergenze = [], []
    for tkr, voce in titoli.items():
        if voce.get("rating") != "wide" or voce.get("p_fv") is None:
            continue
        c = per_tkr.get(tkr)
        r = _riga(tkr, voce, c, in_portafoglio)
        if voce["p_fv"] <= SOGLIA_PFV_ACQUISTO and c is not None:
            up = r["upside_vs_valore_intrinseco_pct"]
            if up is not None and 10 <= up <= 100 and not r["gate_attivi"] \
                    and (c.get("mvf_valuation") or {}).get("dispersion_flag") != "dispersione_alta":
                conferme.append(r)
            elif up is not None and up < 0:
                divergenze.append(r)
    conferme.sort(key=lambda r: (r["p_fv_morningstar"], r["ticker"]))
    divergenze.sort(key=lambda r: (r["p_fv_morningstar"], r["ticker"]))

    # Narrow (numerico): analizzati, senza rating Wide, test confermato
    wide = {t for t, v in titoli.items() if v.get("rating") == "wide"}
    narrow_oggi = []
    for c in tier1:
        tkr = c.get("ticker", "").upper()
        mo = (c.get("mvf_scoring") or {}).get("moat") or {}
        if tkr in wide or mo.get("rating") or not mo.get("test_confermato"):
            continue
        if (c.get("instrument_class") or "common") != "common":
            continue
        if (c.get("quality_gates") or {}).get("active"):
            continue
        narrow_oggi.append(c)
    narrow_oggi.sort(key=lambda c: -((c.get("iqi_score") or {}).get("total") or 0))
    insieme_oggi = [c["ticker"] for c in narrow_oggi]

    stato = _carica_stato(percorso_stato) if percorso_stato else {}
    corrente = stato.get("corrente") or {}
    precedente = stato.get("precedente") or {}
    # idempotenza: i tre briefing del giorno leggono lo stesso "ieri"
    ieri = precedente if corrente.get("data") == data_iso else corrente
    nuovi, usciti = [], []
    if ieri.get("narrow") is not None:
        nuovi = [t for t in insieme_oggi if t not in set(ieri["narrow"])]
        usciti = [t for t in ieri["narrow"] if t not in set(insieme_oggi)]
    if percorso_stato and corrente.get("data") != data_iso:
        nuovo_stato = {"corrente": {"data": data_iso, "narrow": insieme_oggi},
                       "precedente": corrente}
        try:
            percorso_stato.parent.mkdir(parents=True, exist_ok=True)
            percorso_stato.write_text(json.dumps(nuovo_stato, indent=1))
        except Exception as e:
            log.warning("Stato Moat Watch non salvato: %s", e)

    righe_narrow = [_riga(c["ticker"], {"nome": c.get("name")}, c, in_portafoglio)
                    for c in narrow_oggi[:MAX_NARROW]]
    for r in righe_narrow:
        r["nuovo_oggi"] = r["ticker"] in set(nuovi)

    return {
        "wide": {
            "fonte": archivio.get("fonte"),
            "aggiornato": archivio.get("aggiornato"),
            "avvertenza": archivio.get("avvertenza"),
            "titoli_wide_noti": len(wide),
            "ingressi_recenti": ingressi,
            "uscite_per_moat": uscite_moat,
            "uscite_per_prezzo": uscite_prezzo,
            "scontati_confermati_da_mvf": conferme[:8],
            "scontati_ma_mvf_non_conferma": divergenze[:6],
        },
        "narrow_numerico": {
            "nota": ("NON è il rating Morningstar: è il test numerico del moat (ROIC "
                     "sopra il costo del capitale, margini, ROIC incrementale) su titoli "
                     "analizzati e privi di rating Wide. Tag [U]."),
            "elenco": righe_narrow,
            "entrati_rispetto_a_ieri": [t for t in nuovi][:10],
            "usciti_rispetto_a_ieri": [t for t in usciti][:10],
            "confronto_disponibile": ieri.get("narrow") is not None,
        },
    }
