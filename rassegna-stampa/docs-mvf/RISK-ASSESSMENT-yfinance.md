════════════════════════════════════════════════════════════════════════════
RISK ASSESSMENT — AFFIDABILITÀ DI yfinance COME FONTE DATI MVF
════════════════════════════════════════════════════════════════════════════

Oggetto:   quanto fidarsi di yfinance nel tagging DIP (Sez. 6-bis MVF v4.1)
Contesto:  regime S (screening batch), pipeline Proxima Briefing
Evidenza:  log di produzione GitHub Actions + documentazione pubblica
Verdetto:  [V] difendibile con riserve — ma il rischio dominante non è
           l'accuratezza, è la DISPONIBILITÀ INTERMITTENTE E SILENZIOSA

────────────────────────────────────────────────────────────────────────────
SINTESI ESECUTIVA
────────────────────────────────────────────────────────────────────────────

La classificazione [V] regge per il caso d'uso, ma per una ragione diversa
da quella che sembra ovvia. yfinance non è pericoloso perché restituisce
numeri sbagliati: quando risponde, i numeri sono per lo più corretti. È
pericoloso perché **non risponde in modo costante, e il silenzio è
indistinguibile da un risultato legittimo**.

L'evidenza più forte viene dal progetto stesso, non dalla letteratura: tre
esecuzioni dello screener **nello stesso giorno, sullo stesso universo**,
hanno prodotto 240, 174 e 65 candidati di Tier 1. Nessuna delle tre ha
segnalato un errore fatale. Tutte e tre hanno prodotto un briefing dall'aria
normale.

Un calo del 73% nella base analizzata che non lascia traccia nel risultato è
un rischio di natura diversa da un decimale sbagliato in un margine.

────────────────────────────────────────────────────────────────────────────
SEZIONE 1 — EVIDENZA DIRETTA DAL PROGETTO
────────────────────────────────────────────────────────────────────────────

1.1 VARIABILITÀ DELL'UNIVERSO (dato più critico)

  Run del 15 giugno 2026, stesso giorno, stesso comando:
    12:18  →  T1: 240 quality  |  T2: 0 catalyst
    15:59  →  T1: 174 quality  |  T2: 30 catalyst
    16:04  →  T1:  65 quality  |  T2: 0 catalyst

  Escursione: 240 → 65, pari al -73%. Nessun errore fatale sollevato.
  Il pipeline ha completato e pubblicato in tutti e tre i casi.

  IMPLICAZIONE: due briefing consecutivi non sono confrontabili tra loro, e
  non esiste modo di accorgersene leggendo il risultato. Una posizione può
  "sparire" dai candidati non perché sia peggiorata, ma perché quel giorno
  Yahoo non ha risposto.

1.2 TASSI DI ERRORE PER RUN (log 15 giugno, briefing Alex)

    HTTP 404 (simbolo non trovato)      185
    HTTP 500 (errore server)             15
    HTTP 401 (Invalid Crumb)             12+ (a raffica, poi sessione morta)
    "possibly delisted" / no earnings     8+
    Warning totali                       56

1.3 DECADIMENTO DELLA SESSIONE

  Osservato: dopo alcune centinaia di richieste la sessione decade con
  401 "Invalid Crumb". L'effetto concreto è stato l'arricchimento prezzi
  del portafoglio fallito su **20 titoli su 20** subito dopo lo screener,
  mentre lo stesso passaggio per il secondo utente — che riusava la cache
  ed apriva una sessione fresca — riusciva su 10 posizioni su 13.

  Mitigazione applicata: retry con backoff 5s/10s, concorrenza 8 → 4 thread.
  Riduce il sintomo, non elimina la causa.

1.4 COPERTURA GEOGRAFICA

  404 sistematici e riproducibili su: Filippine (.PSE), Indonesia (.JK),
  Dubai (.DU), Argentina (.BA), diverse linee Euronext, alcuni titoli
  scandinavi. Timezone e calendar mancanti su molti titoli asiatici.

  Non è casualità: sono mercati che Yahoo non copre o copre male. La
  decisione già presa di limitare i candidati ai mercati sviluppati rimuove
  gran parte di questa superficie di rischio.

