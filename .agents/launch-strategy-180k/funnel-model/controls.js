/* Controls — Slider panels for all funnel parameters (v3) */
window.PROXIMA = window.PROXIMA || {};

const pct = (v) => (v * 100).toFixed(1) + "%";
const eur = (v) => "€" + Math.round(v).toLocaleString("it-IT");
const num = (v) => Number(v).toFixed(2);
const monthLabel = (v) => { const d = v - 13; return d < 0 ? "M" + d : d === 0 ? "M0" : "M+" + d; };

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

function Panel({ id, title, openState, onToggle, children }) {
  const isOpen = !!openState[id];
  return (
    <div className="panel">
      <div className="panel-header" onClick={() => onToggle(id)}>
        <h3>{title}</h3><span className="chev">{isOpen ? "▼" : "▶"}</span>
      </div>
      {isOpen && <div className="panel-body">{children}</div>}
    </div>
  );
}

const PL = ["Fondazione","Qualificazioni","Pre-lancio","Alpha","Beta","Early Access","Lancio"];

function PhaseBudgets({ channel, label, params, updateArray }) {
  return (
    <>
      <div className="uppercase text-faint" style={{ marginTop: 6, marginBottom: 6 }}>
        Budget pubblicitario {label} per fase (€/mese)
      </div>
      {PL.map((ph, i) => (
        <Slider key={i} label={`Fase ${i+1} (${ph})`} value={params[channel].budgetByPhase[i+1]}
          min={0} max={6000} step={100} fmt={eur}
          onChange={(v) => updateArray([channel, "budgetByPhase"], i+1, v)} />
      ))}
    </>
  );
}

