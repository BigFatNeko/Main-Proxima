/* ============================================================
   Proxima Funnel Model — Bottom-Up 36 mesi (M-12 → M+24)
   Indice 1..36 = mese strategico M-12..M+24
   7 fasi: F1(1-3) F2(4-6) F3(7-9) F4(10-12) F5(13-15) F6(16-18) F7(19+)
   ============================================================ */
window.PROXIMA = window.PROXIMA || {};

window.PROXIMA.getPhase = function (m) {
  if (m <= 3) return 1; if (m <= 6) return 2; if (m <= 9) return 3;
  if (m <= 12) return 4; if (m <= 15) return 5; if (m <= 18) return 6; return 7;
};

window.PROXIMA.phaseNames = {
  1: 'Fondazione e burocrazia', 2: 'Qualificazioni e compliance',
  3: 'Pre-lancio (Infrastruttura)', 4: 'Alpha test',
  5: 'Beta pubblica', 6: 'Early Access', 7: 'Lancio Pubblico'
};

window.PROXIMA.monthLabel = function (m) {
  if (m <= 12) return 'M-' + (13 - m);
  if (m === 13) return 'M0';
  return 'M+' + (m - 13);
};

// Obiettivi strategici — interpolazione lineare tra milestone
window.PROXIMA.getTarget = function (m) {
  var pts = [[13, 0], [19, 50], [25, 200], [31, 400], [37, 700]];
  if (m < 13) return 0;
  for (var i = 0; i < pts.length - 1; i++) {
    if (m <= pts[i + 1][0]) {
      var t = (m - pts[i][0]) / (pts[i + 1][0] - pts[i][0]);
      return Math.round(pts[i][1] + t * (pts[i + 1][1] - pts[i][1]));
    }
  }
  return 700;
};

// Parametri di default
window.PROXIMA.defaultParams = function () {
  return {
    showRate: 0.75, checkupToClient: 0.30,
    google: { cpc: 1.80, clickToCalc: 0.60, calcToBooking: 0.08,
      budgetByPhase: { 1:0, 2:0, 3:0, 4:500, 5:1500, 6:2500, 7:3500 } },
    meta: { cpc: 0.90, clickToCalc: 0.35, calcToBooking: 0.05,
      budgetByPhase: { 1:0, 2:0, 3:0, 4:300, 5:800, 6:1200, 7:1800 } },
    linkedin: { cpc: 6.00, clickToCalc: 0.50, calcToBooking: 0.06,
      budgetByPhase: { 1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:600 }, startMonth: 22 },
    seo: { baseVisits: 30, growthRate: 0.22, visitToCalc: 0.18, calcToBooking: 0.06 },
    social: { baseVisits: 60, growthRate: 0.14, visitToCalc: 0.10, calcToBooking: 0.04 },
    referral: { ratePerClient: 0.06, bookingRate: 0.80, startMonth: 15 },
    borrowed: { bookingsByPhase: { 1:0, 2:0, 3:0, 4:2, 5:5, 6:8, 7:12 } },
    founderHoursPerWeek: 25, hoursPerClient: 3,
    secondConsultantStartMonth: 21, secondConsultantHoursPerWeek: 20,
    arpu: 490, churnMonthly: 0.01,
    constitution: {
      notaio: 2500, cciaa: 200, impostoRegistro: 200, bollo: 156,
      iscrizioneOCF: 700, commercialistaIniziale: 1500, avvocato: 2500,
      assicurazioneRC: 3000, sitoWeb: 4000, branding: 3000, setupCRM: 500,
      esamiCertificazioni: 1500, pecFirmaDigitale: 75
    },
    operating: {
      commercialista: 400, coworking: 350, software: 200,
      assicurazioneMensile: 250, pecTelCloud: 100, quotaOCF: 80
    },
    personnel: {
      founderComp: 1000, numFounders: 2, inpsRate: 0.26,
      secondConsultantMonth: 21, secondConsultantCost: 1500,
      backOfficeMonth: 27, backOfficeCost: 800,
      freelancerMonth: 20, freelancerCost: 600
    },
    riskScenario: 'base',
    startingCapital: 180000
  };
};

