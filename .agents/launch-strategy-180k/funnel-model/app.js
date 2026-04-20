/* ============================================================
   App — state management + layout composition (v2 · 36 mesi)
   ============================================================ */

window.PROXIMA = window.PROXIMA || {};

const STORAGE_KEY = "proxima.funnel.params.v2";

function loadParams() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return window.PROXIMA.defaultParams();
    const parsed = JSON.parse(raw);
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
    () => window.PROXIMA.simulate(params, 36),
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
            <strong>Come funziona questo modello.</strong> Calcola clienti, ricavi,
            costi e cash flow su 36 mesi (da M-12 a M+24), partendo dai numeri veri
            di ogni canale e includendo tutti i costi di costituzione, operativi e del
            personale. Include tre scenari di rischio (base, recessione, crisi). Muovi
            gli slider a sinistra per aggiornare tutto in tempo reale.
          </div>
        </div>
        <window.PROXIMA.Glossary />
        <window.PROXIMA.Dashboard sim={sim} />
        <window.PROXIMA.ProjectionTable sim={sim} />
        <div className="section" style={{ marginTop: 40, paddingTop: 20, borderTop: "1px solid #1E2A3E" }}>
          <div className="text-faint" style={{ fontSize: 11, textAlign: "center" }}>
            Proxima · Modello Funnel v2 · 36 mesi · costi completi · scenari di rischio · dati salvati nel browser
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
      !window.PROXIMA.Glossary || !window.PROXIMA.defaultParams) {
    return setTimeout(boot, 50);
  }
  const root = ReactDOM.createRoot(document.getElementById("root"));
  root.render(<App />);
}

boot();
