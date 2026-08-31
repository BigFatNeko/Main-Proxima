# Briefing finanziario — dove vive la pipeline

**Sorgente unica: `rassegna-stampa/` nella radice del repo.**

Questa cartella conteneva una copia dei sorgenti "per consultazione". La copia
è stata rimossa: era ferma a MVF v3.0 mentre la produzione era già alla v4.1
(`mvf_valuation.py` 729 righe contro 1.865, nessun `edgar_client.py`, nessun
`docs-mvf/`) e conteneva ancora il bug di `normalize_metric()` corretto nella
riscrittura. Chi la apriva leggeva codice sbagliato credendolo attuale.

Lo storico resta in git: `git log -- PROXIMA-Main/04-briefing/pipeline/`.

## Come gira la versione live

- **Codice:** `rassegna-stampa/`, su `main`.
- **Esecuzione:** GitHub Actions, `.github/workflows/briefing.yml` — cron
  lun–sab più `workflow_dispatch`. Il workflow non è più inchiodato a un
  branch: fa checkout del ref da cui parte e ripubblica sullo stesso.
- **Output:** `docs/alex-latest.html`, `docs/vale-latest.html` e
  `docs/archivio/`, serviti via GitHub Pages.
- **Destinatari:** portafogli `alex` e `vale`
  (`rassegna-stampa/portafogli_examples/`).

## Vincoli da rispettare

1. Un cron GitHub Actions parte **solo dal workflow presente sul branch di
   default** → `briefing.yml` deve restare su `main`.
2. I secret (`ANTHROPIC_API_KEY`, `EDGAR_USER_AGENT`) vivono nelle GitHub
   Actions secrets, non nel repo.
3. `docs/archivio/` è la memoria storica del briefing: lo script vi legge i
   briefing precedenti per decidere la modalità del giorno. Non svuotarlo.

## Se un giorno si vuole spostare il codice qui sotto

Resta possibile, ma va fatto in una PR dedicata e verificata con un run
manuale prima di affidarsi al cron. Il punto delicato è che
`briefing_pipeline.py` raggiunge l'archivio con `SCRIPT_DIR.parent / "docs"`:
spostando il codice di due livelli quel path punterebbe a una cartella
inesistente, `load_previous_briefings()` tornerebbe vuota **senza errori** e
il briefing perderebbe la memoria dei giorni precedenti. Prima di muovere i
file va ancorata la radice del repo in modo esplicito.
