"""MVF v4.5.1 — scoring a bande (regime S: screening batch).

Sostituisce il vecchio punteggio v4.1, che normalizzava ogni metrica contro
un target lineare. La v4.5 usa una scala unica a cinque livelli
(Eccellente 100% · Buono 75% · Sufficiente 50% · Debole 25% · Critico 0%) con
bande per ogni metrica (nucleo, Sez. 3-ter), un modificatore di trend a 5 anni
e pesi propri per classe (banche, assicurazioni, REIT, utility).

Voto MVF = punteggio grezzo / peso delle metriche DISPONIBILI x 1000.
Le metriche che Yahoo non puo' dare (NPL, CET1, occupancy, WALT, guidance,
rating Morningstar...) vengono omesse e dichiarate, mai stimate: il voto e'
allora PARZIALE e porta con se' la copertura. Un voto parziale si legge solo
entro la stessa classe e con la stessa copertura approssimativa.

Deviazioni dal testo della specifica, tutte dichiarate:
  - ROA delle banche/assicurazioni: la tabella 3-ter assume un ROA industriale
    (Eccellente >= 12%), che per una banca non esiste. Bande ricalibrate.
  - Insider trading e Affidabilita' della guidance non sono ricavabili da
    Yahoo: omesse senza penalita' di Confidence Score (per la guidance la
    specifica manda i 5 punti all'Earnings Quality).
  - Il moat senza copertura Morningstar sta al massimo a Sufficiente [U].
  - Earnings Quality e FCF/azione sono omessi per banche e assicurazioni: il
    flusso di cassa operativo di un intermediario finanziario non misura
    l'utile in cassa.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from typing import Optional

VERSIONE = "4.5.1"
REGIME = "S"

LIVELLI = ("Eccellente", "Buono", "Sufficiente", "Debole", "Critico")
FRAZIONI = (1.0, 0.75, 0.50, 0.25, 0.0)

# Basi nominali (peso totale della classe): servono all'etichetta e alla
# copertura, non al calcolo del voto, che usa il peso disponibile.
BASI = {"common": 290, "banca": 365, "assicurazione": 365, "utility": 365,
        "reit": 370}

# Metriche che in regime S non esistono: omesse senza costo per il CS.
NON_DISPONIBILI_REGIME_S = frozenset({"insider_trading", "guidance"})

# Metriche che Yahoo spesso non riporta perche' il valore e' zero o non
# applicabile (nessuna SBC, nessun riacquisto, dividendo recente): omesse
# senza penalita' di Confidence Score. Il -2 vale per le metriche core.
NON_CORE = frozenset({"sbc_revenue", "capex_da", "buyback", "dividend_growth",
                      "tax", "capex_revenue", "rd_revenue"})


# ---------------------------------------------------------------------------
# Primitive di banda
# ---------------------------------------------------------------------------

def _alto(v: float, soglie: tuple) -> int:
    """Livello per metriche dove ALTO e' meglio. soglie: 4 minimi decrescenti
    per Eccellente, Buono, Sufficiente, Debole (estremo inferiore incluso)."""
    for i, t in enumerate(soglie):
        if v >= t:
            return i
    return 4


def _basso(v: float, soglie: tuple) -> int:
    """Livello per metriche dove BASSO e' meglio. soglie: 4 massimi crescenti
    (estremo superiore incluso)."""
    for i, t in enumerate(soglie):
        if v <= t:
            return i
    return 4


def _trend(livello: int, delta: Optional[float], ultimo: Optional[float],
           soglia: float, alto_meglio: bool = True) -> tuple[int, int]:
    """Modificatore di trend a 5 anni: +-1 livello, massimo uno.

    `delta` = FY0 - FY-5, `ultimo` = FY0 - FY-1. Scatta solo se la variazione
    a 5 anni supera la soglia E l'ultimo anno va nello stesso verso.
    Ritorna (livello, spostamento in {-1,0,+1} dove +1 = miglioramento).
    """
    if delta is None or soglia is None:
        return livello, 0
    buono = delta if alto_meglio else -delta
    ult = None if ultimo is None else (ultimo if alto_meglio else -ultimo)
    if buono > soglia and (ult is None or ult > 0) and livello > 0:
        return livello - 1, +1
    if buono < -soglia and (ult is None or ult < 0) and livello < 4:
        return livello + 1, -1
    return livello, 0


# ---------------------------------------------------------------------------
# Bande metrica per metrica (nucleo Sez. 3-ter e moduli di classe)
# ---------------------------------------------------------------------------

# (tipo, soglie, soglia_trend)  tipo: "alto" | "basso"
BANDE = {
    "gross_margin":     ("alto",  (0.60, 0.45, 0.30, 0.15), 0.02),
    "ebitda_margin":    ("alto",  (0.35, 0.25, 0.15, 0.08), 0.02),
    "operating_margin": ("alto",  (0.25, 0.18, 0.12, 0.06), 0.02),
    "pretax_margin":    ("alto",  (0.25, 0.18, 0.12, 0.06), 0.02),   # banche
    "net_margin":       ("alto",  (0.18, 0.12, 0.07, 0.03), 0.02),
    "fcf_margin":       ("alto",  (0.18, 0.12, 0.07, 0.02), 0.02),
    "revenue_growth":   ("alto",  (0.12, 0.08, 0.04, 0.0), None),
    "eps_growth":       ("alto",  (0.15, 0.10, 0.05, 0.0), None),
    "fcf_ps_growth":    ("alto",  (0.12, 0.08, 0.04, 0.0), None),
    "roic_spread":      ("alto",  (0.10, 0.05, 0.02, 0.0), 0.03),
    "roe_spread":       ("alto",  (0.10, 0.05, 0.02, 0.0), 0.03),
    "roa":              ("alto",  (0.12, 0.08, 0.05, 0.02), 0.02),
    "roa_finanziaria":  ("alto",  (0.012, 0.009, 0.006, 0.003), 0.002),
    "nd_ebitda":        ("basso", (0.5, 1.5, 2.5, 3.5), 0.5),
    "nd_ebitda_utility": ("basso", (4.0, 5.0, 5.5, 6.5), 0.5),
    "nd_ebitda_telecom": ("basso", (2.0, 3.0, 4.0, 5.0), 0.5),
    "nd_ebitda_reit":   ("basso", (4.5, 5.5, 6.5, 7.5), 0.5),
    "debt_assets":      ("basso", (0.15, 0.30, 0.45, 0.60), 0.05),
    "sbc_revenue":      ("basso", (0.015, 0.03, 0.05, 0.08), 0.005),
    "capex_revenue":    ("basso", (0.03, 0.06, 0.10, 0.15), None),
    "buyback":          ("alto",  (0.03, 0.015, 0.005, 0.0), None),
    "dividend_yield":   ("alto",  (0.04, 0.025, 0.015, 0.005), None),
    "dividend_yield_reit": ("alto", (0.05, 0.04, 0.03, 0.02), None),
    "dividend_growth":  ("alto",  (0.10, 0.06, 0.03, 0.0), None),
    # REIT
    "ffo_margin":       ("alto",  (0.55, 0.45, 0.35, 0.25), None),
    "ffo_payout":       ("basso", (0.70, 0.80, 0.90, 1.00), None),
    "fixed_charge_cov": ("alto",  (4.0, 3.0, 2.5, 1.5), None),
    "ffo_ps_growth":    ("alto",  (0.06, 0.04, 0.02, 0.0), None),
    "rental_growth":    ("alto",  (0.08, 0.05, 0.03, 0.0), None),
    # Banche
    "cost_income":      ("basso", (0.45, 0.55, 0.62, 0.70), None),
    "cost_of_risk":     ("basso", (0.0030, 0.0060, 0.0100, 0.0150), None),
}

# Altman: il livello dipende dal modello. (soglie Z originale, soglie Z'')
ALTMAN_Z = (3.5, 2.99, 2.4, 1.81)
ALTMAN_Z2 = (4.0, 2.6, 1.8, 1.10)


def livello_metrica(nome: str, v: Optional[float],
                    delta: Optional[float] = None,
                    ultimo: Optional[float] = None) -> Optional[tuple[int, int]]:
    """(livello, spostamento_trend) o None se manca il dato."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    tipo, soglie, s_trend = BANDE[nome]
    liv = _alto(v, soglie) if tipo == "alto" else _basso(v, soglie)
    if s_trend is not None:
        return _trend(liv, delta, ultimo, s_trend, tipo == "alto")
    return liv, 0


