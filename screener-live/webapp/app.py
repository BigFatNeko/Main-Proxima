#!/usr/bin/env python3
"""Proxima Screener Live — web app (Flask).

Serve i risultati del motore Regime S dal DB SQLite prodotto da batch.py.
Login per i due soci; dashboard interattiva; scheda di dettaglio per titolo.

Avvio dev:
    cd screener-live/webapp
    pip install -r requirements.txt
    PROXIMA_PASSWORD=... FLASK_SECRET=... python app.py
Produzione (VPS): gunicorn dietro nginx+HTTPS (v. README).
"""
from __future__ import annotations

import functools
import hashlib
import hmac
import json
import os
import sqlite3

from flask import (Flask, g, jsonify, redirect, render_template, request,
                   session, url_for, abort)

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("PROXIMA_DB", os.path.join(BASE, "..", "output", "screener.db"))

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "dev-secret-CAMBIARE-in-produzione")
# password condivisa dei soci (dev: "proxima"); in produzione via env PROXIMA_PASSWORD
_PW = os.environ.get("PROXIMA_PASSWORD", "proxima")


# ---------------------------------------------------------------- auth ------
def _check_pw(pw: str) -> bool:
    return hmac.compare_digest(pw, _PW)


def login_required(fn):
    @functools.wraps(fn)
    def wrap(*a, **k):
        if not session.get("auth"):
            return redirect(url_for("login", next=request.path))
        return fn(*a, **k)
    return wrap


@app.route("/login", methods=["GET", "POST"])
def login():
    err = None
    if request.method == "POST":
        if _check_pw(request.form.get("password", "")):
            session["auth"] = True
            session.permanent = True
            return redirect(request.args.get("next") or url_for("dashboard"))
        err = "Password non corretta."
    return render_template("login.html", err=err)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------------------------------------------------------- db --------
def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def _close(_):
    d = g.pop("db", None)
    if d is not None:
        d.close()


def latest_snapshot():
    row = db().execute(
        "SELECT snapshot_id, created_at, engine, mvf_version FROM snapshots "
        "ORDER BY snapshot_id DESC LIMIT 1").fetchone()
    return dict(row) if row else None


# --------------------------------------------------------------- pages ------
@app.route("/")
@login_required
def dashboard():
    snap = latest_snapshot()
    return render_template("dashboard.html", snap=snap)


@app.route("/ticker/<ticker>")
@login_required
def ticker_detail(ticker):
    snap = latest_snapshot()
    if not snap:
        abort(404)
    row = db().execute(
        "SELECT payload FROM results WHERE snapshot_id=? AND ticker=?",
        (snap["snapshot_id"], ticker)).fetchone()
    if not row:
        abort(404)
    r = json.loads(row["payload"])
    return render_template("detail.html", r=r, snap=snap)


# ---------------------------------------------------------------- api -------
@app.route("/api/results")
@login_required
def api_results():
    snap = latest_snapshot()
    if not snap:
        return jsonify({"snapshot": None, "results": []})
    rows = db().execute(
        "SELECT payload FROM results WHERE snapshot_id=? ORDER BY voto DESC",
        (snap["snapshot_id"],)).fetchall()
    out = []
    for row in rows:
        r = json.loads(row["payload"])
        out.append({
            "t": r["ticker"], "name": r.get("name"), "cl": r["classe"],
            "sec": r.get("sector") or "Altro", "country": r.get("country"),
            "mvf": r["score"].get("vote"), "cov": r["score"].get("coverage"),
            "iqi": r["iqi"].get("iqi"), "cs": r["cs"].get("cs"),
            "csr": r["cs"].get("lettura"),
            "comp": [r["cs"].get("composizione", {}).get(k, 0) for k in ("P", "V", "U")],
            "tier": (r["iqi"].get("tier_dividendo") or "—"),
            "gates": [gg["id"] for gg in r["gates"]],
            "crit": len(r["flags"]["critical"]), "warn": len(r["flags"]["warning"]),
            "tags": [t for t in r["packages"]["tags"] if t != "all"],
            "badges": r["packages"]["badges"],
            "net": (r.get("netto") or {}).get("netto_italia"),
            "delta": r.get("delta_mvf_iqi"),
        })
    return jsonify({"snapshot": snap, "results": out})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
