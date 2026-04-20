/* ============================================================
   Dashboard — KPI cards + Recharts 2.12.7 visualizations
   Receives { sim } with 36-month simulation results.
   ============================================================ */

window.PROXIMA = window.PROXIMA || {};

window.PROXIMA.Dashboard = function Dashboard({ sim }) {
  const {
    ResponsiveContainer, ComposedChart, AreaChart, Bar, Line, Area,
    XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceLine
  } = window.Recharts;

  const { results, breakEvenOperational, breakEvenCumulative,
          cacBlended, cashMinimum, cashMinimumMonth } = sim;

  const eur = (v) => "€\u00A0" + Math.round(v).toLocaleString("it-IT");
  const num = (v) => Math.round(v).toLocaleString("it-IT");
  const ml = (idx) => idx != null && results[idx] ? results[idx].monthLabel : "Mai";
  const last = results[results.length - 1];

  const tooltipFmt = (v) => eur(v);
  const tooltipStyle = {
    backgroundColor: "#121E30", border: "1px solid #2A3952",
    borderRadius: 8, fontFamily: "DM Mono, monospace", fontSize: 12, color: "#E8ECF2"
  };
  const axTick = { fill: "#8B98B0", fontSize: 11 };
  const axLine = { stroke: "#1E2A3E" };
  const every3 = (_, i) => i % 3 === 0;

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

  /* ── Capacity line data ── */
  const clientsData = results.map((r) => ({
    monthLabel: r.monthLabel, totalClients: r.totalClients,
    capacity: r.capacityLimited ? r.totalClients : null
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

      {/* Section 3: Charts — 2×2 grid */}
      <div className="section">
        <div className="section-title">Grafici a 36 mesi</div>

        {/* Row 1 */}
        <div className="chart-row">
          {/* Chart 1: Clienti attivi */}
          <div className="card">
            <div className="card-title">Clienti attivi (36 mesi)</div>
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
                <Line type="monotone" dataKey="capacity" name="Limite capacità"
                      stroke="#F59E0B" strokeWidth={2} strokeDasharray="6 3" dot={false} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          {/* Chart 2: Cash flow */}
          <div className="card">
            <div className="card-title">Cash flow (€180K)</div>
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
                       tickFormatter={(v) => "€" + Math.round(v / 1000) + "k"} />
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
                       tickFormatter={(v) => "€" + Math.round(v / 1000) + "k"} />
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
      </div>
    </div>
  );
};