def livello_capex_da(v: Optional[float], ricavi_in_crescita: bool = True
                     ) -> Optional[int]:
    """CapEx/D&A. Ecc 1,0-1,5x · Buono 1,5-2,0x o 0,9-1,0x · Suff 2,0-2,5x ·
    Debole 0,7-0,9x o 2,5-3,5x · Critico < 0,7x o > 3,5x."""
    if v is None:
        return None
    if 1.0 <= v <= 1.5:
        return 0
    if 1.5 < v <= 2.0 or 0.9 <= v < 1.0:
        return 1
    if 2.0 < v <= 2.5:
        return 2
    if 0.7 <= v < 0.9 or 2.5 < v <= 3.5:
        return 3
    return 4


def livello_rd(v: Optional[float], pharma: bool = False) -> Optional[int]:
    """R&D/ricavi. Generale: Ecc 10-20% · Buono 6-10% o 20-25% · Suff 3-6% ·
    Debole 1-3% o > 25% · Critico < 1%. Pharma: Ecc 15-25% · Buono 12-15%
    o 25-30% · Suff 8-12% · Debole 5-8% o > 30% · Critico < 5%."""
    if v is None:
        return None
    if pharma:
        if 0.15 <= v <= 0.25:
            return 0
        if 0.12 <= v < 0.15 or 0.25 < v <= 0.30:
            return 1
        if 0.08 <= v < 0.12:
            return 2
        if 0.05 <= v < 0.08 or v > 0.30:
            return 3
        return 4
    if 0.10 <= v <= 0.20:
        return 0
    if 0.06 <= v < 0.10 or 0.20 < v <= 0.25:
        return 1
    if 0.03 <= v < 0.06:
        return 2
    if 0.01 <= v < 0.03 or v > 0.25:
        return 3
    return 4


