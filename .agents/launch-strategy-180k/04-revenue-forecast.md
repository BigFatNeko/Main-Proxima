# 04 — Revenue Forecast (18 Mesi)

*Modello basato su pricing a parcella fissa annuale, 3 scenari*

---

## Struttura Pricing Proxima

| Fascia Patrimonio | Parcella Annua | % stimata clienti |
|-------------------|----------------|-------------------|
| Fino a €20.000 | €250 | 30% |
| €20.001 – €50.000 | €500 | 35% |
| €50.001 – €100.000 | €800 | 25% |
| Oltre €100.000 | €1.200 | 10% |

**ARPU (Average Revenue Per User) ponderato:** €490/anno

Calcolo: (0.30 × €250) + (0.35 × €500) + (0.25 × €800) + (0.10 × €1.200) = €75 + €175 + €200 + €120 = **€570/anno**

*Nota: l'ARPU effettivo sarà più basso nei primi mesi perché i primi clienti tendono ad avere patrimoni più piccoli. Usiamo €490 come stima conservativa che include lo sconto early-adopter del 20% sui primi 50 clienti.*

---

## Assunzioni del Modello

| Parametro | Valore | Note |
|-----------|--------|------|
| ARPU medio | €490/anno | Ponderato per mix patrimoni + sconti iniziali |
| Churn annuale | 12% | ~1% mensile. Conservativo per servizio finanziario |
| Churn mensile | 1% | Dei clienti attivi al mese precedente |
| Conversion rate check-up → cliente | 35% | Basato su consulenza gratuita di alta qualità |
| Referral rate | 15% | % nuovi clienti da referral (dal mese 4) |
| CAC medio target | €90 | Blended: organico + paid + referral |
| Mesi per break-even unitario | 2.2 | €90 CAC / (€490 ÷ 12 mesi) = 2.2 mesi |

---

## Scenario Base — Proiezione Mensile

### Mese -6 → 0 (Pre-lancio + Alpha)

| Mese | Nuovi Clienti | Churn | Clienti Totali | Revenue Mensile | Revenue Cumulato |
|------|---------------|-------|----------------|-----------------|------------------|
| -6 | 0 | 0 | 0 | €0 | €0 |
| -5 | 0 | 0 | 0 | €0 | €0 |
| -4 | 0 | 0 | 0 | €0 | €0 |
| -3 | 3 | 0 | 3 | €123 | €123 |
| -2 | 4 | 0 | 7 | €286 | €409 |
| -1 | 5 | 0 | 12 | €490 | €899 |

*Nota: revenue mensile = clienti totali × (€490 ÷ 12)*

### Mese 0 → 6 (Beta + Early Access)

| Mese | Nuovi Clienti | Churn | Clienti Totali | Revenue Mensile | Revenue Cumulato |
|------|---------------|-------|----------------|-----------------|------------------|
| 0 | 8 | 0 | 20 | €817 | €1.716 |
| 1 | 10 | 0 | 30 | €1.225 | €2.941 |
| 2 | 12 | 0 | 42 | €1.715 | €4.656 |
| 3 | 12 | 1 | 53 | €2.165 | €6.821 |
| 4 | 15 | 1 | 67 | €2.736 | €9.557 |
| 5 | 18 | 1 | 84 | €3.430 | €12.987 |

### Mese 6 → 12 (Lancio Pubblico + Scaling)

| Mese | Nuovi Clienti | Churn | Clienti Totali | Revenue Mensile | Revenue Cumulato |
|------|---------------|-------|----------------|-----------------|------------------|
| 6 | 25 | 1 | 108 | €4.410 | €17.397 |
| 7 | 28 | 1 | 135 | €5.513 | €22.910 |
| 8 | 30 | 2 | 163 | €6.656 | €29.566 |
| 9 | 30 | 2 | 191 | €7.799 | €37.365 |
| 10 | 28 | 2 | 217 | €8.861 | €46.226 |
| 11 | 30 | 2 | 245 | €10.004 | €56.230 |

### Mese 12 → 18 (Scaling Nazionale)

| Mese | Nuovi Clienti | Churn | Clienti Totali | Revenue Mensile | Revenue Cumulato |
|------|---------------|-------|----------------|-----------------|------------------|
| 12 | 35 | 3 | 277 | €11.310 | €67.540 |
| 13 | 38 | 3 | 312 | €12.740 | €80.280 |
| 14 | 40 | 3 | 349 | €14.252 | €94.532 |
| 15 | 42 | 4 | 387 | €15.804 | €110.336 |
| 16 | 42 | 4 | 425 | €17.354 | €127.690 |
| 17 | 45 | 4 | 466 | €19.028 | €146.718 |
| 18 | 48 | 5 | 509 | €20.785 | €167.503 |

---

## Riepilogo Scenario Base

