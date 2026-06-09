"""
MVF v3.0 — Modulo di valutazione finanziaria
Base 257, normalizzato su 100. Confidence Score su 100 (4 sub-score).

Contiene:
  - 5 modelli di valutazione (Graham, DDM 1/2 stadi, DCF 2 stadi 10y, EPV, Reverse DCF)
  - WACC esplicito via CAPM esteso (Rf + beta * ERP + CRP)
  - Sensitivity table 5x5 e scenari bull/base/bear
  - Punteggio MVF a 24 metriche pesate (base 257)
  - Confidence Score con 4 sub-score
  - Variation % 5y/3y per ogni metrica
  - Red flags automatici critici e attenzione
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional, Any
import math
import statistics


# =============================================================================
# COSTANTI: tassi sovrani, ERP, CRP (Damodaran NYU semestrale)
# =============================================================================

# Rf — Risk-free rate per mercato (10Y sovereign)
RISK_FREE_RATE = {
    "US": 0.043, "EU_core": 0.025, "IT": 0.038, "ES": 0.032,
    "UK": 0.040, "JP": 0.013, "EM": 0.075,
}
RF_FLOOR = 0.025  # floor su Y per Graham

# ERP — Equity Risk Premium (Damodaran 2025)
ERP = {
    "US": 0.055, "EU_core": 0.058, "IT": 0.063, "ES": 0.060,
    "UK": 0.057, "JP": 0.061, "EM": 0.085,
}

# CRP — Country Risk Premium (spread vs Germania)
CRP = {
    "US": 0.000, "EU_core": 0.000, "IT": 0.018, "ES": 0.008,
    "UK": 0.000, "JP": 0.005, "EM": 0.030,
}

# Pesi MVF v3.0 — Sezione 3B (base 257)
MVF_WEIGHTS = {
    "gross_margin": 15, "ebitda_margin": 5, "operating_margin": 25,
    "net_margin": 18, "fcf_margin": 22, "roic": 15, "roe": 3, "roa": 5,
    "debt_to_equity": 10, "debt_to_assets": 10, "altman_z": 5,
    "sbc_revenue": 5, "capex_revenue": 5, "capex_da": 3, "rd_revenue": 7,
    "insider_trading": 5, "dividend_yield": 16, "payout_ratio": 10,
    "dividend_growth_5y": 10, "buyback_yield": 5, "price_cagr_5y": 5,
    "tax_rate": 13, "moat_score": 25, "earnings_quality": 15,
}
# verifica somma = 257
assert sum(MVF_WEIGHTS.values()) == 257, "MVF weights sum != 257"

# Target ottimali per ogni metrica (normalizzazione 0-1)
MVF_TARGETS = {
    "gross_margin": 0.50, "ebitda_margin": 0.25, "operating_margin": 0.20,
    "net_margin": 0.15, "fcf_margin": 0.15, "roic": 0.15, "roe": 0.15,
    "roa": 0.08, "debt_to_equity": 0.60, "debt_to_assets": 0.30,
    "altman_z": 3.0, "sbc_revenue": 0.03, "capex_revenue": 0.05,
    "capex_da": 1.2, "rd_revenue": 0.08, "insider_trading": 0.0,
    "dividend_yield": 0.04, "payout_ratio": 0.50, "dividend_growth_5y": 0.05,
    "buyback_yield": 0.03, "price_cagr_5y": 0.10, "tax_rate": 0.22,
    "moat_score": 7.0, "earnings_quality": 1.0,
}
# Metriche dove "più basso è meglio"
MVF_INVERTED = {"debt_to_equity", "debt_to_assets", "sbc_revenue",
                "capex_revenue", "payout_ratio", "tax_rate"}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class MVFValuation:
    """Output completo della valutazione MVF v3.0 per un singolo titolo."""
    # Modelli di valutazione (fair value per azione)
    graham_fv: Optional[float] = None
    ddm_1stage_fv: Optional[float] = None
    ddm_2stage_fv: Optional[float] = None
    dcf_2stage_fv: Optional[float] = None
    epv_fv: Optional[float] = None
    reverse_dcf_implied_g: Optional[float] = None

    # WACC componenti
    wacc: Optional[float] = None
    cost_of_equity: Optional[float] = None
    cost_of_debt_at: Optional[float] = None
    beta_used: Optional[float] = None

    # Sensitivity DCF 5x5: variazioni WACC ±100/±200 bp x g_term ±100/±200 bp
    dcf_sensitivity: Optional[list[list[Optional[float]]]] = None

    # Scenari
    bull_fv: Optional[float] = None
    base_fv: Optional[float] = None
    bear_fv: Optional[float] = None
    expected_fv: Optional[float] = None    # 0.25*bull + 0.50*base + 0.25*bear

    # Target finale e MoS
    weighted_fair_value: Optional[float] = None  # media ponderata 5 modelli
    margin_of_safety_pct: Optional[float] = None
    ideal_purchase_price: Optional[float] = None
    upside_at_current_pct: Optional[float] = None

    # ROIC − WACC economic spread
    economic_spread: Optional[float] = None
    economic_spread_negative_2y: bool = False

    # Pesi modelli effettivamente usati (varia per settore/dividendo)
    weights_regime: str = "default"
    model_weights: dict = field(default_factory=dict)
    weight_dividends_halved: bool = False

    # Note di processo
    notes: list[str] = field(default_factory=list)


@dataclass
class ConfidenceScore:
    """4 sub-score 0-25 → totale 0-100."""
    data_quality: float = 0.0           # A: completezza, fonti, coerenza
    business_stability: float = 0.0     # B: FCF volatility, maturità, concentrazione
    projection_reliability: float = 0.0 # C: ciclicità, esposizione macro, pipeline
    model_coherence: float = 0.0        # D: dispersione fair value
    total: float = 0.0
    notes: list[str] = field(default_factory=list)


@dataclass
class VariationMetrics:
    """Variazione % 5y (fallback 3y) per ogni metrica chiave."""
    gross_margin_var: Optional[float] = None
    operating_margin_var: Optional[float] = None
    net_margin_var: Optional[float] = None
    fcf_margin_var: Optional[float] = None
    roic_var: Optional[float] = None
    roe_var: Optional[float] = None
    debt_to_equity_var: Optional[float] = None
    dividend_yield_var: Optional[float] = None
    payout_ratio_var: Optional[float] = None
    years_used: int = 0


@dataclass
class MVFRedFlags:
    """Red flag automatici MVF v3.0 Sezione 8."""
    # Critici
    altman_z_danger: bool = False
    fcf_negative_3y: bool = False
    de_above_3: bool = False
    net_margin_negative_2y: bool = False
    economic_spread_negative_2y: bool = False
    goodwill_over_50pct_equity: bool = False
    sbc_over_8pct_tech: bool = False
    # Attenzione
    altman_z_grey: bool = False
    fcf_negative_1y: bool = False
    payout_above_100: bool = False
    revenue_decline_2y: bool = False
    insider_selling: bool = False
    roe_below_capm: bool = False
    accruals_above_10pct: bool = False
    ccr_below_05: bool = False
    tax_rate_volatile_low: bool = False
    wc_growth_above_revenue: bool = False
    share_dilution_above_3pct: bool = False

    @property
    def critical_count(self) -> int:
        return sum([
            self.altman_z_danger, self.fcf_negative_3y, self.de_above_3,
            self.net_margin_negative_2y, self.economic_spread_negative_2y,
            self.goodwill_over_50pct_equity, self.sbc_over_8pct_tech
        ])

    @property
    def warning_count(self) -> int:
        return sum([
            self.altman_z_grey, self.fcf_negative_1y, self.payout_above_100,
            self.revenue_decline_2y, self.insider_selling, self.roe_below_capm,
            self.accruals_above_10pct, self.ccr_below_05,
            self.tax_rate_volatile_low, self.wc_growth_above_revenue,
            self.share_dilution_above_3pct
        ])


# =============================================================================
# WACC E COSTO DEL CAPITALE
# =============================================================================

def compute_cost_of_equity(market: str, beta: Optional[float]) -> tuple[float, float]:
    """CAPM esteso: Re = Rf + beta * ERP + CRP. Ritorna (Re, beta_used)."""
    rf = RISK_FREE_RATE.get(market, 0.040)
    erp = ERP.get(market, 0.060)
    crp = CRP.get(market, 0.010)
    b = beta if (beta is not None and 0.2 <= beta <= 3.0) else 1.0
    return rf + b * erp + crp, b


def compute_wacc(market_cap: float, total_debt: Optional[float],
                 interest_expense: Optional[float], tax_rate: Optional[float],
                 cost_of_equity: float) -> tuple[Optional[float], Optional[float]]:
    """WACC = E/V*Re + D/V*Rd*(1-T). Ritorna (WACC, Rd_after_tax)."""
    if not market_cap or market_cap <= 0:
        return None, None
    d = total_debt or 0
    v = market_cap + d
    e_w = market_cap / v
    d_w = d / v if v > 0 else 0
    if d > 0 and interest_expense is not None and interest_expense > 0:
        rd_pre = interest_expense / d
        t = tax_rate if (tax_rate is not None and 0 <= tax_rate <= 0.5) else 0.25
        rd_at = rd_pre * (1 - t)
    else:
        rd_at = 0.03  # proxy default
    wacc = e_w * cost_of_equity + d_w * rd_at
    return wacc, rd_at


# =============================================================================
# MODELLI DI VALUTAZIONE — 5 FORMULE
# =============================================================================

def graham_fair_value(eps: Optional[float], g_eps_5y: Optional[float],
                      market: str, is_us: bool) -> Optional[float]:
    """V_Graham = EPS × (M + 2g) × (4.4 / Y). Floor Y_min = 2.5%."""
    if eps is None or eps <= 0:
        return None
    g = g_eps_5y if (g_eps_5y is not None and -0.10 < g_eps_5y < 0.30) else 0.03
    M = 8.5 if is_us else 7.5
    Y_raw = RISK_FREE_RATE.get(market, 0.040)
    Y = max(Y_raw, RF_FLOOR) * 100  # convert to percentage points
    return eps * (M + 2 * g * 100) * (4.4 / Y)


def ddm_1stage(d0: Optional[float], g: Optional[float],
               r: float) -> Optional[float]:
    """Gordon Growth: V = D1 / (r-g). Solo se r > g."""
    if d0 is None or d0 <= 0 or g is None:
        return None
    g_capped = min(g, 0.04)  # max 4% PIL nominale europeo
    if r <= g_capped:
        return None
    d1 = d0 * (1 + g_capped)
    return d1 / (r - g_capped)


def ddm_2stage(d0: Optional[float], g1: Optional[float], g2: Optional[float],
               r: float, years_stage1: int = 5) -> Optional[float]:
    """DDM 2 stadi: g1 alta per 5 anni, g2 perpetua."""
    if d0 is None or d0 <= 0 or g1 is None or g2 is None:
        return None
    g1c = min(max(g1, -0.05), 0.20)
    g2c = min(g2, 0.04)
    if r <= g2c:
        return None
    pv = 0.0
    for i in range(1, years_stage1 + 1):
        div_i = d0 * (1 + g1c) ** i
        pv += div_i / (1 + r) ** i
    terminal_div = d0 * (1 + g1c) ** years_stage1 * (1 + g2c)
    tv = terminal_div / (r - g2c)
    pv += tv / (1 + r) ** years_stage1
    return pv


def dcf_2stage(fcf_0: Optional[float], g1: Optional[float], g_term: float,
               wacc: float, shares_diluted: Optional[float],
               net_debt: Optional[float],
               years_stage1: int = 5,
               years_decay: int = 5) -> Optional[float]:
    """DCF 2 stadi: g1 anni 1-5, decay lineare 6-10, g_term perpetuo."""
    if fcf_0 is None or fcf_0 <= 0 or g1 is None or wacc is None:
        return None
    if wacc <= g_term:
        return None
    g1c = min(max(g1, -0.05), 0.25)

    pv = 0.0
    fcf_t = fcf_0
    # Stage 1: anni 1-5 con g1
    for i in range(1, years_stage1 + 1):
        fcf_t = fcf_t * (1 + g1c)
        pv += fcf_t / (1 + wacc) ** i
    # Stage 1b: decay lineare anni 6-10 da g1 verso g_term
    g_step = (g1c - g_term) / years_decay if years_decay > 0 else 0
    for j in range(1, years_decay + 1):
        i = years_stage1 + j
        g_year = g1c - g_step * j
        fcf_t = fcf_t * (1 + g_year)
        pv += fcf_t / (1 + wacc) ** i

    # Terminal value
    tv = fcf_t * (1 + g_term) / (wacc - g_term)
    pv += tv / (1 + wacc) ** (years_stage1 + years_decay)

    # Equity value
    nd = net_debt or 0
    equity_value = pv - nd
    if shares_diluted and shares_diluted > 0:
        return equity_value / shares_diluted
    return None


def epv_fair_value(operating_income_norm: Optional[float], tax_rate: Optional[float],
                   wacc: float, shares_diluted: Optional[float],
                   net_debt: Optional[float]) -> Optional[float]:
    """EPV Greenwald = NOPAT_norm / WACC. Per aziende mature."""
    if operating_income_norm is None or operating_income_norm <= 0 or wacc <= 0:
        return None
    t = tax_rate if (tax_rate is not None and 0 <= tax_rate <= 0.5) else 0.25
    nopat = operating_income_norm * (1 - t)
    enterprise_value = nopat / wacc
    nd = net_debt or 0
    equity_value = enterprise_value - nd
    if shares_diluted and shares_diluted > 0:
        return equity_value / shares_diluted
    return None


def reverse_dcf_implied_growth(market_cap: float, net_debt: Optional[float],
                                fcf_0: float, wacc: float,
                                g_term: float = 0.02) -> Optional[float]:
    """Trova g1 implicita perché DCF = enterprise value attuale."""
    if not (market_cap and fcf_0 and fcf_0 > 0 and wacc > g_term):
        return None
    target_ev = market_cap + (net_debt or 0)
    # Bisection su g1 in [-0.05, 0.30]
    lo, hi = -0.05, 0.30
    for _ in range(60):
        mid = (lo + hi) / 2
        # ricalcola DCF con questa g1
        pv = 0.0
        fcf_t = fcf_0
        for i in range(1, 6):
            fcf_t = fcf_t * (1 + mid)
            pv += fcf_t / (1 + wacc) ** i
        g_step = (mid - g_term) / 5
        for j in range(1, 6):
            i = 5 + j
            g_year = mid - g_step * j
            fcf_t = fcf_t * (1 + g_year)
            pv += fcf_t / (1 + wacc) ** i
        tv = fcf_t * (1 + g_term) / (wacc - g_term)
        pv += tv / (1 + wacc) ** 10
        if pv > target_ev:
            hi = mid
        else:
            lo = mid
        if abs(pv - target_ev) / target_ev < 0.005:
            return round(mid, 4)
    return round((lo + hi) / 2, 4)


def dcf_sensitivity_table(fcf_0: float, g1: float, wacc_base: float,
                           g_term_base: float, shares: float,
                           net_debt: Optional[float]) -> list[list[Optional[float]]]:
    """Matrice 5x5: WACC ±200/100/0/-100/-200 bp x g_term -200/-100/0/+100/+200 bp."""
    wacc_shifts = [-0.02, -0.01, 0.0, 0.01, 0.02]
    g_shifts = [-0.02, -0.01, 0.0, 0.01, 0.02]
    matrix: list[list[Optional[float]]] = []
    for dw in wacc_shifts:
        row: list[Optional[float]] = []
        w = wacc_base + dw
        for dg in g_shifts:
            g_t = g_term_base + dg
            fv = dcf_2stage(fcf_0, g1, g_t, w, shares, net_debt)
            row.append(round(fv, 2) if fv else None)
        matrix.append(row)
    return matrix


def scenario_analysis(fcf_0: float, g_base: float, wacc: float,
                       shares: float, net_debt: Optional[float],
                       g_term: float = 0.02) -> tuple[Optional[float],
                                                       Optional[float],
                                                       Optional[float],
                                                       Optional[float]]:
    """Bull/Base/Bear con probabilità 25/50/25. Ritorna (bull, base, bear, expected)."""
    bull = dcf_2stage(fcf_0, g_base + 0.03, g_term, wacc - 0.005, shares, net_debt)
    base = dcf_2stage(fcf_0, g_base, g_term, wacc, shares, net_debt)
    bear = dcf_2stage(fcf_0, max(g_base - 0.03, -0.02), g_term,
                      wacc + 0.005, shares, net_debt)
    vals = [v for v in [bull, base, bear] if v is not None]
    if len(vals) < 2:
        return bull, base, bear, None
    # Probabilità mancanti: redistribuiamo
    if all(v is not None for v in [bull, base, bear]):
        expected = 0.25 * bull + 0.50 * base + 0.25 * bear
    elif base is not None:
        expected = base
    else:
        expected = sum(vals) / len(vals)
    return bull, base, bear, round(expected, 2) if expected else None


# =============================================================================
# PESI MODELLI PER SETTORE (Sezione 7 — sintesi)
# =============================================================================

SECTOR_MODEL_WEIGHTS = {
    "default":      {"graham": 0.20, "ddm": 0.30, "dcf": 0.35, "epv": 0.15},
    "reit":         {"graham": 0.00, "ddm": 0.50, "dcf": 0.30, "epv": 0.10},
    "bank":         {"graham": 0.10, "ddm": 0.30, "dcf": 0.30, "epv": 0.30},
    "insurance":    {"graham": 0.10, "ddm": 0.30, "dcf": 0.30, "epv": 0.30},
    "tech_growth":  {"graham": 0.00, "ddm": 0.00, "dcf": 0.60, "epv": 0.10},
    "cyclical":     {"graham": 0.10, "ddm": 0.10, "dcf": 0.40, "epv": 0.30},
    "utility":      {"graham": 0.20, "ddm": 0.40, "dcf": 0.20, "epv": 0.20},
    "no_dividend":  {"graham": 0.25, "ddm": 0.00, "dcf": 0.50, "epv": 0.20},
}


def classify_sector_for_weights(sector: str, industry: str,
                                 pays_dividend: bool,
                                 fcf_negative: bool) -> str:
    s = (sector or "").lower()
    ind = (industry or "").lower()
    if "real estate" in s or "reit" in ind:
        return "reit"
    if "bank" in ind or "financial services" in s and "bank" in ind:
        return "bank"
    if "insurance" in ind:
        return "insurance"
    if "utility" in s or "utilities" in s:
        return "utility"
    if "software" in ind or "technology" in s and fcf_negative:
        return "tech_growth"
    if any(c in s for c in ["energy", "basic materials"]) or "mining" in ind:
        return "cyclical"
    if not pays_dividend:
        return "no_dividend"
    return "default"


def weighted_fair_value(model_fvs: dict, sector_class: str) -> tuple[Optional[float], dict]:
    """Calcola media ponderata fair value usando pesi del settore."""
    weights = SECTOR_MODEL_WEIGHTS.get(sector_class, SECTOR_MODEL_WEIGHTS["default"]).copy()
    # ddm può essere ddm_2stage o ddm_1stage (prendi miglior disponibile)
    ddm_fv = model_fvs.get("ddm_2stage") or model_fvs.get("ddm_1stage")
    candidates = {
        "graham": model_fvs.get("graham"),
        "ddm": ddm_fv,
        "dcf": model_fvs.get("dcf"),
        "epv": model_fvs.get("epv"),
    }
    # rimuovi modelli None e rinormalizza
    avail = {k: v for k, v in candidates.items() if v is not None and v > 0}
    if not avail:
        return None, weights
    w_avail = {k: weights[k] for k in avail}
    tot_w = sum(w_avail.values())
    if tot_w == 0:
        return None, weights
    w_norm = {k: v / tot_w for k, v in w_avail.items()}
    fv = sum(avail[k] * w_norm[k] for k in avail)

    # check divergenza > 30% → segnala
    vals = list(avail.values())
    if len(vals) >= 2:
        med = statistics.median(vals)
        if med > 0:
            max_dev = max(abs(v - med) / med for v in vals)
            if max_dev > 0.30:
                # riduci peso outlier (mantiene logica spec)
                pass  # mantieni com'è ma flag nel callsite
    return round(fv, 2), w_norm


# =============================================================================
# VARIATION % 5Y (fallback 3y)
# =============================================================================

def compute_variation_pct(series: list[Optional[float]],
                          min_years: int = 3) -> tuple[Optional[float], int]:
    """Calcola variazione % tra primo e ultimo valore della serie.
    Series è ordinata dal più recente al più vecchio (yfinance default).
    Ritorna (var%, anni_usati)."""
    if not series or len(series) < min_years:
        return None, 0
    clean = [v for v in series if v is not None and not math.isnan(v)]
    if len(clean) < min_years:
        return None, 0
    n = min(5, len(clean))
    latest, oldest = clean[0], clean[n - 1]
    if oldest == 0:
        return None, 0
    var = (latest - oldest) / abs(oldest)
    return round(var, 4), n


# =============================================================================
# MVF SCORING — 257 → /100
# =============================================================================

def normalize_metric(value: Optional[float], target: float,
                     inverted: bool = False) -> float:
    """Normalizza una metrica su [0, 1] rispetto al target."""
    if value is None:
        return 0.0
    if inverted:
        # più basso è meglio: ratio inverso, cappato a 2
        if value <= 0:
            return 0.0 if inverted else 1.0
        ratio = target / value
    else:
        ratio = value / target if target > 0 else 0
    return max(0.0, min(1.0, ratio / 2))


def compute_mvf_score(metrics: dict, has_dividend: bool, ddm_used: bool,
                     altman_z: Optional[float],
                     economic_spread_neg_2y: bool) -> tuple[float, dict]:
    """Calcola voto MVF /100. Ritorna (score_norm_100, breakdown)."""
    weights = dict(MVF_WEIGHTS)

    # Sezione 3E: azienda senza dividendo → redistribuisci 36 punti
    if not has_dividend:
        weights["dividend_yield"] = 0
        weights["payout_ratio"] = 0
        weights["dividend_growth_5y"] = 0
        weights["fcf_margin"] += 10
        weights["buyback_yield"] += 10
        weights["price_cagr_5y"] += 8
        weights["roic"] += 8

    # Sezione 3F: DDM applicato → dimezza pesi dividendi, redistribuisci 18 pt
    elif ddm_used:
        weights["dividend_yield"] = 8
        weights["payout_ratio"] = 5
        weights["dividend_growth_5y"] = 5
        weights["fcf_margin"] += 10
        weights["net_margin"] += 8

    raw = 0.0
    total_weight = 0.0
    breakdown = {}
    for name, w in weights.items():
        if w == 0:
            continue
        target = MVF_TARGETS.get(name, 1.0)
        inverted = name in MVF_INVERTED
        val = metrics.get(name)
        n = normalize_metric(val, target, inverted)
        raw += w * n
        total_weight += w
        breakdown[name] = {"weight": w, "value": val, "norm": round(n, 3)}

    score_raw = (raw / total_weight) * 100 if total_weight else 0

    # Sezione 3D: penalità additiva Altman-Z
    penalty = 0.0
    if altman_z is not None:
        if altman_z < 1.23:
            penalty = -0.20  # -20%
            breakdown["_altman_penalty"] = "-20% (zona pericolo)"
        elif altman_z < 1.81:
            penalty = -0.10
            breakdown["_altman_penalty"] = "-10% (zona grigia)"
    if economic_spread_neg_2y:
        penalty -= 0.10
        breakdown["_economic_spread_penalty"] = "-10% (ROIC<WACC 2y)"

    score_final = max(0.0, min(100.0, score_raw * (1 + penalty)))
    breakdown["_raw_score"] = round(score_raw, 1)
    breakdown["_total_penalty"] = round(penalty * 100, 1)
    return round(score_final, 1), breakdown


# =============================================================================
# CONFIDENCE SCORE — Sezione 10
# =============================================================================

def compute_confidence_score(data_completeness_pct: float,
                              fcf_series: list[float],
                              sector: str,
                              model_fvs: list[float],
                              has_quality_audit: bool = True) -> ConfidenceScore:
    """4 sub-score 0-25, somma 0-100."""
    cs = ConfidenceScore()
    notes = []

    # A. Qualità dati (0-25)
    a = data_completeness_pct * 25
    if not has_quality_audit:
        a *= 0.7
        notes.append("dati non auditati: -30% sub-A")
    cs.data_quality = round(min(25, max(0, a)), 1)

    # B. Stabilità business (0-25)
    b = 12.5  # base media
    if fcf_series and len(fcf_series) >= 3:
        clean = [v for v in fcf_series if v is not None]
        if len(clean) >= 3 and all(v > 0 for v in clean):
            mean_fcf = statistics.mean(clean)
            if mean_fcf > 0:
                cv = statistics.stdev(clean) / mean_fcf
                # CV basso → score alto
                b = 25 * max(0, 1 - cv)
    # Maturità settore
    s = (sector or "").lower()
    if any(c in s for c in ["utility", "consumer staples", "healthcare"]):
        b = min(25, b + 3)
    elif any(c in s for c in ["technology", "communication"]):
        b = max(0, b - 2)
    cs.business_stability = round(min(25, max(0, b)), 1)

    # C. Affidabilità proiezioni (0-25)
    c = 15.0
    if any(c2 in s for c2 in ["utility", "real estate", "healthcare"]):
        c = 20.0  # settori prevedibili
    elif any(c2 in s for c2 in ["energy", "basic materials", "consumer cyclical"]):
        c = 10.0  # ciclici
    cs.projection_reliability = round(c, 1)

    # D. Coerenza modelli (0-25): dispersione fair value
    if len(model_fvs) >= 2:
        clean_fvs = [v for v in model_fvs if v is not None and v > 0]
        if len(clean_fvs) >= 2:
            med = statistics.median(clean_fvs)
            max_dev = max(abs(v - med) / med for v in clean_fvs) if med > 0 else 1
            if max_dev < 0.15:
                d = 24
            elif max_dev < 0.30:
                d = 17
            else:
                d = 8
                notes.append(f"dispersione FV {max_dev:.0%} > 30%")
            cs.model_coherence = round(d, 1)
        else:
            cs.model_coherence = 10.0
    else:
        cs.model_coherence = 8.0

    cs.total = round(cs.data_quality + cs.business_stability
                     + cs.projection_reliability + cs.model_coherence, 1)
    cs.notes = notes
    return cs


# =============================================================================
# MARGINE DI SICUREZZA E PREZZO IDEALE
# =============================================================================

def margin_of_safety_for_cs(cs_total: float) -> float:
    """Sezione 7: MoS basata su Confidence Score."""
    if cs_total >= 80:
        return 0.30
    if cs_total >= 70:
        return 0.40
    return 0.50


def ideal_purchase_price(fair_value: Optional[float], mos: float) -> Optional[float]:
    if fair_value is None or fair_value <= 0:
        return None
    return round(fair_value * (1 - mos), 2)


# =============================================================================
# RED FLAG DETECTOR (Sezione 8)
# =============================================================================

def detect_red_flags(metrics: dict, altman_z: Optional[float],
                     fcf_series: list[Optional[float]],
                     net_margin_series: list[Optional[float]],
                     economic_spread_neg_2y: bool,
                     goodwill: Optional[float], equity: Optional[float],
                     is_tech: bool, revenue_series: list[Optional[float]],
                     accruals: Optional[float], ccr: Optional[float],
                     share_dilution: Optional[float],
                     payout: Optional[float], roe: Optional[float],
                     cost_of_equity: float,
                     working_capital_series: list[Optional[float]]) -> MVFRedFlags:
    rf = MVFRedFlags()

    # === CRITICI ===
    if altman_z is not None and altman_z < 1.23:
        rf.altman_z_danger = True
    clean_fcf = [v for v in fcf_series if v is not None]
    if len(clean_fcf) >= 3 and all(v < 0 for v in clean_fcf[:3]):
        rf.fcf_negative_3y = True
    de = metrics.get("debt_to_equity")
    if de is not None and de > 3.0:
        rf.de_above_3 = True
    clean_nm = [v for v in net_margin_series if v is not None]
    if len(clean_nm) >= 3:
        neg_count = sum(1 for v in clean_nm[:3] if v < 0)
        if neg_count >= 2:
            rf.net_margin_negative_2y = True
    if economic_spread_neg_2y:
        rf.economic_spread_negative_2y = True
    if goodwill and equity and equity > 0 and (goodwill / equity) > 0.50:
        rf.goodwill_over_50pct_equity = True
    sbc = metrics.get("sbc_revenue")
    if is_tech and sbc is not None and sbc > 0.08:
        rf.sbc_over_8pct_tech = True

    # === ATTENZIONE ===
    if altman_z is not None and 1.23 <= altman_z < 1.81:
        rf.altman_z_grey = True
    if len(clean_fcf) >= 3 and sum(1 for v in clean_fcf[:3] if v < 0) == 1:
        rf.fcf_negative_1y = True
    if payout is not None and payout > 1.0:
        rf.payout_above_100 = True
    clean_rev = [v for v in revenue_series if v is not None]
    if len(clean_rev) >= 3 and clean_rev[0] < clean_rev[1] < clean_rev[2]:
        rf.revenue_decline_2y = True
    if roe is not None and roe < cost_of_equity:
        rf.roe_below_capm = True
    if accruals is not None and accruals > 0.10:
        rf.accruals_above_10pct = True
    if ccr is not None and ccr < 0.5:
        rf.ccr_below_05 = True
    if share_dilution is not None and share_dilution > 0.03:
        rf.share_dilution_above_3pct = True
    clean_wc = [v for v in working_capital_series if v is not None]
    if len(clean_wc) >= 3 and len(clean_rev) >= 3:
        wc_growth = (clean_wc[0] - clean_wc[2]) / abs(clean_wc[2]) if clean_wc[2] else 0
        rev_growth = (clean_rev[0] - clean_rev[2]) / abs(clean_rev[2]) if clean_rev[2] else 0
        if wc_growth > rev_growth and wc_growth > 0.10:
            rf.wc_growth_above_revenue = True

    return rf
