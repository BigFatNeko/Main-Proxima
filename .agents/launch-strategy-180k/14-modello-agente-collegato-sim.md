# 14 — Modello Agente Collegato SIM: Struttura, Ricerca, Negoziazione

*Proxima — percorso operativo per operare il modello gestione-AUM senza autorizzazione SIM propria*
*Ultimo aggiornamento: 2026-04-23*

---

## 1. Cos'è un Agente Collegato di SIM

Ai sensi dell'art. 31-ter TUF e dell'art. 29 MiFID II, un **agente collegato** è un soggetto (persona fisica o giuridica) che agisce sotto la piena e incondizionata responsabilità della SIM mandante.

### Cosa può fare l'agente collegato

| Attività | Consentita |
|---|---|
| Promozione dei servizi della SIM | Sì |
| Raccolta mandati e ordini dai clienti | Sì |
| Collocamento di strumenti finanziari | Sì |
| Consulenza sugli strumenti della SIM | Sì |
| Gestione del rapporto cliente | Sì |
| Detenzione di denaro/titoli dei clienti | **No** — restano in custodia presso la SIM |
| Esecuzione diretta di ordini | **No** — esegue la SIM |

### Vincolo di esclusività

L'agente collegato può operare per **una sola SIM** alla volta (art. 29 MiFID II). Questo è negoziabile solo nella misura in cui le attività svolte per diversi mandanti non si sovrappongono — in pratica, per Proxima è un vincolo reale.

### Responsabilità

La SIM mandante risponde solidalmente per tutti gli atti dell'agente collegato verso i clienti. Questo è il motivo per cui le SIM selezionano con cura i propri agenti e richiedono formazione e supervisione continuativa.

---

## 2. Struttura Operativa del Modello

```
CLIENTE
    │
    │  rapporto commerciale e fiduciario
    ▼
PROXIMA SRL (agente collegato)
    │  raccoglie il mandato
    │  costruisce relazione
    │  fornisce advisory/reportistica
    │  gestisce comunicazione
    │
    │  accordo di agenzia (revenue share)
    ▼
SIM PARTNER (autorizzata CONSOB)
    │  esegue ordini
    │  custodisce asset
    │  gestisce compliance MiFID II
    │  produce rendicontazione ufficiale
    │  risponde ai regolatori
```

Dal punto di vista del cliente: **delega a Proxima, che poi delega l'esecuzione alla SIM**. L'esperienza è quella di avere un gestore dedicato (Proxima), con tutta l'infrastruttura regolamentare garantita dalla SIM.

---

## 3. Modello di Revenue

### Fee typology

| Voce | Chi incassa | Split tipico |
|---|---|---|
| % AUM annuale (es. 1%) | SIM, poi redistribuisce | 40-60% a Proxima |
| Performance fee | SIM, poi redistribuisce | 30-50% a Proxima (se prevista) |
| Onboarding fee | Possibile | Negoziabile |

### Matematica del modello

*AUM fee media sul mercato italiano: 0,8-1,2% annuo*
*Split Proxima: ipotesi conservativa 45%*

| Scenario | N. clienti | AUM medio | AUM totale | Fee totale (1%) | Proxima (45%) |
|---|---|---|---|---|---|
| Early | 100 | €25.000 | €2,5M | €25.000 | **€11.250/anno** |
| Crescita | 300 | €35.000 | €10,5M | €105.000 | **€47.250/anno** |
| Maturo | 700 | €45.000 | €31,5M | €315.000 | **€141.750/anno** |
| Target M+36 | 1.000 | €50.000 | €50M | €500.000 | **€225.000/anno** |

> A €50M AUM con split al 45% e fee all'1%: €225K/anno. Con split al 55%: €275K/anno. Questo è il modello che giustifica l'investimento iniziale.

### Nota sulla performance fee su clienti retail

La performance fee per clienti retail è **fortemente regolamentata** da MiFID II e dalle Linee Guida ESMA 2020:
- Deve essere simmetrica (se il gestore guadagna sull'upside, paga una penale sull'underperformance)
- Deve avere high watermark
- Deve essere calcolata su un benchmark appropriato
- Molte SIM non la applicano sulla clientela retail per semplicità

In prima fase, modellare il revenue **solo su % AUM** — è pulito, allineato agli incentivi, e non crea frizioni con i clienti.

---

## 4. Come Trovare la SIM Partner

### Profilo ideale

Non tutte le SIM accettano agenti collegati. Cercare SIM con queste caratteristiche:

