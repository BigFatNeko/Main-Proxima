/* ============================================================
   Dashboard — KPI cards + CAC per canale + Piano assunzioni + Charts
   v3: dynamic hiring, budget factor, per-channel CAC
   ============================================================ */

window.PROXIMA = window.PROXIMA || {};

window.PROXIMA.Dashboard = function Dashboard({ sim }) {
  const {
    ResponsiveContainer, ComposedChart, AreaChart, Bar, Line, Area,
    XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceLine
  } = window.Recharts;

  const { results, breakEvenOperational, breakEvenCumulative,
          cacBlended, cacByChannel, cashMinimum, cashMinimumMonth,
          hiringPlan } = sim;

  const eur = (v) => "\u20AC\u00A0" + Math.round(v).toLocaleString("it-IT");
  const num = (v) => Math.round(v).toLocaleString("it-IT");
  const ml = (v) => {
    if (v == null) return "Mai";
    if (typeof v === "number" && v >= 1 && v <= results.length) return results[v-1].monthLabel;
    return "Mai";
  };
  const last = results[results.length - 1];

  const tooltipFmt = (v) => eur(v);
  const tooltipStyle = {
    backgroundColor: "#121E30", border: "1px solid #2A3952",
    borderRadius: 8, fontFamily: "DM Mono, monospace", fontSize: 12, color: "#E8ECF2"
  };
  const axTick = { fill: "#8B98B0", fontSize: 11 };
  const axLine = { stroke: "#1E2A3E" };

  /* ── Milestones ── */
  const milestones = [
    { label: "M0 — Lancio", idx: 12 },
    { label: "M+12", idx: 24 },
    { label: "M+23 (fine)", idx: 35 }
  ];

  const Kpi = ({ label, value, sub, accent }) => (
    React.createElement("div", { className: "kpi-card" + (accent ? " accent" : "") },
      React.createElement("div", { className: "kpi-label" }, label),
      React.createElement("div", { className: "kpi-value mono" }, value),
      sub && React.createElement("div", { className: "kpi-sub text-dim" }, sub)
    )
  );

  /* ── Chart data ── */
  const channelData = results.filter((r) => r.month >= 7).map((r) => ({
    monthLabel: r.monthLabel,
    google: r.googleBookings, meta: r.metaBookings,
    linkedin: r.linkedinBookings, seo: r.seoBookings,
    social: r.socialBookings, referral: r.referralBookings,
    borrowed: r.borrowedBookings
  }));

  const chanColors = {
    google: ["Google Ads", "#4285F4"], meta: ["Meta Ads", "#E1306C"],
    linkedin: ["LinkedIn", "#0077B5"], seo: ["SEO", "#4ADE80"],
    social: ["Social organico", "#A78BFA"], referral: ["Referral", "#F59E0B"],
    borrowed: ["Borrowed", "#60A5FA"]
  };

  const costColors = {
    constitutionCosts: ["Costituzione", "#F87171"],
    operatingCosts: ["Operativi", "#60A5FA"],
    personnelCosts: ["Personale", "#A78BFA"],
    marketingCosts: ["Marketing", "#F59E0B"]
  };

  const clientsData = results.map((r) => ({
    monthLabel: r.monthLabel, totalClients: r.totalClients,
    maxCapacity: r.maxClientsByCapacity
  }));

  /* ── CAC per channel (current month = last post-launch with spend) ── */
  const cacChannels = [
    { name: "Google Ads", cac: cacByChannel.google, color: "#4285F4" },
    { name: "Meta Ads", cac: cacByChannel.meta, color: "#E1306C" },
    { name: "LinkedIn Ads", cac: cacByChannel.linkedin, color: "#0077B5" }
  ].filter((c) => c.cac > 0);

  /* ── Staff data for chart ── */
  const staffData = results.filter((r) => r.month >= 13).map((r) => ({
    monthLabel: r.monthLabel,
    staffCount: r.staffCount,
    utilization: Math.round(r.capacityUtilization * 100),
    budgetFactor: Math.round(r.budgetFactor * 100)
  }));

  return (
    <div>
      {/* Section 1: KPI milestone cards */}
      <div className="section">
        <div className="section-title">Indicatori chiave</div>
        {milestones.map((ms) => {
          const r = results[ms.idx];
          if (!r) return null;
          return (
            <div key={ms.idx} style={{ marginBottom: 18 }}>
              <div className="uppercase gold" style={{ marginBottom: 8 }}>{ms.label}</div>
              <div className="kpi-grid">
                <Kpi label="Clienti attivi" value={num(r.totalClients)} />
                <Kpi label="Ricavi mensili (MRR)" value={eur(r.mrr)} />
                <Kpi label="Cash rimanente" value={eur(r.cashRemaining)} />
                <Kpi label="Team" value={num(r.staffCount) + " persone"} />
              </div>
            </div>
          );
        })}
      </div>

      {/* Section 2: Key metrics */}
      <div className="section">
        <div className="section-title">Metriche di sintesi</div>
        <div className="kpi-grid">
          <Kpi label="Pareggio operativo" value={ml(breakEvenOperational)} accent />
          <Kpi label="Pareggio investimento" value={ml(breakEvenCumulative)} />
          <Kpi label="CAC medio" value={eur(cacBlended)} />
          <Kpi label="Cash minimo" value={eur(cashMinimum)}
               sub={"Raggiunto a " + ml(cashMinimumMonth)} />
          <Kpi label="Agenti attivi" value={num(last.activeAgents)} />
        </div>
      </div>

      {/* Section 3: CAC per canale */}
      <div className="section">
        <div className="section-title">CAC per canale (costo acquisizione cliente)</div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 14 }}>
          {cacChannels.map((ch) => (
            <div key={ch.name} className="card" style={{ borderLeft: "3px solid " + ch.color }}>
              <div style={{ fontSize: 12, color: "#8B98B0", marginBottom: 4 }}>{ch.name}</div>
              <div className="mono" style={{ fontSize: 24, fontWeight: 500 }}>{eur(ch.cac)}</div>
              <div className="text-faint" style={{ fontSize: 11, marginTop: 4 }}>per cliente acquisito</div>
            </div>
          ))}
          <div className="card" style={{ borderLeft: "3px solid #C4A962" }}>
            <div style={{ fontSize: 12, color: "#8B98B0", marginBottom: 4 }}>Media ponderata</div>
            <div className="mono gold" style={{ fontSize: 24, fontWeight: 500 }}>{eur(cacBlended)}</div>
            <div className="text-faint" style={{ fontSize: 11, marginTop: 4 }}>tutti i canali paid</div>
          </div>
        </div>
      </div>

      {/* Section 4: Piano assunzioni */}
      <div className="section">
        <div className="section-title">Piano assunzioni (automatico)</div>
        {hiringPlan.length === 0 ? (
          <div className="text-dim" style={{ fontSize: 13 }}>Nessuna assunzione prevista con i parametri attuali.</div>
        ) : (
          <div className="tbl-wrap">
            <table className="proj" style={{ fontSize: 13 }}>
              <thead>
                <tr>
                  <th style={{ textAlign: "left" }}>Mese</th>
                  <th style={{ textAlign: "left" }}>Ruolo</th>
                  <th>Trigger</th>
                  <th>Costo/mese</th>
                  <th>Costo/anno</th>
                </tr>
              </thead>
              <tbody>
                {hiringPlan.map((h, i) => (
                  <tr key={i}>
                    <td style={{ textAlign: "left" }}>
                      <span className="gold mono">{h.monthLabel}</span>
                    </td>
                    <td style={{ textAlign: "left", fontWeight: 600 }}>{h.role}</td>
                    <td className="text-dim">{h.trigger}</td>
                    <td className="mono">{eur(h.cost)}</td>
                    <td className="mono text-dim">{eur(h.cost * 12)}</td>
                  </tr>
                ))}
                <tr style={{ borderTop: "2px solid #2A3952" }}>
                  <td style={{ textAlign: "left" }} colSpan={3}>
                    <span style={{ fontWeight: 600 }}>Totale personale aggiuntivo a fine piano</span>
                  </td>
                  <td className="mono gold" style={{ fontWeight: 700 }}>
                    {eur(hiringPlan.reduce((s, h) => s + h.cost, 0))}
                  </td>
                  <td className="mono text-dim">
                    {eur(hiringPlan.reduce((s, h) => s + h.cost, 0) * 12)}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Section 5: Charts — 2×2 grid */}
      <div className="section">
        <div className="section-title">Grafici a 36 mesi</div>

        {/* Row 1 */}
        <div className="chart-row">
          {/* Chart 1: Clienti attivi + capacity line */}
          <div className="card">
            <div className="card-title">Clienti attivi vs capacita</div>
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={clientsData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid stroke="#1E2A3E" vertical={false} />
                <XAxis dataKey="monthLabel" tick={axTick} tickLine={false}
                       axisLine={axLine} interval={2} />
                <YAxis tick={axTick} tickLine={false} axisLine={axLine} />
                <Tooltip contentStyle={tooltipStyle} />
                <Legend wrapperStyle={{ fontSize: 12, color: "#8B98B0" }} />
                <ReferenceLine x={results[12]?.monthLabel} stroke="#C4A962"
                               strokeDasharray="4 4" label={{ value: "Lancio", fill: "#C4A962", fontSize: 11 }} />
                <Bar dataKey="totalClients" name="Clienti attivi" fill="#C4A962" />
                <Line type="stepAfter" dataKey="maxCapacity" name="Capacita max"
                      stroke="#F59E0B" strokeWidth={2} strokeDasharray="6 3" dot={false} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          {/* Chart 2: Cash flow */}
          <div className="card">
            <div className="card-title">Cash flow ({eur(results[0]?.cashRemaining || 0)})</div>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={results} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="cashGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#4ADE80" stopOpacity={0.6} />
                    <stop offset="100%" stopColor="#F87171" stopOpacity={0.3} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="#1E2A3E" vertical={false} />
                <XAxis dataKey="monthLabel" tick={axTick} tickLine={false}
                       axisLine={axLine} interval={2} />
                <YAxis tick={axTick} tickLine={false} axisLine={axLine}
                       tickFormatter={(v) => "\u20AC" + Math.round(v / 1000) + "k"} />
                <Tooltip contentStyle={tooltipStyle} formatter={tooltipFmt} />
                <ReferenceLine y={0} stroke="#F87171" strokeWidth={1.5} />
                <ReferenceLine y={30000} stroke="#F59E0B" strokeDasharray="6 3"
                               label={{ value: "Riserva minima", fill: "#F59E0B", fontSize: 11, position: "insideTopLeft" }} />
                <Area type="monotone" dataKey="cashRemaining" name="Cash rimanente"
                      stroke="#4ADE80" fill="url(#cashGrad)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Row 2 */}
        <div className="chart-row">
          {/* Chart 3: Costi vs Ricavi */}
          <div className="card">
            <div className="card-title">Costi vs Ricavi mensili</div>
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={results} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid stroke="#1E2A3E" vertical={false} />
                <XAxis dataKey="monthLabel" tick={axTick} tickLine={false}
                       axisLine={axLine} interval={2} />
                <YAxis tick={axTick} tickLine={false} axisLine={axLine}
                       tickFormatter={(v) => "\u20AC" + Math.round(v / 1000) + "k"} />
                <Tooltip contentStyle={tooltipStyle} formatter={tooltipFmt} />
                <Legend wrapperStyle={{ fontSize: 12, color: "#8B98B0" }} />
                {Object.entries(costColors).map(([key, [name, color]]) => (
                  <Bar key={key} dataKey={key} name={name} stackId="costs" fill={color} />
                ))}
                <Line type="monotone" dataKey="mrr" name="MRR" stroke="#4ADE80"
                      strokeWidth={2} dot={false} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          {/* Chart 4: Acquisizione per canale */}
          <div className="card">
            <div className="card-title">Acquisizione per canale</div>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={channelData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid stroke="#1E2A3E" vertical={false} />
                <XAxis dataKey="monthLabel" tick={axTick} tickLine={false}
                       axisLine={axLine} interval={2} />
                <YAxis tick={axTick} tickLine={false} axisLine={axLine} />
                <Tooltip contentStyle={tooltipStyle} />
                <Legend wrapperStyle={{ fontSize: 12, color: "#8B98B0" }} />
                {Object.entries(chanColors).map(([key, [name, color]]) => (
                  <Area key={key} type="monotone" dataKey={key} name={name}
                        stackId="ch" stroke={color} fill={color} fillOpacity={0.7} />
                ))}
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Row 3: Team & utilization */}
        <div className="chart-row" style={{ marginTop: 14 }}>
          <div className="card">
            <div className="card-title">Team e utilizzo capacita</div>
            <ResponsiveContainer width="100%" height={250}>
              <ComposedChart data={staffData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid stroke="#1E2A3E" vertical={false} />
                <XAxis dataKey="monthLabel" tick={axTick} tickLine={false}
                       axisLine={axLine} interval={2} />
                <YAxis yAxisId="left" tick={axTick} tickLine={false} axisLine={axLine} />
                <YAxis yAxisId="right" orientation="right" tick={axTick} tickLine={false}
                       axisLine={axLine} tickFormatter={(v) => v + "%"} domain={[0, 100]} />
                <Tooltip contentStyle={tooltipStyle} />
                <Legend wrapperStyle={{ fontSize: 12, color: "#8B98B0" }} />
                <Bar yAxisId="left" dataKey="staffCount" name="Team (persone)" fill="#A78BFA" />
                <Line yAxisId="right" type="monotone" dataKey="utilization" name="Utilizzo %"
                      stroke="#F59E0B" strokeWidth={2} dot={false} />
                <Line yAxisId="right" type="monotone" dataKey="budgetFactor" name="Budget ads %"
                      stroke="#4ADE80" strokeWidth={2} strokeDasharray="4 3" dot={false} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
