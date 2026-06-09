# Handoff — Sessione Proxima

*Data: 2026-06-09*

## Cosa è stato fatto in questa sessione

1. **Inizializzato il progetto `proxima/`** nella root del repo, con 36 skill di marketing installate via `npx skillkit install coreyhaines31/marketingskills --force` (la skill `revops` ha un warning HIGH di sicurezza — installata con --force).

2. **Creato `.agents/product-marketing-context.md`** — contesto completo di prodotto per Proxima: overview, target audience, personas, pain points, competitive landscape, positioning, objections, messaging, brand identity, channels, metriche. Questo file è il riferimento per tutte le skill di marketing.

3. **Creato `.agents/launch-strategy.md`** — strategia di lancio completa su 18 mesi con budget €180.000:
   - Framework ORB (Owned / Rented / Borrowed channels)
   - 5 fasi: Pre-lancio → Alpha → Beta → Early Access → Lancio Pubblico
   - Budget dettagliato per fase e per categoria
   - Previsione ricavi mese per mese (target: 254 clienti, €114k ARR a mese 18)
   - 3 scenari (pessimistico / base / ottimistico)
   - Workflow operativo: struttura settimana tipo per 2 fondatori, ciclo mensile, review settimanali/mensili, tool stack, regole operative

4. Tutto è stato committato e pushato sul branch **`claude/init-proxima-project-Myyk4`**.

## Struttura file rilevanti

```
Main-Marketing/
├── .agents/
│   ├── product-marketing-context.md   ← Contesto prodotto Proxima
│   ├── launch-strategy.md             ← Strategia lancio 180k/18 mesi
│   └── HANDOFF.md                     ← Questo file
├── proxima/
│   └── .claude/skills/                ← 36 skill marketing (skillkit)
├── PROXIMA-Main/                      ← Materiale di business esistente
│   ├── 01-strategia/
│   ├── 02-modello-previsionale/
│   ├── 03-marketing/
│   ├── 04-briefing/                   ← ⚠ Pipeline in produzione, non toccare
│   └── 05-branding/
└── CLAUDE.md                          ← Istruzioni progetto (leggere sempre)
```

## Cosa fare nella prossima sessione

La strategia di lancio è completa ma è un documento. I prossimi passi logici, in ordine di priorità:

### Priorità 1 — Costruire gli asset della Fase 1
- **Sito web**: wireframe → sviluppo (Next.js). La landing page è l'asset più urgente
- **Calcolatore Costi Banca**: la web app che rende tangibile il problema. Serve una fonte dati per i TER dei fondi italiani (Morningstar API, o database KIID/KID)
- **Piano editoriale**: primo mese di contenuti social (usare le skill `content-strategy`, `copywriting`, `social-content` installate in `proxima/.claude/skills/`)

### Priorità 2 — Allineare con materiale esistente
- In `PROXIMA-Main/01-strategia/` c'è già materiale su piano di lancio, struttura SCF, iter OCF, costi. La launch strategy in `.agents/` dovrebbe essere coerente con quello — verificare e allineare
- In `PROXIMA-Main/02-modello-previsionale/` c'è un modello funnel React da ricalibrare per SCF (vedi `RICALIBRAZIONE-SCF.md`). La previsione ricavi nella launch strategy potrebbe alimentare quel modello

### Priorità 3 — Email e funnel
- Sviluppare la sequenza email completa (usare skill `email-sequence`)
- Setup ActiveCampaign o ConvertKit
- Landing page con form lista d'attesa

## Note importanti

- **Lingua**: tutto in italiano (vedi CLAUDE.md)
- **Branch**: sviluppare su `claude/init-proxima-project-Myyk4`
- **Briefing pipeline**: NON toccare `04-briefing/` né il branch `claude/financial-briefing-pipeline-aVCmh` — è in produzione
- **Struttura legale FISSATA**: SCF. Non proporre SIM o agente collegato
- **Skill marketing**: le 36 skill in `proxima/.claude/skills/` sono reference material, non auto-caricate. Per usarle bisogna leggerle esplicitamente
