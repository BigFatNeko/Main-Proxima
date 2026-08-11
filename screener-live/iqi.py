"""IQI-S, CS-S, MoS e prezzo ideale indicativo (calibrazione §9, spec Sez. 7/10).

IQI = 0.40 x Blocco A (solidita') + 0.60 x Blocco B (prospettive & reddito).
CS = affidabilita' dei dati (provenienza, completezza, puntualita', coerenza).
MoS_finale = MoS_base(IQI) + overlay(CS), cap 60%; prezzo ideale = FV x (1-MoS).
Tutto cio' che esce da qui in Regime S e' marcato "indicativo".
"""
from __future__ import annotations

import statistics

import config
from scoring import step_up, step_down, frac_C3, frac_C5, frac_C11, frac_C12, frac_C27


def _clean(serie):
    return [v for v in serie if v is not None]


# ------------------------------------------------------------------ IQI-S --
def blocco_a(m: dict) -> tuple[float | None, list[str]]:
    ctx = m["ctx"]
    notes = []
    pts = 0.0
    maxp = 0.0
    # A1 patrimoniale (30): leva, copertura interessi, Altman
    sub = []
    de, da = m.get("C11", {}).get("value"), m.get("C12", {}).get("value")
    if de is not None:
        sub.append(frac_C11(de, m, ctx))
    if da is not None:
        sub.append(frac_C12(da, m, ctx))
    if ctx.get("ebit0") and ctx.get("interest_expense"):
        cov = ctx["ebit0"] / ctx["interest_expense"]
        sub.append(step_up(cov, [(8, 1.0), (4, .75), (2, .5), (1.5, .25)]))
    z = m.get("C13", {}).get("value")
    if z is not None and not ctx.get("altman_exempt"):
        sub.append(step_up(z, [(3.0, 1.0), (2.2, .7), (1.81, .45), (1.23, .15)]))
    if sub:
        pts += 30 * statistics.mean(sub)
        maxp += 30
    # A2 reddituale (25): livello margini, stabilita', ROIC-WACC
    sub = []
    om = m.get("C3", {}).get("value")
    if om is not None:
        sub.append((8 / 25, frac_C3(om, m, ctx)))
        om_serie = _clean(m.get("C3", {}).get("series", []))
        if len(om_serie) >= 3 and statistics.mean(om_serie) > 0:
            cv = statistics.pstdev(om_serie) / statistics.mean(om_serie)
            stab = 1.0 if cv < 0.1 else 0.7 if cv < 0.2 else 0.4 if cv < 0.35 else 0.1
            sub.append((7 / 25, stab))
    spread = m.get("C8", {}).get("spread")
    if spread is not None:
        sub.append((10 / 25, step_up(spread, [(8, 1.0), (4, .8), (0, .6), (-4, .3)])))
    if sub:
        got = sum(w * f for w, f in sub)
        tot = sum(w for w, _ in sub)
        pts += 25 * (got / tot)
        maxp += 25
    # A3 cassa (30): FCF margin, costanza, conversione, copertura div+capex
    sub = []
    fm = m.get("C5", {}).get("value")
    if fm is not None:
        sub.append((8 / 30, frac_C5(fm, m, ctx)))
    fcf = _clean(ctx.get("fcf_series", []))
    if len(fcf) >= 3:
        sub.append((7 / 30, sum(1 for v in fcf if v > 0) / len(fcf)))
    ccr = m.get("C27", {}).get("value")
    if ccr is not None:
        sub.append((8 / 30, frac_C27(ccr, m, ctx)))
    if fcf and ctx.get("capex0") is not None:
        need = ctx.get("dividends_paid0", 0) + ctx["capex0"]
        if need > 0:
            cov = (ctx.get("cfo0") or 0) / need
            sub.append((7 / 30, step_up(cov, [(1.5, 1.0), (1.2, .75), (1.0, .5), (0.0, .2)])))
    if sub:
        got = sum(w * f for w, f in sub)
        tot = sum(w for w, _ in sub)
        pts += 30 * (got / tot)
        maxp += 30
    # A4 competitiva (15): moat; se assente si ri-basa il blocco (dichiarato)
    moat = m.get("C26", {}).get("value")
    if moat is not None:
        moat_pts = {"wide": 12, "narrow": 6, "none": 0}.get(moat, 0)
        pts += moat_pts + 1.5  # trend/capital allocation: neutro in batch
        maxp += 15
    else:
        notes.append("A4 (moat) non disponibile: Blocco A ri-basato")
    if maxp == 0:
        return None, notes
    return 100 * pts / maxp, notes