// Costi di costituzione per mese (distribuzione fissa)
function constitutionForMonth(m, c) {
  if (m === 1) return c.notaio + c.cciaa + c.impostoRegistro + c.bollo + c.commercialistaIniziale;
  if (m === 2) return c.pecFirmaDigitale + c.iscrizioneOCF;
  if (m === 3) return c.esamiCertificazioni;
  if (m === 4) return c.avvocato + c.sitoWeb / 2;
  if (m === 5) return c.assicurazioneRC + c.sitoWeb / 2;
  if (m === 6) return c.branding;
  if (m === 7) return c.setupCRM;
  return 0;
}

// Costi personale per mese
function personnelForMonth(m, per) {
  var cost = per.founderComp * per.numFounders * (1 + per.inpsRate / 3);
  if (m >= per.secondConsultantMonth) cost += per.secondConsultantCost;
  if (m >= per.backOfficeMonth) cost += per.backOfficeCost;
  if (m >= per.freelancerMonth) cost += per.freelancerCost;
  return cost;
}

// Moltiplicatori scenario di rischio
var RISK = {
  base:       { clientMult: 1.0, costMult: 1.0, churnMult: 1.0 },
  recessione: { clientMult: 0.7, costMult: 1.15, churnMult: 1.5 },
  crisi:      { clientMult: 0.5, costMult: 1.15, churnMult: 2.0 }
};

// Agenti attivi per fase
var AGENTS_BY_PHASE = { 1: 10, 2: 16, 3: 25, 4: 32, 5: 35, 6: 35, 7: 35 };

