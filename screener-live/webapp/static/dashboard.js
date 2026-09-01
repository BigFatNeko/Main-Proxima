const PKG={difensivo:["Difensivo","pkg"],compounders:["Compounders","pkg"],
 cedola_mensile_candidato:["Cedola mensile","pkg"],etico_candidato:["Etico","pkgw"],
 innovativo:["Innovativo","pkg"],emergenti:["Emergenti","pkg"],pir_candidato:["PIR","pkg"]};

function band(m){return m>=650?"q":m>=500?"mid":"low"}
function barcol(m){return m>=650?"var(--good)":m>=500?"var(--slate)":"var(--warn)"}

function rowHTML(d){
  const gated=d.gates&&d.gates.length;
  const cls=gated?"gate":band(d.mvf);
  const pkgs=(d.tags||[]).map(t=>PKG[t]?`<span class="chip ${PKG[t][1]}">${PKG[t][0]}</span>`:"").join("")
    + (d.badges||[]).map(b=>b==="OCCASIONE D'ORO"?`<span class="chip gold">🥇 Occasione d'oro</span>`
        :`<span class="chip">${b}</span>`).join("");
  const netHTML=d.net!=null?`<div class="net">netto IT <b>${d.net.toFixed(1)}%</b></div>`
    :(d.cl==="reit"?`<div class="net" style="color:var(--warn)">ritenuta REIT</div>`
      :`<div class="net" style="color:var(--muted)">no dividendo</div>`);
  const flagline=gated?`<span class="gatetag">Non investibile · ${d.gates.join("+")}</span>`
    :`<div class="flagline">`+
      (d.crit?`<span class="dot c">● ${d.crit} crit.</span>`:"")+
      (d.warn?`<span class="dot w">● ${d.warn} att.</span>`:"")+
      (!d.crit&&!d.warn?`<span style="color:var(--good)">● pulito</span>`:"")+`</div>`;
  const covWarn=d.cov<.75;
  const mvf=d.mvf==null?"n/d":d.mvf;
  return `<a class="row ${cls}" href="/ticker/${encodeURIComponent(d.t)}" data-sec="${(d.sec||'Altro').replace(/"/g,'')}">
    <div class="id"><div class="tk mono">${d.t}</div><div class="nm">${d.name||''}</div>
      <div class="chips"><span class="chip cls">${d.cl}</span>${pkgs}</div></div>
    <div class="metrics">
      <div class="mvf"><div class="top"><span class="lab">Voto MVF-S</span>
        <span class="num mono">${mvf}<small>/1000</small></span></div>
        <div class="bar"><span style="width:${(d.mvf||0)/10}%;background:${barcol(d.mvf||0)}"></span></div>
        <div class="cov ${covWarn?'warn':''}">copertura ${Math.round((d.cov||0)*100)}%${covWarn?' · insuff.':''}</div></div>
      <div class="mini"><div class="lab">IQI-S</div><div class="num mono">${d.iqi??'n/d'}<small>/100</small></div>
        <div class="csread">${d.tier}</div></div>
      <div class="mini"><div class="lab">CS-S</div><div class="num mono">${d.cs}<small>/100</small></div>
        <div class="pvu" title="[P] ${d.comp[0]}% · [V] ${d.comp[1]}% · [U] ${d.comp[2]}%">
          <i class="p" style="width:${d.comp[0]}%"></i><i class="v" style="width:${d.comp[1]}%"></i><i class="u" style="width:${d.comp[2]}%"></i></div>
        <div class="csread">${d.csr}</div></div>
    </div>
    <div class="status">${flagline}${netHTML}
      <div class="delta">Δ MVF↔IQI <b>${d.delta>0?"+":""}${d.delta??'–'}</b></div></div>
  </a>`;
}

fetch("/api/results").then(r=>r.json()).then(({results})=>{
  const ok=results.filter(d=>!(d.gates&&d.gates.length));
  const gated=results.filter(d=>d.gates&&d.gates.length);
  document.getElementById("rows-ok").innerHTML=ok.map(rowHTML).join("")||'<div class="loading">Nessun risultato.</div>';
  if(gated.length){document.getElementById("gate-h").style.display="";
    document.getElementById("rows-gate").innerHTML=gated.map(rowHTML).join("");}

  const nQual=ok.filter(d=>d.mvf>=650&&!d.crit).length;
  document.getElementById("summary").innerHTML=`
    <div class="stat"><div class="n mono">${results.length}</div><div class="l">titoli analizzati</div></div>
    <div class="stat good"><div class="n mono">${nQual}</div><div class="l">qualità piena (MVF ≥ 650, 0 critici)</div></div>
    <div class="stat"><div class="n mono">${ok.length}</div><div class="l">investibili (nessun gate)</div></div>
    <div class="stat crit"><div class="n mono">${gated.length}</div><div class="l">esclusi da gate</div></div>`;

  const secs={};ok.forEach(d=>{const s=d.sec||'Altro';secs[s]=(secs[s]||0)+1});
  const order=Object.keys(secs).sort((a,b)=>secs[b]-secs[a]);
  let active="Tutti";
  const fb=document.getElementById("filterbar");
  const chip=(l,n,on)=>`<button class="fchip" aria-pressed="${on}" data-f="${l}">${l}<span class="c">${n}</span></button>`;
  fb.innerHTML=chip("Tutti",ok.length,true)+order.map(s=>chip(s,secs[s],false)).join("");
  fb.addEventListener("click",e=>{const b=e.target.closest(".fchip");if(!b)return;
    active=b.dataset.f;
    fb.querySelectorAll(".fchip").forEach(c=>c.setAttribute("aria-pressed",c.dataset.f===active));
    document.querySelectorAll("#rows-ok .row").forEach(r=>{
      r.style.display=(active==="Tutti"||r.dataset.sec===active)?"":"none";});
  });
}).catch(()=>{document.getElementById("rows-ok").innerHTML='<div class="loading">Errore nel caricamento.</div>';});