def livello_payout(p: Optional[float], regolato: bool = False) -> Optional[int]:
    """Payout (il peggiore fra utili e FCF). Ecc 30-50% · Buono 50-65% o
    20-30% · Suff 65-80% o < 20% · Debole 80-100% · Critico > 100%.
    Utility regolate e telecom: tutte le soglie +15 punti percentuali."""
    if p is None or p < 0:
        return None
    s = 0.15 if regolato else 0.0
    if p > 1.00 + s:
        return 4
    if p > 0.80 + s:
        return 3
    if p > 0.65 + s:
        return 2
    if p > 0.50 + s:
        return 1
    if p >= 0.30 + s:
        return 0
    if p >= 0.20 + s:
        return 1
    return 2


def livello_altman(z: Optional[float], modello: str = "Z") -> Optional[int]:
    if z is None:
        return None
    return _alto(z, ALTMAN_Z2 if modello == "Z2" else ALTMAN_Z)


def livello_tax(serie: list, aliquota: Optional[float]) -> Optional[int]:
    """Stabilita' dell'aliquota effettiva (sigma 5y), non il livello.

    Ecc 15-25% e sigma < 3pp · Buono 10-15% o 25-30% con sigma < 3pp ·
    Suff aliquota > 30% stabile · Debole sigma 3-6pp, o < 10% stabile senza
    regime documentato · Critico sigma > 6pp. Il regime documentato non e'
    verificabile in regime S: un'aliquota < 10% stabile vale Debole.
    """
    vals = [x for x in (serie or []) if x is not None and -0.5 < x < 1.0]
    if len(vals) < 3 or aliquota is None:
        return None
    sigma = statistics.pstdev(vals)
    if sigma > 0.06:
        return 4
    if sigma > 0.03:
        return 3
    if 0.15 <= aliquota <= 0.25:
        return 0
    if 0.10 <= aliquota < 0.15 or 0.25 < aliquota <= 0.30:
        return 1
    if aliquota > 0.30:
        return 2
    return 3


