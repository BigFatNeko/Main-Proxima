"""Statistiche di settore in-universo (calibrazione §1, Q1: premiare chi
sovraperforma il proprio settore; spec Sez. 4: percentile ranking vs peer).

Calcola, per ciascun settore e metrica, mediana e rango percentile di ogni
titolo. Alimenta il correttivo settoriale dello scoring: una metrica
sotto-soglia in assoluto ma alta rispetto al settore (es. margini della
grande distribuzione) non viene punita come se fosse debolezza.
"""
from __future__ import annotations

import statistics

# metriche giudicate anche in chiave settoriale (dipendono dal settore)
SECTOR_RELATIVE = ("C1", "C2", "C3", "C4", "C5", "C10")


MIN_PEERS = 4          # sotto questa soglia il gruppo non e' significativo


def _bucketize(records, key_fn):
    buckets: dict[str, dict[str, list[float]]] = {}
    for rec in records:
        key = key_fn(rec) or "?"
        m = rec["metrics"]
        for mid in SECTOR_RELATIVE:
            v = m.get(mid, {}).get("value")
            if v is None:
                continue
            buckets.setdefault(key, {}).setdefault(mid, []).append(v)
    out: dict = {}
    for key, mids in buckets.items():
        out[key] = {mid: {"median": statistics.median(sorted(vs)),
                          "values": sorted(vs), "n": len(vs)}
                    for mid, vs in mids.items()}
    return out


def collect(records: list[dict]) -> dict:
    """records = [{'sector':.., 'industry':.., 'metrics': m}, ...].
    Calcola le distribuzioni a due livelli: industria (fine) e settore (largo).
    L'inject preferisce l'industria se ha abbastanza peer, altrimenti il settore."""
    return {"industry": _bucketize(records, lambda r: (r.get("industry") or "").lower()),
            "sector": _bucketize(records, lambda r: r.get("sector") or "?")}


def pctile(value: float, sorted_vals: list[float]) -> float:
    """Rango percentile (0-100) di value nella distribuzione."""
    if not sorted_vals:
        return 50.0
    below = sum(1 for v in sorted_vals if v < value)
    equal = sum(1 for v in sorted_vals if v == value)
    return (below + 0.5 * equal) / len(sorted_vals) * 100


def inject(ctx: dict, m: dict, stats: dict) -> None:
    """Popola ctx['sector_median_<id>'] e ctx['sector_pctile_<id>'].
    Preferisce il gruppo per INDUSTRIA (fine) se ha >=4 peer, altrimenti il
    SETTORE (largo); sotto soglia in entrambi, il correttivo non si applica."""
    ind = (ctx.get("industry") or "").lower()
    sec = ctx.get("sector") or "?"
    ind_stats = stats.get("industry", {}).get(ind, {})
    sec_stats = stats.get("sector", {}).get(sec, {})
    for mid in SECTOR_RELATIVE:
        v = m.get(mid, {}).get("value")
        if v is None:
            continue
        st = ind_stats.get(mid)
        level = "industria"
        if not st or st["n"] < MIN_PEERS:
            st = sec_stats.get(mid)
            level = "settore"
        if not st or st["n"] < MIN_PEERS:
            continue
        ctx[f"sector_median_{mid}"] = st["median"]
        ctx[f"sector_pctile_{mid}"] = pctile(v, st["values"])
        ctx.setdefault("peer_level", {})[mid] = f"{level} (n={st['n']})"
