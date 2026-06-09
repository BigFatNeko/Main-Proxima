# HANDOFF — Build €30K Funnel Model for Proxima (Agente Collegato SIM)

## Obiettivo

Costruire un simulatore funnel 36 mesi per lo **scenario €30K** (capitale iniziale €30.000, zero mutuo, organic-first) come file HTML self-contained, basato sull'architettura del modello €180K già funzionante.

## Repository & Branch

- **Repo:** `bigfatneko/main-marketing`
- **Branch di sviluppo:** `claude/project-launch-strategy-8cuWN`
- **Directory output:** `.agents/launch-strategy-180k/funnel-model/`
- **File di riferimento (€180K, modello AC-SIM):** branch `claude/sim-launch-cost-analysis-bQpgG` → file `proxima-funnel-ac.html` (1711 righe, React/Recharts/Babel, self-contained)

## Cosa esiste già

**Branch €180K (`claude/project-launch-strategy-8cuWN`):**

- 16 strategic markdown docs in `.agents/launch-strategy-180k/`
- Funnel model app (6 JS modules + `proxima-funnel.html` 81KB bundle) — modello **SCF fee-only** (vecchio)
- `proxima-funnel-ac.html` sul branch `claude/sim-launch-cost-analysis-bQpgG` — modello **Agente Collegato SIM** (nuovo, più avanzato)

**Branch €30K (`claude/init-proxima-project-Myyk4`):**

- 7 strategy docs + `70-azioni-immediate.md` (tailored for €30K organic-first)
- **Nessun funnel model** — va costruito

## Architettura del modello AC-SIM (da replicare/adattare)

Cinque `<script type="text/babel">` in sequenza, tutto su `window.PROXIMA`:

| Script | Contenuto |
|--------|-----------|
| 1 | `getPhase`, `phaseNames`, `monthLabel`, `getTarget`, `defaultParams`, `simulate` |
| 2 | `Controls` — sidebar con tutti i Slider/Panel |
| 3 | `Glossary` — termini in italiano |
| 4 | `Dashboard` — KPI cards + grafici Recharts |
| 5 | `ProjectionTable` — tabella 36 mesi + export CSV/JSON |
| 6 | `App` — state management + layout + `boot()` |

## Modello di business: Agente Collegato SIM

Proxima SRL opera come **agente collegato di SIM** (art. 31-ter TUF, art. 29 MiFID II). Proxima porta i clienti, la SIM partner esegue/custodisce.

**Revenue formula:** `MRR = payingAUM × feeRate × proximaSplit / 12`

**Split ratchet:**

```javascript
if (totalAUM >= 30_000_000) proximaSplit = Math.min(proximaSplit + 0.10, 0.70);
else if (totalAUM >= 10_000_000) proximaSplit = Math.min(proximaSplit + 0.05, 0.70);
```

## defaultParams del modello AC-SIM (€180K)

