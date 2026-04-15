/* ============================================================
   App — state management + layout composition
   ============================================================ */

window.PROXIMA = window.PROXIMA || {};

const STORAGE_KEY = "proxima.funnel.params.v1";

function loadParams() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return window.PROXIMA.defaultParams();
    const parsed = JSON.parse(raw);
    // Merge with defaults to avoid missing keys after schema changes
    const defaults = window.PROXIMA.defaultParams();
    return { ...defaults, ...parsed };
  } catch (e) {
    return window.PROXIMA.defaultParams();
  }
}

function App() {
  const [params, setParams] = React.useState(loadParams);

  React.useEffect(() => {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(params)); } catch (e) {}
  }, [params]);

  const sim = React.useMemo(
    () => window.PROXIMA.simulate(params, 24),
    [params]
  );

  const resetDefaults = () => {
    if (confirm("Ripristinare tutti i parametri ai default?")) {
      setParams(window.PROXIMA.defaultParams());
    }
  };

  return (
    <div className="app">
      <aside className="sidebar">
        <window.PROXIMA.Controls
          params={params}
          setParams={setParams}
          onReset={resetDefaults}
        />
      </aside>
      <main className="main">
        <div className="section">
          <div className="info-banner">
            <strong>Come funziona questo modello.</strong> Invece di partire da obiettivi di
            clienti decisi a tavolino, il numero di clienti viene <em>calcolato</em> dai
            numeri veri di ogni canale (quanti click, quante visite, quante persone
            prenotano, quante diventano clienti paganti). Muovi gli slider a sinistra
            per vedere in tempo reale come cambiano clienti, ricavi, ore di lavoro
            necessarie e mese di pareggio. I valori si salvano automaticamente nel browser.
          </div>
        </div>
        <window.PROXIMA.Glossary />
        <window.PROXIMA.Dashboard sim={sim} />
        <window.PROXIMA.ProjectionTable sim={sim} />
        <div className="section" style={{ marginTop: 40, paddingTop: 20, borderTop: "1px solid #1E2A3E" }}>
          <div className="text-faint" style={{ fontSize: 11, textAlign: "center" }}>
            Proxima · Modello Funnel calcolato dai numeri veri di ogni canale · dati salvati nel browser
          </div>
        </div>
      </main>
    </div>
  );
}

// Wait for all PROXIMA modules to load before rendering
function boot() {
  if (!window.PROXIMA.simulate || !window.PROXIMA.Controls ||
      !window.PROXIMA.Dashboard || !window.PROXIMA.ProjectionTable ||
      !window.PROXIMA.Glossary) {
    return setTimeout(boot, 50);
  }
  const root = ReactDOM.createRoot(document.getElementById("root"));
  root.render(<App />);
}

boot();
