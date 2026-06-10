# HANDOFF — Nuovo Modello Previsionale Costi/Ricavi per Proxima SCF

## Chi sei e cosa devi fare

Sei in una sessione fresca di Claude Code. Il tuo compito: costruire da zero un **modello previsionale costi/ricavi interattivo a 36 mesi** per Proxima SRL, una **Società di Consulenza Finanziaria (SCF)** indipendente fee-only italiana.

Il modello va costruito come file HTML self-contained (React 18 + Recharts + Babel, nessun build step), apribile in qualsiasi browser.

---

## Cos'è Proxima

Proxima SRL è una **SCF fee-only** (art. 18-bis TUF) iscritta alla Sezione III dell'Albo OCF. Due fondatori, target risparmiatori retail con patrimonio <€100K. Nessun prodotto finanziario venduto — solo consulenza indipendente a parcella.

**Modello di revenue:** parcella annuale fissa per fascia patrimoniale.

| Fascia Patrimonio | Parcella Annua | % clienti stimata |
|-------------------|----------------|-------------------|
| Fino a €20.000 | €250 | 30% |
| €20.001 – €50.000 | €500 | 35% |
| €50.001 – €100.000 | €800 | 25% |
| Oltre €100.000 | €1.200 | 10% |

**ARPU ponderato: €490/anno** (include sconto 20% early-adopter sui primi 50 clienti).

**MRR = totalClients × ARPU / 12**

---

## Repository & Branch

- **Repo:** `bigfatneko/main-marketing`
- **Branch di sviluppo:** `claude/project-launch-strategy-8cuWN`
- **Directory di lavoro:** `.agents/launch-strategy-180k/funnel-model/`
- **Output atteso:** `proxima-funnel-scf.html` (file self-contained)

---

## Cosa esiste già nel repo (NON riscrivere — solo riferimento)

Sul branch `claude/project-launch-strategy-8cuWN`:
- 16 documenti strategici in `.agents/launch-strategy-180k/` (regolatorio, costi, budget, KPI, fiscalità)
- Un vecchio funnel model (`proxima-funnel.html`, 81KB) — modello SCF semplificato, **da NON riusare** come base

Sul branch `claude/sim-launch-cost-analysis-bQpgG`:
- `proxima-funnel-ac.html` (1711 righe) — modello per "Agente Collegato SIM" con architettura avanzata. **Usa questo come riferimento architetturale**, ma la logica di revenue è diversa (AUM-based vs parcella fissa).

---

## Architettura di riferimento (da `proxima-funnel-ac.html`)

File HTML self-contained con cinque `<script type="text/babel">`, tutto su `window.PROXIMA`:

| Script | Contenuto |
|--------|-----------|
| 1 — Engine | `getPhase`, `phaseNames`, `monthLabel`, `getTarget`, `defaultParams`, `simulate` |
| 2 — Controls | Sidebar con Slider/Toggle/Panel per tutti i parametri |
| 3 — Glossary | Definizioni dei termini in italiano |
| 4 — Dashboard | KPI cards + grafici Recharts (LineChart, BarChart, AreaChart) |
| 5 — Table | Tabella 36 mesi con export CSV/JSON |
| 6 — App | State management (React useState) + layout + `boot()` |

CDN: React 18, ReactDOM, Babel standalone, Recharts. Zero dipendenze locali.

---

## Fasi del progetto (timeline 36 mesi)

| Fase | Mesi simulazione | Label | Nome |
|------|------------------|-------|------|
| 1 | 1-3 | M-12 → M-10 | Fondazione e burocrazia |
| 2 | 4-6 | M-9 → M-7 | Qualificazioni e compliance |
| 3 | 7-9 | M-6 → M-4 | Pre-lancio (Infrastruttura) |
| 4 | 10-12 | M-3 → M-1 | Alpha test |
| 5 | 13-15 | M0 → M+2 | Beta pubblica |
| 6 | 16-18 | M+3 → M+5 | Early Access |
| 7 | 19-36 | M+6 → M+23 | Lancio Pubblico |

Mesi 1-12 = pre-release (zero revenue da paid/organic, solo borrowed audience in fase 4 Alpha). M0 = mese 13 = lancio.

---

## Parametri del modello SCF

### Acquisizione clienti

