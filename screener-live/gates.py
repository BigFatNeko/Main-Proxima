"""Gate G1-G6 e red flag in batch (calibrazione §8, spec Sez. 8 / 8-bis).

I gate ESCLUDONO strutturalmente (NO-BUY a prescindere dal prezzo).
I red flag SEGNALANO senza bloccare. Due liste separate (vincolo V5).
G6 non e' attivabile in batch (deviazione dichiarata): i suoi segnali
diventano red flag.
"""
from __future__ import annotations

import config


def _clean(serie):
    return [v for v in serie if v is not None]


def evaluate_gates(m: dict) -> list[dict]:
    ctx = m["ctx"]
    gates = []
    ind_l = (ctx.get("industry", "") + " " + ctx.get("sector", "")).lower()
    leveraged = any(k in ind_l for k in config.LEVERAGED_BY_DESIGN)

    # G1 - distruzione di cassa strutturale: FCF < 0 in tutti gli ultimi FY
    fcf = _clean(ctx.get("fcf_series", []))
    if len(fcf) >= 4 and all(v < 0 for v in fcf):
        gm = m.get("C1", {}).get("value")
        rev_cagr = ctx.get("rev_growth_cagr")
        saas_exempt = (gm is not None and gm > 70
                       and rev_cagr is not None and rev_cagr > 20)
        if not saas_exempt:
            gates.append({"id": "G1", "desc": "FCF negativo in tutti gli ultimi "
                          f"{len(fcf)} FY (distruzione di cassa strutturale)"})

    # G2 - distruzione di valore: ROIC - WACC < 0 per >= 4 anni.
    # Per REIT/BDC/MLP la spec usa l'accretion spread (non ancora reperibile in
    # bozza 1): il ROIC contabile e' privo di senso -> G2 non valutabile, skip.
    roic = _clean(ctx.get("roic_series", []))
    wacc_pct = ctx.get("wacc", 0.09) * 100
    if not leveraged and len(roic) >= 4 and all(r < wacc_pct for r in roic[:4]):
        gates.append({"id": "G2", "desc": "ROIC sotto il WACC per >=4 anni "
                      f"(ROIC ult. {roic[0]:.1f}% vs WACC {wacc_pct:.1f}%)"})

    # G3 - leva fuori scala non servita (esenti i leveraged-by-design)
    nde = _clean(ctx.get("nd_ebitda_series", []))
    if not leveraged and len(nde) >= 2 and nde[0] is not None:
        rising = nde[0] > nde[-1]
        cov = None
        if ctx.get("ebit0") and ctx.get("interest_expense"):
            cov = ctx["ebit0"] / ctx["interest_expense"]
        if nde[0] > 6 and rising and cov is not None and cov < 1.5:
            gates.append({"id": "G3", "desc": f"Net Debt/EBITDA {nde[0]:.1f}x in "
                          f"aumento con copertura interessi {cov:.1f}x"})

    # G4 - trasferimento di valore: diluizione > 5%/anno E SBC/Rev > 8%
    dil = m.get("C22", {}).get("value")  # positivo = riduzione
    sbc = m.get("C14", {}).get("value")
    if dil is not None and sbc is not None and dil < -5 and sbc > 8:
        gates.append({"id": "G4", "desc": f"Diluizione {-dil:.1f}%/anno con "
                      f"SBC {sbc:.1f}% dei ricavi"})

    # G5 - insolvenza tecnica: Z < 1.23 + secondo segnale
    z = m.get("C13", {}).get("value")
    if z is not None and z < 1.23 and not ctx.get("altman_exempt"):
        de = ctx.get("de")
        fcf3 = fcf[:3]
        second = (de is not None and de > 3) or \
                 (len(fcf3) >= 2 and sum(1 for v in fcf3 if v < 0) >= 2)
        cov = None
        if ctx.get("ebit0") and ctx.get("interest_expense"):
            cov = ctx["ebit0"] / ctx["interest_expense"]
        second = second or (cov is not None and cov < 1.5)
        if second:
            gates.append({"id": "G5", "desc": f"Altman-Z {z:.2f} confermato da "
                          "un secondo segnale di stress"})
    return gates