// Simulazione principale
window.PROXIMA.simulate = function (p, months) {
  months = months || 36;
  var results = [], totalClients = 0, revCum = 0, costCum = 0;
  var risk = RISK[p.riskScenario] || RISK.base;
  var opBase = 0;
  var keys = Object.keys(p.operating);
  for (var k = 0; k < keys.length; k++) opBase += p.operating[keys[k]];
  var cash = p.startingCapital;
  var cashMin = cash, cashMinMonth = 1;

  for (var m = 1; m <= months; m++) {
    var phase = window.PROXIMA.getPhase(m);
    var phaseName = window.PROXIMA.phaseNames[phase];
    var label = window.PROXIMA.monthLabel(m);
    var isPreRelease = m <= 12;

    // Budget canali paid
    var bG = p.google.budgetByPhase[phase] || 0;
    var bM = p.meta.budgetByPhase[phase] || 0;
    var bL = (m >= p.linkedin.startMonth) ? (p.linkedin.budgetByPhase[phase] || 0) : 0;

    // Canali: calcolo click e prenotazioni
    var gClicks = bG / p.google.cpc;
    var gBook = gClicks * p.google.clickToCalc * p.google.calcToBooking;
    var mClicks = bM / p.meta.cpc;
    var mBook = mClicks * p.meta.clickToCalc * p.meta.calcToBooking;
    var lClicks = bL / p.linkedin.cpc;
    var lBook = lClicks * p.linkedin.clickToCalc * p.linkedin.calcToBooking;

    var seoV = p.seo.baseVisits * Math.pow(1 + p.seo.growthRate, m - 1);
    var seoBook = seoV * p.seo.visitToCalc * p.seo.calcToBooking;
    var socV = p.social.baseVisits * Math.pow(1 + p.social.growthRate, m - 1);
    var socBook = socV * p.social.visitToCalc * p.social.calcToBooking;

    var refBook = (m >= p.referral.startMonth) ? totalClients * p.referral.ratePerClient * p.referral.bookingRate : 0;
    var borBook = p.borrowed.bookingsByPhase[phase] || 0;

    // Pre-release: zero prenotazioni tranne borrowed in fase 4 (Alpha)
    if (isPreRelease) {
      gBook = 0; mBook = 0; lBook = 0; seoBook = 0; socBook = 0; refBook = 0;
      if (phase !== 4) borBook = 0;
    }

    var totBook = gBook + mBook + lBook + seoBook + socBook + refBook + borBook;
    var checkups = totBook * p.showRate;
    var newRaw = checkups * p.checkupToClient * risk.clientMult;

    // Capacita
    var fHours = p.founderHoursPerWeek * 4.33;
    var sHours = (m >= p.secondConsultantStartMonth) ? p.secondConsultantHoursPerWeek * 4.33 : 0;
    var totHours = fHours + sHours;
    var maxCap = totHours / p.hoursPerClient;
    var newCapped = (m >= 13) ? Math.min(newRaw, Math.max(0, maxCap - totalClients)) : newRaw;
    var capLimited = newRaw > newCapped + 0.5;

    // Churn
    var churn = totalClients * p.churnMonthly * risk.churnMult;
    totalClients = Math.max(0, totalClients + newCapped - churn);

    // Costi
    var constCost = constitutionForMonth(m, p.constitution);
    var opCost = opBase * risk.costMult;
    var persCost = personnelForMonth(m, p.personnel);
    var mktCost = (bG + bM + bL) * risk.costMult;
    var totCost = constCost + opCost + persCost + mktCost;

    // Ricavi
    var mrr = totalClients * p.arpu / 12;
    var arr = totalClients * p.arpu;
    revCum += mrr;
    costCum += totCost;

    // Cash flow
    var netBurn = totCost - mrr;
    cash -= netBurn;
    if (cash < cashMin) { cashMin = cash; cashMinMonth = m; }

    results.push({
      month: m, monthLabel: label, phase: phase, phaseName: phaseName, isPreRelease: isPreRelease,
      googleClicks: gClicks, googleBookings: gBook, metaClicks: mClicks, metaBookings: mBook,
      linkedinClicks: lClicks, linkedinBookings: lBook,
      seoVisits: seoV, seoBookings: seoBook, socialVisits: socV, socialBookings: socBook,
      referralBookings: refBook, borrowedBookings: borBook,
      totalBookings: totBook, checkups: checkups,
      newClientsRaw: newRaw, maxClientsByCapacity: maxCap, newClientsCapped: newCapped,
      churnedClients: churn, totalClients: totalClients,
      constitutionCosts: constCost, operatingCosts: opCost,
      personnelCosts: persCost, marketingCosts: mktCost, totalCosts: totCost,
      mrr: mrr, arr: arr,
      netBurn: netBurn, cashRemaining: cash,
      revenueCumulative: revCum, costsCumulative: costCum,
      founderHours: fHours, totalHours: totHours, hoursNeeded: totalClients * p.hoursPerClient,
      capacityLimited: capLimited,
      activeAgents: AGENTS_BY_PHASE[phase] || 35
    });
  }

  // Break-even operativo: primo mese dove mrr >= costi mensili totali
  var beOp = null, beCum = null;
  for (var i = 0; i < results.length; i++) {
    if (beOp === null && results[i].mrr >= results[i].totalCosts) beOp = results[i].month;
    if (beCum === null && results[i].revenueCumulative >= results[i].costsCumulative) beCum = results[i].month;
  }

  // CAC blended: spesa paid totale / clienti da canali paid
  var totPaid = 0, totPaidClients = 0;
  for (var j = 0; j < results.length; j++) {
    var r = results[j];
    totPaid += r.marketingCosts;
    var paidBook = r.googleBookings + r.metaBookings + r.linkedinBookings;
    totPaidClients += paidBook * p.showRate * p.checkupToClient;
  }

  return {
    results: results,
    breakEvenOperational: beOp,
    breakEvenCumulative: beCum,
    cacBlended: totPaidClients > 0 ? totPaid / totPaidClients : 0,
    cashMinimum: cashMin,
    cashMinimumMonth: cashMinMonth
  };
};
