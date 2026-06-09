# PROXIMA-Main — Mappa del container

Container unico di tutto il materiale di business di **Proxima** (SCF *fee-only*).
Consolidato a giugno 2026 recuperando il lavoro che era sparso su più branch.

## Struttura

### `01-strategia/`
- **`piano-di-lancio/`** — strategia di rilancio €180K su 18 mesi (doc numerati
  00→70: executive summary, budget, fasi di lancio, canali, revenue forecast,
  organigramma, architettura agenti, traction, scenari, azioni immediate).
  *Già scritta per la SCF.*
- **`costituzione-e-regolatorio/`** — `10-struttura-societaria` (SRL ordinaria,
  capitale €50.000), `11-iter-regolatorio` (Albo OCF Sez. III, RC professionale),
  `12-costi-costituzione`, `13-timeline`. Più `_recuperato-16-srl-qualifiche-OCF`
  (recuperato dal modello SIM: utile per meccanica SRL + percorso OCF/esame).
- **`tassazione/`** — `italian-taxation.md`.
- **`competitor/`** — `40-analisi-competitor-scf.md`.
- **`_archivio-modello-sim/`** — materiale del modello **agente collegato/SIM**,
  ora abbandonato. Tenuto solo come riferimento storico (vedi `NOTA.md`).

### `02-modello-previsionale/`
- **`funnel-model/`** — modello costi/ricavi: app React single-file
  (`proxima-funnel.html` + `model.js`, `controls.js`, `dashboard.js`…). Si apre
  in browser, slider per scenari su clienti, AUM, costi, cash flow.
- **`_recuperato-funnel-agente-collegato/`** — variante "-ac" con migliorie al
  motore (cohort AUM, stagionalità, prelievi). Da saccheggiare per la
  ricalibrazione, **senza** la logica di split provvigionale verso la SIM.
- **`RICALIBRAZIONE-SCF.md`** — piano per portare il modello in versione SCF
  fee-only (prossimo lavoro tecnico).
- **`_recuperato-17-code-review-funnel.md`** — code review del motore (bug +
  formula ricavi), base tecnica per la ricalibrazione.

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

## Stato e prossimi passi

1. ✅ Repo ripulito, materiale consolidato qui sotto.
2. ▶ **Ricalibrare il modello previsionale** per la SCF fee-only
   (`02-modello-previsionale/RICALIBRAZIONE-SCF.md`).
3. ▶ Eliminare i branch obsoleti su GitHub (modello SIM/agente, branch già merged)
   — da fare con conferma.
4. ▶ Centralizzare in sicurezza la pipeline briefing (senza interrompere il cron).
