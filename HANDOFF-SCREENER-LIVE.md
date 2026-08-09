════════════════════════════════════════════════════════════════════════════
ISTRUZIONI DI INQUADRAMENTO — SCREENER LIVE PER CONSULENZA
════════════════════════════════════════════════════════════════════════════

Motore di valutazione: MVF v4.0 (documento separato — AUTOREVOLE)
Programma sorgente:    Proxima Briefing Pipeline (esistente, in produzione)
Programma target:      screener massivo interattivo per sessione con cliente
Versione handoff:      1.1 — allineata a MVF v4.0

STATO: inquadramento. Nessuna decisione architetturale presa.
       Le questioni aperte (Sez. 9) sono AGENDA, non blocchi: ognuna ha un
       ID, un impatto dichiarato e le sue dipendenze, ed è risolvibile
       indipendentemente dalle altre nell'ordine che si preferisce.

────────────────────────────────────────────────────────────────────────────
GERARCHIA DOCUMENTALE (ordine di lettura e di autorità)
────────────────────────────────────────────────────────────────────────────
  1. MVF v4.0 — istruzioni operative del modello di valutazione.
     File: rassegna-stampa/docs-mvf/MVF_v4.0_istruzioni_operative.md
     È la FONTE AUTOREVOLE. In caso di conflitto con questo handoff,
     prevale la specifica MVF.
  2. Questo documento — inquadramento del progetto, tassonomia di
     implementabilità, agenda decisionale. Sintesi orientata al codice,
     NON un sostituto della specifica.
  3. Codice esistente (repo Main-Proxima) — riferimento implementativo.
     Implementa MVF v3.0: superato, utile solo come base infrastrutturale.

────────────────────────────────────────────────────────────────────────────
NAMING-GUARD
────────────────────────────────────────────────────────────────────────────
  · "screener" senza qualificazione = il modulo esistente screener.py,
    batch notturno del briefing. Il programma nuovo è "screener live".
  · "MVF" senza numero di versione = v4.0. La v3.0 va sempre qualificata.
  · "Voto MVF" = punteggio /1000 su base per classe. "IQI" = /100.
    "CS" = Confidence Score /100. Tre grandezze distinte, non sinonimi.
  · "pacchetto" = raggruppamento di titoli proposto al cliente. Semantica
    non ancora definita → D1.
  · "briefing" = il programma esistente. Fuori perimetro salvo riuso
    infrastrutturale.

────────────────────────────────────────────────────────────────────────────
NOTA DI VERSIONAMENTO DELLA SPECIFICA
────────────────────────────────────────────────────────────────────────────
  Il file consegnato si chiama MVF_V41.MD, ma intestazione, changelog e
  piè di pagina dichiarano v4.0 in ogni occorrenza; l'ultimo changelog è
  "v4.0 rispetto a v3.6". Trattare il contenuto come v4.0. Se esiste un
  delta v4.1, non è in questo file → allineare il naming prima di
  storicizzare qualsiasi output (Sez. 8).


════════════════════════════════════════════════════════════════════════════
SEZIONE 1 — IDENTITÀ DEL PROGETTO
════════════════════════════════════════════════════════════════════════════

A. COSA DEVE FARE
   Screener massivo che, su richiesta e in tempo reale, restituisce pool di
   titoli conformi a criteri derivati da MVF v4.0, organizzati in pacchetti.

B. CONTESTO D'USO (determina tutto il resto)
   Consulenza finanziaria IN PRESENZA. Il consulente è seduto davanti al
   cliente; il cliente esprime vincoli e preferenze; il portafoglio si
   costruisce sul momento anziché essere delegato a lavorazione differita.

C. IMPLICAZIONI NON NEGOZIABILI DEL CONTESTO
   · Latenza percepita in secondi, non minuti.
   · I dati mancanti sono VISIBILI al cliente: la degradazione silenziosa
     accettabile in un batch notturno qui costa credibilità.
   · Un voto va accompagnato dal suo grado di affidabilità, altrimenti
     l'output è una asserzione non sostenibile davanti a chi decide.
   · L'output è materiale di consulenza → il perimetro regolamentare
     precede la costruzione, non la segue (D8).

