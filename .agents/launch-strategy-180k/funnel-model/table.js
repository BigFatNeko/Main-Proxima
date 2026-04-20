/* ============================================================
   Table — 36-month projection (M-12 … M+23)
   ============================================================ */
window.PROXIMA = window.PROXIMA || {};

window.PROXIMA.ProjectionTable = function ProjectionTable({ sim }) {
  const { results, breakEvenOperational, breakEvenCumulative } = sim;
  const [showPre, setShowPre] = React.useState(true);
  const [msg, setMsg] = React.useState("");

  const fmtE = (v) => "\u20AC" + Math.round(v).toLocaleString("it-IT");
  const fmtN = (v) => Math.round(v).toLocaleString("it-IT");

  const flash = (t) => { setMsg(t); setTimeout(() => setMsg(""), 2500); };

  const cols = [
    ["Mese",           (r) => null,                ""],
    ["Fase",           (r) => null,                ""],
    ["Prenotazioni",   (r) => fmtN(r.totalBookings), ""],
    ["Check-up",       (r) => fmtN(r.checkups),    ""],
    ["Max nuovi/mese", (r) => fmtN(r.maxNewPerMonth), ""],
    ["Nuovi clienti",  (r) => fmtN(r.newClientsCapped), ""],
    ["Persi (churn)",  (r) => fmtN(r.churnedClients), ""],
    ["Clienti attivi", (r) => fmtN(r.totalClients), "bold"],
    ["Costi costituz.",  (r) => fmtE(r.constitutionCosts), ""],
    ["Costi operativi",  (r) => fmtE(r.operatingCosts), ""],
    ["Personale",      (r) => fmtE(r.personnelCosts), ""],
    ["Marketing",      (r) => fmtE(r.marketingCosts), ""],
    ["Costi totali",   (r) => fmtE(r.totalCosts),  "bold"],
    ["MRR",            (r) => fmtE(r.mrr),         "gold"],
    ["Burn netto",     (r) => fmtE(r.netBurn),     "burn"],
    ["Cash",           (r) => fmtE(r.cashRemaining), "cash"],
    ["Team",           (r) => fmtN(r.staffCount), ""],
    ["Slot %",         (r) => Math.round(r.appointmentUtilization*100)+"%", "util"],
    ["Ads %",          (r) => Math.round(r.budgetFactor*100)+"%", "bf"],
  ];

  const pillStyle6 = { background: "rgba(74,222,128,0.15)", color: "#4ade80", border: "1px solid rgba(74,222,128,0.25)" };
  const pillStyle7 = { background: "rgba(34,197,94,0.25)", color: "#22c55e", border: "1px solid rgba(34,197,94,0.4)" };

  const phasePill = (p, name) => {
    const extra = p === 6 ? pillStyle6 : p === 7 ? pillStyle7 : undefined;
    return React.createElement("span", { className: `pill pill-p${p}`, style: extra }, name);
  };

  const download = (blob, filename) => {
    const u = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = u; a.download = filename; a.click();
    URL.revokeObjectURL(u);
  };

  const exportCSV = () => {
    const hdr = ["Mese","Fase","Prenotazioni","Check-up","Max nuovi/mese",
      "Nuovi clienti","Churn","Clienti attivi","Costi costituzione",
      "Costi operativi","Personale","Marketing","Costi totali",
      "MRR","Burn netto","Cash","Team","Slot appuntamenti %","Budget ads %"];
    const rows = results.map((r) => [
      r.monthLabel, r.phaseName, Math.round(r.totalBookings), Math.round(r.checkups),
      Math.round(r.maxNewPerMonth), Math.round(r.newClientsCapped),
      Math.round(r.churnedClients), Math.round(r.totalClients),
      Math.round(r.constitutionCosts), Math.round(r.operatingCosts),
      Math.round(r.personnelCosts), Math.round(r.marketingCosts),
      Math.round(r.totalCosts), Math.round(r.mrr), Math.round(r.netBurn),
      Math.round(r.cashRemaining), r.staffCount,
      Math.round(r.appointmentUtilization*100), Math.round(r.budgetFactor*100)
    ].join(";"));
    download(new Blob([hdr.join(";") + "\n" + rows.join("\n")], { type: "text/csv;charset=utf-8" }),
      "proxima-proiezione-36m.csv");
    flash("CSV scaricato");
  };

  const exportJSON = () => {
    download(new Blob([JSON.stringify(results, null, 2)], { type: "application/json" }),
      "proxima-proiezione-36m.json");
    flash("JSON scaricato");
  };

  const visible = showPre ? results : results.filter((r) => !r.isPreRelease);

  const tdStyle = (flag, r) => {
    if (flag === "bold") return { fontWeight: 700 };
    if (flag === "gold") return { color: "#D4A843", fontWeight: 700 };
    if (flag === "burn") return { fontWeight: 700, color: r.netBurn > 0 ? "#ef4444" : "#4ade80" };
    if (flag === "cash") return { fontWeight: 700, color: r.cashRemaining < 30000 ? "#ef4444" : undefined };
    if (flag === "util") return { color: r.appointmentUtilization > 0.85 ? "#F59E0B" : "#8B98B0" };
    if (flag === "bf") return { color: r.budgetFactor < 0.5 ? "#F59E0B" : "#8B98B0" };
    return undefined;
  };

  return (
    React.createElement("div", { className: "section" },
      React.createElement("div", { style: { display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14, flexWrap: "wrap", gap: 8 } },
        React.createElement("div", { className: "section-title", style: { margin: 0 } }, "Tabella completa 36 mesi"),
        React.createElement("div", { style: { display: "flex", gap: 8, alignItems: "center" } },
          msg && React.createElement("span", { className: "text-dim", style: { fontSize: 12 } }, msg),
          React.createElement("label", { style: { fontSize: 12, display: "flex", alignItems: "center", gap: 4, cursor: "pointer" } },
            React.createElement("input", { type: "checkbox", checked: showPre, onChange: () => setShowPre(!showPre) }),
            "Pre-release"
          ),
          React.createElement("button", { className: "btn-ghost btn", onClick: exportCSV }, "\u2193 CSV"),
          React.createElement("button", { className: "btn-ghost btn", onClick: exportJSON }, "\u2193 JSON")
        )
      ),
      React.createElement("div", { className: "tbl-wrap" },
        React.createElement("table", { className: "proj" },
          React.createElement("thead", null,
            React.createElement("tr", null, cols.map(([h], i) =>
              React.createElement("th", { key: i }, h)
            ))
          ),
          React.createElement("tbody", null,
            visible.map((r, idx) => {
              const prev = idx > 0 ? visible[idx - 1] : null;
              const cls = [
                prev && r.phase !== prev.phase ? "phase-boundary" : "",
                r.capacityLimited ? "capacity-limited" : "",
                breakEvenOperational === r.month ? "break-even" : "",
                breakEvenCumulative === r.month ? "break-even" : "",
                r.isPreRelease ? "pre-release" : ""
              ].filter(Boolean).join(" ");
              return React.createElement("tr", { key: r.month, className: cls || undefined },
                React.createElement("td", null,
                  React.createElement("span", { className: "gold mono" }, r.monthLabel),
                  React.createElement("span", { className: "text-faint mono", style: { fontSize: 10, marginLeft: 4 } }, "#" + r.month)
                ),
                React.createElement("td", { style: { textAlign: "left" } }, phasePill(r.phase, r.phaseName)),
                ...cols.slice(2).map(([, fn, flag], ci) =>
                  React.createElement("td", { key: ci, style: tdStyle(flag, r) }, fn(r))
                )
              );
            })
          )
        )
      ),
      React.createElement("div", { style: { marginTop: 12, display: "flex", gap: 16, flexWrap: "wrap", fontSize: 11 }, className: "text-dim" },
        React.createElement("span", null,
          React.createElement("span", { style: { display: "inline-block", width: 10, height: 10, background: "rgba(245,158,11,0.15)", border: "1px solid rgba(245,158,11,0.3)", marginRight: 6, verticalAlign: "middle" } }),
          "Riga arancione = capacit\u00E0 satura"
        ),
        React.createElement("span", null,
          React.createElement("span", { style: { display: "inline-block", width: 10, height: 10, background: "rgba(74,222,128,0.15)", marginRight: 6, verticalAlign: "middle" } }),
          "Riga verde = mese di pareggio"
        ),
        React.createElement("span", null,
          React.createElement("span", { style: { display: "inline-block", width: 10, height: 2, background: "#8E7940", marginRight: 6, verticalAlign: "middle" } }),
          "Linea oro = cambio fase"
        )
      )
    )
  );
};
