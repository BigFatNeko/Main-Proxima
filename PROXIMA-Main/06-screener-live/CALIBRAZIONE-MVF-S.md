# DOCUMENTO DI CALIBRAZIONE — MVF-S (Regime S, batch)

**Stato: PROPOSTA — da approvare riga per riga.**
Ogni banda numerica in questo documento è una proposta di calibrazione, non
specifica MVF. Dove la specifica MVF v4.0 fornisce già una rubrica, è marcata
`DA SPEC` e non si tocca. Dove questo documento devia dalla specifica, la
deviazione è marcata `⚠ DEVIAZIONE` con motivazione.

Come approvare: rispondi citando gli ID (es. "C4 ok, C11 troppo severa:
0,8–1,5 → 80%"). Ciò che non viene contestato si considera approvato alla
prima iterazione di build, ma resta modificabile in ogni momento.

---

## §0 — Perimetro di questo documento

Copre il **Regime S** (batch notturno, universo ampio, deterministico) e le
strutture condivise (pacchetti, alert, profili, schema dati). Il **Regime A**
(analisi completa on-demand su singolo titolo) applica la specifica MVF v4.0
integrale e non ha bisogno di calibrazione: le sue regole sono già scritte.

Fuori perimetro (task posticipati, v. `TASKS-POSTICIPATI.md`): modulo ETF,
screener obbligazionario, screener commodities, canale Proxima nel veicolo
del briefing.

---

## §1 — Formula generale di scoring

Per ogni metrica con peso `w`:

```
punteggio = w × clamp( frazione_livello + mod_trend + bonus_settore , 0 , 1 )
```

- **frazione_livello** — dalla tabella bande della metrica (0 / 0,20 / 0,35 /
  0,50 / 0,60 / 0,70 / 0,80 / 1,00 a seconda della banda).
- **mod_trend** — pendenza a 5 anni (fallback 3, mai meno — come da spec):
  miglioramento chiaro (Δ relativo > +10%) → **+0,10** · stabile → 0 ·
  deterioramento chiaro (Δ relativo < −10%) → **−0,10**.
  È l'implementazione della "Variation %" della spec (Sez. 3B) per le
  metriche che ne sono soggette; le esenzioni della spec restano esenti.
- **bonus_settore** — metrica ≥ 80° percentile della propria industria
  (peer group = mediana/percentili di industria calcolati in-universo, Q8)
  → **+0,10**. Solo bonus, nessun malus: la sottoperformance è già catturata
  dalle bande relative.
- **I guard prevalgono sempre** su livello, trend e bonus (cap
  anti-manipolazione, value-trap, anti-diluizione: §2-bis).

**Metriche non reperibili** → omesse + ri-basatura (Q6):
`Voto MVF-S = (grezzo / base_effettiva) × 1000`, con base_effettiva = base di
classe − pesi delle metriche omesse. Accanto al voto compare **sempre** la
copertura: `MVF-S 742/1000 · copertura 87% (mancano: MOAT 25, Insider 5)`.
Se la copertura scende sotto il **75%** della base di classe → badge
"copertura insufficiente" e il titolo non è proponibile in sessione senza
Regime A.

**Naming** (D4): `Voto MVF-S` (batch, parziale) ≠ `Voto MVF` (Regime A,
pieno). Mai mostrati con lo stesso nome o lo stesso stile visivo. Stessa
distinzione per `IQI-S` e `CS-S`.

---

## §2 — Motore COMMON, base 280 — bande per metrica

Legenda: `REL` = banda relativa alla mediana d'industria (per le metriche il
cui livello assoluto non è confrontabile tra settori). Le percentuali nelle
bande sono frazioni del peso.