def livello_earnings_quality(ccr: Optional[float], accruals: Optional[float]
                             ) -> Optional[int]:
    """Composita CCR (CFO/NI, media 3y) e accruals. Critico se CCR < 0,5 o
    accruals > 10%. Beneish M-Score non calcolato (servono otto input)."""
    if ccr is None and accruals is None:
        return None
    livelli = []
    if ccr is not None:
        if ccr < 0.5:
            livelli.append(4)
        elif ccr < 0.8:
            livelli.append(3)
        elif ccr < 0.9:
            livelli.append(2)
        elif ccr < 1.1:
            livelli.append(1)
        else:
            livelli.append(0)
    if accruals is not None:
        if accruals > 0.10:
            livelli.append(4)
        elif accruals > 0.08:
            livelli.append(3)
        elif accruals > 0.05:
            livelli.append(2)
        elif accruals > 0.0:
            livelli.append(1)
        else:
            livelli.append(0)
    return max(livelli)   # il peggiore dei due segnali


def livello_moat(rating: Optional[str], test_confermato: bool,
                 roic_sopra_wacc: Optional[bool],
                 trend_negativo: bool = False) -> tuple[Optional[int], str]:
    """Moat (25). Rating SOLO Morningstar, modulato dal test numerico.

    Eccellente: Wide con test confermato · Buono: Wide con test debole o
    Narrow con test confermato · Sufficiente: Narrow con test debole o trend
    negativo · Debole: None con ROIC > WACC · Critico: None con ROIC < WACC.
    Senza copertura Morningstar: massimo Sufficiente, solo dal test, tag [U].
    Ritorna (livello, tag).
    """
    r = (rating or "").lower()
    if r == "wide":
        liv = 0 if test_confermato else 1
    elif r == "narrow":
        liv = 1 if test_confermato else 2
    elif r == "none":
        liv = 3 if roic_sopra_wacc else 4
    else:
        if test_confermato:
            return 2, "U"
        if roic_sopra_wacc is None:
            return None, "U"
        return (3 if roic_sopra_wacc else 4), "U"
    if trend_negativo and liv < 4 and r in ("wide", "narrow"):
        liv = min(4, max(liv, 2)) if r == "narrow" else liv + 1
    return liv, "P"


# ---------------------------------------------------------------------------
# Pesi per classe
# ---------------------------------------------------------------------------

PESI_COMMON = {
    "gross_margin": 15, "ebitda_margin": 5, "operating_margin": 25,
    "net_margin": 18, "fcf_margin": 12, "revenue_growth": 5,
    "eps_growth": 10, "fcf_ps_growth": 18,
    "roic_spread": 15, "roe_spread": 3, "roa": 5,
    "nd_ebitda": 10, "debt_assets": 10, "altman": 5,
    "sbc_revenue": 5, "capex_revenue": 5, "capex_da": 3, "rd_revenue": 7,
    "insider_trading": 5, "buyback": 5,
    "dividend_yield": 16, "payout": 10, "dividend_growth": 10,
    "multiple_expansion": 15, "tax": 8, "guidance": 5,
    "moat": 25, "earnings_quality": 15,
}
assert sum(PESI_COMMON.values()) == 290, "pesi common != 290"


