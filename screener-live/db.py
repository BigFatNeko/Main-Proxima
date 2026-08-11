"""Persistenza SQLite (calibrazione §13): ogni riga porta versione MVF,
classe, base, regime pesi, regime di esecuzione e snapshot — vincolo di
tracciabilita' della spec (Sez. 11F) e dell'handoff (Sez. 8)."""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone

import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS snapshots (
  snapshot_id TEXT PRIMARY KEY,
  created_at  TEXT NOT NULL,
  engine      TEXT NOT NULL,
  mvf_version TEXT NOT NULL,
  note        TEXT
);
CREATE TABLE IF NOT EXISTS results (
  snapshot_id     TEXT NOT NULL REFERENCES snapshots(snapshot_id),
  ticker          TEXT NOT NULL,
  classe          TEXT NOT NULL,
  regime          TEXT NOT NULL DEFAULT 'S',
  mvf_version     TEXT NOT NULL,
  base_originale  INTEGER,
  base_effettiva  INTEGER,
  regime_pesi     TEXT,
  voto            INTEGER,
  copertura       REAL,
  iqi             INTEGER,
  cs              INTEGER,
  gates           TEXT,
  red_critical    INTEGER,
  red_warning     INTEGER,
  tags            TEXT,
  badges          TEXT,
  netto_italia    REAL,
  prezzo          REAL,
  fair_value      REAL,
  mos             REAL,
  prezzo_ideale   REAL,
  occasione       INTEGER DEFAULT 0,
  payload         TEXT NOT NULL,
  PRIMARY KEY (snapshot_id, ticker)
);
"""


def open_db(path: str | None = None) -> sqlite3.Connection:
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    conn = sqlite3.connect(path or os.path.join(config.OUTPUT_DIR, "screener.db"))
    conn.executescript(SCHEMA)
    return conn


def new_snapshot(conn: sqlite3.Connection, note: str = "") -> str:
    sid = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    conn.execute("INSERT OR REPLACE INTO snapshots VALUES (?,?,?,?,?)",
                 (sid, datetime.now(timezone.utc).isoformat(),
                  config.ENGINE_VERSION, config.MVF_VERSION, note))
    conn.commit()
    return sid


def save_result(conn: sqlite3.Connection, sid: str, r: dict) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO results VALUES "
        "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (sid, r["ticker"], r["classe"], "S", config.MVF_VERSION,
         r["score"].get("base_original"), r["score"].get("base_effective"),
         r["score"].get("regime_pesi"), r["score"].get("vote"),
         r["score"].get("coverage"), r["iqi"].get("iqi"), r["cs"].get("cs"),
         json.dumps([g["id"] for g in r["gates"]]),
         len(r["flags"]["critical"]), len(r["flags"]["warning"]),
         json.dumps(r["packages"]["tags"]), json.dumps(r["packages"]["badges"]),
         (r.get("netto") or {}).get("netto_italia"),
         r.get("price"), r.get("fair_value"), r.get("mos"),
         r.get("prezzo_ideale"), int(r.get("occasione", False)),
         json.dumps(r, default=str)))
    conn.commit()