def evaluate_red_flags(m: dict) -> dict[str, list[str]]:
    ctx = m["ctx"]
    critical, warning = [], []
    fcf = _clean(ctx.get("fcf_series", []))
    nm_serie = _clean(m.get("C4", {}).get("series", []))
    z = m.get("C13", {}).get("value")
    de = ctx.get("de")

    if z is not None and z < 1.23 and not ctx.get("altman_exempt"):
        critical.append(f"Altman-Z {z:.2f} in zona pericolo")
    if len(fcf) >= 3 and all(v < 0 for v in fcf[:3]):
        critical.append("FCF negativo negli ultimi 3 esercizi")
    if de is not None and de > 3:
        critical.append(f"Debt/Equity {de:.1f} oltre 3")
    if len(nm_serie) >= 3 and sum(1 for v in nm_serie[:3] if v < 0) >= 2:
        critical.append("Margine netto negativo in 2+ degli ultimi 3 esercizi")
    roic = _clean(ctx.get("roic_series", []))
    wacc_pct = ctx.get("wacc", 0.09) * 100
    ind_rf = (ctx.get("industry", "") + " " + ctx.get("sector", "")).lower()
    lev_rf = any(k in ind_rf for k in config.LEVERAGED_BY_DESIGN)
    if not lev_rf and len(roic) >= 2 and all(r < wacc_pct for r in roic[:2]):
        critical.append("ROIC sotto il WACC da 2+ anni (distruzione di valore)")
    gw, eq = ctx.get("goodwill"), ctx.get("equity0")
    if gw and eq and eq > 0 and gw / eq > 0.5:
        critical.append(f"Goodwill al {gw / eq * 100:.0f}% del patrimonio netto")
    sbc = m.get("C14", {}).get("value")
    if sbc is not None and sbc > 8:
        critical.append(f"SBC al {sbc:.1f}% dei ricavi")

    if z is not None and 1.23 <= z <= 1.81 and not ctx.get("altman_exempt"):
        warning.append(f"Altman-Z {z:.2f} in zona grigia")
    if len(fcf) >= 3 and sum(1 for v in fcf[:3] if v < 0) == 1:
        warning.append("FCF negativo in 1 degli ultimi 3 esercizi")
    payout = m.get("C20", {}).get("value")
    if payout is not None and payout > 1.0:
        warning.append(f"Payout {payout * 100:.0f}% oltre il 100%")
    rev = _clean(ctx.get("revenue_series", []))
    if len(rev) >= 3 and rev[0] < rev[1] < rev[2]:
        warning.append("Ricavi in calo da 2 esercizi consecutivi")
    acc = m.get("C27", {}).get("accruals")
    ccr = m.get("C27", {}).get("value")
    if acc is not None and acc > 0.10:
        warning.append(f"Accruals {acc:.2f} oltre 0,10 (qualita' utili)")
    if ccr is not None and ccr < 0.5:
        warning.append(f"CCR {ccr:.2f} sotto 0,5 (poca conversione in cassa)")
    dil = m.get("C22", {}).get("value")
    if dil is not None and dil < -3:
        warning.append(f"Diluizione {-dil:.1f}%/anno oltre il 3%")
    tax = m.get("C25", {}).get("value")
    tax_vol = m.get("C25", {}).get("volatility") or 0
    if tax is not None and tax < 10 and tax_vol > 3:
        warning.append("Aliquota fiscale sotto il 10% e volatile")
    # divergenza EPS vs FCF/share (qualita' utili, spec Sez. 3C)
    eps_g = m.get("C6", {}).get("value")
    fcfps_g = m.get("C7", {}).get("value")
    if eps_g is not None and fcfps_g is not None and eps_g > 5 and fcfps_g < 0:
        warning.append("EPS in crescita ma FCF/azione in calo (verifica accruals)")
    # segnali G6 (capital allocation) declassati a warning in batch
    if dil is not None and dil < -5:
        warning.append("Diluizione persistente: possibile capital allocation "
                       "distruttiva (G6 valutabile solo in Regime A)")
    return {"critical": critical, "warning": warning}
