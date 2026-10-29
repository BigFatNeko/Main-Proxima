"""Rating di moat economico Morningstar: archivio locale e lettura.

Il rating Morningstar e' a licenza e non c'e' nessuna API gratuita. L'unica
fonte pubblica e riproducibile e' VanEck: ogni trimestre pubblica, per
l'indice Morningstar Wide Moat Focus, le societa' con moat Wide e il loro
rapporto prezzo / fair value Morningstar, piu' quelle uscite e il motivo
(moat declassato, prezzo troppo alto). Cio' copre il moat WIDE statunitense.
Per il moat NARROW non esiste una fonte pubblica: non si inventa.

L'archivio vive in `dati/moat_morningstar.json` ed e' scritto da
`aggiorna_moat.py`. Formato:

  {"aggiornato": "2026-09-18",
   "fonte": "VanEck MOAT, ricostituzioni di giugno e settembre 2026",
   "titoli": {"NKE": {"rating": "wide", "p_fv": 0.41, "data": "2026-09-18"}},
   "usciti": {"BMY": {"motivo": "moat", "data": "2026-09-18"}}}
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

log = logging.getLogger("moat")

ARCHIVIO = Path(__file__).resolve().parent / "dati" / "moat_morningstar.json"
_cache: Optional[dict] = None


def carica(forza: bool = False) -> dict:
    global _cache
    if _cache is not None and not forza:
        return _cache
    try:
        _cache = json.loads(ARCHIVIO.read_text())
    except FileNotFoundError:
        _cache = {}
    except Exception as e:
        log.warning("Archivio moat illeggibile (%s): proseguo senza rating.", e)
        _cache = {}
    return _cache


def rating(ticker_yf: str) -> Optional[str]:
    """'wide', 'none' (uscito per moat declassato) o None se non coperto.

    Solo titoli senza suffisso di borsa: l'archivio copre il mercato USA.
    """
    t = (ticker_yf or "").upper()
    if "." in t:
        return None
    arch = carica()
    t = t.replace("-", ".") if t not in arch.get("titoli", {}) else t
    voce = arch.get("titoli", {}).get(t)
    # Uscito per moat declassato = oggi Narrow o None, non si sa quale:
    # per il voto vale come "non coperto" (max Sufficiente, tag [U]).
    return voce.get("rating") if voce else None
