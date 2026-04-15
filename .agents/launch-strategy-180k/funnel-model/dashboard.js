/* ============================================================
   Dashboard — KPI cards + Recharts visualizations
   ============================================================ */

window.PROXIMA = window.PROXIMA || {};

window.PROXIMA.Dashboard = function Dashboard({ sim }) {
  const R = window.Recharts;
  const { results, breakEvenMonth, cacBlended, budgetPaidCumulativeByChannel } = sim;
  const targets = window.PROXIMA.strategyTargets;

  // Milestones: index 13=M+6, 19=M+12, 24=M+18
  const milestones = [
    { key: "m6", idx: 13, label: "M+6 (lancio pubblico)" },
    { key: "m12", idx: 19, label: "M+12" },
    { key: "m18", idx: 24, label: "M+18 (fine strategia)" }
  ];

  const eur = (v) => "€" + Math.round(v).toLocaleString("it-IT");
  const num = (v) => Math.round(v).toLocaleString("it-IT");

  const deltaPill = (actual, target) => {
    if (target === 0) return null;
    const d = (actual - target) / target;
    const cls = d >= 0.02 ? "delta-pos" : d <= -0.02 ? "delta-neg" : "delta-flat";
    const sign = d >= 0 ? "+" : "";
    return <span className={`kpi-delta ${cls}`}>{sign}{(d * 100).toFixed(0)}% vs target</span>;
  };

  const Kpi = ({ label, value, sub, delta, accent }) => (
    <div className={`kpi-card ${accent ? "accent" : ""}`}>
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">{value}</div>
      {sub && <div className="kpi-sub">{sub}</div>}
      {delta}
    </div>
  );

  // Break-even vs strategy target (mese 17-18 = idx 23-24)
  const beLabel = breakEvenMonth
    ? `Mese ${breakEvenMonth} (strategy M${breakEvenMonth - 6})`
    : "Non raggiunto a 24 mesi";

  // Final month row
  const last = results[results.length - 1];

  // Capacity bottleneck detection
  const firstBottleneck = results.find((r) => r.capacityLimited);

  // Chart data: clients actual vs target
  const clientsChart = results.map((r) => ({
    m: `M${r.strategyMonth >= 0 ? "+" : ""}${r.strategyMonth}`,
    mIdx: r.month,
    actual: Math.round(r.totalClients),
    target: targets.clients[r.month] || null,
    maxCap: Math.round(r.maxClientsByCapacity)
  }));

  // Stacked area: new clients by channel
  const stackData = results.map((r) => ({
    m: `M${r.strategyMonth >= 0 ? "+" : ""}${r.strategyMonth}`,
    Google: +r.byChannel.google.toFixed(2),
    Meta: +r.byChannel.meta.toFixed(2),
    LinkedIn: +r.byChannel.linkedin.toFixed(2),
    SEO: +r.byChannel.seo.toFixed(2),
    Social: +r.byChannel.social.toFixed(2),
    Referral: +r.byChannel.referral.toFixed(2),
    Borrowed: +r.byChannel.borrowed.toFixed(2)
  }));

  // Revenue cumulato vs investment
  const revChart = results.map((r) => ({
    m: `M${r.strategyMonth >= 0 ? "+" : ""}${r.strategyMonth}`,
    cumRev: Math.round(r.cumulativeRevenue),
    cumSpend: Math.round(r.cumulativeSpend),
    target: 180000
  }));

  const chanColors = {
    Google: "#60A5FA", Meta: "#F472B6", LinkedIn: "#818CF8",
    SEO: "#4ADE80", Social: "#FBBF24",
    Referral: "#C4A962", Borrowed: "#F87171"
  };

  const tooltipStyle = {
    backgroundColor: "#121E30",
    border: "1px solid #2A3952",
    borderRadius: 8,
    fontFamily: "DM Mono, monospace",
    fontSize: 12,
    color: "#E8ECF2"
  };

  return (
    <div>
      {/* Milestone KPIs */}
      <div className="section">
        <div className="section-title">KPI alle milestone della strategia</div>
        {milestones.map((ms) => {
          const r = results[ms.idx - 1];
          if (!r) return null;
          const targetClients = targets.clients[ms.idx] || 0;
          const targetARR = targets.milestoneARR[ms.idx] || null;
          return (
            <div key={ms.key} style={{ marginBottom: 18 }}>
              <div style={{ display: "flex", alignItems: "baseline", gap: 12, marginBottom: 10 }}>
                <span className="uppercase gold">{ms.label}</span>
                <span className="text-faint mono" style={{ fontSize: 11 }}>
                  index mese {ms.idx}
                </span>
              </div>
              <div className="kpi-grid">
                <Kpi
                  label="Clienti totali"
                  value={num(r.totalClients)}
                  sub={`target strategia: ${targetClients}`}
                  delta={deltaPill(r.totalClients, targetClients)}
                  accent
                />
                <Kpi
                  label="ARR"
                  value={eur(r.arr)}
                  sub={targetARR ? `target: ${eur(targetARR)}` : null}
                  delta={targetARR ? deltaPill(r.arr, targetARR) : null}
                />
                <Kpi
                  label="Nuovi clienti nel mese"
                  value={num(r.newClients)}
                  sub={r.capacityLimited ? "⚠ limitato da capacità" : `teorico: ${num(r.newClientsTheoretical)}`}
                />
                <Kpi
                  label="Prenotazioni check-up"
                  value={num(r.bookings.total)}
                  sub={`di cui presenti: ${num(r.actualCheckups)}`}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Break-even & CAC */}
      <div className="section">
        <div className="section-title">Break-even & Economics</div>
        <div className="kpi-grid">
          <Kpi label="Break-even (€180K cumulato)" value={beLabel} accent />
          <Kpi label="Revenue cumulato (M+18)" value={eur(last.cumulativeRevenue)}
            sub={`target strategia: €167.500`} />
          <Kpi label="Spesa cumulata (M+18)" value={eur(last.cumulativeSpend)}
            sub="paid + fixed ops" />
          <Kpi label="Blended CAC (M+12)" value={eur(cacBlended.m12)}
            sub={`M+18: ${eur(cacBlended.m18)}`} />
        </div>
      </div>

      {/* Bottleneck banner */}
      {firstBottleneck && (
        <div className="section">
          <div className="warn-banner">
            <span className="dot"></span>
            <div>
              <strong>Collo di bottiglia capacità</strong> dal mese <span className="mono gold">
                M{firstBottleneck.strategyMonth >= 0 ? "+" : ""}{firstBottleneck.strategyMonth}
              </span>: la domanda supera le {num(firstBottleneck.maxClientsByCapacity)} ore/mese disponibili.
              Valuta: più ore founder, ingresso anticipato 2° consulente, o ridurre paid ads.
            </div>
          </div>
        </div>
      )}

      {/* Charts */}
      <div className="section">
        <div className="section-title">Crescita clienti — bottom-up vs target strategia</div>
        <div className="card" style={{ padding: 16 }}>
          <R.ResponsiveContainer width="100%" height={320}>
            <R.ComposedChart data={clientsChart} margin={{ top: 10, right: 24, left: 0, bottom: 0 }}>
              <R.CartesianGrid stroke="#1E2A3E" vertical={false} />
              <R.XAxis dataKey="m" tick={{ fill: "#8B98B0", fontSize: 11 }} tickLine={false} axisLine={{ stroke: "#1E2A3E" }} />
              <R.YAxis tick={{ fill: "#8B98B0", fontSize: 11 }} tickLine={false} axisLine={{ stroke: "#1E2A3E" }} />
              <R.Tooltip contentStyle={tooltipStyle} />
              <R.Legend wrapperStyle={{ fontSize: 12, color: "#8B98B0" }} />
              <R.Area type="monotone" dataKey="maxCap" name="Capacità max (ore/3.5)" stroke="#F59E0B" fill="#F59E0B" fillOpacity={0.08} strokeDasharray="4 4" />
              <R.Line type="monotone" dataKey="actual" name="Clienti (modello)" stroke="#C4A962" strokeWidth={2.5} dot={false} />
              <R.Line type="monotone" dataKey="target" name="Target strategia" stroke="#60A5FA" strokeWidth={1.5} strokeDasharray="5 5" dot={false} />
            </R.ComposedChart>
          </R.ResponsiveContainer>
        </div>
      </div>

      <div className="section">
        <div className="section-title">Composizione nuovi clienti per canale</div>
        <div className="card" style={{ padding: 16 }}>
          <R.ResponsiveContainer width="100%" height={280}>
            <R.AreaChart data={stackData} margin={{ top: 10, right: 24, left: 0, bottom: 0 }}>
              <R.CartesianGrid stroke="#1E2A3E" vertical={false} />
              <R.XAxis dataKey="m" tick={{ fill: "#8B98B0", fontSize: 11 }} tickLine={false} axisLine={{ stroke: "#1E2A3E" }} />
              <R.YAxis tick={{ fill: "#8B98B0", fontSize: 11 }} tickLine={false} axisLine={{ stroke: "#1E2A3E" }} />
              <R.Tooltip contentStyle={tooltipStyle} />
              <R.Legend wrapperStyle={{ fontSize: 12, color: "#8B98B0" }} />
              {Object.keys(chanColors).map((k) => (
                <R.Area key={k} type="monotone" dataKey={k} stackId="1"
                  stroke={chanColors[k]} fill={chanColors[k]} fillOpacity={0.75} />
              ))}
            </R.AreaChart>
          </R.ResponsiveContainer>
        </div>
      </div>

      <div className="section">
        <div className="section-title">Revenue cumulato vs investimento €180K</div>
        <div className="card" style={{ padding: 16 }}>
          <R.ResponsiveContainer width="100%" height={260}>
            <R.LineChart data={revChart} margin={{ top: 10, right: 24, left: 0, bottom: 0 }}>
              <R.CartesianGrid stroke="#1E2A3E" vertical={false} />
              <R.XAxis dataKey="m" tick={{ fill: "#8B98B0", fontSize: 11 }} tickLine={false} axisLine={{ stroke: "#1E2A3E" }} />
              <R.YAxis tick={{ fill: "#8B98B0", fontSize: 11 }} tickLine={false} axisLine={{ stroke: "#1E2A3E" }} tickFormatter={(v) => "€" + (v / 1000) + "k"} />
              <R.Tooltip contentStyle={tooltipStyle} formatter={(v) => eur(v)} />
              <R.Legend wrapperStyle={{ fontSize: 12, color: "#8B98B0" }} />
              <R.Line type="monotone" dataKey="cumRev" name="Revenue cumulato" stroke="#4ADE80" strokeWidth={2.5} dot={false} />
              <R.Line type="monotone" dataKey="cumSpend" name="Spesa cumulata" stroke="#F87171" strokeWidth={2} dot={false} />
              <R.Line type="monotone" dataKey="target" name="€180.000 target" stroke="#C4A962" strokeWidth={1.5} strokeDasharray="5 5" dot={false} />
            </R.LineChart>
          </R.ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