1.5 DISCREPANZE DI PREZZO RILEVATE IN SESSIONE

  Confronto tra il broker dell'utente e i dati di mercato pubblici su due
  titoli in portafoglio ha mostrato scarti fino al 15% (Wolters Kluwer:
  71,98 sul broker contro 62,46 di mercato alla stessa data). La causa non è
  stata isolata — può essere linea di quotazione diversa, valuta, o
  schermata non aggiornata — ma il fatto che **non sia stato possibile
  dirimerla** è esso stesso il dato rilevante: senza una seconda fonte non
  c'è modo di sapere quale numero sia giusto.

────────────────────────────────────────────────────────────────────────────
SEZIONE 2 — TASSONOMIA DEL RISCHIO PER TIPO DI DATO
────────────────────────────────────────────────────────────────────────────

L'affidabilità non è uniforme. Trattare "yfinance" come un blocco unico è
l'errore da evitare: alcuni campi meritano [V], altri no.

  CLASSE A — AFFIDABILITÀ ALTA, tag [V] pienamente difendibile
    · Prezzi di chiusura e serie storiche, large e mid cap su NYSE, NASDAQ,
      LSE, Euronext, XETRA, TSE
    · Market cap, volumi
    · Dividendi dichiarati (importo e data) su mercati principali
    Rischio residuo: aggiustamenti per split e corporate action occasional-
    mente errati. È il difetto più citato in letteratura.

  CLASSE B — AFFIDABILITÀ MEDIA, [V] con riserva
    · Voci di conto economico e stato patrimoniale annuali (large cap)
    · Cash flow statement
    · Ratio derivati calcolati dal pipeline su quelle voci
    Rischio: normalizzazione dell'aggregatore non documentata — non è
    sempre chiaro se un valore sia GAAP o adjusted, continuing o total,
    reported o restated. La specifica MVF (Sez. 6-bis C) impone proprio
    questa normalizzazione prima di validare: qui non è verificabile.

  CLASSE C — AFFIDABILITÀ BASSA, il tag [V] NON è difendibile
    · Fondamentali di small e micro cap
    · Qualunque dato su mercati emergenti e frontier
    · Dati forward: earningsGrowth, forwardPE, target analisti
    · Serie storiche oltre 4-5 anni (buchi frequenti)
    · Dati trimestrali (i metodi relativi sono documentati come
      inaffidabili e talvolta restituiscono dataframe vuoti)

  CLASSE D — NON DISPONIBILE, nessun tag possibile
    · MOAT economico (peso 25/280) — dato Morningstar, a licenza
    · Same-store NOI, cap rate, AFFO normalizzato (REIT)
    · Non-accrual, first-lien, PIK (BDC); DCF/unit, coverage (MLP)
    · Guidance ufficiale, consensus multi-broker
    · Capital allocation qualitativa (gate G6)
    Sono esattamente le componenti che hanno motivato la scelta di NON
    implementare i motori REIT/BDC/MLP/preferred in regime S.

────────────────────────────────────────────────────────────────────────────
SEZIONE 3 — RISCHI SISTEMICI (indipendenti dal singolo dato)
────────────────────────────────────────────────────────────────────────────

  R1 — ENDPOINT NON UFFICIALI
       yfinance incapsula endpoint che Yahoo non documenta e non garantisce.
       Yahoo può modificarli senza preavviso; la libreria si rompe finché non
       esce una patch. Non esiste SLA né contratto di servizio.
       Probabilità: media. Impatto: pipeline ferma.

  R2 — RATE LIMITING SILENZIOSO
       Sotto carico gli errori non sono sempre eccezioni: possono essere
       risposte vuote. Un dato assente attraversa il pipeline come "metrica
       non disponibile" e non come "errore".
       Probabilità: alta (osservata). Impatto: erosione invisibile.

  R3 — DERIVA DELLA COMPARABILITÀ NEL TEMPO
       Conseguenza di R2 e del punto 1.1. Il confronto tra briefing di
       giorni diversi assume una base costante che di fatto non lo è.
       Probabilità: alta. Impatto: conclusioni errate sulle tendenze.

  R4 — ASSENZA DI PROVENIENZA
       yfinance non dichiara da quale filing provenga un valore né quando sia
       stato aggiornato. Il DIP della specifica non è implementabile in senso
       proprio: si può affermare che il dato è plausibile, non che sia
       tracciabile a una fonte primaria.
       Probabilità: certa. Impatto: limite strutturale sul Confidence Score.

