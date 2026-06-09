# HANDOFF — Proxima Funnel Model (Agente Collegato SIM)

## Contesto progetto

**Proxima SRL** opera come **agente collegato di SIM** (art. 31-ter TUF, art. 29 MiFID II).
Proxima porta i clienti, la SIM partner esegue e custodia.
Ricavo: `payingAUM × feeRate × proximaSplit / 12` (MRR mensile).
Target: risparmiatori retail con <€100K in asset.

---

## File da modificare

```
/home/user/Main-Marketing/.agents/launch-strategy-180k/funnel-model/proxima-funnel-ac.html
```

**Branch git attivo:** `claude/sim-launch-cost-analysis-bQpgG`
**Commit HEAD:** `333895e`

> Non toccare `proxima-funnel.html` — è il modello SCF fee-only separato (branch `modello/scf-fee-only`).

---

## Architettura del file (1711 righe)

Single-file HTML con React 18 + Recharts + Babel — no build step, si apre direttamente nel browser.

Cinque `<script type="text/babel">` in sequenza su `window.PROXIMA`:

| # | Contenuto |
|---|-----------|
| 1 | `getPhase`, `monthLabel`, `defaultParams`, `simulate` |
| 2 | `Controls` — sidebar con tutti gli Slider/Panel |
| 3 | `Glossary` — termini in italiano |
| 4 | `Dashboard` — KPI cards + grafici Recharts |
| 5 | `ProjectionTable` — tabella 36 mesi + export CSV/JSON |
| 6 | `App` — state, localStorage, layout, `boot()` |

---

## Logica critica del motore (simulate)

### Timeline

`launchM = 13 + simDelayMonths`. Il mese 1–12 è pre-lancio.
`monthLabel` riceve `m - simDelayMonths` come argomento — **non cambiare la funzione stessa**.

### Cohort AUM (formula rendita per cohort)

```javascript
var cAge = m - cohorts[ck].birthMonth;
var aumPer = effectiveAvgAUM * mktF * Math.pow(1 + r12, cAge)
  + (cAge > 0 && Math.abs(netPMT) > 0.01
      ? netPMT * (Math.pow(1 + r12, cAge) - 1) / r12 : 0);
```

### AUM distribution → effectiveAvgAUM

```javascript
var effectiveAvgAUM = (sumPct > 0.01)
  ? (dd.s_pct*dd.s_avg + dd.m_pct*dd.m_avg + dd.l_pct*dd.l_avg) / sumPct
  : p.aum.avgPerClient;
var netPMT = (p.aum.annualContributions - effectiveAvgAUM * annualWithdrawalRate) / 12;
```

### Split ratchet

```javascript
if (totalAUM >= 30000000) proximaSplit = Math.min(proximaSplit + 0.10, 0.70);
else if (totalAUM >= 10000000) proximaSplit = Math.min(proximaSplit + 0.05, 0.70);
var mrr = payingAUM * p.aum.feeRate * proximaSplit / 12;
```

### INPS employer share

```javascript
var persCost = p.personnel.founderComp * p.personnel.numFounders * (1 + p.personnel.inpsRate * 2/3);
// 2/3 del 26% = quota a carico del datore di lavoro
```

### Stagionalità

`effSeasonMult` applicato a paid + organic bookings. **Mai** a `borBook`.

### Hybrid actuals (calibrazione su dati reali)

```javascript
if (act.currentMonth > 0 && m === act.currentMonth) {
  var scale = act.totalClients / totalClients;
  for (var cx = 0; cx < cohorts.length; cx++) cohorts[cx].count *= scale;
  totalClients = act.totalClients;
  if (act.cashBalance > 0) cash = act.cashBalance;
}
```

---

## defaultParams completo

```javascript
{
  showRate: 0.75, checkupToClient: 0.30,
  assetTransferLagMonths: 2, simDelayMonths: 0, launchCalendarMonth: 9,
  seasonality: [0, 1.2, 1.0, 1.1, 1.05, 0.95, 0.85, 0.50, 0.40, 1.30, 1.10, 1.0, 0.60],
  actuals: { currentMonth: 0, totalClients: 0, cashBalance: 0 },
  google:   { cpc: 1.80, clickToCalc: 0.60, calcToBooking: 0.08,
              budgetByPhase: { 1:0, 2:0, 3:0, 4:500, 5:2000, 6:3200, 7:4500 } },
  meta:     { cpc: 0.90, clickToCalc: 0.35, calcToBooking: 0.05,
              budgetByPhase: { 1:0, 2:0, 3:0, 4:300, 5:1100, 6:1600, 7:2300 } },
  linkedin: { cpc: 6.00, clickToCalc: 0.50, calcToBooking: 0.06,
              budgetByPhase: { 1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:600 }, startMonth: 22 },
  seo:      { baseVisits: 30, growthRate: 0.22, visitToCalc: 0.18, calcToBooking: 0.06 },
  social:   { baseVisits: 60, growthRate: 0.14, visitToCalc: 0.10, calcToBooking: 0.04 },
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
  riskScenario: 'base', startingCapital: 180000,
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

---

## Scenari di rischio

```javascript
var RISK = {
  base:       { clientMult: 1.0, costMult: 1.0, churnMult: 1.0 },
  recessione: { clientMult: 0.7, costMult: 1.15, churnMult: 1.5 },
  crisi:      { clientMult: 0.5, costMult: 1.15, churnMult: 2.0 }
};
```

---

## Fasi

| Fase | Mesi (m) | Nome |
|------|----------|------|
| 1 | 1–3 | Fondazione e burocrazia |
| 2 | 4–6 | Qualificazioni e compliance |
| 3 | 7–9 | Pre-lancio (Infrastruttura) |
| 4 | 10–12 | Alpha test |
| 5 | 13–15 | Beta pubblica |
| 6 | 16–18 | Early Access |
| 7 | 19+ | Lancio Pubblico |

Lancio pubblico = M0 = `m === launchM` = `m === 13` con `simDelayMonths: 0`.

---

## Differenze chiave vs modello SCF (proxima-funnel.html)

| | SCF fee-only | Agente collegato SIM |
|---|---|---|
| Ricavo | `clienti × arpu / 12` | `payingAUM × feeRate × proximaSplit / 12` |
| ARPU | €490 fisso | Calcolato da AUM |
| Churn | 1%/mese | 0.6%/mese (mandati più stabili) |
| OCF | Richiesta | Non richiesta |
| Costi costituzione | `iscrizioneOCF` + `esamiCertificazioni` | `simIntegration` €1500, OCF = 0 |

---

## Convenzioni di sviluppo

- Nessun commento salvo dove il WHY non è ovvio.
- Non creare nuovi file — tutto va nel file HTML esistente.
- Non toccare `proxima-funnel.html`.
- Commit format: `feat:` / `fix:` / `refactor:` + descrizione breve.
- Push: `git push -u origin claude/sim-launch-cost-analysis-bQpgG`

---

## Stato attuale — 9 feature implementate

1. Cohort-based AUM tracking (formula rendita per cohort)
2. INPS employer share fix (2/3 del 26%)
3. Market shock scalar (`mktF`)
4. Split ratchet (€10M / €30M, cap 70%)
5. Hybrid actuals mode (calibrazione su dati reali)
6. Monthly seasonality index (12 moltiplicatori)
7. SIM regulatory delay (`simDelayMonths`)
8. AUM client distribution buckets (small / medium / large)
9. Partial withdrawal rate (`annualWithdrawalRate`)

Nessuna feature in sospeso. Attendi istruzioni dall'utente su cosa sviluppare.
