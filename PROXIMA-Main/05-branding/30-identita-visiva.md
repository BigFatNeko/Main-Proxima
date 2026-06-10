# Identità visiva Proxima — sistema v1 (giugno 2026)

**Fase 3 del percorso di branding.** Parte dagli asset già definiti (palette,
font) e li trasforma in un **sistema** con regole d'uso, direzioni di logo e
applicazioni per ogni touchpoint. Tiene conto delle decisioni di giugno 2026:
brand **aziendale** (niente volto-guru), offerta a fasce con **app al centro**
(vedi `40-brand-strategy-scf.md`).

---

## 1. L'idea visiva

**"La stella più vicina."** Proxima (Centauri) è la stella più vicina al
sistema solare: vicinanza + orientamento (le stelle si usano per navigare).
Tradotto in estetica: **cielo notturno sobrio** (navy, petrolio) **con un solo
punto di luce** (gold) su carta calda (avorio). Non spazio/fantascienza, non
fintech al neon: un osservatorio, calmo e preciso.

La ricerca competitor (fase 2) mostra due estetiche dominanti — istituzionale
fredda (Consultique) e social aggressiva (IoInvesto) — e uno spazio libero:
**caldo, sobrio, premium accessibile**. Questo sistema occupa quello spazio.

Tre aggettivi-guida per ogni scelta visiva: **ordinato** (siamo una struttura
organizzata, decisione D3), **caldo** (carta avoriata, foto vere), **preciso**
(numeri tabellari, niente decorazione gratuita).

---

## 2. Logo

### Direzioni proposte

