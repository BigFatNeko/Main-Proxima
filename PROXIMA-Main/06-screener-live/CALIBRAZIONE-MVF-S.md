# DOCUMENTO DI CALIBRAZIONE — MVF-S (Regime S, batch)

**Versione 1.1 — aggiornata dopo la prima review del committente.**
Le correzioni della review sono marcate `✎ REVIEW`. Dove la specifica MVF
v4.0 fornisce già una rubrica, è marcata `DA SPEC` e non si tocca. Dove
questo documento devia dalla specifica, la deviazione è marcata
`⚠ DEVIAZIONE` con motivazione.

**Filosofia fissata in review** `✎ REVIEW`: soglie severe. Un punteggio alto
deve essere raro; il titolo che finalmente soddisfa tutto viene
**enormemente premiato**: MVF-S ≥ 800 senza gate né red flag critici, con
prezzo ≤ prezzo ideale (MoS soddisfatto) → badge **🥇 OCCASIONE D'ORO**,
con evidenza in UI e negli alert pari a quella delle red flag.

---

## §0 — Perimetro

Copre il **Regime S** (batch notturno, universo ampio, deterministico) e le
strutture condivise (pacchetti, alert, profili, schema dati). Il **Regime A**
applica la specifica MVF v4.0 integrale e non richiede calibrazione.

Fuori perimetro (v. `TASKS-POSTICIPATI.md`): modulo ETF, screener
obbligazionario, screener commodities, canale Proxima nel veicolo briefing.

## §0-bis — Legenda generale (tag e acronimi ricorrenti)

**Tag di provenienza dei dati (DIP, spec Sez. 6-bis):**
- **[P] Primario** — dato da fonte ufficiale (bilancio depositato: EDGAR, EDINET, DART, MOPS, ESEF). Ground truth.
- **[V] Validato** — ≥2 fonti indipendenti concordi dopo normalizzazione.
- **[U] Non validato** — fonte singola o conflitto tra fonti.

**Tag degli input previsionali (forward):**
- **[G] Guidance** — previsione ufficiale del management.
- **[C] Consensus** — media delle stime di più analisti/broker.
- **[S] Stima** — stima singola o propria (la più debole: fa scattare cap).

**Acronimi finanziari usati in tutto il documento:**
- **FCF** — Free Cash Flow: cassa generata dopo gli investimenti (CFO − CapEx).
- **CFO** — Cash Flow Operativo: cassa generata dalla gestione corrente.
- **CapEx** — Capital Expenditure: investimenti in immobilizzazioni.
- **D&A** — Deprezzamento e Ammortamento.
- **EBITDA** — utile prima di interessi, tasse, deprezzamenti e ammortamenti.
- **EBIT** — utile operativo (prima di interessi e tasse).
- **EPS** — utile per azione (diluito, salvo diversa indicazione).
- **SBC** — Stock-Based Compensation: compensi in azioni ai dipendenti.
- **ROIC / ROE / ROA** — redditività su capitale investito / patrimonio netto / attivi.
- **WACC** — costo medio ponderato del capitale (la "asticella" del ROIC).
- **D/E, D/A** — debito su patrimonio netto, debito su attivi.
- **CAGR** — tasso di crescita annuo composto.
- **P/E** — prezzo/utili. **Δ P/E** — espansione/contrazione del multiplo.
- **CCR** — Cash Conversion Ratio (CFO/utile netto): quanta parte dell'utile diventa cassa.
- **Accruals** — (utile netto − CFO)/attivi medi: utile "di carta" non convertito in cassa.
- **Altman-Z** — indice di rischio insolvenza (>3 sano, <1,23 pericolo).
- **MoS** — Margine di Sicurezza: sconto richiesto sul fair value.
- **IQI** — Indice di Qualità dell'Investimento (/100): guida il MoS.
- **CS** — Confidence Score (/100): affidabilità dei dati reperiti.
- **TSR** — Total Shareholder Return: rendimento totale (prezzo + dividendi).

---

## §1 — Formula generale di scoring

Per ogni metrica con peso `w`:

```
punteggio = w × clamp( frazione_livello + mod_trend + bonus_settore , 0 , 1 )
```

- **frazione_livello** — dalla tabella bande della metrica.
- **mod_trend** — pendenza a 5 anni (fallback 3, mai meno — spec):
  miglioramento chiaro (Δ relativo > +10%) → **+0,10** · stabile → 0 ·
  deterioramento chiaro (< −10%) → **−0,10**.
- **bonus_settore** — metrica ≥ 80° percentile della propria industria
  (mediane/percentili calcolati in-universo, Q8) → **+0,10**. Solo bonus.
- **I guard prevalgono sempre** (§2-bis).

**Metriche non reperibili** → omesse + ri-basatura (Q6):
`Voto MVF-S = (grezzo / base_effettiva) × 1000`. Accanto al voto compare
**sempre** la copertura: `MVF-S 742/1000 · copertura 87% (mancano: MOAT 25,
Insider 5)`. Copertura < **75%** → badge "copertura insufficiente", titolo
non proponibile in sessione senza Regime A.