────────────────────────────────────────────────────────────────────────────
SEZIONE 4 — COSA VALIDEREBBE DAVVERO
────────────────────────────────────────────────────────────────────────────

Il controllo incrociato è la strada giusta, ma il suo valore dipende molto da
quale seconda fonte si sceglie.

  4.1 SEC EDGAR — IMPLEMENTATO (edgar_client.py)
      Programmatico, gratuito, richiede solo uno User-Agent. XBRL è ground
      truth nel senso pieno della specifica: è il documento depositato.
      Copre US-listed, ADR e FPI (10-K, 20-F, 40-F).

      Implementazione:
        · ticker -> CIK da company_tickers.json (10.387 emittenti)
        · 14 concetti con fallback multipli per tassonomia ed emittente
        · selezione del fatto annuale: form annuale, periodo di ~12 mesi,
          deposito più recente (riflette i restatement)
        · confronto con le tolleranze di Sez. 6-bis C, tre esiti:
            agree      -> provenienza 21/25
            conflict   -> degradata a [U], 10/25
            not_covered-> resta [V], 18/25
        · budget di 60 lookup per run (EDGAR_MAX_LOOKUPS): i companyfacts
          grezzi pesano 1-20 MB e su CI il filesystem parte pulito
        · cache del solo estratto normalizzato: ~0,8 KB per emittente
          invece dei MB del file grezzo, persistita tra run via actions/cache

      NOTA SUL TAG RISULTANTE. Il riscontro EDGAR porta a [V] con conferma
      (21/25), non a [P] (25/25): il valore usato nel calcolo resta quello
      dell'aggregatore, EDGAR lo verifica soltanto. Per arrivare a [P]
      occorrerebbe sostituire i valori di calcolo con quelli XBRL — passo
      successivo, più invasivo, che riguarda soprattutto il progetto
      screener live.

  4.2 SECONDA FONTE COMMERCIALE — per il resto del mondo
      Financial Modeling Prep, EODHD, Twelve Data. Fascia di prezzo bassa,
      SLA reale, copertura europea decorosa. Serve per la parte non-US, dove
      EDGAR non arriva e dove non esiste un equivalente paneuropeo.

  4.3 CONTROLLI INTERNI A COSTO ZERO — da fare comunque
      Non richiedono una seconda fonte e intercettano gli errori grossolani:
        · quadratura: attivo = passivo + patrimonio netto
        · coerenza: FCF ≈ CFO − CapEx
        · continuità: variazioni anno su anno oltre il ±60% su ricavi o
          patrimonio segnalano restatement o errore di parsing
        · sanità: margini fuori da [-100%, +100%], payout negativo, P/E
          negativo trattato come valore valido
      Il modulo espone già il parametro `internal_coherence_ok` per questo.

  4.4 IL CONTROLLO PIÙ IMPORTANTE — copertura per run
      Registrare a ogni esecuzione: titoli richiesti, titoli con dati
      completi, titoli scartati e per quale motivo. Confrontare con la media
      mobile dei run precedenti e allertare oltre una soglia di scostamento.
      È ciò che avrebbe reso visibile il crollo 240 → 65.
      Costo: molto basso. Valore: intercetta il rischio dominante.

────────────────────────────────────────────────────────────────────────────
SEZIONE 5 — RACCOMANDAZIONE OPERATIVA
────────────────────────────────────────────────────────────────────────────