| ID | Metrica (peso) | Bande livello | Note / guard |
|---|---|---|---|
| C1 | Gross Margin (15) | `REL` GM/mediana industria: ≥1,25× → 100% · 1,05–1,25 → 80% · 0,85–1,05 → 60% · 0,60–0,85 → 35% · <0,60× → 0% | Trend attivo |
| C2 | EBITDA Margin (5) | `REL` come C1 | Trend attivo |
| C3 | Operating Margin (25) | ≥25% → 100% · 15–25 → 80% · 8–15 → 60% · 3–8 → 35% · <3% → 0% | Assoluta: l'efficienza operativa ha un pavimento universale. Trend attivo |
| C4 | Net Margin (18) | ≥20% → 100% · 12–20 → 80% · 6–12 → 60% · 2–6 → 35% · <2% → 0% | Negativa 2+ anni → red flag critico (spec) |
| C5 | FCF Margin (12) | ≥15% → 100% · 10–15 → 80% · 5–10 → 60% · 0–5 → 35% · <0 → 0% | Redistribuzioni Sez. 3E/3F della spec applicate a monte |
| C6 | EPS Growth (10) | `DA SPEC` (Sez. 3 B-bis) | Cap 50% se da buyback con NI piatto (spec) |
| C7 | FCF/share Growth (18) | `DA SPEC` (Sez. 3 B-bis) | Guard anti-diluizione/buyback (spec) |
| C8 | ROIC (15) | Spread vs WACC: ≥ +8 p.p. → 100% · +4/+8 → 80% · 0/+4 → 60% · −4/0 → 35% · < −4 p.p. → 0% | Aggancia il ROIC al costo del capitale invece che a un valore assoluto — coerente con l'Economic Spread della spec (Sez. 3C). WACC dal CAPM esteso già implementato |
| C9 | ROE (3) | ≥20% → 100% · 15–20 → 80% · 10–15 → 60% · 5–10 → 35% · <5% → 0% | **Guard leva**: cap 60% se D/E > 2 (ROE drogato dal debito) |
| C10 | ROA (5) | ≥10% → 100% · 6–10 → 80% · 3–6 → 60% · 1–3 → 35% · <1% → 0% | |
| C11 | Debt/Equity (10) | ≤0,3 → 100% · 0,3–0,8 → 80% · 0,8–1,5 → 60% · 1,5–2,5 → 35% · >2,5 → 0% | Esenzioni settoriali spec (banche, utility…) via moduli dedicati |
| C12 | Debt/Assets (10) | ≤0,20 → 100% · 0,20–0,40 → 80% · 0,40–0,55 → 60% · 0,55–0,70 → 35% · >0,70 → 0% | |
| C13 | Altman-Z (5) | ≥3,0 → 100% · 2,6–3,0 → 80% · 1,81–2,6 → 60% · 1,23–1,81 → 20% · <1,23 → 0% | La **penalità additiva** −10%/−20% sul voto finale (spec Sez. 3D) resta separata e si somma. Settori esenti come da spec |
| C14 | SBC/Revenue (5) | ≤1% → 100% · 1–3 → 80% · 3–5 → 60% · 5–8 → 35% · >8% → 0% | >8% tech → red flag critico (spec) |
| C15 | CapEx/Revenue (5) | `REL` vs mediana industria: ≤0,7× → 100% · 0,7–1,0 → 80% · 1,0–1,3 → 60% · 1,3–1,8 → 35% · >1,8× → 0% | Premia la leggerezza di capitale *relativa al settore* |
| C16 | CapEx/D&A (3) | A campana: 0,9–1,5 → 100% · 1,5–2,5 → 80% · 0,6–0,9 → 60% · >2,5 → 35% · <0,6 → 0% | <0,6 = sotto-investimento (consuma gli asset); >2,5 = verifica disciplina (ROIC incrementale) |
| C17 | R&D/Revenue (7) | `REL` vs mediana industria: ≥1,2× → 100% · 0,8–1,2 → 80% · 0,5–0,8 → 60% · <0,5× → 35% · =0 in settore R&D-intensivo → 0% | Settori senza R&D (utility, staples…): metrica **omessa + ri-basata**, non punita |
| C18 | Insider Trading (5) | 12 mesi da Form 4: acquisti netti del C-suite → 100% · neutro/inattivo → 60% · vendite programmate 10b5-1 → 50% · vendite nette non programmate → 20% · vendite massicce C-suite → 0% | Solo US/ADR (EDGAR). Altrove: **omessa + ri-basata** |
| C19 | Dividend Yield (16) | Lordo: 3–6% → 100% · 2–3 → 80% · 6–8 coperto → 70% · 1–2 → 60% · <1% → 35% | **Yield-trap guard**: >8% → cap 35% salvo copertura FCF ≥ 1,3×. Yield 0 → clausola redistribuzione Sez. 3E (spec) |
| C20 | Dividend Payout (10) | 30–60% → 100% · <30 → 80% · 60–75 → 60% · 75–90 → 35% · >90% o negativo → 0% | Cross-check sul payout FCF: se payout FCF > 100% con payout utile sano → usa il peggiore |
| C21 | Dividend Growth (10) | CAGR 5y: ≥8% → 100% · 5–8 → 80% · 2–5 → 60% · 0–2 → 35% · taglio nel quinquennio → 0% | Dividendi da <3 anni: omessa e segnalata (spec) |
| C22 | Buyback (5) | Riduzione share count: ≥2%/anno → 100% · 0–2% → 70% · stabile → 50% · diluizione <2%/anno → 25% · diluizione >2%/anno → 0% | **Guard prezzo**: cap 50% se ricompra sistematicamente a P/E > 1,3× la propria mediana storica (distrugge valore) |
| C23 | Price CAGR (5) | 5y: ≥8% → 100% · 3–8 → 80% · 0–3 → 50% · −5/0 → 25% · <−5% → 0% | La lettura value del prezzo sta in C24 e nella return attribution, non qui |
| C24 | Multiple Expansion (Δ P/E) (5) | `DA SPEC` (contrazione premiata; value-trap guard cap 25%) | |
| C25 | Tax % (13) | Aliquota effettiva media 3y: 15–28% stabile → 100% · 28–35 → 80% · 10–15 → 60% · >35% → 35% · <10% o volatile → 0% | Tax bassa = utili non sostenibili a normalizzazione (spec red flag) |
| C26 | MOAT (25) | wide → 100% · narrow → 60% · none → 0% | **Fonte: Morningstar via IBKR, inserimento manuale** (§7). Finché non inserito: **omessa + ri-basata** + flag "manca metrica importante". ⚠ DEVIAZIONE dichiarata: in Regime S il moat può mancare; mai stimato da proxy |
| C27 | Earnings Quality (15) | CCR ≥1,1 e Accruals ≤0 → 100% · CCR 0,9–1,1 → 80% · 0,7–0,9 → 60% · 0,5–0,7 → 35% · CCR <0,5 o Accruals >0,10 → 0% | Soglie allineate ai red flag spec (Sez. 9I) |