D. COSA NON È
   · Non è il briefing con un'altra interfaccia: il briefing è narrativo,
     batch, non presidiato, mono-utente. Questo è interrogativo,
     interattivo, presidiato, per terzi.
   · Non è una reimplementazione integrale di MVF v4.0 su tutto l'universo:
     v. Sez. 2 e Sez. 4 per il motivo.


════════════════════════════════════════════════════════════════════════════
SEZIONE 2 — ARCHITETTURA: I DUE REGIMI
════════════════════════════════════════════════════════════════════════════

Il progetto ha una discontinuità strutturale rispetto al programma esistente
e una rispetto alla specifica MVF. Entrambe si risolvono con la stessa mossa:
separare due regimi di esecuzione.

──────────────────────────────────────────────────────────────────────────
A. DISCONTINUITÀ 1 — TEMPORALE (vs programma esistente)
──────────────────────────────────────────────────────────────────────────
  Lo screener esistente impiega 5-45 minuti su 500-600 titoli, scaricando
  bilanci uno alla volta. In sessione con cliente è inutilizzabile.

                      BRIEFING (esistente)     SCREENER LIVE (target)
    Esecuzione        notte, non presidiata    su richiesta, presidiata
    Latenza tollerata 45 minuti                secondi
    Dato mancante     degrada in silenzio      il cliente lo vede
    Modello di calcolo on-demand               pre-computazione + query

  → Il calcolo MVF NON può avvenire alla richiesta. Deve essere
    pre-computato in batch e persistito; la sessione interroga e filtra.
    Solo i prezzi correnti si aggiornano dal vivo, e solo per i titoli
    effettivamente a schermo.

──────────────────────────────────────────────────────────────────────────
B. DISCONTINUITÀ 2 — DI REPERIBILITÀ (vs specifica MVF)
──────────────────────────────────────────────────────────────────────────
  MVF v4.0 è redatta come procedura di analisi su UN titolo, con ricerca
  documentale (SEC EDGAR, IR, supplement, Morningstar, consensus broker).
  Non è un algoritmo deterministico su migliaia di titoli. Alcune sue
  componenti non esistono in forma strutturata a nessun prezzo ragionevole
  su scala di universo (Sez. 4).

  → Il voto MVF v4.0 integrale è ottenibile su POCHI titoli, non su tutti.

──────────────────────────────────────────────────────────────────────────
C. RISOLUZIONE — DUE REGIMI, DUE STATUS DICHIARATI
──────────────────────────────────────────────────────────────────────────

  REGIME S — SCREENING (batch, automatico, universo ampio)
    Input:   dati strutturati da API + fonti programmatiche (EDGAR XBRL).
    Calcola: il sottoinsieme di MVF v4.0 derivabile da bilancio (Sez. 4,
             classe R1), i gate calcolabili, un IQI parziale.
    Produce: un punteggio DICHIARATO COME PARZIALE, mai spacciato per
             Voto MVF pieno. Naming da fissare in D4.
    Ruolo:   SELEZIONA. Riduce l'universo a una rosa.

  REGIME A — ANALISI COMPLETA (on-demand, pochi titoli)
    Input:   regime S + ricerca documentale, eventualmente assistita da LLM.
    Calcola: MVF v4.0 integrale — Voto /1000, IQI, CS con tagging DIP,
             gate, MoS, prezzo ideale, scheda A4 (MVF Sez. 11D).
    Ruolo:   GIUSTIFICA. È ciò che si mostra e si difende davanti al
             cliente e ciò che regge una raccomandazione.

  REGOLA TRASVERSALE: i due regimi non si mescolano nell'interfaccia.
  Un titolo in regime S e uno in regime A non hanno lo stesso status
  epistemico; renderli visivamente identici davanti a un cliente è
  fuorviante. La distinzione va portata nel modello dati, non solo nella UI.

──────────────────────────────────────────────────────────────────────────
D. FLUSSO CONSEGUENTE
──────────────────────────────────────────────────────────────────────────
    BATCH (notturno o settimanale, non presidiato)
      universe → fetch → [DIP tagging] → MVF-S → IQI-S → CS-S → gate
                                                    ↓
                                              DATABASE persistito

    LIVE (in sessione, millisecondi)
      UI → query → filtri di pacchetto → rosa
                                          ↓
                          [su richiesta] REGIME A su singolo titolo