```javascript
{
  showRate: 0.75, checkupToClient: 0.30,
  assetTransferLagMonths: 2,
  simDelayMonths: 0,
  launchCalendarMonth: 9,
  seasonality: [0, 1.2, 1.0, 1.1, 1.05, 0.95, 0.85, 0.50, 0.40, 1.30, 1.10, 1.0, 0.60],
  actuals: { currentMonth: 0, totalClients: 0, cashBalance: 0 },
  google: { cpc: 1.80, clickToCalc: 0.60, calcToBooking: 0.08,
    budgetByPhase: { 1:0, 2:0, 3:0, 4:500, 5:2000, 6:3200, 7:4500 } },
  meta: { cpc: 0.90, clickToCalc: 0.35, calcToBooking: 0.05,
    budgetByPhase: { 1:0, 2:0, 3:0, 4:300, 5:1100, 6:1600, 7:2300 } },
  linkedin: { cpc: 6.00, clickToCalc: 0.50, calcToBooking: 0.06,
    budgetByPhase: { 1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:600 }, startMonth: 22 },
  seo: { baseVisits: 30, growthRate: 0.22, visitToCalc: 0.18, calcToBooking: 0.06 },
  social: { baseVisits: 60, growthRate: 0.14, visitToCalc: 0.10, calcToBooking: 0.04 },
  referral: { ratePerClient: 0.06, bookingRate: 0.80, startMonth: 15 },
  borrowed: { bookingsByPhase: { 1:0, 2:0, 3:0, 4:2, 5:5, 6:8, 7:12 } },
  founderHoursPerWeek: 25, hoursOnboarding: 3.5,
  arpu: 374, churnMonthly: 0.006,
  constitution: {
    notaio: 2500, cciaa: 200, impostoRegistro: 200, bollo: 156,
    iscrizioneOCF: 0, commercialistaIniziale: 1500, avvocato: 2500,
    assicurazioneRC: 0, sitoWeb: 4000, branding: 3000, setupCRM: 500,
    esamiCertificazioni: 0, simIntegration: 1500, pecFirmaDigitale: 75
  },
  operating: {
    commercialista: 400, coworking: 350, software: 350,
    assicurazioneMensile: 0, pecTelCloud: 100, quotaOCF: 0
  },
  personnel: { founderComp: 1000, numFounders: 2, inpsRate: 0.26 },
  hiring: {
    consultantHoursPerWeek: 20, consultantCost: 2500, maxConsultants: 4,
    firstConsultantMonth: 19, backOfficeTrigger: 80, backOfficeCost: 900,
    backOfficeMinMonth: 21, contentTrigger: 40, contentCost: 800,
    contentMinMonth: 20, juniorTrigger: 150, juniorCost: 1200,
    juniorHoursPerWeek: 25, juniorMinMonth: 25
  },
  budgetCapAdjust: true, budgetCapThreshold: 0.85,
  riskScenario: 'base',
  startingCapital: 180000,
  waitingList: { count: 10, conversionRate: 0.80 },
  aum: {
    avgPerClient: 50000, sp500Annual: 0.07, sp500Benchmark: 0.10,
    feeRate: 0.012, proximaSplit: 0.50, annualContributions: 4000,
    qualifyRate: 0.65, marketShock: 0, annualWithdrawalRate: 0.04,
    dist: { s_pct: 0.35, s_avg: 20000, m_pct: 0.40, m_avg: 50000, l_pct: 0.25, l_avg: 100000 }
  },
  deferredFees: false,
  mortgage: { enabled: false, principal: 180000, rate: 0.054, preAmortMonths: 18, amortMonths: 60 },
  taxation: { enabled: false, iresRate: 0.24, irapRate: 0.039 }
}
```

## Logica simulate() — sezioni critiche

**Timeline:** `launchM = 13 + simDelayMonths`. Mesi 1-12 = pre-lancio. `monthLabel(m - simDelayMonths)` → `M0` quando `m === launchM`.

**Stagionalità:** `calMonth` = mese di calendario corrispondente a `m`, applicato solo a paid+organic bookings, **non** a borrowed audiences.

**Cohort-based AUM** (annuity formula per cohort):

```javascript
var cAge = m - cohorts[ck].birthMonth;
var aumPer = effectiveAvgAUM * mktF * Math.pow(1 + r12, cAge)
  + (cAge > 0 && Math.abs(netPMT) > 0.01
      ? netPMT * (Math.pow(1 + r12, cAge) - 1) / r12 : 0);
```

**AUM distribution → effectiveAvgAUM:**

```javascript
var effectiveAvgAUM = (sumPct > 0.01)
  ? (dd.s_pct*dd.s_avg + dd.m_pct*dd.m_avg + dd.l_pct*dd.l_avg) / sumPct
  : p.aum.avgPerClient;
var netPMT = (p.aum.annualContributions - effectiveAvgAUM * annualWithdrawalRate) / 12;
```

**INPS employer share (2/3 del 26%):**

```javascript
var persCost = p.personnel.founderComp * p.personnel.numFounders * (1 + p.personnel.inpsRate * 2/3);
```

**Hybrid actuals mode** (calibrazione su dati reali):

```javascript
if (act.currentMonth > 0 && m === act.currentMonth) {
  var scale = act.totalClients / totalClients;
  for (var cx = 0; cx < cohorts.length; cx++) cohorts[cx].count *= scale;
  totalClients = act.totalClients;
  if (act.cashBalance > 0) cash = act.cashBalance;
}
```

