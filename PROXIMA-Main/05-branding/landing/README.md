# Landing page Proxima — raccolta lista d'attesa

Versione operativa della landing, evoluta dall'originale Omma
(`../contenuto-zip/index.html`, da **non** modificare: resta come riferimento).

Riscritta in chiave **SCF fee-only** (giugno 2026): niente copy da robo-advisor,
niente cifre di pricing (parcella ancora da decidere), niente contatore finto.

## Cosa contiene

| File | Contenuto |
|---|---|
| `index.html` | Landing completa: hero + waitlist, problema, **calcolatore costi banca**, come funziona, valori, parcella (senza cifre), chi siamo, CTA, footer legale. |
| `privacy.html` | **Bozza** di informativa GDPR. Da completare e far validare a un legale. |

## ✅ Da fare prima di pubblicare

1. **Collegare Brevo** (oggi il form mostra "le iscrizioni si aprono a brevissimo" e non registra nulla):
   1. Crea un account su [brevo.com](https://www.brevo.com) (piano gratuito).
   2. Crea una lista contatti "Lista d'attesa Proxima".
   3. Vai su *Contatti → Moduli (Forms)* e crea un modulo con il solo campo email.
   4. **Attiva il double opt-in** nelle impostazioni del modulo (obbligatorio per noi: GDPR + qualità lista).
   5. Nella scheda "Condividi"/"Integra" copia l'**URL `action`** del modulo (dominio `sibforms.com`).
   6. Incollalo in `index.html` nella costante `BREVO_FORM_ACTION` (cerca `TODO`).
   7. Prova un'iscrizione vera e verifica che il contatto arrivi nella lista e riceva l'email di conferma.
2. **Sezione "Chi siamo"**: inserire nomi, ruoli, bio (2–3 frasi) e possibilmente foto dei due fondatori. Cerca `TODO` in `index.html`.
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

## Tracking (non ancora installato)

Quando servirà misurare il traffico: preferire un'analytics senza cookie
(es. Plausible) per evitare il cookie banner. Aggiungere il pixel Meta solo
quando partiranno le campagne paid — a quel punto servirà anche il banner consensi.
