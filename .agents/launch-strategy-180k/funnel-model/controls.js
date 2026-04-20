/* ============================================================
   Controls — Slider panels for all funnel parameters
   ============================================================ */

window.PROXIMA = window.PROXIMA || {};

// --- Formatters (module scope) ---
const pct = (v) => (v * 100).toFixed(1) + "%";
const eur = (v) => "€" + Math.round(v).toLocaleString("it-IT");
const num = (v) => Number(v).toFixed(2);
const monthLabel = (v) => { const d = v - 13; return d < 0 ? "M" + d : "M+" + d; };

// --- Slider (module scope) ---
function Slider({ label, value, min, max, step, fmt, onChange }) {
  return (
    <div className="slider-row">
      <div className="slider-label">
        <span className="name">{label}</span>
        <span className="val">{fmt ? fmt(value) : value}</span>
      </div>
      <input type="range" min={min} max={max} step={step} value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))} />
    </div>
  );
}

// --- Panel (module scope) ---
function Panel({ id, title, openState, onToggle, children }) {
  const isOpen = !!openState[id];
  return (
    <div className="panel">
      <div className="panel-header" onClick={() => onToggle(id)}>
        <h3>{title}</h3>
        <span className="chev">{isOpen ? "▼" : "▶"}</span>
      </div>
      {isOpen && <div className="panel-body">{children}</div>}
    </div>
  );
}

// --- PhaseBudgets (module scope, 7 phases) ---
const phaseLabels = [
  "Fondazione", "Qualificazioni", "Pre-lancio",
  "Alpha", "Beta", "Early Access", "Lancio"
];

function PhaseBudgets({ channel, label, params, updateArray }) {
  return (
    <>
      <div className="uppercase text-faint" style={{ marginTop: 6, marginBottom: 6 }}>
        Budget pubblicitario {label} per fase (€/mese)
      </div>
      {phaseLabels.map((ph, i) => (
        <Slider key={i} label={`Fase ${i + 1} (${ph})`}
          value={params[channel].budgetByPhase[i + 1]}
          min={0} max={6000} step={100} fmt={eur}
          onChange={(v) => updateArray([channel, "budgetByPhase"], i + 1, v)} />
      ))}
    </>
  );
}

