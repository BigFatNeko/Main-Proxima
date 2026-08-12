"""Configurazione dello screener live (Regime S) — bozza 1.

Riferimenti: PROXIMA-Main/06-screener-live/CALIBRAZIONE-MVF-S.md (v1.1)
Specifica autorevole: MVF v4.0 (rassegna-stampa/docs-mvf, branch briefing).
"""
from __future__ import annotations

MVF_VERSION = "4.0"
ENGINE_VERSION = "bozza-1"

# --- Parametri macro per mercato (WACC proxy, Graham, CAPM) -----------------
# Da aggiornare con Damodaran a ogni ricalibrazione (v. mvf_valuation.py v3).
MARKET_PARAMS = {
    # market: (wacc_proxy, graham_M, bond10y_pct, rf, erp, crp)
    "US":      (0.085, 8.5, 4.3, 0.043, 0.055, 0.000),
    "EU_core": (0.075, 7.5, 2.6, 0.026, 0.055, 0.000),
    "IT":      (0.090, 7.5, 3.6, 0.036, 0.055, 0.018),
    "ES":      (0.082, 7.5, 3.2, 0.032, 0.055, 0.009),
    "UK":      (0.085, 7.5, 4.4, 0.044, 0.055, 0.005),
    "CH":      (0.070, 7.5, 0.7, 0.025, 0.055, 0.000),
    "JP":      (0.060, 7.5, 1.0, 0.025, 0.055, 0.000),
    "KR":      (0.090, 7.5, 3.3, 0.033, 0.055, 0.005),
    "TW":      (0.090, 7.5, 1.6, 0.025, 0.055, 0.008),
    "CN":      (0.100, 7.5, 2.2, 0.025, 0.055, 0.010),
    "CA":      (0.080, 8.5, 3.4, 0.034, 0.055, 0.000),
    "AU":      (0.085, 7.5, 4.2, 0.042, 0.055, 0.000),
    "OTHER":   (0.095, 7.5, 4.0, 0.040, 0.055, 0.010),
}
GRAHAM_Y_FLOOR = 2.5          # spec Sez. 7 F1
G_TERMINAL = 0.02             # spec F3
G_PERPETUO_MAX = 0.04         # spec F2

# suffisso yfinance -> mercato
SUFFIX_MARKET = {
    ".MI": "IT", ".DE": "EU_core", ".F": "EU_core", ".PA": "EU_core",
    ".AS": "EU_core", ".BR": "EU_core", ".MC": "ES", ".L": "UK",
    ".SW": "CH", ".T": "JP", ".KS": "KR", ".KQ": "KR", ".TW": "TW",
    ".HK": "CN", ".SS": "CN", ".SZ": "CN", ".TO": "CA", ".AX": "AU",
    ".ST": "EU_core", ".CO": "EU_core", ".HE": "EU_core", ".OL": "EU_core",
    ".VI": "EU_core", ".LS": "EU_core", ".IR": "EU_core",
}

# --- Ritenute alla fonte estere (w_home), valori indicativi spec Sez. 7 -----
# Persona fisica IT, regime amministrato/dichiarativo: netto ITALIA =
# lordo x (1 - w_home) x (1 - 0.26). VERIFICARE treaty prima dell'uso reale.
WHT_COUNTRY = {
    "United States": 0.15, "Italy": 0.0, "United Kingdom": 0.0,
    "Germany": 0.26375, "France": 0.25, "Netherlands": 0.15, "Spain": 0.19,
    "Switzerland": 0.35, "Canada": 0.25, "Ireland": 0.25, "Norway": 0.25,
    "Sweden": 0.30, "Denmark": 0.27, "Finland": 0.35, "Belgium": 0.30,
    "Austria": 0.275, "Portugal": 0.28, "Japan": 0.15, "South Korea": 0.22,
    "Taiwan": 0.21, "Hong Kong": 0.0, "China": 0.10, "Singapore": 0.0,
    "Australia": 0.30, "New Zealand": 0.30, "Israel": 0.25,
}
WHT_DEFAULT = 0.15
# Casi speciali per classe (spec Sez. 7): prevalgono sul paese.
WHT_CLASS_US = {"reit": 0.30, "bdc": 0.30, "mlp": 0.37}
T_ITALIA = 0.26

# --- Settori esenti (Altman-Z / gate leva) — spec Sez. 3D, 8-bis ------------
ALTMAN_EXEMPT_KEYWORDS = (
    "bank", "banks", "insurance", "reit", "utilities", "utility",
    "tobacco", "asset management", "capital markets", "credit services",
    "financial", "mortgage",
)
LEVERAGED_BY_DESIGN = ("reit", "bank", "insurance", "utilit", "bdc", "mlp",
                       "midstream", "mortgage", "credit services",
                       "asset management", "financial")

