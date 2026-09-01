"""Motore di scoring MVF-S — bande calibrazione v1.1 (§1, §2, §2-bis).

punteggio = peso x clamp(frazione_livello + mod_trend + bonus_settore, 0, 1)
Metriche senza dato -> OMESSE + ri-basatura (mai punteggi inventati).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import config
import sector_stats


def _pctile_frac(pctile: float) -> float:
    """Banda relativa al settore dal rango percentile (calibrazione §1):
    top decile 1.0 / top quartile 0.8 / sopra mediana 0.6 / meta' inferiore
    0.35 / coda 0.0. La mediana di settore vale ~0.6, non 0."""
    if pctile >= 90:
        return 1.0
    if pctile >= 75:
        return 0.8
    if pctile >= 50:
        return 0.6
    if pctile >= 25:
        return 0.35
    return 0.0


def step_up(v, bands):
    """bands = [(soglia, frac), ...] decrescenti: v >= soglia -> frac."""
    for cut, frac in bands:
        if v >= cut:
            return frac
    return 0.0


def step_down(v, bands):
    """bands = [(soglia, frac), ...] crescenti: v <= soglia -> frac."""
    for cut, frac in bands:
        if v <= cut:
            return frac
    return 0.0


# ------------------------------------------------------- bande v1.1 (REVIEW)
def frac_C1(v, m, ctx): return step_up(v, [(80, 1.0), (60, .8), (40, .6), (25, .35)])
def frac_C2(v, m, ctx): return step_up(v, [(45, 1.0), (30, .8), (20, .6), (10, .35)])
def frac_C3(v, m, ctx): return step_up(v, [(30, 1.0), (20, .8), (12, .6), (5, .35)])
frac_C4 = frac_C3
frac_C5 = frac_C3


def frac_C6(v, m, ctx):
    f = step_up(v, [(15, 1.0), (10, .8), (5, .6), (0, .35)])  # DA SPEC
    ni_cagr = m.get("C6", {}).get("ni_cagr")
    if v is not None and ni_cagr is not None and v - ni_cagr > 5 and ni_cagr <= 1:
        f = min(f, 0.5)  # guard buyback/NI piatto (spec)
    return f


def frac_C7(v, m, ctx):
    f = step_up(v, [(12, 1.0), (8, .8), (4, .6), (0, .35)])  # DA SPEC
    fcf_cagr = m.get("C7", {}).get("fcf_cagr")
    if v is not None and fcf_cagr is not None and v - fcf_cagr > 5 and fcf_cagr <= 1:
        f = min(f, 0.5)  # guard anti-diluizione/buyback (spec)
    return f


def frac_C8(v, m, ctx):
    spread = m.get("C8", {}).get("spread")
    if spread is None:
        return None
    return step_up(spread, [(8, 1.0), (4, .8), (0, .6), (-4, .35)])


def frac_C9(v, m, ctx):
    f = step_up(v, [(30, 1.0), (20, .8), (12, .6), (6, .35)])
    de = ctx.get("de")
    if de is not None and de > 2:
        f = min(f, 0.6)  # guard leva
    return f


def frac_C10(v, m, ctx): return step_up(v, [(20, 1.0), (12, .8), (6, .6), (2, .35)])
def frac_C11(v, m, ctx): return step_down(v, [(0.3, 1.0), (0.8, .8), (1.5, .6), (2.5, .35)])
def frac_C12(v, m, ctx): return step_down(v, [(0.20, 1.0), (0.40, .8), (0.55, .6), (0.70, .35)])


def frac_C13(v, m, ctx):
    return step_up(v, [(3.0, 1.0), (2.6, .85), (2.2, .70), (1.81, .55),
                       (1.5, .35), (1.23, .15)])


def frac_C14(v, m, ctx):
    return step_down(v, [(2, 1.0), (4, .8), (6, .6), (9, .4), (12, .2)])


def frac_C15(v, m, ctx):
    med = ctx.get("sector_median_C15")
    if med in (None, 0):
        return None  # relativa: senza mediana di settore si omette
    r = v / med
    return step_down(r, [(0.7, 1.0), (1.0, .8), (1.3, .6), (1.8, .35)])


def frac_C16(v, m, ctx):
    if 0.9 <= v <= 1.5:
        return 1.0
    if 1.5 < v <= 2.5:
        return 0.8
    if 0.6 <= v < 0.9:
        return 0.6
    if v > 2.5:
        return 0.35
    return 0.0


def frac_C17(v, m, ctx):
    med = ctx.get("sector_median_C17")
    if med in (None, 0):
        return None
    r = v / med
    return step_up(r, [(1.2, 1.0), (0.8, .8), (0.5, .6), (0.0, .35)])


def frac_C19(v, m, ctx):
    f = step_up(v, [(10, 1.0), (7, .8), (5, .6), (3, .4), (1, .25), (0.0001, .10)])
    if v is not None and v >= 7:
        fcf_payout = m.get("C20", {}).get("fcf_payout")
        payout = m.get("C20", {}).get("value")
        covered = (fcf_payout is not None and fcf_payout <= 1 / 1.3) and \
                  (payout is None or payout <= 0.90)
        if not covered:
            f = min(f, 0.35)  # yield-trap guard rafforzato (REVIEW)
    return f


def frac_C20(v, m, ctx):
    p = v * 100
    fcf_payout = m.get("C20", {}).get("fcf_payout")
    if fcf_payout is not None and fcf_payout > 1.0:
        return 0.0  # cross-check FCF: vale il peggiore
    if 30 <= p <= 60:
        return 1.0
    if p < 30:
        return 0.8
    if p <= 75:
        return 0.6
    if p <= 90:
        return 0.35
    return 0.0


def frac_C21(v, m, ctx):
    if m.get("C21", {}).get("cut_in_5y"):
        return 0.0
    return step_up(v, [(8, 1.0), (5, .8), (2, .6), (0, .35)])


def frac_C22(v, m, ctx):
    # v = riduzione % annua dello share count (positivo = buyback netto)
    if v >= 2:
        return 1.0
    if v >= 0.2:
        return 0.7
    if v >= -0.2:
        return 0.5
    if v >= -2:
        return 0.25
    return 0.0


def frac_C23(v, m, ctx):
    return step_up(v, [(8, 1.0), (3, .8), (0, .5), (-5, .25)])


def frac_C24(v, m, ctx):
    # v = scostamento % del P/E attuale dalla mediana storica. DA SPEC:
    # contrazione premiata, espansione forte azzerata; value-trap guard.
    if v <= -10:
        f = 1.0
    elif v <= 10:
        f = 0.5
    else:
        f = 0.0
    if f > 0.25 and v <= -10:
        om_serie = [x for x in m.get("C3", {}).get("series", []) if x is not None]
        rev = [x for x in ctx.get("revenue_series", []) if x is not None]
        deteriorating = (len(om_serie) >= 3 and om_serie[0] < om_serie[2] * 0.9) or \
                        (len(rev) >= 3 and rev[0] < rev[1] < rev[2])
        if deteriorating:
            f = 0.25  # value-trap guard (spec)
    return f


def frac_C25(v, m, ctx):
    vol = m.get("C25", {}).get("volatility") or 0
    if v < 10 or (v < 15 and vol > 6):
        return 0.0 if (v < 10 and vol > 3) else 0.6
    if 15 <= v <= 28:
        return 1.0
    if v <= 35:
        return 0.8
    if 10 <= v < 15:
        return 0.6
    return 0.35  # > 35%


def frac_C26(v, m, ctx):
    return {"wide": 1.0, "narrow": 0.6, "none": 0.0}.get(v)


def frac_C27(v, m, ctx):
    acc = m.get("C27", {}).get("accruals")
    if acc is not None and acc > 0.10:
        return 0.0
    if v >= 1.1 and (acc is None or acc <= 0):
        return 1.0
    if v >= 0.9:
        return 0.8
    if v >= 0.7:
        return 0.6
    if v >= 0.5:
        return 0.35
    return 0.0


@dataclass
class MetricDef:
    mid: str
    name: str
    weight: int
    frac_fn: object
    higher_is_better: bool = True
    trend_active: bool = True   # "Variation %" spec: esenzioni gia' escluse


COMMON_DEFS = [
    MetricDef("C1", "Gross Margin", 15, frac_C1),
    MetricDef("C2", "EBITDA Margin", 5, frac_C2),
    MetricDef("C3", "Operating Margin", 25, frac_C3),
    MetricDef("C4", "Net Margin", 18, frac_C4),
    MetricDef("C5", "FCF Margin", 12, frac_C5),
    MetricDef("C6", "EPS Growth", 10, frac_C6, trend_active=False),
    MetricDef("C7", "FCF/share Growth", 18, frac_C7, trend_active=False),
    MetricDef("C8", "ROIC", 15, frac_C8),
    MetricDef("C9", "ROE", 3, frac_C9),
    MetricDef("C10", "ROA", 5, frac_C10),
    MetricDef("C11", "Debt/Equity", 10, frac_C11, higher_is_better=False),
    MetricDef("C12", "Debt/Assets", 10, frac_C12, higher_is_better=False),
    MetricDef("C13", "Altman-Z", 5, frac_C13, trend_active=False),
    MetricDef("C14", "SBC/Revenue", 5, frac_C14, higher_is_better=False),
    MetricDef("C15", "CapEx/Revenue", 5, frac_C15, higher_is_better=False),
    MetricDef("C16", "CapEx/D&A", 3, frac_C16, trend_active=False),
    MetricDef("C17", "R&D/Revenue", 7, frac_C17),
    MetricDef("C18", "Insider Trading", 5, None, trend_active=False),
    MetricDef("C19", "Dividend Yield", 16, frac_C19, trend_active=False),
    MetricDef("C20", "Dividend Payout", 10, frac_C20, trend_active=False),
    MetricDef("C21", "Dividend Growth", 10, frac_C21, trend_active=False),
    MetricDef("C22", "Buyback", 5, frac_C22, trend_active=False),
    MetricDef("C23", "Price CAGR", 5, frac_C23, trend_active=False),
    MetricDef("C24", "Multiple Expansion", 5, frac_C24, trend_active=False),
    MetricDef("C25", "Tax %", 13, frac_C25, trend_active=False),
    MetricDef("C26", "MOAT", 25, frac_C26, trend_active=False),
    MetricDef("C27", "Earnings Quality", 15, frac_C27, trend_active=False),
]
BASE_COMMON = 280

# Settori senza R&D: C17 omessa e ri-basata, non punita (calibrazione §2)
NO_RD_SECTORS = ("consumer defensive", "utilities", "real estate",
                 "financial services", "energy", "basic materials")


def _trend_mod(serie: list, higher_is_better: bool) -> float:
    vals = [v for v in serie if v is not None]
    if len(vals) < 3:
        return 0.0
    recent = vals[0]
    old = vals[min(len(vals) - 1, 4)]
    if old == 0:
        return 0.0
    delta = (recent - old) / abs(old)
    if not higher_is_better:
        delta = -delta
    if delta > 0.10:
        return 0.10
    if delta < -0.10:
        return -0.10
    return 0.0


def effective_weights(m: dict) -> tuple[dict[str, int], str]:
    """Redistribuzioni spec Sez. 3E (no dividendo) / 3F (DDM attivo)."""
    w = {d.mid: d.weight for d in COMMON_DEFS}
    dy = m.get("C19", {}).get("value")
    regime = "standard"
    if dy is not None and dy <= 0.001:
        # Sez. 3E: 36 punti dividendo redistribuiti
        for mid in ("C19", "C20", "C21"):
            w[mid] = 0
        w["C5"] += 10   # FCF Margin 12->22
        w["C22"] += 10  # Buyback 5->15
        w["C23"] += 8   # Price CAGR 5->13
        w["C8"] += 8    # ROIC 15->23
        regime = "no-dividendo (3E)"
    elif m.get("ddm_applied"):
        w["C19"], w["C20"], w["C21"] = 8, 5, 5
        w["C5"] += 10   # 12->22
        w["C4"] += 8    # 18->26
        regime = "DDM-dimezzato (3F)"
    return w, regime


def score_common(m: dict) -> dict:
    """Scoring del motore common. Ritorna voto, copertura, dettaglio metriche."""
    ctx = m["ctx"]
    weights, regime = effective_weights(m)
    sector_l = (ctx.get("sector") or "").lower()
    detail = []
    raw_pts = 0.0
    scored_w = 0
    omitted = []
    base = sum(weights.values())
    for d in COMMON_DEFS:
        w = weights[d.mid]
        if w == 0:
            continue
        entry = m.get(d.mid, {})
        v = entry.get("value")
        # omissioni strutturali
        if d.mid == "C17" and (v is None or v == 0) and sector_l in NO_RD_SECTORS:
            omitted.append((d.mid, w, "settore senza R&D"))
            continue
        if d.mid == "C13" and ctx.get("altman_exempt"):
            omitted.append((d.mid, w, "settore esente Altman"))
            continue
        if v is None or d.frac_fn is None:
            omitted.append((d.mid, w, "dato non reperibile"))
            continue
        lvl = d.frac_fn(v, m, ctx)
        if lvl is None:
            omitted.append((d.mid, w, "riferimento settoriale mancante"))
            continue
        # CORRETTIVO SETTORIALE (Q1: premiare chi sovraperforma il settore;
        # spec Sez. 4). Per le metriche sector-dependent, chi e' alto rispetto
        # al proprio settore non viene punito dalla soglia assoluta: si prende
        # il massimo tra banda assoluta e banda relativa al percentile.
        sector_rel = 0.0
        pctile = ctx.get(f"sector_pctile_{d.mid}")
        if d.mid in sector_stats.SECTOR_RELATIVE and pctile is not None:
            sector_rel = _pctile_frac(pctile)
        base_lvl = max(lvl, sector_rel)
        trend = _trend_mod(entry.get("series", []), d.higher_is_better) \
            if d.trend_active else 0.0
        # bonus residuo solo per le metriche NON sector-relative gia' in top quintile
        bonus = 0.10 if (d.mid not in sector_stats.SECTOR_RELATIVE
                         and (pctile or 0) >= 80) else 0.0
        frac = max(0.0, min(1.0, base_lvl + trend + bonus))
        pts = w * frac
        raw_pts += pts
        scored_w += w
        detail.append({"id": d.mid, "name": d.name, "weight": w,
                       "value": round(v, 3) if isinstance(v, (int, float)) else v,
                       "level": round(lvl, 2), "sector_rel": round(sector_rel, 2),
                       "sector_pctile": round(pctile) if pctile is not None else None,
                       "trend": trend, "bonus": bonus,
                       "points": round(pts, 1), "tag": entry.get("tag", "U")})
    coverage = scored_w / base if base else 0.0
    vote = (raw_pts / scored_w * 1000) if scored_w else None
    # penalita' Altman additiva progressiva (calibrazione C13, deviazione dich.)
    z = m.get("C13", {}).get("value")
    altman_penalty = 0.0
    if vote is not None and z is not None and not ctx.get("altman_exempt"):
        if z < 1.23:
            altman_penalty = 0.20
        elif z < 1.4:
            altman_penalty = 0.15
        elif z < 1.6:
            altman_penalty = 0.10
        elif z < 1.81:
            altman_penalty = 0.05
        vote *= (1 - altman_penalty)
    return {"vote": round(vote) if vote is not None else None,
            "coverage": round(coverage, 3),
            "base_original": BASE_COMMON, "base_effective": scored_w,
            "regime_pesi": regime, "altman_penalty": altman_penalty,
            "omitted": [{"id": o[0], "weight": o[1], "reason": o[2]} for o in omitted],
            "detail": detail}
