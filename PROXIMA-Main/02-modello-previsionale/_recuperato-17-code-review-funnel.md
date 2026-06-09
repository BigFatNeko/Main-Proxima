> **MATERIALE RECUPERATO** — code review del funnel *agente-collegato* (`proxima-funnel-ac.html`).
> Base tecnica per ricalibrare il modello in versione **SCF fee-only**: vedi `RICALIBRAZIONE-SCF.md`.
> Nota chiave: nel modello SCF NON esiste `proximaSplit` (la SCF trattiene il 100% della parcella).

---

# 17 — Code Review: proxima-funnel-ac.html

## Struttura del codice

Il file è un single-page application da 1.597 righe, completamente autocontenuto.
Dipendenze esterne caricate via CDN: React 18, Recharts 2, Babel standalone.
Nessun bundler — il browser compila JSX al volo. Scelta pragmatica per un tool
interno: zero toolchain, zero deploy, funziona con doppio click.

Architettura logica in tre strati:

**Strato 1 — Model (righe ~200–520)**
Funzioni pure JavaScript (ES5 per compatibilità). `defaultParams()` definisce
tutti i parametri di input. `simulate(p, months)` è il motore: loop mese per mese
da M-12 a M+23, calcola clienti, costi, ricavi, cash, hiring. Restituisce un array
di oggetti risultato e alcune metriche aggregate (break-even, CAC, cash minimo).

**Strato 2 — Controls (righe ~700–870)**
Componenti React che rendono gli slider. Ogni slider usa `S([path], label, min, max,
step, formatter)` — un helper che legge e scrive via `update([path], value)`,
il quale fa un deep-clone dei params e triggera re-render. Pattern semplice, efficace.

**Strato 3 — Dashboard (righe ~900–1.550)**
Componenti React che leggono il risultato di `simulate()` e lo rendono come KPI,
grafici Recharts e tabella mensile. Tutti stateless — ricevono i dati, li stampano.

Il flusso di dati è unidirezionale: params → simulate() → dashboard.
Ogni modifica a uno slider ri-esegue simulate() intero (36 iterazioni, ~1ms) e
aggiorna tutto il DOM via React. Funziona bene a questa scala.

---

## Bug e problemi del modello per SRL agente collegato

### BUG 1 — Slider "Parcella media" disconnesso dal calcolo (alta priorità)
Il pannello "Parcelle e abbandoni" mostra ancora lo slider `arpu` (€374).
Ma la formula del revenue è stata cambiata: `mrr = payingClients * curAUM *
feeRate * proximaSplit / 12`. Il parametro `p.arpu` non viene più letto da nessuna
parte nel calcolo. L'utente muove lo slider e non succede nulla — comportamento
silenziosamente sbagliato. Va rimosso e sostituito con i veri driver del revenue.

### BUG 2 — sp500Annual usato sia come rendimento portafoglio sia come benchmark (alta priorità)
Il parametro `aum.sp500Annual` serve due scopi distinti:
1. Calcolare la crescita dell'AUM dei clienti nel tempo (ora 7%, corretto per un portafoglio bilanciato)
2. Tracciare il benchmark "S&P 500" nel grafico AUM (dovrebbe essere ~10%)

I due valori coincidono per definizione con il parametro attuale, quindi il grafico
confronta il portafoglio con... sé stesso. Il benchmark non ha senso. Serve
un parametro separato `sp500Benchmark` (default 10%) per il confronto grafico.

### BUG 3 — AUM growth: tutti i clienti trattati come se fossero entrati a M0 (media priorità)
La formula corrente:
```
msl = Math.max(0, m - 13)   // mesi dal lancio
curAUM = avgPerClient * (1 + r)^msl + (contributions/12) * msl
```
Questo dà a ogni cliente esistente la crescita piena dal lancio, indipendentemente
da quando si è iscritto. Un cliente entrato a M+20 viene trattato come se avesse
23 mesi di rendimento invece di 3. Sovrastima l'AUM dei cohort recenti.

Fix semplice: usare `msl/2` come età media del portafoglio (i clienti sono
distribuiti nel tempo, la media è a metà del periodo). Errore residuo <5%.

### BUG 4 — Contributi annui non capitalizzano (bassa priorità)
`(annualContributions/12) * msl` somma i versamenti in modo lineare senza
applicarvi il rendimento di mercato. Sottostima leggermente l'AUM finale.
Per un modello semplificato è accettabile, ma si nota su orizzonti >36 mesi.

### PROBLEMA 5 — Mancano slider per feeRate, proximaSplit, annualContributions
I tre parametri che guidano il revenue nel modello AC non hanno controlli UI.
L'utente non può fare scenari "cosa succede se la SIM mi dà 45% invece di 50%"
o "cosa succede se alzo la fee all'1.5%". Sono le leve più importanti del modello.

### PROBLEMA 6 — Label e titoli del pannello non aggiornati al modello AC
- Pannello: "Parcelle e abbandoni" → dovrebbe essere "Ricavi AUM e abbandoni"
- Slider sp500Annual: etichettato "Rendimento annuo benchmark (S&P 500)" ma
  ora rappresenta il rendimento del portafoglio gestito, non il benchmark
- Checkbox deferredFees: dice "Prima parcella dopo 12 mesi" — linguaggio
  da flat fee, non applicabile a un modello % AUM

---

## Piano di fix (in ordine di impatto)

| # | Fix | Impatto sul modello | Complessità |
|---|-----|---------------------|-------------|
| 1 | Rimuovere slider arpu, aggiungere feeRate + proximaSplit + annualContributions | Alto — abilita scenari chiave | Bassa |
| 2 | Separare sp500Annual (portafoglio) da sp500Benchmark (confronto grafico) | Medio — corregge il grafico AUM | Bassa |
| 3 | Fix AUM growth con msl/2 | Medio — corregge sovrastima AUM | Bassa |
| 4 | Aggiornare label e titolo pannello | Zero sul calcolo, alto sulla UX | Minima |
| 5 | Contributi con capitalizzazione | Basso su 36 mesi | Media |
