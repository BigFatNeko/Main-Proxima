/* ============================================================
   Controls — Slider panels for all funnel parameters
   ============================================================ */

window.PROXIMA = window.PROXIMA || {};

window.PROXIMA.Controls = function Controls({ params, setParams, onReset }) {
  const [open, setOpen] = React.useState({
    google: true, meta: true, linkedin: false,
    seo: true, social: false, referral: true,
    borrowed: false, funnel: true, capacity: true, business: true
  });

  const toggle = (k) => setOpen({ ...open, [k]: !open[k] });

  // Helper: update a nested path in params
  const update = (path, value) => {
    const next = JSON.parse(JSON.stringify(params));
    let ref = next;
    for (let i = 0; i < path.length - 1; i++) ref = ref[path[i]];
    ref[path[path.length - 1]] = value;
    setParams(next);
  };

  const updateArray = (path, idx, value) => {
    const next = JSON.parse(JSON.stringify(params));
    let ref = next;
    for (let i = 0; i < path.length - 1; i++) ref = ref[path[i]];
    ref[path[path.length - 1]][idx] = value;
    setParams(next);
  };

  const Slider = ({ label, value, min, max, step, fmt, onChange }) => (
    <div className="slider-row">
      <div className="slider-label">
        <span className="name">{label}</span>
        <span className="val">{fmt ? fmt(value) : value}</span>
      </div>
      <input
        type="range" min={min} max={max} step={step} value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
      />
    </div>
  );

  const Panel = ({ id, title, children }) => (
    <div className="panel">
      <div className="panel-header" onClick={() => toggle(id)}>
        <h3>{title}</h3>
        <span className="chev">{open[id] ? "▼" : "▶"}</span>
      </div>
      {open[id] && <div className="panel-body">{children}</div>}
    </div>
  );

  const pct = (v) => (v * 100).toFixed(1) + "%";
  const eur = (v) => "€" + Math.round(v).toLocaleString("it-IT");
  const num = (v) => Number(v).toFixed(2);

  const PhaseBudgets = ({ channel, label }) => (
    <>
      <div className="uppercase text-faint" style={{ marginTop: 6, marginBottom: 6 }}>
        Budget {label} per fase
      </div>
      {["F1", "F2", "F3", "F4", "F5"].map((ph, i) => (
        <Slider
          key={ph} label={`Fase ${i + 1} (${ph})`}
          value={params[channel].budgetByPhase[i + 1]}
          min={0} max={6000} step={100} fmt={eur}
          onChange={(v) => updateArray([channel, "budgetByPhase"], i + 1, v)}
        />
      ))}
    </>
  );

  return (
    <div>
      <div className="brand">
        <h1>Proxima</h1>
        <span className="brand-tag">Funnel Model</span>
      </div>
      <div className="subtitle">Bottom-up · 24 mesi · sliders in tempo reale</div>

      <div className="toolbar">
        <button className="btn-ghost btn" onClick={onReset}>↻ Reset</button>
      </div>

      <Panel id="funnel" title="Post-funnel & Show-rate">
        <Slider label="Show-rate (% prenotazioni che si presenta)"
          value={params.showRate} min={0.3} max={1} step={0.01} fmt={pct}
          onChange={(v) => update(["showRate"], v)} />
        <Slider label="Check-up → cliente pagante"
          value={params.checkupToClient} min={0.1} max={0.7} step={0.01} fmt={pct}
          onChange={(v) => update(["checkupToClient"], v)} />
      </Panel>

      <Panel id="google" title="Google Ads">
        <Slider label="CPC medio" value={params.google.cpc}
          min={0.5} max={5} step={0.05} fmt={(v) => "€" + num(v)}
          onChange={(v) => update(["google", "cpc"], v)} />
        <Slider label="Click → calcolatore"
          value={params.google.clickToCalc} min={0.1} max={0.9} step={0.01} fmt={pct}
          onChange={(v) => update(["google", "clickToCalc"], v)} />
        <Slider label="Calc → prenotazione"
          value={params.google.calcToBooking} min={0.01} max={0.25} step={0.005} fmt={pct}
          onChange={(v) => update(["google", "calcToBooking"], v)} />
        <PhaseBudgets channel="google" label="Google" />
      </Panel>

      <Panel id="meta" title="Meta Ads (IG + FB)">
        <Slider label="CPC medio" value={params.meta.cpc}
          min={0.2} max={3} step={0.05} fmt={(v) => "€" + num(v)}
          onChange={(v) => update(["meta", "cpc"], v)} />
        <Slider label="Click → calcolatore"
          value={params.meta.clickToCalc} min={0.05} max={0.7} step={0.01} fmt={pct}
          onChange={(v) => update(["meta", "clickToCalc"], v)} />
        <Slider label="Calc → prenotazione"
          value={params.meta.calcToBooking} min={0.01} max={0.2} step={0.005} fmt={pct}
          onChange={(v) => update(["meta", "calcToBooking"], v)} />
        <PhaseBudgets channel="meta" label="Meta" />
      </Panel>

      <Panel id="linkedin" title="LinkedIn Ads (dal mese +9)">
        <Slider label="CPC medio" value={params.linkedin.cpc}
          min={2} max={12} step={0.1} fmt={(v) => "€" + num(v)}
          onChange={(v) => update(["linkedin", "cpc"], v)} />
        <Slider label="Click → calcolatore"
          value={params.linkedin.clickToCalc} min={0.1} max={0.9} step={0.01} fmt={pct}
          onChange={(v) => update(["linkedin", "clickToCalc"], v)} />
        <Slider label="Calc → prenotazione"
          value={params.linkedin.calcToBooking} min={0.01} max={0.2} step={0.005} fmt={pct}
          onChange={(v) => update(["linkedin", "calcToBooking"], v)} />
        <Slider label="Mese di inizio (index)"
          value={params.linkedin.startMonth} min={10} max={24} step={1} fmt={(v) => `M${v - 6}`}
          onChange={(v) => update(["linkedin", "startMonth"], v)} />
        <PhaseBudgets channel="linkedin" label="LinkedIn" />
      </Panel>

      <Panel id="seo" title="SEO Organico">
        <Slider label="Visite base (mese 1)" value={params.seo.baseVisits}
          min={0} max={300} step={5} fmt={(v) => v + "/mese"}
          onChange={(v) => update(["seo", "baseVisits"], v)} />
        <Slider label="Crescita mensile compound"
          value={params.seo.growthRate} min={0} max={0.5} step={0.01} fmt={pct}
          onChange={(v) => update(["seo", "growthRate"], v)} />
        <Slider label="Visita → calcolatore"
          value={params.seo.visitToCalc} min={0.02} max={0.5} step={0.01} fmt={pct}
          onChange={(v) => update(["seo", "visitToCalc"], v)} />
        <Slider label="Calc → prenotazione"
          value={params.seo.calcToBooking} min={0.01} max={0.2} step={0.005} fmt={pct}
          onChange={(v) => update(["seo", "calcToBooking"], v)} />
      </Panel>

      <Panel id="social" title="Social Organico">
        <Slider label="Visite base al sito (mese 1)" value={params.social.baseVisits}
          min={0} max={300} step={5} fmt={(v) => v + "/mese"}
          onChange={(v) => update(["social", "baseVisits"], v)} />
        <Slider label="Crescita mensile compound"
          value={params.social.growthRate} min={0} max={0.4} step={0.01} fmt={pct}
          onChange={(v) => update(["social", "growthRate"], v)} />
        <Slider label="Visita → calcolatore"
          value={params.social.visitToCalc} min={0.02} max={0.4} step={0.01} fmt={pct}
          onChange={(v) => update(["social", "visitToCalc"], v)} />
        <Slider label="Calc → prenotazione"
          value={params.social.calcToBooking} min={0.01} max={0.15} step={0.005} fmt={pct}
          onChange={(v) => update(["social", "calcToBooking"], v)} />
      </Panel>

      <Panel id="referral" title="Referral (dal mese +9)">
        <Slider label="% clienti attivi che porta 1 ref/mese"
          value={params.referral.ratePerClient} min={0} max={0.2} step={0.005} fmt={pct}
          onChange={(v) => update(["referral", "ratePerClient"], v)} />
        <Slider label="Referral → prenotazione"
          value={params.referral.bookingRate} min={0.3} max={1} step={0.02} fmt={pct}
          onChange={(v) => update(["referral", "bookingRate"], v)} />
        <Slider label="Mese di inizio referral"
          value={params.referral.startMonth} min={10} max={24} step={1} fmt={(v) => `M${v - 6}`}
          onChange={(v) => update(["referral", "startMonth"], v)} />
      </Panel>

      <Panel id="borrowed" title="Borrowed (PR + podcast + eventi)">
        <div className="uppercase text-faint" style={{ marginBottom: 6 }}>
          Prenotazioni/mese per fase
        </div>
        {["F1", "F2", "F3", "F4", "F5"].map((ph, i) => (
          <Slider key={ph} label={`Fase ${i + 1} (${ph})`}
            value={params.borrowed.bookingsByPhase[i + 1]}
            min={0} max={40} step={1} fmt={(v) => v + "/mese"}
            onChange={(v) => updateArray(["borrowed", "bookingsByPhase"], i + 1, v)} />
        ))}
      </Panel>

      <Panel id="capacity" title="Capacità operativa">
        <Slider label="Ore/settimana founder"
          value={params.founderHoursPerWeek} min={5} max={50} step={1} fmt={(v) => v + "h"}
          onChange={(v) => update(["founderHoursPerWeek"], v)} />
        <Slider label="Ore per cliente (check-up + onboarding)"
          value={params.hoursPerClient} min={1} max={8} step={0.25} fmt={(v) => v + "h"}
          onChange={(v) => update(["hoursPerClient"], v)} />
        <Slider label="Mese entrata 2° consulente"
          value={params.secondConsultantStartMonth} min={7} max={24} step={1} fmt={(v) => `M${v - 6}`}
          onChange={(v) => update(["secondConsultantStartMonth"], v)} />
        <Slider label="Ore/settimana 2° consulente"
          value={params.secondConsultantHoursPerWeek} min={5} max={50} step={1} fmt={(v) => v + "h"}
          onChange={(v) => update(["secondConsultantHoursPerWeek"], v)} />
      </Panel>

      <Panel id="business" title="Business">
        <Slider label="ARPU (parcella media annua)"
          value={params.arpu} min={300} max={900} step={10} fmt={eur}
          onChange={(v) => update(["arpu"], v)} />
        <Slider label="Churn mensile"
          value={params.churnMonthly} min={0} max={0.05} step={0.002} fmt={pct}
          onChange={(v) => update(["churnMonthly"], v)} />
      </Panel>
    </div>
  );
};
