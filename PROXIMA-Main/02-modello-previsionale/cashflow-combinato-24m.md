# Cash-Flow Combinato Fase 1 (SCF) + Fase 2 (App) — 24 mesi

> Aggancia il **budget operativo SCF** (`../01-strategia/piano-di-lancio/60-budget-operativo-24m.md`,
> revenue da `04-revenue-forecast.md`) con il **margine dell'app** (`app-subscription/`), e include
> l'**automazione AI del traffico telefonico in entrata** in Fase 1. Numeri calcolati (script in
> `scratchpad/combo.js` di sessione); leve dichiarate esplicitamente qui sotto.

---

## 1. Fase 1 — Automazione AI del traffico telefonico in entrata

**Il problema (tuo):** in Fase 1 arriveranno telefonate in entrata per **informazioni sul servizio** e
**prenotazione appuntamenti**. Con 2 fondatori, ogni chiamata persa è un lead perso.

**Perché è quasi 100% automatizzabile:** qui **non c'è raccomandazione personalizzata** (attività
riservata OCF/MiFID) — solo informazioni generali e agenda. Quindi, a differenza della consulenza,
questo strato **non richiede un umano responsabile**.

**Stack consigliato:**
1. **Agente vocale AI (centralino) sul numero in entrata:** risponde 24/7 in italiano, spiega il servizio
   (fee-only, come funziona, prezzi) da una knowledge base, qualifica il chiamante, **prenota
   l'appuntamento direttamente nel calendario condiviso** dei consulenti, invia conferma WhatsApp/SMS/email
   e registra il lead nel CRM. Escalation/richiamata umana solo per casi complessi.
2. **Deflection prima della chiamata:** FAQ chiara sul sito + **widget di prenotazione online** +
   **WhatsApp Business con AI**. Gran parte delle richieste "info + appuntamento" non arriva nemmeno a
   diventare una telefonata.
3. **Cattura asincrona:** overflow/fuori orario → l'AI raccoglie la richiesta, prenota, conferma. **Zero
   lead persi.**

**Costo:** voce AI ~€0,10–0,25/minuto + piattaforma ~€50–150/mese → **irrisorio** vs un centralinista.
**Effetto:** nessuna assunzione front-desk in Fase 1; risposta 24/7 → **più conversione** (per un team di 2
persone le chiamate perse pesano); fondatori liberati dal telefono.

**Il confine da tenere nello script (guardrail):** l'AI dà **informazioni + prenotazioni** (libere); la
**consulenza personalizzata resta all'appuntamento** col consulente OCF. Frase-tipo: *"per la consulenza
personalizzata ti fisso un appuntamento con un consulente"*. L'AI **non** deve dare raccomandazioni
d'investimento personalizzate in chiamata.

**Nel modello** questo è la linea *"reception AI"*: costo ~€150/mese da M+3 e, soprattutto, **evita la
figura di front-desk/VA** (nel budget è previsto un VA a €800/mese da M+15) → saldo **+€650/mese da M+15**.
Impatto € modesto a questa scala: il valore vero è **conversione + servizio + scalabilità**, non il risparmio.

---

## 2. Come si agganciano le due fasi (assunzioni)

| Leva | Valore base |
|---|---|
| **Fase 1 (SCF)** netto mensile | dal doc 60 (burn netto trimestrale, revenue doc 04, parcella €490/anno) |
| **Cash iniziale** | €180.000 |
| **Lancio app (Fase 2)** | **M+12** (dopo il break-even operativo SCF a M+11) |
| **Margine app** | dal modello `app-subscription/` (AI deflection 70%, scenario base) |
| **Reception AI** | −€150/mese da M+3; +€650/mese netto da M+15 (evita il VA) |

