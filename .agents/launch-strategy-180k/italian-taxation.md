# Fiscalità Italiana — Guida per SRL di Consulenza Finanziaria Indipendente

> Documento di riferimento per Proxima SRL.
> Aggiornato ad aprile 2026. Non sostituisce il parere del commercialista.

---

## 1. Struttura fiscale di una SRL in Italia

Una SRL (Società a Responsabilità Limitata) è un soggetto IRES — paga le tasse a livello societario prima di distribuire utili ai soci. I fondatori che percepiscono uno stipendio o compenso da amministratore pagano l'IRPEF a titolo personale su quell'importo.

| Livello | Soggetto | Imposta principale |
|---------|----------|--------------------|
| Societario | SRL | IRES + IRAP |
| Personale (stipendio) | Fondatori/dipendenti | IRPEF + contributi INPS |
| Personale (dividendi) | Soci | 26% ritenuta secca |

---

## 2. IRES — Imposta sul Reddito delle Società

**Aliquota standard: 24%**

- Base imponibile: utile civilistico rettificato dalle variazioni fiscali (TUIR)
- Deducibili: compensi fondatori, stipendi, contributi INPS, interessi passivi sul mutuo (entro limiti ROL), ammortamenti, costi operativi inerenti
- **Non deducibili (o parzialmente)**: spese di rappresentanza (limite 75%), auto aziendali (limite 20%), compensi in nero

### Pagamento IRES (scadenze)

| Scadenza | Cosa si paga | Importo indicativo |
|----------|-------------|-------------------|
| 30 giugno (anno N+1) | Saldo anno N + 1° acconto anno N+1 (40%) | Variabile |
| 30 novembre (anno N+1) | 2° acconto anno N+1 (60%) | Variabile |

**Primo anno**: nessun acconto. Si paga solo il saldo entro il 30 giugno dell'anno successivo.

**Impatto sul cash flow Proxima**: se l'anno fiscale si chiude in utile (es. anno 2), la prima grossa uscita fiscale arriva a giugno dell'anno successivo. Pianificare una riserva di liquidità pari a ~24% dell'utile annuo stimato.

---

## 3. IRAP — Imposta Regionale sulle Attività Produttive

**Aliquota base: 3,9%** (può variare per regione; Lombardia e alcune regioni hanno aliquote leggermente diverse)

- Base imponibile IRAP ≠ base IRES: è il **valore della produzione netta**
- Per una SRL di servizi: ricavi − costi dei servizi − ammortamenti − alcuni costi del personale
- **Attenzione**: i compensi agli amministratori NON sono sempre deducibili IRAP
- Gli interessi passivi (mutuo) sono esclusi dalla base IRAP

### Formula semplificata per Proxima

```
Base IRAP ≈ Ricavi lordi
           − Costi operativi puri (software, cloud, assicurazione, OCF)
           − Ammortamenti
           [NON si deducono: compensi fondatori/admin, interessi mutuo]
```

**Esempio anno 2 (base scenario)**:
- Ricavi: ~€60.000
- Costi deducibili IRAP: ~€15.000
- Base IRAP: ~€45.000
- IRAP dovuta: ~€1.755 (3,9%)

---

## 4. IVA — Imposta sul Valore Aggiunto

### Esenzione per consulenza finanziaria indipendente

I servizi di **consulenza in materia di investimenti** resi da un consulente finanziario autonomo iscritto all'OCF sono **esenti IVA** ai sensi dell'art. 10, comma 1, n. 4, DPR 633/72 (gestione di fondi comuni, intermediazione finanziaria).

**Attenzione**: l'esenzione si applica se il servizio è strettamente finanziario (analisi, raccomandazioni su strumenti finanziari). Servizi accessori (es. formazione, coaching non finanziario) potrebbero essere soggetti a IVA al 22%.

**Pratica**: emettere parcelle senza IVA, indicando "Operazione esente art. 10 n. 4 DPR 633/72". Aprire comunque partita IVA e presentare dichiarazione annuale.

### Volume d'affari e regime contabile

- Sotto €65.000/anno: possibile regime forfettario (ma incompatibile con SRL)
- SRL: sempre in regime ordinario, contabilità ordinaria obbligatoria

---

## 5. Contributi INPS — Fondatori e Dipendenti

### Fondatori (Gestione Separata INPS)

Se i fondatori percepiscono un compenso da amministratore:
- Aliquota INPS Gestione Separata: **~26,23%** (2026)
- Ripartizione: 2/3 a carico della SRL, 1/3 a carico del fondatore
- Il modello assume `inpsRate: 0.26` applicato a 1/3 del compenso → la SRL paga ~17,5% sul compenso

### Dipendenti

- INPS a carico datore: ~23-30% del lordo
- INPS a carico lavoratore: ~9,19% (trattenuto in busta paga)
- TFR: ~6,91% del lordo (accantonato, non uscita mensile)

**Costo reale di un dipendente da €2.500 lordi/mese**:
- INPS datoriale: ~€750
- TFR: ~€173
- **Costo totale SRL: ~€3.423/mese**

