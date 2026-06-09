# Briefing finanziario — pipeline (COPIA centralizzata)

> ⚠ **ATTENZIONE: la pipeline è in produzione e in uso quotidiano.**
> Questa cartella è una **copia per centralizzazione/consultazione**.
> Modificare i file qui **non** cambia l'output dei briefing live.

## Come gira la versione live

- **Codice attivo:** branch `claude/financial-briefing-pipeline-aVCmh`.
- **Esecuzione:** GitHub Actions, workflow `.github/workflows/briefing.yml`
  (cron mattutino lun–sab + `workflow_dispatch` manuale). Il workflow fa
  `checkout` del branch della pipeline, esegue lo script Python e pubblica i
  briefing generati (output su `docs/`, serviti via GitHub Pages).
- **Destinatari attuali:** portafogli di esempio `alex` e `vale`
  (vedi `pipeline/portafogli_examples/`).

## Vincoli da rispettare (per non interrompere il servizio)

1. Un cron GitHub Actions parte **solo dal workflow presente sul branch di
   default** → `briefing.yml` deve restare sul branch di default del repo.
2. Il workflow fa checkout di `claude/financial-briefing-pipeline-aVCmh`:
   **quel branch non va cancellato** finché la pipeline gira da lì.
3. Eventuali secret/API key vivono nelle **GitHub Actions secrets**, non nel repo.

## Migrazione (futura, da fare con cura)

Per portare la pipeline "dentro" `PROXIMA-Main/04-briefing/pipeline/` come
sorgente unica servirà, in un'unica PR testata:

1. spostare il codice e aggiornare i percorsi nello script;
2. aggiornare `briefing.yml` (ref e path di esecuzione);
3. un run manuale `workflow_dispatch` di verifica **prima** di affidarsi al cron;
4. solo dopo la conferma, dismettere il vecchio branch.

Contenuto della copia: `pipeline/` (`screener.py`, `briefing_pipeline.py`,
`mvf_valuation.py`, `filiere_screener.py`, `newspaper_template.html`,
`system_prompt.md`, `requirements.txt`, script di avvio, esempi di portafoglio).