| Caratteristica | Perché importante |
|---|---|
| Già hanno agenti collegati attivi | Hanno processi rodati, non stai chiedendo loro di inventare qualcosa |
| Dimensione media (non grandi gruppi bancari) | Più flessibili, più aperti alla negoziazione, meno burocrazia interna |
| Modello orientato all'advisory/gestione ETF | Allineamento sulla filosofia di investimento |
| Tecnologia digitale (portale cliente, API) | Integrazione con il tuo sistema |
| Track record regolamentare pulito | Controllare su albo CONSOB, nessuna sanzione recente |

### Canali di ricerca

**1. Albo CONSOB delle SIM**
- URL: consob.it → Albi e registri → Imprese di investimento
- Filtrare per SIM autorizzate in Italia, escludere le grandi reti bancarie
- Lista completa: circa 100-130 SIM attive

**2. Assoreti (associazione reti consulenti)**
- Rappresenta SIM e reti di consulenza. Utile per capire chi è attivo nel segmento retail

**3. OCF — Albo agenti collegati**
- Il registro degli agenti collegati esistenti (per vedere quali SIM già usano questo modello)

**4. LinkedIn + ricerca diretta**
- Cercare "responsabile sviluppo rete" o "business development" nelle SIM target
- Un'email diretta con una proposta concreta funziona meglio di un approccio formale

**5. Network personale del socio CFA**
- Chi sta facendo il percorso CFA/CEFA è in contatto con professionisti del settore — warm introduction vale 10x cold outreach

### SIM tipicamente aperte a questo modello

Senza endorsement specifici, le tipologie di SIM da cercare:
- SIM boutique indipendenti (5-30 dipendenti) focalizzate su gestione patrimoniale retail
- SIM nate da spin-off di reti bancarie che vogliono crescere fuori dal canale tradizionale
- SIM che già offrono "white label" o accordi di distribuzione a terzi

---

## 5. Come Valutare una SIM (Due Diligence)

Prima di firmare qualsiasi accordo, verificare:

### Checklist regolamentare

- [ ] Iscrizione all'albo CONSOB come SIM autorizzata (verificare su consob.it)
- [ ] Nessuna sanzione CONSOB o Banca d'Italia negli ultimi 5 anni
- [ ] Bilanci depositati e in utile (o perdite contenute e spiegabili)
- [ ] Assenza di procedure di crisi o amministrazione straordinaria
- [ ] Polizza RC professionale valida con massimali adeguati

### Checklist operativa

- [ ] Hanno già agenti collegati attivi? Quanti? Da quanto tempo?
- [ ] Posso parlare con altri agenti collegati come reference?
- [ ] Che tecnologia offrono al cliente finale (portale, app, reportistica)?
- [ ] Come gestiscono l'onboarding MiFID II del cliente (chi fa il questionario adeguatezza)?
- [ ] Chi produce la rendicontazione periodica al cliente?
- [ ] Tempi di esecuzione ordini (importante per ETF)?
- [ ] Broker/custodian che usano (Directa? IB? Banca depositaria propria?)

### Red flag

| Segnale | Problema |
|---|---|
| Spingono prodotti proprietari o fondi con commissioni elevate | Conflitto di interessi, non allineati con il tuo modello fee-only |
| Non ti danno portabilità dei dati clienti in caso di uscita | Ti rende prigioniero dell'accordo |
| Nessun agente collegato attivo (sei il primo) | Processi non rodati, rischio operativo alto |
| Non vogliono condividere i loro rendiconti regolamentari | Opacità su solidità finanziaria |
| Offrono split AUM >70% subito senza conoscerti | Troppo bello — capire perché |

---

## 6. Come Strutturare l'Accordo

### Punti chiave da negoziare

**A. Revenue split**
- Partenza realistica: 40-45% a Proxima
- Obiettivo dopo 6-12 mesi di track record: 50-55%
- Inserire clausola di revisione al raggiungimento di soglie AUM (es. +5% a ogni €10M AUM)

**B. Proprietà della relazione cliente**
- Questo è il punto più critico dell'intero accordo
- Negoziare esplicitamente: **se la partnership termina, i clienti possono seguire Proxima presso altra SIM**
- Senza questa clausola, rischi di costruire un business che appartiene alla SIM
- Le SIM tendono a resistere su questo — è un deal-breaker se non cedono

**C. Brand e comunicazione**
- Proxima deve poter operare con il proprio brand (non co-branding forzato con la SIM)
- La SIM deve essere menzionata come "partner esecutore" nei documenti obbligatori MiFID II
- Libertà totale su marketing, contenuti, social media

