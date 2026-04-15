/* ============================================================
   Table — 24-month projection
   ============================================================ */

window.PROXIMA = window.PROXIMA || {};

window.PROXIMA.ProjectionTable = function ProjectionTable({ sim }) {
  const { results, breakEvenMonth } = sim;
  const targets = window.PROXIMA.strategyTargets;

  const eur = (v) => "€" + Math.round(v).toLocaleString("it-IT");
  const num1 = (v) => v.toFixed(1);
  const num0 = (v) => Math.round(v).toLocaleString("it-IT");

  const phasePill = (p) => (
    <span className={`pill pill-p${p}`}>F{p} · {window.PROXIMA.phaseLabel(p)}</span>
  );

  const [exportMsg, setExportMsg] = React.useState("");

  const exportCSV = () => {
    const headers = [
      "month_index", "strategy_month", "phase",
      "google_bookings", "meta_bookings", "linkedin_bookings",
      "seo_bookings", "social_bookings", "referral_bookings", "borrowed_bookings",
      "total_bookings", "actual_checkups",
      "new_clients_theoretical", "max_capacity", "capacity_limited",
      "new_clients", "churn", "total_clients",
      "mrr", "arr", "cumulative_revenue",
      "monthly_spend", "cumulative_spend", "target_clients"
    ];
    const rows = results.map((r) => [
      r.month, r.strategyMonth, r.phase,
      r.bookings.google.toFixed(2), r.bookings.meta.toFixed(2), r.bookings.linkedin.toFixed(2),
      r.bookings.seo.toFixed(2), r.bookings.social.toFixed(2),
      r.bookings.referral.toFixed(2), r.bookings.borrowed.toFixed(2),
      r.bookings.total.toFixed(2), r.actualCheckups.toFixed(2),
      r.newClientsTheoretical.toFixed(2), r.maxClientsByCapacity.toFixed(2),
      r.capacityLimited ? 1 : 0,
      r.newClients.toFixed(2), r.churn.toFixed(2), r.totalClients.toFixed(2),
      r.mrr.toFixed(2), r.arr.toFixed(2), r.cumulativeRevenue.toFixed(2),
      r.monthlySpend.toFixed(2), r.cumulativeSpend.toFixed(2),
      targets.clients[r.month] || 0
    ]);
    const csv = [headers.join(","), ...rows.map((row) => row.join(","))].join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "proxima-funnel-projection.csv";
    a.click();
    URL.revokeObjectURL(url);
    setExportMsg("CSV scaricato ✓");
    setTimeout(() => setExportMsg(""), 2500);
  };

  const exportJSON = () => {
    const blob = new Blob([JSON.stringify(sim, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "proxima-funnel-simulation.json";
    a.click();
    URL.revokeObjectURL(url);
    setExportMsg("JSON scaricato ✓");
    setTimeout(() => setExportMsg(""), 2500);
  };

  return (
    <div className="section">
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
        <div className="section-title" style={{ margin: 0 }}>Tabella completa 24 mesi (dal mese -6 al mese +18)</div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          {exportMsg && <span className="text-dim" style={{ fontSize: 12 }}>{exportMsg}</span>}
          <button className="btn-ghost btn" onClick={exportCSV}>↓ CSV</button>
          <button className="btn-ghost btn" onClick={exportJSON}>↓ JSON</button>
        </div>
      </div>

      <div className="tbl-wrap">
        <table className="proj">
          <thead>
            <tr>
              <th>Mese</th>
              <th>Fase</th>
              <th>Google</th>
              <th>Meta</th>
              <th>LinkedIn</th>
              <th>SEO</th>
              <th>Social</th>
              <th>Passaparola</th>
              <th>PR/Podcast</th>
              <th>Totale prenotazioni</th>
              <th>Check-up fatti</th>
              <th>Max gestibili</th>
              <th>Nuovi clienti</th>
              <th>Persi (churn)</th>
              <th>Clienti totali</th>
              <th>Obiettivo</th>
              <th>Ricavi mese</th>
              <th>Ricavi annui</th>
              <th>Ricavi accum.</th>
              <th>Spesa accum.</th>
            </tr>
          </thead>
          <tbody>
            {results.map((r) => {
              const isPhaseBoundary = r.month > 1 &&
                window.PROXIMA.getPhase(r.month) !== window.PROXIMA.getPhase(r.month - 1);
              const isBreakEven = breakEvenMonth === r.month;
              const cls = [
                isPhaseBoundary ? "phase-boundary" : "",
                r.capacityLimited ? "capacity-limited" : "",
                isBreakEven ? "break-even" : ""
              ].filter(Boolean).join(" ");
              const target = targets.clients[r.month] || 0;
              return (
                <tr key={r.month} className={cls}>
                  <td>
                    <span className="gold mono">
                      M{r.strategyMonth >= 0 ? "+" : ""}{r.strategyMonth}
                    </span>
                    <span className="text-faint mono" style={{ fontSize: 10, marginLeft: 4 }}>
                      #{r.month}
                    </span>
                  </td>
                  <td style={{ textAlign: "left" }}>{phasePill(r.phase)}</td>
                  <td>{num1(r.bookings.google)}</td>
                  <td>{num1(r.bookings.meta)}</td>
                  <td>{num1(r.bookings.linkedin)}</td>
                  <td>{num1(r.bookings.seo)}</td>
                  <td>{num1(r.bookings.social)}</td>
                  <td>{num1(r.bookings.referral)}</td>
                  <td>{num1(r.bookings.borrowed)}</td>
                  <td className="gold">{num1(r.bookings.total)}</td>
                  <td>{num1(r.actualCheckups)}</td>
                  <td className="text-dim">{num0(r.maxClientsByCapacity)}</td>
                  <td className={r.capacityLimited ? "" : "gold"}>
                    {num1(r.newClients)}
                    {r.capacityLimited && <span style={{ color: "#F59E0B", marginLeft: 4 }}>⚠</span>}
                  </td>
                  <td className="text-dim">{num1(r.churn)}</td>
                  <td className="gold">{num0(r.totalClients)}</td>
                  <td className="text-dim">{target || "—"}</td>
                  <td>{eur(r.mrr)}</td>
                  <td>{eur(r.arr)}</td>
                  <td>{eur(r.cumulativeRevenue)}</td>
                  <td className="text-dim">{eur(r.cumulativeSpend)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div style={{ marginTop: 12, display: "flex", gap: 16, flexWrap: "wrap", fontSize: 11 }} className="text-dim">
        <span>
          <span style={{ display: "inline-block", width: 10, height: 10, background: "rgba(245,158,11,0.15)", border: "1px solid rgba(245,158,11,0.3)", marginRight: 6, verticalAlign: "middle" }}></span>
          Riga con ⚠ = ore di lavoro sature (il team non riesce a gestire tutti i lead)
        </span>
        <span>
          <span style={{ display: "inline-block", width: 10, height: 10, background: "rgba(74,222,128,0.15)", marginRight: 6, verticalAlign: "middle" }}></span>
          Riga verde = mese di pareggio (ricavi accumulati ≥ €180.000)
        </span>
        <span>
          <span style={{ display: "inline-block", width: 10, height: 2, background: "#8E7940", marginRight: 6, verticalAlign: "middle" }}></span>
          Linea oro = inizio di una nuova fase della strategia
        </span>
      </div>
    </div>
  );
};
