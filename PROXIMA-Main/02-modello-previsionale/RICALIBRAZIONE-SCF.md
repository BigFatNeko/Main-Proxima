# Ricalibrazione del modello previsionale per la SCF (fee-only)

> **STATO (11/06/2026): FATTA.** La versione SCF canonica è
> **`proxima-funnel-scf.html`** (single-file): modello **"a strati"** su 48 mesi
> (M-6 → M+41) — S1 app freemium → S2 pacchetti remoti → S3 consulenza in
> presenza, con parcella S3 selezionabile (%AUM / fissa / modulare). Ricavo
> fee-only diretto dal cliente, senza split. Include in fondo il box **"Stato
> lavori"** (recap fatto/da fare cliccabile, salvato nel browser). Restano da
> **validare sul campo le assunzioni di conversione**. Il resto di questo
> documento è il razionale originale.

Il modello funnel esiste ora in queste versioni:

| Versione | File | Note |
|---|---|---|
| **SCF a strati (attuale)** | `proxima-funnel-scf.html` | **La versione da usare.** 48 mesi, 3 strati, parcella S3 esplorabile, box "Stato lavori". |
| Base (storica) | `funnel-model/` (`proxima-funnel.html`, `model.js`) | Modello a parcella €490/anno, pre-decisione strati. Riferimento. |
| Fasce v1 (rimossa) | `funnel-model-scf/` — solo in storia git (commit `1910deb`) | Prototipo a fasce fatto in sessione, superato dal modello a strati. |
| Agente collegato ("-ac") | `../99-archivio/modello-sim-agente-collegato/funnel-agente-collegato/` | Motore con logica **provvigionale verso la SIM** → non usare. |

## Differenza chiave: niente `proximaSplit`

Nel modello agente-collegato il ricavo era:

```
mrr = payingClients * curAUM * feeRate * proximaSplit / 12
```

dove `proximaSplit` era la quota che la SIM girava a Proxima.

**Nella SCF non esiste alcuno split:** la SCF incassa **direttamente dal cliente**
la propria parcella e ne trattiene il 100%. Quindi:

```
mrr = payingClients * curAUM * feeRate / 12          # se fee % su AUM
# oppure
mrr = payingClients * parcellaAnnua / 12             # se fee fissa
```

> ~~Decisione da prendere: modello di parcella **% su AUM** (es. 0,7–1,0%/anno),
> **fissa annua**, o **ibrido**.~~ → **DECISO (10/06/2026): abbonamento fisso a
> strati** (S1 app €1–5 / S2 remoto €5–20 / S3 in presenza €50–150 al mese,
> indicativi; per S3 il modello permette di esplorare anche %AUM e modulare).
> Implementato in `proxima-funnel-scf.html`. Razionale di brand in
> `05-branding/40-brand-strategy-scf.md`, sez. 2.

## Cosa portare dalla versione "-ac" (migliorie motore)

Dal code review (`../99-archivio/modello-sim-agente-collegato/17-code-review-funnel.md`), sono utili e
indipendenti dal tipo di società:

1. **Cohort AUM** — i clienti non sono tutti entrati a M0: usare età media del
   portafoglio (`msl/2`) invece di crescita piena dal lancio.
2. **Benchmark separato** — distinguere `sp500Annual` (rendimento portafoglio
   gestito) da `sp500Benchmark` (~10%, solo per il grafico di confronto).
3. **Stagionalità / prelievi / shock di mercato** — già implementati nel motore -ac.
4. **Slider mancanti** — esporre `feeRate` e `contributi` come leve; rimuovere lo
   slider `arpu` (disconnesso dal calcolo) e aggiornare le etichette al modello fee-only.

## Allineare i costi alla realtà SCF

La base costi va allineata ai numeri SCF (non SIM):

- Capitale sociale **€50.000** versato (requisito Albo OCF Sez. III).
- **RC professionale** obbligatoria (costo ricorrente).
- Diritto iscrizione/vigilanza OCF (~€600–800/anno) + rinnovo.
- Esame OCF + onorabilità/professionalità dei soci.
- Commercialista, contabilità ordinaria (la SRL non accede al forfettario).
- **Rimuovere** i costi tipici del percorso SIM (integrazione tech SIM, ecc.).

## Output atteso

- `proxima-funnel-scf.html` (single-file, come gli altri).
- Revenue forecast coerente con `01-strategia/piano-di-lancio/04-revenue-forecast.md`
  e `60-budget-operativo-24m.md`.