**Scenari di rischio:**

```javascript
var RISK = {
  base:       { clientMult: 1.0, costMult: 1.0, churnMult: 1.0 },
  recessione: { clientMult: 0.7, costMult: 1.15, churnMult: 1.5 },
  crisi:      { clientMult: 0.5, costMult: 1.15, churnMult: 2.0 }
};
```

## Differenze €30K vs €180K — COSA CAMBIA

| Parametro | €180K | €30K |
|-----------|-------|------|
| `startingCapital` | 180000 | 30000 |
| `mortgage.enabled` | toggle (default off) | **sempre false** — rimuovi pannello mutuo |
| `personnel.founderComp` | 1000 | **0** (zero compenso anno 1) |
| `google.budgetByPhase` | 500→4500 rampa aggressiva | **0→0→0→0→200→500→1200** (micro-budget, solo da fase 5) |
| `meta.budgetByPhase` | 300→2300 | **0→0→0→0→150→400→800** |
| `linkedin` | attivo da M22 | **disabilitato** (budget 0 su tutte le fasi) |
| `seo.baseVisits` | 30 | **50** (più investimento organico) |
| `seo.growthRate` | 0.22 | **0.28** (crescita più aggressiva, è la leva principale) |
| `social.baseVisits` | 60 | **100** (social organico = canale primario) |
| `social.growthRate` | 0.14 | **0.20** |
| `referral.startMonth` | 15 | **14** (referral prima, serve ogni cliente) |
| `borrowed.bookingsByPhase` | 2→12 | **3→7→10→15** (borrowed audience = leva chiave senza budget) |
| `hiring` | consulenti da M19 | **firstConsultantMonth: 25** (rimandato), backOffice/content/junior tutti più tardi e con trigger più alti |
| `constitution.sitoWeb` | 4000 | **1500** (sito economico, Framer/template) |
| `constitution.branding` | 3000 | **500** (DIY con Canva) |
| `constitution.avvocato` | 2500 | **1000** (solo essenziale) |
| `waitingList.count` | 10 | **5** (rete più piccola) |
| `hoursOnboarding` | 3.5 | **3.5** (invariato, è il tempo reale per cliente) |

## Strategia organic-first (dal doc `70-azioni-immediate.md` branch €30K)

- **Social organico** come canale #1 (LinkedIn personal branding, Instagram educativo)
- **SEO content** come canale #2 (blog articoli finanza personale)
- **Borrowed audiences** come canale #3 (guest post, podcast, eventi locali, co-marketing)
- **Paid ads** solo da fase 5 con micro-budget (€200-500/mese), scala solo se ROI positivo
- **Zero compenso fondatori** anno 1 — tutto il cash va in growth
- **Nessun mutuo** — €30K puri di equity

## Fasi e struttura (invariate)

| Fase | Mesi | Nome |
|------|------|------|
| 1 | 1-3 | Fondazione e burocrazia |
| 2 | 4-6 | Qualificazioni e compliance |
| 3 | 7-9 | Pre-lancio (Infrastruttura) |
| 4 | 10-12 | Alpha test |
| 5 | 13-15 | Beta pubblica |
| 6 | 16-18 | Early Access |
| 7 | 19+ | Lancio Pubblico |

## Output atteso

1. File `proxima-funnel-30k.html` — self-contained, stessa architettura di `proxima-funnel-ac.html`
2. Titolo/header che dica chiaramente "Scenario €30K — Organic First"
3. Pannello mutuo rimosso (o nascosto)
4. defaultParams calibrati per €30K come da tabella sopra
5. Stessa qualità di Dashboard, tabella 36 mesi, export CSV/JSON, glossario
6. Commit e push su branch `claude/project-launch-strategy-8cuWN`

## TL;DR

Prendi `proxima-funnel-ac.html` (1711 righe, modello AC-SIM €180K), clona la struttura, sostituisci i defaultParams con i valori €30K dalla tabella, rimuovi il pannello mutuo, e salva come `proxima-funnel-30k.html`. Tutto il resto dell'engine (cohort AUM, split ratchet, stagionalità, risk scenarios, hybrid actuals) resta identico.
