# 61 — Budget di Lancio: Modello SCF "a Strati" (app + consulenza)

*Proxima — SRL SCF fee-only | 2 fondatori | orizzonte 24 mesi (M-6 → M+18)*
*v1 — 2026-06-10. Costruito dal basso (bottom-up). Dove in conflitto, **aggiorna** le
ipotesi di costo dei doc `12-costi-costituzione.md`, `10-struttura-societaria.md` e
`60-budget-operativo-24m.md` — vedi §1.*

---

## 0. Modello di business (aggiornato)

Proxima incassa **direttamente dal cliente** (fee-only, nessuno split verso terzi). Il
ricavo è ibrido: **abbonamenti** sugli strati 1–2 + **parcella %AUM con bonus** sullo strato 3.

| Strato | Cosa riceve il cliente | Canale | Logica di ricavo |
|---|---|---|---|
| **1** | App gratuita + abbonamento base: consigli **generici per classe di rischio** | App self-service | Abbonamento basso, **volume alto** |
| **2** | Pacchetti di consulenza mirata, anche via **telefono/webcam** | App + remoto | Abbonamento medio / fee a pacchetto |
| **3** | Consulenza **di persona**: analisi profonda di profilo di rischio e patrimonio | In presenza | **Parcella %AUM (0,7–1,2%/anno) + bonus performance** |

L'app è contemporaneamente **top-of-funnel** (acquisizione di massa a basso costo) e
**motore di monetizzazione** degli strati 1–2; lo strato 3 è il margine alto a basso volume.

### ⚠ Vincolo regolatorio sullo strato 3 — leggere prima di mettere a budget l'app

Una SCF **può solo consigliare**. Non può **eseguire ordini** né **detenere somme o
strumenti** del cliente (art. 18-bis, c. 3, TUF). Il cliente esegue **sempre** da sé.

- Questo limite **non è "arginabile"**: è la definizione stessa della SCF. Se Proxima
  eseguisse al posto del cliente servirebbe la **gestione di portafogli** (SIM/SGR), cioè
  il percorso già abbandonato col commercialista.
- Per il cliente poco "avvezzo" la leva è la **UX**, non la deroga: ordini **pre-compilati**
  che il cliente conferma sul *proprio* broker, onboarding assistito, eventuale
  **partnership con un broker** per semplificare apertura conto ed esecuzione.
- Il **bonus/performance fee** è ammesso **solo** se addebitato *al cliente* ed è
  trasparente (MiFID II); mai come incentivo retrocesso da banche/SGR/assicurazioni.

> Implicazione di budget: **non** finanziare lo sviluppo di una funzione di "esecuzione
> ordini" — sarebbe inutilizzabile. Lo strato 3 costa **tempo-uomo qualificato** (CRM +
> processo), non tecnologia. Il grosso del capitale serve per **app (strati 1–2)** e
> **marketing**.

---

## 1. Tre correzioni ai documenti esistenti (riducono il fabbisogno reale)

Prima di sommare, tre numeri errati nei doc attuali vanno corretti — due liberano cassa,
uno la alza:

| # | Doc | Cosa dicono | Realtà | Effetto |
|---|---|---|---|---|
| a | `10`, `RICALIBRAZIONE` | "Capitale sociale minimo **€50.000** per la SCF" | Le fonti specializzate **non** riportano un capitale minimo SCF: il requisito patrimoniale vincolante è la **polizza RC** + indipendenza/professionalità. I €50K sembrano il minimo della **S.p.A.**, non un obbligo SCF. | **Libera €50–90K** di "capitale bloccato": basta una SRL ordinaria capitalizzata a €10–20K. **Da confermare col commercialista.** |
| b | `12`, `60` | Quota OCF "€500–1.000/anno" | Quota annua **società** SCF ~**€3.240/anno** (2025) + €168 tassa gov. una-tantum + ~€350 contributo iscrizione | **+~€2.300/anno** sul ricorrente |
| c | `12` | INPS "gestione commercianti, ~€7.800–8.400/anno" (minimale fisso) | Per attività professionale i soci-amministratori vanno di norma in **Gestione Separata** sul *compenso*, **senza minimale fisso** (aliquota 2026: 26,07% se già altrove assicurati, 33,72% altrimenti) | Con **compenso €0** → INPS **~€0**. **Risparmio fino a ~€8K/anno.** Da confermare col commercialista. |

