# Screener Live — motore Regime S (bozza 1)

Implementazione della calibrazione `PROXIMA-Main/06-screener-live/CALIBRAZIONE-MVF-S.md`
(v1.1). Specifica autorevole: MVF v4.0.

## Cosa fa la bozza 1

- **Fetch**: yfinance (fonte secondaria) + **SEC EDGAR XBRL** (primaria [P]
  per US/ADR) con cross-validation e tagging DIP [P]/[V]/[U].
- **Scoring common (base 280)**: tutte le bande v1.1 (livello + trend +
  bonus settoriale), guard trasversali, redistribuzioni Sez. 3E/3F,
  ri-basatura delle metriche mancanti, penalità Altman progressiva.
- **Gate G1–G5** + red flag (critici/attenzione). G6 solo Regime A.
- **IQI-S** (Blocco A/B con tier dividendo e cap forward [S]), **CS-S**
  (provenienza/completezza/puntualità/coerenza), catena **MoS** → prezzo
  ideale indicativo, **netto Italia**.
- **Pacchetti**: tag idoneità (difensivo, compounders, innovativo, emergenti,
  PIR, etico-candidato, cedola mensile) + badge (Aristocrat/King/OCCASIONE
  D'ORO).
- **Persistenza**: SQLite con snapshot, versione MVF, classe, base, regime.

## Uso

```bash
pip install -r requirements.txt
python batch.py --test              # banco di prova (calibrazione §14)
python batch.py --tickers KO JNJ    # ticker specifici
```

Override manuali (file JSON accanto al codice):
- `moat_overrides.json` — `{"KO": "wide"}` (Morningstar via IBKR, §7)
- `class_overrides.json` — `{"ARCC": "bdc"}` (routing classi)
- `themes_overrides.json` — `{"IONQ": "quantum"}` (tag tematici Innovativo)

## Limiti dichiarati della bozza 1

- REIT: motore parziale (le dedicate da IR — AFFO, occupancy, WALT — non
  sono ancora reperibili) → copertura bassa **dichiarata**, mai mascherata.
- BDC/MLP/preferred: rilevate ma non ancora votate (motori dedicati in coda).
- Insider (C18) e MOAT (C26): omesse+ri-basate finché non arrivano T18/T19
  o l'inserimento manuale.
- EDINET/DART/MOPS/ESEF: nello stack definitivo (§9), non ancora cablati →
  fuori dagli US il tag resta [U] e il CS-S lo riflette onestamente.
- Universo automatico, mediane settoriali, web app, PDF, alert giornalieri:
  prossime iterazioni.

⚠ Nota ambiente: l'IP di uscita condiviso degli ambienti cloud può essere
rate-limitato da Yahoo (HTTP 429). Sul VPS di produzione il problema non si
pone; il codice ha comunque retry con backoff e non inventa mai dati.
