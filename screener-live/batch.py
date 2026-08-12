#!/usr/bin/env python3
"""Batch Regime S — bozza 1.

USO:
    python batch.py --tickers KO JNJ SPCE
    python batch.py --test          # banco di prova (calibrazione §14)

Output: tabella a video + output/screener.db + output/results.json
Classi implementate in bozza 1: common (completa), reit (parziale: le
dedicate da IR non sono ancora reperibili -> copertura bassa dichiarata).
BDC/MLP/preferred: rilevate e marcate "non implementata in bozza 1".
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
import db as dbmod
import fetchers
import fetch_us
import gates as gatesmod
import iqi as iqimod
import metrics as metricsmod
import packages as pkgmod
import scoring
import sector_stats

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger("batch")


def _class_overrides() -> dict:
    p = os.path.join(os.path.dirname(__file__), "class_overrides.json")
    return json.load(open(p)) if os.path.exists(p) else {}


def _moat_overrides() -> dict:
    p = os.path.join(os.path.dirname(__file__), "moat_overrides.json")
    return json.load(open(p)) if os.path.exists(p) else {}


def analyze_one(ticker: str, source: str = "auto") -> dict | None:
    """Fase 1: fetch + metriche + classe. NON fa scoring (serve prima
    calcolare le statistiche di settore sull'universo)."""
    raw = None
    if source in ("auto", "yfinance"):
        raw = fetchers.fetch_yf(ticker)
    if raw is None and source in ("auto", "edgar"):
        raw = fetch_us.build_raw_us(ticker)
        if raw is not None:
            log.info("  %s via EDGAR+stockanalysis (yfinance non disponibile)", ticker)
    if raw is None:
        return None
    if raw.get("_source", "").startswith("edgar"):
        validation = {"tags": {}, "agree_ratio": 1.0, "statement_trust": "P"}
    else:
        edgar = fetchers.fetch_edgar(ticker)
        validation = fetchers.cross_validate(raw, edgar)
    m = metricsmod.compute_metrics(raw, validation)
    klass = metricsmod.detect_class(raw["info"], _class_overrides())
    moat = _moat_overrides().get(ticker.upper())
    if moat:
        m["C26"] = {"value": moat, "series": [], "tag": "V"}
    if klass == "reit":
        m["ctx"]["altman_exempt"] = True
        m["C4"] = {"value": None, "series": [], "tag": "U"}  # informativa nei REIT
    return {"ticker": ticker, "m": m, "klass": klass, "validation": validation}


def score_one(analysis: dict) -> dict:
    """Fase 2: scoring completo (ctx puo' gia' contenere le stat di settore)."""
    ticker, m = analysis["ticker"], analysis["m"]
    klass, validation = analysis["klass"], analysis["validation"]
    if klass in ("bdc", "mlp", "preferred"):
        return {"ticker": ticker, "classe": klass, "status": "classe non "
                "implementata in bozza 1 (motori dedicati in arrivo)",
                "score": {}, "iqi": {}, "cs": {}, "gates": [], "flags":
                {"critical": [], "warning": []}, "packages": {"tags": [],
                "badges": [], "notes": []}}

    fv_res = iqimod.fair_value(m)          # imposta ddm_applied prima dei pesi
    score = scoring.score_common(m)
    gates = gatesmod.evaluate_gates(m)
    flags = gatesmod.evaluate_red_flags(m)
    iqi_res = iqimod.compute_iqi(m)
    cs_res = iqimod.compute_cs(score, validation, m)
    netto = iqimod.netto_italia(m, klass)
    mos_res = iqimod.mos_chain(iqi_res.get("iqi"), cs_res["cs"])
    price = m["ctx"].get("price")
    fv = fv_res.get("fv")
    prezzo_ideale = None
    if fv and mos_res.get("mos") is not None and not gates:
        prezzo_ideale = fv * (1 - mos_res["mos"])
    pkgs = pkgmod.assign_packages(m, score, iqi_res, gates, flags, klass)
    occ = pkgmod.occasione_badge(score, gates, flags, price, prezzo_ideale)
    if occ:
        pkgs["badges"].append("OCCASIONE D'ORO")

    delta = None
    if score.get("vote") is not None and iqi_res.get("iqi") is not None:
        delta = score["vote"] / 10 - iqi_res["iqi"]  # riconciliazione MVF<->IQI

    return {"ticker": ticker, "name": m["ctx"].get("name"),
            "classe": klass, "status": "ok",
            "country": m["ctx"].get("country"), "sector": m["ctx"].get("sector"),
            "industry": m["ctx"].get("industry"),
            "score": score, "iqi": iqi_res, "cs": cs_res,
            "delta_mvf_iqi": round(delta, 1) if delta is not None else None,
            "gates": gates, "flags": flags, "packages": pkgs,
            "netto": netto, "price": price,
            "fair_value": round(fv, 2) if fv else None,
            "fv_models": fv_res.get("models"),
            "mos": mos_res.get("mos"), "mos_stato": mos_res.get("stato"),
            "prezzo_ideale": round(prezzo_ideale, 2) if prezzo_ideale else None,
            "occasione": occ}


def fmt_row(r: dict) -> str:
    if r.get("status") != "ok":
        return f"{r['ticker']:8s} [{r['classe']}] {r.get('status')}"
    s, i, c = r["score"], r["iqi"], r["cs"]
    gate_s = ",".join(g["id"] for g in r["gates"]) or "-"
    tag_s = ",".join(t for t in r["packages"]["tags"] if t != "all") or "-"
    badge = " ".join("🥇" if b == "OCCASIONE D'ORO" else b for b in r["packages"]["badges"])
    voto = f"{s['vote']}" if s.get("vote") is not None else "n/d"
    net = (r.get("netto") or {}).get("netto_italia")
    net_s = f"{net:.1f}%" if net is not None else "-"
    pi = r.get("prezzo_ideale")
    pi_s = f"{pi:,.0f}" if pi else "-"
    warn = "⚠️ copertura" if s.get("coverage", 0) < config.COVERAGE_MIN else ""
    return (f"{r['ticker']:8s} [{r['classe']:6s}] MVF-S {voto:>4s}/1000 "
            f"(cop {s.get('coverage', 0) * 100:3.0f}%) IQI-S {i.get('iqi') or 'n/d':>3} "
            f"CS-S {c.get('cs'):>2} | gate {gate_s:6s} | 🔴{len(r['flags']['critical'])} "
            f"🟡{len(r['flags']['warning'])} | netto IT {net_s:>5s} | "
            f"P.ideale {pi_s:>7s} | {tag_s} {badge} {warn}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickers", nargs="+", help="ticker da analizzare")
    ap.add_argument("--test", action="store_true", help="banco di prova §14")
    ap.add_argument("--universe-us", action="store_true",
                    help="screena l'universo US large-cap (config.UNIVERSE_US)")
    ap.add_argument("--json", action="store_true", help="stampa json completo")
    ap.add_argument("--source", choices=["auto", "yfinance", "edgar"],
                    default="auto", help="fonte dati (edgar = solo US, no Yahoo)")
    ap.add_argument("--no-peers", action="store_true",
                    help="salta i peer di settore (niente correttivo settoriale)")
    args = ap.parse_args()
    if args.universe_us:
        tickers = config.UNIVERSE_US
    elif args.test:
        tickers = config.TEST_SET
    else:
        tickers = args.tickers or []
    if not tickers:
        ap.error("indica --tickers, --test o --universe-us")

    # universo da analizzare = titoli richiesti + peer di settore (solo per
    # le mediane; i peer non vengono mostrati ne' salvati)
    peers = [] if args.no_peers else [p for p in config.SECTOR_PEERS if p not in tickers]
    universe = list(dict.fromkeys(tickers + peers))

    # --- PASSO 1: metriche di tutto l'universo -----------------------------
    log.info("Passo 1/2: metriche (%d titoli, di cui %d peer)", len(universe), len(peers))
    analyses: dict[str, dict] = {}
    for t in universe:
        try:
            a = analyze_one(t, source=args.source)
        except Exception as e:
            log.exception("errore analisi %s: %s", t, e)
            a = None
        if a is not None:
            analyses[t] = a

    # --- statistiche di settore su tutto l'universo ------------------------
    stats = sector_stats.collect(
        [{"sector": a["m"]["ctx"].get("sector"), "metrics": a["m"]}
         for a in analyses.values()])

    # --- PASSO 2: scoring dei soli titoli richiesti ------------------------
    log.info("Passo 2/2: scoring")
    conn = dbmod.open_db()
    sid = dbmod.new_snapshot(conn, note="run bozza 1 + correttivo settoriale")
    results = []
    for t in tickers:
        a = analyses.get(t)
        if a is None:
            print(f"{t:8s} DATI NON REPERIBILI (segnalato, mai inventato)")
            continue
        sector_stats.inject(a["m"]["ctx"], a["m"], stats)   # correttivo settoriale
        try:
            r = score_one(a)
        except Exception as e:
            log.exception("errore scoring %s: %s", t, e)
            continue
        results.append(r)
        if r.get("status") == "ok":
            dbmod.save_result(conn, sid, r)
        print(fmt_row(r))

    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(config.OUTPUT_DIR, "results.json"), "w") as f:
        json.dump({"snapshot": sid, "results": results}, f, indent=1, default=str)
    if args.json:
        print(json.dumps(results, indent=1, default=str))
    print(f"\nSnapshot {sid}: {len(results)} titoli -> output/screener.db, "
          "output/results.json")


if __name__ == "__main__":
    main()