| Milestone | Clienti | ARR | Revenue Cumulato | Spesa Cumulata |
|-----------|---------|-----|------------------|----------------|
| Mese 0 (fine Alpha) | 20 | €9.800 | €1.716 | €50.000 |
| Mese 6 (lancio pubblico) | 108 | €52.920 | €17.397 | €123.000 |
| Mese 12 | 277 | €135.730 | €67.540 | €172.000 |
| **Mese 18** | **509** | **€249.410** | **€167.503** | **€180.000** |

**Break-even cumulato: mese 17-18** — Il revenue cumulato pareggia l'investimento totale.

**ARR a regime (mese 18): ~€250.000/anno** con 509 clienti attivi.

---

## Scenario Ottimistico (+30%)

Assunzioni: CAC più basso (€70), conversion rate 42%, churn 8% annuo.

| Milestone | Clienti | ARR | Revenue Cumulato |
|-----------|---------|-----|------------------|
| Mese 6 | 140 | €68.600 | €22.500 |
| Mese 12 | 360 | €176.400 | €88.000 |
| **Mese 18** | **660** | **€323.400** | **€218.000** |

Break-even cumulato: **mese 14-15**.

---

## Scenario Conservativo (-30%)

Assunzioni: CAC più alto (€130), conversion rate 25%, churn 18% annuo.

| Milestone | Clienti | ARR | Revenue Cumulato |
|-----------|---------|-----|------------------|
| Mese 6 | 65 | €31.850 | €10.400 |
| Mese 12 | 170 | €83.300 | €41.500 |
| **Mese 18** | **320** | **€156.800** | **€105.000** |

Break-even cumulato: **mese 24-26** (richiede continuare dopo i 18 mesi).

---

## Unit Economics

### Lifetime Value (LTV)

```
LTV = ARPU / Churn Rate Annuale
LTV = €490 / 0.12 = €4.083

Con churn al 8% (ottimistico): LTV = €6.125
Con churn al 18% (conservativo): LTV = €2.722
```

### LTV:CAC Ratio

| Scenario | LTV | CAC | LTV:CAC | Giudizio |
|----------|-----|-----|---------|----------|
| Ottimistico | €6.125 | €70 | 87:1 | Eccellente — scala aggressivamente |
| **Base** | **€4.083** | **€90** | **45:1** | **Ottimo — margine sano** |
| Conservativo | €2.722 | €130 | 21:1 | Buono — margine sufficiente |

*Nota: ratio LTV:CAC così alti sono tipici dei servizi finanziari fee-only dove il churn è naturalmente basso e il costo marginale per cliente è minimo.*

### Payback Period

```
Payback = CAC / (ARPU mensile)
Payback = €90 / €40.8 = 2.2 mesi (scenario base)
```

Il costo di acquisizione si ripaga in poco più di 2 mesi. Questo significa che ogni euro investito in acquisizione genera profitto dal terzo mese in poi.

---

## Composizione Revenue per Canale (Stima Mese 12)

| Canale Acquisizione | % Clienti | Clienti | CAC | Costo Totale |
|---------------------|-----------|---------|-----|-------------|
| Organico (SEO + social) | 30% | 83 | €30 | €2.490 |
| Paid ads (Google + Meta) | 35% | 97 | €120 | €11.640 |
| Referral | 20% | 55 | €50 | €2.750 |
| Borrowed (PR + podcast + eventi) | 10% | 28 | €80 | €2.240 |
| Direct/brand | 5% | 14 | €0 | €0 |
| **Totale** | **100%** | **277** | **€69 blended** | **€19.120** |

**Obiettivo mese 18:** Referral e organico sopra il 55% dei nuovi clienti per ridurre dipendenza da paid.

---

## Proiezione Anno 2 (Mese 19-30) — Indicativa

Se il modello funziona e si reinveste il revenue:

| Parametro | Target Anno 2 |
|-----------|---------------|
| Clienti a fine anno 2 | 900-1.100 |
| ARR | €450.000-550.000 |
| Revenue annuo | €380.000-480.000 |
| Team | 2-3 consulenti + 1 marketing FT |
| Espansione | Tutta Italia + possibile DACH |

**Il servizio diventa profittabile operativamente dal mese 12-14** (costi operativi coperti dal revenue, escluso l'investimento iniziale).

---

## Rischi sul Revenue

| Rischio | Impatto su Revenue | Probabilità | Mitigazione |
|---------|-------------------|-------------|-------------|
| ARPU più basso (clienti piccoli) | -15-20% revenue | Media | Incentivare upgrade con gamification |
| Churn più alto del previsto | -10-25% a lungo termine | Bassa | NPS tracking, exit interview, save offers |
| CAC paid insostenibile | Rallentamento crescita | Media | Spostare budget su organico e referral |
| Stagionalità (estate, natale) | Calo acquisizioni 2-3 mesi | Alta | Anticipare con pipeline di lead |
| Regolamentazione OCF | Blocco totale temporaneo | Bassa | Avere piano B (consulenza generica) |
