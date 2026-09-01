"""Calcolo delle metriche grezze dal raw yfinance/EDGAR.

Ogni metrica esce come dict:
  {"value": float|None, "series": [piu' recente..piu' vecchio], "tag": P|V|U}
Mai inventare: se il dato non c'e', value=None e la metrica verra' omessa
con ri-basatura (calibrazione §1).
"""
from __future__ import annotations

import statistics
from datetime import date, datetime

import config


def _ratio_series(num: list, den: list, pct: bool = True) -> list:
    out = []
    for i in range(min(len(num), len(den))):
        n, d = num[i], den[i]
        if n is None or d in (None, 0):
            out.append(None)
        else:
            out.append((n / d) * (100 if pct else 1))
    return out


def _cagr(new: float | None, old: float | None, years: int) -> float | None:
    if new is None or old is None or years <= 0:
        return None
    if old <= 0:
        if new > 0:
            return None  # da negativo a positivo: CAGR non definito
        return None
    if new <= 0:
        return -100.0
    return ((new / old) ** (1 / years) - 1) * 100


def _series_cagr(serie: list, min_years: int = 3) -> tuple[float | None, int]:
    """CAGR sulla serie annuale (recente per prima). Mai sotto 3 anni (spec)."""
    vals = [v for v in serie if v is not None]
    if len(vals) < min_years + 1:
        vals = [v for v in serie if v is not None]
        if len(vals) < 4:  # 3 intervalli minimi
            return None, 0
    n = min(len(vals) - 1, 5)
    return _cagr(vals[0], vals[n], n), n


def _split_factors(shares: list) -> list[float]:
    """Fattori cumulativi per normalizzare la serie azioni (piu' recente per
    prima) su un'unica base, correggendo gli stock split (T20).

    EDGAR non rettifica il numero di azioni per gli split; yfinance si'. Uno
    split appare come salto improvviso (es. 3:1 -> +200% in un anno), che i
    cambi organici (buyback/emissioni) non producono mai. Rileva il salto e
    riporta gli anni precedenti alla base corrente. Su serie gia' rettificate
    (yfinance) nessun salto -> fattori tutti 1 (no-op).
    """
    n = len(shares)
    factors = [1.0] * n
    if n < 2:
        return factors
    common = [2.0, 3.0, 4.0, 1.5, 5.0, 6.0, 10.0]
    cum = 1.0
    for i in range(1, n):                 # da recente (0) verso vecchio
        newer, older = shares[i - 1], shares[i]
        if newer and older and older > 0:
            r = newer / older             # >1 split diretto, <1 reverse split
            f = None
            if r >= 1.4:
                cand = min(common, key=lambda c: abs(c - r))
                if abs(cand - r) / cand <= 0.08:
                    f = cand
            elif r <= 0.71:
                cand = min(common, key=lambda c: abs(c - 1 / r))
                if abs(cand - 1 / r) / cand <= 0.08:
                    f = 1 / cand
            if f:
                cum *= f
        factors[i] = cum
    return factors


def _annual_dividends(div_series: dict[str, float]) -> dict[int, float]:
    out: dict[int, float] = {}
    for d, v in div_series.items():
        y = int(d[:4])
        out[y] = out.get(y, 0.0) + v
    return out


def detect_class(info: dict, overrides: dict) -> str:
    tkr = (info.get("symbol") or "").upper()
    if tkr in overrides:
        return overrides[tkr]
    ind = (info.get("industry") or "").lower()
    sec = (info.get("sector") or "").lower()
    name = (info.get("shortName") or info.get("longName") or "").lower()
    if "reit" in ind or "reit" in sec or "real estate investment trust" in ind:
        return "reit"
    if "midstream" in ind and (" lp" in name or "partners" in name):
        return "mlp"
    if "asset management" in ind and ("bdc" in name or "capital" in name and " lp" not in name):
        # euristica debole: le BDC vere si fissano in class_overrides.json
        pass
    return "common"


