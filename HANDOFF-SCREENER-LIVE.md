# Handoff — dal Briefing Pipeline allo Screener Live per consulenza

**Scopo di questo documento**: dare a una nuova sessione tutto il contesto necessario per costruire un **secondo programma**, diverso da quello esistente ma che ne riusa il motore di valutazione.

- **Programma esistente** (già in produzione): genera un briefing finanziario quotidiano automatico.
- **Programma da costruire**: uno screener massivo che, **su richiesta e in tempo reale davanti a un cliente**, restituisce pool di titoli che soddisfano criteri predefiniti, organizzati in pacchetti.

**Documenti di riferimento nel repository**:
- `rassegna-stampa/docs-mvf/MVF_v4.0_istruzioni_operative.md` — la specifica MVF completa (1.212 righe). **È la fonte autorevole**: questo handoff ne è una sintesi orientata all'implementazione, non un sostituto.
- Il codice Python esistente implementa la **v3.0**, ferma a due versioni indietro. La Parte 2 mappa la distanza tra le due.

> **Nota di versionamento**: il file caricato si chiama `MVF_V41.MD` ma l'intestazione, il changelog e il piè di pagina dichiarano ovunque **v4.0**. Da chiarire se esistono delta v4.1 non presenti nel documento.

---

## Parte 1 — Il programma esistente

### Cosa fa

Ogni mattina alle 3:00 UTC un workflow GitHub Actions genera due briefing HTML personalizzati (per due utenti, Alex e Vale), li pubblica su GitHub Pages e li committa in archivio. Zero intervento umano.

Repository: `BigFatNeko/Main-Proxima`, branch `claude/financial-briefing-pipeline-aVCmh`
Directory di lavoro: `rassegna-stampa/`

### Flusso in 6 step

```
1. screener.py          → analizza ~500-600 titoli globali, produce JSON candidati
2. load context         → portafogli CSV utente, to-do, briefing storici
3. market snapshot      → indici e macro via yfinance
4. Claude API           → genera il briefing in markdown (claude-opus-4-6, streaming)
5. Jinja2 render        → HTML newspaper-style
6. delivery             → commit in docs/, GitHub Pages, Telegram opzionale
```

### File principali

| File | Righe | Ruolo |
|---|---|---|
| `screener.py` | 2.492 | Screener massivo: universe building, fetch dati, filtri, scoring |
| `mvf_valuation.py` | 729 | Motore di valutazione **MVF v3.0** — da riscrivere per la v4.0 |
| `briefing_pipeline.py` | 847 | Orchestratore end-to-end |
| `filiere_screener.py` | 365 | Screener per filiere tematiche (15 settori strategici) |
| `docs-mvf/MVF_v4.0_istruzioni_operative.md` | 1.212 | **La specifica target** |

### Cosa è riutilizzabile

**Da riusare quasi integralmente** — è infrastruttura, non logica di valutazione:
- Universe building TradingView, mappatura ticker TV→yfinance (`screener.py` righe 65-360)
- Fetch dati, gestione sessioni, retry, parallelismo
- Calcolo delle metriche di bilancio grezze

**Da riscrivere**: `mvf_valuation.py`, che implementa la v3.0 su base 257. La v4.0 cambia base, scala, e introduce concetti che non esistono nel codice (IQI, DIP, gate, routing per classe).

**Da ignorare**: tutto il layer briefing (chiamata Claude, template HTML, modalità giornaliere, personalizzazione utente, GitHub Actions).

---

## Parte 2 — Da MVF v3.0 (implementato) a MVF v4.0 (target)

### 2.1 — Il salto in sintesi

