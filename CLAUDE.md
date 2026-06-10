# CLAUDE.md — Proxima (SCF)

Istruzioni di progetto per le sessioni Claude Code. **Rispondi sempre in italiano.**

## Cos'è Proxima

Proxima è una **SCF — Società di Consulenza Finanziaria** (consulenza finanziaria
indipendente *fee-only*, iscritta all'Albo OCF Sezione III, art. 18-bis TUF).
Target: risparmiatori italiani con meno di €100.000, mal serviti dalle banche.
2 fondatori, base Emilia-Romagna → Nord Italia → Italia. Budget di lancio
pianificato: €180K su 18 mesi.

**Struttura legale FISSATA (giugno 2026):** dopo confronto col commercialista,
l'unica strada percorribile è la **SCF**. I percorsi alternativi esplorati in
passato — **SIM** e **agente collegato di SIM** (art. 31-ter TUF) — sono
**abbandonati**. Non riproporli come opzione di default.

## Questo repository

È l'hub centrale dell'azienda. Tutto il materiale di business vive sotto
**`PROXIMA-Main/`**:

| Cartella | Contenuto |
|---|---|
| `01-strategia/` | Piano di lancio €180K, struttura societaria SCF, iter OCF, costi, tassazione, competitor, scenari macro. |
| `02-modello-previsionale/` | Modello funnel costi/ricavi (React single-file). **Da ricalibrare per SCF fee-only**: vedi `02-modello-previsionale/RICALIBRAZIONE-SCF.md`. |
| `03-marketing/` | Strategia marketing + libreria di ~36 skill (growth, SEO, CRO, copywriting, paid ads, launch strategy…), tenute anche per uso futuro. |
| `04-briefing/` | **COPIA** della pipeline di briefing finanziario. ⚠ Vedi avviso sotto. |
| `05-branding/` | Asset di brand + landing page. |
| `99-archivio/` | Materiale **superato** (percorso SIM/agente collegato), consolidato e ordinato come riferimento storico. Vedi `99-archivio/README.md`. |

## ⚠ Briefing pipeline — NON ROMPERE

La pipeline di rassegna stampa / briefing è **in produzione e in uso quotidiano**.

- Il codice "vivo" sta sul branch **`claude/financial-briefing-pipeline-aVCmh`**.
- Gira via **`.github/workflows/briefing.yml`** (cron mattutino, lun–sab). Un cron
  GitHub Actions parte **solo dal branch di default** → `briefing.yml` deve
  restare sul branch di default, e il branch della pipeline non va cancellato.
- `PROXIMA-Main/04-briefing/pipeline/` è una **copia per centralizzazione**:
  modificarla **non** cambia l'output live.
- Prima di toccare il workflow o il branch del briefing, leggi
  `PROXIMA-Main/04-briefing/README.md`.

## Convenzioni

- Lingua: italiano.
- Sviluppa sul branch indicato nella sessione; non spingere sul branch di default
  senza permesso esplicito.
- Storia: a giugno 2026 il repo è stato ripulito da un template
  "everything-claude-code" e da un progetto "LLM Council", entrambi non pertinenti.

## Tooling di sessione (`.claude/`)

La cartella `.claude/` sta **alla radice** (così Claude Code la auto-carica a ogni
sessione web) e contiene strumenti, non materiale di business:

- **`skills/last30days/`** — ricerca multi-fonte (Reddit, HN, X, YouTube,
  Polymarket…) sugli ultimi 30 giorni. Si invoca con `/last30days`. Per la
  copertura piena servono API key in `.claude/last30days.env` (gitignorato) o nei
  secret dell'ambiente web; modello in `.claude/last30days.env.example`.
- **`skills/caveman/`** — modalità di risposta ultra-compatta (`lite`/`full`/`ultra`).
  **Non** attiva di default: si accende dicendo "caveman mode" / "be brief" / `/caveman`.
- Hook `SessionStart` in `settings.json`: a inizio sessione mostra lo stato di
  configurazione di last30days (avvolto in `|| true`, non blocca nulla).

La libreria di ~36 skill di marketing/growth sta invece sotto
`PROXIMA-Main/03-marketing/skills/` come **riferimento** (non auto-caricata).
