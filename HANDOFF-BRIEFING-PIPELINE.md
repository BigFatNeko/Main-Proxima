════════════════════════════════════════════════════════════════════════════
HANDOFF OPERATIVO — PROXIMA BRIEFING PIPELINE
════════════════════════════════════════════════════════════════════════════

Destinatario:  nuova sessione di coding sullo stesso progetto
Stato:         in produzione, funzionante. MVF v4.1 attivo.
Ultimo run:    #117 dell'11 agosto 2026, success, 15m 53s
Aggiornato:    11 agosto 2026

Questo documento serve a riprendere il lavoro senza rileggere il codice.
Le questioni aperte (Sez. 5) hanno ID stabili: si possono affrontare in
qualunque ordine, ognuna è indipendente.

NON confondere con HANDOFF-SCREENER-LIVE.md, che riguarda un PROGETTO
DIVERSO (screener interattivo per consulenza davanti al cliente).

────────────────────────────────────────────────────────────────────────────
COORDINATE
────────────────────────────────────────────────────────────────────────────
  Repo        BigFatNeko/Main-Proxima
              (il vecchio nome Main-Marketing redirige: le API GitHub
               accettano ancora "Main-Marketing" come owner/repo)
  Branch      claude/financial-briefing-pipeline-aVCmh
              173 commit avanti a main, 5 indietro
  Directory   rassegna-stampa/    <- questa e' la directory viva
  Workflow    .github/workflows/briefing.yml
  Pubblicato  docs/alex-latest.html, docs/vale-latest.html (GitHub Pages)
  Specifica   rassegna-stampa/docs-mvf/MVF_v4.0_istruzioni_operative.md
              (dichiara v4.0 nell'intestazione, la versione corrente e' 4.1)


════════════════════════════════════════════════════════════════════════════
SEZIONE 1 — COSA FA IL SISTEMA
════════════════════════════════════════════════════════════════════════════

Ogni mattina alle 3:00 UTC un workflow GitHub Actions genera due briefing
finanziari HTML personalizzati (Alex e Vale), li pubblica su GitHub Pages e
li archivia in git. Zero intervento umano.

  1. screener.py       analizza ~300 titoli globali -> JSON candidati
  2. load context      portafogli CSV, to-do, briefing storici
  3. market snapshot   indici e macro
  4. Claude API        genera il briefing markdown (claude-opus-4-6, streaming)
  5. Jinja2            render HTML newspaper-style
  6. delivery          commit in docs/, GitHub Pages

  FILE                    RIGHE   RUOLO
  ─────────────────────────────────────────────────────────────────────
  screener.py             2.783   universe, fetch, filtri, scoring, MVF
  mvf_valuation.py        1.865   motore di valutazione MVF v4.1
  briefing_pipeline.py      897   orchestratore end-to-end
  edgar_client.py           637   cross-check XBRL su SEC EDGAR
  filiere_screener.py       365   15 filiere tematiche
  system_prompt.md          365   istruzioni al modello che scrive


════════════════════════════════════════════════════════════════════════════
SEZIONE 2 — MVF v4.1: COSA E' STATO IMPLEMENTATO
════════════════════════════════════════════════════════════════════════════

Il modulo e' stato riscritto dalla v3.0 (base 257, voto /100) alla v4.1.
Non era un aggiornamento di parametri: e' cambiata l'architettura.

A. IMPLEMENTATO E ATTIVO
   · STEP 0 di routing per classe (Sez. 2 della specifica)
     common 280 | REIT 370 | BDC 299 | MLP 309 | preferred 168
   · Voto su 1000, base 280 per le azioni ordinarie
   · Metriche nuove con i loro guard: FCF/share growth (18), EPS growth
     (10), Multiple expansion (5)
   · Clausole di redistribuzione: senza dividendo, DDM attivo
   · Penalita' Altman-Z additiva (-10% / -20%), con esenzioni settoriali
   · IQI (Blocco A + B) che guida il margine di sicurezza
   · MoS a due passi: base da IQI + overlay da CS, cap 60%, astensioni
   · Gate di qualita' G1-G5 (G6 non valutabile senza fonte qualitativa)
   · Riconciliazione Voto <-> IQI con i tre verdetti
   · Rendimento netto post-imposte HOME vs ITALIA, con i casi speciali
     REIT/MLP/BDC USA
   · Return attribution (decomposizione log del rendimento)

