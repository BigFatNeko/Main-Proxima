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
            <strong>Modello bottom-up.</strong> I clienti emergono dalle conversioni reali
            di ogni canale, non da target top-down. Modifica gli slider a sinistra per
            vedere in tempo reale impatto su KPI, capacità, break-even. I parametri
            sono salvati in locale.
          </div>
        </div>
        <window.PROXIMA.Dashboard sim={sim} />
        <window.PROXIMA.ProjectionTable sim={sim} />
        <div className="section" style={{ marginTop: 40, paddingTop: 20, borderTop: "1px solid #1E2A3E" }}>
          <div className="text-faint" style={{ fontSize: 11, textAlign: "center" }}>
            Proxima Funnel Model · bottom-up · React 18 + Recharts · dati locali (localStorage)
          </div>
        </div>
      </main>
    </div>
  );
}

// Wait for all PROXIMA modules to load before rendering
function boot() {
  if (!window.PROXIMA.simulate || !window.PROXIMA.Controls ||
      !window.PROXIMA.Dashboard || !window.PROXIMA.ProjectionTable) {
    return setTimeout(boot, 50);
  }
  const root = ReactDOM.createRoot(document.getElementById("root"));
  root.render(<App />);
}

boot();
