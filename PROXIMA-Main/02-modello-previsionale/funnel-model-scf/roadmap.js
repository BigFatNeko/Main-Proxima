/* ============================================================
   Roadmap — Stato lavori Proxima: recap costante fatto / da fare
   Aggiorna l'elenco AREE qui sotto quando cambiano i piani; i click
   dell'utente (fatto/da fare) si salvano nel browser e prevalgono
   sul valore `done` di partenza.
   ============================================================ */

window.PROXIMA = window.PROXIMA || {};

(function () {
  const ROADMAP_STORAGE_KEY = "proxima.roadmap.v1";

  const AREE = [
    {
      title: "Iter regolatorio e burocratico",
      items: [
        { id: "reg-srl", label: "Costituzione della SRL (capitale €50.000 versato)", done: false },
        { id: "reg-esame", label: "Esame OCF dei soci (requisiti di professionalità)", done: false },
        { id: "reg-onorabilita", label: "Documentazione onorabilità e indipendenza", done: false },
        { id: "reg-albo", label: "Iscrizione all'Albo OCF Sez. III (SCF)", done: false },
        { id: "reg-rc", label: "Polizza RC professionale", done: false },
        { id: "reg-privacy", label: "Adempimenti privacy/GDPR (registri, informative)", done: false },
      ],
    },
    {
      title: "App",
      items: [
        { id: "app-offerta", label: "Definizione offerta a fasce (Check-up / App / Monitor / Live)", done: true },
        { id: "app-legale", label: "Verifica legale del report IA gratuito (perimetro consulenza)", done: false },
        { id: "app-arch", label: "Architettura tecnica e scelta dello stack", done: false },
        { id: "app-mvp", label: "MVP del report IA (Check-up gratuito)", done: false },
        { id: "app-abbonamento", label: "App in abbonamento (insights e personalizzazione)", done: false },
        { id: "app-premium", label: "Funzioni premium (monitoraggio portafoglio, call)", done: false },
      ],
    },
    {
      title: "Landing page",
      items: [
        { id: "land-copy", label: "Riscrittura copy sul posizionamento SCF (via fee di gestione e linguaggio da gestione)", done: false },
        { id: "land-ab", label: "A/B test della tagline sulla waitlist", done: false },
        { id: "land-pub", label: "Pubblicazione + raccolta waitlist (email, consensi)", done: false },
        { id: "land-analytics", label: "Analytics e tracciamento conversioni", done: false },
      ],
    },
    {
      title: "Marketing",
      items: [
        { id: "mkt-ricalibra", label: "Ricalibrazione strategia marketing v1 → SCF", done: false },
        { id: "mkt-contenuti", label: "Piano editoriale e rubriche corporate (format senza volto-guru)", done: false },
        { id: "mkt-canali", label: "Setup canali social", done: false },
        { id: "mkt-pr", label: "PR, podcast e partnership", done: false },
        { id: "mkt-paid", label: "Campagne paid Google/Meta (post-lancio)", done: false },
      ],
    },
    {
      title: "Branding",
      items: [
        { id: "brand-audit", label: "Audit del brand pre-SCF", done: true },
        { id: "brand-ricerca", label: "Ricerca branding competitor", done: true },
        { id: "brand-identita", label: "Sistema identità visiva v1", done: true },
        { id: "brand-strategy", label: "Brand strategy SCF v1", done: true },
        { id: "brand-logo", label: "Scelta direzione logo + esecutivo dal designer", done: false },
        { id: "brand-marchio", label: "Verifica/deposito marchio (UIBM/EUIPO, classe 36)", done: false },
        { id: "brand-template", label: "Template: card social, report, slide", done: false },
      ],
    },
    {
      title: "Amministrazione interna (organizzativa e contabile)",
      items: [
        { id: "amm-forma", label: "Scelta della forma societaria (SCF) col commercialista", done: true },
        { id: "amm-contabilita", label: "Contabilità ordinaria operativa col commercialista", done: false },
        { id: "amm-banca", label: "Conto corrente societario", done: false },
        { id: "amm-ruoli", label: "Organigramma e ruoli interni (chi fa cosa)", done: false },
        { id: "amm-strumenti", label: "Strumenti interni: CRM, fatturazione, archivio documenti", done: false },
        { id: "amm-modello", label: "Ricalibrazione del modello previsionale alle fasce SCF (v1 — assunzioni da validare)", done: true },
      ],
    },
  ];

  function loadRoadmapOverrides() {
    try {
      return JSON.parse(localStorage.getItem(ROADMAP_STORAGE_KEY)) || {};
    } catch (e) {
      return {};
    }
  }

  function Roadmap() {
    const [overrides, setOverrides] = React.useState(loadRoadmapOverrides);

    React.useEffect(() => {
      try { localStorage.setItem(ROADMAP_STORAGE_KEY, JSON.stringify(overrides)); } catch (e) {}
    }, [overrides]);

    const isDone = (item) => (overrides[item.id] !== undefined ? overrides[item.id] : item.done);
    const toggle = (item) => setOverrides({ ...overrides, [item.id]: !isDone(item) });

    const tutte = AREE.flatMap((a) => a.items);
    const fatte = tutte.filter(isDone).length;
    const pct = Math.round((fatte / tutte.length) * 100);

    return (
      <div className="section">
        <div className="section-title">Stato lavori — fatto / da fare</div>
        <div className="card" style={{ marginBottom: 14 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 12, flexWrap: "wrap" }}>
            <div>
              <div className="card-title">Recap operativo Proxima</div>
              <div className="card-sub" style={{ marginBottom: 0 }}>
                Clicca una voce per segnarla fatta o da fare (si salva nel browser).
                L'elenco di partenza si aggiorna in <span className="mono">roadmap.js</span>.
              </div>
            </div>
            <div className="mono" style={{ fontSize: 14 }}>
              <span className="gold">{fatte}</span> <span className="text-dim">di {tutte.length} fatte · {pct}%</span>
            </div>
          </div>
          <div className="roadmap-progress"><div style={{ width: pct + "%" }} /></div>
        </div>
        <div className="roadmap-grid">
          {AREE.map((area) => {
            const fatteArea = area.items.filter(isDone).length;
            return (
              <div className="card" key={area.title}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 10, gap: 8 }}>
                  <div className="card-title" style={{ marginBottom: 0 }}>{area.title}</div>
                  <span className="mono text-dim" style={{ fontSize: 11, whiteSpace: "nowrap" }}>{fatteArea}/{area.items.length}</span>
                </div>
                {area.items.map((item) => (
                  <div
                    key={item.id}
                    className={"roadmap-item" + (isDone(item) ? " done" : "")}
                    onClick={() => toggle(item)}
                  >
                    <span className="roadmap-check">{isDone(item) ? "✓" : ""}</span>
                    <span>{item.label}</span>
                  </div>
                ))}
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  window.PROXIMA.Roadmap = Roadmap;
})();