B. DELIBERATAMENTE NON IMPLEMENTATO (regime S = screening batch)
   · Motori REIT/BDC/MLP/preferred: le classi vengono RILEVATE e marcate
     senza voto. Il motore common userebbe metriche non pertinenti.
     Casi reali nei portafogli: MITT (REIT) e SMSD (preferred).
   · MOAT Morningstar: sostituito da proxy euristico da fondamentali,
     dichiarato come deviazione in moat_proxy_score()
   · DIP completo con tagging [P]/[V]/[U] su tutte le fonti

C. DECISIONI PRESE CON IL COMMITTENTE
   · yfinance = [V], non [U]. Cap provenienza 18/25; 21 con riscontro
     EDGAR concorde; 10 se il riscontro e' discorde.
   · IQI con B1/B4 da proxy storici, taggati [S], con il cap combinato al
     50% previsto dalla specifica per quel caso.

D. BUG CORRETTO DURANTE LA RISCRITTURA — leggere prima di toccare i pesi
   In v3.0 normalize_metric() divideva il rapporto per 2: raggiungere il
   target valeva 0.5, e un titolo eccellente si fermava a ~570/1000. Su
   quella scala il Voto non era commensurabile con l'IQI e la
   riconciliazione Delta = Voto/10 - IQI segnalava "value trap" su
   qualunque titolo di qualita'. Ora il target vale punteggio pieno.
   Profili di controllo: eccellente 946/1000 IQI 83, mediocre 530/44,
   scarso 296/17 — tutti con verdetto "convergenza".


════════════════════════════════════════════════════════════════════════════
SEZIONE 3 — CROSS-CHECK SEC EDGAR
════════════════════════════════════════════════════════════════════════════

edgar_client.py implementa la gerarchia primary-first del DIP: i valori
yfinance vengono confrontati con l'XBRL depositato presso la SEC.

  Esito         Provenienza   Significato
  ────────────────────────────────────────────────────────────────────
  agree         21/25         EDGAR conferma il dato
  conflict      10/25 -> [U]  fonti discordi: valgono meno di una sola
  partial       invariata     meno di 3 campi confrontabili
  not_covered   18/25 -> [V]  fuori dal perimetro SEC

  · Nessuna API key, solo EDGAR_USER_AGENT (secret gia' configurato)
  · Tolleranze della specifica: 1% voci esatte, 1 p.p. o 2% sui ratio
  · Budget 60 lookup/run (EDGAR_MAX_LOOKUPS), cache dei soli estratti
    normalizzati (~0,8 KB per emittente contro i MB del grezzo)
  · Degradazione graziosa: ogni errore lascia il pipeline su yfinance

  RISULTATO REALE DEL RUN #117 — da tenere presente:

    276 titoli valutati: 3 confermati, 0 in conflitto, 0 parziali,
    273 fuori perimetro SEC | download 4 | budget residuo 56/60

  Il meccanismo funziona (zero conflitti, zero errori HTTP) ma copre
  l'1% dei candidati: lo screener lavora su universo globale (~45
  mercati) e gli Stati Uniti sono un mercato su quarantacinque con
  --limit-per-market 50. Vedi P3.


════════════════════════════════════════════════════════════════════════════
SEZIONE 4 — RISK ASSESSMENT yfinance (sintesi)
════════════════════════════════════════════════════════════════════════════

Documento completo: rassegna-stampa/docs-mvf/RISK-ASSESSMENT-yfinance.md

Il rischio dominante NON e' l'accuratezza ma la disponibilita'
intermittente e silenziosa. Evidenza dal progetto: tre run dello stesso
giorno sullo stesso universo hanno prodotto 240, 174 e 65 candidati Tier 1
senza sollevare un solo errore fatale, pubblicando ogni volta un briefing
dall'aria normale.

Mitigazione attiva: _log_coverage() in screener.py registra i candidati per
run e allerta oltre il 40% di scostamento dalla media degli ultimi 10.
Verificato: il crollo a 65 produce "COPERTURA ANOMALA ... -73%".

  ATTENZIONE: coverage_history.json vive in data/screener_results/, che su
  CI non persiste tra run. Finche' non entra in actions/cache lo storico
  riparte da zero ogni volta e l'allerta non puo' scattare. Vedi P7.

