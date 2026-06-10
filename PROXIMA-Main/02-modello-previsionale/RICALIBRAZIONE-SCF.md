# Ricalibrazione del modello previsionale per la SCF (fee-only)

Il modello funnel esiste in due versioni in questa cartella:

| Versione | File | Note |
|---|---|---|
| Base | `funnel-model/` (`proxima-funnel.html`, `model.js`) | Versione più pulita, senza split SIM. **Punto di partenza.** |
| Agente collegato ("-ac") | `../99-archivio/modello-sim-agente-collegato/funnel-agente-collegato/` | Motore più evoluto (cohort AUM, stagionalità, prelievi, shock di mercato) ma con logica **provvigionale verso la SIM** → da non usare così com'è. |

L'obiettivo è produrre **un'unica versione SCF fee-only** (`proxima-funnel-scf.html`)
che unisca il motore migliore con la logica di ricavo corretta per una SCF.

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

> Decisione da prendere: modello di parcella **% su AUM** (es. 0,7–1,0%/anno),
> **fissa annua**, o **ibrido**. La scelta cambia revenue forecast e pricing
> (vedi `03-marketing/skills/pricing-strategy`).

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