**D. Esclusività e perimetro**
- L'esclusività è obbligatoria per legge (una SIM per agente)
- Negoziare il perimetro: se la SIM non offre certi servizi (es. consulenza previdenziale), Proxima può operare autonomamente in quell'area come SCF separata

**E. Onboarding e processo**
- Chi gestisce il questionario MiFID II (suitability): idealmente Proxima fa l'intervista, la SIM valida
- Chi produce il contratto con il cliente: la SIM, ma Proxima può avere un modello white-label
- Tempi di attivazione di un nuovo cliente: target <48 ore dall'onboarding

**F. Technology integration**
- API o feed dati dalla SIM verso il CRM/portale Proxima
- Accesso real-time ai portafogli clienti per Proxima
- Report automatici scaricabili per il cliente dall'interfaccia Proxima (non solo dal portale SIM)

**G. Exit e durata**
- Durata iniziale: 12-24 mesi, rinnovabile
- Preavviso per uscita: 3-6 mesi (tempo per trovare nuova SIM)
- Portabilità clienti: esplicita e garantita (rif. punto B)

---

## 7. Il Pitch alla SIM

Quando Proxima si presenta a una SIM potenziale partner, porta sul tavolo:

| Asset | Valore per la SIM |
|---|---|
| ~€1M AUM informale già gestito | Pipeline immediata di clienti pronti |
| Lista d'attesa esistente | Dimostrazione della domanda reale |
| Piano marketing €180K | Capacità di acquisizione clienti a scala |
| Modello digitale first | Acquisisce un segmento che la SIM tradizionale non raggiunge |
| Brand fee-only trasparente | Differenziazione positiva per la SIM stessa |
| Socio CFA in progress | Competenza tecnica in costruzione |

**Il messaggio chiave**: *"Portiamo clienti che non avete e che non riuscireste ad acquisire con i vostri canali. Voi fornite l'infrastruttura regolamentare. Cresciamo insieme."*

---

## 8. Timeline di Attivazione

| Settimana | Attività |
|---|---|
| 1-2 | Identificazione 10-15 SIM candidate dall'albo CONSOB |
| 3-4 | Ricerca su ciascuna: bilanci, sanzioni, agenti collegati attivi, tecnologia |
| 5-6 | Shortlist 3-5 SIM. Primo contatto (email + LinkedIn) con proposta sintetica |
| 7-10 | Meeting con le SIM interessate. Presentazione piano business |
| 11-14 | Due diligence approfondita sulle 1-2 più interessanti |
| 15-18 | Negoziazione accordo con avvocato specializzato in diritto finanziario |
| 19-20 | Firma e notifica OCF (la SIM registra Proxima come agente collegato) |
| 21-24 | Onboarding operativo: test processo, integrazione tech, formazione |
| **M+6** | **Primi clienti ufficialmente onboardati sulla SIM partner** |

---

## 9. Costi di Setup di Questo Modello

| Voce | Costo stimato |
|---|---|
| Avvocato per negoziazione e revisione accordo | €2.000-4.000 |
| Eventuali costi di onboarding richiesti dalla SIM | €0-2.000 (dipende) |
| Integrazione tecnologica (API, portale) | €1.000-3.000 |
| Formazione obbligatoria richiesta dalla SIM | €200-500 |
| **Totale setup** | **€3.200-9.500** |

Costo corrente (post-attivazione): nessuno oltre ai costi operativi già previsti. La SIM deduce la propria quota dalla fee complessiva prima di girare la parte Proxima.

---

## 10. Rischi Specifici di Questo Modello

| Rischio | Probabilità | Mitigazione |
|---|---|---|
| La SIM fallisce o perde autorizzazione | Bassa | Due diligence finanziaria preventiva; portabilità clienti nel contratto |
| La SIM cambia condizioni dopo M+12 | Media | Clausole contrattuali di stabilità dello split per durata minima |
| I clienti si sentono "venduti" alla SIM | Media | Brand Proxima forte, comunicazione chiara del modello |
| La SIM non porta avanti le ottimizzazioni che vuoi | Media | Verificare in anticipo flessibilità sulla costruzione dei portafogli |
| Non trovi SIM disponibile | Bassa-Media | Ampliare ricerca, considerare SIM estere con passaporto EU (es. Malta, Lituania) |

---

*Prossimo passo operativo: costruire la lista delle 10-15 SIM candidate dall'albo CONSOB e avviare la ricerca di background su ciascuna.*
