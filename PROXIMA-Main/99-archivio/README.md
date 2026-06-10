# 99 — Archivio storico

Materiale **superato / abbandonato**, tenuto solo come **riferimento storico**.
Le cartelle `01`–`05` contengono ciò che è in uso per la SCF; qui sta ciò che è
stato esplorato e poi messo da parte.

> Decisione (giugno 2026): i branch git obsoleti **non** vengono cancellati; il
> loro materiale utile è consolidato qui, ordinato, così il repo resta pulito.

## Contenuto

### `modello-sim-agente-collegato/` — percorso SIM / agente collegato (ABBANDONATO)

Percorso alternativo esplorato in passato: costituire Proxima come **SRL agente
collegato di una SIM** (art. 31-ter TUF) invece che come **SCF**. Dopo confronto
col commercialista (giugno 2026) l'unica strada percorribile è la **SCF**, quindi
questo percorso è **abbandonato**.

| File | Cos'è | Stato |
|---|---|---|
| `15-business-model-agente-collegato.md` | Business model della partnership con la SIM (split provvigionale, AUM…). | ❌ Obsoleto |
| `16-srl-qualifiche-OCF.md` | Meccanica di costituzione **SRL** + percorso **OCF / esame / CF Autonomo**. | ♻️ Parti **utili anche per la SCF** (ignora i pezzi su SIM/art. 31-ter) |
| `17-code-review-funnel.md` | Code review del motore funnel (bug + formula ricavi). | ♻️ Base tecnica per la **ricalibrazione** |
| `funnel-agente-collegato/` (`model-ac.js`, `proxima-funnel-ac.html`) | Variante "-ac" del modello funnel: motore più evoluto (cohort AUM, stagionalità, prelievi, shock) ma con **split provvigionale verso la SIM**. | ♻️ Saccheggiare le migliorie motore, **non** la logica di split |

## ♻️ Parti ancora utili per la SCF

Anche se il percorso SIM è chiuso, alcuni contenuti restano riusabili:

- **Costituzione SRL + iter OCF** → `modello-sim-agente-collegato/16-srl-qualifiche-OCF.md`
  (le parti societarie e di qualifica valgono anche per la SCF; vedi anche
  `../01-strategia/piano-di-lancio/10-struttura-societaria.md` e `11-iter-regolatorio.md`).
- **Migliorie al motore del funnel** → `modello-sim-agente-collegato/17-code-review-funnel.md`
  + `modello-sim-agente-collegato/funnel-agente-collegato/` alimentano la
  ricalibrazione fee-only descritta in `../02-modello-previsionale/RICALIBRAZIONE-SCF.md`.

> ⚠️ Non riproporre il percorso SIM / agente collegato come opzione, salvo
> esplicita richiesta.
