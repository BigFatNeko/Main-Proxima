# Proxima — Area clienti (prototipo)

Prime quattro interfacce dell'applicazione Proxima SCF. È un **prototipo
navigabile con dati simulati**: nessun backend, nessuna autenticazione reale,
nessun dato di mercato. Serve a validare flusso, contenuti e linguaggio prima di
scrivere il sistema vero.

## Avvio

```bash
cd app
npm install
npm run dev     # http://localhost:5173
```

Altri comandi: `npm run build` (build di produzione), `npm run typecheck`.

## Il flusso

| # | Schermata | File | Cosa fa |
|---|---|---|---|
| 1 | Login | `src/screens/LoginScreen.tsx` | Accesso e registrazione simulati. Nessuna password viene salvata. |
| 2 | Questionario | `src/screens/QuestionarioScreen.tsx` | 16 domande in stile MiFID II, divise nelle cinque aree di adeguatezza. |
| 3 | Consulente digitale | `src/screens/ConsulenteScreen.tsx` | Spiega il profilo e propone il portafoglio modello + il piano tariffario. |
| 4 | Dashboard | `src/screens/DashboardScreen.tsx` | Confronto fra il portafoglio del cliente e il benchmark Proxima. |

La schermata mostrata dipende dallo stato dell'utente (`src/state/AppContext.tsx`):
niente sessione → login; sessione senza questionario → questionario; questionario
senza pacchetto → consulente; tutto completo → **dashboard**. È così che al secondo
accesso si entra direttamente nella dashboard.

## Come viene calcolato il profilo

`src/lib/profilo.ts`. Ogni risposta vale da 0 a 10 punti; i punti sono normalizzati
a 0-100 per area. Il punteggio grezzo pesa tolleranza 40%, orizzonte 35%, capacità 25%.

Sopra al punteggio agiscono i **vincoli di adeguatezza**: l'adeguatezza MiFID non è
una media, un singolo elemento critico abbassa il profilo comunque.

| Condizione | Tetto |
|---|---|
| Serve il capitale entro 2 anni | Conservativo |
| Nessun fondo di emergenza | Prudente |
| Conoscenza < 30/100 | Prudente |
| Tolleranza < 25/100 | Prudente |
| Disinvestimento anticipato molto probabile | Equilibrato |
| Capacità < 30/100 | Equilibrato |

I vincoli applicati vengono mostrati al cliente parola per parola: il salto fra
punteggio grezzo e punteggio finale è sempre spiegato.

## Il "bot"

`src/lib/bot.ts` è un **motore a regole deterministico**, non un modello
linguistico: ogni frase discende dall'esito della profilazione ed è quindi
ricostruibile a posteriori — requisito pratico per una SCF, che deve poter
motivare ogni proposta fatta al cliente.

Il consulente digitale può raccomandare al massimo un gradino sopra il profilo
calcolato, e **nessun gradino sopra** se esiste un vincolo di adeguatezza. Se il
cliente sceglie comunque un pacchetto diverso dalla raccomandazione, la dashboard
lo segnala e il testo rimanda alla conferma scritta con il consulente.

## Dati da sostituire

| Cosa | Dove | Nota |
|---|---|---|
| Autenticazione | `src/state/storage.ts` | Oggi è localStorage. Va sostituita prima di qualunque uso con clienti. |
| Serie di performance | `src/data/performance.ts` | Random walk deterministico seminato dal profilo, non dati reali. |
| Portafogli modello | `src/data/pacchetti.ts` | Allocazioni, rendimenti attesi e TER sono indicativi: da validare. |
| Testi del questionario | `src/data/questionario.ts` | Bozza di prodotto, da far approvare al consulente iscritto OCF. |

I piani tariffari (€250 / €500 / €800 / €1.200) seguono
`PROXIMA-Main/01-strategia/piano-di-lancio/04-revenue-forecast.md`.

## Note di design

I token in `src/styles/tokens.css` riprendono la landing page in
`PROXIMA-Main/05-branding/`: navy `#0D2B4E`, petrolio, oro `#C4A44A`, avorio,
font Plus Jakarta Sans + DM Sans.

I colori delle due serie del grafico (`#0093AB` portafoglio, `#B98A1F` benchmark)
sono derivati dal brand ma **verificati** per banda di luminosità, croma,
separazione per daltonismo (ΔE 17,9) e contrasto sulla superficie. Il grafico ha
legenda, etichette di fine linea, tooltip con crosshair e una vista in tabella
per chi non può leggere il colore.

L'interfaccia è solo in tema chiaro, coerente con il brand avorio.
