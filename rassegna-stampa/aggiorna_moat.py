#!/usr/bin/env python3
"""Aggiorna l'archivio dei rating di moat Morningstar da VanEck.

Fonte: i PDF trimestrali "MOAT reconstitution" che VanEck pubblica per
l'indice Morningstar Wide Moat Focus (stesso URL ogni trimestre):

  https://www.vaneck.com/us/en/blogs/moat-investing/moat-reconstitution-<mese>-<anno>.pdf

Ogni PDF riguarda UNA delle due meta' dell'indice (dicembre/giugno oppure
marzo/settembre) e contiene: i 40 titoli con moat WIDE e il rapporto prezzo /
fair value Morningstar, i titoli aggiunti, quelli rimossi (con la colonna del
motivo: moat declassato, prezzo troppo alto, altro) e i 10 candidati
successivi. Letti i due PDF piu' recenti si ricostruisce l'insieme dei titoli
Wide e i movimenti.

Cosa NON c'e': il moat NARROW. Morningstar non lo pubblica da nessuna parte
gratuita. Se hai un export dal tuo account Morningstar (screener: Economic
Moat), mettilo in `dati/moat_manuale.csv` con colonne
`ticker,rating,fair_value,data` (rating = wide|narrow|none): ha la
precedenza su tutto il resto.

Uso:  python aggiorna_moat.py            # scarica e riscrive l'archivio
      python aggiorna_moat.py --pdf a.pdf b.pdf   # da file locali (test)
Richiede `pdftotext` (poppler-utils). Senza, o senza rete, lascia
l'archivio com'e' ed esce con codice 0: il briefing non deve fermarsi qui.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import re
import shutil
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

log = logging.getLogger("aggiorna_moat")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                    datefmt="%H:%M:%S")

QUI = Path(__file__).resolve().parent
ARCHIVIO = QUI / "dati" / "moat_morningstar.json"
MANUALE = QUI / "dati" / "moat_manuale.csv"
URL = "https://www.vaneck.com/us/en/blogs/moat-investing/moat-reconstitution-{mese}-{anno}.pdf"
MESI = {3: "march", 6: "june", 9: "september", 12: "december"}

_TICKER = r"[A-Z][A-Z0-9]{0,5}(?:[./-][A-Z])?"
_RIGA_SX = re.compile(rf"^\s*(\d+)\s{{2,}}(.+?)\s{{2,}}({_TICKER})\s+(\d\.\d{{2}})\s+(\d+\.\d{{2}})")
_RIGA_AGG = re.compile(rf"\s{{3,}}(\d+)\s{{2,}}(.+?)\s{{2,}}({_TICKER})\s+(\d\.\d{{2}})\s+(\S+)")
_RIGA_RIM = re.compile(rf"\s{{3,}}(\d+)\s{{2,}}(.+?)\s{{2,}}({_TICKER})(?:\s{{2,}}|\s*$)")
_RIGA_HOLD = re.compile(rf"(\d+)\s{{2,}}(.+?)\s{{2,}}({_TICKER})\s+(\d\.\d{{2}})(?=\s{{2,}}|\s*$)")
_RIGA_PROSS = re.compile(rf"^\s*(\d+)\s{{2,}}(.+?)\s{{2,}}({_TICKER})\s+(\d\.\d{{2}})\s*$")


# VanEck scrive BFB dove Yahoo e TradingView hanno BF-B / BF.B
ALIAS = {"BFB": "BF-B"}


def normalizza(t: str) -> str:
    """BF/B, BF.B -> BF-B (forma Yahoo)."""
    t = t.replace("/", "-").replace(".", "-")
    return ALIAS.get(t, t)


def pdf_a_testo(percorso: Path) -> str:
    if not shutil.which("pdftotext"):
        raise RuntimeError("pdftotext non disponibile")
    out = subprocess.run(["pdftotext", "-layout", str(percorso), "-"],
                         capture_output=True, text=True, timeout=60, check=True)
    return out.stdout


def leggi_testo(testo: str) -> dict:
    """Estrae data, titoli, aggiunti, rimossi (col motivo) e prossimi 10."""
    m = re.search(r"As of\s+(\w+)\s+(\d{1,2}),\s+(\d{4})", testo)
    if not m:
        raise ValueError("data non trovata nel PDF")
    data = datetime.strptime(" ".join(m.groups()), "%B %d %Y").date().isoformat()

    titoli, aggiunti, rimossi, prossimi, indice = [], [], [], [], []
    m_pfv = re.search(r"Price/Fair Value as of\s+(\w+)\s+(\d{1,2}),\s+(\d{4})", testo)
    data_pfv = (datetime.strptime(" ".join(m_pfv.groups()), "%B %d %Y").date().isoformat()
                if m_pfv else data)
    in_prossimi = False
    in_indice = False
    sezione_dx = "aggiunti"
    col_rimossi: dict[str, int] = {}
    for riga in testo.splitlines():
        if "Next 10 Potential" in riga:
            in_prossimi = True
            continue
        if "Index Holdings" in riga:
            in_prossimi, in_indice = False, True
            continue
        if in_indice:
            # due colonne di (n, nome, ticker, peso) per riga
            for h in _RIGA_HOLD.finditer(riga):
                indice.append({"ticker": normalizza(h.group(3)), "nome": h.group(2).strip(),
                               "peso": float(h.group(4))})
            continue
        if in_prossimi:
            p = _RIGA_PROSS.match(riga)
            if p and len(prossimi) < 10:
                prossimi.append({"ticker": normalizza(p.group(3)), "nome": p.group(2).strip(),
                                 "p_fv": float(p.group(4))})
            continue
        # La tabella a sinistra (i 40 titoli) e quelle a destra (aggiunti,
        # rimossi) condividono le righe: si legge prima la sinistra, poi il resto.
        sx = _RIGA_SX.match(riga)
        resto = riga
        if sx:
            titoli.append({"ticker": normalizza(sx.group(3)), "nome": sx.group(2).strip(),
                           "p_fv": float(sx.group(4))})
            resto = " " * sx.end() + riga[sx.end():]
        if "Removed Index Constituents" in riga:
            sezione_dx = "rimossi"
            continue
        if sezione_dx == "aggiunti":
            ag = _RIGA_AGG.search(resto[sx.end():] if sx else resto)
            if ag and "Screen" not in riga:
                aggiunti.append({"ticker": normalizza(ag.group(3)), "nome": ag.group(2).strip(),
                                 "p_fv": float(ag.group(4))})
            continue
        # Intestazione a tre righe: "Moat  Price/Fair" / "Name Ticker Other" /
        # "Rating Value". Le colonne si ricavano dalle posizioni.
        mh = re.search(r"Moat\s+Price/Fair", riga)
        if mh:
            col_rimossi["moat"] = mh.start()
            col_rimossi["prezzo"] = riga.index("Price/Fair")
            continue
        if re.search(r"Name\s+Ticker", riga) and "Other" in riga and "Failed" not in riga:
            col_rimossi["altro"] = riga.index("Other", sx.end() if sx else 0)
            continue
        if "•" in riga and col_rimossi:
            r = _RIGA_RIM.search(resto[sx.end():] if sx else resto)
            if r:
                pos = riga.index("•", sx.end() if sx else 0)
                motivo = min(col_rimossi, key=lambda k: abs(col_rimossi[k] - pos))
                rimossi.append({"ticker": normalizza(r.group(3)), "nome": r.group(2).strip(),
                                "motivo": motivo})
    if len(titoli) < 30:
        raise ValueError(f"solo {len(titoli)} titoli letti: layout cambiato?")
    if len(indice) < 40:
        raise ValueError(f"solo {len(indice)} titoli nell'elenco 'Index Holdings'")
    return {"data": data, "data_pfv": data_pfv, "titoli": titoli, "indice": indice,
            "aggiunti": aggiunti, "rimossi": rimossi, "prossimi": prossimi}


def costruisci_archivio(letture: list[dict]) -> dict:
    """Unisce le letture (dalla piu' recente) in un unico archivio.

    L'elenco "Index Holdings" del PDF piu' recente e' l'insieme corrente dei
    titoli Wide in indice; i rapporti P/FV vengono dalle tabelle di
    ricostituzione (quaranta per PDF) e dai "prossimi dieci".
    """
    letture = sorted(letture, key=lambda x: x["data"], reverse=True)
    recente = letture[0]
    pfv: dict = {}
    for L in reversed(letture):              # il piu' recente sovrascrive
        for t in L["titoli"] + L["prossimi"] + L["aggiunti"]:
            pfv[t["ticker"]] = (t["p_fv"], L["data_pfv"])
    titoli: dict = {}
    for t in recente["indice"]:
        v, d = pfv.get(t["ticker"], (None, None))
        titoli[t["ticker"]] = {"rating": "wide", "p_fv": v, "data_pfv": d,
                               "peso_indice": t["peso"], "stato": "in_indice",
                               "nome": t["nome"], "data": recente["data"]}
    for L in reversed(letture):
        for t in L["prossimi"]:
            if t["ticker"] not in titoli:
                titoli[t["ticker"]] = {"rating": "wide", "p_fv": t["p_fv"],
                                       "data_pfv": L["data_pfv"], "stato": "candidato",
                                       "nome": t["nome"], "data": L["data"]}
    usciti: dict = {}
    movimenti: list = []
    for L in reversed(letture):
        d = L["data"]
        for t in L["aggiunti"]:
            movimenti.append({"tipo": "ingresso", "ticker": t["ticker"], "nome": t["nome"],
                              "p_fv": t["p_fv"], "data": d})
        for t in L["rimossi"]:
            movimenti.append({"tipo": f"uscita_{t['motivo']}", "ticker": t["ticker"],
                              "nome": t["nome"], "data": d})
            if t["motivo"] == "moat":
                titoli.pop(t["ticker"], None)
                usciti[t["ticker"]] = {"motivo": "moat", "data": d, "nome": t["nome"]}
            elif t["ticker"] not in titoli:
                # tolto per prezzo o per altro: il moat Wide c'era ancora
                titoli[t["ticker"]] = {"rating": "wide", "p_fv": None,
                                       "stato": f"uscito_{t['motivo']}", "nome": t["nome"],
                                       "data": d}
    for tk in list(usciti):                  # rientrato dopo un'uscita: non piu' uscito
        if tk in titoli:
            usciti.pop(tk)
    movimenti.sort(key=lambda x: (x["data"], x["ticker"]), reverse=True)
    return {
        "aggiornato": recente["data"],
        "fonte": "VanEck MOAT (Morningstar Wide Moat Focus Index), ricostituzioni del "
                 + " e del ".join(L["data"] for L in letture),
        "avvertenza": "Copre solo il moat WIDE statunitense. P/FV = prezzo / fair value "
                      "Morningstar alla data indicata (data_pfv): invecchia, rileggi la data.",
        "titoli": titoli, "usciti": usciti, "movimenti": movimenti[:80],
    }


def applica_manuale(arch: dict) -> int:
    """Export manuale dall'account Morningstar: precedenza su tutto."""
    if not MANUALE.exists():
        return 0
    n = 0
    with MANUALE.open(newline="") as f:
        for r in csv.DictReader(f):
            t = normalizza((r.get("ticker") or "").strip().upper())
            rating = (r.get("rating") or "").strip().lower()
            if not t or rating not in ("wide", "narrow", "none"):
                continue
            fv = r.get("fair_value") or None
            arch["titoli"][t] = {
                "rating": rating, "p_fv": None,
                "fair_value": float(fv) if fv else None,
                "data": (r.get("data") or date.today().isoformat()),
                "stato": "manuale", "nome": t}
            arch["usciti"].pop(t, None)
            n += 1
    return n


def scarica(mese: int, anno: int, dest: Path) -> bool:
    import requests
    r = requests.get(URL.format(mese=MESI[mese], anno=anno), timeout=60,
                     headers={"User-Agent": "Mozilla/5.0 (compatible; ProximaBot/1.0)"})
    if r.status_code != 200 or not r.content.startswith(b"%PDF"):
        return False
    dest.write_bytes(r.content)
    return True


def ultimi_trimestri(n: int = 2, oggi: date | None = None) -> list[tuple[int, int]]:
    oggi = oggi or date.today()
    out, anno, mese = [], oggi.year, oggi.month
    cand = []
    for a in (anno, anno - 1):
        for m in (12, 9, 6, 3):
            if (a, m) <= (anno, mese):
                cand.append((a, m))
    cand.sort(reverse=True)
    return [(m, a) for a, m in cand[:n + 2]]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", nargs="+", help="PDF locali invece del download")
    ap.add_argument("--output", type=Path, default=ARCHIVIO)
    a = ap.parse_args()

    letture = []
    try:
        if a.pdf:
            for p in a.pdf:
                letture.append(leggi_testo(pdf_a_testo(Path(p))))
        else:
            import tempfile
            with tempfile.TemporaryDirectory() as td:
                for mese, anno in ultimi_trimestri():
                    if len(letture) >= 2:
                        break
                    dest = Path(td) / f"{anno}-{mese}.pdf"
                    try:
                        if scarica(mese, anno, dest):
                            letture.append(leggi_testo(pdf_a_testo(dest)))
                            log.info("Letta ricostituzione %s/%s: %d titoli", mese, anno,
                                     len(letture[-1]["titoli"]))
                        else:
                            log.info("Ricostituzione %s/%s non ancora pubblicata.", mese, anno)
                    except Exception as e:
                        log.warning("Ricostituzione %s/%s non leggibile: %s", mese, anno, e)
    except Exception as e:
        log.warning("Aggiornamento moat saltato (%s): archivio invariato.", e)
        return 0
    if len(letture) < 2:
        log.warning("Servono due ricostituzioni (le due meta' dell'indice), trovate %d: "
                    "archivio invariato.", len(letture))
        return 0
    arch = costruisci_archivio(letture)
    n_man = applica_manuale(arch)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(arch, indent=1, ensure_ascii=False, sort_keys=True))
    log.info("Archivio moat: %d titoli Wide, %d usciti per moat, %d movimenti, %d da CSV manuale -> %s",
             len(arch["titoli"]), len(arch["usciti"]), len(arch["movimenti"]), n_man, a.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
