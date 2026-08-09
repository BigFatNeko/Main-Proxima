# Handoff — dal Briefing Pipeline allo Screener Live per consulenza

**Scopo di questo documento**: dare a una nuova sessione tutto il contesto necessario per costruire un **secondo programma**, diverso da quello esistente ma che ne riusa il motore di valutazione.

- **Programma esistente** (già in produzione): genera un briefing finanziario quotidiano automatico.
- **Programma da costruire**: uno screener massivo che, **su richiesta e in tempo reale davanti a un cliente**, restituisce pool di titoli che soddisfano criteri predefiniti, organizzati in pacchetti.

Il criterio di selezione dei titoli deriverà dalle **regole MVF 4.0**, evoluzione delle regole MVF v3.0 documentate qui sotto.

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
| `mvf_valuation.py` | 729 | **Motore di valutazione MVF v3.0** — il pezzo da riusare |
| `briefing_pipeline.py` | 847 | Orchestratore end-to-end |
| `filiere_screener.py` | 365 | Screener per filiere tematiche (15 settori strategici) |
| `system_prompt.md` | 365 | Istruzioni per il modello che scrive il briefing |
| `newspaper_template.html` | — | Template Jinja2 dell'output |

### Cosa è riutilizzabile per il nuovo programma

**Da riusare quasi integralmente**:
- `mvf_valuation.py` — tutto il motore di valutazione
- `screener.py` sezioni: universe building TradingView, mappatura ticker TV→yfinance, fetch dati, filtri hard/soft, calcolo metriche

**Da NON riusare**: tutto il layer briefing (chiamata Claude, template HTML, logica modalità giornaliere, personalizzazione utente).

---

## Parte 2 — Il motore MVF v3.0 (base per MVF 4.0)

Questa è la parte che conta per il nuovo programma. MVF = sistema di valutazione proprietario che assegna a ogni titolo un voto su 100 più un Confidence Score.

### 2.1 — Universe building

Fonte primaria: **TradingView screener** (libreria `tradingview-screener`), con fallback su `finvizfinance` per il mercato USA.

Mercati coperti (`TV_MARKETS`):
- **US**: america
- **EU**: italy, germany, france, spain, netherlands, switzerland, uk, sweden, denmark, norway, finland, belgium, ireland, austria, portugal, poland, turkey, greece, hungary, czech_republic
- **ASIA**: japan, china, hong_kong, korea, india, singapore, taiwan, australia, indonesia, malaysia, thailand, vietnam, philippines, new_zealand
- **LATAM**: brazil, mexico, chile, colombia, argentina
- **AFRICA_ME**: south_africa, saudi_arabia, israel, uae

I ticker TradingView vengono convertiti in ticker yfinance tramite `TV_TO_YF_SUFFIX` (es. `BIT` → `.MI`, `XETR` → `.DE`, `EURONEXT` → `.PA`, `LSE` → `.L`).

**Nota critica per il nuovo programma**: molti mercati emergenti (`.PSE` Filippine, `.JK` Indonesia, `.DU` Dubai, `.BA` Argentina) restituiscono sistematicamente 404 da Yahoo Finance. Nel programma esistente questi errori sono tollerati e ignorati. Se il nuovo programma deve mostrare risultati a un cliente, conviene **escludere a monte** i mercati non coperti da dati affidabili.

Filtri di ingresso all'universe:
```python
min_market_cap_million = 300     # small-cap 300M+ inclusi
min_price_usd = 0.50
data_years = 5
```

### 2.2 — Hard filters (esclusione immediata)

Un titolo che fa scattare **anche uno solo** di questi flag viene escluso:

| Filtro | Soglia | Eccezioni |
|---|---|---|
| `altman_z_below_1_23` | Altman Z < 1,23 (zona distress) | banche, assicurazioni, REIT |
| `fcf_negative_3y` | Free cash flow negativo per 3 anni consecutivi | — |
| `debt_equity_above_3` | Debt/Equity > 3,0 | banche, assicurazioni |
| `net_margin_neg_2_of_3` | Margine netto negativo in 2 anni su 3 | — |
| `goodwill_over_50_pct_equity` | Goodwill > 50% del patrimonio netto | — |
| `sbc_over_8_pct_revenue` | Stock-based comp > 8% dei ricavi | solo settori Tech/Software |

