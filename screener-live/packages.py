"""Tag di idoneita' ai pacchetti e badge (calibrazione §10, v1.1).

Prerequisito per ogni tag (tranne All): nessun gate, nessun red flag critico,
copertura >= 75%. Commissioni/fiscalita' NON sono mai sbarranti: producono
segnalazioni, non esclusioni.
"""
from __future__ import annotations

import json
import os

import config


def _themes_overrides() -> dict:
    p = os.path.join(os.path.dirname(__file__), "themes_overrides.json")
    if os.path.exists(p):
        return json.load(open(p))
    return {}


def assign_packages(m: dict, score: dict, iqi_res: dict, gates: list,
                    flags: dict, klass: str) -> dict:
    ctx = m["ctx"]
    mvf = score.get("vote")
    iqi = iqi_res.get("iqi")
    coverage = score.get("coverage", 0)
    tags = ["all"]
    badges = []
    notes = []
    eligible_base = (not gates and not flags.get("critical")
                     and coverage >= config.COVERAGE_MIN and mvf is not None)

    dy = m.get("C19", {}).get("value") or 0
    dg = m.get("C21", {}).get("value")
    incr5 = m.get("C21", {}).get("increases_of5")
    payout = m.get("C20", {}).get("value")
    fm = m.get("C5", {}).get("value")
    de = ctx.get("de")
    beta = ctx.get("beta")
    years = ctx.get("div_years_paid", 0)
    consec = ctx.get("div_consec_increases", 0)
    cut = m.get("C21", {}).get("cut_in_5y")

    # badge storia dividendo
    if consec >= 50:
        badges.append("KING")
    elif consec >= 25:
        badges.append("ARISTOCRAT")

    if eligible_base:
        d = config.DEFENSIVO
        strong_growth = (dg is not None and dg >= d["divcagr_min"]
                         and (incr5 or 0) >= d["increases_of5_min"])
        difensivo = (years >= d["years_paid_min"] and not cut
                     and (dy >= d["yield_min"] or strong_growth)
                     and (payout is None or payout <= d["payout_max"])
                     and (fm is None or fm >= d["fcf_margin_min"])
                     and (de is None or de <= d["de_max"])
                     and (beta is None or beta <= d["beta_max"])
                     and mvf >= d["mvf_min"]
                     and (iqi is None or iqi >= d["iqi_min"]))
        if difensivo:
            tags.append("difensivo")
            months = ctx.get("div_payment_months", [])
            if months:
                tags.append("cedola_mensile_candidato")
                ctx["payment_months"] = months

        c = config.COMPOUNDERS
        roic = m.get("C8", {}).get("value")
        spread = m.get("C8", {}).get("spread")
        fcfps = m.get("C7", {}).get("value")
        dil = m.get("C22", {}).get("value")
        if ((roic is not None and roic >= c["roic_min"])
                or (spread is not None and spread >= c["spread_min"])) \
                and fcfps is not None and fcfps >= c["fcfps_cagr_min"] \
                and (dil is None or dil >= -0.2) and mvf >= c["mvf_min"]:
            tags.append("compounders")

        theme = config.THEME_BY_INDUSTRY.get(ctx.get("industry", ""))
        theme = _themes_overrides().get(ctx["ticker"], theme)
        if theme in config.INNOVATIVE_THEMES and mvf >= config.INNOVATIVO_MVF_MIN:
            rev_ok = (ctx.get("rev_growth_cagr") or 0) >= 10
            rd = m.get("C17", {}).get("value")
            if rev_ok or (rd is not None and rd > 0):
                tags.append("innovativo")
                ctx["theme"] = theme

        if ctx.get("country") in config.EMERGENTI_COUNTRIES \
                and mvf >= config.EMERGENTI_MVF_MIN:
            tags.append("emergenti")

        if ctx.get("country") in config.PIR_COUNTRIES:
            tags.append("pir_candidato")

        ind_l = (ctx.get("industry") or "").lower()
        excluded = any(k in ind_l for k in config.ETICO_EXCLUDED_INDUSTRIES)
        if not excluded:
            tags.append("etico_candidato")
            notes.append("Etico: in attesa di verifica ESG manuale (IBKR)")

    # segnalazioni fiscali/commissionali: mai sbarranti (REVIEW)
    if klass in ("mlp",):
        notes.append("Attrito fiscale ALTO (K-1, ritenuta §1446 fino ~37%)")
    if klass in ("reit", "bdc") and (ctx.get("country") == "United States"):
        notes.append("Ritenuta USA 30% su distribuzioni: confronta sul netto Italia")
    return {"tags": tags, "badges": badges, "notes": notes}


def occasione_badge(score: dict, gates: list, flags: dict,
                    price: float | None, prezzo_ideale: float | None) -> bool:
    """Badge OCCASIONE D'ORO (calibrazione §1/§12)."""
    return (score.get("vote") is not None
            and score["vote"] >= config.OCCASIONE_MVF_MIN
            and not gates and not flags.get("critical")
            and price is not None and prezzo_ideale is not None
            and price <= prezzo_ideale)