**Naming** (D4): `Voto MVF-S` ≠ `Voto MVF` (Regime A). Mai visivamente
identici. Stessa distinzione per `IQI-S` e `CS-S`.

---

## §2 — Motore COMMON, base 280 — bande per metrica

**Legenda di sezione** — GM: Gross Margin (margine lordo = utile lordo/ricavi) ·
OM: Operating Margin (margine operativo) · NM: Net Margin (margine netto) ·
FCF Margin: FCF/ricavi · R&D: Ricerca & Sviluppo · Payout: quota dell'utile
distribuita come dividendo · Buyback: riacquisto di azioni proprie · Insider:
acquisti/vendite di azioni da parte di dirigenti · MOAT: vantaggio competitivo
durevole · 10b5-1: piani di vendita programmata dei dirigenti (US).

Le percentuali nelle bande sono frazioni del peso.

| ID | Metrica (peso) | Bande livello | Note / guard |
|---|---|---|---|
| C1 | Gross Margin (15) | `✎ REVIEW` assoluta: ≥80% → 100% · 60–80 → 80% · 40–60 → 60% · 25–40 → 35% · <25% → 0% | Trend attivo |
| C2 | EBITDA Margin (5) | Assoluta (allineata a C1, da confermare): ≥45% → 100% · 30–45 → 80% · 20–30 → 60% · 10–20 → 35% · <10% → 0% | Trend attivo |
| C3 | Operating Margin (25) | `✎ REVIEW` ≥30% → 100% · 20–30 → 80% · 12–20 → 60% · 5–12 → 35% · <5% → 0% | Trend attivo |
| C4 | Net Margin (18) | `✎ REVIEW` come C3: ≥30% → 100% · 20–30 → 80% · 12–20 → 60% · 5–12 → 35% · <5% → 0% | Negativa 2+ anni → red flag critico (spec) |
| C5 | FCF Margin (12) | `✎ REVIEW` come C3: ≥30% → 100% · 20–30 → 80% · 12–20 → 60% · 5–12 → 35% · <5% → 0% | Redistribuzioni Sez. 3E/3F spec applicate a monte |
| C6 | EPS Growth (10) | `DA SPEC` (Sez. 3 B-bis) | Cap 50% se da buyback con utile piatto |
| C7 | FCF/share Growth (18) | `DA SPEC` (Sez. 3 B-bis) | Guard anti-diluizione/buyback |
| C8 | ROIC (15) | Spread vs WACC: ≥ +8 p.p. → 100% · +4/+8 → 80% · 0/+4 → 60% · −4/0 → 35% · < −4 p.p. → 0% | Economic Spread spec (Sez. 3C) |
| C9 | ROE (3) | `✎ REVIEW` come C3: ≥30% → 100% · 20–30 → 80% · 12–20 → 60% · 6–12 → 35% · <6% → 0% | **Guard leva**: cap 60% se D/E > 2 |
| C10 | ROA (5) | `✎ REVIEW` ≥20% → 100% · 12–20 → 80% · 6–12 → 60% · 2–6 → 35% · <2% → 0% | |
| C11 | Debt/Equity (10) | ≤0,3 → 100% · 0,3–0,8 → 80% · 0,8–1,5 → 60% · 1,5–2,5 → 35% · >2,5 → 0% | Esenzioni settoriali spec via moduli dedicati |
| C12 | Debt/Assets (10) | ≤0,20 → 100% · 0,20–0,40 → 80% · 0,40–0,55 → 60% · 0,55–0,70 → 35% · >0,70 → 0% | |
| C13 | Altman-Z (5) | `✎ REVIEW` progressiva: ≥3,0 → 100% · 2,6–3,0 → 85% · 2,2–2,6 → 70% · 1,81–2,2 → 55% · 1,5–1,81 → 35% · 1,23–1,5 → 15% · <1,23 → 0% | Penalità additiva sul voto finale resa progressiva `⚠ DEVIAZIONE` (spec: 2 scalini): Z 1,6–1,81 → −5% · 1,4–1,6 → −10% · 1,23–1,4 → −15% · <1,23 → −20%. Settori esenti come da spec |
| C14 | SBC/Revenue (5) | `✎ REVIEW` più elastica, floor a 12%: ≤2% → 100% · 2–4 → 80% · 4–6 → 60% · 6–9 → 40% · 9–12 → 20% · >12% → 0% | Il red flag spec a >8% (tech) resta come **segnale** |
| C15 | CapEx/Revenue (5) | Relativa vs mediana industria: ≤0,7× → 100% · 0,7–1,0 → 80% · 1,0–1,3 → 60% · 1,3–1,8 → 35% · >1,8× → 0% | Leggerezza di capitale relativa al settore |
| C16 | CapEx/D&A (3) | A campana: 0,9–1,5 → 100% · 1,5–2,5 → 80% · 0,6–0,9 → 60% · >2,5 → 35% · <0,6 → 0% | <0,6 = sotto-investimento |
| C17 | R&D/Revenue (7) | Relativa vs mediana industria: ≥1,2× → 100% · 0,8–1,2 → 80% · 0,5–0,8 → 60% · <0,5× → 35% · =0 in settore R&D-intensivo → 0% | Settori senza R&D: **omessa + ri-basata** |
| C18 | Insider Trading (5) | 12 mesi: acquisti netti del C-suite → 100% · neutro → 60% · vendite programmate (10b5-1) → 50% · vendite nette non programmate → 20% · vendite massicce C-suite → 0% | `✎ REVIEW` estendere oltre gli US: registri internal dealing ufficiali UE (CONSOB, BaFin, AMF, FCA) → **task T18**. Dove non reperibile: omessa + ri-basata |
| C19 | Dividend Yield (16) | `✎ REVIEW` lordo: ≥10% coperto → 100% · 7–10 → 80% · 5–7 → 60% · 3–5 → 40% · 1–3 → 25% · <1% → 10% | **Yield-trap guard rafforzato**: ogni banda ≥7% richiede copertura FCF ≥ 1,3× E payout ≤90%, altrimenti cap 35%. Yield 0 → clausola redistribuzione Sez. 3E |
| C20 | Dividend Payout (10) | 30–60% → 100% · <30 → 80% · 60–75 → 60% · 75–90 → 35% · >90% o negativo → 0% | Cross-check sul payout FCF: vale il peggiore |
| C21 | Dividend Growth (10) | CAGR 5y: ≥8% → 100% · 5–8 → 80% · 2–5 → 60% · 0–2 → 35% · taglio nel quinquennio → 0% | Dividendi da <3 anni: omessa e segnalata |
| C22 | Buyback (5) | Riduzione share count ≥2%/anno → 100% · 0–2% → 70% · stabile → 50% · diluizione <2%/anno → 25% · >2%/anno → 0% | **Guard prezzo**: cap 50% se ricompra a P/E > 1,3× mediana storica |
| C23 | Price CAGR (5) | 5y: ≥8% → 100% · 3–8 → 80% · 0–3 → 50% · −5/0 → 25% · <−5% → 0% | Lettura value in C24 e return attribution |
| C24 | Multiple Expansion (Δ P/E) (5) | `DA SPEC` (contrazione premiata; value-trap guard cap 25%) | |
| C25 | Tax % (13) | Aliquota effettiva 3y: 15–28% stabile → 100% · 28–35 → 80% · 10–15 → 60% · >35% → 35% · <10% o volatile → 0% | |
| C26 | MOAT (25) | wide → 100% · narrow → 60% · none → 0% | `✎ REVIEW` metodo: replicare quello dello stock screener MVF in chat — **ricerca web del rating Morningstar pubblicato** per ticker, parsing dal risultato; tag [V] se ≥2 riscontri concordi, [U] se singolo → **task T19** (robustezza + termini d'uso). Inserimento/override manuale sempre possibile (§7). Finché assente: omessa + ri-basata + flag |
| C27 | Earnings Quality (15) | CCR ≥1,1 e Accruals ≤0 → 100% · CCR 0,9–1,1 → 80% · 0,7–0,9 → 60% · 0,5–0,7 → 35% · CCR <0,5 o Accruals >0,10 → 0% | Soglie allineate ai red flag spec (Sez. 9I) |

### §2-bis — Guard trasversali (prevalgono su tutto)

`DA SPEC`, in batch:
1. **Anti-buyback su EPS** (C6): g_EPS − g_utile > 5 p.p. con utile piatto/in calo → cap 50%.
2. **Anti-diluizione su FCF/share** (C7): g_FCF/share − g_FCF aggregato > 5 p.p. con FCF aggregato piatto/in calo → cap 50%.
3. **Value-trap su multiplo** (C24): multiplo contratto E (margini in calo O ricavi in calo 2y) → max 25%.
4. **Yield-trap** (C19): come da tabella, rafforzato.
5. **ROE-leva** (C9): cap 60% se D/E > 2.
6. Divergenza EPS↑/FCF-share piatta 2+ anni → red flag qualità utili.

---

## §3 — REIT, base 370

**Legenda di sezione** — REIT: società immobiliare quotata obbligata a
distribuire ~90% del reddito · AFFO: Adjusted Funds From Operations, la
"cassa vera" di un REIT (equivalente del FCF) · NOI: Net Operating Income,
reddito operativo degli immobili · Same-store NOI: crescita del NOI a
perimetro costante (senza acquisizioni) · Occupancy: tasso di occupazione
degli immobili · WALT: durata media residua ponderata dei contratti di
affitto · NAV: Net Asset Value, valore patrimoniale netto degli immobili ·
Cap rate: rendimento d'acquisto di un immobile · Accretion spread: cap rate
− costo del capitale (crea o distrugge valore comprando) · EBITDAre: EBITDA
rettificato per il settore immobiliare · P/AFFO: prezzo su AFFO (il "P/E dei
REIT").

Remapping e rubriche di AFFO/share Growth, Same-store NOI, Accretion Spread:
`DA SPEC` (Sez. 9B). Bande proposte per le dedicate senza rubrica:

| ID | Metrica (peso) | Bande livello | Note |
|---|---|---|---|
| R1 | Occupancy (15) | ≥97% → 100% · 94–97 → 80% · 90–94 → 60% · 85–90 → 35% · <85% → 0% | Da differenziare per sottosettore (T16) |
| R2 | WALT (15) | ≥8 anni → 100% · 5–8 → 80% · 3–5 → 60% · 1,5–3 → 35% · <1,5 → 0% | |
| R3 | Net Debt/EBITDAre (15) | ≤4,5× → 100% · 4,5–5,5 → 80% · 5,5–6,5 → 60% · 6,5–7,5 → 35% · >7,5× → 0% | |
| R4 | NAV Premium/Discount (15) | Sconto 5–20% con organico sano → 100% · par ±5% → 80% · premio 5–15% → 60% · premio >15% → 35% · premio >30% → 0% | **Guard NAV** (spec): sconto >20% mai oltre 60% senza conferme organiche |
| R5 | AFFO Margin (27) | Relativa vs mediana sottosettore: ≥1,15× → 100% · 0,95–1,15 → 80% · 0,80–0,95 → 60% · <0,80× → 35% | AFFO non validato → [U] (spec 6-bis G) |
| R6 | AFFO Payout (15) | ≤75% → 100% · 75–85 → 80% · 85–90 → 60% · 90–100 → 35% · >100% → 0% | >90% → red flag attenzione |

---

## §4 — BDC, base 299

**Legenda di sezione** — BDC: Business Development Company, veicolo quotato
che presta a medie imprese · NAV: valore netto degli attivi per azione ·
NII: Net Investment Income, reddito netto da investimenti (l'"utile" di una
BDC) · DNII: NII distribuibile · Non-accrual: prestiti in portafoglio che
hanno smesso di pagare · First-lien: prestiti con garanzia di primo grado
(più sicuri) · PIK: Payment-In-Kind, interessi pagati in titoli anziché
cassa (segnale di stress) · Spillover: reddito distribuibile accantonato ·
Base dividend: dividendo ordinario (esclusi gli extra) · Asset coverage:
attivi/debito, vincolo regolamentare (≥150%) · Hurdle: soglia minima di
rendimento prima delle commissioni di incentivo.

Rubriche `DA SPEC` (J.3): premio/sconto NAV, non-accrual, copertura NII.
Bande proposte per il resto:

| ID | Metrica (peso) | Bande livello |
|---|---|---|
| B1 | % first-lien (8) | ≥80% → 100% · 65–80 → 80% · 50–65 → 60% · 35–50 → 35% · <35% → 0% |
| B2 | Yield medio portafoglio (7) | A campana: 9–12% → 100% · 7–9 → 80% · 12–14 → 60% · <7% → 40% · >14% → 20% |
| B3 | % reddito PIK (15) | ≤2% → 100% · 2–4 → 75% · 4–6 → 50% · 6–8 → 25% · >8% → 0% |
| B4 | Gestione interna/esterna (7) | Interna → 100% · esterna allineata → 60% · esterna fee-heavy → 20% |
| B5 | Struttura commissionale (8) | Mgmt ≤1,25% + hurdle ≥7% + lookback → 100% · 1,5%/hurdle 7% → 70% · ≥1,75% senza lookback → 30% · peggio → 0% |
| B6 | Leva regolamentare (10) | 0,9–1,25× → 100% · 0,7–0,9 o 1,25–1,5 → 70% · <0,7 o 1,5–1,8 → 40% · >1,8× → 0% |
| B7 | Asset Coverage (10) | ≥200% → 100% · 180–200 → 80% · 165–180 → 60% · 150–165 → 30% · <150% → 0% |
| B8 | NII Margin (25) | ≥55% → 100% · 45–55 → 80% · 35–45 → 60% · 25–35 → 35% · <25% → 0% |
| B9 | DNII/spillover (22) | Coperto + spillover in accumulo → 100% · coperto → 70% · erosione → 35% · DNII < base div → 0% |
| B10 | NII/share Growth (10) | ≥6% → 100% · 3–6 → 80% · 0–3 → 50% · <0 → 0% |
| B11 | NAV/share Growth (8) | ≥3% → 100% · 1–3 → 80% · ±1% → 50% · −3/−1 → 25% · <−3% → 0% |
| B12 | Yield base (16) | 8–11% coperto → 100% · 6–8 → 80% · 11–13 → 60% · <6 → 50% · >13% → 30% |
| B13 | NII Payout (10) | ≤85% → 100% · 85–95 → 70% · 95–100 → 40% · >100% → 0% |
| B14 | Crescita base dividend (10) | ≥5% → 100% · 2–5 → 80% · 0–2 → 50% · taglio → 0% |

---

## §5 — MLP, base 309

**Legenda di sezione** — MLP: Master Limited Partnership (partnership
quotata US, tipicamente pipeline/midstream) · Midstream: trasporto e
stoccaggio di idrocarburi · DCF (qui): Distributable Cash Flow, cassa
distribuibile — NON il modello di valutazione DCF · DCF/unit: cassa
distribuibile per quota · Coverage: DCF/distribuzione (quanto è coperta la
cedola) · Fee-based: ricavi da tariffe fisse (vs esposti al prezzo delle
commodity) · Take-or-pay / MVC: contratti che pagano anche se il cliente non
usa la capacità · GP/LP: General/Limited Partner · IDR: Incentive
Distribution Rights, diritti che dirottano cassa al GP (male per i soci) ·
K-1: modulo fiscale US delle partnership (complicazione per l'italiano) ·
§1446: ritenuta US fino a ~37% sulle distribuzioni MLP a non-residenti.

Rubriche `DA SPEC` (K.3): coverage, % fee-based, Net Debt/EBITDA,
concentrazione. Bande proposte per il resto:

| ID | Metrica (peso) | Bande livello |
|---|---|---|
| M1 | Qualità contratti (7) | Take-or-pay/MVC >80% e durata >7y → 100% · 60–80% / 5–7y → 70% · 40–60% → 40% · <40% → 0% |
| M2 | Maint vs Growth CapEx (8) | Maint dichiarato + growth con ROIC > WACC → 100% · mix sano → 70% · indisciplinato → 30% · maint occultato → 0% |
| M3 | Backlog organico (7) | ≥5% EBITDA/anno → 100% · 2–5% → 70% · 0–2% → 40% · nullo → 20% |
| M4 | IDR / allineamento GP-LP (8) | IDR eliminati → 100% · con cap → 50% · pieni → 0% |
| M5 | Governance sponsor (7) | Sponsor solido senza conflitti → 100% · neutro → 60% · conflitti/overhang → 20% |
| M6 | DCF/unit Growth (18) | ≥6% → 100% · 3–6 → 80% · 0–3 → 50% · <0 → 0% + guard anti-diluizione `DA SPEC` |
| M7 | DCF Margin (22) | Relativa vs mediana midstream: ≥1,15× → 100% · 0,95–1,15 → 80% · 0,80–0,95 → 60% · <0,80× → 35% |
| M8 | Copertura interessi (10) | ≥4× → 100% · 3–4 → 80% · 2–3 → 60% · 1,5–2 → 35% · <1,5× → 0% |
| M9 | Distribution Yield (16) | 7–10% coperto → 100% · 5–7 → 80% · 10–12 → 60% · <5 → 50% · >12% → 30% |
| M10 | DCF Payout (10) | ≤70% → 100% · 70–80 → 80% · 80–90 → 60% · 90–100 → 35% · >100% → 0% |
| M11 | Distribution Growth (10) | ≥4% → 100% · 2–4 → 80% · 0–2 → 50% · taglio → 0% |

Overlay fiscale K-1/§1446 `DA SPEC` (K.7): fuori dal Voto, dentro il netto
Italia, ben visibile in UI ("attrito fiscale ALTO").

---

## §6 — Preferred (MVF-P), base 168

**Legenda di sezione** — Preferred: azione privilegiata, ibrido
azione/obbligazione a cedola fissa · Baby bond: obbligazione quotata a
piccolo taglio · Seniority: ordine di rimborso in caso di crisi · Equity
cushion: capitale azionario sotto il preferred (assorbe le perdite per
primo) · Cumulative: le cedole saltate si accumulano e vanno pagate ·
Call/YTC: diritto dell'emittente di rimborsare anticipatamente / rendimento
in caso di call · YTW: Yield-to-Worst, rendimento nello scenario peggiore ·
F2F: fixed-to-float, cedola che diventa variabile dopo una data · Par:
valore nominale (tipicamente $25) · Duration: sensibilità del prezzo ai
tassi · IG/HY: Investment Grade / High Yield (qualità creditizia) · QDI:
Qualified Dividend Income (trattamento fiscale US).

Rubriche `DA SPEC` (L.1): copertura, rating, YTW vs comparabile, cumulative,
call. Bande proposte per il resto:

| ID | Metrica (peso) | Bande livello |
|---|---|---|
| P1 | Seniority (8) | Baby bond/senior → 100% · preferred tradizionale → 70% · junior → 40% · deeply subordinated → 20% |
| P2 | Equity cushion (7) | Preferred ≤15% struttura → 100% · 15–30% → 70% · 30–50% → 40% · >50% → 0% |
| P3 | Solidità emittente (15) | MVF-S emittente ≥650 → 100% · 500–650 → 70% · 400–500 → 40% · <400 o gate → 0% (contagio `DA SPEC`) |
| P4 | Rischio esistenziale settore (10) | Stabile/regolato → 100% · ciclico → 60% · esistenziale → 0–20% |
| P5 | Fixed vs F2F (8) | F2F con reset sano → 100% · fixed con call vicina → 60% · perpetual fixed cedola bassa → 20% |
| P6 | Perpetual vs term (5) | Term ≤10y → 100% · term lungo → 70% · perpetual → 40% |
| P7 | Current yield (8) | ≥7% coperto → 100% · 5,5–7 → 70% · 4–5,5 → 40% · <4% → 10% |
| P8 | Prezzo vs par (7) | ≤95 → 100% · 95–100 → 80% · 100–103 → 50% · > call price → 0% |
| P9 | Duration (8) | ≤4y → 100% · 4–7 → 70% · 7–10 → 40% · >10y → 10% |
| P10 | Fiscale (5) | Ritenuta 15% treaty → 100% · 30% → 40% · §1446 → 0% |

---

## §7 — MOAT ed ESG: reperimento e inserimento

`✎ REVIEW` aggiornato dalla review:

**MOAT** — metodo primario: replicare il metodo dello stock screener MVF in
chat, cioè **ricerca web del rating Morningstar pubblicato** per il ticker,
con parsing del verdetto (wide/narrow/none). Tagging: [V] se ≥2 riscontri
concordi, [U] se riscontro singolo, campo vuoto se nessun riscontro (mai
inventare). Robustezza del parsing e verifica dei termini d'uso → task T19.
**L'inserimento manuale resta sempre disponibile e prevale** sul dato
reperito automaticamente (coda "da verificare" con link alla pagina IBKR del
titolo). Refresh annuale o su evento. Finché il moat manca: metrica omessa +
ri-basatura + flag "manca metrica importante".

**ESG** — inserimento manuale da IBKR **per area**: la maschera prevede
**quattro campi**: punteggio complessivo + **E** (ambiente) + **S**
(sociale) + **G** (governance), più il sotto-tag **Green** (basse
emissioni/economia circolare). Il pacchetto Etico richiede l'ESG inserito;
senza, il titolo resta "candidato Etico in attesa di verifica ESG".
Pre-filtro calcolato (prima dell'ESG): esclusioni settoriali dichiarate —
tabacco, carbone termico, armi controverse, gambling — **solo dentro il
pacchetto Etico**. Scala e soglia esatta: T17.

---

## §8 — Gate G1–G6 e red flag in batch

**Legenda di sezione** — Gate: condizione di esclusione strutturale (NO-BUY
a prescindere dal prezzo) · Red flag: segnalazione che NON blocca ·
Net Debt: debito totale − cassa · Copertura interessi: EBIT/oneri
finanziari · Diluizione: aumento del numero di azioni (riduce la quota di
ogni socio) · Goodwill: avviamento pagato nelle acquisizioni · Impairment:
svalutazione.

`DA SPEC` (Sez. 8-bis), soglie operative:

| Gate | Implementazione batch |
|---|---|
| G1 | FCF < 0 in tutti gli ultimi 5 FY (per classe: AFFO/NII/DCF). Ciclici: media normalizzata 7–10y < 0. Esenzione SaaS growth: Gross Margin > 70% E Revenue CAGR > 20% (proxy Sez. 9E, da confermare) |
| G2 | ROIC − WACC < 0 per ≥4 anni (REIT: accretion spread; se non reperibile → gate non valutabile, segnalato) |
| G3 | Net Debt/EBITDA > 6× **e** in aumento **e** EBIT/oneri < 1,5×. Esenti: leveraged-by-design (REIT, BDC, MLP, banche, utility) |
| G4 | Diluizione netta > 5%/anno per 3 anni **e** SBC/Rev > 8% (varianti di classe `DA SPEC`) |
| G5 | Altman-Z < 1,23 (settore non esente) **+** un secondo segnale tra: D/E > 3 · FCF < 0 in 2/3 FY · copertura interessi < 1,5× |
| G6 | **Non attivabile in batch** `⚠ DEVIAZIONE`: richiede giudizio di capital allocation. I suoi segnali generano red flag; G6 si attiva in Regime A |

Red flag: tutti quelli calcolabili della Sez. 8 alle soglie di spec, due
tabelle separate (critico/attenzione), mai bloccanti (V5). Conferma
multi-segnale `DA SPEC`.

---

## §9 — Fonti dati e DIP per mercato

**Legenda di sezione** — EDGAR: archivio ufficiale della SEC (USA) · XBRL:
formato dati strutturato dei bilanci · EDINET/DART/MOPS: equivalenti
ufficiali per Giappone/Corea/Taiwan · ESEF: formato XBRL obbligatorio UE dal
2021 · OAM: archivi nazionali UE dei documenti ufficiali · ADR: azione
estera quotata a New York · H-share: azione cinese quotata a Hong Kong ·
FY: anno fiscale completato · TTM: ultimi 12 mesi (VIETATO dalla spec: solo
FY completati).

**`✎ REVIEW` — Il DIP è multi-fonte, non anti-yfinance.** yfinance è una fonte
**legittima**; il punto è che va **validata** da almeno un'altra fonte
indipendente (TradingView, stockanalysis, EDGAR). Un dato è `[V]` quando ≥2
aggregatori concordano dopo normalizzazione, `[U]` con fonte singola o
conflitto, `[P]` solo da deposito ufficiale. Nessuna fonte è "cattiva" a
priori; conta la concordanza.

Stato di implementazione (bozza 1). Tre percorsi cablati e verificati:

| Percorso | Copertura | Fonti | Tag | Profondità | Stato |
|---|---|---|---|---|---|
| **EDGAR + stockanalysis** | USA + ADR | SEC EDGAR XBRL (fondamentali) + stockanalysis (prezzi) | **[P]** | serie multi-anno | ✅ cablato |
| **yfinance** | globale | yfinance, cross-validato con EDGAR/TradingView | [V]/[U] | serie multi-anno | ✅ codice (qui rate-limited; ok su VPS) |
| **TradingView** | globale (IT/DE/FR/UK/CH/JP/KR/TW/HK…) | scanner TradingView | **[U]** | **snapshot corrente** | ✅ cablato — non-US |

- **Non-US via TradingView = snapshot parziale dichiarato.** TradingView dà i
  fondamentali CORRENTI (margini, ROE/ROIC/ROA, leva, yield, P/E, crescita YoY)
  ma non le serie storiche complete → copertura 50-70% dichiarata, e tag `[U]`
  (fonte singola) → CS-S basso. È coerente con la spec (fuori dal perimetro SEC
  la profondità degrada per costruzione). Verificato: ENI/ASML/Nestlé/Toyota/
  Samsung/TSMC/LVMH/Shell producono un MVF-S parziale con caveat visibili.
- **Promozione a [V] sul VPS.** Quando yfinance è raggiungibile (produzione),
  fa da seconda fonte: yfinance ∩ TradingView concordi → `[V]`, e le serie
  storiche di yfinance alzano la copertura. La macchina di cross-validation
  (`fetchers.cross_validate`) è già generalizzabile a questo.
- **Prossimo salto di qualità (T22):** fonti ufficiali non-US (EDINET JP,
  DART KR, MOPS TW, ESEF UE) → tag `[P]` e profondità multi-anno anche fuori
  dagli USA. Grande lavoro, per-paese.

Regole di tagging (invariate, `DA SPEC` Sez. 6-bis):
- [P] solo ufficiale; [V] ≥2 fonti concordi dopo normalizzazione (tolleranze
  spec); [U] singola o conflitto.
- `✎ REVIEW` **Promozione [U] → [V]**: un dato annuale da fonte singola
  (sicura o meno) è promosso a [V] se **(a)** confermato da ≥2 altre
  piattaforme dopo normalizzazione, **oppure (b)** ricostruibile dalle
  trimestrali con quadratura (somma delle trimestrali ≈ annuale entro le
  tolleranze spec: ≤1% voci esatte, ≤1 p.p./2% relativo per i ratio).
- La **profondità annuale** abbassa il sub-score B del CS (completezza),
  **non** la provenienza: un bilancio ESEF è [P] a tutti gli effetti.
- CS-S **stabile per costruzione**: cambia solo cambiando le fonti (T4).
- Estrazione PDF: una tantum per FY, revisione a campione, cache. Estrazione
  inaffidabile → campo vuoto + segnalazione.

Forward (B1/B4 IQI): consensus yfinance se ≥3 stime → [C]; altrimenti
estrapolazione dal CAGR storico → [S] con cap 50% combinato `DA SPEC`.

---

## §10 — Pacchetti: regole di idoneità

Prerequisito di ogni tag (tranne All): **nessun gate attivo, nessun red flag
critico, copertura ≥75%**.

| Pacchetto | Regola di idoneità |
|---|---|
| **All** | Tutto l'universo con voto calcolato, gate inclusi (marcati) |
| **Difensivo** | `✎ REVIEW` Dividendo pagato da **≥10 anni senza tagli** E (**yield lordo ≥4%** OPPURE **crescita del dividendo forte e costante**: CAGR 5y ≥6% con aumento in ≥4 degli ultimi 5 anni). Più: payout ≤75% (REIT: AFFO payout ≤85%); FCF margin ≥8%; D/E ≤1,5; beta 5y ≤1,0; MVF-S ≥600; IQI-S ≥55. Badge: **Aristocrat** (≥25y aumenti), **King** (≥50y) |
| **Etico** | Pre-filtro esclusioni + ESG inserito ≥ soglia (per area, §7). Sotto-tag **Green** |
| **Innovativo** | Tag tematico ∈ {chip, nucleare, AI/software, quantum, robotica, spazio, cybersecurity, biotech, fintech, innovazione in altri settori} E (R&D/Rev ≥ mediana O Revenue CAGR 5y ≥10%); MVF-S ≥500. Liste curate approvate dal committente |
| **Emergenti** | Geografico: Cina (ADR/H), Corea, Taiwan; MVF-S ≥500; volatilità e impatto commissionale in evidenza |
| **PIR** | Emittente IT o UE con stabile organizzazione in Italia; conformità 70/25/5 a livello di paniere. Richiede intermediario dedicato (T10) |
| **Cedola mensile** | `✎ REVIEW` **Sottoinsieme stretto del Difensivo**: tutti i criteri Difensivo obbligatori + tag mese di pagamento; il costruttore combina per coprire ~12 mesi. Ranking per netto Italia |
| **Compounders** | ROIC ≥15% (o spread ≥ +5 p.p.) stabile 5y; FCF/share CAGR ≥8%; diluizione ≤0; MVF-S ≥650. Nessun requisito di yield |

Incroci = intersezione dei tag.

---

## §11 — Griglie profilo × pacchetto

Profili: **Prudente · Bilanciato · Dinamico · Aggressivo**.

| Sleeve | Prudente | Bilanciato | Dinamico | Aggressivo |
|---|---|---|---|---|
| Azionario (titoli + ETF azionari) | 20% | 40% | 60% | 80% |
| Obbligazionario | 60% | 45% | 25% | 10% |
| Reali (oro/commodities via ETC) | 5% | 5% | 8% | 5% |
| Liquidità/monetario | 15% | 10% | 7% | 5% |

- Innovativo/Emergenti per Prudente/Bilanciato: max 10%/20% come satellite.
- `✎ REVIEW` **Commissioni e fiscalità: MAI criteri sbarranti.** La
  composizione titoli singoli vs ETF per fascia di patrimonio (<€20K → 4–8
  titoli · €20–50K → 8–15 · €50–100K → 12–20) è **indicativa**. Il programma
  **segnala** — non blocca — quando qualcosa è mal ottimizzato
  (commissionalmente o fiscalmente) e mostra sempre il **confronto al
  netto**: `TSR netto atteso = crescita attesa + rendimento netto Italia −
  drag commissionale stimato`, così un titolo fiscalmente inefficiente ma
  con prospettive superiori può compensare **nei numeri**, non a sensazione.
- Obbligazionario e Reali: whitelist provvisoria minima approvata a mano
  (BOT/BTP + 5–10 ETF UCITS core + 1–2 ETC oro) in attesa di T1–T3.

---

## §12 — Catalogo alert (monitoraggio giornaliero)

`✎ REVIEW` **Gerarchia di evidenza**: le **zone d'acquisto raggiunte (A7)
hanno la stessa evidenza delle red flag** — il briefing "Attenzione oggi" ha
due sezioni di pari rango in testa: 🔴 **Rischi** (A1–A6, A10) e 🟢
**Occasioni** (A7, badge 🥇 OCCASIONE D'ORO quando MVF-S ≥ 800 e prezzo ≤
prezzo ideale).

| # | Evento | Cadenza |
|---|---|---|
| A1 | Gate G1–G6 scattato su titolo posseduto | Immediato |
| A2 | Nuovo red flag **critico** | Immediato |
| A3 | Taglio/sospensione dividendo | Immediato |
| A4 | Dividendo con copertura sotto soglia (payout FCF/AFFO/NII > 100%) | Immediato |
| A5 | Calo Voto MVF-S ≥ 50 punti | Al ricalcolo |
| A6 | Calo IQI-S ≥ 10 punti | Al ricalcolo |
| A7 | **Prezzo ≤ prezzo ideale (MoS pieno raggiunto)** — watchlist e universo, evidenza pari alle red flag | Giornaliero |
| A8 | Prezzo > fair value +15% su posseduto | Giornaliero |
| A9 | Earnings entro 7 giorni | Settimanale |
| A10 | CS-S < 50 o copertura < 75% | Al ricalcolo |
| A11 | Candidato migliore del posseduto (Δ MVF-S ≥ 100 E Δ IQI-S ≥ 15, stessa classe) — segnalazione, mai automatismo | Settimanale |

Canale: veicolo del briefing con canale dedicato **Proxima** (T8); dati
clienti solo su web app con login.

---

## §13 — Naming, versionamento, schema output

Ogni riga persistita porta (`DA SPEC` 11F + handoff Sez. 8):

```
ticker · isin · classe · versione MVF (4.0) · base_originale ·
base_effettiva · regime pesi (std / no-div / DDM-dimezzato) ·
regime esecuzione (S | A) · voto (MVF-S o MVF) · copertura % ·
metriche omesse[] · IQI-S (split A/B) · CS-S (+ [P]/[V]/[U]) ·
forward [G]/[C]/[S] · gate[] · red flag[] · tag pacchetti[] ·
tag tematici[] · badge (Aristocrat/King/OCCASIONE D'ORO) ·
ESG (totale + E + S + G + Green) · netto Italia ·
fair value indicativo + MoS + prezzo ideale ("indicativo — Regime S") ·
snapshot_id · data calcolo
```

- Regime S e Regime A mai visivamente identici.
- Log immutabile (D8): ogni sessione cliente salva snapshot di ciò che è
  stato mostrato + decisioni del cliente.

---

## §14 — Banco di prova (Q30)

- **Attesi in alto** (nessun gate): KO, JNJ, MO, MCD, TGT, WMT, SPGI · ENI.MI
  (netto Italia con ritenuta estera zero) · FRT (motore REIT; in bozza 1 la
  copertura REIT sarà bassa finché mancano AFFO/occupancy da IR — atteso
  badge "copertura insufficiente", non un voto pieno).
- **SPCE**: atteso **G1**. Se il motore non lo esclude, il motore è rotto.
- **LULU**: non verrà esclusa dai gate (profittevole, poco indebitata) — 
  corretto. Lo scarto passa da moat (moda = poco difendibile), multiplo caro
  (C24/B3), riconciliazione "qualità cara → watchlist". Voto alto + IQI
  basso = sistema che funziona.
- Falsi negativi: nessuno dei 9 titoli di qualità deve avere gate attivi.

---

## §15 — Fuori da questo documento

V. `TASKS-POSTICIPATI.md`: modulo ETF, obbligazioni, commodities, provider a
pagamento, canale Proxima, filiere briefing, PIR, verifiche IBKR, insider
non-US (T18), lookup moat robusto (T19).