### 2.3 — Soft filters (warning, non escludono)

Ogni warning attivo sottrae 3 punti dal composite score:

| Filtro | Soglia |
|---|---|
| `altman_z_grey_zone` | 1,23 ≤ Altman Z ≤ 1,81 |
| `fcf_negative_1_of_3` | FCF negativo in 1 anno su 3 |
| `payout_above_100` | Payout ratio > 100% |
| `revenue_decline_2y` | Ricavi in calo per 2 anni consecutivi |
| `roe_below_capm_r` | ROE inferiore al costo del capitale (WACC) |
| `accruals_above_0_10` | Accruals ratio > 0,10 (qualità utili scadente) |
| `ccr_below_0_5` | Cash conversion ratio < 0,5 |
| `share_dilution_above_3_pct` | Diluizione azionaria > 3% annuo |
| `tax_rate_volatile_below_10` | Tax rate < 10% (anomalo/volatile) |

### 2.4 — Punteggio MVF: 24 metriche, base 257 punti

Il voto MVF nasce da 24 metriche pesate, normalizzate su una base di 257 punti e riportate su scala 100.

```python
MVF_WEIGHTS = {
    # Redditività (103 punti)
    "gross_margin": 15, "ebitda_margin": 5, "operating_margin": 25,
    "net_margin": 18, "fcf_margin": 22, "roic": 15, "roe": 3, "roa": 5,

    # Solidità patrimoniale (25 punti)
    "debt_to_equity": 10, "debt_to_assets": 10, "altman_z": 5,

    # Efficienza del capitale (25 punti)
    "sbc_revenue": 5, "capex_revenue": 5, "capex_da": 3,
    "rd_revenue": 7, "insider_trading": 5,

    # Ritorno per l'azionista (46 punti)
    "dividend_yield": 16, "payout_ratio": 10, "dividend_growth_5y": 10,
    "buyback_yield": 5, "price_cagr_5y": 5,

    # Qualità del business (53 punti)
    "tax_rate": 13, "moat_score": 25, "earnings_quality": 15,
}
# somma = 257 (verificata da assert nel codice)
```

Target ottimali per la normalizzazione (valore che porta la metrica al punteggio pieno):

```python
MVF_TARGETS = {
    "gross_margin": 0.50, "ebitda_margin": 0.25, "operating_margin": 0.20,
    "net_margin": 0.15, "fcf_margin": 0.15, "roic": 0.15, "roe": 0.15,
    "roa": 0.08, "debt_to_equity": 0.60, "debt_to_assets": 0.30,
    "altman_z": 3.0, "sbc_revenue": 0.03, "capex_revenue": 0.05,
    "capex_da": 1.2, "rd_revenue": 0.08, "insider_trading": 0.0,
    "dividend_yield": 0.04, "payout_ratio": 0.50, "dividend_growth_5y": 0.05,
    "buyback_yield": 0.03, "price_cagr_5y": 0.10, "tax_rate": 0.22,
    "moat_score": 7.0, "earnings_quality": 1.0,
}

# Metriche dove "più basso è meglio" (normalizzazione invertita)
MVF_INVERTED = {"debt_to_equity", "debt_to_assets", "sbc_revenue",
                "capex_revenue", "payout_ratio", "tax_rate"}
```

### 2.5 — I cinque modelli di valutazione

Per ogni titolo `mvf_valuation.py` calcola il fair value con cinque metodi indipendenti:

1. **Graham** — formula rivista, con floor sul rendimento risk-free al 2,5%
2. **DDM a 1 stadio** — Gordon growth, per società a dividendo stabile
3. **DDM a 2 stadi** — crescita alta iniziale poi perpetua
4. **DCF a 2 stadi su 10 anni** — con tabella di sensitività 5×5 (WACC ±100/±200 bp × crescita terminale ±100/±200 bp)
5. **EPV (Earnings Power Value)** — valore degli utili normalizzati senza crescita

