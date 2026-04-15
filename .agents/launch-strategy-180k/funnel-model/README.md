# Proxima — Funnel Model Bottom-Up

Modello di funnel interattivo che calcola i clienti di Proxima partendo dai dati reali di ogni step di conversione per ogni canale, invece che dai target top-down.

## Come aprirlo

Apri `index.html` con doppio click o tramite:

```bash
open index.html            # macOS
xdg-open index.html         # Linux
start index.html            # Windows
```

Oppure servi la directory con un server locale:

```bash
python3 -m http.server 8080
# poi apri http://localhost:8080
```

Nessun build step: tutti i file sono caricati dal browser via Babel standalone + React 18 UMD + Recharts UMD.

## Cosa modella

Funnel per ogni canale:

```
Traffico → Uso calcolatore → Prenotazione check-up → Check-up completato → Cliente pagante
```

**Canali modellati separatamente:**

1. Google Ads (CPC + CVR funnel)
2. Meta Ads IG+FB
3. LinkedIn Ads (dal mese 15 = strategy month +9)
4. SEO organico (compound growth)
5. Social organico IG/TikTok/LinkedIn
6. Referral (% clienti attivi × CVR referral, dal mese 15)
7. Borrowed (PR + podcast + eventi, lead stimati/mese)

**Vincolo di capacità:**

- Founder: X ore/settimana (default 20h)
- Ogni cliente richiede 3.5h (check-up + onboarding + prima consulenza)
- Secondo consulente entra al mese 20 (strategy month +14)
- Se i lead superano la capacità, i clienti effettivi sono limitati

## Output

1. **Dashboard** con KPI a M6, M12, M18 della strategia + confronto con target top-down (108 / 277 / 509 clienti).
2. **Grafico crescita clienti** (actual vs target) con evidenza del collo di bottiglia.
3. **Grafico stacked** dei nuovi clienti per canale.
4. **Tabella 24 mesi** con prenotazioni per canale, capacità max, nuovi clienti, churn, totale, MRR, ARR.
5. **Break-even** (revenue cumulato ≥ €180.000).

## Struttura

| File | Contenuto |
|------|-----------|
| `index.html` | Entry point, palette, font DM Sans/DM Mono, CDN |
| `model.js` | Logica funnel bottom-up mese per mese |
| `controls.js` | Slider per tutti i parametri |
| `dashboard.js` | KPI cards + Recharts |
| `table.js` | Tabella 24 mesi |
| `app.js` | Componente principale, state management |

## Palette

- Navy scuro: `#0C1420`
- Card bg: `#121E30`
- Border: `#1E2A3E`
- Oro smorzato: `#C4A962`
- Text primary: `#E8ECF2`
- Text secondary (grigio-blu): `#8B98B0`