════════════════════════════════════════════════════════════════════════════
SEZIONE 3 — DISTANZA v3.0 (CODICE) → v4.0 (SPECIFICA)
════════════════════════════════════════════════════════════════════════════

Il codice in mvf_valuation.py implementa la v3.0. Non è un aggiornamento di
pesi: è cambiata l'architettura concettuale. Va riscritto, non ritoccato.

  DIMENSIONE            v3.0 (implementata)    v4.0 (specifica)
  ──────────────────────────────────────────────────────────────────────
  Base di calcolo       257, unica             5 basi per classe
  Scala Voto            0-100                  0-1000
  Classi strumento      1                      5 + STEP 0 di routing
  Margine di sicurezza  dal fair value         da IQI + overlay CS
  IQI                   assente                0-100, guida il MoS
  Qualità dei dati      assente                DIP, tagging [P]/[V]/[U]
  Esclusioni            6 hard filter          6 gate G1-G6 + red flag
  Fiscalità             assente                netto ITALIA obbligatorio
  Return attribution    assente                obbligatoria 1y e 5y

  BASI PER CLASSE (MVF Sez. 2 STEP 0):
    common 280 · REIT 370 · BDC 299 · MLP 309 · preferred 168 (MVF-P)
    Voto = (punteggio grezzo / BASE) × 1000

  ► VINCOLO DERIVATO — NON CONFRONTABILITÀ TRA CLASSI (MVF Sez. 11F)
    I Voti MVF sono confrontabili solo intra-classe e intra-versione. Un
    pacchetto income che mescola common, REIT, BDC, MLP e preferred — cioè
    esattamente gli strumenti da rendita — NON può essere ordinato per Voto
    MVF. Serve un criterio di ranking cross-classe → D2.

  METRICHE NUOVE O RIBILANCIATE NEL MOTORE COMMON (base 280 invariata):
    · FCF per Share Growth        peso 18   NUOVA
    · EPS Growth                  18 → 10
    · FCF Margin                  22 → 12
    · Multiple Expansion (Δ P/E)  peso  5   NUOVA
    Ognuna porta un guard anti-manipolazione (anti-diluizione da buyback,
    value-trap guard): v. MVF Sez. 3 B-bis per bande e cap.

  CLAUSOLE DI REDISTRIBUZIONE (MVF Sez. 3 E, F):
    · Senza dividendo: i 36 punti dividendo → FCF Margin 12→22,
      Buyback 5→15, Price CAGR 5→13, ROIC 15→23.
    · Con dividendo E DDM applicato: pesi dividendo dimezzati (16→8, 10→5,
      10→5); i 18 punti → FCF Margin 12→22, Net Margin 18→26.
    Il regime va SEMPRE dichiarato in output.

  PENALITÀ ALTMAN-Z, additiva sul Voto normalizzato (MVF Sez. 3 D):
    zona grigia 1,23-1,80 → −10% · sotto 1,23 → −20%.
    Esenti: banche, assicurazioni, REIT, utility regolate, asset-light.


════════════════════════════════════════════════════════════════════════════
SEZIONE 4 — TASSONOMIA DELLE METRICHE PER REPERIBILITÀ
════════════════════════════════════════════════════════════════════════════

Classificazione operativa delle componenti MVF v4.0 secondo la fonte
necessaria. Determina cosa entra nel Regime S e cosa resta al Regime A.
È il documento da consultare quando si decide l'ambito di una sprint.

──────────────────────────────────────────────────────────────────────────
R1 — DERIVABILE DA DATI STRUTTURATI (entra nel Regime S)
──────────────────────────────────────────────────────────────────────────
  Tutte le metriche di margine, redditività, leva, cassa: gross/EBITDA/
  operating/net/FCF margin, ROIC, ROE, ROA, D/E, D/A, Altman-Z, SBC/Rev,
  CapEx/Rev, CapEx/D&A, R&D/Rev, tax rate, accruals, CCR.
  Dividendi: yield, payout, dividend growth CAGR, buyback yield.
  Prezzo: price CAGR, Δ P/E, movimenti 1m/6m/1y/5y, return attribution
  (identità Prezzo = EPS × P/E: entrambi i termini sono disponibili).
  Crescita per azione: EPS growth e FCF/share growth, inclusi i guard
  anti-diluizione (richiedono la serie dello share count — disponibile).
  Gate: G1, G2, G3, G4, G5 sono derivabili da bilancio.