Più un **Reverse DCF** che estrae la crescita implicita nel prezzo corrente.

Il fair value finale è una **media ponderata dei cinque modelli**, con pesi che variano per regime (settore, presenza di dividendo). Da questo derivano:
- `weighted_fair_value` — fair value di riferimento
- `margin_of_safety_pct` — margine di sicurezza
- `ideal_purchase_price` — prezzo ideale di acquisto
- `upside_at_current_pct` — upside al prezzo corrente

Scenari: `bull_fv`, `base_fv`, `bear_fv`, ed `expected_fv = 0,25 × bull + 0,50 × base + 0,25 × bear`.

### 2.6 — WACC via CAPM esteso

```
WACC = Rf + beta × ERP + CRP
```

Costanti per mercato (fonte Damodaran NYU, aggiornamento semestrale):

| Mercato | Risk-free | ERP | Country Risk Premium |
|---|---|---|---|
| US | 4,3% | 5,5% | 0,0% |
| EU core | 2,5% | 5,8% | 0,0% |
| Italia | 3,8% | 6,3% | 1,8% |
| Spagna | 3,2% | 6,0% | 0,8% |
| UK | 4,0% | 5,7% | 0,0% |
| Giappone | 1,3% | 6,1% | 0,5% |
| Emergenti | 7,5% | 8,5% | 3,0% |

Vincoli: `g_terminal_max = 2%`, `g_perpetua_max = 4%`, `rf_floor = 2,5%`.

Viene inoltre calcolato l'**economic spread** = ROIC − WACC, con flag se negativo per 2 anni.

### 2.7 — Confidence Score (0-100)

Quattro sotto-punteggi da 0 a 25 ciascuno:

| Sub-score | Cosa misura |
|---|---|
| `data_quality` | Completezza dei dati, affidabilità fonti, coerenza interna |
| `business_stability` | Volatilità del FCF, maturità del business, concentrazione clienti |
| `projection_reliability` | Ciclicità, esposizione macro, visibilità sulla pipeline |
| `model_coherence` | Dispersione tra i fair value dei cinque modelli |

**Questo è un elemento chiave per l'uso davanti a un cliente**: un voto MVF alto con Confidence basso significa "il numero c'è ma non ci puoi appoggiare una decisione". Nel nuovo programma va reso visibile, non nascosto.

### 2.8 — Composite score e bonus

Oltre al voto MVF esiste un `composite_score` con un sistema di bonus/malus:

| Fattore | Effetto |
|---|---|
| Piotroski F-Score ≥ 8 | +10 |
| Piotroski F-Score ≥ 6 | +5 |
| Piotroski F-Score < 4 | −5 |
| Moat score (scala 0-10) | +1,5 × punteggio (max +15) |
| DCF upside > 10% | +min(upside × 20, 10) |
| Appartenenza a filiera strategica | +5 |
| Accelerazione utili > 5% | +5 |
| EV/EBITDA < 8 | +8 |
| EV/EBITDA < 12 | +4 |
| EV/EBITDA > 20 | −4 |
| FCF yield > 8% | +8 |
| FCF yield > 5% | +4 |
| FCF yield > 3% | +2 |
| Ogni soft filter attivo | −3 |

### 2.9 — Tag di strategia già implementati

Il programma esistente etichetta i titoli con questi tag — **sono il punto di partenza naturale per i "pacchetti" del nuovo programma**:

**`income`** — richiede tutte queste condizioni:
```python
dividend_yield > 0.04 and payout_ratio < 0.80 and pe_ratio < 18
and net_margin > 0.05 and debt_to_equity < 1.5
```

**`quality`**:
```python
operating_margin > 0.15 and roic > 0.12
and debt_to_equity < 1.0 and warning_count <= 1
```

**`post_news_bull`** — sorpresa utili > +5% ma il prezzo si è mosso meno del 3% nei 5 giorni successivi (reazione mancata al rialzo)