5.1 SUL TAG [V] — confermato, con perimetro esplicito

  [V] è difendibile per le classi A e B della Sezione 2: prezzi e
  fondamentali annuali di large e mid cap sui mercati sviluppati. È il
  perimetro in cui il pipeline già opera dopo la restrizione ai mercati
  sviluppati.

  NON è difendibile per le classi C e D. Il modulo deve poter degradare a
  [U] per singolo titolo quando la copertura è sotto soglia — non basta un
  tag globale deciso a priori.

  Implementazione attuale (mvf_valuation.py):
    PROVENANCE_CAP_V              18/25   yfinance senza riscontro
    PROVENANCE_CAP_V_CROSSCHECKED 21/25   con seconda fonte concorde
    PROVENANCE_CAP_U              10/25   riscontro discorde o dato sparso
    Gate CS: 50/100 di specifica riscalato sul massimo raggiungibile

  Nota sulla scelta del 18: una base interamente [V] senza alcun [P] cade
  nella fascia 60-79% del sub-score A della specifica (17-21). 18 è il
  valore basso della fascia, coerente con l'assenza di verifica incrociata.

5.2 STATO DEGLI INTERVENTI

  [FATTO] 1. Log di copertura per run con allerta            (§4.4)
             Soglia 40% sulla media mobile degli ultimi 10 run. Verificato
             sul caso reale: il crollo a 65 candidati produce un avviso
             esplicito che il briefing non è confrontabile con i precedenti.
  [FATTO] 2. SEC EDGAR per i titoli US                       (§4.1)
             edgar_client.py, integrato nello STEP 7 del pipeline.
  [APERTO] 3. Controlli di coerenza interna                  (§4.3)
             Il parametro internal_coherence_ok è già esposto da
             compute_confidence_score ma non è ancora alimentato: quadratura
             di bilancio, FCF ≈ CFO − CapEx, salti anno su anno oltre ±60%.
             Costo basso, nessuna dipendenza esterna.
  [APERTO] 4. Seconda fonte commerciale per il non-US        (§4.2)
             Rilevante solo se il perimetro resta ampio. Oggi i titoli
             europei del portafoglio restano [V] non verificati: EDGAR non
             li copre e non esiste un equivalente paneuropeo.

5.3 COSA NON FARE

  · Non trattare yfinance come fonte unica per dati mostrati a un cliente:
    vale per il progetto screener live, non per il briefing personale.
  · Non assumere che l'assenza di errori significhi completezza dei dati.
  · Non confrontare voti MVF tra run diversi senza verificare che la
    copertura dei dati sia comparabile.

────────────────────────────────────────────────────────────────────────────
CONCLUSIONE
────────────────────────────────────────────────────────────────────────────

Per un briefing personale su portafogli di grandi società quotate su mercati
sviluppati, yfinance è adeguato e [V] è una classificazione onesta.

Il limite da tenere presente non è la precisione del singolo numero: è che
la base su cui il numero viene calcolato varia da un giorno all'altro senza
dirlo. Finché il destinatario è chi ha scritto il sistema, è un rischio
gestibile. Quando i numeri finiscono davanti a un cliente — cioè nel
progetto screener live — quel rischio va chiuso prima, non dopo.

════════════════════════════════════════════════════════════════════════════
FONTI
════════════════════════════════════════════════════════════════════════════
- Log di produzione GitHub Actions, run 15 giugno 2026 (tre esecuzioni)
- Osservazioni dirette in sessione, giugno-agosto 2026
- yfinance Python Workflows: Data Quality & Trust — Quadratic
  https://www.quadratichq.com/blog/yfinance-python-workflows-ensure-data-quality-trust
- Data from yfinance — some Observations, Tobi Lux (Medium)
  https://medium.com/@Tobi_Lux/data-from-yfinance-some-observations-41e99d768069
- yfinance Library — A Complete Guide, AlgoTrading101
  https://algotrading101.com/learn/yfinance-guide/
- Yahoo Finance API: Complete Guide + Best Alternatives (2026), MarketXLS
  https://marketxls.com/blog/yahoo-finance-api-ultimate-guide
- Issues · ranaroussi/yfinance
  https://github.com/ranaroussi/yfinance/issues
════════════════════════════════════════════════════════════════════════════