──────────────────────────────────────────────────────────────────────────
R2 — RICHIEDE FONTE PROGRAMMATICA DEDICATA (fattibile, ha un costo)
──────────────────────────────────────────────────────────────────────────
  · DIP tagging [P]/[V]/[U] — SEC EDGAR è programmatico e gratuito (solo
    User-Agent): company_tickers.json, submissions, companyfacts,
    companyconcept, frames. XBRL come ground truth per US-listed/ADR/FPI.
    Fuori dal perimetro SEC (EU, JP, CN/HK) non esiste equivalente
    paneuropeo → il tagging degrada a [V] o [U] per costruzione.
  · Insider trading (peso 5) — Form 4 via EDGAR, automatizzabile.
  · Auditor change, CFO turnover — 8-K e DEF 14A, full-text search EDGAR.

──────────────────────────────────────────────────────────────────────────
R3 — PROPRIETARIO O DOCUMENTALE (non entra nel Regime S senza decisione)
──────────────────────────────────────────────────────────────────────────
  · MOAT economico, peso 25 su 280 (~9% del Voto) — la specifica impone
    "solo Morningstar": dato a licenza. → D3
  · Same-store NOI, cap rate, accretion spread (REIT) — supplement IR in
    PDF, non standardizzati.
  · AFFO — non-GAAP, definizione variabile per emittente; la specifica
    stessa (Sez. 6-bis G) impone normalizzazione prima di qualsiasi
    confronto cross-REIT, pena tag [U].
  · B1 / B4 forward — richiedono guidance ufficiale [G] o consensus
    multi-broker [C]; in loro assenza sono [S] e fanno scattare il cap.
  · Capital allocation e G6 — giudizio qualitativo su M&A distruttivi,
    svalutazioni goodwill ricorrenti, rating Morningstar.
  · Metriche dedicate BDC/MLP (non-accrual, first-lien, PIK, coverage,
    concentrazione sponsor, contratti in scadenza) — filing e IR.

──────────────────────────────────────────────────────────────────────────
CONSEGUENZA STRUTTURALE SUL CONFIDENCE SCORE
──────────────────────────────────────────────────────────────────────────
  Il CS v4.0 è calcolato oggettivamente dalla quota di dati [P], pesata per
  il peso delle metriche. In Regime S, con dati da aggregatore singolo, la
  specifica impone il tag [U]: il CS risultante è strutturalmente basso e
  il gate CS < 50 escluderebbe quasi l'intero universo.

  Non è un difetto della specifica: è il suo funzionamento corretto
  applicato a un regime per cui non era pensata. Serve una regola esplicita
  di CS per il Regime S, distinta da quella del Regime A → D4.


════════════════════════════════════════════════════════════════════════════
SEZIONE 5 — VINCOLI STRUTTURALI DA PORTARE NEL DESIGN
════════════════════════════════════════════════════════════════════════════