### §2-bis — Guard trasversali (prevalgono su tutto)

`DA SPEC`, implementati così in batch:

1. **Anti-buyback su EPS** (C6): g_EPS − g_NetIncome > 5 p.p. con NI
   piatto/in calo → cap 50%.
2. **Anti-diluizione su FCF/share** (C7): g_FCF/share − g_FCF aggregato
   > 5 p.p. con FCF aggregato piatto/in calo → cap 50%.
3. **Value-trap su multiplo** (C24): multiplo contratto E (margini in calo O
   revenue in calo 2y) → max 25%.
4. **Yield-trap** (C19): come da tabella.
5. **ROE-leva** (C9): come da tabella.
6. Divergenza EPS↑/FCF-share piatta 2+ anni → red flag qualità utili
   (segnala, non blocca).

---

## §3 — REIT, base 370

Remapping, riallocazioni e metriche con rubrica (AFFO/share Growth,
Same-store NOI, Accretion Spread) sono `DA SPEC` (Sez. 9B). Bande proposte
per le dedicate senza rubrica:

| ID | Metrica (peso) | Bande livello | Note |
|---|---|---|---|
| R1 | Occupancy (15) | ≥97% → 100% · 94–97 → 80% · 90–94 → 60% · 85–90 → 35% · <85% → 0% | Soglie da rivedere per sottosettore (net-lease vs office vs hotel) alla prima taratura |
| R2 | WALT (15) | ≥8 anni → 100% · 5–8 → 80% · 3–5 → 60% · 1,5–3 → 35% · <1,5 → 0% | |
| R3 | Net Debt/EBITDAre (15) | ≤4,5× → 100% · 4,5–5,5 → 80% · 5,5–6,5 → 60% · 6,5–7,5 → 35% · >7,5× → 0% | Spec: 5,5–6,0 "sano" per net-lease → banda 80 |
| R4 | NAV Premium/Discount (15) | Sconto 5–20% con organico sano → 100% · par ±5% → 80% · premio 5–15% → 60% · premio >15% → 35% · premio >30% → 0% | **Guard NAV** (spec): sconto >20% NON premiato oltre 60% finché same-store NOI e occupancy non confermano; sottosettori a rischio strutturale (office/mall/timber/hotel) mai oltre 60% da sconto |
| R5 | AFFO Margin (27) | `REL` vs mediana sottosettore REIT: ≥1,15× → 100% · 0,95–1,15 → 80% · 0,80–0,95 → 60% · <0,80× → 35% | AFFO da fonte non validata → [U] e CS giù (spec 6-bis G) |
| R6 | AFFO Payout (15) | ≤75% → 100% · 75–85 → 80% · 85–90 → 60% · 90–100 → 35% · >100% → 0% | >90% → red flag attenzione (spec) |

---

## §4 — BDC, base 299

Rubriche `DA SPEC` (J.3): premio/sconto NAV, non-accrual, copertura NII del
base dividend. Bande proposte per il resto:

| ID | Metrica (peso) | Bande livello |
|---|---|---|
| B1 | % first-lien / senior secured (8) | ≥80% → 100% · 65–80 → 80% · 50–65 → 60% · 35–50 → 35% · <35% → 0% |
| B2 | Yield medio ponderato portafoglio (7) | A campana: 9–12% → 100% · 7–9 → 80% · 12–14 → 60% · <7% → 40% · >14% → 20% (yield estremo = rischio credito, non pregio) |
| B3 | % reddito PIK/non-cash (15) | ≤2% → 100% · 2–4 → 75% · 4–6 → 50% · 6–8 → 25% · >8% → 0% |
| B4 | Gestione interna vs esterna (7) | Interna → 100% · esterna con fee allineate → 60% · esterna fee-heavy → 20% |
| B5 | Struttura commissionale (8) | Mgmt ≤1,25% + incentive con hurdle ≥7% e total-return lookback → 100% · 1,5%/hurdle 7% → 70% · ≥1,75% senza lookback → 30% · peggio → 0% |
| B6 | Leva regolamentare (slot D/E, 10) | 0,9–1,25× → 100% · 0,7–0,9 o 1,25–1,5 → 70% · <0,7 o 1,5–1,8 → 40% · >1,8× → 0% |
| B7 | Asset Coverage (slot D/A, 10) | ≥200% → 100% · 180–200 → 80% · 165–180 → 60% · 150–165 → 30% · <150% → 0% |
| B8 | NII Margin (slot Op. Margin, 25) | ≥55% → 100% · 45–55 → 80% · 35–45 → 60% · 25–35 → 35% · <25% → 0% |
| B9 | DNII/spillover (slot FCF Margin, 22) | Base div coperto + spillover in accumulo → 100% · coperto senza spillover → 70% · erosione spillover → 35% · DNII < base div → 0% |
| B10 | NII/share Growth (10) | CAGR: ≥6% → 100% · 3–6 → 80% · 0–3 → 50% · <0 → 0% |
| B11 | NAV/share Growth (8) | ≥3% → 100% · 1–3 → 80% · ±1% → 50% · −3/−1 → 25% · <−3% → 0% |
| B12 | Yield base (16) | 8–11% coperto → 100% · 6–8 → 80% · 11–13 → 60% · <6 → 50% · >13% → 30% (supplemental esclusi dal run-rate, `DA SPEC` J.5) |
| B13 | NII Payout (10) | ≤85% → 100% · 85–95 → 70% · 95–100 → 40% · >100% → 0% |
| B14 | Crescita base dividend (10) | ≥5% → 100% · 2–5 → 80% · 0–2 → 50% · taglio → 0% |

---

## §5 — MLP, base 309

Rubriche `DA SPEC` (K.3): coverage, % fee-based, Net Debt/EBITDA,
concentrazione. Bande proposte per il resto:

| ID | Metrica (peso) | Bande livello |
|---|---|---|
| M1 | Qualità contratti (7) | Take-or-pay/MVC >80% e durata media >7y → 100% · 60–80% / 5–7y → 70% · 40–60% → 40% · <40% → 0% |
| M2 | Maint vs Growth CapEx (8) | Maint dichiarato separatamente + growth con ROIC incrementale > WACC → 100% · mix sano non dettagliato → 70% · growth indisciplinato → 30% · maint occultato nel growth → 0% |
| M3 | Backlog organico (7) | ≥5% EBITDA/anno contrattualizzato → 100% · 2–5% → 70% · 0–2% → 40% · nullo → 20% |
| M4 | IDR / allineamento GP-LP (8) | IDR eliminati → 100% · IDR con cap → 50% · IDR pieni → 0% |
| M5 | Governance sponsor (7) | Sponsor IG senza conflitti → 100% · neutro → 60% · conflitti/overhang di cessione → 20% |
| M6 | DCF/unit Growth (slot EPS, 18) | ≥6% → 100% · 3–6 → 80% · 0–3 → 50% · <0 → 0% + guard anti-diluizione `DA SPEC` (cap 25%) |
| M7 | DCF Margin (slot FCF Margin, 22) | `REL` vs mediana midstream: ≥1,15× → 100% · 0,95–1,15 → 80% · 0,80–0,95 → 60% · <0,80× → 35% |
| M8 | Copertura interessi (slot D/A, 10) | ≥4× → 100% · 3–4 → 80% · 2–3 → 60% · 1,5–2 → 35% · <1,5× → 0% |
| M9 | Distribution Yield (16) | 7–10% coperto → 100% · 5–7 → 80% · 10–12 → 60% · <5 → 50% · >12% → 30% |
| M10 | DCF Payout (10) | ≤70% → 100% · 70–80 → 80% · 80–90 → 60% · 90–100 → 35% · >100% → 0% |
| M11 | Distribution Growth (10) | ≥4% → 100% · 2–4 → 80% · 0–2 → 50% · taglio → 0% |

