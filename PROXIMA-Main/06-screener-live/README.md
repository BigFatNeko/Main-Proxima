# 06 — Screener Live (MVF v4.0)

Hub di progetto dello **screener live**: il programma che in sessione con il
cliente restituisce pool di titoli conformi a MVF v4.0, organizzati in
pacchetti, e che a cadenza programmata sorveglia i titoli posseduti dai
clienti per il ribilanciamento.

## Ordine di lettura

| File | Contenuto | Stato |
|---|---|---|
| `DECISIONI.md` | Registro delle decisioni prese (D1–D8 dell'handoff + Q1–Q30 delle sessioni di inquadramento). | Vivo, si aggiorna |
| `CALIBRAZIONE-MVF-S.md` | **Il documento da approvare riga per riga**: bande di scoring per le 5 classi, regole pacchetti, griglie di allocazione, catalogo alert, fonti dati, schema output. | ⏳ In approvazione |
| `TASKS-POSTICIPATI.md` | Lavori rimandati consapevolmente, per non dimenticarli. | Vivo |

## Gerarchia documentale

1. **MVF v4.0** (`rassegna-stampa/docs-mvf/MVF_v4.0_istruzioni_operative.md`
   sul branch `claude/financial-briefing-pipeline-aVCmh`) — fonte autorevole.
2. Handoff di inquadramento (caricato in sessione, v1.1).
3. Questa cartella — decisioni operative e calibrazione.
4. Codice esistente (`04-briefing/pipeline/`) — riferimento infrastrutturale
   (implementa MVF v3.0, superato come logica di valutazione).

In caso di conflitto tra la calibrazione e la specifica MVF, la calibrazione
**dichiara esplicitamente la deviazione**; le deviazioni non dichiarate sono
errori da correggere.

## Regola di lavoro

Prima solidi, poi il codice: nessuna implementazione finché
`CALIBRAZIONE-MVF-S.md` non è approvato.