| | v3.0 (nel codice) | v4.0 (specifica) |
|---|---|---|
| Base di calcolo | 257, unica | **Cinque basi per classe di strumento** |
| Scala del voto | 0-100 | **0-1000** |
| Classi di strumento | una sola | **5, con routing obbligatorio** |
| Margine di sicurezza | derivato dal fair value | **derivato dall'IQI + overlay CS** |
| Indice di qualità investimento | assente | **IQI 0-100, nuovo** |
| Qualità dei dati | assente | **DIP con provenance tagging** |
| Esclusioni | 6 hard filter | **6 gate strutturali G1-G6 + red flag separati** |
| Fiscalità | assente | **Rendimento netto post-imposte obbligatorio** |

### 2.2 — Le cinque classi e le loro basi

Prima di qualsiasi calcolo, lo **STEP 0** instrada il titolo:

| Classe | Base | Lente di analisi | Sezione |
|---|---|---|---|
| Common equity | **280** | motore standard | Sez. 3 |
| REIT | **370** | AFFO/share, same-store NOI, accretion spread | Sez. 9B |
| BDC | **299** | NAV/NII, non-accrual, first-lien | Sez. 9J |
| MLP / midstream | **309** | DCF per unit (Distributable Cash Flow), K-1 | Sez. 9K |
| Preferred / ibridi | **168** (voto MVF-P) | credito e reddito: YTW, copertura, call | Sez. 9L |

Il voto è sempre normalizzato su 1000: `Voto = (punteggio grezzo / BASE) × 1000`.

> **Conseguenza diretta sui "pacchetti"**: la specifica dichiara esplicitamente che **i voti non sono confrontabili tra classi diverse** (Sez. 11F) — solo intra-classe e intra-versione. Un pacchetto income che mescola common, REIT, BDC, MLP e preferred **non può essere ordinato per voto MVF**. Serve un criterio di ranking cross-classe: i candidati naturali sono l'**IQI** (sempre su 100) o il **rendimento netto Italia**. Questa è una decisione di progetto da prendere prima di scrivere lo schema dati.

### 2.3 — Pesi common equity, base 280

```
Gross Margin                              15
EBITDA Margin                              5
Operating Margin                          25
Net Margin                                18
FCF Margin                                12    ← era 22 in v3.0
EPS Growth (CAGR 5y, min 3y)              10    ← era 18
FCF per Share Growth (CAGR 5y, min 3y)    18    ← NUOVO in v4.0
ROIC                                      15
ROE                                        3
ROA                                        5
Debt to Equity                            10
Debt to Assets                            10
Altman-Z Score                             5
SBC / Revenue                              5
CapEx / Revenue                            5
CapEx / D&A                                3
R&D / Revenue                              7
Insider Trading                            5
Dividend Yield                            16
Dividend Payout Ratio                     10
Dividend Growth (5y, min 3y)              10
Buyback of Shares                          5
Price CAGR                                 5
Multiple Expansion/Contraction (Δ P/E)     5    ← NUOVO
Tax Percentage                            13
MOAT Economico (solo Morningstar)         25
Earnings Quality (Accruals / CCR)         15
─────────────────────────────────────────────
TOTALE                                   280
```

**Le tre metriche nuove o ribilanciate** meritano attenzione perché portano guard anti-manipolazione:

- **FCF per Share Growth (18)** — bande: >12% → 100%, 8-12% → 80%, 4-8% → 60%, 0-4% → 35%, <0 → 0%. **Guard anti-diluizione**: se FCF/share cresce molto più del FCF aggregato per effetto dei buyback con FCF aggregato piatto o in calo → cap al 50% (financial engineering).
- **EPS Growth (10)** — bande: >15% → 100%, 10-15% → 80%, 5-10% → 60%, 0-5% → 35%, <0 → 0%. Stesso modificatore qualità sui buyback.
- **Multiple Expansion/Contraction (5)** — direzione value: la contrazione del multiplo è premiata, l'espansione forte penalizzata. **Value-trap guard**: multiplo contratto per fondamentali in deterioramento → max 25%.

**Segnale di qualità utili incrociato**: EPS/share in crescita ma FCF/share piatto o in calo per 2+ anni → red flag, da confermare con Accruals/CCR.