**`post_news_bear`** — sorpresa utili < −5% con stessa mancata reazione

### 2.10 — Filiere strategiche (15)

Mappatura industria → filiera, usata per il tag tematico:

**Classiche**: semiconduttori, difesa, uranio/nucleare, energia oil&gas, rare earth e metalli, batterie/litio/storage, gestione rifiuti, consumer staples, helium e gas industriali

**Meno analizzate** (bassa copertura analisti, potenziale alfa): agroalimentare upstream (fertilizzanti, sementi, macchinari), siderurgia e metalli speciali, shipping marittimo (container/bulk/tanker), infrastrutture idriche, riassicurazione specialty, packaging e foreste

### 2.11 — Tier del programma esistente

| Tier | Cosa contiene | Universo |
|---|---|---|
| **Tier 1** | Quality — analisi MVF completa | 500 titoli, market cap > 300M |
| **Tier 2** | Speculative/catalyst — segnali di volume, short squeeze, accelerazione | market cap 5M-500M, prezzo > 0,10 |
| **Tier 3** | Special situations | buckets tematici |
| **Filiere** | Candidati per settore strategico | 15 filiere |

---

## Parte 3 — Il programma da costruire

### Requisiti dichiarati dal committente

> "È fondamentalmente uno screener massivo che mi consente di avere, su richiesta, il pool di titoli che soddisfano i requisiti divisi per pacchetti.
>
> Questo serve quando siamo davanti a un cliente e quel cliente vuole vedere la creazione del portafoglio lì sul posto anziché delegare noi per farlo in un altro momento.
>
> I criteri per selezionare i titoli verranno estrapolati dalle regole MVF 4.0 che usa lo stock screener."

### Contesto d'uso

Consulenza finanziaria **in presenza**. Il consulente è seduto davanti al cliente, il cliente esprime preferenze o vincoli, e il portafoglio si costruisce sul momento. È una situazione di vendita: la latenza e gli errori visibili costano credibilità.

### Il vincolo architetturale centrale

**Lo screener attuale impiega dai 5 ai 45 minuti per girare.** Analizza 500-600 titoli scaricando bilanci completi da Yahoo Finance, uno alla volta, in parallelo su 8 thread.

Davanti a un cliente questo è inutilizzabile. La differenza fondamentale tra i due programmi non è funzionale, è **temporale**:

| | Briefing (esistente) | Screener live (da costruire) |
|---|---|---|
| Quando gira | Notte, batch, non presidiato | Su richiesta, presidiato |
| Latenza accettabile | 45 minuti | **Secondi** |
| Se un dato manca | Si degrada in silenzio | Il cliente lo vede |
| Modello | Calcolo on-demand | **Pre-computazione + query** |

La conseguenza progettuale è netta: il nuovo programma **non può calcolare MVF al momento della richiesta**. Deve avere un database pre-calcolato, aggiornato in batch (notturno o settimanale), e in sessione limitarsi a interrogarlo e filtrarlo.

Architettura suggerita:

```
BATCH (notturno, non presidiato)
  universe building → fetch dati → MVF 4.0 → scrittura su DB
                                              (SQLite / Parquet / Postgres)

LIVE (davanti al cliente, millisecondi)
  UI → query sul DB → filtri per pacchetto → risultati
     → eventuale refresh prezzi solo per i titoli mostrati
```

Solo i prezzi correnti vanno aggiornati in tempo reale, e solo per la manciata di titoli effettivamente visualizzati. Tutto il resto (bilanci, fair value, voti, confidence) è pre-computato.

### Cosa significa "pacchetti" — da chiarire

Il termine non è stato ancora definito dal committente. Le letture possibili:

1. **Per obiettivo dell'investitore**: income / dividend growth / crescita / difensivo / speculativo
2. **Per profilo di rischio**: conservativo / bilanciato / aggressivo
3. **Per orizzonte**: breve / medio / lungo termine
4. **Per tema o filiera**: i 15 settori strategici già mappati
5. **Portafogli pre-confezionati**: pacchetto = allocazione completa pronta, non solo una lista