| | Direzione | Descrizione | Pro | Contro |
|---|---|---|---|---|
| **A** | **Stella** ⭐ *consigliata* | Wordmark "proxima" minuscolo in navy + segno: stella a 4 punte gold (la scintilla/stella di navigazione). Il segno vive anche da solo (favicon, app icon, watermark report). | Racconta il nome, funziona a ogni scala, sobria | La stella a 4 punte è diffusa (va disegnata con carattere: punte asimmetriche, una più lunga verso l'alto-destra = "oltre") |
| B | **Orbita** | Monogramma "P" navy attraversato da un'ellisse orbitale sottile con un punto gold sull'orbita (il cliente che avanza). | Distintivo, ottimo per app icon | Più "tech", rischia di sembrare un logo da startup SaaS |
| C | Tipografica pura | Solo wordmark con dettaglio sul glifo "x" (incrocio = stella implicita) | Massima sobrietà istituzionale | Debole a scala piccola, poco riconoscibile sui social |

Bozze geometriche in `assets/` (`marchio-A-stella.svg`, `marchio-B-orbita.svg`):
sono **schizzi per decidere la direzione**, non esecutivi — il wordmark
definitivo va fatto disegnare (vedi sez. 8).

### Lockup con descrittore (obbligatorio)

Metà degli italiani non sa cosa sia la consulenza indipendente (fase 2, sez.
2.2) → il logo viaggia **sempre**, nei contesti di primo contatto, con il
descrittore di categoria:

```
[segno] proxima
        Consulenza finanziaria indipendente
```

Descrittore in DM Sans Regular, navy al 70% (`#0D2B4E` su avorio regge fino al
55% di opacità; non scendere oltre). Senza descrittore solo dove il contesto è
già noto (dentro l'app, nei report per clienti).

### Regole d'uso

- Area di rispetto: altezza della "x" del wordmark su ogni lato.
- Su fondo chiaro: wordmark navy + segno gold. Su fondo navy/petrolio: wordmark
  avorio + segno gold. **Mai** wordmark gold (contrasto 2,2:1 su chiaro).
- Mai effetti: niente ombre, gradienti, contorni.

---

## 3. Colore

| Colore | Hex | Ruolo | Quota indicativa |
|---|---|---|---|
| **Avorio** | `#F5F3EE` | Fondo principale, "carta" | ~60% |
| **Navy** | `#0D2B4E` | Testo, struttura, fondi scuri | ~25% |
| **Petrolio** | `#1D4A52` | Secondario: card, grafici, hover | ~10% |
| **Gold** | `#C4A44A` | Accento: traguardi, il "punto di luce" | ~5% |

**Regole di accessibilità (contrasti WCAG misurati):**

- Navy su avorio **12,9:1** e petrolio su avorio **8,8:1** → testo libero (AAA).
- Gold su avorio **2,2:1** → ❌ mai testo su fondo chiaro; solo elementi
  decorativi ≥3px o icone grandi.
- Gold su navy **5,9:1** → ✅ testo grande/accenti su fondo scuro (è il
  pairing-firma del brand: titolo avorio + parola chiave gold su navy).
- Bianco su petrolio **9,8:1**, avorio su navy **12,9:1** → ✅.

**Tinte di servizio** (derivate, per UI app): navy al 10% su avorio per bordi e
divisori; verde/rosso per stati solo dentro l'app, mai nel marketing (niente
"verde guadagno" da trading app).

**Dark mode app:** fondo navy, testo avorio, accenti gold — già pronta per
costruzione, nessun colore nuovo.

---

## 4. Tipografia

- **Plus Jakarta Sans** (700/600) — titoli, numeri-chiave. Autorità.
- **DM Sans** (400/500) — testo, UI, didascalie. Calore.
- Entrambi Google Fonts (gratuiti, web + app senza licenze).

Scala (web, base 16px): 14 / 16 / 20 / 25 / 31 / 39 / 49. Interlinea 1,5 sul
testo, 1,1–1,2 sui titoli. **Numeri tabellari** (`font-variant-numeric:
tabular-nums`) ovunque compaiano cifre: parcelle, percentuali, tabelle — la
precisione è un valore di brand.

Maiuscole: mai titoli in ALL CAPS (urlato); etichette piccole in maiuscoletto
spaziato (+8% tracking) sono ammesse.

---

## 5. Sistema grafico

- **Griglia e spazio:** base 8px; il bianco è autorità — densità massima: una
  idea per schermata/sezione. Raggi angoli: 8px (card), 999px (pill/CTA).
- **Icone:** outline 1,5px, angoli arrotondati, navy; gold riservato a
  traguardi/milestone. Un solo set (es. Lucide) per coerenza app/sito.
- **Fotografia:** persone italiane vere in momenti quotidiani (tram, caffè,
  scrivania), luce naturale, palette desaturata verso l'avorio. **Vietato:**
  stock "uomo in giacca indica grafico", grattacieli, monete/salvadanai,
  lifestyle di lusso. Con brand aziendale (D3) le foto mostrano **il team al
  lavoro e i clienti**, mai un volto singolo ricorrente.
- **Dataviz:** linee navy/petrolio, **gold solo per il punto-traguardo** (es.
  obiettivo raggiunto); fondi puliti, niente griglie fitte; mai grafici che
  promettono rendimenti (vincolo compliance, vedi audit sez. 5) — si mostrano
  scenari e confronti di costo, non proiezioni di guadagno.
- **La firma visiva ricorrente:** il "punto di luce" — un singolo elemento gold
  per composizione (la stella del logo, il punto sull'orbita, il traguardo nel
  grafico). Se in una pagina ci sono due cose d'oro, una è di troppo.

---

## 6. Applicazioni per touchpoint

| Touchpoint | Ruolo (da D2) | Note visive |
|---|---|---|
| **Landing/waitlist** | Lista d'attesa → terreno per il marketing → futuro sito | Hero su avorio, sezione fasce prezzo su navy con gold; il copy va riscritto (audit, sez. 4) |
| **Report IA gratuito** | Primo contatto col prodotto: **è il biglietto da visita del brand** | PDF/pagina impaginata come un documento da private bank: copertina navy, carta avorio, numeri tabellari, watermark stella. Deve *sembrare* il report da €150/mese |
| **App (fasce €1–5 / €5–20)** | Insights, personalizzazione, monitoraggio | UI su avorio, dark mode navy; gold per traguardi di risparmio (lì vive il valore "abitudine") |
| **Consulenza live (€50–150)** | Call dedicate | Template slide/documenti coordinati col report; il cliente premium riconosce la stessa carta |
| **Social corporate** | Format riconoscibili senza volto-guru | Rubriche brandizzate (es. card "Tradotto:" che spiega un termine a settimana): si possiede il **formato**, non la faccia. Template card: avorio, titolo Jakarta, stella gold |
| **Email** | Waitlist e clienti | Testo semplice su avorio, un solo CTA navy |

---

## 7. Asset in questa cartella

- `assets/marchio-A-stella.svg` — bozza direzione A (consigliata)
- `assets/marchio-B-orbita.svg` — bozza direzione B

---

## 8. Prossimi passi

1. **Scegliere la direzione del logo** (A/B/C) → poi brief a un designer per
   l'esecutivo del wordmark (budget tipico €1,5–4K per identità completa;
   rientra nella voce brand del piano €180K).
2. Verifica formale **marchio** UIBM/EUIPO classe 36 prima dell'esecutivo
   (vedi fase 2, sez. 2.5).
3. Costruire i template: card social, report IA, slide consulenza — dopo il
   logo definitivo.
4. Applicare il sistema alla **nuova landing** (riscrittura copy da
   `40-brand-strategy-scf.md` + audit sez. 4).