Elementi della specifica che hanno effetto diretto sull'architettura, da
tenere presenti fin dallo schema dati e non da aggiungere dopo.

  V1 — ROUTING PRIMA DEL CALCOLO (MVF Sez. 2 STEP 0)
       La classe di strumento determina base, metriche, pesi dei modelli,
       gate applicabili e ritenuta fiscale. Va risolta all'ingresso della
       pipeline, non a valle. Il campo "classe" è chiave primaria logica
       tanto quanto il ticker.

  V2 — NON CONFRONTABILITÀ DEI VOTI (MVF Sez. 11F)
       V. Sez. 3. Vincola qualsiasi ordinamento di pacchetto misto → D2.

  V3 — TRE GRANDEZZE INDIPENDENTI
       Voto MVF (qualità azienda) · IQI (qualità investimento) · CS
       (qualità dati). Non sono riducibili l'una all'altra e la specifica
       impone di mostrarle tutte. La riconciliazione MVF↔IQI (Δ = Voto/10 −
       IQI) è essa stessa un segnale: Δ > +20 = qualità cara → watchlist;
       Δ < −20 = sospetto value trap → scrutinio rinforzato.

  V4 — CATENA DEL MARGINE DI SICUREZZA
       MoS_finale = MoS_base(IQI) + overlay(CS), con cap 60% e astensione
       sotto IQI 30. Il prezzo ideale NON è una proprietà del titolo: è una
       funzione di due indici derivati. Modellarlo come campo calcolato,
       non come dato.

  V5 — GATE ≠ RED FLAG
       I gate G1-G6 escludono strutturalmente a prescindere da prezzo, MoS
       e IQI. I red flag segnalano senza bloccare. Due tabelle distinte,
       due comportamenti distinti nell'interfaccia. Regola trasversale
       della specifica: conferma multi-segnale, nessun segnale isolato con
       storia di falsi positivi esclude da solo.

  V6 — IL CONFRONTO SI FA SUL NETTO ITALIA (MVF Sez. 7)
       Obbligatorio per ogni titolo che distribuisce. La ritenuta alla
       fonte cambia l'ordinamento: REIT USA fino al 30%, MLP fino a ~37%
       (IRC §1446), BDC spesso 30% — contro il 15% standard con W-8BEN.
       Un pacchetto income ordinato per yield lordo mostra una classifica
       sbagliata a un cliente italiano. Questa regola nasce per l'analisi
       ma descrive esattamente il caso d'uso di questo progetto.
       Netto ITALIA = Yield_lordo × (1 − w_home) × (1 − 0,26)

  V7 — SEGMENTAZIONE GIÀ PRESENTE NELLA SPECIFICA
       I tier dividendo del Blocco B (forte ≥10y / solido 5-9y / nascente
       <3y / no-div con buyback / nessuna remunerazione) sono già una
       tassonomia di profilo di remunerazione, con pesi B1/B2 diversi per
       tier. È il candidato naturale come ossatura dei pacchetti income
       → confluisce in D1.


════════════════════════════════════════════════════════════════════════════
SEZIONE 6 — PATRIMONIO RIUTILIZZABILE DAL PROGRAMMA ESISTENTE
════════════════════════════════════════════════════════════════════════════

Repo: BigFatNeko/Main-Proxima, branch claude/financial-briefing-pipeline-aVCmh
Directory: rassegna-stampa/

  FILE                          RIGHE   DESTINO
  ────────────────────────────────────────────────────────────────────────
  screener.py                   2.492   RIUSO PARZIALE (infrastruttura)
  mvf_valuation.py                729   RISCRIVERE (implementa v3.0)
  briefing_pipeline.py            847   IGNORARE (layer briefing)
  filiere_screener.py             365   RIUSO EVENTUALE (tassonomia settori)
  docs-mvf/MVF_v4.0_...md       1.212   SPECIFICA — leggere per primo

A. DA RIUSARE — è infrastruttura, non logica di valutazione
   · screener.py righe 65-360: CONFIG, TV_MARKETS (5 macro-aree, ~45
     mercati), TV_TO_YF_SUFFIX (mappatura ticker TradingView → yfinance),
     data class Candidate/IntrinsicMetrics.
   · Universe building via tradingview-screener, fallback finvizfinance US.
   · Fetch parallelo, gestione sessione, retry con backoff.
   · Calcolo delle metriche di bilancio grezze (classe R1 della Sez. 4).
   · FILIERE_STRATEGIC: mappatura industria → 15 filiere tematiche.

B. DA CONSULTARE COME RIFERIMENTO, NON DA COPIARE
   · screener.py righe 880-1210: hard/soft filter e composite score v3.0.
     Mostrano cosa è già automatizzato e con quali soglie; i gate v4.0
     sono più severi e strutturati diversamente.
   · mvf_valuation.py: i cinque modelli di valutazione e il WACC via CAPM
     esteso (Rf + β×ERP + CRP) sono concettualmente invariati in v4.0;
     cambiano i pesi per classe. Le tabelle Rf/ERP/CRP per mercato sono
     riusabili previo aggiornamento Damodaran.

