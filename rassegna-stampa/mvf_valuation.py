"""
MVF v4.1 — Modulo di valutazione finanziaria
=============================================================================

Riscrittura sull'architettura v4.1 (il documento sorgente dichiara "v4.0"
nell'intestazione ma la versione corrente della specifica e' la 4.1).

DIFFERENZE STRUTTURALI RISPETTO ALLA v3.0 (modulo precedente):
  - Base di calcolo 257 -> 280 (common), con basi dedicate per classe
  - Voto normalizzato su 1000 (era /100)
  - STEP 0 di routing per classe di strumento (Sez. 2)
  - IQI (Indice di Qualita' dell'Investimento) su 100 -> guida il MoS
  - MoS = MoS_base(IQI) + overlay(CS), non piu' derivato dal solo CS
  - Gate di qualita' G1-G6 (Sez. 8-bis), distinti dai red flag
  - Metriche nuove: FCF/share growth (18), EPS growth (10), Delta P/E (5)
  - Rendimento netto post-imposte HOME vs ITALIA (Sez. 7)
  - Riconciliazione Voto MVF <-> IQI

REGIME DI ESECUZIONE
  Questo modulo gira in REGIME S (screening batch, fonte dati singola).
  La specifica MVF e' redatta per il REGIME A (analisi documentale su un
  singolo titolo, con provenance tagging [P]/[V]/[U] via EDGAR/IR).
  Le deviazioni dal regime A sono esplicite e marcate "DEVIAZIONE REGIME S".

  Deviazioni attive:
    1. MOAT (peso 25/280): la specifica impone Morningstar. In regime S si
       usa un proxy euristico da fondamentali -> vedi moat_proxy_score().
    2. Confidence Score: senza tagging DIP tutti i dati sarebbero [U] e il
       gate CS<50 escluderebbe l'intero universo. Il CS e' ricalibrato sulla
       scala di regime S -> vedi compute_confidence_score(). Gate a 35.
    3. IQI Blocco B: B1/B4 richiedono guidance [G] o consensus [C]. In
       regime S sono derivati da serie storiche e taggati [S], con il cap
       al 50% che la specifica stessa prevede per quel caso (Sez. 7).

  Ogni output porta i campi mvf_version, instrument_class, base, regime.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional, Any
import math
import statistics


MVF_VERSION = "4.1"
EXECUTION_REGIME = "S"   # S = screening batch | A = analisi documentale


# =============================================================================
# COSTANTI: tassi sovrani, ERP, CRP (Damodaran NYU semestrale)
# =============================================================================

RISK_FREE_RATE = {
    "US": 0.043, "EU_core": 0.025, "IT": 0.038, "ES": 0.032,
    "UK": 0.040, "JP": 0.013, "EM": 0.075,
}
RF_FLOOR = 0.025  # floor su Y per Graham

ERP = {
    "US": 0.055, "EU_core": 0.058, "IT": 0.063, "ES": 0.060,
    "UK": 0.057, "JP": 0.061, "EM": 0.085,
}

CRP = {
    "US": 0.000, "EU_core": 0.000, "IT": 0.018, "ES": 0.008,
    "UK": 0.000, "JP": 0.005, "EM": 0.030,
}


# =============================================================================
# STEP 0 — CLASSI DI STRUMENTO E BASI (Sez. 2)
# =============================================================================

# Ogni classe ha la PROPRIA base. I Voti NON sono confrontabili tra classi
# diverse (Sez. 11F): confronto valido solo intra-classe e intra-versione.
INSTRUMENT_BASES = {
    "common":    280,
    "reit":      370,
    "bdc":       299,
    "mlp":       309,
    "preferred": 168,   # VOTO MVF-P, motore credito/reddito
}

# In regime S e' implementato il solo motore common. Le altre classi vengono
# RILEVATE e marcate: meglio nessun voto che un voto prodotto dal motore
# sbagliato su metriche non pertinenti.
IMPLEMENTED_ENGINES = {"common"}


# =============================================================================
# PESI MVF v4.1 — BASE COMMON 280 (Sez. 3B)
# =============================================================================

MVF_WEIGHTS_COMMON = {
    # Redditivita'
    "gross_margin": 15, "ebitda_margin": 5, "operating_margin": 25,
    "net_margin": 18, "fcf_margin": 12,
    # Crescita per azione (v4.x)
    "eps_growth": 10, "fcf_per_share_growth": 18,
    # Ritorni sul capitale
    "roic": 15, "roe": 3, "roa": 5,
    # Solidita'
    "debt_to_equity": 10, "debt_to_assets": 10, "altman_z": 5,
    # Efficienza del capitale
    "sbc_revenue": 5, "capex_revenue": 5, "capex_da": 3, "rd_revenue": 7,
    "insider_trading": 5,
    # Remunerazione azionista
    "dividend_yield": 16, "payout_ratio": 10, "dividend_growth_5y": 10,
    "buyback_yield": 5, "price_cagr_5y": 5, "multiple_expansion": 5,
    # Qualita' del business
    "tax_rate": 13, "moat_score": 25, "earnings_quality": 15,
}
assert sum(MVF_WEIGHTS_COMMON.values()) == 280, "MVF v4.1 common weights sum != 280"

# Target ottimali per la normalizzazione lineare (metriche non a bande)
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

# Metriche dove "piu' basso e' meglio"
MVF_INVERTED = {"debt_to_equity", "debt_to_assets", "sbc_revenue",
                "capex_revenue", "payout_ratio", "tax_rate"}

# Metriche valutate a bande discrete (Sez. 3 B-bis), non per rapporto/target
MVF_BANDED = {"eps_growth", "fcf_per_share_growth", "multiple_expansion"}


# =============================================================================
# FISCALITA' — RITENUTE ALLA FONTE (Sez. 7)
# =============================================================================

IT_DIVIDEND_TAX = 0.26   # imposta sostitutiva italiana sul netto-frontiera

# VALORI INDICATIVI: la specifica impone di verificare la convenzione
# vigente (testo del trattato / Agenzia delle Entrate) prima dell'uso.
WITHHOLDING_TAX = {
    "US": 0.15,      # con W-8BEN (30% senza)
    "UK": 0.00,
    "NL": 0.15,
    "DE": 0.15,      # 26,375% statutario, 15% via rimborso
    "FR": 0.15,      # 25% statutario, ~15% via trattato
    "ES": 0.19,
    "CH": 0.15,      # 35% statutario, 15% via rimborso
    "CA": 0.15,      # 25% statutario, 15% via trattato
    "IE": 0.20,
    "IT": 0.00,      # titolo domestico: nessuna ritenuta estera
    "JP": 0.15,
    "DK": 0.15,
    "SE": 0.15,
    "NO": 0.15,
    "AU": 0.15,
    "CN": 0.10,
}
DEFAULT_WITHHOLDING = 0.15

# Casi speciali che rompono il treaty rate ordinario (Sez. 7)
SPECIAL_WITHHOLDING_US = {
    "reit":      0.30,   # ordinary dividend distributions fuori treaty
    "mlp":       0.37,   # ritenuta IRC 1446
    "bdc":       0.30,   # ordinary income, spesso non qualified
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class InstrumentRouting:
    """Esito dello STEP 0 di classificazione (Sez. 2)."""
    instrument_class: str = "common"
    base: int = 280
    engine_available: bool = True
    routing_reason: str = ""
    notes: list[str] = field(default_factory=list)


@dataclass
class MVFValuation:
    """Output completo della valutazione MVF v4.1 per un singolo titolo."""
    # Identita' e versionamento (Sez. 11F)
    mvf_version: str = MVF_VERSION
    execution_regime: str = EXECUTION_REGIME
    instrument_class: str = "common"
    base: int = 280

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

    # Sensitivity DCF 5x5
    dcf_sensitivity: Optional[list[list[Optional[float]]]] = None

    # Scenari
    bull_fv: Optional[float] = None
    base_fv: Optional[float] = None
    bear_fv: Optional[float] = None
    expected_fv: Optional[float] = None

    # Target finale e MoS (catena v4.1: IQI -> MoS_base, CS -> overlay)
    weighted_fair_value: Optional[float] = None
    margin_of_safety_pct: Optional[float] = None
    mos_base_pct: Optional[float] = None
    mos_overlay_pct: Optional[float] = None
    ideal_purchase_price: Optional[float] = None
    upside_at_current_pct: Optional[float] = None
    abstain: bool = False
    abstain_reason: str = ""

    # ROIC - WACC economic spread
    economic_spread: Optional[float] = None
    economic_spread_negative_2y: bool = False

    # Robustezza valutativa (Sez. 7)
    model_dispersion_pct: Optional[float] = None
    dispersion_flag: str = ""

    # Pesi modelli effettivamente usati
    weights_regime: str = "default"
    model_weights: dict = field(default_factory=dict)
    weight_dividends_halved: bool = False

    notes: list[str] = field(default_factory=list)


@dataclass
class ConfidenceScore:
    """4 sub-score 0-25 -> totale 0-100 (Sez. 10).

    In regime S la scala e' ricalibrata: senza provenance tagging DIP il
    sub-score A non puo' superare il tetto di regime.
    """
    provenance: float = 0.0          # A: provenienza/autorevolezza
    completeness: float = 0.0        # B: completezza/copertura
    timeliness: float = 0.0          # C: puntualita'
    coherence: float = 0.0           # D: coerenza/cross-validation
    total: float = 0.0
    regime: str = EXECUTION_REGIME
    source_tag: str = "V"            # [P] primario | [V] validato | [U] non validato
    gate_threshold: float = 46.5     # 50/100 di specifica, riscalato sul cap
    gate_active: bool = False
    reading: str = ""                # Alta / Media / Bassa / Insufficiente
    notes: list[str] = field(default_factory=list)
    _provenance_cap: float = 18.0

    # Retrocompatibilita' con il modulo v3.0
    @property
    def data_quality(self) -> float:
        return self.provenance

    @property
    def business_stability(self) -> float:
        return self.completeness

    @property
    def projection_reliability(self) -> float:
        return self.timeliness

    @property
    def model_coherence(self) -> float:
        return self.coherence


@dataclass
class IQIScore:
    """Indice di Qualita' dell'Investimento (Sez. 7). Guida il MoS.

    IQI = 0.40 x BLOCCO A (Solidita') + 0.60 x BLOCCO B (Prospettive & Reddito)
    """
    # Blocco A — Solidita' (0-100)
    a1_patrimoniale: float = 0.0     # max 30
    a2_reddituale: float = 0.0       # max 25
    a3_cassa: float = 0.0            # max 30
    a4_competitiva: float = 0.0      # max 15
    blocco_a: float = 0.0

    # Blocco B — Prospettive & Reddito (0-100)
    b1_crescita: float = 0.0
    b2_remunerazione: float = 0.0
    b3_multiplo: float = 0.0         # max 15
    b4_tsr_forward: float = 0.0      # max 15
    blocco_b: float = 0.0

    dividend_tier: str = ""          # forte / solido / nascente / buyback / nessuna
    b1_max: float = 0.0
    b2_max: float = 0.0
    forward_capped: bool = False     # cap 50% se B1+B4 sono stime [S]

    total: float = 0.0
    notes: list[str] = field(default_factory=list)


@dataclass
class QualityGates:
    """Gate di esclusione qualita' G1-G6 (Sez. 8-bis). NO-BUY strutturale.

    A differenza dei red flag, un gate attivo esclude il titolo a
    prescindere da prezzo, MoS e IQI.
    """
    g1_cash_destruction: bool = False
    g2_value_destruction: bool = False
    g3_leverage_unserviced: bool = False
    g4_shareholder_transfer: bool = False
    g5_technical_insolvency: bool = False
    g6_capital_allocation: bool = False   # non valutabile in regime S
    active: list[str] = field(default_factory=list)
    details: dict = field(default_factory=dict)
    not_evaluable: list[str] = field(default_factory=list)

    @property
    def is_blocked(self) -> bool:
        return bool(self.active)


@dataclass
class NetYield:
    """Rendimento netto post-imposte HOME vs ITALIA (Sez. 7)."""
    gross_yield: Optional[float] = None
    withholding_rate: Optional[float] = None
    net_home: Optional[float] = None
    net_italy: Optional[float] = None
    withholding_drag: Optional[float] = None
    italian_tax_drag: Optional[float] = None
    total_tax_drag: Optional[float] = None
    effective_combined_rate: Optional[float] = None
    country: str = ""
    special_case: str = ""
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
    years_used: int = 0


@dataclass
class MVFRedFlags:
    """Red flag automatici (Sez. 8). SEGNALANO, non escludono."""
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
    # v4.x
    eps_fcf_divergence: bool = False        # EPS/share su ma FCF/share piatto
    multiple_expansion_driven: bool = False  # rendimento 5y da espansione multiplo
    eps_growth_from_buyback: bool = False
    forward_estimates_only: bool = False     # B1+B4 solo stime [S]


# =============================================================================
# STEP 0 — ROUTING DI CLASSIFICAZIONE (Sez. 2)
# =============================================================================

_REIT_HINTS = ("reit", "real estate investment trust", "mortgage trust")
_BDC_HINTS = ("business development compan", "bdc")
_MLP_HINTS = (" lp", " l.p.", "partners lp", "midstream", "master limited")
_PREFERRED_HINTS = ("preferred", " pfd", "pref shs", "depositary shs",
                    "baby bond", "cumulative pfd")


def classify_instrument(sector: Optional[str], industry: Optional[str],
                        name: Optional[str] = None,
                        ticker: Optional[str] = None,
                        quote_type: Optional[str] = None) -> InstrumentRouting:
    """STEP 0: instrada il titolo al motore corretto (Sez. 2).

    Va risolto PRIMA di qualunque calcolo: la classe determina base,
    metriche, pesi dei modelli, gate applicabili e ritenuta fiscale.
    """
    s = (sector or "").lower()
    ind = (industry or "").lower()
    nm = (name or "").lower()
    tk = (ticker or "").upper()
    blob = f"{ind} {nm}"

    def _route(cls: str, reason: str) -> InstrumentRouting:
        available = cls in IMPLEMENTED_ENGINES
        r = InstrumentRouting(
            instrument_class=cls,
            base=INSTRUMENT_BASES[cls],
            engine_available=available,
            routing_reason=reason,
        )
        if not available:
            r.notes.append(
                f"Classe '{cls}' rilevata (base {INSTRUMENT_BASES[cls]}): motore "
                f"dedicato non disponibile in regime {EXECUTION_REGIME}. "
                f"Nessun voto emesso — il motore common userebbe metriche non "
                f"pertinenti. Analisi dedicata richiesta (regime A)."
            )
        return r

    # Preferred / ibridi: motore credito, esce dal motore azionario
    if any(h in blob for h in _PREFERRED_HINTS):
        return _route("preferred", "denominazione contiene marcatore preferred/ibrido")
    # Il suffisso -P / .PR indica spesso una linea preferred
    if tk.endswith(("-P", ".PR")) or "-P" in tk.split(".")[0][-2:]:
        return _route("preferred", "suffisso ticker tipico di linea preferred")

    if any(h in blob for h in _BDC_HINTS):
        return _route("bdc", "denominazione contiene marcatore BDC")

    if any(h in blob for h in _MLP_HINTS):
        return _route("mlp", "denominazione contiene marcatore MLP/midstream")

    if "real estate" in s or any(h in blob for h in _REIT_HINTS):
        return _route("reit", "settore/industria immobiliare o marcatore REIT")

    return _route("common", "nessun marcatore di classe speciale rilevato")


# =============================================================================
# WACC — CAPM ESTESO
# =============================================================================

def compute_cost_of_equity(market: str, beta: Optional[float]) -> tuple[float, float]:
    """r = Rf + beta x ERP + CRP. Ritorna (cost_of_equity, beta_usato)."""
    rf = RISK_FREE_RATE.get(market, RISK_FREE_RATE["US"])
    erp = ERP.get(market, ERP["US"])
    crp = CRP.get(market, CRP["US"])
    b = beta if beta is not None and 0.1 <= beta <= 3.0 else 1.0
    return rf + b * erp + crp, b


def compute_wacc(market_cap: float, total_debt: Optional[float],
                 interest_expense: Optional[float], tax_rate: Optional[float],
                 cost_of_equity: float) -> tuple[Optional[float], Optional[float]]:
    """WACC = E/(D+E) x Re + D/(D+E) x Rd x (1-t). Ritorna (wacc, rd_after_tax)."""
    if not market_cap or market_cap <= 0:
        return None, None
    d = total_debt or 0
    e = market_cap
    v = d + e
    if v <= 0:
        return None, None
    t = tax_rate if tax_rate is not None and 0 <= tax_rate <= 0.60 else 0.25
    if d > 0 and interest_expense:
        rd = abs(interest_expense) / d
        rd = max(0.005, min(0.20, rd))
    else:
        rd = 0.05
    rd_at = rd * (1 - t)
    wacc = (e / v) * cost_of_equity + (d / v) * rd_at
    return round(wacc, 4), round(rd_at, 4)


# =============================================================================
# MODELLI DI VALUTAZIONE (Sez. 7)
# =============================================================================

def graham_fair_value(eps: Optional[float], g_eps_5y: Optional[float],
                      market: str, is_us: Optional[bool] = None) -> Optional[float]:
    """V = EPS x (M + 2g) x (4.4 / Y). M = 8.5 US / 7.5 EU. Floor Y 2.5%."""
    if eps is None or eps <= 0:
        return None
    us = is_us if is_us is not None else (market == "US")
    m = 8.5 if us else 7.5
    g = (g_eps_5y or 0.03) * 100
    g = max(-5, min(20, g))
    y = max(RF_FLOOR, RISK_FREE_RATE.get(market, 0.043)) * 100
    return round(eps * (m + 2 * g) * (4.4 / y), 2)


def ddm_1stage(d0: Optional[float], g: Optional[float],
               r: float) -> Optional[float]:
    """Gordon: V = D1 / (r - g). g = min(0.04, min(g_sost, g_stor))."""
    if d0 is None or d0 <= 0:
        return None
    gg = min(0.04, g if g is not None else 0.02)
    if r <= gg:
        return None
    return round(d0 * (1 + gg) / (r - gg), 2)


def ddm_2stage(d0: Optional[float], g1: Optional[float], g2: Optional[float],
               r: float, years1: int = 5) -> Optional[float]:
    """DDM a 2 stadi: g1 anni 1-5, g2 perpetuo dall'anno 6."""
    if d0 is None or d0 <= 0:
        return None
    gg1 = g1 if g1 is not None else 0.03
    gg2 = min(0.04, g2 if g2 is not None else 0.02)
    if r <= gg2:
        return None
    pv = 0.0
    d = d0
    for t in range(1, years1 + 1):
        d = d * (1 + gg1)
        pv += d / ((1 + r) ** t)
    d_term = d * (1 + gg2)
    tv = d_term / (r - gg2)
    pv += tv / ((1 + r) ** years1)
    return round(pv, 2)


def dcf_2stage(fcf_0: Optional[float], g1: Optional[float], g_term: float,
               wacc: float, shares: Optional[float],
               net_debt: Optional[float] = None,
               years: int = 10) -> Optional[float]:
    """DCF a 2 stadi su 10 anni con decay lineare di g negli anni 6-10."""
    if fcf_0 is None or fcf_0 <= 0 or not shares or shares <= 0:
        return None
    if wacc <= g_term:
        return None
    gg1 = g1 if g1 is not None else 0.05
    gg1 = max(-0.10, min(0.25, gg1))
    pv = 0.0
    fcf = fcf_0
    for t in range(1, years + 1):
        if t <= 5:
            g_t = gg1
        else:
            # decay lineare da g1 a g_term negli anni 6-10
            frac = (t - 5) / (years - 5)
            g_t = gg1 + (g_term - gg1) * frac
        fcf = fcf * (1 + g_t)
        pv += fcf / ((1 + wacc) ** t)
    tv = fcf * (1 + g_term) / (wacc - g_term)
    pv += tv / ((1 + wacc) ** years)
    equity_value = pv - (net_debt or 0)
    if equity_value <= 0:
        return None
    return round(equity_value / shares, 2)


def epv_fair_value(operating_income_norm: Optional[float],
                   tax_rate: Optional[float], wacc: float,
                   shares: Optional[float],
                   net_debt: Optional[float] = None) -> Optional[float]:
    """EPV = NOPAT normalizzato / WACC. Valore degli utili senza crescita."""
    if operating_income_norm is None or operating_income_norm <= 0:
        return None
    if not shares or shares <= 0 or wacc <= 0:
        return None
    t = tax_rate if tax_rate is not None and 0 <= tax_rate <= 0.60 else 0.25
    nopat = operating_income_norm * (1 - t)
    ev = nopat / wacc
    equity_value = ev - (net_debt or 0)
    if equity_value <= 0:
        return None
    return round(equity_value / shares, 2)


def reverse_dcf_implied_growth(market_cap: float, net_debt: Optional[float],
                               fcf_0: Optional[float], wacc: float,
                               g_term: float = 0.02,
                               years: int = 10) -> Optional[float]:
    """Estrae la crescita implicita nel prezzo corrente (bisezione)."""
    if not fcf_0 or fcf_0 <= 0 or not market_cap or market_cap <= 0:
        return None
    if wacc <= g_term:
        return None
    target_ev = market_cap + (net_debt or 0)

    def _ev_for_g(g: float) -> float:
        pv = 0.0
        fcf = fcf_0
        for t in range(1, years + 1):
            if t <= 5:
                g_t = g
            else:
                frac = (t - 5) / (years - 5)
                g_t = g + (g_term - g) * frac
            fcf = fcf * (1 + g_t)
            pv += fcf / ((1 + wacc) ** t)
        tv = fcf * (1 + g_term) / (wacc - g_term)
        return pv + tv / ((1 + wacc) ** years)

    lo, hi = -0.30, 0.50
    if _ev_for_g(lo) > target_ev or _ev_for_g(hi) < target_ev:
        return None
    for _ in range(60):
        mid = (lo + hi) / 2
        if _ev_for_g(mid) < target_ev:
            lo = mid
        else:
            hi = mid
    return round((lo + hi) / 2, 4)


def dcf_sensitivity_table(fcf_0: float, g1: float, wacc_base: float,
                          g_term_base: float, shares: float,
                          net_debt: Optional[float] = None) -> list:
    """Tabella 5x5: WACC +/-100/200bp x g_term +/-100/200bp."""
    out = []
    for dw in (-0.02, -0.01, 0.0, 0.01, 0.02):
        row = []
        for dg in (-0.02, -0.01, 0.0, 0.01, 0.02):
            w = wacc_base + dw
            g = g_term_base + dg
            if w <= g or w <= 0:
                row.append(None)
                continue
            row.append(dcf_2stage(fcf_0, g1, g, w, shares, net_debt))
        out.append(row)
    return out


def scenario_analysis(fcf_0: float, g_base: float, wacc: float,
                      shares: float, net_debt: Optional[float] = None,
                      g_term: float = 0.02) -> tuple:
    """Bull / base / bear + expected = 0.25 bull + 0.50 base + 0.25 bear.

    Ritorna (bull, base, bear, expected).
    """
    bull = dcf_2stage(fcf_0, g_base + 0.03, g_term, max(0.03, wacc - 0.01),
                      shares, net_debt)
    base = dcf_2stage(fcf_0, g_base, g_term, wacc, shares, net_debt)
    bear = dcf_2stage(fcf_0, max(-0.05, g_base - 0.03), max(0.0, g_term - 0.01),
                      wacc + 0.01, shares, net_debt)
    expected = None
    if base is not None:
        parts, weights = [], []
        if bull is not None:
            parts.append(bull); weights.append(0.25)
        parts.append(base); weights.append(0.50)
        if bear is not None:
            parts.append(bear); weights.append(0.25)
        tot_w = sum(weights)
        expected = round(sum(p * w for p, w in zip(parts, weights)) / tot_w, 2)
    return bull, base, bear, expected


# =============================================================================
# PESI DEI MODELLI PER CLASSE E REGIME (Sez. 7)
# =============================================================================

SECTOR_MODEL_WEIGHTS = {
    "default":     {"graham": 0.20, "ddm": 0.30, "dcf": 0.35, "epv": 0.15},
    "no_dividend": {"graham": 0.25, "ddm": 0.00, "dcf": 0.50, "epv": 0.20},
    "bank":        {"graham": 0.15, "ddm": 0.45, "dcf": 0.20, "epv": 0.20},
    "insurance":   {"graham": 0.15, "ddm": 0.45, "dcf": 0.20, "epv": 0.20},
    "utility":     {"graham": 0.15, "ddm": 0.40, "dcf": 0.30, "epv": 0.15},
    "cyclical":    {"graham": 0.20, "ddm": 0.20, "dcf": 0.35, "epv": 0.25},
    "tech_growth": {"graham": 0.10, "ddm": 0.00, "dcf": 0.65, "epv": 0.25},
    # Classi dedicate (motori non implementati in regime S, pesi documentati)
    "reit":        {"graham": 0.00, "ddm": 0.50, "dcf": 0.30, "epv": 0.10},
    "bdc":         {"graham": 0.00, "ddm": 0.35, "dcf": 0.40, "epv": 0.15},
    "mlp":         {"graham": 0.00, "ddm": 0.35, "dcf": 0.35, "epv": 0.10},
}


def classify_sector_for_weights(sector: str, industry: str,
                                pays_dividend: bool,
                                fcf_negative: bool) -> str:
    s = (sector or "").lower()
    ind = (industry or "").lower()
    if "real estate" in s or "reit" in ind:
        return "reit"
    if "bank" in ind or ("financial services" in s and "bank" in ind):
        return "bank"
    if "insurance" in ind:
        return "insurance"
    if "utility" in s or "utilities" in s:
        return "utility"
    if "software" in ind or ("technology" in s and fcf_negative):
        return "tech_growth"
    if any(c in s for c in ["energy", "basic materials"]) or "mining" in ind:
        return "cyclical"
    if not pays_dividend:
        return "no_dividend"
    return "default"


def weighted_fair_value(model_fvs: dict,
                        sector_class: str) -> tuple[Optional[float], dict, dict]:
    """Media ponderata dei fair value + robustezza valutativa (Sez. 7).

    Ritorna (fair_value, pesi_normalizzati, info_dispersione).
    Dispersione < 15% pesi standard; 15-30% media; > 30% riduci peso outlier
    + red flag di processo. Non tocca MoS ne' CS.
    """
    weights = SECTOR_MODEL_WEIGHTS.get(
        sector_class, SECTOR_MODEL_WEIGHTS["default"]).copy()
    ddm_fv = model_fvs.get("ddm_2stage") or model_fvs.get("ddm_1stage")
    candidates = {
        "graham": model_fvs.get("graham"),
        "ddm": ddm_fv,
        "dcf": model_fvs.get("dcf"),
        "epv": model_fvs.get("epv"),
    }
    avail = {k: v for k, v in candidates.items() if v is not None and v > 0}
    if not avail:
        return None, weights, {"dispersion_pct": None, "flag": "no_models"}

    w_avail = {k: weights[k] for k in avail}
    tot_w = sum(w_avail.values())
    if tot_w == 0:
        return None, weights, {"dispersion_pct": None, "flag": "zero_weights"}
    w_norm = {k: v / tot_w for k, v in w_avail.items()}

    # Robustezza valutativa
    vals = list(avail.values())
    dispersion = None
    flag = "robusta"
    if len(vals) >= 2:
        med = statistics.median(vals)
        if med > 0:
            dispersion = max(abs(v - med) / med for v in vals)
            if dispersion > 0.30:
                flag = "dispersione_alta"
                # riduci il peso dell'outlier piu' distante dalla mediana
                outlier = max(avail, key=lambda k: abs(avail[k] - med))
                if len(avail) > 1:
                    w_norm[outlier] *= 0.5
                    tot = sum(w_norm.values())
                    w_norm = {k: v / tot for k, v in w_norm.items()}
            elif dispersion > 0.15:
                flag = "dispersione_media"

    fv = sum(avail[k] * w_norm[k] for k in avail)
    info = {
        "dispersion_pct": round(dispersion, 4) if dispersion is not None else None,
        "flag": flag,
        "models_used": list(avail.keys()),
    }
    return round(fv, 2), w_norm, info


# =============================================================================
# VARIATION % 5Y (fallback 3y)
# =============================================================================

def compute_variation_pct(series: list[Optional[float]],
                          min_years: int = 3) -> tuple[Optional[float], int]:
    """Variazione % tra primo e ultimo valore. Serie dal piu' recente."""
    if not series or len(series) < min_years:
        return None, 0
    clean = [v for v in series if v is not None and not math.isnan(v)]
    if len(clean) < min_years:
        return None, 0
    n = min(5, len(clean))
    latest, oldest = clean[0], clean[n - 1]
    if oldest == 0:
        return None, 0
    return round((latest - oldest) / abs(oldest), 4), n


def compute_cagr(series: list[Optional[float]],
                 min_years: int = 3) -> tuple[Optional[float], int]:
    """CAGR su serie ordinata dal piu' recente al piu' vecchio.

    Mai sotto 3 anni: se non raggiungibile, ritorna None (Sez. 3A).
    """
    if not series:
        return None, 0
    clean = [v for v in series if v is not None and not math.isnan(v)]
    if len(clean) < min_years:
        return None, 0
    n = min(5, len(clean))
    latest, oldest = clean[0], clean[n - 1]
    periods = n - 1
    if periods <= 0 or oldest is None or oldest <= 0 or latest <= 0:
        return None, 0
    return round((latest / oldest) ** (1 / periods) - 1, 4), n


# =============================================================================
# METRICHE A BANDE (Sez. 3 B-bis)
# =============================================================================

def eps_growth_band(cagr: Optional[float],
                    net_income_flat_or_down: bool = False) -> Optional[float]:
    """EPS Growth, peso 10. Ritorna frazione del peso [0,1].

    MODIFICATORE QUALITA': EPS che cresce molto piu' del net income per
    riduzione dello share count (buyback) con NI piatto/in calo -> cap 50%.
    """
    if cagr is None:
        return None
    if cagr > 0.15:
        frac = 1.00
    elif cagr > 0.10:
        frac = 0.80
    elif cagr > 0.05:
        frac = 0.60
    elif cagr >= 0:
        frac = 0.35
    else:
        frac = 0.0
    if net_income_flat_or_down and frac > 0.50:
        frac = 0.50   # financial engineering
    return frac


def fcf_per_share_growth_band(cagr: Optional[float],
                              fcf_aggregate_flat_or_down: bool = False
                              ) -> Optional[float]:
    """FCF per Share Growth, peso 18. Ritorna frazione del peso [0,1].

    GUARD ANTI-DILUIZIONE/BUYBACK: FCF/share che cresce molto piu' del FCF
    aggregato per riduzione dello share count con FCF aggregato piatto o in
    calo -> cap 50%.
    """
    if cagr is None:
        return None
    if cagr > 0.12:
        frac = 1.00
    elif cagr > 0.08:
        frac = 0.80
    elif cagr > 0.04:
        frac = 0.60
    elif cagr >= 0:
        frac = 0.35
    else:
        frac = 0.0
    if fcf_aggregate_flat_or_down and frac > 0.50:
        frac = 0.50
    return frac


def multiple_expansion_band(pe_current: Optional[float],
                            pe_historical_median: Optional[float],
                            pe_peer_median: Optional[float],
                            eps_stable_or_growing: bool,
                            fundamentals_deteriorating: bool = False
                            ) -> Optional[float]:
    """Multiple Expansion/Contraction (Delta P/E), peso 5.

    Direzione VALUE: la contrazione e' premiata, l'espansione forte
    penalizzata. VALUE-TRAP GUARD: multiplo contratto per fondamentali in
    deterioramento -> max 25%.
    """
    if pe_current is None or pe_current <= 0:
        return None
    ref = [v for v in (pe_historical_median, pe_peer_median)
           if v is not None and v > 0]
    if not ref:
        return None
    below_all = all(pe_current < v for v in ref)
    above_all = all(pe_current > v for v in ref)

    if below_all and eps_stable_or_growing:
        frac = 1.00
    elif above_all:
        frac = 0.0
    else:
        frac = 0.50

    if fundamentals_deteriorating and frac > 0.25:
        frac = 0.25   # value-trap guard
    return frac


def moat_proxy_score(operating_margin: Optional[float],
                     roic: Optional[float],
                     gross_margin: Optional[float],
                     economic_spread: Optional[float],
                     margin_stability: Optional[float] = None) -> Optional[float]:
    """DEVIAZIONE REGIME S — proxy del MOAT su scala 0-10.

    La specifica (Sez. 3A) impone il moat economico Morningstar, dato a
    licenza. In regime S si usa un proxy da fondamentali. Va sempre
    dichiarato come deviazione: NON e' il moat Morningstar.

    Ancoraggio: none=0 / narrow=6 / wide=12 nella scala IQI A4, qui 0-10.
    """
    signals = 0.0
    n = 0
    if operating_margin is not None:
        n += 1
        if operating_margin > 0.25:
            signals += 3.0
        elif operating_margin > 0.15:
            signals += 2.0
        elif operating_margin > 0.08:
            signals += 1.0
    if roic is not None:
        n += 1
        if roic > 0.20:
            signals += 3.0
        elif roic > 0.12:
            signals += 2.0
        elif roic > 0.08:
            signals += 1.0
    if gross_margin is not None:
        n += 1
        if gross_margin > 0.50:
            signals += 2.0
        elif gross_margin > 0.35:
            signals += 1.0
    if economic_spread is not None:
        n += 1
        if economic_spread > 0.05:
            signals += 2.0
        elif economic_spread > 0:
            signals += 1.0
    if n == 0:
        return None
    score = min(10.0, signals)
    if margin_stability is not None and margin_stability < 0.5 and score > 2:
        score -= 1.0   # margini instabili: moat meno credibile
    return round(score, 1)


# =============================================================================
# SCORING MVF v4.1 — BASE 280 -> VOTO /1000
# =============================================================================

def normalize_metric(value: Optional[float], target: float,
                     inverted: bool = False) -> float:
    """Normalizza una metrica su [0, 1] rispetto al target.

    Il target e' il valore OTTIMALE: raggiungerlo vale punteggio pieno.
    (In v3.0 il rapporto era diviso per 2, quindi il target valeva 0.5 e un
    titolo eccellente arrivava a ~570/1000. Su quella scala il Voto non era
    commensurabile con l'IQI e la riconciliazione Delta = Voto/10 - IQI
    (Sez. 7) segnalava "value trap" su qualunque titolo di qualita'.)

    Coerente con le metriche a bande, dove il superamento della soglia
    eccellente vale il 100% del peso.
    """
    if value is None:
        return 0.0
    if inverted:
        if value <= 0:
            return 0.0
        ratio = target / value
    else:
        ratio = value / target if target > 0 else 0
    return max(0.0, min(1.0, ratio))


def compute_mvf_score(metrics: dict, has_dividend: bool, ddm_used: bool,
                      altman_z: Optional[float],
                      economic_spread_neg_2y: bool,
                      instrument_class: str = "common",
                      altman_exempt: bool = False,
                      banded_fractions: Optional[dict] = None
                      ) -> tuple[float, dict]:
    """Voto MVF su base 280 normalizzato a /1000 (Sez. 3).

    banded_fractions: frazioni [0,1] gia' calcolate per le metriche a bande
    (eps_growth, fcf_per_share_growth, multiple_expansion). Se una manca, la
    metrica viene esclusa dal totale invece di contare zero: un dato assente
    non e' un dato negativo.

    Ritorna (voto_1000, breakdown).
    """
    if instrument_class != "common":
        return 0.0, {
            "_error": f"motore common non applicabile a classe '{instrument_class}'",
            "_instrument_class": instrument_class,
        }

    weights = dict(MVF_WEIGHTS_COMMON)
    banded = banded_fractions or {}
    regime_notes = []

    # Sez. 3E — azienda senza dividendo: i 36 punti si redistribuiscono
    if not has_dividend:
        weights["dividend_yield"] = 0
        weights["payout_ratio"] = 0
        weights["dividend_growth_5y"] = 0
        weights["fcf_margin"] += 10      # 12 -> 22
        weights["buyback_yield"] += 10   # 5 -> 15
        weights["price_cagr_5y"] += 8    # 5 -> 13
        weights["roic"] += 8             # 15 -> 23
        regime_notes.append("senza_dividendo: 36 pt redistribuiti")
    # Sez. 3F — doppia ponderazione: DDM applicato -> dimezza pesi dividendi
    elif ddm_used:
        weights["dividend_yield"] = 8
        weights["payout_ratio"] = 5
        weights["dividend_growth_5y"] = 5
        weights["fcf_margin"] += 10      # 12 -> 22
        weights["net_margin"] += 8       # 18 -> 26
        regime_notes.append("DDM_attivo: pesi dividendi dimezzati, 18 pt redistribuiti")

    # Altman-Z non applicabile a settori esenti
    if altman_exempt:
        weights["altman_z"] = 0
        regime_notes.append("altman_z: settore esente, peso azzerato")

    raw = 0.0
    total_weight = 0.0
    breakdown = {}

    for name, w in weights.items():
        if w == 0:
            continue
        if name in MVF_BANDED:
            frac = banded.get(name)
            if frac is None:
                continue   # dato assente: escluso dal totale, non penalizzato
            n = frac
            val = banded.get(f"{name}_raw")
        else:
            target = MVF_TARGETS.get(name, 1.0)
            inverted = name in MVF_INVERTED
            val = metrics.get(name)
            if val is None:
                continue   # coerenza con le bande: assente != zero
            n = normalize_metric(val, target, inverted)
        raw += w * n
        total_weight += w
        breakdown[name] = {"weight": w, "value": val, "norm": round(n, 3)}

    if total_weight == 0:
        return 0.0, {"_error": "nessuna metrica disponibile"}

    # Normalizzazione: (punteggio grezzo / BASE) x 1000, riscalata sul peso
    # effettivamente disponibile per non penalizzare i dati mancanti.
    score_raw_1000 = (raw / total_weight) * 1000
    coverage = total_weight / sum(MVF_WEIGHTS_COMMON.values())

    # Sez. 3D — penalita' Altman-Z ADDITIVA sul voto normalizzato
    penalty = 0.0
    if not altman_exempt and altman_z is not None:
        if altman_z < 1.23:
            penalty = -0.20
            breakdown["_altman_penalty"] = "-20% (zona pericolo)"
        elif altman_z < 1.81:
            penalty = -0.10
            breakdown["_altman_penalty"] = "-10% (zona grigia)"
    if economic_spread_neg_2y:
        penalty -= 0.10
        breakdown["_economic_spread_penalty"] = "-10% (ROIC<WACC 2y)"

    score_final = max(0.0, min(1000.0, score_raw_1000 * (1 + penalty)))

    breakdown["_raw_score_1000"] = round(score_raw_1000, 1)
    breakdown["_total_penalty_pct"] = round(penalty * 100, 1)
    breakdown["_base"] = INSTRUMENT_BASES["common"]
    breakdown["_weight_coverage"] = round(coverage, 3)
    breakdown["_regime_notes"] = regime_notes
    breakdown["_mvf_version"] = MVF_VERSION
    return round(score_final, 1), breakdown


# =============================================================================
# IQI — INDICE DI QUALITA' DELL'INVESTIMENTO (Sez. 7)
# =============================================================================

def _band(value: Optional[float], thresholds: list[tuple[float, float]],
          default: float = 0.0) -> float:
    """Applica una scala a soglie decrescenti. thresholds: [(soglia, frazione)]."""
    if value is None:
        return default
    for thr, frac in thresholds:
        if value >= thr:
            return frac
    return 0.0


def compute_iqi(metrics: dict,
                altman_z: Optional[float],
                economic_spread: Optional[float],
                wacc: Optional[float],
                moat_0_10: Optional[float],
                dividend_years: Optional[int],
                has_buyback: bool,
                fcf_series: Optional[list] = None,
                margin_series: Optional[list] = None,
                pe_current: Optional[float] = None,
                pe_historical_median: Optional[float] = None,
                pe_peer_median: Optional[float] = None,
                tsr_forward: Optional[float] = None,
                growth_expected: Optional[float] = None,
                growth_from_buyback: bool = False,
                interest_coverage: Optional[float] = None,
                net_debt_ebitda: Optional[float] = None,
                altman_exempt: bool = False,
                forward_is_estimate: bool = True) -> IQIScore:
    """IQI = 0.40 x Blocco A (Solidita') + 0.60 x Blocco B (Prospettive).

    DEVIAZIONE REGIME S: B1 e B4 dovrebbero venire da guidance [G] o
    consensus [C]. Qui sono derivati da serie storiche e taggati [S]; si
    applica il cap combinato al 50% previsto dalla specifica per quel caso.
    """
    iqi = IQIScore()
    notes = []

    # ---------------------------------------------------------------- BLOCCO A
    # A1 Patrimoniale (max 30): leva 12 | liquidita' 6 | coperture 6 | attivo 6
    a1 = 0.0
    de = metrics.get("debt_to_equity")
    da = metrics.get("debt_to_assets")
    lev_pts = 0.0
    lev_n = 0
    if de is not None:
        lev_n += 1
        lev_pts += _band(-de, [(-0.5, 1.0), (-1.0, 0.8), (-2.0, 0.5), (-3.0, 0.2)])
    if da is not None:
        lev_n += 1
        lev_pts += _band(-da, [(-0.2, 1.0), (-0.35, 0.8), (-0.5, 0.5), (-0.7, 0.2)])
    if net_debt_ebitda is not None:
        lev_n += 1
        lev_pts += _band(-net_debt_ebitda,
                         [(-1.0, 1.0), (-2.5, 0.8), (-3.5, 0.5), (-4.5, 0.2)])
    a1 += (lev_pts / lev_n) * 12 if lev_n else 6.0

    ccr = metrics.get("earnings_quality")
    a1 += _band(ccr, [(1.0, 1.0), (0.8, 0.75), (0.5, 0.5)]) * 6 if ccr is not None else 3.0

    if interest_coverage is not None:
        a1 += _band(interest_coverage, [(8, 1.0), (4, 0.8), (2.5, 0.6), (1.5, 0.3)]) * 6
    else:
        a1 += 3.0

    if altman_exempt:
        a1 += 3.0   # neutro: Altman non applicabile alla classe
        notes.append("A1: Altman-Z non applicabile (settore esente), punti neutri")
    elif altman_z is not None:
        a1 += _band(altman_z, [(3.0, 1.0), (2.6, 0.8), (1.81, 0.5), (1.23, 0.2)]) * 6
    else:
        a1 += 3.0
    iqi.a1_patrimoniale = round(min(30.0, a1), 1)

    # A2 Reddituale (max 25): livello margini 8 | stabilita' 7 | ROIC+spread 10
    a2 = 0.0
    om = metrics.get("operating_margin")
    nm = metrics.get("net_margin")
    lvl = []
    if om is not None:
        lvl.append(_band(om, [(0.25, 1.0), (0.15, 0.8), (0.08, 0.5), (0.03, 0.25)]))
    if nm is not None:
        lvl.append(_band(nm, [(0.15, 1.0), (0.10, 0.8), (0.05, 0.5), (0.01, 0.25)]))
    a2 += (sum(lvl) / len(lvl)) * 8 if lvl else 4.0

    if margin_series:
        clean = [v for v in margin_series if v is not None]
        if len(clean) >= 3:
            mean_m = statistics.mean(clean)
            if mean_m and abs(mean_m) > 1e-9:
                cv = statistics.pstdev(clean) / abs(mean_m)
                a2 += _band(-cv, [(-0.15, 1.0), (-0.30, 0.75), (-0.50, 0.5),
                                  (-0.80, 0.25)]) * 7
            else:
                a2 += 3.5
        else:
            a2 += 3.5
    else:
        a2 += 3.5

    roic = metrics.get("roic")
    roic_pts = _band(roic, [(0.20, 1.0), (0.12, 0.8), (0.08, 0.5), (0.04, 0.25)]) \
        if roic is not None else 0.5
    spread_pts = 0.5
    if economic_spread is not None:
        spread_pts = _band(economic_spread,
                           [(0.05, 1.0), (0.02, 0.8), (0.0, 0.5)])
    a2 += ((roic_pts + spread_pts) / 2) * 10
    iqi.a2_reddituale = round(min(25.0, a2), 1)

    # A3 Cassa (max 30): FCF margin 8 | costanza 7 | conversione+EQ 8 | copertura 7
    a3 = 0.0
    fcfm = metrics.get("fcf_margin")
    a3 += _band(fcfm, [(0.15, 1.0), (0.10, 0.8), (0.05, 0.5), (0.01, 0.25)]) * 8 \
        if fcfm is not None else 4.0

    if fcf_series:
        clean = [v for v in fcf_series if v is not None]
        if len(clean) >= 3:
            pos = sum(1 for v in clean if v > 0) / len(clean)
            a3 += pos * 7
        else:
            a3 += 3.5
    else:
        a3 += 3.5

    accr = metrics.get("accruals_ratio")
    eq_pts = []
    if ccr is not None:
        eq_pts.append(_band(ccr, [(1.0, 1.0), (0.8, 0.75), (0.5, 0.5)]))
    if accr is not None:
        eq_pts.append(_band(-accr, [(-0.02, 1.0), (-0.05, 0.8), (-0.10, 0.5)]))
    a3 += (sum(eq_pts) / len(eq_pts)) * 8 if eq_pts else 4.0

    payout = metrics.get("payout_ratio")
    capex_rev = metrics.get("capex_revenue")
    if payout is not None or capex_rev is not None:
        drain = (payout or 0) * 0.6 + (capex_rev or 0) * 2
        a3 += _band(-drain, [(-0.3, 1.0), (-0.6, 0.75), (-0.9, 0.5), (-1.2, 0.25)]) * 7
    else:
        a3 += 3.5
    iqi.a3_cassa = round(min(30.0, a3), 1)

    # A4 Competitiva (max 15): moat 12 | trend + capital allocation 3
    a4 = 0.0
    if moat_0_10 is not None:
        # ancoraggio specifica: none 0 / narrow 6 / wide 12 su 12 punti
        a4 += min(12.0, (moat_0_10 / 10.0) * 12.0)
        notes.append("A4: moat da proxy fondamentali, NON Morningstar (deviazione regime S)")
    else:
        a4 += 4.0
    # Capital allocation non valutabile in regime S: punti neutri
    a4 += 1.5
    notes.append("A4: capital allocation non valutabile in regime S, punti neutri")
    iqi.a4_competitiva = round(min(15.0, a4), 1)

    iqi.blocco_a = round(iqi.a1_patrimoniale + iqi.a2_reddituale
                         + iqi.a3_cassa + iqi.a4_competitiva, 1)

    # ---------------------------------------------------------------- BLOCCO B
    # Tier dividendo -> modula B1 e B2 (somma fissa 70)
    if dividend_years is not None and dividend_years >= 10:
        tier, b1_max, b2_max = "forte", 25.0, 45.0
    elif dividend_years is not None and dividend_years >= 5:
        tier, b1_max, b2_max = "solido", 32.0, 38.0
    elif dividend_years is not None and dividend_years > 0:
        tier, b1_max, b2_max = "nascente", 55.0, 15.0
    elif has_buyback:
        tier, b1_max, b2_max = "buyback", 45.0, 25.0
    else:
        tier, b1_max, b2_max = "nessuna", 70.0, 0.0
    iqi.dividend_tier = tier
    iqi.b1_max = b1_max
    iqi.b2_max = b2_max

    # B1 Crescita attesa
    b1_frac = _band(growth_expected,
                    [(0.15, 1.0), (0.10, 0.8), (0.05, 0.6), (0.0, 0.35)]) \
        if growth_expected is not None else 0.35
    if growth_from_buyback and b1_frac > 0.50:
        b1_frac = 0.50
        notes.append("B1: cap 50% (crescita da buyback con NI piatto)")
    iqi.b1_crescita = round(b1_max * b1_frac, 1)

    # B2 Remunerazione
    if b2_max > 0:
        dy = metrics.get("dividend_yield")
        dg = metrics.get("dividend_growth_5y")
        checks = 0
        if dy is not None and dy >= 0.025:
            checks += 1
        if dg is not None and dg >= 0.05:
            checks += 1
        if payout is not None and payout <= 0.70:
            checks += 1
        if fcfm is not None and dy is not None and fcfm > 0:
            checks += 1
        b2_frac = {4: 1.0, 3: 0.75, 2: 0.50, 1: 0.25}.get(checks, 0.10)
        if payout is not None and payout > 1.0:
            b2_frac = min(b2_frac, 0.25)
            notes.append("B2: payout > 100%, remunerazione a rischio")
        iqi.b2_remunerazione = round(b2_max * b2_frac, 1)
    else:
        iqi.b2_remunerazione = 0.0

    # B3 Posizionamento multiplo (max 15)
    b3_frac = 0.5
    ref = [v for v in (pe_historical_median, pe_peer_median)
           if v is not None and v > 0]
    if pe_current is not None and pe_current > 0 and ref:
        if all(pe_current < v for v in ref):
            b3_frac = 1.0
        elif all(pe_current > v for v in ref):
            b3_frac = 0.2
    iqi.b3_multiplo = round(15.0 * b3_frac, 1)

    # B4 TSR forward (max 15)
    b4_frac = _band(tsr_forward, [(0.12, 1.0), (0.08, 0.70), (0.04, 0.40)],
                    default=0.10) if tsr_forward is not None else 0.40
    iqi.b4_tsr_forward = round(15.0 * b4_frac, 1)

    # MODIFICATORE AFFIDABILITA' FORWARD (Sez. 7): B1+B4 prevalentemente [S]
    if forward_is_estimate:
        combined = iqi.b1_crescita + iqi.b4_tsr_forward
        cap = (b1_max + 15.0) * 0.50
        if combined > cap:
            scale = cap / combined
            iqi.b1_crescita = round(iqi.b1_crescita * scale, 1)
            iqi.b4_tsr_forward = round(iqi.b4_tsr_forward * scale, 1)
            iqi.forward_capped = True
            notes.append(
                "B1+B4 da stime storiche [S]: cap combinato al 50% "
                "(convinzione max 'Media')")

    iqi.blocco_b = round(iqi.b1_crescita + iqi.b2_remunerazione
                         + iqi.b3_multiplo + iqi.b4_tsr_forward, 1)

    iqi.total = round(0.40 * iqi.blocco_a + 0.60 * iqi.blocco_b, 1)
    iqi.notes = notes
    return iqi


# =============================================================================
# CONFIDENCE SCORE — RICALIBRATO PER REGIME S (Sez. 10)
# =============================================================================

# TAGGING DELLA FONTE IN REGIME S
#
# Decisione di progetto: yfinance e' classificato [V] (validato), non [U].
# Motivazione: i fondamentali che espone provengono dai filing depositati e
# passano per una normalizzazione dell'aggregatore; non sono una fonte
# singola non verificata nel senso della Sez. 6-bis C. Non sono pero' [P]:
# non c'e' lettura diretta di XBRL/IR e le note al bilancio non sono
# accessibili.
#
# Sulla scala della specifica (sub-score A per quota [P]: >=80% -> 22-25,
# 60-79% -> 17-21, 40-59% -> 11-16) una base interamente [V] senza [P] si
# colloca nella fascia 60-79%: cap 18/25. Con un secondo riscontro
# indipendente concorde sale a 21/25 (alto della fascia).
#
# Il gate resta equivalente al 50/100 della specifica, riscalato sul massimo
# effettivamente raggiungibile. In regime A (DIP su EDGAR) vanno ripristinati
# PROVENANCE_CAP_V = 25 e il gate a 50.
PROVENANCE_CAP_V = 18.0            # yfinance da solo: [V] senza riscontro
PROVENANCE_CAP_V_CROSSCHECKED = 21.0   # [V] con seconda fonte concorde
PROVENANCE_CAP_U = 10.0            # fallback se la fonte degrada a [U]

_SPEC_GATE_ON_100 = 50.0           # soglia di gate della specifica


def _gate_threshold(provenance_cap: float) -> float:
    """Gate riscalato sul massimo raggiungibile con il cap di provenienza."""
    max_reachable = provenance_cap + 75.0
    return round(_SPEC_GATE_ON_100 * max_reachable / 100.0, 1)


# Compatibilita' con i chiamanti precedenti
PROVENANCE_CAP_REGIME_S = PROVENANCE_CAP_V
CS_GATE_REGIME_S = _gate_threshold(PROVENANCE_CAP_V)


def compute_confidence_score(data_completeness_pct: float,
                             fcf_series: list,
                             sector: str,
                             model_fvs: list,
                             has_quality_audit: bool = True,
                             fiscal_year_age_days: Optional[int] = None,
                             internal_coherence_ok: Optional[bool] = None,
                             source_tag: str = "V",
                             cross_checked: bool = False,
                             cross_check_agrees: Optional[bool] = None
                             ) -> ConfidenceScore:
    """4 sub-score 0-25 -> totale 0-100, su scala di regime S.

    source_tag: "V" (default, yfinance) | "U" (fonte degradata) | "P".
    cross_checked / cross_check_agrees: esito del riscontro con una seconda
    fonte indipendente. Un riscontro DISCORDE abbassa la provenienza sotto il
    livello di partenza: due fonti che si contraddicono valgono meno di una
    sola non verificata (Sez. 6-bis C, conflitto material -> [U]).
    """
    cs = ConfidenceScore()
    notes = []

    # A. Provenienza / autorevolezza
    if source_tag == "P":
        cap = 25.0
        notes.append("fonte [P] primaria")
    elif source_tag == "U":
        cap = PROVENANCE_CAP_U
        notes.append("fonte [U] non validata")
    else:
        if cross_checked and cross_check_agrees is True:
            cap = PROVENANCE_CAP_V_CROSSCHECKED
            notes.append("fonte [V] con riscontro indipendente concorde")
        elif cross_checked and cross_check_agrees is False:
            cap = PROVENANCE_CAP_U
            notes.append(
                "riscontro DISCORDE: conflitto material -> degradata a [U] "
                "(Sez. 6-bis C)")
        else:
            cap = PROVENANCE_CAP_V
            notes.append("fonte [V] da aggregatore, nessun riscontro incrociato")

    a = cap
    if not has_quality_audit:
        a *= 0.7
        notes.append("dati non auditati: -30% sub-A")
    cs.provenance = round(a, 1)
    cs._provenance_cap = cap

    # B. Completezza / copertura
    b = max(0.0, min(25.0, data_completeness_pct * 25))
    cs.completeness = round(b, 1)

    # C. Puntualita'
    if fiscal_year_age_days is None:
        c = 15.0
    elif fiscal_year_age_days <= 120:
        c = 25.0
    elif fiscal_year_age_days <= 240:
        c = 20.0
    elif fiscal_year_age_days <= 400:
        c = 14.0
    else:
        c = 7.0
        notes.append("ultimo esercizio oltre 400 giorni: dato stantio")
    cs.timeliness = round(c, 1)

    # D. Coerenza — in regime S non c'e' cross-validation multi-fonte:
    #    si usa la coerenza interna dei dati disponibili.
    d = 12.5
    clean_fcf = [v for v in (fcf_series or []) if v is not None]
    if len(clean_fcf) >= 3:
        d += 4.0
    if internal_coherence_ok is True:
        d += 6.0
    elif internal_coherence_ok is False:
        d -= 6.0
        notes.append("incoerenze interne rilevate nei dati di bilancio")
    cs.coherence = round(max(0.0, min(25.0, d)), 1)

    cs.total = round(cs.provenance + cs.completeness
                     + cs.timeliness + cs.coherence, 1)
    cs.gate_threshold = _gate_threshold(cap)
    cs.gate_active = cs.total < cs.gate_threshold

    # Lettura riscalata sul massimo raggiungibile con questo cap
    max_reachable = cap + 75.0
    pct = cs.total / max_reachable if max_reachable else 0
    if cs.gate_active:
        cs.reading = "Insufficiente"
    elif pct >= 0.80:
        cs.reading = "Alta"
    elif pct >= 0.65:
        cs.reading = "Media"
    else:
        cs.reading = "Bassa"

    # La riscalatura sul massimo raggiungibile non deve mascherare una
    # provenienza degradata: completezza e coerenza alte non compensano una
    # fonte in conflitto. Con cap [U] la lettura non supera "Media".
    if cap <= PROVENANCE_CAP_U and cs.reading == "Alta":
        cs.reading = "Media"
        notes.append("lettura limitata a 'Media': provenienza [U]")

    cs.source_tag = source_tag if not (
        source_tag == "V" and cap <= PROVENANCE_CAP_U) else "U"
    cs.notes = notes
    return cs


# =============================================================================
# GATE DI ESCLUSIONE QUALITA' G1-G6 (Sez. 8-bis)
# =============================================================================

# Settori leveraged-by-design: esenti da G3 (leva) e G5 (Altman)
LEVERAGED_BY_DESIGN = {"reit", "bank", "insurance", "utility", "bdc", "mlp"}


def evaluate_quality_gates(fcf_series: Optional[list],
                           economic_spread_history: Optional[list],
                           economic_spread: Optional[float],
                           net_debt_ebitda: Optional[float],
                           net_debt_ebitda_rising: bool,
                           interest_coverage: Optional[float],
                           share_dilution_3y: Optional[float],
                           sbc_revenue: Optional[float],
                           altman_z: Optional[float],
                           sector_class: str,
                           second_signal: bool = False,
                           is_saas_growth: bool = False,
                           normalized_fcf_mean: Optional[float] = None
                           ) -> QualityGates:
    """Gate G1-G6: NO-BUY strutturale a prescindere da prezzo, MoS e IQI.

    REGOLA TRASVERSALE: conferma multi-segnale — nessun segnale isolato con
    storia di falsi positivi esclude da solo.
    """
    g = QualityGates()
    exempt = sector_class in LEVERAGED_BY_DESIGN

    # G1 — Distruzione di cassa strutturale: FCF negativo in tutti gli ultimi 5y
    clean_fcf = [v for v in (fcf_series or []) if v is not None]
    if len(clean_fcf) >= 5 and all(v < 0 for v in clean_fcf[:5]):
        if is_saas_growth:
            g.details["g1"] = "FCF negativo 5y ma SaaS growth: gate non applicato (Sez. 9E)"
        else:
            g.g1_cash_destruction = True
            g.details["g1"] = f"FCF negativo in tutti gli ultimi 5 anni: {clean_fcf[:5]}"
    elif normalized_fcf_mean is not None and normalized_fcf_mean < 0 and len(clean_fcf) >= 5:
        g.g1_cash_destruction = True
        g.details["g1"] = "media FCF normalizzata negativa (ciclico)"

    # G2 — Distruzione di valore persistente: ROIC-WACC < 0 per >= 4 anni
    hist = [v for v in (economic_spread_history or []) if v is not None]
    if len(hist) >= 4 and all(v < 0 for v in hist[:4]):
        g.g2_value_destruction = True
        g.details["g2"] = "ROIC-WACC negativo per 4+ anni normalizzati"
    elif len(hist) < 4:
        g.not_evaluable.append("G2 (storico spread ROIC-WACC < 4 anni)")

    # G3 — Leva fuori scala non servita (settori esenti: leveraged-by-design)
    if exempt:
        g.not_evaluable.append(f"G3 (settore '{sector_class}' leveraged-by-design)")
    elif (net_debt_ebitda is not None and net_debt_ebitda > 4.5
          and net_debt_ebitda_rising
          and interest_coverage is not None and interest_coverage < 1.5):
        g.g3_leverage_unserviced = True
        g.details["g3"] = (f"Net Debt/EBITDA {net_debt_ebitda:.1f}x in aumento "
                           f"con copertura interessi {interest_coverage:.1f}x")

    # G4 — Trasferimento valore dall'azionista: diluizione > 5%/anno 3y E SBC > 8%
    if (share_dilution_3y is not None and share_dilution_3y > 0.05
            and sbc_revenue is not None and sbc_revenue > 0.08):
        g.g4_shareholder_transfer = True
        g.details["g4"] = (f"diluizione {share_dilution_3y:.1%}/anno con "
                           f"SBC/Revenue {sbc_revenue:.1%}")

    # G5 — Insolvenza tecnica confermata: Altman < 1.23 + secondo segnale
    if exempt:
        g.not_evaluable.append(f"G5 (settore '{sector_class}' esente da Altman-Z)")
    elif altman_z is not None and altman_z < 1.23:
        if second_signal:
            g.g5_technical_insolvency = True
            g.details["g5"] = f"Altman-Z {altman_z:.2f} + secondo segnale confermato"
        else:
            g.details["g5"] = (f"Altman-Z {altman_z:.2f} sotto soglia ma senza "
                               f"secondo segnale: gate non attivato "
                               f"(conferma multi-segnale)")

    # G6 — Capital allocation distruttiva: non valutabile senza fonte qualitativa
    g.not_evaluable.append("G6 (capital allocation: richiede regime A)")

    g.active = [k.split("_")[0].upper() for k, v in asdict(g).items()
                if isinstance(v, bool) and v and k.startswith("g")]
    return g


# =============================================================================
# MARGINE DI SICUREZZA — CATENA IQI -> BASE, CS -> OVERLAY (Sez. 7)
# =============================================================================

MOS_CAP = 0.60
IQI_ABSTAIN_THRESHOLD = 30.0


def mos_base_from_iqi(iqi_total: Optional[float]) -> tuple[Optional[float], str]:
    """PASSO 1 — MoS base dall'IQI. Ritorna (mos, nota); None = astensione."""
    if iqi_total is None:
        return 0.45, "IQI non calcolabile: MoS prudenziale 45%"
    if iqi_total < IQI_ABSTAIN_THRESHOLD:
        return None, f"IQI {iqi_total:.0f} < 30: ASTENSIONE"
    if iqi_total >= 90:
        return 0.15, ""
    if iqi_total >= 80:
        return 0.20, ""
    if iqi_total >= 70:
        return 0.25, ""
    if iqi_total >= 60:
        return 0.30, ""
    if iqi_total >= 50:
        return 0.35, ""
    if iqi_total >= 40:
        return 0.45, ""
    return 0.55, ""


def mos_overlay_from_cs(cs: ConfidenceScore) -> tuple[Optional[float], str]:
    """PASSO 2 — Overlay dal Confidence Score. None = gate, non azionabile."""
    if cs.gate_active:
        return None, (f"CS {cs.total:.0f} < {cs.gate_threshold:.0f} "
                      f"(soglia regime {cs.regime}): GATE, non azionabile")
    max_reachable = PROVENANCE_CAP_REGIME_S + 75.0
    pct = cs.total / max_reachable if max_reachable else 0
    if pct >= 0.80:
        return 0.0, ""
    if pct >= 0.65:
        return 0.05, ""
    return 0.10, "CS basso: overlay +10% con warning"


def compute_final_mos(iqi: Optional[IQIScore],
                      cs: ConfidenceScore,
                      gates: Optional[QualityGates] = None
                      ) -> tuple[Optional[float], dict]:
    """MoS_finale = MoS_base(IQI) + overlay(CS), con cap e astensioni.

    Ritorna (mos_finale, dettaglio). mos None = non azionabile.
    """
    detail = {"mos_base": None, "overlay": None, "abstain": False,
              "reason": "", "notes": []}

    if gates is not None and gates.is_blocked:
        detail["abstain"] = True
        detail["reason"] = f"GATE DI QUALITA' attivo: {', '.join(gates.active)} — NO-BUY strutturale"
        return None, detail

    iqi_total = iqi.total if iqi is not None else None
    base, base_note = mos_base_from_iqi(iqi_total)
    detail["mos_base"] = base
    if base_note:
        detail["notes"].append(base_note)
    if base is None:
        detail["abstain"] = True
        detail["reason"] = base_note
        return None, detail

    overlay, ov_note = mos_overlay_from_cs(cs)
    detail["overlay"] = overlay
    if ov_note:
        detail["notes"].append(ov_note)
    if overlay is None:
        detail["abstain"] = True
        detail["reason"] = ov_note
        return None, detail

    mos = base + overlay
    if mos > MOS_CAP:
        detail["abstain"] = True
        detail["reason"] = f"MoS {mos:.0%} oltre il cap del 60%: ASTENSIONE"
        return None, detail

    detail["notes"].append(f"MoS = {base:.0%} (IQI) + {overlay:.0%} (CS)")
    return round(mos, 4), detail


def margin_of_safety_for_cs(cs_total: float) -> float:
    """Compatibilita' v3.0. Deprecata: in v4.1 il MoS deriva dall'IQI.

    Mantenuta solo per non rompere chiamanti non ancora migrati.
    """
    if cs_total >= 80:
        return 0.30
    if cs_total >= 70:
        return 0.40
    return 0.50


def ideal_purchase_price(fair_value: Optional[float],
                         mos: Optional[float]) -> Optional[float]:
    if fair_value is None or fair_value <= 0 or mos is None:
        return None
    return round(fair_value * (1 - mos), 2)


# =============================================================================
# RICONCILIAZIONE VOTO MVF <-> IQI (Sez. 7)
# =============================================================================

def reconcile_mvf_iqi(voto_1000: Optional[float],
                      iqi_total: Optional[float]) -> dict:
    """Delta = (Voto MVF / 10) - IQI. Segnala qualita' cara o value trap."""
    if voto_1000 is None or iqi_total is None:
        return {"delta": None, "verdict": "non_calcolabile", "action": ""}
    delta = round(voto_1000 / 10 - iqi_total, 1)
    if abs(delta) <= 20:
        return {"delta": delta, "verdict": "convergenza",
                "action": "nessun aggiustamento"}
    if delta > 20:
        return {"delta": delta, "verdict": "qualita_cara",
                "action": ("ottimo business a prezzo non attraente: WATCHLIST, "
                           "non forzare Buy")}
    verdict = {"delta": delta, "verdict": "sospetto_value_trap",
               "action": ("scrutinio: Reverse DCF obbligatorio, value-trap guard, "
                          "convinzione -1 livello, MoS +1 scalino")}
    if voto_1000 < 400 and iqi_total < 40:
        verdict["verdict"] = "doppia_debolezza"
        verdict["action"] = "MVF < 400 e IQI < 40: astensione confermata"
    return verdict


# =============================================================================
# FISCALITA' — RENDIMENTO NETTO POST-IMPOSTE (Sez. 7)
# =============================================================================

def compute_net_yield(gross_yield: Optional[float],
                      country: Optional[str],
                      instrument_class: str = "common") -> NetYield:
    """Rendimento netto HOME vs ITALIA per persona fisica residente in Italia,
    regime del risparmio amministrato (Sez. 7).

        Netto HOME   = Yield_lordo x (1 - w_home)
        Netto ITALIA = Yield_lordo x (1 - w_home) x (1 - 0.26)

    Il confronto tra titoli a dividendo si fa sul NETTO ITALIA: e' il
    rendimento realmente incassato. La ritenuta estera in regime amministrato
    in genere NON e' recuperabile.
    """
    ny = NetYield(gross_yield=gross_yield, country=(country or "").upper())
    if gross_yield is None or gross_yield <= 0:
        ny.notes.append("nessuna distribuzione: calcolo non applicabile")
        return ny

    c = (country or "").upper()
    w = WITHHOLDING_TAX.get(c, DEFAULT_WITHHOLDING)

    # Casi speciali US che rompono il treaty rate ordinario
    if c == "US" and instrument_class in SPECIAL_WITHHOLDING_US:
        w = SPECIAL_WITHHOLDING_US[instrument_class]
        ny.special_case = instrument_class
        ny.notes.append(
            f"{instrument_class.upper()} USA: ritenuta {w:.0%} anziche' il 15% "
            f"treaty ordinario")
    if c not in WITHHOLDING_TAX:
        ny.notes.append(
            f"paese '{c or 'ignoto'}' non in tabella: applicato default "
            f"{DEFAULT_WITHHOLDING:.0%}, da verificare")

    ny.withholding_rate = w
    ny.net_home = round(gross_yield * (1 - w), 6)
    ny.net_italy = round(gross_yield * (1 - w) * (1 - IT_DIVIDEND_TAX), 6)
    ny.withholding_drag = round(gross_yield * w, 6)
    ny.italian_tax_drag = round(gross_yield * (1 - w) * IT_DIVIDEND_TAX, 6)
    ny.total_tax_drag = round(gross_yield - ny.net_italy, 6)
    ny.effective_combined_rate = round(1 - (1 - w) * (1 - IT_DIVIDEND_TAX), 4)
    ny.notes.append(
        "valori indicativi: verificare la convenzione vigente prima dell'uso")
    return ny


# =============================================================================
# RED FLAG DETECTOR (Sez. 8)
# =============================================================================

def detect_red_flags(metrics: dict, altman_z: Optional[float],
                     fcf_series: list, net_margin_series: list,
                     economic_spread_neg_2y: bool,
                     goodwill: Optional[float], equity: Optional[float],
                     is_tech: bool, revenue_series: list,
                     accruals: Optional[float], ccr: Optional[float],
                     share_dilution: Optional[float],
                     payout: Optional[float], roe: Optional[float],
                     cost_of_equity: float,
                     working_capital_series: list,
                     eps_growth: Optional[float] = None,
                     fcf_share_growth: Optional[float] = None,
                     multiple_share_of_return: Optional[float] = None,
                     eps_growth_from_buyback: bool = False,
                     forward_is_estimate: bool = False) -> MVFRedFlags:
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
    if len(clean_nm) >= 3 and sum(1 for v in clean_nm[:3] if v < 0) >= 2:
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

    # === v4.x ===
    if (eps_growth is not None and fcf_share_growth is not None
            and eps_growth > 0.05 and fcf_share_growth <= 0.0):
        rf.eps_fcf_divergence = True
    if multiple_share_of_return is not None and multiple_share_of_return > 0.70:
        rf.multiple_expansion_driven = True
    if eps_growth_from_buyback:
        rf.eps_growth_from_buyback = True
    if forward_is_estimate:
        rf.forward_estimates_only = True

    return rf


# =============================================================================
# RETURN ATTRIBUTION (Sez. 7)
# =============================================================================

def return_attribution(price_start: Optional[float], price_end: Optional[float],
                       eps_start: Optional[float], eps_end: Optional[float],
                       avg_dividend_yield: Optional[float] = None) -> dict:
    """Decomposizione log del rendimento: Prezzo = EPS x (P/E).

        ln(P_t/P_0) = ln(EPS_t/EPS_0) + ln(PE_t/PE_0)

    Quota EPS > ~70% -> rendimento "guadagnato", ripetibile.
    Multiple expansion dominante -> sentiment, mean-reverting: alza il MoS.
    """
    out = {"price_return": None, "eps_share": None, "multiple_share": None,
           "tsr": None, "verdict": "", "notes": []}
    if not all(v is not None and v > 0
               for v in (price_start, price_end, eps_start, eps_end)):
        out["notes"].append("dati insufficienti per la decomposizione")
        return out

    r_price = price_end / price_start - 1
    out["price_return"] = round(r_price, 4)
    ln_p = math.log(price_end / price_start)
    if abs(ln_p) < 1e-9:
        out["notes"].append("rendimento nullo: decomposizione non significativa")
        return out

    ln_eps = math.log(eps_end / eps_start)
    pe_start = price_start / eps_start
    pe_end = price_end / eps_end
    ln_pe = math.log(pe_end / pe_start)

    out["eps_share"] = round(ln_eps / ln_p, 4)
    out["multiple_share"] = round(ln_pe / ln_p, 4)
    if avg_dividend_yield:
        out["tsr"] = round(r_price + avg_dividend_yield, 4)

    if out["eps_share"] > 0.70:
        out["verdict"] = "guadagnato"
        out["notes"].append("rendimento trainato dagli utili: ripetibile")
    elif out["multiple_share"] > 0.70:
        out["verdict"] = "multiplo"
        out["notes"].append(
            "rendimento trainato dall'espansione del multiplo: sentiment, "
            "mean-reverting. Rischio de-rating: alzare il MoS")
    else:
        out["verdict"] = "misto"
    return out