def pesi(classe: str, ha_dividendo: bool, ddm_significativo: bool,
         rd_materiale: bool, settore_telecom: bool = False
         ) -> tuple[dict, list[str]]:
    """Tabella dei pesi per classe, con le clausole del nucleo applicate.

    Ritorna (pesi, note di regime). Una chiave con peso 0 non partecipa.
    """
    note: list[str] = []
    w = dict(PESI_COMMON)

    if classe == "banca" or classe == "assicurazione":
        # Sostituzioni a pari peso (9A). Quelle non ricavabili da Yahoo non
        # hanno ancora un nome qui: restano fuori dal calcolo.
        w.update({
            "gross_margin": 0, "ebitda_margin": 0, "fcf_margin": 0,
            "fcf_ps_growth": 0, "nd_ebitda": 0, "debt_assets": 0,
            "altman": 0, "capex_revenue": 0, "capex_da": 0, "rd_revenue": 0,
            "earnings_quality": 0, "insider_trading": 0, "guidance": 0,
        })
        w["operating_margin"] = 0
        w["pretax_margin"] = 25
        w["roa"] = 10                 # 5 + 5 dell'EBITDA margin
        w["roe_spread"] = 11          # 3 + 8 di CapEx
        w["roic_spread"] = 22         # 15 + 7 di R&D (ROTE)
        w["cost_income"] = 15 if classe == "banca" else 0
        w["cost_of_risk"] = 15 if classe == "banca" else 0
        note.append(f"{classe}: metriche di cassa/CET1/NPL/NIM non disponibili in regime S")
    elif classe == "reit":
        w.update({
            "net_margin": 0, "altman": 0, "nd_ebitda": 0, "fcf_margin": 0,
            "fcf_ps_growth": 0, "eps_growth": 10, "capex_revenue": 0,
            "capex_da": 0, "rd_revenue": 0, "insider_trading": 0,
            "guidance": 0, "sbc_revenue": 0,
        })
        w["ffo_margin"] = 27           # AFFO margin (proxy FFO)
        w["ffo_ps_growth"] = 18        # AFFO per share growth (proxy FFO)
        w["ffo_payout"] = 15
        w["fixed_charge_cov"] = 10
        w["nd_ebitda_reit"] = 15
        w["rental_growth"] = 5
        w["revenue_growth"] = 0
        # Fuori dal REIT: imposte (non le pagano), qualita' degli utili (utile
        # contabile schiacciato dagli ammortamenti) e Delta P/E (il P/E non
        # misura un REIT; servirebbe il Delta P/AFFO).
        w["tax"] = 0
        w["earnings_quality"] = 0
        w["multiple_expansion"] = 0
        w["dividend_yield"] = 16
        w["payout"] = 0
        note.append("reit: FFO = utile netto + ammortamenti - plusvalenze, "
                    "proxy dell'AFFO [U]; occupancy, WALT, same-store NOI e "
                    "accretion spread non disponibili")
    elif classe == "utility":
        w["altman"] = 0
        w["nd_ebitda"] = 0
        w["nd_ebitda_utility"] = 15    # 10 + 5 dell'Altman
        w["capex_revenue"] = 0
        w["capex_da"] = 0
        w["capex_vs_dep"] = 8
        w["rd_revenue"] = 0
        w["insider_trading"] = 0
        w["guidance"] = 0
        note.append("utility: rate base, earned-allowed ROE, regulatory lag "
                    "e % ricavi regolati non disponibili")
    else:
        w["insider_trading"] = 0
        w["guidance"] = 0

    if classe in ("common",):
        # La guidance non c'e' in regime S: i suoi 5 punti vanno all'Earnings Quality.
        w["earnings_quality"] += 5
        note.append("guidance non disponibile: 5 punti all'Earnings Quality")
    if not rd_materiale and w.get("rd_revenue"):
        w["roic_spread"] += w["rd_revenue"]
        w["rd_revenue"] = 0
        note.append("R&D non materiale (< 0,5% dei ricavi): 7 punti al ROIC")

    # Clausole dividendi (Sez. 3 E e F)
    div_keys = [k for k in ("dividend_yield", "payout", "dividend_growth") if w.get(k)]
    if not ha_dividendo and classe == "common":
        for k in div_keys:
            w[k] = 0
        w["fcf_margin"] += 10
        w["buyback"] += 10
        w["roic_spread"] += 8
        w["revenue_growth"] += 8
        note.append("senza dividendo: 36 punti redistribuiti (Sez. 3-E)")
    elif not ha_dividendo:
        for k in div_keys:
            w[k] = 0
        note.append("senza dividendo: pesi dividendi azzerati")
    elif ddm_significativo and classe == "common":
        w["dividend_yield"] = 8
        w["payout"] = 5
        w["dividend_growth"] = 5
        w["fcf_margin"] += 10
        w["net_margin"] += 8
        note.append("DDM significativo: pesi dividendi dimezzati (Sez. 3-F)")
    return {k: v for k, v in w.items() if v}, note


