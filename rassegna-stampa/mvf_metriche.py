"""Dai bilanci Yahoo ai livelli di banda MVF v4.5.1.

Qui si legge tutto cio' che serve a `mvf_bande.calcola_voto`: serie a 5 anni,
trend, CAGR, test numerico del moat. Niente valutazione e niente rete: prende
DataFrame gia' scaricati. Ogni dato che manca resta None e la metrica viene
omessa dal voto, mai stimata.
"""

from __future__ import annotations

import math
import statistics
from typing import Optional

import mvf_bande as mb
import mvf_valuation as mvf


# ---------------------------------------------------------------------------
# Lettura dei DataFrame (colonne = esercizi, dal piu' recente)
# ---------------------------------------------------------------------------

def _riga(df, nomi, col: int = 0) -> Optional[float]:
    if df is None or getattr(df, "empty", True):
        return None
    for n in ([nomi] if isinstance(nomi, str) else nomi):
        if n in df.index:
            try:
                v = df.loc[n].iloc[col]
            except Exception:
                continue
            if v is not None and not (isinstance(v, float) and math.isnan(v)):
                return float(v)
    return None


def _serie(df, nomi, n: int = 5) -> list:
    """Valori dal piu' recente; None dove manca il dato."""
    if df is None or getattr(df, "empty", True):
        return []
    out = []
    for i in range(min(n, df.shape[1])):
        out.append(_riga(df, nomi, i))
    return out


def _rapporto(a: list, b: list) -> list:
    out = []
    for i in range(min(len(a), len(b))):
        x, y = a[i], b[i]
        out.append(x / y if x is not None and y not in (None, 0) else None)
    return out


def _delta(serie: list) -> tuple[Optional[float], Optional[float]]:
    """(FY0 - FY piu' vecchio, FY0 - FY-1) su una serie di rapporti."""
    v = [x for x in serie if x is not None]
    if len(v) < 3 or serie[0] is None:
        return None, None
    ultimo = serie[0] - serie[1] if len(serie) > 1 and serie[1] is not None else None
    return serie[0] - v[-1], ultimo


def _livello(nome: str, valore, serie=None):
    """Livello con trend se la serie e' disponibile."""
    if valore is None:
        return None
    d, u = _delta(serie) if serie else (None, None)
    return mb.livello_metrica(nome, valore, d, u)


def _cagr(serie: list) -> Optional[float]:
    return mvf.compute_cagr(serie)[0]


# ---------------------------------------------------------------------------
# Classe di voto
# ---------------------------------------------------------------------------

def classe_di_voto(sector_class: str, industry: str = "") -> str:
    """Classe del motore a bande dal sector_class usato per i pesi di valore."""
    ind = (industry or "").lower()
    if sector_class == "bank":
        return "banca"
    if sector_class == "insurance":
        return "assicurazione"
    if sector_class == "utility" and ("regulated" in ind or "diversified" in ind):
        return "utility"
    if sector_class == "reit":
        return "reit"
    return "common"


# ---------------------------------------------------------------------------
# Test numerico del moat (3-ter)
# ---------------------------------------------------------------------------

def test_moat(roic_serie: list, wacc: Optional[float],
              op_margin: Optional[float], mediana_op_margin: Optional[float],
              roic_incrementale: Optional[float]) -> tuple[bool, dict]:
    """Confermato se >= 3 test su 4 sono veri. Il test (3), quota di mercato,
    non e' ricavabile da Yahoo: i tre restanti devono passare tutti."""
    esiti: dict = {}
    if wacc is not None:
        ok = [r for r in roic_serie if r is not None]
        if len(ok) >= 4:
            esiti["roic_sopra_wacc_4_su_5"] = sum(1 for r in ok if r - wacc > 0) >= 4
    if op_margin is not None:
        rif = mediana_op_margin if mediana_op_margin is not None else 0.12
        esiti["margine_operativo_sopra_mediana"] = op_margin >= rif
    if roic_incrementale is not None and wacc is not None:
        esiti["roic_incrementale_3y"] = roic_incrementale >= wacc + 0.05
    veri = sum(1 for v in esiti.values() if v)
    confermato = veri >= 3 or (len(esiti) == 3 and veri == 3)
    return confermato, esiti


# ---------------------------------------------------------------------------
# Costruzione dei livelli
# ---------------------------------------------------------------------------

