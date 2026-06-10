# PROXIMA-Main — Mappa del container

Container unico di tutto il materiale di business di **Proxima** (SCF *fee-only*).
Consolidato a giugno 2026 recuperando il lavoro che era sparso su più branch.

## Struttura

### `01-strategia/`
- **`piano-di-lancio/`** — strategia di rilancio €180K su 18 mesi (doc numerati
  00→70: executive summary, budget, fasi di lancio, canali, revenue forecast,
  organigramma, architettura agenti, traction, scenari, azioni immediate).
  Include struttura societaria SRL, iter OCF, costi di costituzione e timeline.
  *Già scritta per la SCF.*
- **`tassazione/`** — `italian-taxation.md`.
- **`competitor/`** — `40-analisi-competitor-scf.md`.

### `02-modello-previsionale/`
- **`funnel-model/`** — modello costi/ricavi: app React single-file
  (`proxima-funnel.html` + `model.js`, `controls.js`, `dashboard.js`…). Si apre
  in browser, slider per scenari su clienti, AUM, costi, cash flow.
- **`RICALIBRAZIONE-SCF.md`** — piano per portare il modello in versione SCF
  fee-only (prossimo lavoro tecnico). Attinge alle migliorie motore archiviate in
  `../99-archivio/modello-sim-agente-collegato/` (variante "-ac" + code review).

### `03-marketing/`
- **`strategia/proxima-marketing-strategy.md`** — strategia marketing completa.
- **`skills/`** — libreria di ~36 skill growth/marketing (SEO: `seo-audit`,
  `ai-seo`, `programmatic-seo`, `schema-markup`; CRO: `page-cro`, `form-cro`,
  `signup-flow-cro`; contenuti: `copywriting`, `content-strategy`, `social-content`;
  acquisizione: `paid-ads`, `cold-email`, `referral-program`, `launch-strategy`;
  prodotto/prezzo: `pricing-strategy`, `customer-research`, `revops`…). Conservate
  tutte, anche quelle non ancora usate.

### `04-briefing/`
- **`pipeline/`** — **copia** del codice della rassegna stampa / briefing
  (`screener.py`, `briefing_pipeline.py`, `mvf_valuation.py`, template…).
- ⚠ **La pipeline in produzione gira altrove.** Vedi `04-briefing/README.md`
  prima di modificare qualsiasi cosa: c'è un cron attivo che genera i briefing
  giornalieri.

### `05-branding/`
- Asset di brand + landing page (`contenuto-zip/index.html`) e zip originale.

### `99-archivio/`
- **`modello-sim-agente-collegato/`** — materiale del percorso **SIM / agente
  collegato** (art. 31-ter TUF), **abbandonato** a giugno 2026. Consolidato qui,
  ordinato, come riferimento storico. Alcune parti (costituzione SRL/OCF, migliorie
  al motore del funnel) restano riusabili per la SCF — vedi `99-archivio/README.md`.

## Stato e prossimi passi

1. ✅ Repo ripulito; materiale superato spostato in `99-archivio/`
   (i branch git obsoleti sono **tenuti**, non cancellati).
2. ✅ `main` impostato come branch di default pulito.
3. ▶ **Ricalibrare il modello previsionale** per la SCF fee-only
   (`02-modello-previsionale/RICALIBRAZIONE-SCF.md`).
4. ▶ Centralizzare in sicurezza la pipeline briefing (senza interrompere il cron).
