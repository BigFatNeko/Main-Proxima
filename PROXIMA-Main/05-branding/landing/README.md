# Landing page Proxima — raccolta lista d'attesa

Versione operativa della landing, evoluta dall'originale Omma
(`../contenuto-zip/index.html`, da **non** modificare: resta come riferimento).

Riscritta in chiave **SCF fee-only** (giugno 2026): niente copy da robo-advisor,
niente cifre di pricing (parcella ancora da decidere), niente contatore finto.

## Cosa contiene

| File | Contenuto |
|---|---|
| `index.html` | Landing completa: hero con mockup app animato, problema, **calcolatore banca vs indipendente**, come funziona, vetrina app + valori, parcella (senza cifre), team (senza nomi), CTA "accesso anticipato", footer legale. |
| `privacy.html` | **Bozza** di informativa GDPR (incl. sezione cookie). Da completare e far validare a un legale. |
| `fonts/` | Font self-hostati (woff2). **Non** reintrodurre il link a Google Fonts: caricarli da Google trasmette l'IP dei visitatori a terzi (problema GDPR). |
| `_headers` | Header di sicurezza per Netlify (CSP, no-frame, nosniff…). Su altri hosting vanno replicati. |

### Scelte di persuasione applicate (e i loro limiti)

- CTA in prima persona e benefit-led ("Avvisami al lancio", "Riserva il mio posto").
- Loss aversion: il calcolatore ancora il costo della banca prima della richiesta email.
- Scarsità **vera**: "primi posti limitati" = fase Alpha a clienti controllati del piano di lancio. Se la fase cambia, aggiornare il testo.
- Risk reversal: "gratis / 10 secondi / cancellati quando vuoi".
- Micro-impegno: l'interazione con gli slider precede la richiesta di iscrizione.
- **Vietato** aggiungere contatori o testimonianze finte: solo numeri reali.

## ✅ Da fare prima di pubblicare

1. **Collegare Brevo** (oggi il form mostra "le iscrizioni si aprono a brevissimo" e non registra nulla):
   1. Crea un account su [brevo.com](https://www.brevo.com) (piano gratuito).
   2. Crea una lista contatti "Lista d'attesa Proxima".
   3. Vai su *Contatti → Moduli (Forms)* e crea un modulo con il solo campo email.
   4. **Attiva il double opt-in** nelle impostazioni del modulo (obbligatorio per noi: GDPR + qualità lista).
   5. Nella scheda "Condividi"/"Integra" copia l'**URL `action`** del modulo (dominio `sibforms.com`).
   6. Incollalo in `index.html` nella costante `BREVO_FORM_ACTION` (cerca `TODO`).
   7. Prova un'iscrizione vera e verifica che il contatto arrivi nella lista e riceva l'email di conferma.
2. **Sezione "Chi siamo"**: per scelta è sul team (senza nomi). Verificare che le partnership con commercialisti citate esistano davvero prima di pubblicare.
3. **Footer legale**: P.IVA, sede legale, email di contatto reale (oggi `info@proxima.example`).
4. **Privacy**: completare i campi evidenziati in `privacy.html` e farla validare; poi rimuovere il banner BOZZA.
5. **Dominio e hosting**: la pagina è statica, va bene qualsiasi hosting (Netlify, Vercel, GitHub Pages). Test locale: `npx serve .`

## Regole di compliance (non derogabili)

- **Nessuna cifra di pricing** finché la parcella SCF non è decisa
  (vedi `../../02-modello-previsionale/RICALIBRAZIONE-SCF.md`). Quando sarà decisa,
  aggiornare la sezione "La parcella".
- **Nessuna promessa di rendimento.** Il calcolatore confronta solo i costi, con
  ipotesi dichiarate in pagina (crescita illustrativa 4% annuo): non trasformarlo
  in un simulatore di guadagni.
- La SCF **consiglia soltanto**: mai usare verbi come "gestiamo", "investiamo per te",
  "ribilanciamo noi". I soldi dei clienti non passano mai da Proxima.
- Finché l'iscrizione **OCF Sez. III** non è perfezionata, la pagina resta in modalità
  lista d'attesa (nessuna offerta di servizi). Al perfezionamento, aggiornare il
  footer con il numero di iscrizione.
- Niente social proof inventata (il contatore "1.847 in lista" dell'originale è stato
  rimosso apposta). Si possono mostrare solo numeri veri.

## Cookie e tracciamento (predisposti, NON attivi)

GA4 e Meta Pixel sono già integrati ma **dormienti**: si attivano solo
inserendo gli ID in `index.html` (`ANALYTICS_GA4_ID`, `META_PIXEL_ID`).
Finché gli ID sono vuoti: zero cookie, zero banner, zero script esterni.

### Per attivarli

1. Creare la proprietà GA4 (analytics.google.com) → copiare l'ID `G-…`.
2. Creare il pixel in Meta Events Manager (business.facebook.com) → copiare l'ID numerico.
3. Incollare gli ID nelle due costanti in `index.html`. Da quel momento il banner
   appare alla prima visita e gli script partono **solo dopo il consenso**, per categoria.
4. In `privacy.html`, sezione 5: rimuovere il placeholder iniziale e inserire l'ID GA4.

### Obblighi che scattano all'attivazione

- Il banner deve restare com'è: "Rifiuta tutti" facile quanto "Accetta tutti",
  scelte granulari, link "Preferenze cookie" nel footer per cambiare idea (Garante,
  Linee guida cookie 2021).
- Privacy aggiornata **prima** dell'attivazione (sezione 5 già pronta).
- In GA4: disattivare Google Signals e ridurre la conservazione dati al minimo (2 mesi).
- Per Meta Pixel: accettare l'addendum contitolarità nel Business Manager.
- Il consenso è salvato nel browser dell'utente (`localStorage`): per registri di
  consenso "audit-proof" valutare un CMP commerciale (es. Iubenda, ~€30/anno,
  genera anche la cookie policy).
- I numeri saranno parziali: solo chi acconsente (~60–80%) viene tracciato.
  Per dati di traffico completi senza consenso, affiancare un'analytics
  cookieless (es. Plausible).