```javascript
// Funnel: click → calcolatore → booking → checkup → cliente
showRate: 0.75,           // % booking che si presentano al checkup
checkupToClient: 0.30,    // % checkup che diventano clienti

// Paid channels
google: {
  cpc: 1.80, clickToCalc: 0.60, calcToBooking: 0.08,
  budgetByPhase: { 1:0, 2:0, 3:0, 4:500, 5:1500, 6:2500, 7:3500 }
},
meta: {
  cpc: 0.90, clickToCalc: 0.35, calcToBooking: 0.05,
  budgetByPhase: { 1:0, 2:0, 3:0, 4:300, 5:800, 6:1200, 7:1800 }
},
linkedin: {
  cpc: 6.00, clickToCalc: 0.50, calcToBooking: 0.06,
  budgetByPhase: { 1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:600 },
  startMonth: 22
},

// Organic channels
seo:    { baseVisits: 30, growthRate: 0.22, visitToCalc: 0.18, calcToBooking: 0.06 },
social: { baseVisits: 60, growthRate: 0.14, visitToCalc: 0.10, calcToBooking: 0.04 },

// Other channels
referral: { ratePerClient: 0.06, bookingRate: 0.80, startMonth: 15 },
borrowed: { bookingsByPhase: { 1:0, 2:0, 3:0, 4:2, 5:5, 6:8, 7:12 } },

// Waiting list (injection at M0)
waitingList: { count: 10, conversionRate: 0.80 },
```

### Revenue e clienti

```javascript
arpu: 490,                // €490/anno per cliente (parcella fissa ponderata)
churnMonthly: 0.01,       // 1%/mese = 12% annuo
deferredFees: false,      // toggle: se true, revenue parte 12 mesi dopo acquisizione

// AUM tracking (solo per benchmark, NON per revenue)
aum: {
  avgPerClient: 80000,    // AUM medio per cliente
  sp500Annual: 0.10       // rendimento annuo S&P 500 per benchmark
},
```

### Costi di costituzione (una tantum, distribuiti nei mesi 1-7)

```javascript
constitution: {
  notaio: 2500,                // M1: atto costitutivo SRL
  cciaa: 200,                  // M1: diritti camerali
  impostoRegistro: 200,        // M1: imposta registro
  bollo: 156,                  // M1: marca da bollo
  commercialistaIniziale: 1500,// M1: apertura P.IVA, INPS, INAIL
  pecFirmaDigitale: 75,        // M2: PEC + firma digitale
  iscrizioneOCF: 700,          // M2: iscrizione albo SCF sezione III
  esamiCertificazioni: 1500,   // M3: esame OCF per 2 fondatori
  avvocato: 2500,              // M4: statuto SCF-compliant, contrattualistica MiFID II
  sitoWeb: 4000,               // M4-M5: split 50/50
  assicurazioneRC: 3000,       // M5: RC professionale obbligatoria per SCF
  branding: 3000,              // M6: identità visiva
  setupCRM: 500                // M7: CRM + configurazione
}
// Distribuzione:
// M1: notaio + cciaa + impostoRegistro + bollo + commercialistaIniziale = €4.556
// M2: pecFirmaDigitale + iscrizioneOCF = €775
// M3: esamiCertificazioni = €1.500
// M4: avvocato + sitoWeb/2 = €4.500
// M5: assicurazioneRC + sitoWeb/2 = €5.000
// M6: branding = €3.000
// M7: setupCRM = €500
// Totale: €19.831
```

### Costi operativi (mensili, da mese 1)

```javascript
operating: {
  commercialista: 400,         // contabilità, bilancio, dichiarazioni
  coworking: 350,              // ufficio condiviso
  software: 200,               // CRM, portfolio analysis, compliance tools
  assicurazioneMensile: 250,   // RC ammortizzata mensilmente
  pecTelCloud: 100,            // PEC, telefonia VoIP, Google Workspace
  quotaOCF: 80                 // quota annuale OCF ammortizzata
}
// Totale: €1.380/mese
```

### Personale

```javascript
personnel: {
  founderComp: 1000,     // €1.000/mese per fondatore
  numFounders: 2,
  inpsRate: 0.26         // INPS gestione separata 26%
}
// Formula costo: founderComp × numFounders × (1 + inpsRate × 2/3)
// = 1000 × 2 × (1 + 0.1733) = €2.347/mese
// Il 2/3 dell'INPS è a carico della SRL

// Hiring dinamico (trigger automatici)
hiring: {
  consultantHoursPerWeek: 20,
  consultantCost: 2500,        // costo mensile per consulente
  maxConsultants: 4,
  firstConsultantMonth: 19,    // non prima di M+6
  backOfficeTrigger: 80,       // assumi back-office a 80 clienti
  backOfficeCost: 900,
  backOfficeMinMonth: 21,
  contentTrigger: 40,          // assumi content creator a 40 clienti
  contentCost: 800,
  contentMinMonth: 20,
  juniorTrigger: 150,          // assumi consulente junior a 150 clienti
  juniorCost: 1200,
  juniorHoursPerWeek: 25,
  juniorMinMonth: 25
}
```

