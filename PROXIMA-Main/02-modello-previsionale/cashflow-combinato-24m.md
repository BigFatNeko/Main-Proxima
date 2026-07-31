# Cash-Flow Combinato Fase 1 (SCF) + Fase 2 (App) — 24 mesi · v2

> **v2 — pricing unificato, canale unico, niente doppio conteggio.** Aggancia il budget operativo SCF
> (`../01-strategia/piano-di-lancio/60-budget-operativo-24m.md`) con il margine dell'app, usando il listino
> unico di `pricing-unificato.md` (ricorrente Free/Pro/Max + costituzione a scaglioni + oraria €100/h).
> Numeri calcolati (`scratchpad/cf2.js`). La v1 additiva è superata.

---

## 1. Fase 1 — Automazione AI del traffico telefonico in entrata

**Il problema:** in Fase 1 arrivano telefonate per **informazioni** e **prenotazione appuntamenti**; con 2
fondatori ogni chiamata persa è un lead perso. **È quasi 100% automatizzabile** perché **non c'è
raccomandazione personalizzata** (attività riservata OCF): solo info + agenda.

**Stack:** (1) **agente vocale AI** sul numero in entrata — risponde 24/7 in italiano, spiega il servizio da
knowledge base, qualifica, **prenota nel calendario dei consulenti**, conferma via WhatsApp/SMS, logga in CRM;
(2) **deflection** con FAQ + booking online + WhatsApp AI; (3) **cattura asincrona** fuori orario → zero lead
persi. **Costo** ~€0,10–0,25/min + €50–150/mese: irrisorio vs un centralinista.

**Guardrail:** l'AI dà **informazioni e prenotazioni**; la **consulenza personalizzata resta
all'appuntamento** col consulente OCF ("per la consulenza ti fisso un appuntamento"). Nel modello: linea
*reception AI* ~€150/mese, che **evita la figura di front-desk**. Impatto € modesto — il valore è
**conversione + servizio 24/7 + fondatori liberi dal telefono**.

---

## 2. Modello v2 — logica e assunzioni

**Principio (da `pricing-unificato.md`):** una **sola base clienti** su **un solo listino**, servita da **due
canali** che si sommano solo perché intercettano clienti **diversi**:
- **Canale human (Fase 1 SCF):** acquisizione locale, **capacità-limitata** (2 fondatori + consulente PT),
  clienti di consulenza → tier **Max** (€500/anno) **+ costituzione** a scaglioni sul nuovo portafoglio.
  Curva nuovi clienti da doc 04, **cap ~30/mese** (la capacità umana); dopo il lancio app scende a ~15–22.
- **Canale app (Fase 2, da M+12):** funnel di massa Free→Pro→Max, nazionale/self-serve → clienti **net-new**
  che il canale umano non raggiungerebbe. Free €0 (no costituzione, solo oraria €100/h), Pro/Max ricorrente +
  costituzione. **Nessun doppio conteggio:** human e app sono flussi distinti.

**Correzione-chiave vs doc 04/60:** i doc precedenti contavano **solo il ricorrente** (parcella €490).
Il listino unificato prevede anche la **costituzione una tantum** (componente B) — che il modello ora
applica **anche ai clienti di Fase 1**. È la voce che cambia il quadro di cassa.

**Assunzioni (scenario base):** costituzione applicata al **45%** dei nuovi clienti human (molti fee-only
vengono per *ottimizzare* un portafoglio esistente, non costituirne uno nuovo) e al **25%** dei nuovi paganti
app · portafoglio medio human €40.000 / app €30.000 · scaglioni 3/2/1/0,5% · AI deflection 75% · costo fisso
app €4.000/mese da M+12 · costi operativi SCF dal doc 60 · cassa a M+0 €122.739 (dopo pre-lancio).

---

## 3. Cash-flow combinato v2 (scenario base)

