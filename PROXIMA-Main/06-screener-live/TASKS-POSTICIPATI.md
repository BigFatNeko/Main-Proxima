# Tasks posticipati — Screener Live

Richiesta esplicita (Q22): reminder dei lavori rimandati consapevolmente,
da riprendere **a conclusione dei lavori** sullo screener azionario v1.
Ogni task ha un ID stabile; quando si apre, si cita l'ID.

## Moduli di valutazione da costruire a parte (profondità massima)

| ID | Task | Note |
|---|---|---|
| T1 | **Modulo ETF** | In attesa delle regole di valutazione dal committente (Q11/Q26: "te le incollo"). Vincolo già fissato: universo solo **UCITS** (PRIIPs — il retail UE non può comprare ETF domiciliati USA). Serve per: sleeve core dei portafogli piccoli, sleeve obbligazionario/reali provvisori. Nel frattempo: whitelist provvisoria minima approvata a mano (§11 calibrazione). |
| T2 | **Screener obbligazionario** | Profondità massima voluta (Q22): govies + corporate. Costruire come motore autonomo (stile MVF) e innestare. Priorità italiana: BOT/BTP (tassazione 12,5%), MOT. |
| T3 | **Screener commodities** | Profondità massima voluta (Q22). ETC UCITS + eventuale analisi produttori (già coperti dal motore azionario). |

## Dati e integrazioni

| ID | Task | Note |
|---|---|---|
| T4 | **Provider dati a pagamento** | Rivalutare quando: servono trimestrali EU strutturate, ESG programmatico, SLA prezzi live in sessione. Candidati visti: FMP, EODHD (~€50–100/mese). La decisione cambia i tag DIP → dichiarare il cambio di fonte nello storico (spec 11F). |
| T5 | **Verifica API IBKR** | Cosa espongono lecitamente TWS API / Web API: fondamentali di terze parti, ESG, Morningstar? Se sì → automazione del flusso §7; se no → resta il flusso manuale assistito sulla rosa. Da fare in fase di build, con i ToS alla mano. |
| T6 | **IBKR Flex Query** | Implementare l'aggancio posizioni + prezzi medi di carico dei conti clienti (Q15/Q28) appena esiste la struttura advisor operativa. Interim: import CSV. |
| T7 | **Consensus forward migliore** | B1/B4 oggi da yfinance ([C] se ≥3 stime, altrimenti [S] con cap 50%). Con provider a pagamento → consensus multi-broker vero. |

## Prodotto e canali

| ID | Task | Note |
|---|---|---|
| T8 | **Canale "Proxima"** nel veicolo del briefing | Accanto ad A (Alex) e V (Vale): clienti, report, briefing mirato, gestionale documentale, workflow e reportistica per gli istituti di vigilanza (Q27). ⚠ Dati clienti mai su pagine pubbliche → vive sulla web app con login. |
| T9 | **Filiere aggiuntive nel briefing mattutino** | Il committente vuole estendere le filiere del briefing esistente con quelle emerse qui: AI/software, quantum, robotica, spazio, cybersecurity, biotech/genomica, fintech, nucleare (oltre a uranio già presente). ⚠ Tocca il branch di produzione `claude/financial-briefing-pipeline-aVCmh` → seguire le cautele di `04-briefing/README.md`, non rompere il cron. |
| T10 | **Pacchetto PIR — setup operativo** | Richiede intermediario italiano che gestisca il piano in amministrato (IBKR non può; candidato: Directa). Verificare col commercialista vincoli 70/25/5, plafond €40K/anno – €200K totale, e la convivenza con i conti IBKR. |
| T11 | **Relazione di adeguatezza MiFID** | Verificare con l'assetto compliance se il PDF di sessione può fungere da relazione di adeguatezza (D7/D8) e cosa deve contenere come minimo. |
| T12 | **Perimetro esecuzione ordini SCF** | Art. 18-bis: la SCF consiglia, l'esecuzione resta al cliente. Verificare il flusso operativo su IBKR (chi clicca l'ordine, come si traccia la decisione del cliente). |

## Igiene e coerenza

| ID | Task | Note |
|---|---|---|
| T13 | **Naming file specifica** | Il file consegnato si chiama `MVF_V41.MD` ma il contenuto dichiara v4.0 ovunque (handoff, nota di versionamento). Allineare il nome prima di storicizzare output. |
| T14 | **Portafogli personali fuori dal codice** | `04-briefing/pipeline/portafogli_examples/` contiene posizioni reali (alex.csv, vale.csv). Con l'arrivo di clienti veri: migrare tutti i portafogli nel DB della web app (UE, con login) e togliere i CSV dal repo. |
| T15 | **Discrepanza filiere handoff** | L'handoff dichiara "15 filiere mappate", il codice ne mappa 9. Riconciliare quando si estende la tassonomia (T9). |
| T16 | **Soglie occupancy REIT per sottosettore** | La banda R1 (§3 calibrazione) è unica; alla prima taratura differenziare net-lease / office / hotel / industrial. |
| T17 | **Scala ESG IBKR** | Fissare la soglia esatta di idoneità Etico sulla scala effettivamente mostrata da IBKR (da fare sul primo lotto reale di inserimenti, §10). |

## Aggiunti in review v1.1

| ID | Task | Note |
|---|---|---|
| T18 | **Insider non-US** | Estendere C18 oltre EDGAR/Form 4: registri internal dealing ufficiali UE (CONSOB internal dealing, BaFin Directors' Dealings, AMF, FCA PDMR). Nessuna API unificata gratuita nota: valutare per-paese. Dove non reperibile: metrica omessa + ri-basata. |
| T19 | **Lookup moat Morningstar via web** | Implementare in modo robusto il metodo dello stock screener MVF in chat: ricerca web del rating pubblicato + parsing (wide/narrow/none), tag [V] se ≥2 riscontri, [U] se singolo. Verificare termini d'uso; il manuale prevale sempre. |

## Aggiunti durante il collaudo bozza 1

| ID | Task | Note |
|---|---|---|
| T20 | **Aggiustamento per stock split** | I dati EDGAR delle azioni (share count) NON sono rettificati per split; yfinance sì. Su WMT lo split 3:1 (feb 2024) fa leggere una "diluizione 23%/anno" falsa, che intacca C7 (FCF/share growth), C22 (buyback) e genera un red flag errato → deprime il voto. Serve leggere la serie split da EDGAR (StockholdersEquityNoteStockSplitConversionRatio o i prezzi rettificati di stockanalysis) e normalizzare la serie azioni. Priorità alta: falsa i per-share di ogni titolo che ha fatto split nel periodo. |
| T21 | **Correttivo settoriale — universo vero** | Il correttivo (percentile vs peer) è tanto più giusto quanto più l'universo è ampio e ben classificato. In bozza 1 i peer sono una lista curata (config.SECTOR_PEERS); a regime devono venire dall'universo completo MSCI World+KR+TW+Cina. |