### Capacità e hiring automatico

```javascript
founderHoursPerWeek: 25,   // ore/settimana disponibili per fondatore
hoursOnboarding: 5,        // ore per onboarding nuovo cliente

// Logica:
// maxNewPerMonth = totalHours / hoursOnboarding
// appointmentUtilization = newClientsRaw / maxNewPerMonth
// Se utilization > 85% → assumi consulente (min 3 mesi tra assunzioni)
// Smart budget: se slots saturi → riduci automaticamente spesa ads
budgetCapAdjust: true,
budgetCapThreshold: 0.85,
```

### Mutuo (opzionale, toggle)

```javascript
mortgage: {
  enabled: false,              // default off, attivabile da UI
  principal: 180000,
  rate: 0.054,                 // 5.40% annuo
  preAmortMonths: 18,          // primi 18 mesi solo interessi
  amortMonths: 60              // poi ammortamento 60 mesi
}
// Billing semestrale (ogni 6 mesi):
// Pre-amort: principal × rate / 2 = €4.860/semestre
// Post-amort: piano francese semestrale
```

### Tassazione italiana (opzionale, toggle)

```javascript
taxation: {
  enabled: false,              // default off, attivabile da UI
  iresRate: 0.24,              // IRES 24% su utile
  irapRate: 0.039              // IRAP 3.9% su valore produzione netta
}
// Logica: provision mensile basata su trailing 12-month profit
// IRES: trailingProfit × 0.24 / 12
// IRAP: max(0, mrr - opCost) × 0.039
// Attivo solo da mese 13 (post-lancio)
```

### Scenari di rischio

```javascript
var RISK = {
  base:       { clientMult: 1.0, costMult: 1.0, churnMult: 1.0 },
  recessione: { clientMult: 0.7, costMult: 1.15, churnMult: 1.5 },
  crisi:      { clientMult: 0.5, costMult: 1.15, churnMult: 2.0 }
};
```

---

## Logica simulate() — come deve funzionare

Per ogni mese `m` da 1 a 36:

1. **Capacity:** calcola ore disponibili (fondatori + consulenti + junior), dividi per `hoursOnboarding` → `maxNewPerMonth`
2. **Hiring triggers:** se `appointmentUtilization > 85%` e mese >= soglia → assumi. Se `totalClients >= trigger` → assumi back-office/content/junior
3. **Demand (full budget):** per ogni paid channel: `budget / cpc × clickToCalc × calcToBooking` = bookings. Per organic: `baseVisits × (1+growthRate)^(m-1) × visitToCalc × calcToBooking`. Per referral: `totalClients × ratePerClient × bookingRate`. Per borrowed: fisso per fase
4. **Pre-release filter:** mesi 1-12 = zero bookings da paid/organic, solo borrowed in fase 4
5. **Smart budget:** se `utilization > threshold` → riduci budget paid con fattore proporzionale
6. **Apply budget factor:** ricalcola bookings paid con budget ridotto
7. **New clients:** `totalBookings × showRate × checkupToClient × riskMultiplier`, cappato a `maxNewPerMonth`
8. **Waiting list:** a M0 (mese 13) inietta `waitingList.count × conversionRate` clienti extra
9. **Churn:** `totalClients × churnMonthly × riskChurnMult`
10. **Costs:** constitution (mesi 1-7) + operating + personnel + marketing + mortgage (semestrale) + taxation (provision mensile)
11. **Revenue:** `payingClients × arpu / 12` (payingClients = totalClients, o differito di 12 mesi se toggle attivo)
12. **AUM tracking:** solo per benchmark visivo, non per revenue. `managedAUM` cresce con nuovi clienti (×avgPerClient) e compounding S&P 500, decresce con churn
13. **Cash:** `cash -= (totalCosts - mrr)`, traccia minimo

**Output summary:** `breakEvenOperational`, `breakEvenCumulative`, `cacBlended`, `cacByChannel`, `cashMinimum`, `cashMinimumMonth`, `hiringPlan`

---

## Feature avanzate da includere (dal modello AC-SIM)

Queste feature esistono nel modello AC-SIM e vanno portate nel nuovo modello SCF:

1. **Stagionalità:** array `seasonality[0..12]` (indice 0 unused, 1=gen..12=dic). Moltiplica solo bookings paid+organic, NON borrowed. Richiede `launchCalendarMonth` per mappare mese simulazione → mese calendario.
2. **SIM delay / launch delay:** `simDelayMonths` — sposta il lancio in avanti. `launchM = 13 + simDelayMonths`.
3. **Hybrid actuals mode:** `actuals: { currentMonth, totalClients, cashBalance }` — se `currentMonth > 0`, al mese indicato sovrascrive totalClients e cash con dati reali (calibrazione).
4. **Cohort-based AUM** (per tracking benchmark, non revenue): ogni mese crea una coorte di nuovi clienti con il loro AUM medio. L'AUM compone con rendimento di mercato. Il churn rimuove pro-rata.
5. **AUM distribution:** `dist: { s_pct, s_avg, m_pct, m_avg, l_pct, l_avg }` — mix di clienti piccoli/medi/grandi.

---

## UI — Cosa mostrare

### Dashboard (KPI cards)
- Clienti totali a fine simulazione
- MRR e ARR finali
- Break-even operativo (mese)
- Break-even cumulativo (mese)
- Cash minimo raggiunto (€ e mese)
- CAC blended e per canale
- AUM totale gestito (benchmark)
- Staff count finale

### Grafici (Recharts)
- **Clienti nel tempo** (area chart, 36 mesi)
- **Revenue vs Costi** (line chart, MRR vs costi mensili)
- **Cash remaining** (area chart con reference line a €0 e €30K warning)
- **AUM** (line chart con benchmark S&P 500)
- **Breakdown costi** (stacked bar: constitution, operating, personnel, marketing, mortgage, tax)

### Tabella 36 mesi
- Colonne: Mese, Fase, Nuovi clienti, Churn, Totale clienti, Revenue, Costi, Net burn, Cash, AUM
- Export CSV e JSON
- Highlighting: rosso se cash < €30K, verde se net burn positivo

### Pannello controlli (sidebar)
- Slider per tutti i parametri principali
- Toggle per mutuo, tassazione, deferred fees
- Dropdown per scenario rischio (base/recessione/crisi)
- Sezione "Capitale iniziale" con slider
- Sezione "Actuals" per calibrazione

---

## Valori attesi (scenario base, per sanity check)

Questi numeri vengono dai documenti strategici esistenti:

| Metrica | Valore atteso |
|---------|---------------|
| Clienti a M+6 (mese 19) | ~80-110 |
| Clienti a M+12 (mese 25) | ~250-300 |
| Clienti a M+23 (mese 36) | ~500-700 |
| Break-even operativo | ~M+11 (mese 24) |
| Break-even cumulativo | ~M+17/18 (mese 30-31) |
| Cash minimo | ~€30K-35K (intorno a M+11) |
| ARR a M+18 | ~€250K |
| Investimento totale fino a break-even | ~€148K |

---

## Cosa NON fare

- NON usare il modello Agente Collegato SIM per il revenue (quello usa `AUM × feeRate × proximaSplit`). Qui il revenue è `clienti × ARPU / 12`
- NON creare file multipli — tutto in un unico HTML self-contained
- NON aggiungere un build step (webpack, vite, etc.) — deve funzionare aprendo il file nel browser
- NON modificare i documenti strategici esistenti
- NON inventare parametri — usa quelli documentati sopra

---

## Istruzioni operative

1. **Leggi** il file `proxima-funnel-ac.html` dal branch `claude/sim-launch-cost-analysis-bQpgG` per capire l'architettura (fetch il branch se serve: `git fetch origin claude/sim-launch-cost-analysis-bQpgG`)
2. **Costruisci** `proxima-funnel-scf.html` nella directory `.agents/launch-strategy-180k/funnel-model/`
3. **Testa** che i numeri siano coerenti con i valori attesi nella tabella sopra
4. **Commit e push** su branch `claude/project-launch-strategy-8cuWN`

---

## Contesto regolatorio (per il glossario)

- **SCF** = Società di Consulenza Finanziaria (art. 18-bis TUF)
- **OCF** = Organismo di vigilanza Consulenti Finanziari (gestisce l'Albo)
- **CONSOB** = Commissione Nazionale per le Società e la Borsa (vigilanza)
- **MiFID II** = Direttiva europea 2014/65/UE (trasparenza costi, adeguatezza)
- **IRES** = Imposta sul Reddito delle Società (24%)
- **IRAP** = Imposta Regionale sulle Attività Produttive (3.9%)
- **INPS** = Istituto Nazionale Previdenza Sociale (contributi 26%, 2/3 a carico SRL)
- **RC professionale** = Responsabilità Civile, polizza obbligatoria per SCF
- **Fee-only** = modello senza commissioni su prodotti, solo parcella al cliente
- **AUM** = Assets Under Management (patrimonio consigliato, non gestito direttamente)
- **ARPU** = Average Revenue Per User (€490/anno)
- **CAC** = Customer Acquisition Cost
- **Churn** = tasso di abbandono clienti (1%/mese = 12%/anno)
