/* ============================================================
   Dashboard SCF — KPI cards + CAC per canale + Piano assunzioni + Charts
   v1 SCF: abbonati per fascia, utenti gratuiti, costi app/IA
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

  const eur = (v) => "€ " + Math.round(v).toLocaleString("it-IT");
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
    appCosts: ["App e IA", "#22D3EE"],
    personnelCosts: ["Personale", "#A78BFA"],
    marketingCosts: ["Marketing", "#F59E0B"]
  };

  const fasceData = results.map((r) => ({
    monthLabel: r.monthLabel,
    app: Math.round(r.clientsApp),
    monitor: Math.round(r.clientsMonitor),
    live: Math.round(r.clientsLive),
    freeUsers: Math.round(r.freeUsers)
  }));

  /* ── CAC per channel ── */
  const cacChannels = [
    { name: "Google Ads", cac: cacByChannel.google, color: "#4285F4" },
    { name: "Meta Ads", cac: cacByChannel.meta, color: "#E1306C" },
    { name: "LinkedIn Ads", cac: cacByChannel.linkedin, color: "#0077B5" }
  ].filter((c) => c.cac > 0);

  /* ── Staff data for chart ── */
  const staffData = results.filter((r) => r.month >= 13).map((r) => ({
    monthLabel: r.monthLabel,
    staffCount: r.staffCount,
    utilization: Math.round(r.liveUtilization * 100),
    budgetFactor: Math.round(r.budgetFactor * 100)
  }));

  /* ── AUM + S&P 500 data ── */
  const aumData = results.filter((r) => r.month >= 13).map((r) => ({
    monthLabel: r.monthLabel,
    aumMonitorato: Math.round(r.totalAUM / 1000),
    sp500Benchmark: Math.round(r.sp500BenchmarkValue / 1000)
  }));

  const hasMortgage = results.some((r) => r.mortgageCost > 0);
  const hasTax = results.some((r) => r.taxCost > 0);

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
                <Kpi label="Abbonati paganti" value={num(r.totalClients)}
                     sub={num(r.clientsApp) + " App · " + num(r.clientsMonitor) + " Monitor · " + num(r.clientsLive) + " Live"} />
                <Kpi label="Utenti gratuiti (Check-up)" value={num(r.freeUsers)} />
                <Kpi label="Ricavi mensili (MRR)" value={eur(r.mrr)}
                     sub={"ARPU " + eur(r.arpuEff) + "/anno"} />
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
        <div className="section-title">CAC per canale (costo acquisizione abbonato)</div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 14 }}>
          {cacChannels.map((ch) => (
            <div key={ch.name} className="card" style={{ borderLeft: "3px solid " + ch.color }}>
              <div style={{ fontSize: 12, color: "#8B98B0", marginBottom: 4 }}>{ch.name}</div>
              <div className="mono" style={{ fontSize: 24, fontWeight: 500 }}>{eur(ch.cac)}</div>
              <div className="text-faint" style={{ fontSize: 11, marginTop: 4 }}>per abbonato acquisito</div>
            </div>
          ))}
          <div className="card" style={{ borderLeft: "3px solid #C4A962" }}>
            <div style={{ fontSize: 12, color: "#8B98B0", marginBottom: 4 }}>Media ponderata</div>
            <div className="mono gold" style={{ fontSize: 24, fontWeight: 500 }}>{eur(cacBlended)}</div>
            <div className="text-faint" style={{ fontSize: 11, marginTop: 4 }}>tutti i canali paid</div>
          </div>
        </div>
        <div className="text-faint" style={{ fontSize: 11, marginTop: 8 }}>
          ⚠ Con ARPU blended basso, confronta sempre il CAC col valore-vita della fascia: un CAC sostenibile
          per un cliente Live (€{num((results[0] && 90*12) || 1080)}/anno) può non esserlo per un cliente App.
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

      {/* Section 5: AUM monitorato + S&P 500 benchmark */}
      <div className="section">
        <div className="section-title">Patrimonio monitorato (Monitor + Live) vs S&P 500</div>
        <div className="kpi-grid" style={{ marginBottom: 16 }}>
          <Kpi label="AUM monitorato a M0" value={eur(results[12]?.totalAUM || 0)} sub="Lancio" />
          <Kpi label="AUM monitorato a M+12" value={eur(results[24]?.totalAUM || 0)} />
          <Kpi label="AUM monitorato a M+23" value={eur(last.totalAUM)} />
          <Kpi label="S&P 500 benchmark a M+23"
            value={eur(last.sp500BenchmarkValue || 0)}
            sub="Partendo dall'AUM a M0" />
        </div>
        <div className="card">
          <div className="card-title">Patrimonio monitorato (€k) — KPI di credibilità, non genera ricavi</div>
          <ResponsiveContainer width="100%" height={280}>
            <ComposedChart data={aumData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
              <CartesianGrid stroke="#1E2A3E" vertical={false} />
              <XAxis dataKey="monthLabel" tick={axTick} tickLine={false} axisLine={axLine} interval={2} />
              <YAxis tick={axTick} tickLine={false} axisLine={axLine}
                tickFormatter={(v) => "€" + v + "k"} />
              <Tooltip contentStyle={tooltipStyle} formatter={(v) => "€" + v.toLocaleString("it-IT") + "k"} />
              <Legend wrapperStyle={{ fontSize: 12, color: "#8B98B0" }} />
              <Area type="monotone" dataKey="aumMonitorato" name="AUM monitorato"
                stroke="#C4A962" fill="rgba(196,169,98,0.2)" strokeWidth={2} />
              <Line type="monotone" dataKey="sp500Benchmark" name="S&P 500 benchmark"
                stroke="#4ADE80" strokeWidth={2} strokeDasharray="5 3" dot={false} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Section 6: Mortgage + Tax summary (conditional) */}
      {(hasMortgage || hasTax) && (
        <div className="section">
          <div className="section-title">Mutuo e Fiscalità</div>
          <div className="kpi-grid">
            {hasMortgage && (
              <Kpi label="Costo mutuo totale (36 mesi)"
                value={eur(results.reduce((s, r) => s + r.mortgageCost, 0))}
                sub="Interessi + rimborso capitale" />
            )}
            {hasTax && (
              <Kpi label="Tasse totali stimate (36 mesi)"
                value={eur(results.reduce((s, r) => s + r.taxCost, 0))}
                sub="IRES + IRAP (provisione mensile)" />
            )}
            {hasMortgage && (
              <Kpi label="Rata mensile mutuo (post pre-amm.)"
                value={eur(results.find((r) => r.mortgageCost > 0 && r.month > (results[0]?.month || 0) + 18)?.mortgageCost || results.find((r) => r.mortgageCost > 0)?.mortgageCost || 0)} />
            )}
          </div>
        </div>
      )}

      {/* Section 7: Charts — 2×2 grid */}
      <div className="section">
        <div className="section-title">Grafici a 36 mesi</div>

        {/* Row 1 */}
        <div className="chart-row">
          {/* Chart 1: Abbonati per fascia + utenti gratuiti */}
          <div className="card">
            <div className="card-title">Abbonati per fascia + utenti gratuiti</div>
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={fasceData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid stroke="#1E2A3E" vertical={false} />
                <XAxis dataKey="monthLabel" tick={axTick} tickLine={false}
                       axisLine={axLine} interval={2} />
                <YAxis yAxisId="left" tick={axTick} tickLine={false} axisLine={axLine} />
                <YAxis yAxisId="right" orientation="right" tick={axTick} tickLine={false} axisLine={axLine} />
                <Tooltip contentStyle={tooltipStyle} />
                <Legend wrapperStyle={{ fontSize: 12, color: "#8B98B0" }} />
                <ReferenceLine yAxisId="left" x={results[12]?.monthLabel} stroke="#C4A962"
                               strokeDasharray="4 4" label={{ value: "Lancio", fill: "#C4A962", fontSize: 11 }} />
                <Bar yAxisId="left" dataKey="app" name="App" stackId="f" fill="#60A5FA" />
                <Bar yAxisId="left" dataKey="monitor" name="Monitor" stackId="f" fill="#A78BFA" />
                <Bar yAxisId="left" dataKey="live" name="Live" stackId="f" fill="#C4A962" />
                <Line yAxisId="right" type="monotone" dataKey="freeUsers" name="Utenti gratuiti"
                      stroke="#4ADE80" strokeWidth={2} strokeDasharray="4 3" dot={false} />
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

          {/* Chart 4: Iscrizioni Check-up per canale */}
          <div className="card">
            <div className="card-title">Iscrizioni al Check-up per canale</div>
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
            <div className="card-title">Team e slot Live</div>
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
                <Line yAxisId="right" type="monotone" dataKey="utilization" name="Slot Live %"
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