> ⚠️ **Nota di riconciliazione col doc 60 — da correggere.** La colonna *"Cash residuo"* del doc 60 è
> calcolata in modo **incongruente**: nei primi trimestri fa `180.000 − costo cumulato` (ignora il revenue),
> in quelli finali aggiunge il revenue in parte → arriva a "€115.578" a M+24. Ricostruendo il cash dalla
> colonna *"Burn netto"* (l'unica coerente: revenue − costi), il **cash Fase-1 a M+24 è ~€185.308**, non
> €115.578. Qui uso la base coerente (~€185.308). **Va sistemata la colonna del doc 60.**

---

## 3. Cash-flow combinato (scenario base)

Valori trimestrali; "cash fine" = liquidità a fine periodo.

| Periodo | Fase 1 (SCF) | App (Fase 2) | Reception AI | Netto | **Cash fine** |
|---|---|---|---|---|---|
| Pre-lancio (M-12→M-1) | −€57.261 | — | — | −€57.261 | €122.739 |
| Q5 · M+0→M+2 | −€12.533 | — | €0 | −€12.533 | €110.206 |
| Q6 · M+3→M+5 | −€12.459 | — | −€450 | −€12.909 | €97.297 |
| Q7 · M+6→M+8 | −€7.711 | — | −€450 | −€8.161 | €89.136 |
| Q8 · M+9→M+11 | −€2.126 | — | −€450 | −€2.576 | €86.560 |
| Q9 · M+12→M+14 | +€8.512 | **−€10.249** | −€450 | −€2.187 | €84.373 |
| Q10 · M+15→M+17 | +€19.996 | −€4.464 | +€1.950 | +€17.482 | €101.856 |
| Q11 · M+18→M+20 | +€27.810 | +€2.254 | +€1.950 | +€32.014 | €133.870 |
| Q12 · M+21→M+24 | +€41.080 | +€15.366 | +€2.600 | +€59.046 | **€192.916** |

**Cash a M+24:** ~€192.916 combinato vs ~€185.308 solo-SCF → **delta app+AI su 24 mesi: solo ~+€7.600.**
**Cash minimo:** ~€84.373 a M+14 (il lancio app crea una **seconda gobba** di burn).

---

## 4. Cinque letture strategiche

1. **L'app, nei primi 24 mesi, è quasi neutra di cassa — il payoff è anno 2-3.** Entro la finestra
   contribuisce solo ~+€2.900 cumulati: nasce con €4.000/mese di costo fisso (dev/infra) + CAC prima che
   ricavi e base installata scalino. Ma il suo margine mensile passa da −€4.000 (mese 0 app) a **~€22.500/mese
   al suo mese 24** (oltre la finestra). **È un investimento di Fase 2, non un tappabuchi di cassa a 24 mesi.**

2. **Il timing di lancio dell'app conta per il runway.** Lanciandola a M+12 (subito dopo il break-even SCF,
   con cassa ancora sottile) si crea una **seconda gobba** che porta il minimo a ~€84K a M+14. Alternative da
   valutare nel modello: **lancio a M+18** (cassa più solida), oppure **MVP lean** (costo fisso app <€4.000)
   finanziato dal cash-flow SCF già positivo.

3. **Il costo fisso app (€4.000/mese) è la leva-perno.** È ciò che rende l'app cash-negativa all'inizio.
   Dimensionarlo (MVP no-code/low-code, infra snella) sposta materialmente break-even e minimo di cassa.

4. **La reception AI in Fase 1 rende poco in € ma molto in conversione.** A questa scala evita ~€650/mese di
   front-desk; il valore vero è non perdere lead (risposta 24/7) e liberare i fondatori — leva di *ricavo*
   indiretta, non di *costo*.

5. **La liquidità regge lo scenario base**, ma il combinato **non** migliora sensibilmente il runway a 24 mesi
   (l'app se lo "mangia" reinvestendo in sé). Il buffer del doc 60 (mai sotto €15–25K) resta valido; la
   seconda gobba da app va coperta con la stessa disciplina.

---

## 5. Caveat — riconciliazione dei modelli di pricing (da decidere)

Sul tavolo ci sono **tre logiche di prezzo** non ancora unificate:
- **Doc 04 (Fase 1):** parcella fissa annua per fascia (ARPU €490/anno).
- **Tua ipotesi recente:** % una tantum alla costituzione + oraria a ricalibrazione.
- **App (Fase 2):** abbonamenti Free/Pro/Max + **3% costituzione** una tantum.

⚠️ **Sovrapposizione:** il "3% costituzione" dell'app è economicamente **lo stesso atto** della costituzione
portafoglio della consulenza SCF. Nel combinato le due fasi sono trattate come **flussi additivi su una
timeline** (SCF fino al lancio app, poi app in aggiunta): utile per il cash-flow, ma **prima del lancio app
va deciso quale pricing prevale** ed evitato il doppio conteggio dello stesso cliente/portafoglio.
Le leve (mese di lancio app, costo fisso app, AI deflection, reception AI) sono tutte regolabili nel modello.
