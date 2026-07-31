# Pricing Unificato Proxima — Riconciliazione dei tre modelli

> Unifica le tre logiche di prezzo emerse (parcella fissa doc 04 · "% costituzione + oraria" ·
> abbonamenti app Free/Pro/Max) in **un solo listino**, così il modello combinato
> (`cashflow-combinato-24m.md`) smette di trattarle come flussi separati e non c'è doppio conteggio.

---

## 1. Il principio: non tre modelli, ma UN listino su due canali

Le tre logiche descrivono lo **stesso** business visto da angoli diversi. Riconciliate in **tre
componenti**, valide identiche in Fase 1 (SCF human-led, locale) e Fase 2 (app, scala):

| Componente | Cos'è | Quando | Da quale dei 3 modelli arriva |
|---|---|---|---|
| **A · Accesso (ricorrente)** | scala abbonamento Free/Pro/Max | mensile/annuale | parcella doc 04 **+** abbonamenti app |
| **B · Costituzione (una tantum)** | % a scaglioni sul nuovo portafoglio | anno 1, fatturata subito | "% costituzione" **+** "3% app" |
| **C · Ricalibrazione/extra (a consumo)** | oraria, oltre quanto incluso nel tier | on-demand | "oraria alla ricalibrazione" |

**La chiave:** Fase 1 e Fase 2 **non hanno prezzi diversi** — sono **due canali dello stesso listino**.
Un cliente acquisito dal consulente (Fase 1) e uno acquisito dall'app (Fase 2) pagano lo **stesso**
ricorrente + la **stessa** costituzione. Cambia solo il **costo di servirlo** (umano vs AI), che sta nello
strato costi, **non** nei ricavi.

---

## 2. Componente A — Scala abbonamento unica

| Tier | Prezzo | Contenuto | Ruolo Fase 1 (human) | Ruolo Fase 2 (app) |
|---|---|---|---|---|
| **Free** | €0 | insight di mercato, education, visualizzazione performance | lead magnet / pre-qualifica | top-of-funnel di massa |
| **Pro** | €10/mese · €80/anno | self-service: analisi, simulazioni, monitoraggio, Q&A | poco senso human | cuore self-serve dell'app |
| **Max** | €48/mese · €500/anno | consulenza continuativa + chiamate (immediata + trimestrale) | **il cuore della Fase 1**, venduto dal consulente | app + validazione umana |

**Riconciliazione col doc 04:** la "parcella fissa €490/anno" **è** il tier **Max** (€500/anno). Non è un
terzo modello: è lo stesso ricorrente, prima non ancora "tierizzato". Le fasce €250/€500/€800/€1.200 del
doc 04 vanno **archiviate** e sostituite dalla coppia Pro/Max (il prezzo non dipende più dalla fascia di
patrimonio, ma dal **livello di servizio** scelto — più difendibile e coerente col fee-only).

→ Conseguenza sull'ARPU: **l'ARPU €490 del doc 04 è l'ARPU del tier Max**, valido per i clienti-consulenza
di Fase 1 (quasi tutti Max). In Fase 2 l'ARPU **per utente registrato** è più basso (molti Free/Pro) ma su
volumi molto maggiori + il one-off di costituzione.

---

## 3. Componente B — Costituzione portafoglio (una tantum, a scaglioni)

Unifica "% alla costituzione" e "3% app" in **una** tariffa a **scaglioni marginali decrescenti** (risolve
il problema del 3% troppo alto sui patrimoni grandi che avevo segnalato):

| Scaglione di patrimonio | Aliquota marginale |
|---|---|
| fino a €25.000 | **3,0%** |
| €25.001 – €50.000 | **2,0%** |
| €50.001 – €100.000 | **1,0%** |
| oltre €100.000 | **0,5%** |
| *minimo* | *€300* |

**Effetto (una tantum, anno 1):**
| Portafoglio | Costituzione | Aliquota effettiva |
|---|---|---|
| €20.000 | €600 | 3,0% |
| €35.000 | €950 | 2,7% |
| €50.000 | €1.250 | 2,5% |
| €100.000 | €1.750 | 1,75% |
| €200.000 | €2.250 | 1,1% |

Si applica **sia a Pro sia a Max**, solo se c'è da **costituire un portafoglio nuovo**, fatturata subito.
È fee-only a norma (pagata dal cliente, zero retrocessioni); comunicarla come **"parcella una tantum di
pianificazione e impostazione"**, non come "% sul capitale".

> Nel modello app finora usato: 3% **flat**. Adottando gli scaglioni, aggiornare il parametro (il modello
> ha già la leva "portafoglio medio"; basta sostituire il 3% flat con l'aliquota effettiva della fascia
> media — es. ~2,7% su €35K).

---

## 4. Componente C — Ricalibrazione / extra (a consumo)

- **Inclusa** nel Max (check-up trimestrale) e come 1 call nel Pro 6 mesi.
- **Oltre** l'incluso, o per Pro/Free: **tariffa oraria €150–180/h** (add-on). Così l'idea "oraria alla
  ricalibrazione" diventa un **add-on marginale**, non un quarto modello.

---

## 5. Regola anti-doppio-conteggio (per il modello combinato)

1. **Un cliente = un solo tier** (ricorrente) **+ al più una** costituzione (una tantum, anno 1) **+**
   eventuale oraria a consumo.
2. **Fase 1 e Fase 2 non sono ricavi paralleli.** L'app **non** aggiunge un flusso sopra la SCF: **sposta**
   l'acquisizione e il servizio dal canale umano al canale app, (a) **allargando il funnel** (Free→Pro→Max)
   e (b) **abbattendo il costo di servizio** (AI). Lo stesso cliente non va contato due volte.
3. **Implicazione per `cashflow-combinato-24m.md`:** la versione attuale somma "SCF (parcella €490)" +
   "margine app" come flussi additivi — è una **semplificazione da correggere** una volta scelto il mix di
   canale. Interpretazione corretta: dopo il lancio app, i **nuovi** clienti arrivano prevalentemente dal
   canale app (stesso listino, costo di servizio più basso); i clienti Fase 1 **migrano** sul tier Max
   dell'app. Il ricavo non raddoppia: **migliora il margine** (stesso ricavo, meno costo-to-serve) e
   **accelera il volume** (funnel più largo).

---

## 6. Decisioni aperte per i fondatori

1. **Aliquote di costituzione** (§3): confermare scaglioni 3/2/1/0,5% e il minimo €300 (o cap massimo?).
2. **Free ha la costituzione?** Proposta: no — la costituzione presuppone un tier a pagamento (Pro/Max);
   il Free resta puramente informativo. *(Nel modello app la costituzione è già legata ai soli nuovi
   paganti, quindi coerente.)*
3. **Mix di canale nel tempo:** che quota dei nuovi clienti passa dal canale app vs human, mese per mese?
   È il parametro che serve per rifare il combinato **senza doppio conteggio**.
4. **ARPU-target Fase 2:** definire il blended ricorrente per utente registrato (dipende dal mix Free/Pro/Max)
   — sostituisce il €490 flat del doc 04 nei calcoli di massa.

*Prossimo passo tecnico: aggiornare `cashflow-combinato-24m.md` con la logica "canale unico, costo-to-serve
variabile" (punto §5.3) e sostituire il 3% flat con gli scaglioni nel modello app.*