Affidabilita' per classe di dato:
  ALTA   prezzi e serie storiche large/mid cap su mercati sviluppati
  MEDIA  conto economico e stato patrimoniale annuali (normalizzazione
         dell'aggregatore non documentata)
  BASSA  small cap, mercati emergenti, dati forward, trimestrali
  NULLA  MOAT, same-store NOI, AFFO, guidance, consensus


════════════════════════════════════════════════════════════════════════════
SEZIONE 5 — QUESTIONI APERTE
════════════════════════════════════════════════════════════════════════════

Indipendenti fra loro. ID stabili per riferimento.

  P1 — WORKFLOW YAML DIVERGENTE TRA BRANCH E MAIN   [priorita' alta]
       Il file su branch ha 61 righe in piu' di quello su main: secret
       EDGAR_USER_AGENT, step "Cache SEC EDGAR", mkdir edgar_cache.
       workflow_dispatch legge la definizione dal ref che gli passi, ma i
       run SCHEDULATI usano sempre il default branch.
       Conseguenza: i briefing automatici delle 3:00 girano SENZA EDGAR.
       Fix: portare briefing.yml su main (PR o cherry-pick).
       Verifica: negli step del job deve comparire "Cache SEC EDGAR".

  P2 — PREZZI PORTAFOGLIO A ZERO                     [priorita' alta]
       Run #117: "Portfolio prices enriched: 0/23 posizioni" per Alex.
       Causa: dopo uno screener da 300 candidati la sessione yfinance e'
       gia' decaduta (401 Invalid Crumb) quando tocca al portafoglio.
       Il retry con backoff 5s/10s e la riduzione a 4 thread non bastano.
       Sintomo rivelatore: Vale, che gira dopo con cache screener e
       sessione fresca, i prezzi li ottiene.
       Fix proposto: invertire l'ordine — arricchire i prezzi del
       portafoglio PRIMA di lanciare lo screener. E' il dato che l'utente
       vede per primo nella grid HTML.

  P3 — EDGAR COPRE SOLO L'1% DEI CANDIDATI           [decisione]
       Vedi Sez. 3. Non e' un bug: e' il perimetro SEC contro un universo
       globale. Opzioni:
         a) restringere l'universo ai mercati sviluppati con piu' peso USA
         b) seconda fonte a pagamento per l'Europa (Financial Modeling
            Prep, EODHD, Twelve Data)
         c) accettare l'1% e usare EDGAR solo per i titoli in portafoglio
       Nota: (c) e' probabilmente il miglior rapporto valore/costo, perche'
       i titoli che contano davvero sono le 37 posizioni dei due portafogli,
       non i 300 candidati dello screener.

  P4 — CONTROLLI DI COERENZA INTERNA NON ALIMENTATI  [basso costo]
       compute_confidence_score() espone gia' il parametro
       internal_coherence_ok ma nessuno lo valorizza.
       Da implementare: quadratura attivo = passivo + patrimonio netto;
       FCF ~= CFO - CapEx; salti anno su anno oltre +/-60% su ricavi o
       patrimonio; margini fuori da [-100%, +100%]; payout negativo.
       Nessuna dipendenza esterna, migliora subito il sub-score D.

  P5 — SECONDA FONTE PER I TITOLI EUROPEI            [decisione, a costo]
       EDGAR non copre ENI, RMS, STLAP, PST, TGYM, CS.PA, WKL.AS, SAN.PA,
       IMAE, IJPA — cioe' gran parte dei due portafogli. Restano [V] non
       verificati. Non esiste un equivalente paneuropeo gratuito.

  P6 — MOTORI DELLE CLASSI NON-COMMON                [progetto a se']
       MITT (REIT) e SMSD (preferred) oggi non ricevono voto. Implementare
       il motore REIT richiede AFFO, same-store NOI e accretion spread, che
       non sono su yfinance (stanno nei supplement IR in PDF). Da valutare
       solo se il peso di quelle posizioni lo giustifica.

  P7 — STORICO COPERTURA NON PERSISTE                [basso costo]
       coverage_history.json sta in data/screener_results/, che non e' in
       actions/cache. Aggiungerlo (o spostarlo in edgar_cache/, gia'
       cachata) perche' l'allerta di P-copertura possa funzionare davvero.


════════════════════════════════════════════════════════════════════════════
SEZIONE 6 — COME LAVORARE SUL PROGETTO
════════════════════════════════════════════════════════════════════════════

A. TEST LOCALE (sempre prima di pushare)
     cd rassegna-stampa
     BRIEFING_PORTFOLIO_DIR=$PWD/portafogli_examples \
       python3 briefing_pipeline.py --user vale --dry-run
     # --dry-run salta screener e chiamata API: verifica CSV, routing,
     # render HTML. Costo zero.

   Attesi: "Portfolio vale: 14 posizioni, cash=433, pac=400"
           "Portfolio alex: 23 posizioni, cash=2, pac=0"

B. TEST DEL MOTORE MVF
     python3 -c "import mvf_valuation as m; ..."
   Le funzioni sono pure e testabili singolarmente: classify_instrument,
   compute_mvf_score, compute_iqi, evaluate_quality_gates,
   compute_final_mos, compute_net_yield, reconcile_mvf_iqi.

C. TEST EDGAR
     EDGAR_USER_AGENT="Nome Cognome email@dominio.it" \
       python3 edgar_client.py AAPL KO JNJ MITT

D. LANCIARE IL WORKFLOW
   Da codice: mcp__github__actions_run_trigger con
     owner=BigFatNeko, repo=Main-Marketing (il redirect funziona),
     workflow_id=briefing.yml,
     ref=claude/financial-briefing-pipeline-aVCmh   <- NON "main",
     altrimenti usa il YAML vecchio (vedi P1)
   Durata tipica: 15-16 minuti.

E. LEGGERE I LOG DI UN RUN
   list_workflow_runs restituisce output enormi: salvarlo e usare grep,
   non leggerlo tutto. Il run_number (#117) NON e' il run_id: serve l'id
   numerico lungo per list_workflow_jobs.
   Poi get_job_logs con return_content=false da' un URL scaricabile con
   curl, molto piu' pratico del contenuto inline.

F. GIT
   Il remote ha auto-commit del bot ("briefing Alex + Vale <data>") dopo
   ogni run: fare SEMPRE
     git pull origin claude/financial-briefing-pipeline-aVCmh --rebase
   prima di pushare, altrimenti il push viene rifiutato.


════════════════════════════════════════════════════════════════════════════
SEZIONE 7 — INSIDIE NOTE (costate tempo, non ripeterle)
════════════════════════════════════════════════════════════════════════════

  · CSV PORTAFOGLI: una virgola dentro il campo note rompe il parsing
    pandas ("Expected 5 fields, saw 6"). Scrivere "4 az. per 302 EUR",
    non "4 az, 302 EUR".

  · DATAFRAME yfinance: le voci di bilancio sono l'INDICE (righe), le date
    sono le COLONNE. Costruire un fixture con
    pd.DataFrame(dict, columns=date) produce un frame di NaN silenzioso:
    usare pd.DataFrame(dict, index=date).T.

  · SDK ANTHROPIC: con max_tokens elevati (24.000) messages.create()
    solleva ValueError. Serve messages.stream() + get_final_message().

  · BILLING ANTHROPIC: "credit balance too low" e' il SALDO, non il limite
    mensile. Alzare il limite non aggiunge credito.

  · WORKSPACE ANTHROPIC: la chiave API appartiene a un workspace specifico
    ("Rassegna Stampa"); i crediti di un altro workspace non sono
    utilizzabili.

  · PROXY DI QUESTO AMBIENTE: yfinance e' bloccato (SSL reset), EDGAR e le
    API GitHub funzionano. Non si possono testare i prezzi live in locale.

  · workflow_dispatch legge il YAML dal ref passato, ma il codice Python
    arriva dal branch che fa checkout lo step 2. Si possono avere
    contemporaneamente YAML vecchio e codice nuovo — e' esattamente cio'
    che e' successo nel run #116.

  · OSSERVABILITA': i messaggi a livello debug non compaiono nei log di
    Actions. Un modulo silenzioso e' indistinguibile da un modulo che non
    ha mai girato. Emettere sempre un riepilogo INFO a fine run.


════════════════════════════════════════════════════════════════════════════
SEZIONE 8 — CONTESTO UTENTI (per capire le scelte di prodotto)
════════════════════════════════════════════════════════════════════════════

Il profilo completo e le regole di scrittura sono in system_prompt.md.
Qui solo cio' che serve a chi tocca il codice.

  ALEX   ~320.129 EUR, 23 posizioni, P&L +47.544. Liquidita' 2,04 EUR:
         azzerata. Il briefing non deve proporre acquisti senza indicare
         da dove viene il denaro.
  VALE   ~6.556 EUR, 14 posizioni, P&L +471. PAC 400 EUR/mese con overlay
         reserve a scaglioni (-7% / -14% / -21%): il primo scaglione e'
         stato consumato su MITT il 7 agosto. Liquidita' 432,88 EUR = la
         reserve residua.

  Entrambi sono investitori persone fisiche residenti in Italia: per questo
  la v4.1 impone il confronto sul rendimento NETTO ITALIA, non sul lordo.


════════════════════════════════════════════════════════════════════════════
FINE HANDOFF
════════════════════════════════════════════════════════════════════════════
Da fare per primo, se si vuole un impatto immediato: P1 (i briefing
automatici girano senza EDGAR) e P2 (i prezzi del portafoglio sono a zero
per Alex, ed e' la prima cosa che vede aprendo la pagina).
════════════════════════════════════════════════════════════════════════════