### 2.4 — Clausole di redistribuzione dei pesi

**Azienda senza dividendo**: i 36 punti dividendo (16+10+10) si redistribuiscono → FCF Margin 12→22, Buyback 5→15, Price CAGR 5→13, ROIC 15→23.

**Doppia ponderazione dividendi**: se il titolo paga dividendi *e* si applica il DDM, i pesi dividendo si dimezzano (16→8, 10→5, 10→5) e i 18 punti liberati vanno a FCF Margin 12→22 e Net Margin 18→26. Il regime va sempre dichiarato.

**Penalità Altman-Z additiva sul voto finale**: zona grigia 1,23-1,80 → −10% sul voto normalizzato; sotto 1,23 → −20%. Esenti: banche, assicurazioni, REIT, utility regolate, asset-light (es. tabacco).

### 2.5 — IQI, il concetto centralmente nuovo

L'**Indice di Qualità dell'Investimento** (0-100) è distinto dal voto MVF e **guida il margine di sicurezza**:

```
IQI = 0,40 × BLOCCO A (Solidità) + 0,60 × BLOCCO B (Prospettive & Reddito)
```

**Blocco A — Solidità (0-100)**
| Componente | Max | Contenuto |
|---|---|---|
| A1 Patrimoniale | 30 | leva D/E, D/A, NetDebt/EBITDA (12); liquidità (6); copertura interessi (6); qualità attivo + Altman-Z (6) |
| A2 Reddituale | 25 | livello margini (8); stabilità margini (7); ROIC e spread ROIC−WACC (10) |
| A3 Cassa | 30 | FCF Margin (8); costanza FCF (7); conversione + earnings quality (8); copertura FCF/(Div+CapEx mant.) (7) |
| A4 Competitiva | 15 | moat Morningstar none 0 / narrow 6 / wide 12; trend moat + capital allocation (3) |

**Blocco B — Prospettive & Reddito (0-100)**, modulato sul profilo dividendo:

| Tier dividendo | B1 Crescita | B2 Remunerazione |
|---|---|---|
| Forte (≥10 anni) | 25 | 45 |
| Solido (5-9 anni) | 32 | 38 |
| Nascente (<3 anni) | 55 | 15 |
| No div + buyback | 45 | 25 |
| Nessuna remunerazione | 70 | 0 |

Fissi in tutti i tier: **B3 Posizionamento multiplo** (15) e **B4 TSR forward** (15: ≥12% → 100, 8-12% → 70, 4-8% → 40, <4% → 10).

### 2.6 — Margine di sicurezza: derivazione a due passi

```
Prezzo Ideale = Fair Value medio ponderato × (1 − MoS_finale)
MoS_finale    = MoS_base(IQI) + overlay(CS)
```

**Passo 1 — MoS base dall'IQI**:
| IQI | MoS |
|---|---|
| ≥90 | 15% |
| 80-89 | 20% |
| 70-79 | 25% |
| 60-69 | 30% |
| 50-59 | 35% |
| 40-49 | 45% |
| 30-39 | 55% |
| <30 | **astensione** |

**Passo 2 — Overlay dal Confidence Score**: CS ≥80 → +0% · 65-79 → +5% · 50-64 → +10% con warning · **<50 → gate, non azionabile**.

Vincoli: overlay max +10%; MoS finale con cap al 60% (oltre → astensione); CS <65 → convinzione massima "Media".

**Riconciliazione MVF ↔ IQI**: Δ = (Voto MVF ÷ 10) − IQI.
- |Δ| ≤ 20 → convergenza, nessun aggiustamento
- Δ > +20 → "qualità cara": ottimo business a prezzo non attraente → watchlist, non forzare un Buy
- Δ < −20 → **sospetto value trap**: scrutinio con Reverse DCF obbligatorio, capital allocation come tie-breaker, convinzione −1 livello, MoS +1 scalino
- MVF <400 e IQI <40 → astensione confermata