def blocco_b(m: dict) -> tuple[float | None, list[str], str]:
    ctx = m["ctx"]
    notes = []
    years = ctx.get("div_years_paid", 0)
    dy = m.get("C19", {}).get("value") or 0.0
    buyback = (m.get("C22", {}).get("value") or 0) > 0.2
    cut = m.get("C21", {}).get("cut_in_5y")
    # tier dividendo (spec V7)
    if years >= 10 and not cut:
        tier, b1_max, b2_max = "forte (>=10y)", 25, 45
    elif years >= 5:
        tier, b1_max, b2_max = "solido (5-9y)", 32, 38
    elif years >= 1:
        tier, b1_max, b2_max = "nascente (<3-5y)", 55, 15
    elif buyback:
        tier, b1_max, b2_max = "no-div con buyback", 45, 25
    else:
        tier, b1_max, b2_max = "nessuna remunerazione", 70, 0
    # B1 crescita attesa: forward [S] = estrapolazione storica -> cap 50% (DIP F)
    growth_est = m.get("C6", {}).get("value")
    fwd_tag = "S"
    b1 = None
    if growth_est is not None:
        f = step_up(growth_est, [(15, 1.0), (10, .8), (5, .6), (0, .35)])
        ni_cagr = m.get("C6", {}).get("ni_cagr")
        if ni_cagr is not None and growth_est - ni_cagr > 5 and ni_cagr <= 1:
            f = min(f, 0.5)
        b1 = b1_max * f
    # B2 remunerazione
    b2 = None
    if b2_max > 0:
        payout = m.get("C20", {}).get("value")
        dg = m.get("C21", {}).get("value")
        fcf_payout = m.get("C20", {}).get("fcf_payout")
        conds = [dy >= 2.5, dg is not None and dg >= 5,
                 payout is not None and payout <= 0.75,
                 fcf_payout is not None and fcf_payout <= 0.8]
        frac = [0.25, 0.5, 0.75, 1.0][max(sum(bool(c) for c in conds) - 1, 0)] \
            if any(conds) else 0.25
        if cut:
            frac = min(frac, 0.25)
        b2 = b2_max * frac
    # B3 posizionamento multiplo (15)
    b3 = None
    pe, pe_med = ctx.get("pe"), ctx.get("pe_median_hist")
    if pe and pe_med:
        r = pe / pe_med
        b3 = 15 * (1.0 if r < 0.9 else 0.5 if r <= 1.1 else 0.15)
    # B4 TSR forward (15)
    b4 = None
    if growth_est is not None:
        tsr = growth_est + dy
        b4 = 15 * step_up(tsr, [(12, 1.0), (8, .7), (4, .4), (0, .1)])
    # cap forward [S]: B1+B4 <= 50% del massimo combinato (spec 6-bis F)
    if fwd_tag == "S" and b1 is not None and b4 is not None:
        cap = 0.5 * (b1_max + 15)
        if b1 + b4 > cap:
            scale = cap / (b1 + b4)
            b1 *= scale
            b4 *= scale
            notes.append("B1+B4 da stima storica [S]: cap 50% applicato")
    parts = [(b1, b1_max), (b2, b2_max), (b3, 15), (b4, 15)]
    got = sum(p for p, mx in parts if p is not None)
    tot = sum(mx for p, mx in parts if p is not None and mx > 0)
    if tot == 0:
        return None, notes, tier
    return 100 * got / tot, notes, tier


def compute_iqi(m: dict) -> dict:
    a, na = blocco_a(m)
    b, nb, tier = blocco_b(m)
    iqi = None
    if a is not None and b is not None:
        iqi = 0.40 * a + 0.60 * b
    elif a is not None:
        iqi = a
        na.append("Blocco B non calcolabile: IQI-S = solo Blocco A")
    return {"iqi": round(iqi) if iqi is not None else None,
            "blocco_a": round(a) if a is not None else None,
            "blocco_b": round(b) if b is not None else None,
            "tier_dividendo": tier, "note": na + nb, "forward_tag": "S"}


# ------------------------------------------------------------------- CS-S --
def compute_cs(score: dict, validation: dict, m: dict) -> dict:
    detail = score.get("detail", [])
    total_w = sum(d["weight"] for d in detail) or 1
    wp = sum(d["weight"] for d in detail if d["tag"] == "P") / total_w
    wpv = sum(d["weight"] for d in detail if d["tag"] in ("P", "V")) / total_w
    # A provenienza (quota [P] pesata) - bande spec Sez. 10
    a = 24 if wp >= .8 else 19 if wp >= .6 else 13 if wp >= .4 else 8 if wp >= .2 else 3
    # B completezza (copertura della base + profondita' storico)
    cov = score.get("coverage", 0)
    depth = min(len(_clean(m["ctx"].get("revenue_series", []))), 5) / 5
    b = round(25 * (0.7 * cov + 0.3 * depth))
    # C puntualita' (bozza 1: bilanci annuali yfinance = ultimo FY) -> medio-alto
    c = 18
    # D coerenza cross-validation
    ratio = validation.get("agree_ratio")
    d = 20 if (ratio or 0) >= .75 else 14 if (ratio or 0) >= .5 else 8 if ratio is not None else 6
    cs = a + b + c + d
    comp = {"P": round(wp * 100), "V": round((wpv - wp) * 100),
            "U": round((1 - wpv) * 100)}
    return {"cs": cs, "sub": {"A": a, "B": b, "C": c, "D": d},
            "composizione": comp,
            "lettura": ("Alta" if cs >= 80 else "Media" if cs >= 65 else
                        "Bassa" if cs >= 50 else "GATE DATI")}


