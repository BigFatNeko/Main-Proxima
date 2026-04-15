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
    { key: "m6", idx: 13, label: "M+6 — lancio pubblico" },
    { key: "m12", idx: 19, label: "M+12 — fine primo anno" },
    { key: "m18", idx: 24, label: "M+18 — fine della strategia" }
  ];

  const eur = (v) => "€" + Math.round(v).toLocaleString("it-IT");
  const num = (v) => Math.round(v).toLocaleString("it-IT");

  const deltaPill = (actual, target) => {
    if (target === 0) return null;
    const d = (actual - target) / target;
    const cls = d >= 0.02 ? "delta-pos" : d <= -0.02 ? "delta-neg" : "delta-flat";
    const sign = d >= 0 ? "+" : "";
    return <span className={`kpi-delta ${cls}`}>{sign}{(d * 100).toFixed(0)}% vs obiettivo</span>;
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
    ? `Mese ${breakEvenMonth} (strategia M${breakEvenMonth - 6})`
    : "Non raggiunto nei 24 mesi";

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
        <div className="section-title">Risultati chiave alle tappe della strategia</div>
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
                  mese interno del modello: {ms.idx}
                </span>
              </div>
              <div className="kpi-grid">
                <Kpi
                  label="Clienti totali attivi"
                  value={num(r.totalClients)}
                  sub={`obiettivo strategia: ${targetClients}`}
                  delta={deltaPill(r.totalClients, targetClients)}
                  accent
                />
                <Kpi
                  label="Ricavi annui (se tutti rinnovano)"
                  value={eur(r.arr)}
                  sub={targetARR ? `obiettivo: ${eur(targetARR)}` : null}
                  delta={targetARR ? deltaPill(r.arr, targetARR) : null}
                />
                <Kpi
                  label="Nuovi clienti in questo mese"
                  value={num(r.newClients)}
                  sub={r.capacityLimited ? "⚠ ore di lavoro sature" : `senza limiti di capacità: ${num(r.newClientsTheoretical)}`}
                />
                <Kpi
                  label="Prenotazioni di check-up nel mese"
                  value={num(r.bookings.total)}
                  sub={`di cui si presentano: ${num(r.actualCheckups)}`}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Break-even & CAC */}
      <div className="section">
        <div className="section-title">Pareggio e costi di acquisizione clienti</div>
        <div className="kpi-grid">
          <Kpi label="Mese di pareggio (ricavi ≥ €180K investiti)" value={beLabel} accent />
          <Kpi label="Ricavi accumulati a fine strategia (M+18)" value={eur(last.cumulativeRevenue)}
            sub={`obiettivo strategia: €167.500`} />
          <Kpi label="Spesa totale a fine strategia (M+18)" value={eur(last.cumulativeSpend)}
            sub="pubblicità + costi fissi operativi" />
          <Kpi label="Costo medio per acquisire 1 cliente (a M+12)" value={eur(cacBlended.m12)}
            sub={`a M+18: ${eur(cacBlended.m18)}`} />
        </div>
      </div>

      {/* Bottleneck banner */}
      {firstBottleneck && (
        <div className="section">
          <div className="warn-banner">
            <span className="dot"></span>
            <div>
              <strong>Attenzione: ore di lavoro sature</strong> dal mese <span className="mono gold">
                M{firstBottleneck.strategyMonth >= 0 ? "+" : ""}{firstBottleneck.strategyMonth}
              </span>: la domanda di consulenze supera i {num(firstBottleneck.maxClientsByCapacity)} clienti/mese gestibili dal team.
              Soluzioni possibili: aumentare le ore del founder, anticipare l'ingresso del 2° consulente, o ridurre la pubblicità a pagamento.
            </div>
          </div>
        </div>
      )}

      {/* Charts */}
      <div className="section">
        <div className="section-title">Crescita clienti — modello calcolato vs obiettivo della strategia</div>
        <div className="card" style={{ padding: 16 }}>
          <R.ResponsiveContainer width="100%" height={320}>
            <R.ComposedChart data={clientsChart} margin={{ top: 10, right: 24, left: 0, bottom: 0 }}>
              <R.CartesianGrid stroke="#1E2A3E" vertical={false} />
              <R.XAxis dataKey="m" tick={{ fill: "#8B98B0", fontSize: 11 }} tickLine={false} axisLine={{ stroke: "#1E2A3E" }} />
              <R.YAxis tick={{ fill: "#8B98B0", fontSize: 11 }} tickLine={false} axisLine={{ stroke: "#1E2A3E" }} />
              <R.Tooltip contentStyle={tooltipStyle} />
              <R.Legend wrapperStyle={{ fontSize: 12, color: "#8B98B0" }} />
              <R.Area type="monotone" dataKey="maxCap" name="Capacità massima (limite ore di lavoro)" stroke="#F59E0B" fill="#F59E0B" fillOpacity={0.08} strokeDasharray="4 4" />
              <R.Line type="monotone" dataKey="actual" name="Clienti (calcolati dal modello)" stroke="#C4A962" strokeWidth={2.5} dot={false} />
              <R.Line type="monotone" dataKey="target" name="Obiettivo della strategia" stroke="#60A5FA" strokeWidth={1.5} strokeDasharray="5 5" dot={false} />
            </R.ComposedChart>
          </R.ResponsiveContainer>
        </div>
      </div>

      <div className="section">
        <div className="section-title">Da quali canali arrivano i nuovi clienti ogni mese</div>
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
        <div className="section-title">Ricavi accumulati vs investimento iniziale di €180.000</div>
        <div className="card" style={{ padding: 16 }}>
          <R.ResponsiveContainer width="100%" height={260}>
            <R.LineChart data={revChart} margin={{ top: 10, right: 24, left: 0, bottom: 0 }}>
              <R.CartesianGrid stroke="#1E2A3E" vertical={false} />
              <R.XAxis dataKey="m" tick={{ fill: "#8B98B0", fontSize: 11 }} tickLine={false} axisLine={{ stroke: "#1E2A3E" }} />
              <R.YAxis tick={{ fill: "#8B98B0", fontSize: 11 }} tickLine={false} axisLine={{ stroke: "#1E2A3E" }} tickFormatter={(v) => "€" + (v / 1000) + "k"} />
              <R.Tooltip contentStyle={tooltipStyle} formatter={(v) => eur(v)} />
              <R.Legend wrapperStyle={{ fontSize: 12, color: "#8B98B0" }} />
              <R.Line type="monotone" dataKey="cumRev" name="Ricavi accumulati" stroke="#4ADE80" strokeWidth={2.5} dot={false} />
              <R.Line type="monotone" dataKey="cumSpend" name="Spesa accumulata" stroke="#F87171" strokeWidth={2} dot={false} />
              <R.Line type="monotone" dataKey="target" name="Investimento di €180.000" stroke="#C4A962" strokeWidth={1.5} strokeDasharray="5 5" dot={false} />
            </R.LineChart>
          </R.ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
