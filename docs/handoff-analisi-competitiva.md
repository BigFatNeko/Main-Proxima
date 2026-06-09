# HANDOFF — Sessione Analisi Competitiva Proxima

**Data:** 9 giugno 2026
**Branch di lavoro:** `claude/proxima-competitor-analysis-bE7oR`
**Repository:** `bigfatneko/main-marketing`
**Working directory:** `/home/user/Main-Marketing`

---

## Cos'è Proxima

Proxima è una startup finanziaria italiana in fase pre-lancio. I fondatori (2 co-founder, 50/50) stanno costruendo un servizio di advisory/gestione finanziaria indipendente per risparmiatori con €10K–€100K di patrimonio. Budget totale: €180K. Sede: Emilia-Romagna, poi espansione nazionale.

---

## Cosa è stato fatto in questa sessione

Questa è stata una sessione di **ricerca competitiva pura** — nessun codice scritto, nessun commit. Tutto il lavoro è stato di analisi attraverso agenti web e codebase.

### 1. Analisi codebase
Il codebase contiene documentazione marketing/strategica estesa: piano di lancio 18 mesi, modello finanziario, piano media, comparatori, FAQ. Proxima era originariamente pianificata come **SCF (Società di Consulenza Finanziaria)** fee-only con pricing €250–€800/anno flat.

### 2. Ricerca competitiva (completata)
Ricerca approfondita su tutto il mercato italiano fee-only/SCF + internazionale. Vedi sezione "Findings" sotto.

### 3. Pivot strategico emerso a fine sessione
**Punto critico:** i fondatori hanno rivelato di voler fare **gestione patrimoniale discrezionale** (loro gestiscono il portafoglio via API, i clienti aprono conto es. Interactive Brokers) — NON semplice consulenza SCF. Questo è un cambio di categoria regolamentare fondamentale. La sessione si è chiusa su questo tema, con analisi parziale e raccomandazione di approfondire.

---

## Findings chiave — Mercato SCF italiano

### Il competitor più simile: Plannix SCF

- Fondata giugno 2023, OCF apr 2024, Milano
- Fondatore: **Luca Lixi** (CEO, ex Santander/Fideuram) — il moat è il suo personal brand e la community di 35.000 Facebook costruita in 6 anni sotto WikiLixi/Lixi Invest
- Modello: flat fee €990–€4.900/anno, consulente dedicato, metodologia **ERASER** (6 step: Esplora, Raccogli, Analizza, Sviluppa, Esegui, Revisiona)
- Metriche feb 2025: €820K ARR, +425% YoY, 1.000+ clienti, €518M asset analizzati
- **Media cliente reale: €500K+ patrimonio totale, €180K investito** — non serve il segmento €10K–€100K nonostante le dichiarazioni
- Weakness: traffico web -51% inizio 2026; no discussioni su forum indipendenti (solo community controllata); no esecuzione ordini; prezzo 4x Proxima
- Revenue 2024 (bilancio): €392K, perdita €45K (growth phase)

### Altri competitor principali

| Player | Tipo | Min AUM | Fee | Margine netto |
|---|---|---|---|---|
| Consultique SCF | SCF tradizionale | ~€500K | 0,5–0,9% AUM | **22,5%** |
| IoInvesto SCF | Rete 90+ advisor | Nessuno dichiarato | ~1% AUM | 4,4% |
| SoldiExpert SCF | SCF storica | €100–200K | 0,15–1,59% | **-10,7% (perdita)** |
| Moneyfarm | Robo-advisor (SIM) | €2.500 | 0,75% | Negativo (scala) |
| Finax | Robo-advisor (SK passport) | €10 | 0,15–1% | ~3,2% |
| Euclidea/Fürstenberg | Robo-advisor (SIM, ora Banca Ifis) | €5.000 | 0,60–1,20% | N/D |

### Il white space reale (pre-pivot)
Nessuna SCF italiana offre advisory umana ongoing per clienti €10K–€100K a flat fee sotto €500/anno in modo economicamente sostenibile. Il gap è reale e strutturale.

### Problemi strutturali SCF
- IVA 22% su fee (banche non la applicano — svantaggio percettivo)
- OCF registration: 4–6 mesi, costo reale €15–35K pre-ricavi, bottleneck sulla Relazione di Attività (70–130 pp)
- Assicurazione RC deve essere attiva **prima** della domanda OCF
- Software advisory deve essere dichiarato nella domanda (no "TBD")
- Esecuzione ordini vietata per SCF — il cliente deve andare in banca/broker da solo (questo è esattamente il motivo del pivot dei fondatori)

---

## Il Pivot — Gestione Patrimoniale Discrezionale