def detect_market(ticker: str, info: dict) -> str:
    for suf, mkt in config.SUFFIX_MARKET.items():
        if ticker.upper().endswith(suf):
            return mkt
    country = info.get("country") or ""
    for c, m in (("United States", "US"), ("Italy", "IT"), ("Japan", "JP"),
                 ("United Kingdom", "UK"), ("Switzerland", "CH"),
                 ("South Korea", "KR"), ("Taiwan", "TW"), ("China", "CN"),
                 ("Canada", "CA"), ("Australia", "AU"), ("Spain", "ES")):
        if country == c:
            return m
    return "US" if country == "" else "OTHER"


def compute_metrics(raw: dict, validation: dict) -> dict:
    """Tutte le metriche del motore common + contesto. Vedi calibrazione §2."""
    info = raw["info"]
    m: dict = {"ctx": {}}
    ctx = m["ctx"]
    ctx["ticker"] = raw["ticker"]
    ctx["name"] = info.get("shortName") or info.get("longName") or raw["ticker"]
    ctx["sector"] = info.get("sector") or ""
    ctx["industry"] = info.get("industry") or ""
    ctx["country"] = info.get("country") or ""
    ctx["currency"] = info.get("currency") or ""
    ctx["market"] = detect_market(raw["ticker"], info)
    ctx["price"] = info.get("currentPrice") or info.get("regularMarketPrice")
    ctx["beta"] = info.get("beta")
    ctx["market_cap"] = info.get("marketCap")
    ctx["pe"] = info.get("trailingPE")
    ctx["fy_end"] = None

    tags = validation.get("tags", {})
    trust = validation.get("statement_trust", "U")

    def tag_for(*facts: str) -> str:
        """Tag DIP della metrica = il peggiore dei fatti di input."""
        rank = {"P": 0, "V": 1, "U": 2}
        worst = "P" if facts else trust
        for f in facts:
            t = tags.get(f, trust)
            if rank[t] > rank[worst]:
                worst = t
        return worst

    rev = raw["revenue"]
    ni = raw["net_income"]
    cfo = raw["cfo"]
    capex = [abs(v) if v is not None else None for v in raw["capex"]]
    fcf = [(c - x) if (c is not None and x is not None) else None
           for c, x in zip(cfo, capex)]
    if not any(v is not None for v in fcf):
        fcf = raw["fcf_yf"]
    ctx["fcf_series"] = fcf
    ctx["revenue_series"] = rev

    def put(mid, value, serie=None, tag="U", extra=None):
        m[mid] = {"value": value, "series": serie or [], "tag": tag}
        if extra:
            m[mid].update(extra)

    # --- margini ---------------------------------------------------------
    gm = _ratio_series(raw["gross_profit"], rev)
    put("C1", gm[0] if gm else None, gm, tag_for("revenue"))
    em = _ratio_series(raw["ebitda"], rev)
    put("C2", em[0] if em else None, em, tag_for("revenue"))
    om = _ratio_series(raw["operating_income"], rev)
    put("C3", om[0] if om else None, om, tag_for("revenue"))
    nm = _ratio_series(ni, rev)
    put("C4", nm[0] if nm else None, nm, tag_for("revenue", "net_income"))
    fm = _ratio_series(fcf, rev)
    put("C5", fm[0] if fm else None, fm, tag_for("revenue", "cfo", "capex"))

    # --- crescita per azione (C6, C7) ------------------------------------
    # Normalizza azioni ed EPS per gli stock split (T20): azioni su base
    # corrente, EPS scala all'inverso. Cosi' i per-azione sono coerenti.
    split_f = _split_factors(raw["shares"])
    ctx["split_adjusted"] = any(abs(f - 1.0) > 0.01 for f in split_f)
    shares = [(s * f) if s is not None else None
              for s, f in zip(raw["shares"], split_f)]
    eps = [(e / f) if e is not None else None
           for e, f in zip(raw["diluted_eps"], split_f)]
    eps_cagr, _ = _series_cagr(eps)
    ni_cagr, _ = _series_cagr(ni)
    put("C6", eps_cagr, eps, tag_for("net_income"),
        {"ni_cagr": ni_cagr})
    fcfps = [(f / s) if (f is not None and s not in (None, 0)) else None
             for f, s in zip(fcf, shares)]
    fcfps_cagr, _ = _series_cagr(fcfps)
    fcf_cagr, _ = _series_cagr(fcf)
    put("C7", fcfps_cagr, fcfps, tag_for("cfo", "capex"),
        {"fcf_cagr": fcf_cagr})

    # --- redditivita' -----------------------------------------------------
    wacc = config.MARKET_PARAMS[ctx["market"]][0]
    ctx["wacc"] = wacc
    tax_rates = _ratio_series(raw["tax_provision"], raw["pretax_income"], pct=False)
    tax = tax_rates[0] if tax_rates and tax_rates[0] is not None else 0.24
    tax = min(max(tax, 0.0), 0.45)
    ctx["tax_rate"] = tax
    roic_series = []
    for i in range(len(raw["ebit"])):
        ebit_i = raw["ebit"][i] if i < len(raw["ebit"]) else None
        debt_i = raw["total_debt"][i] if i < len(raw["total_debt"]) else None
        eq_i = raw["equity"][i] if i < len(raw["equity"]) else None
        cash_i = raw["cash"][i] if i < len(raw["cash"]) else None
        if None in (ebit_i, eq_i) or (debt_i is None):
            roic_series.append(None)
            continue
        invested = (debt_i or 0) + eq_i - (cash_i or 0)
        roic_series.append((ebit_i * (1 - tax) / invested) * 100 if invested > 0 else None)
    ctx["roic_series"] = roic_series
    put("C8", roic_series[0] if roic_series else None, roic_series,
        tag_for("equity"), {"spread": (roic_series[0] - wacc * 100)
                            if roic_series and roic_series[0] is not None else None})
    roe = _ratio_series(ni, raw["equity"])
    put("C9", roe[0] if roe else None, roe, tag_for("net_income", "equity"))
    roa = _ratio_series(ni, raw["total_assets"])
    put("C10", roa[0] if roa else None, roa, tag_for("net_income", "total_assets"))

    # --- leva -------------------------------------------------------------
    de = _ratio_series(raw["total_debt"], raw["equity"], pct=False)
    put("C11", de[0] if de else None, de, tag_for("equity"))
    da = _ratio_series(raw["total_debt"], raw["total_assets"], pct=False)
    put("C12", da[0] if da else None, da, tag_for("total_assets"))
    ctx["de"] = de[0] if de else None

    # --- Altman-Z ---------------------------------------------------------
    z = None
    try:
        ta = raw["total_assets"][0]
        wc = raw["working_capital"][0] if raw["working_capital"] else None
        if wc is None and raw["current_assets"] and raw["current_liab"]:
            wc = raw["current_assets"][0] - raw["current_liab"][0]
        re_ = raw["retained"][0] if raw["retained"] else None
        ebit0 = raw["ebit"][0]
        tl = raw["total_liab"][0] if raw["total_liab"] else None
        mc = ctx["market_cap"]
        rev0 = rev[0]
        if None not in (ta, wc, re_, ebit0, tl, mc, rev0) and ta > 0 and tl > 0:
            z = (1.2 * wc / ta + 1.4 * re_ / ta + 3.3 * ebit0 / ta
                 + 0.6 * mc / tl + 1.0 * rev0 / ta)
    except (IndexError, TypeError):
        pass
    ind_l = (ctx["industry"] + " " + ctx["sector"]).lower()
    ctx["altman_exempt"] = any(k in ind_l for k in config.ALTMAN_EXEMPT_KEYWORDS)
    put("C13", z, [], tag_for("total_assets"))

    # --- disciplina -------------------------------------------------------
    sbc = _ratio_series(raw["sbc"], rev)
    put("C14", sbc[0] if sbc else None, sbc, tag_for("revenue"))
    cxr = _ratio_series(capex, rev)
    put("C15", cxr[0] if cxr else None, cxr, tag_for("capex", "revenue"))
    da_series = raw["da_cf"] or raw["da_income"]
    cxda = _ratio_series(capex, da_series, pct=False)
    put("C16", cxda[0] if cxda else None, cxda, tag_for("capex"))
    rdr = _ratio_series(raw["rd"], rev)
    rd_val = rdr[0] if rdr else None
    put("C17", rd_val, rdr, tag_for("revenue"))
    put("C18", None, [], "U")  # Insider: Form 4 non ancora cablato (T18)

    # --- dividendi --------------------------------------------------------
    ann_div = _annual_dividends(raw["dividends_series"])
    this_year = date.today().year
    years = sorted(y for y in ann_div if y < this_year)
    dps_last = ann_div.get(this_year - 1)
    price = ctx["price"]
    dy = (dps_last / price * 100) if (dps_last and price) else None
    if dy is None and not ann_div:
        dy = 0.0  # nessun dividendo in storia: yield zero certo
    put("C19", dy, [], "V" if raw["dividends_series"] else "P")
    payout = None
    if raw["dividends_paid"] and ni and raw["dividends_paid"][0] is not None \
            and ni[0] not in (None, 0):
        payout = abs(raw["dividends_paid"][0]) / ni[0]
        payout = payout if ni[0] > 0 else None
    fcf_payout = None
    if raw["dividends_paid"] and fcf and raw["dividends_paid"][0] is not None \
            and fcf[0] not in (None, 0) and fcf[0] > 0:
        fcf_payout = abs(raw["dividends_paid"][0]) / fcf[0]
    put("C20", payout, [], tag_for("net_income"), {"fcf_payout": fcf_payout})
    dg = None
    cut_in_5y = None
    increases_of5 = None
    if len(years) >= 6:
        dg = _cagr(ann_div[years[-1]], ann_div[years[-6]], 5)
        last6 = [ann_div[y] for y in years[-6:]]
        cut_in_5y = any(last6[i + 1] < last6[i] * 0.98 for i in range(5))
        increases_of5 = sum(1 for i in range(5) if last6[i + 1] > last6[i] * 1.001)
    put("C21", dg, [], "V" if ann_div else "U",
        {"cut_in_5y": cut_in_5y, "increases_of5": increases_of5})
    # storia lunga per Difensivo/badge
    paid_years = 0
    consec_increases = 0
    if years:
        yrs = years[::-1]  # dal piu' recente
        for i, y in enumerate(yrs):
            if ann_div.get(y, 0) > 0 and (i == 0 or yrs[i - 1] - y == 1):
                paid_years += 1
            else:
                break
        seq = years
        for i in range(len(seq) - 1, 0, -1):
            if ann_div[seq[i]] > ann_div[seq[i - 1]] * 1.001:
                consec_increases += 1
            else:
                break
    ctx["div_years_paid"] = paid_years
    ctx["div_consec_increases"] = consec_increases
    ctx["div_payment_months"] = sorted({int(d[5:7]) for d in raw["dividends_series"]
                                        if d[:4] == str(this_year - 1)})

    # --- buyback / prezzo -------------------------------------------------
    sh_cagr, _ = _series_cagr(shares)
    put("C22", -sh_cagr if sh_cagr is not None else None, shares,
        tag_for("equity"))  # positivo = riduzione share count
    prices = raw["prices"]
    pr_dates = sorted(prices)
    price_cagr = None
    if len(pr_dates) > 250:
        first, last = prices[pr_dates[0]], prices[pr_dates[-1]]
        yrs_span = (datetime.fromisoformat(pr_dates[-1])
                    - datetime.fromisoformat(pr_dates[0])).days / 365.25
        price_cagr = _cagr(last, first, max(int(round(yrs_span)), 1))
    put("C23", price_cagr, [], "V" if prices else "U")
    # Delta P/E: P/E attuale vs mediana storica (prezzo di fine FY / EPS FY)
    pe_hist = []
    eps_ok = [e for e in eps if e is not None]
    if prices and len(eps_ok) >= 3:
        yr_end_price: dict[int, float] = {}
        for d in pr_dates:
            yr_end_price[int(d[:4])] = prices[d]
        yrs_sorted = sorted(yr_end_price)[-len(eps_ok):]
        for i, y in enumerate(reversed(yrs_sorted)):
            if i < len(eps_ok) and eps_ok[i] and eps_ok[i] > 0:
                pe_hist.append(yr_end_price[y] / eps_ok[i])
    pe_med = statistics.median(pe_hist) if len(pe_hist) >= 3 else None
    ctx["pe_median_hist"] = pe_med
    dpe = None
    if pe_med and ctx["pe"]:
        dpe = (ctx["pe"] / pe_med - 1) * 100
    put("C24", dpe, pe_hist, "V" if dpe is not None else "U")

    # --- tasse e qualita' utili ------------------------------------------
    tax_pct = [t * 100 if t is not None else None for t in tax_rates]
    tax_vals = [t for t in tax_pct[:3] if t is not None]
    tax_avg = statistics.mean(tax_vals) if tax_vals else None
    tax_vol = (statistics.pstdev(tax_vals) if len(tax_vals) >= 2 else 0.0)
    put("C25", tax_avg, tax_pct, tag_for("net_income"), {"volatility": tax_vol})
    put("C26", None, [], "U")  # MOAT: manuale/lookup (T19), mai stimato
    ccr = None
    accruals = None
    if cfo and ni and cfo[0] is not None and ni[0] not in (None, 0) and ni[0] > 0:
        ccr = cfo[0] / ni[0]
    if cfo and ni and raw["total_assets"] and None not in (cfo[0], ni[0]) \
            and raw["total_assets"][0]:
        avg_assets = raw["total_assets"][0]
        if len(raw["total_assets"]) > 1 and raw["total_assets"][1]:
            avg_assets = (raw["total_assets"][0] + raw["total_assets"][1]) / 2
        accruals = (ni[0] - cfo[0]) / avg_assets
    put("C27", ccr, [], tag_for("net_income", "cfo"), {"accruals": accruals})

    # contesto extra per gate/red flag/IQI
    ctx["goodwill"] = raw["goodwill"][0] if raw["goodwill"] else None
    ctx["equity0"] = raw["equity"][0] if raw["equity"] else None
    ctx["ebitda0"] = raw["ebitda"][0] if raw["ebitda"] else None
    ctx["net_debt"] = None
    if raw["total_debt"] and raw["total_debt"][0] is not None:
        ctx["net_debt"] = raw["total_debt"][0] - (raw["cash"][0] or 0
                                                  if raw["cash"] else 0)
    ctx["interest_expense"] = (abs(raw["interest_expense"][0])
                               if raw["interest_expense"] and raw["interest_expense"][0]
                               else None)
    ctx["ebit0"] = raw["ebit"][0] if raw["ebit"] else None
    ctx["eps0"] = eps[0] if eps else None
    ctx["shares0"] = shares[0] if shares else info.get("sharesOutstanding")
    ctx["dps_last"] = dps_last
    ctx["nd_ebitda_series"] = []
    for i in range(min(len(raw["total_debt"]), len(raw["ebitda"]))):
        d_, e_ = raw["total_debt"][i], raw["ebitda"][i]
        c_ = raw["cash"][i] if i < len(raw["cash"]) else 0
        if None in (d_, e_) or e_ <= 0:
            ctx["nd_ebitda_series"].append(None)
        else:
            ctx["nd_ebitda_series"].append((d_ - (c_ or 0)) / e_)
    ctx["dividends_paid0"] = (abs(raw["dividends_paid"][0])
                              if raw["dividends_paid"] and raw["dividends_paid"][0]
                              else 0.0)
    ctx["capex0"] = capex[0] if capex else None
    ctx["cfo0"] = cfo[0] if cfo else None
    ctx["rev_growth_cagr"], _ = _series_cagr(rev)
    return m