C. DA IGNORARE
   Chiamata Claude, template Jinja2, system prompt, modalità giornaliere,
   personalizzazione utente, workflow GitHub Actions.


════════════════════════════════════════════════════════════════════════════
SEZIONE 7 — VINCOLI TECNICI NOTI (esperienza diretta sul programma esistente)
════════════════════════════════════════════════════════════════════════════

A. YAHOO FINANCE / yfinance
   · Rate limiting aggressivo: dopo alcune centinaia di richieste la
     sessione decade con 401 "Invalid Crumb". Sintomo osservato in
     produzione: arricchimento prezzi fallito su 20 titoli su 20 subito
     dopo un run completo dello screener. Mitigazione applicata: retry con
     backoff 5s/10s, concorrenza ridotta da 8 a 4 thread.
   · 404 sistematici: Filippine (.PSE), Indonesia (.JK), Dubai (.DU),
     Argentina (.BA), alcune linee Euronext.
   · 500 sporadici lato server, transitori.
   · Timezone/calendar mancanti su molti titoli asiatici.
   → Per uso davanti a cliente: valutare provider con SLA almeno per i
     prezzi live. Per i fondamentali US il DIP spinge comunque su EDGAR,
     che è gratuito e stabile.

B. AMBIENTE DI ESECUZIONE
   Il programma esistente gira su GitHub Actions (ubuntu-latest, timeout
   130 min, Python 3.11). NON adatto a richieste interattive: serve
   esecuzione locale o servizio sempre attivo.

C. COSTI LLM (se il Regime A è assistito)
   Riferimento dal briefing: claude-opus-4-6, max_tokens 24.000, prompt
   caching attivo → ~1,00-1,05 $ per generazione. Con max_tokens elevati
   la SDK Anthropic IMPONE lo streaming (messages.stream() +
   get_final_message()); messages.create() solleva ValueError.
   Il Regime S è deterministico e non ha costo LLM.

D. DIPENDENZE ATTUALI
   tradingview-screener>=2.5.0,<3.0 · finvizfinance>=1.0,<2.0
   yfinance>=0.2.40,<0.3 · pandas>=2.0,<3.0 · numpy>=1.24,<3.0
   anthropic>=0.69,<1.0 · jinja2>=3.1,<4.0 · markdown>=3.5,<4.0
   requests>=2.31,<3.0


════════════════════════════════════════════════════════════════════════════
SEZIONE 8 — VERSIONAMENTO E TRACCIABILITÀ
════════════════════════════════════════════════════════════════════════════

La specifica MVF ha una sezione dedicata (11F) che il nuovo programma deve
rispettare, perché produce output mostrati a terzi e potenzialmente
riesaminati nel tempo.

  · IDENTITÀ DI UN OUTPUT: ticker + data + versione MVF + classe/base.
  · Confrontabilità: solo a parità di versione E di base.
  · Storico delle basi: 257 (v3.0) → 280 (v3.1+). Scala Voto: /100 fino a
    v3.4, /1000 da v3.5. REIT: base 280 → 370 in v3.6, non confrontabile
    con REIT ≤ v3.5 senza ricalcolo.
  · v4.0 aggiunge BDC/MLP/preferred con basi proprie: i Voti non sono
    confrontabili TRA classi in nessun caso.
  · Il regime dei pesi applicato (senza dividendo / DDM attivo) va
    dichiarato nell'output, perché cambia la composizione del punteggio.

  → Per il programma nuovo: ogni riga persistita in DB porta versione
    MVF, classe, base, regime pesi, e — nuovo rispetto alla specifica —
    il REGIME DI ESECUZIONE (S o A, Sez. 2C). Senza quest'ultimo campo i
    due regimi diventano indistinguibili a valle.


════════════════════════════════════════════════════════════════════════════
SEZIONE 9 — AGENDA DELLE DECISIONI APERTE
════════════════════════════════════════════════════════════════════════════