def costruisci(classe: str, info: dict, fin, bs, cf, dividends, m: dict,
               wacc: Optional[float], re_: Optional[float], sector: str,
               industry: str, market: str, moat_rating: Optional[str] = None,
               mediana_op_margin: Optional[float] = None,
               ddm_significativo: bool = False,
               multiple_expansion_frac: Optional[float] = None) -> dict:
    """Ritorna {livelli, valori, ctx} per `mb.calcola_voto`.

    `m` e' il dict delle metriche gia' calcolate da compute_metrics
    (IntrinsicMetrics.asdict).
    """
    L: dict = {}
    V: dict = {}
    ctx: dict = {}

    ricavi = _serie(fin, "Total Revenue", 5)
    ni = _serie(fin, "Net Income", 5)
    ta = _serie(bs, "Total Assets", 5)
    eq = _serie(bs, "Stockholders Equity", 5)
    debito = _serie(bs, "Total Debt", 5)
    cfo = _serie(cf, "Operating Cash Flow", 5)
    fcf = _serie(cf, "Free Cash Flow", 5)
    ebt = _serie(fin, "Pretax Income", 5)
    tasse = _serie(fin, "Tax Provision", 5)

    # --- margini con trend ---
    for nome, righe in (("gross_margin", "Gross Profit"),
                        ("operating_margin", "Operating Income"),
                        ("ebitda_margin", "EBITDA"),
                        ("net_margin", "Net Income")):
        s = _rapporto(_serie(fin, righe, 5), ricavi)
        if s and s[0] is not None:
            V[nome] = s[0]
            L[nome] = _livello(nome, s[0], s)
    s = _rapporto(fcf, ricavi)
    if s and s[0] is not None:
        V["fcf_margin"] = s[0]
        L["fcf_margin"] = _livello("fcf_margin", s[0], s)
    s = _rapporto(ebt, ricavi)
    if s and s[0] is not None:
        V["pretax_margin"] = s[0]
        L["pretax_margin"] = _livello("pretax_margin", s[0], s)

    # Fallback da `info` quando Yahoo non ha il conto economico (banche europee)
    if "net_margin" not in V and info.get("profitMargins") is not None:
        V["net_margin"] = info["profitMargins"]
        L["net_margin"] = _livello("net_margin", info["profitMargins"])
    if classe in ("banca", "assicurazione") and "pretax_margin" not in V \
            and info.get("operatingMargins") is not None:
        V["pretax_margin"] = info["operatingMargins"]
        L["pretax_margin"] = _livello("pretax_margin", info["operatingMargins"])

    # --- crescita ---
    cg = _cagr(ricavi)
    if cg is not None:
        V["revenue_growth"] = cg
        L["revenue_growth"] = _livello("revenue_growth", cg)
        V["rental_growth"] = cg
        L["rental_growth"] = _livello("rental_growth", cg)
    eps_s = _serie(fin, "Diluted EPS", 5)
    if not [x for x in eps_s if x is not None]:
        eps_s = _serie(fin, "Basic EPS", 5)
    eps_c = _cagr(eps_s)
    ni_c = _cagr(ni)
    if eps_c is not None:
        V["eps_growth"] = eps_c
        liv = mb.livello_metrica("eps_growth", eps_c)[0]
        # EPS >> utile netto per buyback con utile piatto: max Sufficiente
        if ni_c is not None and ni_c < 0.02 and eps_c > ni_c + 0.03:
            liv = max(liv, 2)
        L["eps_growth"] = liv
    azioni = _serie(bs, ["Ordinary Shares Number", "Share Issued"], 5)
    fcf_ps = _rapporto(fcf, azioni)
    fcf_ps_c = _cagr(fcf_ps)
    if fcf_ps_c is not None and classe not in ("banca", "assicurazione"):
        V["fcf_ps_growth"] = fcf_ps_c
        liv = mb.livello_metrica("fcf_ps_growth", fcf_ps_c)[0]
        agg = _cagr(fcf)
        if agg is not None and agg < 0.02 and fcf_ps_c > agg + 0.03:
            liv = max(liv, 2)
        L["fcf_ps_growth"] = liv

    # --- ritorni sul capitale ---
    nopat_s, ic_s = [], []
    for i in range(min(5, len(ebt))):
        oi = _riga(fin, "Operating Income", i)
        t = tasse[i] if i < len(tasse) else None
        e = ebt[i] if i < len(ebt) else None
        aliq = (t / e) if (t is not None and e and e > 0) else None
        nopat_s.append(oi * (1 - aliq) if (oi is not None and aliq is not None) else None)
        eqi = eq[i] if i < len(eq) else None
        di = debito[i] if i < len(debito) else None
        ic_s.append((eqi + (di or 0)) if eqi is not None else None)
    roic_s = _rapporto(nopat_s, ic_s)
    roic = m.get("roic")
    ro_ref = wacc
    if classe in ("banca", "assicurazione"):
        # ROTE al posto del ROIC (9A): utile / patrimonio tangibile
        tang = _riga(bs, "Tangible Book Value")
        ni0 = ni[0] if ni else None
        if ni0 is None and info.get("netIncomeToCommon"):
            ni0 = info["netIncomeToCommon"]
        rote = ni0 / tang if (ni0 is not None and tang and tang > 0) else None
        if rote is None and m.get("roe") is not None:
            rote = m["roe"]
        roic = rote
        ro_ref = re_
        ctx["rote_da_roe"] = rote is not None and not (tang and tang > 0)
    if roic is not None and ro_ref is not None:
        V["roic_spread"] = roic - ro_ref
        d, u = _delta([r - ro_ref if r is not None else None for r in roic_s])
        L["roic_spread"] = mb.livello_metrica("roic_spread", roic - ro_ref, d, u)
    roe = m.get("roe")
    if roe is None and info.get("returnOnEquity") is not None:
        roe = info["returnOnEquity"]
    if roe is not None and re_ is not None:
        V["roe_spread"] = roe - re_
        liv, tr = mb.livello_metrica("roe_spread", roe - re_)
        # guardia: patrimonio < 15% degli attivi (ROE gonfiato dalla leva)
        if classe == "common" and eq and ta and eq[0] and ta[0] and eq[0] / ta[0] < 0.15:
            liv = max(liv, 2)
        L["roe_spread"] = (liv, tr)
    roa = m.get("roa")
    if roa is None and info.get("returnOnAssets") is not None:
        roa = info["returnOnAssets"]
    if roa is not None:
        nome = "roa_finanziaria" if classe in ("banca", "assicurazione") else "roa"
        V["roa"] = roa
        L["roa"] = mb.livello_metrica(nome, roa,
                                      *_delta(_rapporto(ni, ta)))

    # --- leva ---
    ebitda0 = _riga(fin, "EBITDA")
    if ebitda0 is None:
        oi0, da0 = _riga(fin, "Operating Income"), _riga(cf, "Depreciation And Amortization")
        ebitda0 = (oi0 + da0) if (oi0 is not None and da0 is not None) else None
    cassa = _riga(bs, ["Cash Cash Equivalents And Short Term Investments",
                       "Cash And Cash Equivalents"])
    nd = (debito[0] - (cassa or 0)) if debito and debito[0] is not None else None
    nd_eb = None
    if nd is not None and ebitda0 is not None:
        # cassa netta = Eccellente; EBITDA <= 0 con debito netto = Critico
        nd_eb = 0.0 if nd <= 0 else (99.0 if ebitda0 <= 0 else nd / ebitda0)
    chiave_nd = {"utility": "nd_ebitda_utility", "reit": "nd_ebitda_reit"}.get(
        classe, "nd_ebitda")
    if nd_eb is not None and classe not in ("banca", "assicurazione"):
        V[chiave_nd] = nd_eb
        L[chiave_nd] = mb.livello_metrica(chiave_nd, nd_eb)
        ctx["nd_ebitda"] = nd_eb
    da_s = _rapporto(debito, ta)
    if da_s and da_s[0] is not None and classe not in ("banca", "assicurazione"):
        V["debt_assets"] = da_s[0]
        L["debt_assets"] = _livello("debt_assets", da_s[0], da_s)

    # --- Altman (Z originale o Z'' per servizi/tech/EM) ---
    z, modello = m.get("altman_z"), "Z"
    if sector in ("Technology", "Communication Services", "Consumer Cyclical",
                  "Real Estate"):
        z2 = _altman_z2(bs, fin)
        if z2 is not None:
            z, modello = z2, "Z2"
    ctx["altman_z"], ctx["altman_modello"] = z, modello
    if z is not None and classe == "common":
        V["altman"] = z
        L["altman"] = mb.livello_altman(z, modello)

    # --- efficienza del capitale ---
    if m.get("sbc_revenue") is not None:
        V["sbc_revenue"] = m["sbc_revenue"]
        L["sbc_revenue"] = mb.livello_metrica("sbc_revenue", m["sbc_revenue"])
    if m.get("capex_revenue") is not None:
        V["capex_revenue"] = m["capex_revenue"]
        L["capex_revenue"] = mb.livello_metrica("capex_revenue", m["capex_revenue"])
    if m.get("capex_da") is not None:
        V["capex_da"] = m["capex_da"]
        L["capex_da"] = mb.livello_capex_da(m["capex_da"])
        if classe == "utility":
            d = m["capex_da"]
            nd_v = ctx.get("nd_ebitda")
            if 1.5 <= d <= 2.5 and (nd_v is None or nd_v <= 5.5):
                lv = 0
            elif 1.2 <= d < 1.5 or 2.5 < d <= 3.0:
                lv = 1
            elif 1.0 <= d < 1.2 or 3.0 < d <= 3.5:
                lv = 2
            elif d < 1.0:
                lv = 3
            else:
                lv = 4 if (nd_v is not None and nd_v > 6) else 3
            V["capex_vs_dep"] = d
            L["capex_vs_dep"] = lv
    rd = m.get("rd_revenue")
    ctx["rd_materiale"] = rd is not None and rd >= 0.005
    if ctx["rd_materiale"]:
        V["rd_revenue"] = rd
        L["rd_revenue"] = mb.livello_rd(rd, pharma=(sector == "Healthcare"))

    # --- riacquisto netto: riduzione delle azioni (CAGR 3y) ---
    az = [x for x in azioni[:4] if x is not None]
    if len(az) >= 4 and az[-1] > 0 and az[0] > 0:
        riduzione = 1 - (az[0] / az[-1]) ** (1 / 3)
        V["buyback"] = riduzione
        L["buyback"] = mb.livello_metrica("buyback", riduzione)[0]

    # --- dividendi ---
    dy = m.get("dividend_yield")
    ctx["ha_dividendo"] = bool(dy and dy > 0)
    pay_eps = info.get("payoutRatio")
    div_pagati = _riga(cf, ["Cash Dividends Paid", "Common Stock Dividend Paid"])
    pay_fcf = None
    if div_pagati is not None and fcf and fcf[0] and fcf[0] > 0:
        pay_fcf = abs(div_pagati) / fcf[0]
    candidati = [p for p in (pay_eps, pay_fcf) if p is not None]
    payout = max(candidati) if candidati else None
    ffo_payout = None
    if dy:
        chiave_dy = "dividend_yield_reit" if classe == "reit" else "dividend_yield"
        liv = mb.livello_metrica(chiave_dy, dy)[0]
        if dy > 0.07 and payout is not None and payout > 1.0:
            liv = max(liv, 3)          # yield-trap
        V["dividend_yield"] = dy
        L["dividend_yield"] = liv
    if payout is not None and classe != "reit":
        V["payout"] = payout
        L["payout"] = mb.livello_payout(payout, regolato=(classe == "utility"))
    dg = m.get("dividend_growth_5y")
    if dg is not None:
        V["dividend_growth"] = dg
        L["dividend_growth"] = mb.livello_metrica("dividend_growth", dg)[0]

    # --- tax ---
    aliq_s = [(t / e) if (t is not None and e and e > 0) else None
              for t, e in zip(tasse, ebt)]
    if classe not in ("reit",):
        L["tax"] = mb.livello_tax(aliq_s, m.get("tax_rate"))
        V["tax"] = m.get("tax_rate")

    # --- earnings quality (non per intermediari finanziari) ---
    if classe in ("common", "utility"):
        ccr_s = _rapporto(cfo[:3], ni[:3])
        ccr_v = [x for x in ccr_s if x is not None and x > -10]
        ccr = statistics.mean(ccr_v) if len(ccr_v) >= 2 else m.get("cash_conversion_ratio")
        V["earnings_quality"] = ccr
        L["earnings_quality"] = mb.livello_earnings_quality(ccr, m.get("accruals_ratio"))

    # --- classi dedicate ---
    if classe == "banca":
        costi = _riga(fin, ["Non Interest Expense", "Operating Expense", "Total Expenses"])
        ric0 = ricavi[0] if ricavi else None
        if costi is not None and ric0 and ric0 > 0:
            ci = abs(costi) / ric0
            V["cost_income"] = ci
            L["cost_income"] = mb.livello_metrica("cost_income", ci)[0]
        prov = _riga(fin, ["Provision For Loan Lossess", "Provision For Credit Losses",
                           "Provision For Loan Losses"])
        prestiti = _riga(bs, ["Net Loan", "Gross Loan", "Loans"])
        if prov is not None and prestiti and prestiti > 0:
            cr = abs(prov) / prestiti
            V["cost_of_risk"] = cr
            L["cost_of_risk"] = mb.livello_metrica("cost_of_risk", cr)[0]

    if classe == "reit":
        da_cf = _serie(cf, ["Depreciation And Amortization",
                            "Depreciation Amortization Depletion"], 5)
        var_cn = _serie(cf, "Change In Working Capital", 5)
        ffo = []
        for i in range(min(len(cfo), 5)):
            c0 = cfo[i]
            ffo.append((c0 - (var_cn[i] if i < len(var_cn) and var_cn[i] is not None else 0))
                       if c0 is not None else None)
        s = _rapporto(ffo, ricavi)
        if s and s[0] is not None:
            V["ffo_margin"] = s[0]
            L["ffo_margin"] = mb.livello_metrica("ffo_margin", s[0])[0]
        if div_pagati is not None and ffo and ffo[0] and ffo[0] > 0:
            ffo_payout = abs(div_pagati) / ffo[0]
            V["ffo_payout"] = ffo_payout
            L["ffo_payout"] = mb.livello_metrica("ffo_payout", ffo_payout)[0]
            if dy and dy > 0.09 and ffo_payout > 1.0:
                L["dividend_yield"] = max(L.get("dividend_yield", 0) or 0, 3)
        ffo_ps = _rapporto(ffo, azioni)
        g = _cagr(ffo_ps)
        if g is not None:
            V["ffo_ps_growth"] = g
            liv = mb.livello_metrica("ffo_ps_growth", g)[0]
            gagg = _cagr(ffo)
            if gagg is not None and gagg > g + 0.03 and liv > 3:
                liv = 4
            L["ffo_ps_growth"] = liv
        interessi = _riga(fin, ["Interest Expense", "Interest Expense Non Operating"])
        if ebitda0 and interessi:
            fcc = ebitda0 / abs(interessi)
            V["fixed_charge_cov"] = fcc
            L["fixed_charge_cov"] = mb.livello_metrica("fixed_charge_cov", fcc)[0]

    # --- moat ---
    roic_ok = None
    if roic_s and wacc is not None:
        v = [r for r in roic_s if r is not None]
        roic_ok = (sum(1 for r in v if r - wacc > 0) >= max(1, len(v) - 1)) if len(v) >= 3 else None
    incr = None
    if len(ic_s) >= 4 and len(nopat_s) >= 4 and None not in (nopat_s[0], nopat_s[3], ic_s[0], ic_s[3]):
        dic = ic_s[0] - ic_s[3]
        if dic and dic > 0:
            incr = (nopat_s[0] - nopat_s[3]) / dic
    op_m = V.get("operating_margin", V.get("pretax_margin"))
    conf, esiti = test_moat(roic_s, wacc if classe not in ("banca", "assicurazione") else re_,
                            op_m, mediana_op_margin, incr)
    liv_moat, tag = mb.livello_moat(moat_rating, conf, roic_ok)
    if liv_moat is not None:
        L["moat"] = liv_moat
    ctx["moat"] = {"rating": moat_rating, "test_confermato": conf, "test": esiti, "tag": tag}

    frazioni = {}
    if multiple_expansion_frac is not None:
        frazioni["multiple_expansion"] = _ladder(multiple_expansion_frac)
    return {"livelli": L, "valori": V, "ctx": ctx, "frazioni": frazioni}


def _ladder(frac: float) -> float:
    """La rubrica del Delta P/E restituisce frazioni 0/0.25/0.5/1: le porta sui
    cinque gradini della scala unica."""
    gradini = [0.0, 0.25, 0.5, 0.75, 1.0]
    return min(gradini, key=lambda g: abs(g - frac))


def _altman_z2(bs, fin) -> Optional[float]:
    """Z'' = 6,56 X1 + 3,26 X2 + 6,72 X3 + 1,05 X4 (servizi, tech, EM)."""
    ta = _riga(bs, "Total Assets")
    tl = _riga(bs, "Total Liabilities Net Minority Interest")
    if not ta or ta <= 0 or not tl or tl <= 0:
        return None
    wc = (_riga(bs, "Current Assets") or 0) - (_riga(bs, "Current Liabilities") or 0)
    re_ = _riga(bs, "Retained Earnings") or 0
    ebit = _riga(fin, ["EBIT", "Operating Income"])
    eq = _riga(bs, "Stockholders Equity")
    if ebit is None or eq is None:
        return None
    return 6.56 * wc / ta + 3.26 * re_ / ta + 6.72 * ebit / ta + 1.05 * eq / tl