### Cosa vogliono i fondatori
- Clienti aprono conto presso broker (es. Interactive Brokers)
- Proxima gestisce il portafoglio **in modo discrezionale** via API
- 3–5 portafogli modello per livello di rischio
- Ordini eseguiti centralmente su tutti i conti simultaneamente
- Il cliente controlla solo l'app, finanzia, chiama se necessario

### Cosa cambia regolatorialmente
Questo è **gestione di portafogli** (MiFID II, Allegato I, Sez. A, punto 4) — richiede licenza SIM o equivalente EU, non OCF.

| | SCF | SIM / Gestore discrezionale |
|---|---|---|
| Regolatori | OCF | **Consob + Banca d'Italia** |
| Capitale minimo | ~€10K | **€75K–€750K+** (IFR Class 3) |
| Tempistica autorizzazione | 4–6 mesi | **12–24 mesi** |
| Compliance annuale | ~€30K | €150–400K |

### Opzioni regolatorie analizzate

**Opzione 1 — SIM italiana full**
Percorso ortodosso. €300K+ in costi preparatori, 18–24 mesi. Sensato solo con funding istituzionale (€2M+).

**Opzione 2 — Licenza EU leggera + passaporto MiFID II in Italia** *(più interessante)*
Modello Finax (licenza slovacca). Candidati: Lituania, Malta, Cipro.
- Costo stimato: €100–250K
- Tempi: 8–14 mesi
- Passaporto in Italia = notifica formale, nessuna seconda autorizzazione

**Opzione 3 — Partnership con SIM italiana esistente** *(percorso veloce, consigliato per validazione)*
- Proxima fa brand, acquisizione clienti, definisce portafogli modello
- SIM partner detiene la licenza, esegue gli ordini
- Time-to-market: 3–6 mesi
- Svantaggio: cede 30–50% del margine; dipendenza strategica

### Interactive Brokers come custodian
IB Advisor Account permette:
- Gestione multi-account sotto master account
- Model Portfolios + Allocation Orders su tutti i conti simultaneamente
- Rebalancing automatico, fee billing integrato
- **Richiede che il gestore sia licenziato presso un regolatore riconosciuto** — non aggira la regulation

### Competitors nel nuovo posizionamento
Non più Plannix/SCF. Ora: Moneyfarm, Finax, Euclidea, Revolut Wealth, Scalable Capital.

Il differenziatore che rimane valido: **human advisor + gestione discrezionale + flat fee + target esplicito €10K–€100K** — nessun player lo fa oggi in Italia.

---

## Differenziatori e strategie di margine emerse (da sviluppare)

- **Behavioral coaching** come positioning principale (Vanguard: +150–200bps/anno vs. self-directed)
- **B2B — commercialisti e notai** come canale di distribuzione a CAC zero
- **Nicchie trigger-based**: partite IVA, eredi da successione, divorziati, neo-pensionati
- **Sessioni di gruppo** (20–30 clienti simultanei) come leva di margine principale
- **Flat fee su gestione discrezionale** — inedito in Italia, tutti i concorrenti usano % AUM
- **Bank Cost Calculator** come asset virale e distribuibile via API embed
- **Modello productized**: deliverable fissi per tier, ore consulente calcolate internamente
- **White-label per commercialisti**: Proxima gestisce, il commercialista eroga ai propri clienti

---

## Cosa fare nella prossima sessione

### Priorità 1 — Approfondire la via regolamentare (ricerca non completata)
L'agente su questo topic ha esaurito il limite di utilizzo. Da ricercare:
- Quali SIM italiane oggi offrono partnership white-label per fintech
- Requisiti K-factor IFR 2019/2020 per capital requirement reale (il minimo nominale €75K può crescere significativamente)
- Lituania vs. Malta: confronto tempi, costi, requisiti per licenza investment management 2025/2026
- Fornitori tech white-label startup-friendly: WealthKernel (UK), Bambu, Objectway Italia — pricing e modelli per startup

### Priorità 2 — Salvare e strutturare le ricerche in documenti nel codebase
Tutti i findings di questa sessione sono in conversazione ma non sono stati committati nel repo. Valutare se creare documenti di analisi nel codebase.

### Priorità 3 — Revisione del business plan nel codebase
Il codebase contiene un piano finanziario e un piano di lancio costruiti attorno al modello SCF. Con il pivot a gestione discrezionale, quasi tutto va rivisto: struttura legale, capex, timeline, comparatori con competitor.

---

## Note operative

- Il modello discusso nell'SCF (Bank Cost Calculator, gamification, community, flat fee, portafogli modello, target €10–100K) rimane **valido come product vision** — quello che cambia è solo il wrapper regolatorio
- Il codebase è in italiano, il team lavora in italiano
- **Nessun commit è stato fatto in questa sessione** — tutto il lavoro è stato di ricerca/analisi
- Il branch `claude/proxima-competitor-analysis-bE7oR` esiste ma non ha modifiche committed da questa sessione