### 2.7 — Pesi dei modelli di valutazione per classe

| Classe | Composizione |
|---|---|
| Con dividendo (standard) | vedi Sez. 7 della specifica |
| Senza dividendo | Graham 25 / DCF 50 / EPV 20 / Reverse DCF 5 |
| REIT | DDM 50 / DCF 30 / EPV 10 / Graham 0 + Reverse DCF sanity |
| BDC | P/NAV comparables 40 / DDM base-div 35 / EPV su NII 15 / reverse-yield 10 |
| MLP | DDM distribuzione 35 / EV-EBITDA + DCF-yield 35 / DCF-model su DCF/unit 20 / EPV 10 |
| Preferred | modelli di crescita **non applicabili**; target = min(fair value da required yield, call price) |

**Robustezza valutativa**: dispersione tra modelli <15% → pesi standard; 15-30% → media; >30% → riduci il peso dell'outlier e alza un red flag di processo. Non tocca MoS né CS.

### 2.8 — DIP: Protocollo di Integrità dei Dati

Assente dal codice attuale, e probabilmente il pezzo più oneroso da implementare.

**Gerarchia delle fonti**: SEC EDGAR programmatico (XBRL come ground truth) per US-listed, ADR e FPI → IR e bilanci IFRS per l'Europa → EDINET per il Giappone → HKEXnews/SSE/SZSE per Cina e Hong Kong → Damodaran per ERP/CRP.

**Provenance tagging su ogni dato storico**:
- `[P]` primario, fonte ufficiale
- `[V]` validato, ≥2 fonti concordi dopo normalizzazione
- `[U]` non validato, fonte singola o conflitto

Tolleranze di riconciliazione: voci esatte ≤1%, ratio ≤1 punto percentuale o ≤2% relativo.

**Pre-flight gate**: si reperisce, si tagga, si calcola un CS provvisorio. Se CS <50 o esistono input material `[U]` → output "NON AZIONABILE — DATI INSUFFICIENTI" con l'elenco dei dati mancanti. Mai una tesi ad alta convinzione su dati deboli.

**Tagging separato per gli input forward**: `[G]` guidance ufficiale, `[C]` consensus multi-broker, `[S]` stima propria. Se B1+B4 sono prevalentemente `[S]` → cap al 50%, convinzione max "Media", red flag forward.

### 2.9 — Confidence Score v4.0

Quattro sub-score da 0 a 25, ora **calcolati oggettivamente dai tag di provenienza** pesati per il peso delle metriche:

| Sub-score | Cosa misura |
|---|---|
| A. Provenienza | quota `[P]`: ≥80% → 22-25 · 60-79 → 17-21 · 40-59 → 11-16 · 20-39 → 6-10 · <20 → 0-5 |
| B. Completezza | metriche reperite vs vuote o stimate; storico 5y/3y |
| C. Puntualità | ultimo esercizio completato e auditato; prezzo e macro attuali |
| D. Coerenza | concordanza tra fonti; le discrepanze non risolte abbassano |

Lettura: ≥80 Alta · 65-79 Media · 50-64 Bassa · **<50 gate**.

### 2.10 — Gate di esclusione qualità (NO-BUY strutturale)

Distinti dai red flag: i red flag segnalano, i gate **escludono a prescindere da prezzo, MoS e IQI**.

| Gate | Condizione |
|---|---|
| **G1** | Distruzione di cassa strutturale: FCF negativo in tutti gli ultimi 5 anni (ciclici: media normalizzata negativa). SaaS growth con FCF negativo strategico esclusa dal gate |
| **G2** | Distruzione di valore persistente: ROIC−WACC < 0 per ≥4 anni normalizzati |
| **G3** | Leva fuori scala non servita: Net Debt/EBITDA oltre soglia, in aumento, **e** EBIT/oneri < 1,5x. Settori leveraged-by-design esenti |
| **G4** | Trasferimento di valore dall'azionista: diluizione netta > 5%/anno per 3 anni **e** SBC/Revenue > 8% |
| **G5** | Insolvenza tecnica confermata: Altman-Z < 1,23 (settore non esente) + almeno un secondo segnale |
| **G6** | Capital allocation distruttiva persistente: giudizio "Carente" ricorrente (Morningstar Poor + M&A distruttivi o svalutazioni goodwill ripetute) |

