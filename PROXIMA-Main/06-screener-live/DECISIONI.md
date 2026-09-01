# Registro delle decisioni — Screener Live

Decisioni prese nelle sessioni di inquadramento (agosto 2026). Gli ID D1–D8
vengono dall'handoff; Q1–Q30 dalle due tornate di domande. Una decisione si
riapre solo esplicitamente, citando l'ID.

## Agenda D1–D8 dell'handoff

| ID | Questione | Esito |
|---|---|---|
| D1 | Semantica di "pacchetto" | Tag di idoneità multipli per titolo. I pacchetti sono modi di proporre portafogli (All, Etico/Green, Difensivo, Innovativo, Emergenti + PIR, Cedola mensile, Compounders) con incroci possibili. **Nessun voto al pacchetto**: lo screener restituisce titoli marcati "papabile per X, Y"; la composizione resta al consulente. Ogni pacchetto si declina in proporzioni azioni/obbligazioni/ETF/commodities per profilo investitore (griglie in calibrazione §11). |
| D2 | Ranking cross-classe | Superata dal D1: non si ordina il pacchetto, si ordina la lista candidati. Ordinamento primario IQI-S (/100, cross-classe), colonne sempre visibili: Voto MVF-S (confronto solo intra-classe), netto Italia per gli income. |
| D3 | MOAT | **Morningstar, non LLM** (preferenza esplicita per la validità storica del rating). Consultazione manuale via account IBKR (report Morningstar inclusi); inserimento nel DB tramite maschera dedicata, solo per la rosa (non per l'universo). Finché non inserito: metrica omessa + ri-basatura + flag "manca metrica importante". Verifica di automazione lecita via API IBKR → task posticipato. |
| D4 | Regola CS in Regime S | Il CS resta **affidabilità dei dati** come da spec (provenienza, completezza, puntualità, coerenza), calcolato sui tag [P]/[V]/[U] reali dello stack gratuito. La **copertura** delle metriche si mostra a parte, accanto al voto. Naming: `Voto MVF-S` (parziale, batch) vs `Voto MVF` (pieno, Regime A). Gate CS<50 invariato. |
| D5 | Perimetro universo | **MSCI World (23 mercati) + Corea del Sud + Taiwan + Cina solo ADR e H-share.** Niente A-share in v1. Niente altri emergenti. |
| D6 | Input cliente in sessione | Importo, profilo di rischio (questionario di adeguatezza), pacchetto/i, esclusioni, orizzonte. Griglie profilo×pacchetto in calibrazione §11. |
| D7 | Formato output | App con UI professionale + **PDF A4** da lasciare al cliente (contenuti fiscali per il commercialista + info utili a ribilanciamento/retention). Il PDF può fungere da relazione di adeguatezza MiFID (da verificare con l'assetto compliance). |
| D8 | Perimetro regolamentare | Strumento interno di supporto al consulente (SCF, art. 18-bis TUF): nessun banner. Si costruiscono di default: **log immutabile con snapshot dei dati** mostrati/raccomandati + tracciamento decisioni del cliente. |

## Decisioni della prima tornata (Q1–Q18)

| ID | Esito |
|---|---|
| Q1 | Scoring = **livello + trend + premio sovraperformance settoriale** (formula in calibrazione §1). |
| Q2 | Soglie ricostruite insieme, approvazione voce per voce (calibrazione §2–§6). |
| Q3 | → D5. |
| Q4 | Fonti: **stack gratuito quasi-definitivo** (v. sotto B) — EDGAR + EDINET + DART + MOPS + ESEF + fonti PDF ufficiali + yfinance per cross-validation. Provider a pagamento = task posticipato, non prerequisito. |
| Q5 | → D4. yfinance ammesso come fonte secondaria (non cattivo, ma incompleto); mai inventare, mai fonti inaffidabili. |
| Q6 | Metriche non reperibili: **omesse + ri-basatura** (mai punteggi inventati), con segnalazione esplicita quando manca una metrica importante. |
| Q7 | → D3. |
| Q8 | Peer group: **mediana settore/industria costruita automaticamente in-universo**. |
| Q9 | → D1. |
| Q10 | Verificato IBKR (advisor structure e white branding gratuiti; commissioni ~0,05% min €1,25–4 EU, $1 US; frazioni solo su large cap). Taglio minimo per titolo singolo ~€800–1.000; sotto si diversifica con ETF. Il programma mostra l'**impatto commissionale stimato** di ogni portafoglio proposto. |
| Q11 | ETF: dentro, ma **modulo posticipato** — le regole di valutazione arriveranno a parte (task). Vincolo già fissato: universo ETF = solo **UCITS** (PRIIPs: il retail UE non può comprare ETF domiciliati USA). |
| Q12 | Classi: tutte e 5 (common, REIT, BDC, MLP, preferred), con l'attrito fiscale bene in vista per BDC/MLP. |
| Q13 | → D1/D2. |
| Q14 | Ribilanciamento: il programma **segnala, non decide**. Briefing giornaliero automatizzato sui titoli posseduti dai clienti (catalogo alert in calibrazione §12). |
| Q15 | Carichi medi: **automatizzati via IBKR Flex Query** (posizioni + prezzo medio di tutti i conti collegati alla struttura advisor). Interim: import CSV. |
| Q16 | Deployment: **web app su VPS europeo** (batch cron + DB + API + UI con login), multi-postazione, dati in UE, portafogli clienti fuori da GitHub. |
| Q17 | → D7. |
| Q18 | → D8. |

## Decisioni della seconda tornata (Q19–Q30)

| ID | Esito |
|---|---|
| Q19 | "Emergenti" = **geografico**: i titoli dei mercati classificati emergenti da MSCI presenti nel nostro universo (Cina ADR/H-share, Corea, Taiwan). |
| Q20 | Cina: **solo ADR + H-share**. |
| Q21 | ESG: punteggio **letto da IBKR** (fonte considerata affidabile), inserito manualmente per la shortlist del pacchetto Etico dopo un pre-filtro calcolato (esclusioni settoriali). Automazione lecita da verificare → task. |
| Q22 | Obbligazioni e commodities: profondità massima voluta → **screener dedicati da costruire a parte** e innestare dopo, come l'MVF → task posticipati con reminder. |
| Q23 | → D3 (Morningstar via IBKR, flusso semi-automatico sulla rosa). |
| Q24 | Griglie profilo×pacchetto: le disegna Claude e le approva il committente (calibrazione §11). |
| Q25 | Pacchetti aggiuntivi attivati: **PIR, Cedola mensile, Compounders**. (Value contrarian, Beni reali, Liquidità: non attivati per ora.) |
| Q26 | → Q11/Q22 (modulo ETF posticipato con reminder). |
| Q27 | Catalogo alert approvato integralmente. Canale: **stesso veicolo del briefing mattutino** con maschera/canale dedicato — accanto ad A (Alex) e V (Vale) nasce **Proxima** (funzionalità aziendali: clienti, report, briefing mirato, documentale, workflow vigilanza). ⚠ Nota: i dati clienti non possono stare su GitHub Pages pubblico → il canale Proxima vive sulla web app con login (Q16); il briefing personale resta dov'è. |
| Q28 | Confermato: portafogli clienti fuori dal repo (GDPR/segreto professionale), regime fiscale di default **dichiarativo** se conto IBKR (IBKR Irlanda non è sostituto d'imposta), parametrizzabile per cliente. |
| Q29 | Confermato deployment Q16. |
| Q30 | **Banco di prova** — qualità indiscutibile: KO, JNJ, ENI.MI, MO, MCD, FRT (REIT), TGT, WMT, SPGI. Scarti esemplificativi: SPCE, LULU. Principio dichiarato: nessuna esclusione a prescindere, la tossicità emerge dai dati (iper-indebitamento, assenza di vantaggio economico, gestione per il tornaconto del management). |

## Nota B — filosofia fonti dati (fissata)

Includere **da subito** tutto ciò che è gratuito e strutturato, includendo
anche le fonti solo-PDF; i dati solo annuali si trattano come **attendibili ma
meno profondi** (la minore profondità pesa sul sub-score di completezza del
CS, non sulla provenienza). La soluzione è **quasi-definitiva**: il CS non
deve "salire nel tempo" per aggiunte incrementali — cambierà solo se/quando
si adotterà un provider a pagamento o un'altra soluzione (task posticipato).
