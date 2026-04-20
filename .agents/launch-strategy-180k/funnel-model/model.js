/* ============================================================
   Proxima Funnel Model — Bottom-Up 36 mesi (M-12 → M+24)
   v3: assunzioni dinamiche, budget intelligente, CAC per canale
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
    founderHoursPerWeek: 25, hoursOnboarding: 5,
    clientRisk: {
      lowPct: 0.75, mediumPct: 0.20,
      lowHoursPerMonth: 0.33,
      mediumHoursPerMonth: 4.33,
      highHoursPerMonth: 21.7
    },
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
      founderComp: 1000, numFounders: 2, inpsRate: 0.26
    },
    hiring: {
      consultantClientsEach: 35,
      consultantHoursPerWeek: 20,
      consultantCost: 2500,
      maxConsultants: 4,
      firstConsultantMonth: 19,
      backOfficeTrigger: 80,
      backOfficeCost: 900,
      backOfficeMinMonth: 21,
      contentTrigger: 40,
      contentCost: 800,
      contentMinMonth: 20,
      juniorTrigger: 150,
      juniorCost: 1200,
      juniorHoursPerWeek: 25,
      juniorMinMonth: 25
    },
    budgetCapAdjust: true,
    budgetCapThreshold: 0.85,
    riskScenario: 'base',
    startingCapital: 180000
  };
};

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

function weightedHoursPerClient(cr) {
  var highPct = Math.max(0, 1 - cr.lowPct - cr.mediumPct);
  return cr.lowPct * cr.lowHoursPerMonth + cr.mediumPct * cr.mediumHoursPerMonth + highPct * cr.highHoursPerMonth;
}

var RISK = {
  base:       { clientMult: 1.0, costMult: 1.0, churnMult: 1.0 },
  recessione: { clientMult: 0.7, costMult: 1.15, churnMult: 1.5 },
  crisi:      { clientMult: 0.5, costMult: 1.15, churnMult: 2.0 }
};

var AGENTS_BY_PHASE = { 1: 10, 2: 16, 3: 25, 4: 32, 5: 35, 6: 35, 7: 35 };

window.PROXIMA.simulate = function (p, months) {
  months = months || 36;
  var results = [], totalClients = 0, revCum = 0, costCum = 0;
  var risk = RISK[p.riskScenario] || RISK.base;
  var opBase = 0;
  var keys = Object.keys(p.operating);
  for (var k = 0; k < keys.length; k++) opBase += p.operating[keys[k]];
  var cash = p.startingCapital;
  var cashMin = cash, cashMinMonth = 1;
  var h = p.hiring;
  var hiredConsultants = 0, hasBackOffice = false, hasContent = false, hasJunior = false;
  var hiringPlan = [];
  var lastConsultantHireMonth = 0;

  var gCumSpend = 0, gCumClients = 0;
  var mCumSpend = 0, mCumClients = 0;
  var lCumSpend = 0, lCumClients = 0;

  for (var m = 1; m <= months; m++) {
    var phase = window.PROXIMA.getPhase(m);
    var phaseName = window.PROXIMA.phaseNames[phase];
    var label = window.PROXIMA.monthLabel(m);
    var isPreRelease = m <= 12;

    // --- Appointment capacity: no client cap, only new-client bottleneck ---
    var fHours = p.founderHoursPerWeek * 4.33;
    var consultantHours = hiredConsultants * h.consultantHoursPerWeek * 4.33;
    var juniorHours = hasJunior ? h.juniorHoursPerWeek * 4.33 : 0;
    var totHours = fHours + consultantHours + juniorHours;
    var maxNewByHours = p.hoursOnboarding > 0 ? totHours / p.hoursOnboarding : 999;

    // --- Dynamic hiring: trigger when appointment slots are >85% full ---
    if (!hasBackOffice && m >= h.backOfficeMinMonth && totalClients >= h.backOfficeTrigger) {
      hasBackOffice = true;
      hiringPlan.push({ month: m, monthLabel: label, role: 'Back-office',
        cost: h.backOfficeCost, trigger: h.backOfficeTrigger + ' clienti' });
    }
    if (!hasContent && m >= h.contentMinMonth && totalClients >= h.contentTrigger) {
      hasContent = true;
      hiringPlan.push({ month: m, monthLabel: label, role: 'Content creator',
        cost: h.contentCost, trigger: h.contentTrigger + ' clienti' });
    }
    if (!hasJunior && m >= h.juniorMinMonth && totalClients >= h.juniorTrigger) {
      hasJunior = true;
      hiringPlan.push({ month: m, monthLabel: label, role: 'Consulente junior',
        cost: h.juniorCost, trigger: h.juniorTrigger + ' clienti' });
    }

    // --- Demand calculation (full budget first, then adjust) ---
    var bGFull = p.google.budgetByPhase[phase] || 0;
    var bMFull = p.meta.budgetByPhase[phase] || 0;
    var bLFull = (m >= p.linkedin.startMonth) ? (p.linkedin.budgetByPhase[phase] || 0) : 0;

    var gClicksFull = bGFull > 0 ? bGFull / p.google.cpc : 0;
    var gBookFull = gClicksFull * p.google.clickToCalc * p.google.calcToBooking;
    var mClicksFull = bMFull > 0 ? bMFull / p.meta.cpc : 0;
    var mBookFull = mClicksFull * p.meta.clickToCalc * p.meta.calcToBooking;
    var lClicksFull = bLFull > 0 ? bLFull / p.linkedin.cpc : 0;
    var lBookFull = lClicksFull * p.linkedin.clickToCalc * p.linkedin.calcToBooking;

    var seoV = p.seo.baseVisits * Math.pow(1 + p.seo.growthRate, m - 1);
    var seoBook = seoV * p.seo.visitToCalc * p.seo.calcToBooking;
    var socV = p.social.baseVisits * Math.pow(1 + p.social.growthRate, m - 1);
    var socBook = socV * p.social.visitToCalc * p.social.calcToBooking;

    var refBook = (m >= p.referral.startMonth) ? totalClients * p.referral.ratePerClient * p.referral.bookingRate : 0;
    var borBook = p.borrowed.bookingsByPhase[phase] || 0;

    if (isPreRelease) {
      gBookFull = 0; mBookFull = 0; lBookFull = 0; seoBook = 0; socBook = 0; refBook = 0;
      bGFull = 0; bMFull = 0; bLFull = 0;
      if (phase !== 4) borBook = 0;
    }

    var totBookFull = gBookFull + mBookFull + lBookFull + seoBook + socBook + refBook + borBook;
    var checkupsFull = totBookFull * p.showRate;
    var newRawFull = checkupsFull * p.checkupToClient * risk.clientMult;

    // --- Appointment utilization: demand vs slots ---
    var appointmentUtil = maxNewByHours > 0 ? newRawFull / maxNewByHours : 0;

    // --- Hire consultant when appointment demand exceeds 85% of slots ---
    if (m >= h.firstConsultantMonth && hiredConsultants < h.maxConsultants
        && appointmentUtil > 0.85 && (m - lastConsultantHireMonth) >= 3) {
      hiredConsultants++;
      lastConsultantHireMonth = m;
      // Recalculate capacity after hire
      consultantHours = hiredConsultants * h.consultantHoursPerWeek * 4.33;
      totHours = fHours + consultantHours + juniorHours;
      maxNewByHours = p.hoursOnboarding > 0 ? totHours / p.hoursOnboarding : 999;
      appointmentUtil = maxNewByHours > 0 ? newRawFull / maxNewByHours : 0;
      hiringPlan.push({ month: m, monthLabel: label,
        role: 'Consulente #' + (hiredConsultants + 1),
        cost: h.consultantCost,
        trigger: 'appuntamenti al ' + Math.round(appointmentUtil * 100) + '% dopo assunzione' });
    }

    // --- Smart budget: reduce ads only when appointment slots are full ---
    var budgetFactor = 1.0;
    if (p.budgetCapAdjust && m >= 13 && appointmentUtil > p.budgetCapThreshold) {
      budgetFactor = Math.max(0.05, 1 - (appointmentUtil - p.budgetCapThreshold) / (1 - p.budgetCapThreshold));
    }

    // --- Apply budget factor ---
    var bG = bGFull * budgetFactor;
    var bM = bMFull * budgetFactor;
    var bL = bLFull * budgetFactor;
    var gClicks = bG > 0 ? bG / p.google.cpc : 0;
    var gBook = gClicks * p.google.clickToCalc * p.google.calcToBooking;
    var mClicks = bM > 0 ? bM / p.meta.cpc : 0;
    var mBook = mClicks * p.meta.clickToCalc * p.meta.calcToBooking;
    var lClicks = bL > 0 ? bL / p.linkedin.cpc : 0;
    var lBook = lClicks * p.linkedin.clickToCalc * p.linkedin.calcToBooking;
    if (isPreRelease) { gBook = 0; mBook = 0; lBook = 0; bG = 0; bM = 0; bL = 0; }

    var totBook = gBook + mBook + lBook + seoBook + socBook + refBook + borBook;
    var checkups = totBook * p.showRate;
    var newRaw = checkups * p.checkupToClient * risk.clientMult;

    var newCapped = (m >= 13) ? Math.min(newRaw, maxNewByHours) : newRaw;
    var capLimited = newRaw > newCapped + 0.5;

    var churn = totalClients * p.churnMonthly * risk.churnMult;
    totalClients = Math.max(0, totalClients + newCapped - churn);

    // --- Per-channel client attribution ---
    var paidConvRate = p.showRate * p.checkupToClient * risk.clientMult;
    var gClients = gBook * paidConvRate;
    var mClients = mBook * paidConvRate;
    var lClients = lBook * paidConvRate;
    gCumSpend += bG; gCumClients += gClients;
    mCumSpend += bM; mCumClients += mClients;
    lCumSpend += bL; lCumClients += lClients;

    // --- Costs ---
    var constCost = constitutionForMonth(m, p.constitution);
    var opCost = opBase * risk.costMult;

    var persCost = p.personnel.founderComp * p.personnel.numFounders * (1 + p.personnel.inpsRate / 3);
    persCost += hiredConsultants * h.consultantCost;
    if (hasBackOffice) persCost += h.backOfficeCost;
    if (hasContent) persCost += h.contentCost;
    if (hasJunior) persCost += h.juniorCost;

    var mktCost = (bG + bM + bL) * risk.costMult;
    var totCost = constCost + opCost + persCost + mktCost;

    var mrr = totalClients * p.arpu / 12;
    var arr = totalClients * p.arpu;
    revCum += mrr;
    costCum += totCost;

    var netBurn = totCost - mrr;
    cash -= netBurn;
    if (cash < cashMin) { cashMin = cash; cashMinMonth = m; }

    var staffCount = p.personnel.numFounders + hiredConsultants + (hasBackOffice?1:0) + (hasContent?1:0) + (hasJunior?1:0);

    results.push({
      month: m, monthLabel: label, phase: phase, phaseName: phaseName, isPreRelease: isPreRelease,
      googleClicks: gClicks, googleBookings: gBook, googleBudget: bG,
      metaClicks: mClicks, metaBookings: mBook, metaBudget: bM,
      linkedinClicks: lClicks, linkedinBookings: lBook, linkedinBudget: bL,
      seoVisits: seoV, seoBookings: seoBook, socialVisits: socV, socialBookings: socBook,
      referralBookings: refBook, borrowedBookings: borBook,
      totalBookings: totBook, checkups: checkups,
      newClientsRaw: newRaw, maxNewPerMonth: maxNewByHours, newClientsCapped: newCapped,
      churnedClients: churn, totalClients: totalClients,
      constitutionCosts: constCost, operatingCosts: opCost,
      personnelCosts: persCost, marketingCosts: mktCost, totalCosts: totCost,
      mrr: mrr, arr: arr,
      netBurn: netBurn, cashRemaining: cash,
      revenueCumulative: revCum, costsCumulative: costCum,
      founderHours: fHours, totalHours: totHours,
      hoursForOnboarding: newCapped * p.hoursOnboarding,
      maxNewThisMonth: maxNewByHours,
      capacityLimited: capLimited,
      appointmentUtilization: appointmentUtil, budgetFactor: budgetFactor,
      hiredConsultants: hiredConsultants, hasBackOffice: hasBackOffice,
      hasContent: hasContent, hasJunior: hasJunior, staffCount: staffCount,
      activeAgents: AGENTS_BY_PHASE[phase] || 35
    });
  }

  var beOp = null, beCum = null;
  for (var i = 0; i < results.length; i++) {
    if (beOp === null && results[i].mrr >= results[i].totalCosts) beOp = results[i].month;
    if (beCum === null && results[i].revenueCumulative >= results[i].costsCumulative) beCum = results[i].month;
  }

  return {
    results: results,
    breakEvenOperational: beOp,
    breakEvenCumulative: beCum,
    cacBlended: (gCumClients+mCumClients+lCumClients) > 0
      ? (gCumSpend+mCumSpend+lCumSpend) / (gCumClients+mCumClients+lCumClients) : 0,
    cacByChannel: {
      google: gCumClients > 0 ? gCumSpend / gCumClients : 0,
      meta: mCumClients > 0 ? mCumSpend / mCumClients : 0,
      linkedin: lCumClients > 0 ? lCumSpend / lCumClients : 0
    },
    cashMinimum: cashMin,
    cashMinimumMonth: cashMinMonth,
    hiringPlan: hiringPlan
  };
};
