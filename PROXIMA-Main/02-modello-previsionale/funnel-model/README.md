# Proxima — Modello Funnel (in italiano)

Applicazione web interattiva che calcola, mese per mese, quanti clienti e quanti ricavi genererà la strategia di lancio Proxima, **partendo dai numeri veri di ogni canale** (click, visite, percentuali di chi prenota, ecc.) invece che da obiettivi fissati a tavolino.

Pensato per essere usato anche da chi non ha background di marketing o finance: tutte le etichette sono in italiano e c'è un **glossario integrato** con le definizioni dei termini.

## Come aprirlo

Servono tre cose:

1. Un **server locale** (il browser blocca il caricamento diretto da file)
2. Un **browser** moderno (Chrome, Firefox, Edge, Safari)
3. Una **connessione internet** (per caricare React e Recharts dalla CDN)

### Passo 1 — Aprire un terminale nella cartella

```bash
cd /percorso/alla/cartella/funnel-model
```

Su Windows PowerShell, se il percorso contiene spazi, usa le virgolette:
```powershell
cd "C:\Users\tuo-nome\...\funnel-model"
```

### Passo 2 — Avviare il server

```bash
python3 -m http.server 8080
```

Su Windows è spesso `python` invece di `python3`:
```powershell
python -m http.server 8080
```

Il terminale dirà: `Serving HTTP at :: port 8080`. Lascia questa finestra aperta.

### Passo 3 — Aprire il browser

Vai su: **http://localhost:8080**

> ⚠️ Importante: devi scrivere `http://localhost:8080` nella barra dell'indirizzo, NON aprire `index.html` con doppio click. Il doppio click non funziona perché il browser blocca il caricamento dei file JavaScript per motivi di sicurezza (errore CORS).

### Passo 4 — Chiudere il server

Quando hai finito, torna al terminale e premi `Ctrl+C`.

## Cosa vedrai

**Sidebar di sinistra** — Tutti i parametri del modello, raggruppati in pannelli espandibili:

- **Dopo la prenotazione** — % persone che si presenta, % che diventa cliente pagante
- **Google / Meta / LinkedIn Ads** — costo per click e conversioni del funnel pubblicitario
- **SEO** — visite gratuite da Google, crescita mensile, conversioni
- **Social organici** — visite da post gratuiti su IG/TikTok/LinkedIn
- **Passaparola** — clienti esistenti che portano altri clienti
- **PR, podcast ed eventi** — prenotazioni da credibilità costruita altrove
- **Ore di lavoro disponibili** — capacità del founder e del 2° consulente
- **Parcelle e abbandoni** — parcella media, % disdette mensili

**Area principale:**

1. **Glossario** (collassabile, in alto) — definizioni di tutti i termini in italiano semplice
2. **Risultati chiave** alle tappe della strategia (M+6, M+12, M+18)
3. **Pareggio e costi di acquisizione** clienti
4. **Grafici**: crescita vs obiettivo, composizione per canale, ricavi vs €180K
5. **Tabella completa 24 mesi** — esportabile in CSV o JSON
6. **Stato lavori** (in fondo) — recap costante delle cose fatte e da fare su
   tutti i fronti: iter regolatorio, app, landing page, marketing, branding,
   amministrazione interna. Clicca una voce per segnarla fatta/da fare (si
   salva nel browser); l'elenco di partenza si aggiorna in `roadmap.js`.

Ogni modifica a uno slider **aggiorna tutto in tempo reale**. I valori si salvano automaticamente nel browser (resistono al reload della pagina).

## Struttura dei file

| File | Cosa fa |
|------|---------|
| `index.html` | Entry point: palette colori, font, caricamento CDN |
| `model.js` | Logica del modello: calcolo funnel, 7 canali, vincolo capacità |
| `controls.js` | Sidebar con tutti gli slider e pannelli collassabili |
| `glossary.js` | Pannello glossario con definizioni dei termini |
| `dashboard.js` | KPI card e grafici (Recharts) |
| `table.js` | Tabella completa 24 mesi con export CSV/JSON |
| `roadmap.js` | Box "Stato lavori": recap fatto/da fare per area (regolatorio, app, landing, marketing, branding, amministrazione) |
| `app.js` | Componente root, gestione stato, salvataggio nel browser |

## Palette

- Sfondo principale: `#0C1420` (navy scuro)
- Card: `#121E30`
- Bordi: `#1E2A3E`
- Oro smorzato (accenti): `#C4A962`
- Testo principale: `#E8ECF2`
- Testo secondario: `#8B98B0` (grigio-blu)

Font: **DM Sans** (testo) + **DM Mono** (numeri e tabelle).