# ---------------------------------------------------------------------------
# Voto
# ---------------------------------------------------------------------------

@dataclass
class RisultatoVoto:
    voto_1000: Optional[float] = None
    base_nominale: int = 0
    peso_disponibile: float = 0.0
    copertura: float = 0.0
    parziale: bool = False
    penalita_altman: float = 0.0
    dettaglio: dict = field(default_factory=dict)
    omesse: list = field(default_factory=list)
    omesse_core: int = 0
    note: list = field(default_factory=list)


def calcola_voto(classe: str, livelli: dict, ha_dividendo: bool,
                 ddm_significativo: bool, rd_materiale: bool,
                 altman_z: Optional[float] = None, altman_modello: str = "Z",
                 altman_esente: bool = False, settore_telecom: bool = False,
                 valori: Optional[dict] = None,
                 frazioni_dirette: Optional[dict] = None) -> RisultatoVoto:
    """Voto MVF su 1000 dalle bande.

    livelli: {metrica: (livello 0-4, spostamento_trend) | livello | None}.
    frazioni_dirette: metriche gia' espresse come frazione del peso (Delta P/E,
    che ha una rubrica propria nel nucleo).
    """
    pesi_cl, note = pesi(classe, ha_dividendo, ddm_significativo, rd_materiale,
                         settore_telecom)
    valori = valori or {}
    frazioni_dirette = frazioni_dirette or {}
    r = RisultatoVoto(base_nominale=BASI.get(classe, 290), note=list(note))
    grezzo = 0.0
    disponibile = 0.0
    tot = sum(pesi_cl.values())
    for nome, peso in pesi_cl.items():
        if nome in NON_DISPONIBILI_REGIME_S:
            continue
        if nome in frazioni_dirette:
            frac = frazioni_dirette[nome]
            liv_txt = None
            trend = 0
        else:
            voce = livelli.get(nome)
            if voce is None:
                r.omesse.append(nome)
                continue
            liv, trend = voce if isinstance(voce, tuple) else (voce, 0)
            frac = FRAZIONI[liv]
            liv_txt = LIVELLI[liv]
        if frac is None:
            r.omesse.append(nome)
            continue
        grezzo += peso * frac
        disponibile += peso
        r.dettaglio[nome] = {
            "peso": peso, "valore": valori.get(nome), "livello": liv_txt,
            "frazione": round(frac, 3), "trend": trend,
        }
    if disponibile <= 0:
        r.note.append("nessuna metrica disponibile")
        return r

    # Altman: penalita' solo in zona di pericolo, -15% (v4.5.1). Nessuna in grigia.
    pen = 0.0
    if not altman_esente and altman_z is not None:
        soglia = ALTMAN_Z2[3] if altman_modello == "Z2" else ALTMAN_Z[3]
        if altman_z < soglia:
            pen = -0.15
            r.note.append(f"Altman {altman_modello}={altman_z:.2f} in zona di pericolo: -15% sul voto")
    voto = grezzo / disponibile * 1000.0 * (1 + pen)
    r.voto_1000 = round(max(0.0, min(1000.0, voto)), 1)
    r.peso_disponibile = disponibile
    # Copertura contro la BASE NOMINALE della classe, non contro i soli pesi
    # che la tabella elenca: per una banca mancano NIM, CET1, NPL e altre sei
    # metriche, e nascondere quei 140 punti farebbe sembrare completo un
    # voto fatto su meta' dei dati. Si tolgono i 5 punti dell'insider trading
    # e, fuori dal common, i 5 della guidance (inesistenti in regime S).
    denominatore = r.base_nominale - 5 - (0 if classe == "common" else 5)
    r.copertura = round(min(1.0, disponibile / denominatore), 3) if denominatore else 0.0
    r.parziale = r.copertura < 0.85
    r.penalita_altman = pen
    r.omesse_core = sum(1 for n in r.omesse
                        if n not in NON_DISPONIBILI_REGIME_S and n not in NON_CORE)
    return r