L'interpretazione 5 è la più coerente con il caso d'uso descritto ("il cliente vuole vedere la creazione del portafoglio lì sul posto"), ma va confermata prima di progettare lo schema dati.

Base di partenza già disponibile: i tag `income` e `quality` della sezione 2.9, più le 15 filiere della 2.10.

### Domande da porre al committente prima di scrivere codice

1. **Pacchetti**: quali sono esattamente, e sono liste di candidati o allocazioni complete con pesi?
2. **MVF 4.0**: quali regole cambiano rispetto alla v3.0 documentata sopra? Pesi diversi, metriche nuove, soglie riviste?
3. **Ampiezza dell'universo**: si mantiene la copertura globale o ci si concentra sui mercati sviluppati? (Vedi il problema dei 404 sui mercati emergenti in 2.1 — davanti a un cliente un titolo senza prezzo è imbarazzante.)
4. **Input del cliente**: cosa può scegliere in sessione? Importo, orizzonte, rischio, settori da escludere, valuta?
5. **Output**: schermo condiviso, PDF stampabile, entrambi?
6. **Frequenza di aggiornamento del batch**: giornaliera come oggi, o settimanale è sufficiente?
7. **Vincoli normativi**: il programma produce una raccomandazione personalizzata? In tal caso il perimetro regolamentare (consulenza finanziaria) va verificato prima, non dopo.

---

## Parte 4 — Vincoli tecnici da tenere presenti

### Yahoo Finance / yfinance

- **Rate limiting aggressivo**. Dopo qualche centinaio di richieste la sessione decade con errore 401 `Invalid Crumb`. Nel programma esistente il problema si è manifestato così: dopo lo screener completo, l'arricchimento prezzi del portafoglio falliva su 20 titoli su 20. Mitigazione applicata: retry con backoff 5s/10s e riduzione della concorrenza da 8 a 4 thread.
- **404 sistematici** su Filippine, Indonesia, Dubai, Argentina, alcune linee di Euronext.
- **500 sporadici** lato server, transitori.
- **Timezone/calendar mancanti** per molti titoli asiatici.

Per un'applicazione mostrata a un cliente, valutare un data provider a pagamento con SLA (Refinitiv, FactSet, Financial Modeling Prep, EODHD) almeno per i prezzi live.

### Costi API modello

Il briefing usa `claude-opus-4-6` con `max_tokens = 24000` e prompt caching sul system prompt. Costo osservato: circa **1,00-1,05 $ per briefing generato**. Con `max_tokens` elevati la SDK Anthropic **impone lo streaming** (`messages.stream()` + `get_final_message()`); `messages.create()` solleva `ValueError`.

Se il nuovo programma non deve generare testo narrativo, questo costo non si applica — è puro screening deterministico.

### Ambiente di esecuzione

Il programma esistente gira su GitHub Actions (`ubuntu-latest`, timeout 130 minuti, Python 3.11). Per un applicativo usato in presenza serve invece un'esecuzione locale o un servizio sempre attivo — GitHub Actions non è adatto a richieste interattive.

### Dipendenze

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

## Parte 5 — Riepilogo operativo per chi riceve questo documento

**Da leggere per primo nel repository** (`BigFatNeko/Main-Proxima`, branch `claude/financial-briefing-pipeline-aVCmh`):

1. `rassegna-stampa/mvf_valuation.py` — il motore da portare a MVF 4.0, 729 righe, autonomo
2. `rassegna-stampa/screener.py` righe 65-360 — configurazione, mercati, data class
3. `rassegna-stampa/screener.py` righe 880-1210 — filtri e scoring

**Da ignorare**: tutto ciò che riguarda briefing, template HTML, system prompt, personalizzazione utente, GitHub Actions.

**Primo problema da risolvere in ordine di importanza**: il passaggio da calcolo on-demand a pre-computazione su database. È la scelta che determina tutta l'architettura successiva.
