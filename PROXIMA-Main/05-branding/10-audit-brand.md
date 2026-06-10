# Audit di brand — Proxima (giugno 2026)

**Scopo:** verificare quali asset di brand esistenti reggono nel nuovo assetto
**SCF fee-only** (Albo OCF Sez. III, art. 18-bis TUF), quali vanno ricalibrati e
quali vanno abbandonati. È la base per le fasi successive (ricerca competitor,
identità visiva, brand strategy SCF).

**Contesto chiave:** il materiale di brand esistente è stato prodotto **prima**
della decisione di giugno 2026 di percorrere la strada SCF. Riflette in parte un
posizionamento da *fintech di gestione del risparmio* (app, fee di gestione,
performance fee) che una SCF **non può** né offrire né comunicare.

---

## 1. Inventario degli asset esistenti

| Asset | Dove vive | Data/versione |
|---|---|---|
| Landing page waitlist | `contenuto-zip/index.html` (generata con Omma) | pre-giugno 2026 |
| Brand strategy & messaging (sez. 5) | `03-marketing/strategia/proxima-marketing-strategy.md` | v1.0, maggio 2026 |
| Valori di brand (6) | landing + marketing strategy | — |
| Palette + tipografia | landing + marketing strategy, sez. 5.5 | — |
| Tagline "Oltre i limiti comuni" | landing + marketing strategy | — |
| Analisi competitor SCF | `01-strategia/competitor/40-analisi-competitor-scf.md` | aprile 2026 |

---

## 2. ✅ DA TENERE — regge nel mondo SCF

Questi asset sono indipendenti dal veicolo societario e restano validi:

- **Nome "Proxima"** — evoca vicinanza ("la stella più vicina"), coerente con la
  promessa di consulenza accessibile. ⚠ Da verificare in fase 2: conflitti di
  naming nel settore finanziario italiano (marchi simili, SGR/società esistenti).
- **I 6 valori**: trasparenza, disciplina, accessibilità, semplicità, solidità,
  abitudine. Sono valori da *consulente*, non da *gestore* — anzi, calzano
  meglio ora. (Unica nota: vedi "abitudine/gamification" in sez. 3.)
- **Personalità di brand** (marketing strategy, sez. 5.2): onesto non iper-positivo,
  competente non condiscendente, caldo non commerciale, disciplinato non noioso.
  Perfettamente adatta a una SCF che vende fiducia.
- **Tone of voice** (sez. 5.4): tu non Lei, numeri concreti, niente gergo senza
  traduzione, niente superlativi, niente immaginario da ricchezza esclusiva.
  Da tenere integralmente.
- **Messaggio hero**: *"I tuoi risparmi meritano di crescere. Non di restare
  fermi."* — non implica gestione, funziona anche per la consulenza.
- **Messaggi anti-barriera riutilizzabili**:
  - "Non devi diventare un esperto. Devi trovare qualcuno di cui fidarti."
  - "Sai sempre quanto paghi. E perché." (anzi: ancora più vero nel fee-only)
  - "Investire è un processo, non una scommessa."
- **Identità visiva di base**: Navy `#0D2B4E`, Petrolio `#1D4A52`, Gold `#C4A44A`,
  Avorio `#F5F3EE`; Plus Jakarta Sans (titoli) + DM Sans (testo); whitespace,
  oro usato con parsimonia, fotografia di persone italiane reali. Distintiva nel
  panorama SCF (vedi fase 2) e coerente con "serietà senza arroganza".
- **Posizionamento di fondo**: consulenza seria per chi ha meno di €100K ed è
  ignorato sia dalle SCF tradizionali (>€500K) sia dalle banche.

---

## 3. 🔧 DA RICALIBRARE — buona sostanza, forma da aggiornare