Overlay fiscale K-1/§1446 `DA SPEC` (K.7): fuori dal Voto, dentro il netto
Italia e ben visibile nella UI ("attrito fiscale ALTO").

---

## §6 — Preferred (MVF-P), base 168

Rubriche `DA SPEC` (L.1): copertura, rating, YTW vs comparabile, cumulative,
call. Bande proposte per il resto:

| ID | Metrica (peso) | Bande livello |
|---|---|---|
| P1 | Seniority (8) | Baby bond/senior → 100% · preferred tradizionale → 70% · junior/subordinato → 40% · deeply subordinated → 20% |
| P2 | Equity cushion (7) | Preferred ≤15% della struttura → 100% · 15–30% → 70% · 30–50% → 40% · >50% → 0% |
| P3 | Solidità emittente (15) | MVF-S emittente ≥650 → 100% · 500–650 → 70% · 400–500 → 40% · <400 o gate attivo → 0% (contagio `DA SPEC` L.4) |
| P4 | Rischio esistenziale settore (10) | Settore stabile/regolato → 100% · ciclico → 60% · esistenziale (spec cita es. cannabis) → 0–20% |
| P5 | Fixed vs fixed-to-float (8) | F2F con reset a spread sano → 100% · fixed con call ravvicinata → 60% · perpetual fixed a cedola bassa → 20% |
| P6 | Perpetual vs term (5) | Term ≤10y → 100% · term lungo → 70% · perpetual → 40% |
| P7 | Current/stripped yield (8) | ≥7% coperto → 100% · 5,5–7 → 70% · 4–5,5 → 40% · <4% → 10% |
| P8 | Prezzo vs par (7) | ≤95 → 100% · 95–100 → 80% · 100–103 → 50% · > call price → 0% (`DA SPEC` upside negativo) |
| P9 | Duration (8) | ≤4y → 100% · 4–7 → 70% · 7–10 → 40% · >10y → 10% |
| P10 | Fiscale investitore (5) | Ritenuta 15% treaty → 100% · 30% → 40% · §1446 → 0% |

---

## §7 — MOAT ed ESG: flusso semi-automatico da IBKR

Decisione D3/Q21: la fonte è **Morningstar (moat) e il punteggio ESG visti
dentro IBKR**, considerati benchmark affidabili. Punto onesto sul quale devi
sapere come stanno le cose:

- I dati visibili nel tuo account IBKR sono **licenziati per consultazione
  personale**. Le API IBKR (TWS/Web) espongono alcuni fondamentali di terze
  parti ma, a oggi, **non** il moat Morningstar né in modo certo l'ESG; lo
  scraping del Client Portal violerebbe i termini d'uso. → task dedicato:
  verificare in fase di build cosa espongono lecitamente le API IBKR.