window.PROXIMA.Controls = function Controls({ params, setParams, onReset }) {
  const [open, setOpen] = React.useState({
    scenario:true, funnel:true, google:true, meta:true, linkedin:false,
    seo:true, social:false, referral:true, borrowed:false, capacity:true,
    hiring:true, budgetCap:true,
    constitution:false, operating:false, personnel:true, business:true,
    waitingList:true, aum:false, mortgage:false, taxation:false, capital:true
  });
  const toggle = React.useCallback((k) => setOpen((p) => ({ ...p, [k]: !p[k] })), []);

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
  const S = (path, label, min, max, step, fmt) => (
    <Slider label={label} value={path.reduce((o,k)=>o[k], params)}
      min={min} max={max} step={step} fmt={fmt} onChange={(v) => update(path, v)} />
  );
  const eurCpc = (v) => "€" + num(v);

  return (
    <div>
      <div className="brand"><h1>Proxima</h1><span className="brand-tag">Modello Funnel</span></div>
      <div className="subtitle">Calcolato dai numeri veri · 36 mesi · aggiornamento in tempo reale</div>
      <div className="toolbar"><button className="btn-ghost btn" onClick={onReset}>↻ Reset</button></div>

      <Panel id="scenario" title="Scenario di rischio" openState={open} onToggle={toggle}>
        <div className="scenario-group">
          {["base","recessione","crisi"].map((s) => (
            <button key={s}
              className={"scenario-btn scenario-"+s+(params.riskScenario===s?" active":"")}
              onClick={() => update(["riskScenario"],s)}>{s}</button>
          ))}
        </div>
      </Panel>

      <Panel id="funnel" title="Dopo la prenotazione" openState={open} onToggle={toggle}>
        {S(["showRate"],"% che si presenta all'appuntamento",0.3,1,0.01,pct)}
        {S(["checkupToClient"],"% check-up → cliente pagante",0.1,0.7,0.01,pct)}
      </Panel>

      <Panel id="google" title="Google Ads" openState={open} onToggle={toggle}>
        {S(["google","cpc"],"Costo per click",0.5,5,0.05,eurCpc)}
        {S(["google","clickToCalc"],"% click → calcolatore",0.1,0.9,0.01,pct)}
        {S(["google","calcToBooking"],"% calcolatore → prenotazione",0.01,0.25,0.005,pct)}
        <PhaseBudgets channel="google" label="Google" params={params} updateArray={updateArray} />
      </Panel>

      <Panel id="meta" title="Meta Ads" openState={open} onToggle={toggle}>
        {S(["meta","cpc"],"Costo per click",0.2,3,0.05,eurCpc)}
        {S(["meta","clickToCalc"],"% click → calcolatore",0.05,0.7,0.01,pct)}
        {S(["meta","calcToBooking"],"% calcolatore → prenotazione",0.01,0.2,0.005,pct)}
        <PhaseBudgets channel="meta" label="Meta" params={params} updateArray={updateArray} />
      </Panel>

      <Panel id="linkedin" title="LinkedIn Ads" openState={open} onToggle={toggle}>
        {S(["linkedin","cpc"],"Costo per click",2,12,0.1,eurCpc)}
        {S(["linkedin","clickToCalc"],"% click → calcolatore",0.1,0.9,0.01,pct)}
        {S(["linkedin","calcToBooking"],"% calcolatore → prenotazione",0.01,0.2,0.005,pct)}
        {S(["linkedin","startMonth"],"Mese di inizio",10,30,1,monthLabel)}
        <PhaseBudgets channel="linkedin" label="LinkedIn" params={params} updateArray={updateArray} />
      </Panel>

      <Panel id="seo" title="SEO — traffico gratuito da Google" openState={open} onToggle={toggle}>
        {S(["seo","baseVisits"],"Visite al sito nel primo mese",0,300,5,(v)=>v+"/mese")}
        {S(["seo","growthRate"],"Crescita mensile",0,0.5,0.01,pct)}
        {S(["seo","visitToCalc"],"% visitatori → calcolatore",0.02,0.5,0.01,pct)}
        {S(["seo","calcToBooking"],"% calcolatore → prenotazione",0.01,0.2,0.005,pct)}
      </Panel>

      <Panel id="social" title="Social organici" openState={open} onToggle={toggle}>
        {S(["social","baseVisits"],"Visite al sito nel primo mese",0,300,5,(v)=>v+"/mese")}
        {S(["social","growthRate"],"Crescita mensile",0,0.4,0.01,pct)}
        {S(["social","visitToCalc"],"% visitatori → calcolatore",0.02,0.4,0.01,pct)}
        {S(["social","calcToBooking"],"% calcolatore → prenotazione",0.01,0.15,0.005,pct)}
      </Panel>

      <Panel id="referral" title="Passaparola" openState={open} onToggle={toggle}>
        {S(["referral","ratePerClient"],"% clienti attivi che porta 1 contatto/mese",0,0.2,0.005,pct)}
        {S(["referral","bookingRate"],"% contatti che prenota",0.3,1,0.02,pct)}
        {S(["referral","startMonth"],"Mese di inizio",10,24,1,monthLabel)}
      </Panel>

      <Panel id="borrowed" title="PR, podcast ed eventi" openState={open} onToggle={toggle}>
        <div className="uppercase text-faint" style={{marginBottom:6}}>Prenotazioni/mese per fase</div>
        {PL.map((ph,i) => (
          <Slider key={i} label={`Fase ${i+1} (${ph})`} value={params.borrowed.bookingsByPhase[i+1]}
            min={0} max={40} step={1} fmt={(v)=>v+"/mese"}
            onChange={(v)=>updateArray(["borrowed","bookingsByPhase"],i+1,v)} />
        ))}
      </Panel>

      <Panel id="capacity" title="Capacita e ore di lavoro" openState={open} onToggle={toggle}>
        {S(["founderHoursPerWeek"],"Ore a settimana del founder",5,50,1,(v)=>v+"h")}
        {S(["hoursOnboarding"],"Onboarding per nuovo cliente",2,10,0.5,(v)=>v+"h una tantum")}
      </Panel>

      <Panel id="hiring" title="Assunzioni dinamiche" openState={open} onToggle={toggle}>
        <div className="uppercase text-faint" style={{marginBottom:8}}>Consulenti aggiuntivi</div>
        {S(["hiring","consultantHoursPerWeek"],"Ore/settimana per consulente",10,40,5,(v)=>v+"h")}
        {S(["hiring","consultantCost"],"Costo per consulente (€/mese)",500,5000,100,eur)}
        {S(["hiring","maxConsultants"],"Max consulenti aggiuntivi",0,6,1)}
        {S(["hiring","firstConsultantMonth"],"Mese prima assunzione possibile",13,30,1,monthLabel)}

        <div className="uppercase text-faint" style={{marginTop:14,marginBottom:8}}>Back-office</div>
        {S(["hiring","backOfficeTrigger"],"Clienti necessari per assunzione",20,200,10)}
        {S(["hiring","backOfficeCost"],"Costo back-office (€/mese)",300,2000,100,eur)}
        {S(["hiring","backOfficeMinMonth"],"Mese minimo",13,30,1,monthLabel)}

        <div className="uppercase text-faint" style={{marginTop:14,marginBottom:8}}>Content creator</div>
        {S(["hiring","contentTrigger"],"Clienti necessari per assunzione",10,150,10)}
        {S(["hiring","contentCost"],"Costo content creator (€/mese)",200,2000,100,eur)}
        {S(["hiring","contentMinMonth"],"Mese minimo",13,30,1,monthLabel)}

        <div className="uppercase text-faint" style={{marginTop:14,marginBottom:8}}>Consulente junior</div>
        {S(["hiring","juniorTrigger"],"Clienti necessari per assunzione",50,300,10)}
        {S(["hiring","juniorCost"],"Costo junior (€/mese)",500,2500,100,eur)}
        {S(["hiring","juniorHoursPerWeek"],"Ore/settimana junior",10,40,5,(v)=>v+"h")}
        {S(["hiring","juniorMinMonth"],"Mese minimo",15,36,1,monthLabel)}
      </Panel>

      <Panel id="budgetCap" title="Gestione budget automatica" openState={open} onToggle={toggle}>
        <div style={{marginBottom:12}}>
          <label style={{display:"flex",alignItems:"center",gap:8,cursor:"pointer",fontSize:13}}>
            <input type="checkbox" checked={!!params.budgetCapAdjust}
              onChange={() => update(["budgetCapAdjust"], !params.budgetCapAdjust)} />
            Riduci ads quando capacita satura
          </label>
          <div className="text-faint" style={{fontSize:11,marginTop:4}}>
            Scala il budget pubblicitario quando il team non puo gestire nuovi clienti.
          </div>
        </div>
        {params.budgetCapAdjust && S(["budgetCapThreshold"],"Soglia di utilizzo per riduzione",0.5,0.95,0.05,pct)}
      </Panel>

      <Panel id="constitution" title="Costi di costituzione" openState={open} onToggle={toggle}>
        {S(["constitution","notaio"],"Notaio",1000,5000,100,eur)}
        {S(["constitution","cciaa"],"Camera di Commercio (CCIAA)",100,500,50,eur)}
        {S(["constitution","impostoRegistro"],"Imposta di registro",100,400,50,eur)}
        {S(["constitution","bollo"],"Bollo",100,300,10,eur)}
        {S(["constitution","iscrizioneOCF"],"Iscrizione OCF",300,1500,100,eur)}
        {S(["constitution","commercialistaIniziale"],"Commercialista (iniziale)",500,3000,100,eur)}
        {S(["constitution","avvocato"],"Avvocato",1000,5000,100,eur)}
        {S(["constitution","assicurazioneRC"],"Assicurazione RC professionale",1500,6000,100,eur)}
        {S(["constitution","sitoWeb"],"Sito web",1000,10000,500,eur)}
        {S(["constitution","branding"],"Branding",1000,8000,500,eur)}
        {S(["constitution","setupCRM"],"Setup CRM",200,2000,100,eur)}
        {S(["constitution","esamiCertificazioni"],"Esami e certificazioni",500,3000,100,eur)}
        {S(["constitution","pecFirmaDigitale"],"PEC e firma digitale",30,200,5,eur)}
      </Panel>

      <Panel id="operating" title="Costi operativi mensili" openState={open} onToggle={toggle}>
        {S(["operating","commercialista"],"Commercialista",200,800,50,eur)}
        {S(["operating","coworking"],"Coworking",0,1500,50,eur)}
        {S(["operating","software"],"Software",50,600,50,eur)}
        {S(["operating","assicurazioneMensile"],"Assicurazione mensile",100,500,25,eur)}
        {S(["operating","pecTelCloud"],"PEC, telefono e cloud",50,300,25,eur)}
        {S(["operating","quotaOCF"],"Quota annuale OCF",30,200,10,eur)}
      </Panel>

      <Panel id="personnel" title="Compensi fondatori" openState={open} onToggle={toggle}>
        {S(["personnel","founderComp"],"Compenso per fondatore (€/mese)",0,3000,100,eur)}
        {S(["personnel","numFounders"],"Numero fondatori",1,4,1)}
      </Panel>

      <Panel id="business" title="Parcelle e abbandoni" openState={open} onToggle={toggle}>
        {S(["arpu"],"Parcella media per cliente (€/anno)",300,1500,10,eur)}
        {S(["churnMonthly"],"% clienti che disdicono ogni mese",0,0.05,0.002,pct)}
        <div style={{marginTop:12}}>
          <label style={{display:"flex",alignItems:"center",gap:8,cursor:"pointer",fontSize:13}}>
            <input type="checkbox" checked={!!params.deferredFees}
              onChange={() => update(["deferredFees"], !params.deferredFees)} />
            Prima parcella dopo 12 mesi (pagamento differito)
          </label>
          <div className="text-faint" style={{fontSize:11,marginTop:4}}>
            I clienti pagano il primo anno di parcella solo al compimento del 12° mese. Ritarda significativamente il break-even.
          </div>
        </div>
      </Panel>

      <Panel id="waitingList" title="Lista d'attesa e pre-lancio" openState={open} onToggle={toggle}>
        <div className="text-faint" style={{fontSize:11,marginBottom:10}}>
          Persone acquisite durante la fase Alpha che diventano clienti al lancio (M0).
        </div>
        {S(["waitingList","count"],"Persone in lista d'attesa",0,100,1,(v)=>v+" persone")}
        {S(["waitingList","conversionRate"],"% che diventa cliente a M0",0,1,0.05,pct)}
      </Panel>

      <Panel id="aum" title="Patrimonio gestito (AUM) e S&P 500" openState={open} onToggle={toggle}>
        <div className="text-faint" style={{fontSize:11,marginBottom:10}}>
          Usato per proiettare il patrimonio totale gestito e confrontarlo con il rendimento S&P 500.
        </div>
        {S(["aum","avgPerClient"],"Patrimonio medio per cliente (€)",10000,500000,5000,eur)}
        {S(["aum","sp500Annual"],"Rendimento annuo benchmark (S&P 500)",0.05,0.15,0.005,pct)}
      </Panel>

      <Panel id="mortgage" title="Mutuo (finanziamento 180k)" openState={open} onToggle={toggle}>
        <div style={{marginBottom:12}}>
          <label style={{display:"flex",alignItems:"center",gap:8,cursor:"pointer",fontSize:13}}>
            <input type="checkbox" checked={!!params.mortgage.enabled}
              onChange={() => update(["mortgage","enabled"], !params.mortgage.enabled)} />
            Capitale ottenuto tramite mutuo
          </label>
          <div className="text-faint" style={{fontSize:11,marginTop:4}}>
            Durante il pre-ammortamento si pagano solo gli interessi. Rata mensile calcolata automaticamente.
          </div>
        </div>
        {params.mortgage.enabled && <>
          {S(["mortgage","principal"],"Capitale a mutuo",50000,300000,5000,eur)}
          {S(["mortgage","rate"],"Tasso annuo",0.01,0.12,0.001,(v)=>(v*100).toFixed(2)+"%")}
          {S(["mortgage","preAmortMonths"],"Mesi pre-ammortamento",6,36,6,(v)=>v+" mesi")}
          {S(["mortgage","amortMonths"],"Durata piano rimborso (mesi)",12,120,12,(v)=>v+" mesi")}
          <div className="text-faint" style={{fontSize:11,marginTop:8,padding:"8px",background:"rgba(196,169,98,0.08)",borderRadius:4}}>
            Interessi mensili pre-ammortamento: {eur(params.mortgage.principal * params.mortgage.rate / 12)}/mese
            {" · "}ogni 6 mesi: {eur(params.mortgage.principal * params.mortgage.rate / 2)}
          </div>
        </>}
      </Panel>

      <Panel id="taxation" title="Fiscalità (IRES + IRAP)" openState={open} onToggle={toggle}>
        <div style={{marginBottom:12}}>
          <label style={{display:"flex",alignItems:"center",gap:8,cursor:"pointer",fontSize:13}}>
            <input type="checkbox" checked={!!params.taxation.enabled}
              onChange={() => update(["taxation","enabled"], !params.taxation.enabled)} />
            Includi stima tasse nel cash flow
          </label>
          <div className="text-faint" style={{fontSize:11,marginTop:4}}>
            Provisione mensile IRES (24%) su utile stimato + IRAP (3,9%) sul margine operativo. Approssimazione per accrual.
          </div>
        </div>
        {params.taxation.enabled && <>
          {S(["taxation","iresRate"],"Aliquota IRES",0.15,0.30,0.01,pct)}
          {S(["taxation","irapRate"],"Aliquota IRAP",0.02,0.06,0.001,pct)}
        </>}
      </Panel>

      <Panel id="capital" title="Capitale iniziale" openState={open} onToggle={toggle}>
        {S(["startingCapital"],"Capitale iniziale (equity + mutuo)",50000,300000,10000,eur)}
      </Panel>
    </div>
  );
};
