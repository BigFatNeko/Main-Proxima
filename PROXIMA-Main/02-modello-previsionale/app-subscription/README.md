# Modello Scalabile App — Abbonamenti (Fase 2)

> Motore di ricavo dell'**app** (strategia di massa, Fase 2), distinto dal funnel SCF
> fee-only della Fase 1 (`../funnel-model/`). Modella abbonamenti multi-durata **Free / Pro /
> Max** + la **fee di costituzione 3%** una tantum. Strumento interattivo:
> **`app-model.html`** (single-file, stesso motore di questo documento).
>
> ⚠️ I numeri "scenario base" qui sotto sono **output calcolati** dal motore con le assunzioni
> indicate (verificati con simulazione). Cambiando le leve nello strumento cambiano di conseguenza.

---

## 1. Pricing (input dai fondatori)

### Free — €0
Insight di mercato + visualizzazione performance. Top-of-funnel: bacino da cui convertire a pagamento.

### Pro
| Cadenza | Prezzo | €/mese effettivo | Sconto vs mensile |
|---|---|---|---|
| Mensile | €10/mese | €10,00 | — |
| 3 mesi | €25 | €8,33 | −17% |
| 6 mesi | €40 | €6,67 | −33% |
| 1 anno | €80 | €6,67 | −33% |

**Incluso nel Pro 6 mesi:** 1 mese di Max + **1 chiamata gratuita** ai consulenti.

### Max
| Cadenza | Prezzo | €/mese effettivo | Sconto vs mensile |
|---|---|---|---|
| Mensile | €48/mese | €48,00 | — |
| 3 mesi | €130 | €43,33 | −10% |
| 6 mesi | €250 | €41,67 | −13% |
| 1 anno | €500 | €41,67 | −13% |

**Incluso nel Max:** 1 chiamata immediata (onboarding) + 1 **chiamata trimestrale**.

### Fee di costituzione — 3% una tantum
Sia Pro sia Max: se al **primo anno** c'è da **costituire un portafoglio nuovo**, si applica il
**3% sulla cifra del portafoglio**, **fatturato subito**. È la parcella fee-only di impostazione
(pagata dal cliente, nessuna retrocessione) incorporata nell'app.

---

## 2. Logica di ricavo (motore)

Simulazione **mensile** a coorti. Per ogni mese `m`:

```
nuovi_free      = signup(m)                          # curva di crescita acquisizione
nuovi_pro       = free * conv_pro_mese                # conversione dal bacino free
nuovi_max       = free * conv_max_mese
free            = (free + nuovi_free - nuovi_pro - nuovi_max) * (1 - churn_free)
pro             = pro * (1 - churn_pro) + nuovi_pro
max             = max * (1 - churn_max) + nuovi_max

upgrade         = pro * up_rate_mese                  # upgrade Pro->Max (v2)
pro            -= upgrade ; max += upgrade

MRR             = pro * ARPU_pro + max * ARPU_max     # ricavo ricorrente abbonamenti
one_off(3%)     = (nuovi_pro + nuovi_max) * tasso_costituzione * portafoglio_medio * 0,03
```

### Strato costi → margine (v2)

```
chiamate        = max/3 + (nuovi_max + upgrade) + nuovi_pro·quota_pro_6m
chiamate_umane  = chiamate * (1 - ai_deflection)     # <-- leva AI
ore_call        = chiamate_umane * durata_min / 60
FTE consulenti  = ceil(ore_call / ore_produttive_FTE)
costo_consulenti= ore_call * costo_ora
costo_AI        = chiamate*ai_deflection*costo_AI_interazione + free*costo_AI_self_service
costo_totale    = costo_consulenti + costo_AI + ricavo*commissioni_pagamento
                  + nuovi_paganti*CAC + costo_fisso_piattaforma
margine         = ricavo - costo_totale
```