- Conseguenza di design: **inserimento manuale assistito, solo per la rosa**
  (mai per l'universo intero). Il pre-filtro quantitativo riduce l'universo a
  qualche centinaio di candidati; per quelli la UI mostra una coda "moat/ESG
  da inserire" con link diretto alla pagina IBKR del titolo: tu guardi,
  clicchi wide/narrow/none e il punteggio ESG, fine. Il moat cambia
  lentamente → refresh annuale o su evento, non un lavoro continuo.
- Finché il dato manca: metrica omessa + ri-basatura + flag (Q6). Il pacchetto
  **Etico** richiede l'ESG inserito: senza, il titolo resta "candidato Etico
  in attesa di verifica ESG", mai idoneo automaticamente.
- Pre-filtro Etico calcolato (prima dell'ESG manuale): esclusioni settoriali
  dichiarate — tabacco, carbone termico, armi controverse, gambling —
  **solo dentro il pacchetto Etico** (Altria resta idonea altrove).
  Raffinamento **Green**: sotto-tag per basse emissioni/economia circolare,
  assegnato insieme all'ESG manuale.

---

## §8 — Gate G1–G6 e red flag in batch

`DA SPEC` (Sez. 8-bis), con le soglie operative che la spec lascia aperte:

| Gate | Implementazione batch |
|---|---|
| G1 | FCF < 0 in tutti gli ultimi 5 FY (classe: AFFO/NII/DCF). Ciclici: media normalizzata 7–10y < 0. Esenzione SaaS growth `DA SPEC` (unit economics) → in batch la esenzione scatta se Gross Margin > 70% e Revenue CAGR > 20% (proxy Sez. 9E, da confermare) |
| G2 | ROIC − WACC < 0 per ≥4 anni (REIT: accretion spread, se reperibile; altrimenti gate non valutabile → segnalato) |
| G3 | Net Debt/EBITDA > 6× **e** in aumento **e** EBIT/oneri < 1,5×. Esenti: leveraged-by-design `DA SPEC` (REIT, BDC, MLP, banche, utility) |
| G4 | Diluizione netta > 5%/anno per 3 anni **e** SBC/Rev > 8% (varianti di classe `DA SPEC`) |
| G5 | Altman-Z < 1,23 (settore non esente) **+** almeno un secondo segnale tra: D/E > 3 · FCF < 0 in 2 degli ultimi 3 FY · copertura interessi < 1,5× |
| G6 | **Non attivabile in batch** ⚠ DEVIAZIONE dichiarata: richiede giudizio di capital allocation (Morningstar + M&A). In batch i suoi segnali (impairment goodwill ricorrenti, M&A seriali con ROIC in calo) generano solo red flag; G6 si attiva in Regime A |

Red flag: tutti quelli calcolabili della Sez. 8 implementati alle soglie di
spec, due tabelle separate (critico/attenzione), mai bloccanti (V5).
Conferma multi-segnale `DA SPEC`: nessun segnale singolo con storia di falsi
positivi esclude da solo.

---

## §9 — Fonti dati e DIP per mercato (stack gratuito quasi-definitivo)

Filosofia fissata (Decisioni, nota B): tutto il gratuito strutturato da
subito, PDF inclusi, annuale = attendibile ma meno profondo, niente crescita
progressiva del CS.

| Mercati | Fonte primaria | Tag | Profondità | Cross-validation |
|---|---|---|---|---|
| USA + ADR (incl. cinesi/EU quotate US) | SEC EDGAR XBRL | [P] | Trimestrale | yfinance |
| Giappone | EDINET API v2 | [P] | Trimestrale | yfinance |
| Corea | DART/OpenDART | [P] | Trimestrale | yfinance |
| Taiwan | MOPS | [P] | Trimestrale | yfinance |
| UE (Italia, Germania, Francia, …) | ESEF via filings.xbrl.org + OAM | [P] | **Annuale** | yfinance (trimestrali → [V]/[U]) |
| UK | ESEF/NSM + Companies House iXBRL | [P] | Annuale | yfinance |
| CH, Canada, Australia, HK (H-share), Singapore, NZ, Israele | Bilancio annuale ufficiale PDF (estrazione assistita, cache annuale) | [V] | Annuale | yfinance |
| Prezzi (tutti) | yfinance con retry/backoff | — | — | SLA prezzi live = task provider |

Regole:
- Il tagging DIP segue la spec (Sez. 6-bis): [P] solo da fonte ufficiale;
  [V] con ≥2 fonti concordi dopo normalizzazione (tolleranze di spec);
  [U] singola fonte o conflitto.
- La **profondità annuale** abbassa il sub-score B del CS (completezza
  storico trimestrale), **non** il sub-score A (provenienza): un bilancio
  ESEF è [P] a tutti gli effetti. È l'implementazione di "attendibile ma
  meno profondo".
- Il CS-S risultante è **stabile per costruzione**: cambia solo se cambiano
  le fonti (provider a pagamento = task posticipato).
- Estrazione PDF: una tantum per FY, revisione a campione, cache nel DB. Se
  l'estrazione non è affidabile per un titolo → campo vuoto + segnalazione
  (mai inventare).

Forward (B1/B4 dell'IQI): consenso analisti da yfinance se ≥3 stime → [C];
altrimenti estrapolazione dal CAGR storico → [S] con cap 50% combinato
`DA SPEC` (Sez. 6-bis F). In batch la convinzione resta quindi
strutturalmente ≤ "Media": corretto così, è il Regime A che la alza.

---

## §10 — Pacchetti: regole di idoneità (tag per titolo)

Un titolo può portare più tag. I tag si calcolano nel batch; la composizione
del portafoglio resta al consulente (D1). Prerequisito di ogni tag (tranne
All): **nessun gate attivo, nessun red flag critico, copertura ≥75%**.

| Pacchetto | Regola di idoneità proposta |
|---|---|
| **All** | Nessun filtro: tutto l'universo con voto calcolato, gate inclusi (marcati). "Zero limiti" |
| **Difensivo** | Dividendo pagato da ≥10 anni senza tagli (tier "forte" spec V7) **oppure** streak di aumenti ≥10y; yield lordo ≥2,5%; payout ≤75% (REIT: AFFO payout ≤85%); FCF margin ≥8%; D/E ≤1,5; beta 5y ≤1,0; MVF-S ≥600; IQI-S ≥55. Badge separati: **Aristocrat** (≥25y aumenti), **King** (≥50y) |
| **Etico** | Pre-filtro esclusioni (tabacco, carbone termico, armi controverse, gambling) + ESG IBKR inserito ≥ soglia (proposta: fascia "medium risk" o migliore — la scala esatta la fissiamo sul primo lotto reale). Sotto-tag **Green**: basse emissioni / economia circolare (con l'ESG manuale) |
| **Innovativo** | Tag tematico ∈ {chip, nucleare, AI/software, quantum, robotica, spazio, cybersecurity, biotech, fintech, innovazione in altri settori} **e** (R&D/Rev ≥ mediana industria **o** Revenue CAGR 5y ≥10%); MVF-S ≥500 (soglia più permissiva: è il pacchetto growth). Classificazione tematica: mappatura industry + liste curate per i pure-play che le industry non catturano (quantum, AI) — proposte da Claude, **approvate da te** prima dell'ingresso in lista |
| **Emergenti** | Geografico (Q19): domicilio/listing Cina (ADR/H), Corea, Taiwan; MVF-S ≥500; nota volatilità e impatto commissionale in evidenza |
| **PIR** | Emittente italiano o UE con stabile organizzazione in Italia; badge di conformità ai vincoli 70/25/5 calcolato **a livello di paniere**, non di titolo. ⚠ Richiede intermediario italiano dedicato (task posticipato: scelta broker + verifica commercialista) |
| **Cedola mensile** | Sottoinsieme income (Difensivo ∪ REIT/BDC idonei) con tag del **mese di pagamento**; il costruttore di portafoglio combina i titoli per coprire ~12 mesi di accrediti. Ranking interno per netto Italia |
| **Compounders** | ROIC ≥15% (o spread ≥ +5 p.p.) stabile 5y; FCF/share CAGR ≥8%; diluizione ≤0 (share count stabile o in calo); MVF-S ≥650. Nessun requisito di yield |

Incroci = intersezione dei tag (Etico+Difensivo, Emergenti+Innovativo, …),
già gratis con questo schema.

---

## §11 — Griglie profilo × pacchetto (PROPOSTA da approvare)

Profili (allineabili al vostro questionario di adeguatezza quando esiste):
**Prudente · Bilanciato · Dinamico · Aggressivo**.

Ripartizione base per profilo (percentuali del portafoglio):

| Sleeve | Prudente | Bilanciato | Dinamico | Aggressivo |
|---|---|---|---|---|
| Azionario (titoli singoli + ETF azionari) | 20% | 40% | 60% | 80% |
| Obbligazionario (govies + ETF obblig.) | 60% | 45% | 25% | 10% |
| Reali (oro/commodities via ETC) | 5% | 5% | 8% | 5% |
| Liquidità/monetario | 15% | 10% | 7% | 5% |

Il pacchetto scelto governa la **composizione dello sleeve azionario**, non
le proporzioni tra sleeve (quelle sono del profilo). Vincoli aggiuntivi:

- Pacchetti Innovativo/Emergenti per profili Prudente/Bilanciato: max 10%/20%
  del portafoglio totale come satellite; il resto dello sleeve azionario va a
  Difensivo/Compounders o ETF core.
- Quota titoli singoli vs ETF core dentro lo sleeve azionario, per patrimonio
  (regola commissionale Q10, taglio minimo ~€800–1.000 a titolo):
  <€20K → 0–30% titoli singoli (4–8 posizioni) · €20–50K → 30–60%
  (8–15 posizioni) · €50–100K → 50–80% (12–20 posizioni).
- Obbligazionario e Reali: **in attesa dei moduli dedicati** (task) si parte
  con una whitelist provvisoria minima approvata a mano (BOT/BTP + 5–10 ETF
  UCITS core + 1–2 ETC oro), dichiarata come provvisoria.
- Ogni portafoglio proposto mostra l'**impatto commissionale stimato**
  (n. ordini × minimi di commissione / importo) prima della conferma.

---

## §12 — Catalogo alert (monitoraggio titoli posseduti) — approvato Q27

Batch giornaliero sui portafogli clienti; briefing "Attenzione oggi" solo a
eccezioni (niente rumore quotidiano). Soglie proposte:

| # | Evento | Soglia |
|---|---|---|
| A1 | Gate G1–G6 scattato su titolo posseduto | Immediato, priorità massima |
| A2 | Nuovo red flag **critico** | Immediato |
| A3 | Taglio/sospensione del dividendo annunciato | Immediato |
| A4 | Dividendo annunciato con copertura sotto soglia (payout FCF/AFFO/NII > 100%) | Immediato |
| A5 | Calo Voto MVF-S ≥ 50 punti al ricalcolo | Al ricalcolo fondamentali |
| A6 | Calo IQI-S ≥ 10 punti | Al ricalcolo |
| A7 | Prezzo entrato in zona d'acquisto (≤ prezzo ideale) — per candidati in watchlist | Giornaliero |
| A8 | Prezzo > fair value +15% su titolo posseduto (valutare presa di profitto) | Giornaliero |
| A9 | Earnings/trimestrale in arrivo entro 7 giorni | Settimanale |
| A10 | CS-S sceso sotto 50 (dati diventati inaffidabili) o copertura < 75% | Al ricalcolo |
| A11 | Candidato migliore del posseduto nello stesso ruolo (Δ MVF-S ≥ 100 **e** Δ IQI-S ≥ 15, stessa classe) — **segnalazione**, mai raccomandazione automatica (Q14) | Settimanale |

Canale: stesso veicolo del briefing mattutino con **canale dedicato Proxima**
(accanto ad A e V) — ma i dati clienti vivono sulla web app con login, non su
pagine pubbliche (Q27/Q28). Dettaglio implementativo in fase di build.

---

## §13 — Naming, versionamento, schema output

Ogni riga persistita porta (`DA SPEC` 11F + handoff Sez. 8):

```
ticker · isin · classe (V1: chiave logica) · versione MVF (4.0) ·
base_originale · base_effettiva (post ri-basatura) · regime pesi
(std / no-div / DDM-dimezzato) · regime esecuzione (S | A) ·
voto (MVF-S o MVF) · copertura % · metriche omesse[] · IQI-S (A/B split) ·
CS-S (+ composizione [P]/[V]/[U]) · forward tags [G]/[C]/[S] ·
gate attivi[] · red flag[] (critici/attenzione) · tag pacchetti[] ·
tag tematici[] · badge (Aristocrat/King/…) · netto Italia (se distribuisce) ·
fair value indicativo + MoS + prezzo ideale (marcati "indicativo — Regime S") ·
snapshot_id · data calcolo
```

- Regime S e Regime A **mai** visivamente identici in UI (handoff Sez. 2C).
- Fair value in Regime S: i modelli calcolabili (Graham/DCF/EPV con dati
  strutturati) girano e producono un prezzo ideale **indicativo**; la
  versione difendibile davanti al cliente è quella del Regime A. Entrambi
  etichettati per quello che sono.
- Log immutabile (D8): ogni sessione cliente salva snapshot_id di tutto ciò
  che è stato mostrato/proposto + decisioni del cliente.

---

## §14 — Banco di prova (Q30)

Prima validazione del motore, prevista come test automatico:

- **Attesi in alto** (MVF-S ≥ ~650 e nessun gate): KO, JNJ, MO, MCD, TGT,
  WMT, SPGI (common) · ENI.MI (common, netto Italia con w_home=0) · FRT
  (motore REIT, atteso idoneo Difensivo con badge King — streak più lungo
  del settore REIT).
- **SPCE (Virgin Galactic)**: atteso **G1** (distruzione di cassa
  strutturale) → NON INVESTIBILE a prescindere dal prezzo. Se il motore non
  lo esclude, il motore è rotto.
- **LULU (lululemon)**: caso di test intenzionale — è profittevole, poco
  indebitata, ROIC alto: **non** verrà esclusa dai gate, e questo è
  corretto. Il tuo scarto passa da: moat (moda = vantaggio non difendibile →
  none/narrow, deciso da te via Morningstar), multiplo storicamente caro
  (C24 + B3 dell'IQI bassi), riconciliazione Δ = qualità cara → watchlist.
  Se LULU esce con MVF-S alto ma IQI-S basso e "qualità cara", il sistema
  sta funzionando: il Voto misura l'azienda, l'IQI l'investimento.
- Test dei falsi negativi: nessuno dei 9 titoli di qualità deve avere gate
  attivi o copertura < 75% (se accade, è un problema di dati, non di
  giudizio — da risolvere prima del go-live).

---

## §15 — Cosa NON è in questo documento

Rimandato con reminder in `TASKS-POSTICIPATI.md`: modulo ETF (regole in
arrivo da te), screener obbligazionario, screener commodities, provider a
pagamento/SLA prezzi live, canale Proxima nel veicolo briefing, filiere
aggiuntive nel briefing mattutino, PIR (broker + commercialista), verifica
API IBKR, perimetro esecuzione ordini SCF.