| Periodo | Ricavo | Costo | Netto | **Cash fine** |
|---|---|---|---|---|
| Q5 · M+0→M+2 | €16.487 | €16.290 | +€197 | €122.936 |
| Q6 · M+3→M+5 | €28.322 | €20.790 | +€7.532 | €130.468 |
| Q7 · M+6→M+8 | €54.681 | €24.290 | +€30.391 | €160.860 |
| Q8 · M+9→M+11 | €67.194 | €28.790 | +€38.404 | €199.264 |
| Q9 · M+12→M+14 *(lancio app)* | €67.825 | €42.962 | +€24.863 | €224.127 |
| Q10 · M+15→M+17 | €82.988 | €47.423 | +€35.565 | €259.692 |
| Q11 · M+18→M+20 | €99.086 | €49.725 | +€49.361 | €309.053 |
| Q12 · M+21→M+24 | €167.439 | €70.518 | +€96.921 | **€405.974** |

**Break-even mensile ~M+1** · **cash minimo ~€121.422** (M+0, non scende mai sotto) · **ARR ricorrente a
M+24 ~€271.638** · a M+24 la base è ~396 Max human + app (Free ~4.236, Pro ~306, Max ~86).

---

## 4. Confronto con il doc 60 — cosa cambia

| Metrica | Doc 60 (solo ricorrente) | **v2 unificato (+ costituzione)** |
|---|---|---|
| Break-even operativo | M+11 | **~M+1** |
| Cash minimo | ~€31.680 | **~€121.422** |
| Cash a M+24 | €115.578 *(colonna incoerente)* / €185.308 *(da burn netto)* | **~€405.974** |

La differenza non è "ottimismo": è la **fee di costituzione che il doc 60 non contava**. Un business fee-only
che incassa la parcella di impostazione **all'avvio** è strutturalmente cash-generativo prima di quanto
mostrasse il piano. ⚠️ Resta da **correggere la colonna "cash residuo" del doc 60** (incoerente col suo stesso
burn netto) e da **aggiungere la costituzione al doc 04**.

---

## 5. Cinque letture strategiche

1. **La costituzione è il motore di cassa; il ricorrente è la rendita.** Il one-off finanzia i primi 24 mesi
   e anticipa il break-even a ~M+1; il ricorrente (ARR ~€272K a M+24) è l'annualità che regge il lungo periodo.
   Stesso pattern visto nell'app: **l'upfront domina all'inizio**.
2. **L'app entro 24 mesi allarga il funnel e aggiunge ~€21.500/mese di ricavo a M+24**, con costo (fisso €4K +
   AI + CAC) facilmente assorbito ora che la cassa è solida. La sua "seconda gobba" della v1 sparisce.
3. **Nessun doppio conteggio:** i clienti human (locali, a capacità) e app (nazionali, self-serve) sono
   distinti; l'app dà **volume incrementale**, non un ricavo duplicato sugli stessi clienti.
4. **La reception AI + AI deflection tengono i costi piatti** mentre i ricavi salgono: il costo trimestrale
   passa da €16K a €70K mentre il ricavo va da €16K a €167K — leva operativa forte.
5. **Con questa cassa, la scelta di lancio app si de-rischia:** a M+12 la cassa è ~€200K → l'app si può
   lanciare senza intaccare il buffer, o anticipare.

---

## 6. Sensibilità — la costituzione è l'assunzione-perno

Il risultato dipende soprattutto dal **tasso di costituzione** (quanti clienti costituiscono un portafoglio
*nuovo*) e dalla **dimensione media** del portafoglio.

| Scenario | Costituz. human / app · portaf. | Break-even | Cash minimo | **Cash M+24** |
|---|---|---|---|---|
| **Base** | 45% / 25% · €40K / €30K | ~M+1 | ~€121K | **~€405.974** |
| **Conservativo** | 25% / 15% · €30K / €22K | ~M+6 | ~€111K | **~€233.679** |

→ Anche nello scenario conservativo il quadro è **nettamente migliore del doc 60** (break-even M+6 vs M+11,
cash M+24 €234K vs €115–185K). Il range di cassa a M+24 è **€234K–€406K**.

---

## 7. Cosa aggiornare a valle

- **Doc 60:** correggere la colonna "cash residuo" (usare il burn netto) e integrare la costituzione.
- **Doc 04:** aggiungere la componente one-off di costituzione (oggi conta solo il ricorrente €490).
- **Modello app (`app-subscription/`):** sostituire il **3% flat** con gli **scaglioni** (3/2/1/0,5%).
- **Decisione aperta residua:** il **mix di canale mese-per-mese** (quota nuovi clienti human vs app) —
  qui assunto (human cap 30→15/mese, app dal M+12); confermare/tarare con i fondatori.