# --- Tassonomia tematica per il pacchetto Innovativo (§10) -------------------
# industry (yfinance) -> tema. Estensione con liste curate: themes_overrides.json
THEME_BY_INDUSTRY = {
    "Semiconductors": "chip", "Semiconductor Equipment & Materials": "chip",
    "Software - Infrastructure": "ai_software", "Software - Application": "ai_software",
    "Information Technology Services": "ai_software",
    "Uranium": "nucleare", "Aerospace & Defense": "spazio",
    "Internet Content & Information": "ai_software",
    "Biotechnology": "biotech", "Drug Manufacturers - Specialty & Generic": "biotech",
    "Diagnostics & Research": "biotech",
    "Credit Services": "fintech", "Software - Services": "ai_software",
    "Electronic Components": "chip", "Computer Hardware": "chip",
    "Communication Equipment": "chip",
    "Specialty Industrial Machinery": "robotica",
}
INNOVATIVE_THEMES = {"chip", "nucleare", "ai_software", "quantum", "robotica",
                     "spazio", "cybersecurity", "biotech", "fintech"}

# --- Pacchetto Etico: esclusioni settoriali (solo dentro il pacchetto) ------
ETICO_EXCLUDED_INDUSTRIES = ("tobacco", "thermal coal", "coal", "gambling",
                             "casinos", "defense")

# --- Paesi per i pacchetti geografici ---------------------------------------
EMERGENTI_COUNTRIES = ("China", "Hong Kong", "South Korea", "Taiwan")
PIR_COUNTRIES = ("Italy",)  # UE con stabile organizzazione IT: solo via override

# --- Fetch -------------------------------------------------------------------
EDGAR_UA = "Proxima SCF screener-live contact: relia.laprimavera@libero.it"
CACHE_DIR = "cache"
OUTPUT_DIR = "output"
YF_MAX_RETRIES = 3
YF_BACKOFF_S = 5

# --- Soglie trasversali (calibrazione §1, §10, §12) --------------------------
COVERAGE_MIN = 0.75          # sotto: "copertura insufficiente"
OCCASIONE_MVF_MIN = 800      # badge OCCASIONE D'ORO
DEFENSIVO = dict(years_paid_min=10, yield_min=4.0, divcagr_min=6.0,
                 increases_of5_min=4, payout_max=0.75, fcf_margin_min=8.0,
                 de_max=1.5, beta_max=1.0, mvf_min=600, iqi_min=55)
COMPOUNDERS = dict(roic_min=15.0, spread_min=5.0, fcfps_cagr_min=8.0,
                   mvf_min=650)
INNOVATIVO_MVF_MIN = 500
EMERGENTI_MVF_MIN = 500

# Banco di prova (calibrazione §14)
TEST_SET = ["KO", "JNJ", "ENI.MI", "MO", "MCD", "FRT", "TGT", "WMT", "SPGI",
            "SPCE", "LULU"]

# Universo US large-cap (bozza 1, gira su EDGAR senza Yahoo). A regime sara'
# sostituito dall'universo MSCI World + KR/TW/Cina (T21).
UNIVERSE_US = [
    # Consumer Defensive
    "KO", "PG", "PEP", "MO", "PM", "COST", "WMT", "KR", "CL", "GIS", "KMB", "MDLZ",
    # Consumer Cyclical / retail
    "MCD", "HD", "LOW", "NKE", "SBUX", "TJX", "ROST", "TGT", "LULU", "DG", "DLTR",
    # Healthcare
    "JNJ", "UNH", "LLY", "MRK", "ABBV", "PFE", "ABT", "TMO", "DHR",
    # Technology / comms
    "MSFT", "AAPL", "NVDA", "GOOGL", "META", "ORCL", "ADBE", "CRM", "CSCO",
    # Financials / data
    "SPGI", "MCO", "V", "MA", "JPM",
    # Industrials / energy
    "CAT", "HON", "DE", "XOM", "CVX",
    # REIT + caso limite
    "FRT", "SPCE",
]

# Peer di settore per il correttivo settoriale (usati solo per le mediane,
# non mostrati). US large cap con buona copertura dei settori del test.
SECTOR_PEERS = [
    # Consumer Defensive / staples
    "PG", "PEP", "COST", "KR", "CL", "GIS", "KMB",
    # Consumer Cyclical / retail
    "HD", "LOW", "NKE", "SBUX", "TJX", "ROST",
    # Healthcare
    "PFE", "MRK", "ABBV", "LLY", "ABT",
    # Financial (peer di SPGI)
    "MCO", "V", "MA",
    # Technology
    "MSFT", "AAPL", "ORCL",
    # Discount retail (peer di WMT/TGT)
    "DG", "DLTR", "BJ",
]
