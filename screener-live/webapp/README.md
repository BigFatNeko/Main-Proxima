# Proxima Screener Live — Web App

Interfaccia web del motore Regime S. Login per i due soci, dashboard
interattiva (filtro per settore, ordinamento per Voto MVF) e **scheda di
dettaglio per titolo** (il «giustifica»: scomposizione metrica, cascata
fiscale netto Italia, prezzo ideale, red flag, composizione dati [P]/[V]/[U]).

Legge dal DB SQLite prodotto da `batch.py` (`../output/screener.db`),
snapshot più recente.

## Sviluppo (locale)

```bash
cd screener-live
python batch.py --universe-global --source free    # popola il DB
cd webapp
pip install -r requirements.txt
PROXIMA_PASSWORD=scegli-una-password FLASK_SECRET=una-stringa-lunga-casuale python app.py
# http://127.0.0.1:5000  — password = quella impostata
```

## Produzione (VPS europeo)

1. **Batch a cadenza** (cron notturno) che aggiorna il DB:
   ```
   0 3 * * *  cd /srv/proxima/screener-live && python batch.py --universe-global --source free
   ```
   Sul VPS yfinance funziona → usare `--source auto` per la cross-validation
   yfinance↔TradingView ([V]) e per la copertura piena non-US (T23).

2. **App con gunicorn dietro nginx + HTTPS**:
   ```
   gunicorn -w 2 -b 127.0.0.1:5000 app:app
   ```
   nginx come reverse proxy con certificato (Let's Encrypt). Variabili
   d'ambiente obbligatorie: `FLASK_SECRET` (lungo, casuale) e
   `PROXIMA_PASSWORD` (forte). Mai lasciare i default.

## Sicurezza e dati clienti (D8)

- Oggi il DB contiene **solo output dello screener** (nessun dato cliente).
- Quando arriveranno i portafogli clienti (T6/T14): DB su VPS UE, dietro
  login e HTTPS, mai su pagine pubbliche. Aggiungere un log immutabile con
  snapshot di ciò che viene mostrato/raccomandato (traccia D8).
- Auth attuale = singola password condivisa (adeguata per 2 soci). Per più
  utenti: passare a utenti+hash e sessioni per-utente.

## Struttura

```
webapp/
  app.py                 Flask: auth, /, /ticker/<t>, /api/results
  templates/
    login.html           accesso
    dashboard.html       lista + filtro (idrata da /api/results)
    detail.html          scheda titolo (giustifica)
  static/
    app.css              design system (tema chiaro/scuro)
    dashboard.js         render lista + filtro settore
  requirements.txt
```
