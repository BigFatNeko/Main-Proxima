# Proxima — Modello Funnel SCF (fasce in abbonamento)

**Questa è la versione SCF fee-only del modello previsionale** (v1, giugno 2026),
costruita sulle decisioni del 10/06/2026:

| Fascia | Prezzo (indicativo) | Cosa include |
|---|---|---|
| **Check-up** | Gratis | Report personalizzato via IA — punto d'ingresso del funnel |
| **App** | €1–5/mese | Insights e personalizzazione |
| **Monitor** | €5–20/mese | Revisione e monitoraggio del portafoglio |
| **Live** | €50–150/mese | Consulenza approfondita con call dedicate |

Differenze chiave rispetto al modello base (`../funnel-model/`):

- **Niente parcella €490**: i ricavi sono abbonamenti mensili per fascia
  (`MRR = App×prezzo + Monitor×prezzo + Live×prezzo`). La SCF incassa il 100%
  direttamente dal cliente — nessuno split con SIM.
- **Funnel a due stadi**: i canali portano **utenti gratuiti** al Check-up IA;
  gli abbonati arrivano dai nuovi Check-up (default 6%) e dalla base gratuita
  accumulata (default 0,3%/mese). ⚠ **Queste conversioni sono le assunzioni
  più sensibili e vanno validate sul campo.**
- **La capacità vincola solo la fascia Live**: App e Monitor scalano col
  software; le ore del team limitano onboarding e cura dei clienti Live.
- **Costi app e IA**: sviluppo app una tantum (default €18K, M-9→M-4), hosting
  mensile e costo IA per ogni report generato (il gratis non è gratis per noi).
- **AUM monitorato** (Monitor+Live): KPI di credibilità, **non genera ricavi**.
- **Churn per fascia**: App 4,5%/mese, Monitor 2%, Live 1,2% (default).
- **Stato lavori** in fondo alla pagina: recap costante fatto/da fare su
  regolatorio, app, landing, marketing, branding, amministrazione
  (cliccabile, si salva nel browser; elenco di partenza in `roadmap.js`).

## Come aprirlo

Come il modello base: serve un server locale.

```bash
cd /percorso/alla/cartella/funnel-model-scf
python3 -m http.server 8080      # su Windows: python -m http.server 8080
```

Poi apri **http://localhost:8080** (non doppio click su index.html: errore CORS).

## Struttura dei file

| File | Cosa fa |
|------|---------|
| `index.html` | Entry point: palette, font, caricamento CDN |
| `model.js` | Motore SCF: funnel gratuito→fasce, capacità Live, costi app/IA |
| `controls.js` | Sidebar: pannello "Fasce e abbonamenti" + canali + costi |
| `glossary.js` | Glossario aggiornato all'offerta a fasce |
| `dashboard.js` | KPI (abbonati per fascia, utenti gratuiti, ARPU) e grafici |
| `table.js` | Tabella 36 mesi con colonne per fascia, export CSV/JSON |
| `roadmap.js` | Box "Stato lavori": recap fatto/da fare per area |
| `app.js` | Componente root, stato, salvataggio nel browser |

## Assunzioni da validare (in ordine di impatto)

1. **% Check-up → abbonati** (default 6%) — decide quasi tutto.
2. **Mix delle fasce** (default 60/30/10) — decide l'ARPU blended (~€170/anno).
3. **Churn App** (default 4,5%/mese) — gli abbonamenti micro hanno churn alto.
4. **Costo IA per report** (default €0,40) — a volumi alti pesa sul margine.

Il vecchio modello a parcella resta in `../funnel-model/` come riferimento;
la logica provvigionale SIM è in `../../99-archivio/` (non usarla).