Regola trasversale importante: **conferma multi-segnale** — nessun segnale isolato con storia di falsi positivi esclude da solo.

### 2.11 — Fiscalità: il rendimento netto Italia

Novità v4.0, **obbligatoria per ogni titolo che paga dividendo** e particolarmente rilevante per il caso d'uso di questo progetto (cliente persona fisica residente in Italia, regime del risparmio amministrato).

```
Netto HOME   = Yield_lordo × (1 − w_home)
Netto ITALIA = Yield_lordo × (1 − w_home) × (1 − 0,26)
```

Ritenute alla fonte indicative — **la specifica impone di verificare la convenzione vigente prima dell'uso**:

| Paese | Ritenuta |
|---|---|
| USA | 15% con W-8BEN (30% senza) |
| UK | 0% |
| Paesi Bassi | 15% |
| Germania | 26,375% → 15% con rimborso |
| Francia | 25% → ~15% |
| Spagna | 19% |
| Svizzera | 35% → 15% con rimborso |
| Canada | 25% → 15% |
| Irlanda | ~15-25% |

**Casi speciali che rompono il 15% standard**:
- **REIT USA**: le ordinary dividend distributions spesso non godono del treaty → usare **30%** salvo prova contraria
- **MLP USA**: ritenuta IRC §1446 fino a **~37%**
- **BDC USA**: ordinary income, spesso 30% per non residenti

> **Il confronto tra titoli a dividendo si fa sul netto Italia**, non sul lordo. Per un pacchetto income mostrato a un cliente italiano questo è il numero che conta — e ribalta l'ordinamento rispetto allo yield lordo, soprattutto quando ci sono REIT e MLP americani in lista.

---

## Parte 3 — Il programma da costruire

### Requisiti dichiarati dal committente

> "È fondamentalmente uno screener massivo che mi consente di avere, su richiesta, il pool di titoli che soddisfano i requisiti divisi per pacchetti.
>
> Questo serve quando siamo davanti a un cliente e quel cliente vuole vedere la creazione del portafoglio lì sul posto anziché delegare noi per farlo in un altro momento.
>
> I criteri per selezionare i titoli verranno estrapolati dalle regole MVF 4.0 che usa lo stock screener."

### Il primo vincolo: latenza

Lo screener attuale impiega **dai 5 ai 45 minuti**. Davanti a un cliente è inutilizzabile.

| | Briefing (esistente) | Screener live (da costruire) |
|---|---|---|
| Quando gira | Notte, batch, non presidiato | Su richiesta, presidiato |
| Latenza accettabile | 45 minuti | **Secondi** |
| Se un dato manca | Si degrada in silenzio | Il cliente lo vede |
| Modello | Calcolo on-demand | **Pre-computazione + query** |

Architettura conseguente:

```
BATCH (notturno o settimanale, non presidiato)
  universe → fetch dati → DIP tagging → MVF 4.0 → IQI → CS → gate
                                                    ↓
                                              DATABASE

LIVE (davanti al cliente, millisecondi)
  UI → query sul DB → filtri per pacchetto → risultati
     → refresh prezzi solo per i titoli mostrati
```

### Il secondo vincolo, più serio: la v4.0 non è interamente automatizzabile

Questo è il punto che va affrontato prima di scrivere codice.

MVF v4.0 è scritta come **procedura di analisi per un operatore o un LLM che fa ricerca documentale su un singolo titolo**, non come algoritmo deterministico su migliaia di titoli. Diversi elementi non sono ottenibili da API finanziarie:

| Elemento | Perché non si automatizza facilmente |
|---|---|
| **MOAT (peso 25)** | La specifica impone "solo Morningstar" — dato proprietario a pagamento, non su yfinance |
| **DIP tagging [P]/[V]/[U]** | Richiede fetch da SEC EDGAR, riconciliazione multi-fonte e normalizzazione FY/TTM, GAAP/adjusted |
| **Same-store NOI, cap rate (REIT)** | Vivono negli supplement IR in PDF |
| **B1/B4 forward** | Servono guidance ufficiale e consensus multi-broker |
| **Capital allocation (G6)** | Giudizio qualitativo su M&A e svalutazioni ricorrenti |
| **Auditor change, CFO turnover** | Da proxy statement e comunicati |

Il MOAT da solo pesa 25 su 280, quasi il 9% del voto. Il DIP determina il CS, che determina l'overlay del MoS e può attivare un gate.

**La strada praticabile è a due livelli**:

1. **Livello screening** (batch, automatico, su migliaia di titoli): il sottoinsieme di MVF v4.0 calcolabile da dati strutturati. Produce un voto parziale dichiarato come tale, più i gate calcolabili (G1, G2, G3, G4, G5 sono quasi tutti derivabili da bilancio; G6 no).
2. **Livello analisi completa** (on-demand, sui pochi titoli che entrano nel portafoglio del cliente): MVF v4.0 integrale, con ricerca documentale, eventualmente assistita da LLM.

Il livello 1 seleziona, il livello 2 giustifica. Va deciso **come rappresentare la differenza nell'interfaccia**: un titolo con voto da screening non ha lo stesso status di un titolo con analisi completa, e mostrarli identici davanti a un cliente è fuorviante.

Una conseguenza pratica: il **Confidence Score da screening** sarà strutturalmente basso, perché i dati vengono da un aggregatore singolo (`[U]` secondo la specifica). Se si applicasse il gate CS <50 alla lettera, quasi nulla passerebbe. Serve una regola esplicita per il regime screening, diversa da quella dell'analisi completa.

### Cosa significa "pacchetti" — da chiarire

Il termine non è ancora definito. Letture possibili:

1. Per obiettivo: income / dividend growth / crescita / difensivo / speculativo
2. Per profilo di rischio: conservativo / bilanciato / aggressivo
3. Per orizzonte temporale
4. Per tema o filiera: i 15 settori strategici già mappati
5. **Portafogli pre-confezionati**: pacchetto = allocazione completa con pesi, non solo una lista

La quinta è la più coerente con "il cliente vuole vedere la creazione del portafoglio lì sul posto", ma va confermata perché determina lo schema dati.

Elementi già disponibili come base: i tag `income` e `quality` del codice v3.0 (Sez. 2.9 del vecchio handoff, ancora validi come euristica), le 15 filiere, e in v4.0 i **tier dividendo** del Blocco B (forte ≥10 anni / solido 5-9 / nascente <3 / no-div con buyback / nessuna remunerazione), che sono già una segmentazione naturale per pacchetti income.

### Domande aperte per il committente

1. **Pacchetti**: liste di candidati o allocazioni complete con pesi?
2. **Ranking cross-classe**: dato che i voti MVF non sono confrontabili tra common, REIT, BDC, MLP e preferred, su cosa si ordina un pacchetto misto? IQI, netto Italia, o si separano i pacchetti per classe?
3. **MOAT**: si compra la licenza dati Morningstar, si usa un proxy calcolato, o si accetta un voto parziale in fase di screening?
4. **Regime CS in screening**: quale soglia sostituisce il gate <50 quando per costruzione i dati sono `[U]`?
5. **Universo**: copertura globale o solo mercati sviluppati? (Vedi 4.1: davanti a un cliente un titolo senza prezzo è un problema di credibilità.)
6. **Input del cliente in sessione**: importo, orizzonte, rischio, settori da escludere, valuta, vincoli fiscali?
7. **Output**: schermo condiviso, PDF stampabile (la specifica ha già una scheda A4 in Sez. 11D), entrambi?
8. **Perimetro regolamentare**: il programma produce una raccomandazione personalizzata a un cliente. Il vincolo normativo va verificato prima di costruirlo, non dopo — nel progetto esistente è già emerso il tema della regolamentazione SCF.