| Asset | Problema | Direzione di ricalibrazione |
|---|---|---|
| **Brand promise** *"We grow your money the same way we would grow our own"* | "Grow your money" implica gestione: una SCF **consiglia**, non fa crescere direttamente i soldi del cliente. In più è in inglese. | Riformulare in chiave advisory, es. *"Ti consigliamo come consiglieremmo noi stessi."* (da definire in fase 4) |
| **Mission** *"Make wealth-building a habit, not a privilege"* | Concetto giusto, lingua sbagliata (il ToV vieta inglese forzato). | Tradurre/adattare in fase 4. |
| **"Si parte da €50 al mese"** | Era il conferimento minimo del prodotto di gestione. Una SCF non raccoglie conferimenti: il cliente paga una **parcella**. | Trasformare nel messaggio "consulenza accessibile": la cifra diventerà la parcella d'ingresso (dipende dalla decisione pricing, D1). |
| **"Solido come una banca privata. Accessibile come un'app."** | L'app non è più il prodotto; resta al massimo un portale di supporto. | Mantenere la struttura del contrasto, sostituire il secondo termine (es. "alla portata di tutti"). Decisione D2. |
| **Valore "Abitudine" + gamification** | La gamification era una feature dell'app. Nella SCF l'abitudine resta centrale (PAC, piani d'accumulo, check-in periodici col consulente) ma non è più "meccanica di prodotto". | Tenere il valore, riscrivere la spiegazione: l'abitudine la costruisce la *relazione di consulenza*, non i badge. |
| **Tagline "Oltre i limiti comuni"** | Non ha problemi di compliance, ma è astratta e va stress-testata contro il naming/messaging dei competitor. | Confermare o rivedere dopo la fase 2. Decisione D4. |
| **Numeri e obiettivi nel marketing strategy doc** | 50.000 utenti / 120.000 utenti / CAC €80 / "AUM-generating users": metriche da fintech B2C. Il piano SCF parla di 500–600 clienti a M18, CAC <€70–120. | Il doc `proxima-marketing-strategy.md` va segnato come **v1 pre-SCF** e ricalibrato dopo la fase 4. |

---

## 4. ❌ DA BUTTARE — incompatibile con la SCF

### 4.1 La struttura fee della landing (critico)

La landing comunica:

> "Fee di gestione annua 0,5%" + performance fee a scaglioni
> ("se rende il 5% → +0,5% … oltre il 20% → +5%")
> "Paghiamo di più solo quando guadagni di più."

Tutto questo è **da rimuovere integralmente**:

1. Una SCF **non ha "fee di gestione"**: non gestisce patrimoni. Incassa una
   parcella di consulenza pagata direttamente dal cliente (vedi
   `02-modello-previsionale/RICALIBRAZIONE-SCF.md`).
2. Le **performance fee sul rendimento del portafoglio** presuppongono una
   gestione che la SCF non esercita, e contraddicono il principio fee-only
   (la remunerazione non deve dipendere dai prodotti né dai risultati di
   investimento: è ciò che garantisce l'assenza di conflitto di interessi —
   il cuore del nostro stesso pitch).
3. È anche **incoerente internamente**: l'analisi competitor posiziona Proxima a
   "€250–490/anno fisso", la landing dice "0,5% annuo", la ricalibrazione del
   modello lascia la decisione aperta. → Decisione D1, da chiudere prima della
   fase 4.

### 4.2 Linguaggio da gestione patrimoniale (critico, anche compliance)

Frasi della landing da eliminare o riscrivere radicalmente:

- *"Ti costruiamo un piano … con trasparenza totale sulle fee e sulle scelte che **facciamo**"*
- *"**Monitoriamo, ribilanciamo**, ti aggiorniamo"*
- *"Tre passi. Poi **ci pensiamo noi**."*

Una SCF **raccomanda**; è il cliente che esegue presso la propria banca/broker.
Comunicare "ci pensiamo noi / ribilanciamo" descrive un servizio di gestione che
Proxima non può legalmente prestare (art. 18-bis TUF: la SCF non detiene somme o
strumenti dei clienti e non gestisce). Pubblicare la landing così com'è
esporrebbe a rilievi OCF/Consob oltre a creare aspettative sbagliate.

Il flusso "tre passi" si salva cambiando il terzo passo: da "ci pensiamo noi" a
qualcosa come "tu esegui, noi ti accompagniamo" (revisioni periodiche,
ribilanciamenti **consigliati**, aggiornamenti).

### 4.3 Framing "fintech savings platform"

Il titolo stesso dello zip (`proxima-italian-fintech-saving.zip`) e il framing
del marketing strategy doc ("Proxima SRL enters the Italian fintech market")
appartengono al percorso abbandonato. Proxima non è una fintech che lancia
un'app: è una **società di consulenza finanziaria indipendente** con strumenti
digitali. La differenza non è cosmetica: cambia categoria competitiva
(non MoneyFarm ma IoInvesto/Consultique), aspettative del cliente e regole di
comunicazione.

---

## 5. Vincoli di compliance sulla comunicazione (da rispettare in tutte le fasi)

- **"Consulenza su base indipendente"** è un'etichetta regolata (MiFID II):
  usarla è un vantaggio competitivo ma comporta requisiti precisi (ampia gamma
  di strumenti valutati, no incentivi trattenuti).
- **Niente promesse o proiezioni di rendimento** nel materiale promozionale
  senza i dovuti caveat; mai "rendimenti garantiti".
- Le comunicazioni devono essere **chiare, corrette e non fuorvianti**: vietato
  suggerire servizi non prestati (gestione, custodia).
- Indicare correttamente l'iscrizione all'Albo OCF Sez. III una volta ottenuta;
  prima dell'iscrizione, **non** presentarsi come SCF operativa (la waitlist può
  dire "prossimamente", non raccogliere mandati).

---

## 6. Decisioni aperte (bloccanti per le fasi 3–4)

| # | Decisione | Opzioni | Impatto sul brand |
|---|---|---|---|
| **D1** | Modello di parcella | Fissa annua / % su AUM advisory (0,7–1,0%) / ibrida | Determina il messaggio-pilastro "Sai sempre quanto paghi". La parcella fissa è la più differenziante e la più facile da comunicare; la % su AUM rende di più su patrimoni alti ma assomiglia al pricing dei gestori. |
| **D2** | Ruolo di app/portale | Portale clienti di supporto / nessuna app al lancio | Decide se "accessibile come un'app" sopravvive e quanto pesa il digitale nell'identità. |
| **D3** | Volto del brand | Brand aziendale / personal brand dei 2 fondatori / ibrido | Nel segmento <€100K vincono i personal brand (IoInvesto docet). Una SCF "senza volto" parte svantaggiata sui social. |
| **D4** | Tagline | Confermare "Oltre i limiti comuni" / evolvere | Da decidere dopo la ricerca competitor (fase 2). |

---

## 7. Sintesi

Il brand Proxima ha **fondamenta solide e riutilizzabili** (nome, valori,
personalità, tono di voce, identità visiva, messaggio hero) e **uno strato
superficiale da rifare** (tutto ciò che descrive il *servizio*: pricing, "come
funziona", promessa operativa). La buona notizia: ciò che va buttato è ciò che
costava meno costruire; ciò che resta è ciò che richiede anni (fiducia, tono,
posizionamento).

Prossimo passo → **fase 2**: ricerca su come si presentano oggi le SCF italiane
(`20-ricerca-branding-competitor.md`).