Dove `ARPU` (€/mese per utente attivo) = media pesata dei €/mese-effettivi sul **mix di cadenza**
scelto (mensile/3m/6m/annuale). Il ricavo è la somma di **due flussi**: abbonamenti (ricorrente) +
fee 3% (una tantum, concentrata nell'anno 1 di ogni coorte).

**Carico chiamate** (vincolo di capacità consulenti), stima mensile:
`chiamate ≈ max/3 (trimestrali) + nuovi_max (immediata) + nuovi_pro·quota_pro_6mesi (call inclusa)`.

---

## 3. Scenario base — assunzioni

| Leva | Valore base |
|---|---|
| Signup Free iniziali | 150/mese |
| Crescita signup | +6%/mese (cap 2.500/mese) |
| Conversione Free→Pro | 1,5%/mese del bacino free |
| Conversione Free→Max | 0,4%/mese del bacino free |
| Churn Free / Pro / Max | 6% / 4% / 3% al mese |
| Mix cadenza Pro (mensile/3m/6m/anno) | 40% / 20% / 15% / 25% |
| Mix cadenza Max (mensile/3m/6m/anno) | 30% / 20% / 20% / 30% |
| Tasso costituzione portafoglio (anno 1) | 25% dei nuovi paganti |
| Portafoglio medio nuovo | €35.000 |

## 4. Scenario base — output calcolati

**Unit economics (dai prezzi + mix + churn):**
| Metrica | Pro | Max |
|---|---|---|
| ARPU | **€8,33/mese → €100/anno** | **€43,90/mese → €527/anno** |
| Vita media cliente (1/churn) | 25 mesi | 33 mesi |
| **LTV abbonamento** | **€208** | **€1.463** |

→ **Un cliente Max vale ~7× un cliente Pro.** La leva di valore è l'upgrade a Max.

**Proiezione (scenario base):**
| Mese | Free | Pro | Max | MRR | ARR | One-off 3% (mese) |
|---|---|---|---|---|---|---|
| M6 | 822 | 30 | 8 | €596 | €7.151 | €3.425 |
| M12 | 1.671 | 120 | 33 | €2.443 | €29.312 | €7.592 |
| M18 | 2.682 | 264 | 74 | €5.448 | €65.371 | €12.450 |
| M24 | 3.995 | 469 | 133 | €9.760 | **€117.125** | €18.694 |
| M36 | 8.278 | 1.143 | 331 | €24.069 | **€288.824** | €38.909 |

**Ricavi cumulati:**
| Flusso | Anno 1 | Anno 2 |
|---|---|---|
| Abbonamenti | €10.889 | €71.668 |
| One-off 3% | **€45.308** | **€157.755** |
| **Totale (24 mesi)** | colspan | **€285.620** |

---

## 5. Cinque letture strategiche

1. **Il 3% di costituzione domina i ricavi iniziali** (€45K vs €11K di abbonamenti nell'anno 1). Nei
   primi mesi l'app è di fatto un **motore di acquisizione per la consulenza fee-only**, non ancora un
   business da abbonamenti. Il ricorrente cresce e supera il one-off solo più avanti, con la base
   installata. Implicazione: la sostenibilità dell'app dipende dal **flusso di nuovi portafogli**, quindi
   dal tasso di costituzione e dal portafoglio medio, più che dai canoni.

2. **Max vale ~7× Pro** (LTV €1.463 vs €208). Ogni euro speso per spingere l'**upgrade a Max** rende
   molto più dell'acquisizione di nuovi Pro. Il bundle **"1 mese di Max dentro il Pro 6 mesi"** è un
   funnel di upgrade intelligente: fa provare il valore premium (la chiamata) a chi è già Pro.

3. **Posizionamento prezzo coerente col mercato.** Pro annuale €80 (€6,67/mese) è **sotto** l'entry di
   qualunque SCF (IoInvesto €500/anno, Plannix Smart €990); Max €500/anno è **metà** di Plannix Premium
   (€1.490) pur includendo chiamate periodiche. La coppia Pro/Max copre bene la finestra <€100K
   individuata in `../../01-strategia/competitor/43-pricing-competitor.md`.

4. **Attenzione al 3% su patrimoni grandi (nota fee-only + pricing).** 3% su €35K = €1.050 (proporzionato);
   su €100K = €3.000 (alto). Valutare un **cap** o **scaglioni decrescenti**. È fee-only a norma (pagato dal
   cliente, zero retrocessioni), ma va comunicato come **"parcella una tantum di pianificazione"**, non come
   "% sul capitale" — per non evocare la commissione d'ingresso bancaria da cui Proxima vuole distinguersi.

5. **Le chiamate incluse sono un costo di capacità (tempo consulente).** Al M36 (~331 Max attivi) il carico
   è ~1.300+ chiamate trimestrali/anno + le immediate: va dimensionato l'**organico consulenti** o la
   durata/formato delle call. Lo strumento espone il "carico chiamate" per pianificare le assunzioni.

---

## 6. Strato costi & margine — assunzioni e output

**Assunzioni costi (scenario base):** upgrade Pro→Max 1%/mese del bacino Pro · durata chiamata 30′ ·
costo consulente €35/ora · 100 ore produttive/FTE·mese · costo fisso piattaforma €4.000/mese ·
CAC €50/nuovo pagante · commissioni pagamento 2,5% · costo AI ~€0,30/interazione.

**Margine (con upgrade attivo):**
| Mese | ARR | Ricavo/mese | Costo/mese | Margine | % | Chiamate umane | FTE |
|---|---|---|---|---|---|---|---|
| M12 | €31.394 | €10.208 | €6.192 | €4.016 | 39% | 23 | 1 |
| M24 | €131.150 | €29.623 | €9.955 | €19.668 | 66% | 83 | 1 |
| M36 | €332.434 | €66.611 | €17.048 | €49.564 | 74% | 203 | 2 |

**Break-even di margine: ~M8.** L'upgrade Pro→Max porta i Max a M36 da ~331 a **~432** (più valore).

## 7. Eliminare il "problema chiamate" con l'AI

Il vincolo che limita davvero la scala non è il prezzo ma la **capacità umana** delle chiamate incluse.
L'AI lo scioglie — con un caveat regolatorio onesto.

**Come:**
1. **Da sincrono a AI-first asincrono.** La chiamata trimestrale diventa un **copilot in-app** che monitora
   il portafoglio in continuo, genera il check-up periodico (report/video personalizzato), risponde in chat
   24/7 e propone ribilanciamenti. Nessuno slot da prenotare.
2. **AI per tier:**
   - **Free** → AI pura (insight di mercato, education): zero umano.
   - **Pro** → self-service AI completo (analisi, simulazioni, Q&A). La call del Pro 6m diventa opzionale/escalation.
   - **Max** → AI continua + **1 sola validazione umana annuale** (invece di 4 call) + escalation on-demand;
     onboarding guidato dall'AI con revisione umana asincrona.
3. **Effetto nel modello** (leva `AI deflection`): a ~85% il carico umano al M36 crolla da **~203 a ~30
   chiamate/mese** e da **2 FTE a 1**; il costo consulenti passa da ~€3.560 a ~€530/mese, sostituito da ~€470
   di AI. Soprattutto **rompe il legame lineare clienti↔organico**: a 10× utenti il modello a mano si spezza,
   quello AI-first no.

**Il caveat che non va nascosto:** in Italia la **raccomandazione personalizzata** su strumenti finanziari è
attività riservata e il **consulente iscritto OCF resta responsabile** della raccomandazione (MiFID II).
Quindi l'AI può fare il ~90% (profilazione, analisi, bozza di raccomandazione, conversazione, alert), ma un
umano deve **validare/firmare** la raccomandazione. **L'AI elimina il *tempo* umano ripetitivo, non la
*responsabilità* umana.** Per azzerare del tutto l'umano servirebbe riposizionarsi come *software di supporto
alle decisioni* (non "consulenza personalizzata" riservata): è una scelta di **modello**, non solo tecnica.

## 8. Limiti del modello (v1)

- Conversione modellata come tasso mensile sul bacino free (no lag esplicito di attivazione).
- Churn per tier costante (i prepagati 6m/annuali sono in realtà "lockati" → churn effettivo più basso:
  il modello è **prudente** sui ricorrenti lunghi).
- Upgrade Pro→Max non modellato esplicitamente (incluso implicitamente nelle conversioni): da aggiungere in v2.
- One-off 3% applicato ai **nuovi** paganti dell'anno; non ai rinnovi (corretto: la costituzione è una tantum).
- Nessun costo dedotto (è un modello di **ricavo**): margini e organico vanno incrociati col budget operativo
  (`../../01-strategia/piano-di-lancio/60-budget-operativo-24m.md`).