---

## 6. Mutuo — Deducibilità degli Interessi

### Deducibilità IRES

Gli interessi passivi su mutuo sono deducibili ai fini IRES entro il limite del **30% del ROL** (Risultato Operativo Lordo = EBITDA fiscale).

- Nei primi anni (EBITDA negativo o zero): gli interessi potrebbero non essere deducibili → si riportano agli anni successivi
- Appena l'azienda raggiunge un EBITDA positivo, si recuperano gli interessi non dedotti in precedenza

### Esempio mutuo Proxima (€180.000 al 5,40%)

| Periodo | Pagamento | Composizione |
|---------|-----------|-------------|
| Mesi 1-18 (pre-ammortamento) | €810/mese | Solo interessi |
| Ogni 6 mesi | €4.860 | Interessi semestrali |
| Dal mese 19 in poi | ~€3.418/mese | Quota capitale + interessi (piano 60 mesi) |

> **Nota**: il calcolo dell'utente di €2.400 ogni 6 mesi si avvicina a un capitale di ~€89.000 al 5,40%. Con €180.000 il semestrale è ~€4.860. Verificare con la banca l'importo esatto — potrebbe variare se il tasso è applicato su base diversa (es. 360 giorni commerciali vs 365).

### Non deducibilità IRAP

Gli interessi passivi **non sono deducibili** ai fini IRAP. Il costo del mutuo abbatte solo la base IRES, non quella IRAP.

---

## 7. Dividendi — Tassazione dei Soci

Quando la SRL produce utile e i soci vogliono distribuirlo:

- **Ritenuta a titolo definitivo: 26%** sull'importo distribuito (art. 27 DPR 600/73)
- La SRL funge da sostituto d'imposta: trattiene il 26% e versa all'Erario
- Il socio non deve dichiarare il dividendo nella propria IRPEF

**Strategia comune per i fondatori**: tenere basso il compenso da amministratore (per ridurre INPS) e distribuire utili come dividendi — ma attenzione: l'Agenzia delle Entrate può riqualificare dividendi sproporzionati come reddito da lavoro.

---

## 8. Impatto sulla Strategia di Lancio Proxima

### Timeline fiscale attesa

| Evento | Timing stimato | Importo indicativo |
|--------|---------------|-------------------|
| Prima dichiarazione IVA | Aprile anno 2 | 0 (esenzione) |
| Prima IRAP | Giugno anno 2 | ~€500-800 |
| Primo IRES | Giugno anno 3 | Solo se utile anno 2 |
| Primo acconto IRES | Giugno anno 3 | 40% dell'IRES anno 2 |

### Cash flow: impatto pagamento differito parcella

Se la parcella viene pagata dopo 12 mesi dall'acquisizione del cliente:
- I primi 12 mesi post-lancio (M0→M+11): **zero ricavi** dalla gestione
- L'utile imponibile rimane negativo → nessun IRES, nessuna IRAP significativa
- Il break-even operativo si sposta di 12-18 mesi rispetto al modello senza differimento
- Il cash minimum scende più in basso → riserva di liquidità più critica

**Raccomandazione**: con pagamento differito e mutuo attivo, mantenere almeno €40.000-50.000 di riserva minima nel cash flow model.

### Stima tasse cumulative (scenario base, nessun differimento)

| Anno | Utile stimato | IRES (24%) | IRAP (3,9%) | Totale |
|------|--------------|-----------|------------|--------|
| Anno 1 (M-12→M0) | -€85.000 | €0 | €0 | €0 |
| Anno 2 (M+1→M+12) | -€20.000 | €0 | ~€800 | ~€800 |
| Anno 3 (M+13→M+23) | +€45.000 | ~€10.800 | ~€2.500 | ~€13.300 |

---

## 9. Adempimenti Periodici

| Frequenza | Adempimento | Chi lo gestisce |
|-----------|-------------|-----------------|
| Mensile | F24 INPS dipendenti | Commercialista |
| Mensile | Buste paga | Consulente del lavoro |
| Trimestrale | Liquidazione IVA (se dovuta) | Commercialista |
| Annuale | Dichiarazione IVA (aprile) | Commercialista |
| Annuale | IRAP + IRES (giugno) | Commercialista |
| Annuale | Bilancio civilistico + deposito CCIAA | Commercialista |
| Annuale | Modello 770 (sostituto d'imposta) | Commercialista |

**Costo stimato commercialista**: €400-600/mese per una SRL piccola con 2-5 dipendenti (già incluso nei costi operativi del modello a €400/mese).

---

## 10. Riferimenti Normativi

- **IRES**: TUIR (DPR 917/1986), art. 72-161
- **IRAP**: D.Lgs. 446/1997
- **IVA esenzione servizi finanziari**: DPR 633/1972, art. 10, c. 1, n. 4
- **Dividendi**: DPR 600/1973, art. 27
- **Consulenza finanziaria indipendente**: D.Lgs. 58/1998 (TUF), art. 18-bis; Regolamento OCF
- **Deducibilità interessi passivi**: TUIR art. 96