> Correzione (a) + (c) sono il motivo per cui un avvio "magro" è molto più economico di
> quanto i doc lasciassero intendere.

---

## 2. Pavimento regolatorio — quanto serve solo per *esistere* come SCF

Incomprimibile: senza, non ci si iscrive all'albo.

**Una-tantum (costituzione → iscrizione):**

| Voce | Realistico |
|---|---|
| Notaio + atto costitutivo SRL | €1.500–2.500 |
| CCIAA + bollo + imposta di registro | ~€560 |
| Avvocato (statuto SCF, contrattualistica MiFID II) | €2.000–3.000 |
| Commercialista setup (P.IVA, INPS, comunicazioni) | €1.000–1.500 |
| Esame OCF ×2 + preparazione | €1.000–3.000 |
| Iscrizione OCF (tassa gov. + contributo + bollo) | ~€550 |
| Setup AML/KYC + consulenza compliance iniziale | €1.500–3.000 |
| RC professionale anno 1 (massimale €1M/sinistro; **prima** dell'iscrizione) | €1.500–3.000 |
| PEC + firma digitale | ~€100 |
| **TOTALE pavimento una-tantum** | **~€12.000–16.000** |

**Ricorrente "struttura minima" / anno** (escl. app, marketing, compenso fondatori):

| Voce | Realistico /anno |
|---|---|
| Quota OCF società | ~€3.240 |
| RC professionale (rinnovo, cresce con AUM) | €1.500–3.000 |
| Commercialista ordinaria | €3.600–6.000 |
| Software (CRM, analisi portafoglio, compliance) | €2.400–4.800 |
| AML (formazione + tool) | €500–1.300 |
| Sede (domicilio iniziale → coworking) | €0–7.200 |
| PEC / telefonia / cloud | €1.200–2.400 |
| **TOTALE struttura / anno** | **~€18.000–28.000** (≈ €1.500–2.000/mese) |

---

## 3. Il prodotto digitale è ora la voce centrale

Il driver di budget numero uno. La forchetta dipende da **chi costruisce l'app**.

| Componente | In-house / low-code | Outsourced (agenzia) |
|---|---|---|
| Landing page + sito vetrina + SEO base | €3.000–5.000 | €6.000–9.000 |
| **App Strato 1** (freemium, profilazione rischio, contenuti per classe, paywall abbonamento) | €8.000–18.000 | €25.000–45.000 |
| **App Strato 2** (pacchetti, booking, video-consulto, messaggistica sicura) | €15.000–25.000 | €25.000–45.000 |
| Strato 3 (no app dedicata: CRM + processo + portale cliente leggero) | €5.000–12.000 | €10.000–20.000 |
| Ricorrente: infra/hosting, app store, manutenzione (~15–20%/anno del build), produzione contenuti per classe di rischio | €6.000–12.000/anno | €10.000–18.000/anno |

**Fasatura consigliata (riduce il rischio di capitale):**

1. **M-6 → M-1:** landing + sito + raccolta lista d'attesa. **App Strato 1 MVP.**
2. **M0 → M+6:** lancio Strato 1, validazione domanda e abbonamenti.
3. **M+6 → M+12:** se i numeri reggono, build **Strato 2** (finanziato dalla traction, non a debito).
4. Strato 3 **da subito** ma "manuale" (Calendly + Zoom + CRM); si tooler-izza dopo.

> Regola d'oro: **non costruire l'app Strato 2/3 finché lo Strato 1 non ha validato la
> domanda.** È la differenza tra un fabbisogno da €130K e uno da €230K.

---

## 4. Blocchi di costo (bottom-up, 24 mesi)

| Blocco | Contenuto |
|---|---|
| **A. Costituzione & compliance** | una-tantum, §2 |
| **B. Struttura operativa** | ricorrente §2 × 24 mesi |
| **C. Prodotto digitale** | web + app + infra/manutenzione, §3 |
| **D. Marketing** | preparazione terreno (pre-lancio) + acquisizione (post-lancio), 18 mesi |
| **E. Personale** | fondatori **€0 fino a ~M+12** poi ramp; collaboratori (contenuti/quant, dev, social) |
| **F. Buffer** | contingenza ~12% |

---

## 5. Tre dimensionamenti di cassa (24 mesi, fondatori a €0 all'inizio)

| Blocco | 🟢 **Phased / Lean** | 🔵 **Base / Product** | 🔴 **Scale** |
|---|---|---|---|
| A. Costituzione | €13K | €15K | €17K |
| B. Struttura (24m) | €38K | €46K | €53K |
| C. Prodotto digitale | €29K *(App S1 MVP; S2/S3 manuali)* | €60K *(App S1+S2)* | €107K *(App S1+S2+S3 tooling)* |
| D. Marketing (18m) | €23K *(~€1,3K/mese, organico)* | €54K *(~€3K/mese, paid moderato)* | €99K *(~€5,5K/mese, paid forte)* |
| E. Personale | €14K *(1 collaboratore PT)* | €43K *(comp soci da M+12 + 1–2 collab.)* | €74K *(comp soci da M+9 + 2–3 collab.)* |
| F. Buffer (~12%) | €14K | €27K | €41K |
| **CASSA TOTALE** | **~€115–140K** | **~€200–230K** | **~€280–330K** |
| Break-even operativo atteso | ~M+15 | ~M+11–12 | ~M+9–10 |
| Profilo app | solo Strato 1, alto-touch manuale | Strati 1–2 prodotto vero | Strati 1–3 completi |
| Capitale richiesto | alla portata di 2 autofinanziatori | serve coppia molto capitalizzata **o** investitore | territorio investitore |
| Rischio principale | massa critica clienti più lenta | brucia molto se il CAC non regge | esecuzione + burn elevato pre-validazione |

---

## 6. Raccomandazione

**Parti dal profilo 🟢 Phased / Lean (~€120–140K di cassa), con una regola ferrea:
nessun euro sull'app Strato 2/3 finché lo Strato 1 non valida la domanda.**

Perché:

- Rispetta i due vincoli dichiarati: **capitale non ancora deciso** (tieni il numero
  basso e flessibile) e **compenso fondatori €0** (massimo risparmio di cassa nei primi mesi).
- Il **pavimento regolatorio è basso** (~€14K una-tantum + ~€22K/anno): il resto è scelta,
  non obbligo. Sbagliare in grande sull'app *prima* di validare è l'errore più caro.
- Se lo Strato 1 funziona, lo Strato 2 e la spinta paid si **finanziano dalla traction**
  (o si alza capitale **dopo** avere numeri reali in mano — una raccolta molto più facile).
- Mantiene aperta la strada al Base/Scale senza precludere nulla: è un Base "messo in fase".

**Anti-pattern da evitare:** partire dal Base/Scale (€200K+) costruendo l'app completa e
il paid aggressivo *prima* di sapere se gli italiani <€100K si abbonano davvero a consigli
per classe di rischio. È esattamente l'ipotesi più rischiosa e non validata del piano.

---

## 7. Decisioni ancora aperte (tightening del numero)

1. **Build dell'app: in-house/low-code o agenzia?** È lo swing singolo più grande
   (≈ €30–60K). Se un fondatore sa sviluppare (o si usa un low-code tipo FlutterFlow),
   il Lean scende verso €115K; se tutto in agenzia, sale verso €140K+.
2. **Tetto di capitale dei soci** — una volta scelto il profilo, fissa la riserva
   intoccabile e i trigger di taglio marketing (cfr. doc 60 §Buffer).
3. **Pricing degli strati** (abbonamento S1/S2, %AUM S3) — guida il revenue forecast e
   va inserito nel modello funnel (`02-modello-previsionale/`), da ricalibrare per i
   ricavi a strati (oggi è single-stream %AUM).

---

*Fonti regolatorie/costo (giu 2026): Consultique e Athena SCF (quota OCF €3.240/anno,
massimali RC, assenza di capitale minimo SCF dichiarato); INPS Gestione Separata 2026
(aliquote 26,07% / 33,72%); Reg. MEF 66/2012 (requisiti patrimoniali e assicurativi);
art. 18-bis TUF; DM 206/2008. Importi pratici da confermare col commercialista in fase
di costituzione.*