# ------------------------------------------------- fair value / MoS ---------
def fair_value(m: dict) -> dict:
    """Media ponderata Graham/DDM/DCF/EPV — indicativa in Regime S."""
    ctx = m["ctx"]
    mkt = config.MARKET_PARAMS[ctx["market"]]
    wacc, graham_m, y10, rf, erp, crp = mkt
    y = max(y10, config.GRAHAM_Y_FLOOR)
    models = {}
    eps0 = ctx.get("eps0")
    growth = m.get("C6", {}).get("value")
    if eps0 and eps0 > 0 and growth is not None:
        g = max(min(growth, 15.0), 0.0)
        models["graham"] = eps0 * (graham_m + 2 * g) * 4.4 / y
    dy = m.get("C19", {}).get("value") or 0
    dps = ctx.get("dps_last")
    ddm_applied = False
    if dps and dy > 0.01:
        beta = ctx.get("beta") or 1.0
        r = rf + beta * erp + crp
        roe = (m.get("C9", {}).get("value") or 0) / 100
        payout = m.get("C20", {}).get("value") or 0.6
        g_sost = max(roe * (1 - payout), 0.0)
        g_hist = max((m.get("C21", {}).get("value") or 0) / 100, 0.0)
        g = min(config.G_PERPETUO_MAX, g_sost if g_sost > 0 else g_hist, g_hist if g_hist > 0 else config.G_PERPETUO_MAX)
        if r - g > 0.01:
            models["ddm"] = dps * (1 + g) / (r - g)
            ddm_applied = True
    fcf = _clean(ctx.get("fcf_series", []))
    shares = ctx.get("shares0")
    net_debt = ctx.get("net_debt") or 0
    if fcf and fcf[0] > 0 and shares:
        g1 = max(min((m.get("C7", {}).get("fcf_cagr") or 5.0) / 100, 0.15), 0.0)
        gt = config.G_TERMINAL
        pv, f = 0.0, fcf[0]
        for yr in range(1, 11):
            gr = g1 if yr <= 5 else g1 + (gt - g1) * (yr - 5) / 5
            f *= (1 + gr)
            pv += f / (1 + wacc) ** yr
        tv = f * (1 + gt) / (wacc - gt) / (1 + wacc) ** 10
        models["dcf"] = max((pv + tv - net_debt), 0) / shares
    ebit0, tax = ctx.get("ebit0"), ctx.get("tax_rate", 0.24)
    if ebit0 and ebit0 > 0 and shares:
        models["epv"] = max(ebit0 * (1 - tax) / wacc - net_debt, 0) / shares
    m["ddm_applied"] = ddm_applied
    if not models:
        return {"fv": None, "models": {}, "ddm_applied": ddm_applied}
    if dy <= 0.001:
        weights = {"graham": .25, "dcf": .50, "epv": .20}  # spec: no-div
    else:
        weights = {"graham": .20, "ddm": .30, "dcf": .35, "epv": .15}
    avail = {k: v for k, v in models.items() if v and v > 0}
    wsum = sum(weights.get(k, 0) for k in avail)
    fv = sum(v * weights.get(k, 0) for k, v in avail.items()) / wsum if wsum else None
    disp = None
    if len(avail) >= 2 and fv:
        disp = statistics.pstdev(avail.values()) / statistics.mean(avail.values())
    return {"fv": fv, "models": {k: round(v, 2) for k, v in avail.items()},
            "dispersion": round(disp, 2) if disp is not None else None,
            "ddm_applied": ddm_applied}


def mos_chain(iqi: int | None, cs: int) -> dict:
    if iqi is None:
        return {"mos": None, "stato": "IQI-S non calcolabile"}
    if iqi < 30:
        return {"mos": None, "stato": "ASTENSIONE (IQI < 30)"}
    base = step_up(iqi, [(90, .15), (80, .20), (70, .25), (60, .30),
                         (50, .35), (40, .45), (30, .55)])
    if cs < 50:
        return {"mos": None, "stato": "GATE DATI (CS < 50): non azionabile"}
    overlay = 0.0 if cs >= 80 else 0.05 if cs >= 65 else 0.10
    mos = min(base + overlay, 0.60)
    return {"mos": mos, "mos_base": base, "overlay": overlay, "stato": "ok"}


def netto_italia(m: dict, klass: str) -> dict | None:
    ctx = m["ctx"]
    dy = m.get("C19", {}).get("value")
    if not dy or dy <= 0:
        return None
    country = ctx.get("country") or ""
    w = config.WHT_COUNTRY.get(country, config.WHT_DEFAULT)
    if country == "United States" and klass in config.WHT_CLASS_US:
        w = config.WHT_CLASS_US[klass]
    if country == "Italy":
        w = 0.0
    netto_home = dy * (1 - w)
    netto_it = netto_home * (1 - config.T_ITALIA)
    return {"lordo": round(dy, 2), "w_home": w,
            "netto_home": round(netto_home, 2), "netto_italia": round(netto_it, 2),
            "drag_totale": round(dy - netto_it, 2)}