// --- Main Controls component ---
window.PROXIMA.Controls = function Controls({ params, setParams, onReset }) {
  const [open, setOpen] = React.useState({
    scenario: true, funnel: true, google: true, meta: true, linkedin: false,
    seo: true, social: false, referral: true, borrowed: false, capacity: true,
    constitution: false, operating: false, personnel: true, business: true, capital: true
  });

  const toggle = React.useCallback(
    (k) => setOpen((prev) => ({ ...prev, [k]: !prev[k] })), []
  );

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

  return (
    <div>
      <div className="brand">
        <h1>Proxima</h1>
        <span className="brand-tag">Modello Funnel</span>
      </div>
      <div className="subtitle">Calcolato dai numeri veri · 24 mesi · aggiornamento in tempo reale</div>
      <div className="toolbar">
        <button className="btn-ghost btn" onClick={onReset}>↻ Reset</button>
      </div>

      {/* 1. Scenario di rischio */}
      <Panel id="scenario" title="Scenario di rischio" openState={open} onToggle={toggle}>
        {["base", "recessione", "crisi"].map((s) => (
          <button key={s} className={"btn" + (params.riskScenario === s ? " btn-active" : " btn-ghost")}
            style={{ marginRight: 6, marginBottom: 4, textTransform: "capitalize" }}
            onClick={() => update(["riskScenario"], s)}>{s}</button>
        ))}
      </Panel>

      {/* 2. Dopo la prenotazione */}
      <Panel id="funnel" title="Dopo la prenotazione" openState={open} onToggle={toggle}>
        <Slider label="% di persone che si presenta all'appuntamento"
          value={params.showRate} min={0.3} max={1} step={0.01} fmt={pct}
          onChange={(v) => update(["showRate"], v)} />
        <Slider label="% di check-up che diventano clienti paganti"
          value={params.checkupToClient} min={0.1} max={0.7} step={0.01} fmt={pct}
          onChange={(v) => update(["checkupToClient"], v)} />
      </Panel>

      {/* 3. Google Ads */}
      <Panel id="google" title="Google Ads" openState={open} onToggle={toggle}>
        <Slider label="Costo per click" value={params.google.cpc}
          min={0.5} max={5} step={0.05} fmt={(v) => "€" + num(v)}
          onChange={(v) => update(["google", "cpc"], v)} />
        <Slider label="% click → calcolatore" value={params.google.clickToCalc}
          min={0.1} max={0.9} step={0.01} fmt={pct}
          onChange={(v) => update(["google", "clickToCalc"], v)} />
        <Slider label="% calcolatore → prenotazione" value={params.google.calcToBooking}
          min={0.01} max={0.25} step={0.005} fmt={pct}
          onChange={(v) => update(["google", "calcToBooking"], v)} />
        <PhaseBudgets channel="google" label="Google" params={params} updateArray={updateArray} />
      </Panel>

      {/* 4. Meta Ads */}
      <Panel id="meta" title="Meta Ads" openState={open} onToggle={toggle}>
        <Slider label="Costo per click" value={params.meta.cpc}
          min={0.2} max={3} step={0.05} fmt={(v) => "€" + num(v)}
          onChange={(v) => update(["meta", "cpc"], v)} />
        <Slider label="% click → calcolatore" value={params.meta.clickToCalc}
          min={0.05} max={0.7} step={0.01} fmt={pct}
          onChange={(v) => update(["meta", "clickToCalc"], v)} />
        <Slider label="% calcolatore → prenotazione" value={params.meta.calcToBooking}
          min={0.01} max={0.2} step={0.005} fmt={pct}
          onChange={(v) => update(["meta", "calcToBooking"], v)} />
        <PhaseBudgets channel="meta" label="Meta" params={params} updateArray={updateArray} />
      </Panel>

      {/* 5. LinkedIn Ads */}
      <Panel id="linkedin" title="LinkedIn Ads (parte al mese +10)" openState={open} onToggle={toggle}>
        <Slider label="Costo per click" value={params.linkedin.cpc}
          min={2} max={12} step={0.1} fmt={(v) => "€" + num(v)}
          onChange={(v) => update(["linkedin", "cpc"], v)} />
        <Slider label="% click → calcolatore" value={params.linkedin.clickToCalc}
          min={0.1} max={0.9} step={0.01} fmt={pct}
          onChange={(v) => update(["linkedin", "clickToCalc"], v)} />
        <Slider label="% calcolatore → prenotazione" value={params.linkedin.calcToBooking}
          min={0.01} max={0.2} step={0.005} fmt={pct}
          onChange={(v) => update(["linkedin", "calcToBooking"], v)} />
        <Slider label="Mese di inizio" value={params.linkedin.startMonth}
          min={10} max={24} step={1} fmt={monthLabel}
          onChange={(v) => update(["linkedin", "startMonth"], v)} />
        <PhaseBudgets channel="linkedin" label="LinkedIn" params={params} updateArray={updateArray} />
      </Panel>

      {/* 6. SEO */}
      <Panel id="seo" title="SEO — traffico gratuito da Google" openState={open} onToggle={toggle}>
        <Slider label="Visite al sito nel primo mese" value={params.seo.baseVisits}
          min={0} max={300} step={5} fmt={(v) => v + "/mese"}
          onChange={(v) => update(["seo", "baseVisits"], v)} />
        <Slider label="Crescita mensile" value={params.seo.growthRate}
          min={0} max={0.5} step={0.01} fmt={pct}
          onChange={(v) => update(["seo", "growthRate"], v)} />
        <Slider label="% visitatori → calcolatore" value={params.seo.visitToCalc}
          min={0.02} max={0.5} step={0.01} fmt={pct}
          onChange={(v) => update(["seo", "visitToCalc"], v)} />
        <Slider label="% calcolatore → prenotazione" value={params.seo.calcToBooking}
          min={0.01} max={0.2} step={0.005} fmt={pct}
          onChange={(v) => update(["seo", "calcToBooking"], v)} />
      </Panel>

      {/* 7. Social organici */}
      <Panel id="social" title="Social organici" openState={open} onToggle={toggle}>
        <Slider label="Visite al sito nel primo mese" value={params.social.baseVisits}
          min={0} max={300} step={5} fmt={(v) => v + "/mese"}
          onChange={(v) => update(["social", "baseVisits"], v)} />
        <Slider label="Crescita mensile" value={params.social.growthRate}
          min={0} max={0.4} step={0.01} fmt={pct}
          onChange={(v) => update(["social", "growthRate"], v)} />
        <Slider label="% visitatori → calcolatore" value={params.social.visitToCalc}
          min={0.02} max={0.4} step={0.01} fmt={pct}
          onChange={(v) => update(["social", "visitToCalc"], v)} />
        <Slider label="% calcolatore → prenotazione" value={params.social.calcToBooking}
          min={0.01} max={0.15} step={0.005} fmt={pct}
          onChange={(v) => update(["social", "calcToBooking"], v)} />
      </Panel>

      {/* 8. Passaparola */}
      <Panel id="referral" title="Passaparola" openState={open} onToggle={toggle}>
        <Slider label="% clienti attivi che porta 1 contatto/mese"
          value={params.referral.ratePerClient} min={0} max={0.2} step={0.005} fmt={pct}
          onChange={(v) => update(["referral", "ratePerClient"], v)} />
        <Slider label="% contatti che prenota" value={params.referral.bookingRate}
          min={0.3} max={1} step={0.02} fmt={pct}
          onChange={(v) => update(["referral", "bookingRate"], v)} />
        <Slider label="Mese di inizio" value={params.referral.startMonth}
          min={10} max={24} step={1} fmt={monthLabel}
          onChange={(v) => update(["referral", "startMonth"], v)} />
      </Panel>

      {/* 9. PR, podcast ed eventi */}
      <Panel id="borrowed" title="PR, podcast ed eventi" openState={open} onToggle={toggle}>
        <div className="uppercase text-faint" style={{ marginBottom: 6 }}>
          Prenotazioni/mese per fase
        </div>
        {phaseLabels.map((ph, i) => (
          <Slider key={i} label={`Fase ${i + 1} (${ph})`}
            value={params.borrowed.bookingsByPhase[i + 1]}
            min={0} max={40} step={1} fmt={(v) => v + "/mese"}
            onChange={(v) => updateArray(["borrowed", "bookingsByPhase"], i + 1, v)} />
        ))}
      </Panel>

      {/* 10. Ore di lavoro disponibili */}
      <Panel id="capacity" title="Ore di lavoro disponibili" openState={open} onToggle={toggle}>
        <Slider label="Ore a settimana del founder" value={params.founderHoursPerWeek}
          min={5} max={50} step={1} fmt={(v) => v + "h"}
          onChange={(v) => update(["founderHoursPerWeek"], v)} />
        <Slider label="Ore di lavoro per ogni nuovo cliente" value={params.hoursPerClient}
          min={1} max={8} step={0.25} fmt={(v) => v + "h"}
          onChange={(v) => update(["hoursPerClient"], v)} />
        <Slider label="Mese di ingresso del 2° consulente" value={params.secondConsultantStartMonth}
          min={7} max={24} step={1} fmt={monthLabel}
          onChange={(v) => update(["secondConsultantStartMonth"], v)} />
        <Slider label="Ore a settimana del 2° consulente" value={params.secondConsultantHoursPerWeek}
          min={5} max={50} step={1} fmt={(v) => v + "h"}
          onChange={(v) => update(["secondConsultantHoursPerWeek"], v)} />
      </Panel>

      {/* 11. Costi di costituzione */}
      <Panel id="constitution" title="Costi di costituzione" openState={open} onToggle={toggle}>
        <Slider label="Notaio" value={params.constitution.notaio}
          min={1000} max={5000} step={100} fmt={eur}
          onChange={(v) => update(["constitution", "notaio"], v)} />
        <Slider label="Camera di Commercio (CCIAA)" value={params.constitution.cciaa}
          min={100} max={500} step={50} fmt={eur}
          onChange={(v) => update(["constitution", "cciaa"], v)} />
        <Slider label="Imposta di registro" value={params.constitution.impostoRegistro}
          min={100} max={400} step={50} fmt={eur}
          onChange={(v) => update(["constitution", "impostoRegistro"], v)} />
        <Slider label="Bollo" value={params.constitution.bollo}
          min={100} max={300} step={10} fmt={eur}
          onChange={(v) => update(["constitution", "bollo"], v)} />
        <Slider label="Iscrizione OCF" value={params.constitution.iscrizioneOCF}
          min={300} max={1500} step={100} fmt={eur}
          onChange={(v) => update(["constitution", "iscrizioneOCF"], v)} />
        <Slider label="Commercialista (iniziale)" value={params.constitution.commercialistaIniziale}
          min={500} max={3000} step={100} fmt={eur}
          onChange={(v) => update(["constitution", "commercialistaIniziale"], v)} />
        <Slider label="Avvocato" value={params.constitution.avvocato}
          min={1000} max={5000} step={100} fmt={eur}
          onChange={(v) => update(["constitution", "avvocato"], v)} />
        <Slider label="Assicurazione RC professionale" value={params.constitution.assicurazioneRC}
          min={1500} max={6000} step={100} fmt={eur}
          onChange={(v) => update(["constitution", "assicurazioneRC"], v)} />
        <Slider label="Sito web" value={params.constitution.sitoWeb}
          min={1000} max={10000} step={500} fmt={eur}
          onChange={(v) => update(["constitution", "sitoWeb"], v)} />
        <Slider label="Branding" value={params.constitution.branding}
          min={1000} max={8000} step={500} fmt={eur}
          onChange={(v) => update(["constitution", "branding"], v)} />
        <Slider label="Setup CRM" value={params.constitution.setupCRM}
          min={200} max={2000} step={100} fmt={eur}
          onChange={(v) => update(["constitution", "setupCRM"], v)} />
        <Slider label="Esami e certificazioni" value={params.constitution.esamiCertificazioni}
          min={500} max={3000} step={100} fmt={eur}
          onChange={(v) => update(["constitution", "esamiCertificazioni"], v)} />
        <Slider label="PEC e firma digitale" value={params.constitution.pecFirmaDigitale}
          min={30} max={200} step={5} fmt={eur}
          onChange={(v) => update(["constitution", "pecFirmaDigitale"], v)} />
      </Panel>

      {/* 12. Costi operativi mensili */}
      <Panel id="operating" title="Costi operativi mensili" openState={open} onToggle={toggle}>
        <Slider label="Commercialista" value={params.operating.commercialista}
          min={200} max={800} step={50} fmt={eur}
          onChange={(v) => update(["operating", "commercialista"], v)} />
        <Slider label="Coworking" value={params.operating.coworking}
          min={0} max={1500} step={50} fmt={eur}
          onChange={(v) => update(["operating", "coworking"], v)} />
        <Slider label="Software" value={params.operating.software}
          min={50} max={600} step={50} fmt={eur}
          onChange={(v) => update(["operating", "software"], v)} />
        <Slider label="Assicurazione mensile" value={params.operating.assicurazioneMensile}
          min={100} max={500} step={25} fmt={eur}
          onChange={(v) => update(["operating", "assicurazioneMensile"], v)} />
        <Slider label="PEC, telefono e cloud" value={params.operating.pecTelCloud}
          min={50} max={300} step={25} fmt={eur}
          onChange={(v) => update(["operating", "pecTelCloud"], v)} />
        <Slider label="Quota annuale OCF" value={params.operating.quotaOCF}
          min={30} max={200} step={10} fmt={eur}
          onChange={(v) => update(["operating", "quotaOCF"], v)} />
      </Panel>

      {/* 13. Personale */}
      <Panel id="personnel" title="Personale" openState={open} onToggle={toggle}>
        <Slider label="Compenso per fondatore (€/mese)" value={params.founderComp}
          min={0} max={3000} step={100} fmt={eur}
          onChange={(v) => update(["founderComp"], v)} />
        <Slider label="Numero fondatori" value={params.numFounders}
          min={1} max={4} step={1}
          onChange={(v) => update(["numFounders"], v)} />
        <Slider label="Mese ingresso 2° consulente" value={params.secondConsultantMonth}
          min={13} max={36} step={1} fmt={monthLabel}
          onChange={(v) => update(["secondConsultantMonth"], v)} />
        <Slider label="Costo 2° consulente (€/mese)" value={params.secondConsultantCost}
          min={500} max={4000} step={100} fmt={eur}
          onChange={(v) => update(["secondConsultantCost"], v)} />
        <Slider label="Mese ingresso back-office" value={params.backOfficeMonth}
          min={13} max={36} step={1} fmt={monthLabel}
          onChange={(v) => update(["backOfficeMonth"], v)} />
        <Slider label="Costo back-office (€/mese)" value={params.backOfficeCost}
          min={300} max={2000} step={100} fmt={eur}
          onChange={(v) => update(["backOfficeCost"], v)} />
        <Slider label="Mese ingresso freelancer" value={params.freelancerMonth}
          min={13} max={36} step={1} fmt={monthLabel}
          onChange={(v) => update(["freelancerMonth"], v)} />
        <Slider label="Costo freelancer (€/mese)" value={params.freelancerCost}
          min={200} max={1500} step={100} fmt={eur}
          onChange={(v) => update(["freelancerCost"], v)} />
      </Panel>

      {/* 14. Parcelle e abbandoni */}
      <Panel id="business" title="Parcelle e abbandoni" openState={open} onToggle={toggle}>
        <Slider label="Parcella media per cliente (€/anno)" value={params.arpu}
          min={300} max={900} step={10} fmt={eur}
          onChange={(v) => update(["arpu"], v)} />
        <Slider label="% clienti che disdicono ogni mese" value={params.churnMonthly}
          min={0} max={0.05} step={0.002} fmt={pct}
          onChange={(v) => update(["churnMonthly"], v)} />
      </Panel>

      {/* 15. Capitale iniziale */}
      <Panel id="capital" title="Capitale iniziale" openState={open} onToggle={toggle}>
        <Slider label="Capitale iniziale" value={params.startingCapital}
          min={50000} max={300000} step={10000} fmt={eur}
          onChange={(v) => update(["startingCapital"], v)} />
      </Panel>
    </div>
  );
};