Ogni voce è indipendente e risolvibile separatamente. ID stabile per
riferimento nelle sessioni successive. "Blocca" indica cosa non può essere
implementato finché la decisione non è presa.

  D1 — SEMANTICA DI "PACCHETTO"
       Domanda: lista di candidati o allocazione completa con pesi?
       Letture possibili: per obiettivo (income / dividend growth /
       crescita / difensivo / speculativo) · per profilo di rischio · per
       orizzonte · per filiera (15 già mappate) · portafogli
       pre-confezionati con pesi.
       Nota: la formulazione del committente ("il cliente vuole vedere la
       creazione del portafoglio lì sul posto") propende per l'ultima.
       Materiale disponibile: tier dividendo Blocco B (V7), tag income/
       quality v3.0, FILIERE_STRATEGIC.
       Blocca: schema dati, modello di output, UI.

  D2 — RANKING CROSS-CLASSE
       Domanda: su cosa si ordina un pacchetto che mescola classi, dato
       che i Voti MVF non sono confrontabili (V2)?
       Candidati: IQI (sempre /100, cross-classe per costruzione) ·
       rendimento netto ITALIA (V6, per pacchetti income) · MoS finale ·
       oppure separazione dei pacchetti per classe.
       Blocca: logica di ordinamento, presentazione dei risultati.
       Dipende da: D1.

  D3 — MOAT (peso 25/280)
       Domanda: licenza Morningstar, proxy calcolato, o Voto dichiarato
       parziale in Regime S?
       Nota: la specifica dice "solo Morningstar" — un proxy va comunque
       dichiarato come deviazione dalla specifica, non silenziato.
       Blocca: completezza del Voto in Regime S, Blocco A4 dell'IQI.

  D4 — REGOLA CS IN REGIME S
       Domanda: quale soglia sostituisce il gate CS < 50 quando i dati
       sono [U] per costruzione (Sez. 4)? E come si chiama il punteggio
       parziale, per non confonderlo con il Voto MVF pieno?
       Blocca: qualunque filtro di qualità in batch; naming dell'output.

  D5 — PERIMETRO DELL'UNIVERSO
       Domanda: copertura globale come oggi (~45 mercati) o solo mercati
       sviluppati?
       Elementi: i 404 sistematici (Sez. 7A) sono tollerabili in batch
       notturno, molto meno davanti a un cliente; MSCI World / FTSE
       Developed come perimetro già usato nel briefing per un vincolo
       analogo.
       Blocca: universe building, dimensionamento del batch.

  D6 — INPUT DEL CLIENTE IN SESSIONE
       Domanda: cosa può impostare il cliente? Importo, orizzonte,
       profilo di rischio, settori da escludere, valuta di riferimento,
       vincoli fiscali (residenza → V6).
       Blocca: UI, parametrizzazione delle query.
       Dipende da: D1.

  D7 — FORMATO DI OUTPUT
       Domanda: schermo condiviso, PDF stampabile, entrambi?
       Nota: la specifica ha già una scheda riassuntiva A4 (MVF Sez. 11D)
       con 11 campi definiti — è un formato di output pronto per il
       Regime A.
       Blocca: layer di presentazione.

  D8 — PERIMETRO REGOLAMENTARE
       Domanda: l'output costituisce raccomandazione personalizzata? Con
       quale abilitazione viene erogato?
       Nota: nel progetto esistente è già emerso il tema SCF come
       prerequisito. Da verificare PRIMA della costruzione: incide su cosa
       il programma può mostrare, con quali avvertenze, e su cosa va
       tracciato.
       Blocca: nulla tecnicamente, tutto sostanzialmente.


════════════════════════════════════════════════════════════════════════════
FINE ISTRUZIONI DI INQUADRAMENTO
════════════════════════════════════════════════════════════════════════════
Specifica autorevole: rassegna-stampa/docs-mvf/MVF_v4.0_istruzioni_operative.md
Due regimi (Sez. 2C): S = seleziona, dichiarato parziale | A = giustifica
Vincoli da portare nello schema dati: V1 routing · V2 non confrontabilità ·
V3 tre grandezze · V4 catena MoS · V5 gate≠red flag · V6 netto Italia
Agenda decisionale: D1-D8 (Sez. 9), indipendenti, ID stabili
════════════════════════════════════════════════════════════════════════════