---

## Parte 4 — Vincoli tecnici noti

### 4.1 — Yahoo Finance / yfinance

- **Rate limiting aggressivo**: dopo qualche centinaio di richieste la sessione decade con 401 `Invalid Crumb`. Nel programma esistente il sintomo è stato l'arricchimento prezzi fallito su 20 titoli su 20 subito dopo lo screener. Mitigazione applicata: retry con backoff 5s/10s e concorrenza ridotta da 8 a 4 thread.
- **404 sistematici**: Filippine (`.PSE`), Indonesia (`.JK`), Dubai (`.DU`), Argentina (`.BA`), alcune linee Euronext.
- **500 sporadici** lato server, transitori.
- **Timezone e calendar mancanti** per molti titoli asiatici.

Per un'applicazione mostrata a un cliente conviene un provider con SLA (Refinitiv, FactSet, Financial Modeling Prep, EODHD) almeno per i prezzi live. Il DIP della v4.0 spinge comunque verso SEC EDGAR per i fondamentali US, che è gratuito e richiede solo uno User-Agent.

### 4.2 — Costi

Il briefing usa `claude-opus-4-6` con `max_tokens = 24000` e prompt caching: circa **1,00-1,05 $ per briefing**. Con `max_tokens` elevati la SDK Anthropic **impone lo streaming** (`messages.stream()` + `get_final_message()`); `messages.create()` solleva `ValueError`.

Per lo screener live: il livello 1 è deterministico e non ha costi LLM. Il livello 2, se assistito da LLM per la ricerca documentale, ha un costo per titolo analizzato — da dimensionare sul numero di titoli che entrano davvero in un portafoglio cliente.

### 4.3 — Ambiente

Il programma esistente gira su GitHub Actions (`ubuntu-latest`, timeout 130 minuti, Python 3.11). Per un applicativo usato in presenza serve esecuzione locale o un servizio sempre attivo: GitHub Actions non è adatto a richieste interattive.

### 4.4 — Dipendenze attuali

```
tradingview-screener>=2.5.0,<3.0
finvizfinance>=1.0,<2.0
yfinance>=0.2.40,<0.3
pandas>=2.0,<3.0
numpy>=1.24,<3.0
anthropic>=0.69,<1.0
jinja2>=3.1,<4.0
markdown>=3.5,<4.0
requests>=2.31,<3.0
```

---

## Parte 5 — Ordine di lettura consigliato

1. **`rassegna-stampa/docs-mvf/MVF_v4.0_istruzioni_operative.md`** — la specifica completa. Prioritarie: Sez. 2 (STEP 0 routing), Sez. 3 (pesi), Sez. 7 (IQI, MoS, fiscalità), Sez. 8-bis (gate), Sez. 6-bis (DIP).
2. `rassegna-stampa/screener.py` righe 65-360 — configurazione, mercati, mappatura ticker, data class.
3. `rassegna-stampa/screener.py` righe 880-1210 — filtri e scoring v3.0, utili come riferimento di ciò che è già automatizzato.
4. `rassegna-stampa/mvf_valuation.py` — implementazione v3.0: da riscrivere, ma mostra come sono già strutturati i cinque modelli di valutazione e il WACC via CAPM esteso.

**Due decisioni da prendere prima di scrivere codice**, in quest'ordine:

1. **Quale sottoinsieme della v4.0 è automatizzabile in batch**, e come si dichiara la differenza tra un voto da screening e un'analisi completa.
2. **Pre-computazione su database** invece di calcolo on-demand — è la scelta che determina tutta l'architettura successiva.
