/* ============================================================
   Proxima Funnel Model SCF — Bottom-Up 36 mesi (M-12 → M+23)
   v1 SCF: offerta a fasce in abbonamento (decisioni 10/06/2026)
   Check-up IA gratuito → App (€1-5) → Monitor (€5-20) → Live (€50-150)
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
  // Obiettivo abbonati paganti (tutte le fasce). Con ARPU da abbonamento
  // (~€170/anno blended) servono molti più clienti che nel piano a parcella €490.
  var pts = [[13, 0], [19, 100], [25, 500], [31, 1200], [37, 2200]];
  if (m < 13) return 0;
  for (var i = 0; i < pts.length - 1; i++) {
    if (m <= pts[i + 1][0]) {
      var t = (m - pts[i][0]) / (pts[i + 1][0] - pts[i][0]);
      return Math.round(pts[i][1] + t * (pts[i + 1][1] - pts[i][1]));
    }
  }
  return 2200;
};

window.PROXIMA.defaultParams = function () {
  return {
    // Conversioni dal Check-up gratuito (⚠ assunzioni da validare sul campo)
    checkupToPaid: 0.06,         // % nuovi utenti Check-up che si abbona nel mese
    freeBaseConvMonthly: 0.003,  // % della base gratuita che si abbona ogni mese

    google: { cpc: 1.80, clickToCalc: 0.60, calcToBooking: 0.18,
      budgetByPhase: { 1:0, 2:0, 3:0, 4:500, 5:1500, 6:2500, 7:3500 } },
    meta: { cpc: 0.90, clickToCalc: 0.35, calcToBooking: 0.12,
      budgetByPhase: { 1:0, 2:0, 3:0, 4:300, 5:800, 6:1200, 7:1800 } },
    linkedin: { cpc: 6.00, clickToCalc: 0.50, calcToBooking: 0.12,
      budgetByPhase: { 1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:600 }, startMonth: 22 },
    seo: { baseVisits: 30, growthRate: 0.22, visitToCalc: 0.18, calcToBooking: 0.15 },
    social: { baseVisits: 60, growthRate: 0.14, visitToCalc: 0.10, calcToBooking: 0.10 },
    referral: { ratePerClient: 0.04, bookingRate: 0.60, startMonth: 15 },
    borrowed: { bookingsByPhase: { 1:0, 2:0, 3:0, 4:6, 5:15, 6:25, 7:40 } },

    // Capacità: vincola solo la fascia Live (call dedicate)
    founderHoursPerWeek: 25, hoursOnboarding: 3, hoursLiveMonthly: 0.75,

    // Offerta a fasce (D1 10/06/2026, prezzi indicativi). mixLive = 1 - mixApp - mixMonitor
    fasce: {
      priceApp: 3, priceMonitor: 12, priceLive: 90,
      mixApp: 0.60, mixMonitor: 0.30,
      churnApp: 0.045, churnMonitor: 0.02, churnLive: 0.012
    },

    // Costi specifici di app e IA
    appCosts: { sviluppoApp: 18000, hostingMensile: 150, aiCostPerCheckup: 0.40 },

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
      consultantHoursPerWeek: 20,
      consultantCost: 2500,
      maxConsultants: 4,
      firstConsultantMonth: 19,
      backOfficeTrigger: 60,     // clienti assistiti (Monitor+Live)
      backOfficeCost: 900,
      backOfficeMinMonth: 21,
      contentTrigger: 30,        // clienti assistiti (Monitor+Live)
      contentCost: 800,
      contentMinMonth: 20,
      juniorTrigger: 120,        // clienti assistiti (Monitor+Live)
      juniorCost: 1200,
      juniorHoursPerWeek: 25,
      juniorMinMonth: 25
    },
    budgetCapAdjust: true,
    budgetCapThreshold: 0.85,
    riskScenario: 'base',
    startingCapital: 180000,
    waitingList: { count: 10, conversionRate: 0.80 },
    aum: { avgPerClient: 40000, sp500Annual: 0.10 },
    mortgage: { enabled: false, principal: 180000, rate: 0.054, preAmortMonths: 18, amortMonths: 60 },
    taxation: { enabled: false, iresRate: 0.24, irapRate: 0.039 }
  };
};

function constitutionForMonth(m, c, app) {
  var base = 0;
  if (m === 1) base = c.notaio + c.cciaa + c.impostoRegistro + c.bollo + c.commercialistaIniziale;
  if (m === 2) base = c.pecFirmaDigitale + c.iscrizioneOCF;
  if (m === 3) base = c.esamiCertificazioni;
  if (m === 4) base = c.avvocato + c.sitoWeb / 2;
  if (m === 5) base = c.assicurazioneRC + c.sitoWeb / 2;
  if (m === 6) base = c.branding;
  if (m === 7) base = c.setupCRM;
  // Sviluppo app distribuito su 6 mesi (M-9 → M-4), pronto per l'Alpha
  if (m >= 4 && m <= 9) base += app.sviluppoApp / 6;
  return base;
}

var RISK = {
  base:       { clientMult: 1.0, costMult: 1.0, churnMult: 1.0 },
  recessione: { clientMult: 0.7, costMult: 1.15, churnMult: 1.5 },
  crisi:      { clientMult: 0.5, costMult: 1.15, churnMult: 2.0 }
};

var AGENTS_BY_PHASE = { 1: 10, 2: 16, 3: 25, 4: 32, 5: 35, 6: 35, 7: 35 };

window.PROXIMA.simulate = function (p, months) {
  months = months || 36;
  var results = [], revCum = 0, costCum = 0;
  var risk = RISK[p.riskScenario] || RISK.base;
  var mixLive = Math.max(0, 1 - p.fasce.mixApp - p.fasce.mixMonitor);
  var opBase = 0;
  var keys = Object.keys(p.operating);
  for (var k = 0; k < keys.length; k++) opBase += p.operating[keys[k]];
  var cash = p.startingCapital;
  var cashMin = cash, cashMinMonth = 1;
  var h = p.hiring;
  var hiredConsultants = 0, hasBackOffice = false, hasContent = false, hasJunior = false;
  var hiringPlan = [];
  var lastConsultantHireMonth = 0;

  // Stato del funnel SCF
  var freeUsers = 0;
  var cApp = 0, cMon = 0, cLive = 0;

  var gCumSpend = 0, gCumClients = 0;
  var mCumSpend = 0, mCumClients = 0;
  var lCumSpend = 0, lCumClients = 0;
  var sp500Monthly = Math.pow(1 + p.aum.sp500Annual, 1 / 12) - 1;
  var sp500BenchmarkValue = 0;
  var monitoredAUM = 0;
  var revWindow12 = [], costWindow12 = [];

  for (var m = 1; m <= months; m++) {
    var phase = window.PROXIMA.getPhase(m);
    var phaseName = window.PROXIMA.phaseNames[phase];
    var label = window.PROXIMA.monthLabel(m);
    var isPreRelease = m <= 12;

    // --- Capacità: le ore vincolano solo la fascia Live ---
    var fHours = p.founderHoursPerWeek * 4.33;
    var consultantHours = hiredConsultants * h.consultantHoursPerWeek * 4.33;
    var juniorHours = hasJunior ? h.juniorHoursPerWeek * 4.33 : 0;
    var totHours = fHours + consultantHours + juniorHours;
    var liveCareHours = cLive * p.hoursLiveMonthly;
    var hoursForOnboarding = Math.max(0, totHours - liveCareHours);
    var maxNewLive = p.hoursOnboarding > 0 ? hoursForOnboarding / p.hoursOnboarding : 999;

    // --- Assunzioni a soglia: sui clienti assistiti (Monitor + Live) ---
    var assistiti = cMon + cLive;
    if (!hasBackOffice && m >= h.backOfficeMinMonth && assistiti >= h.backOfficeTrigger) {
      hasBackOffice = true;
      hiringPlan.push({ month: m, monthLabel: label, role: 'Back-office',
        cost: h.backOfficeCost, trigger: h.backOfficeTrigger + ' clienti assistiti' });
    }
    if (!hasContent && m >= h.contentMinMonth && assistiti >= h.contentTrigger) {
      hasContent = true;
      hiringPlan.push({ month: m, monthLabel: label, role: 'Content creator',
        cost: h.contentCost, trigger: h.contentTrigger + ' clienti assistiti' });
    }
    if (!hasJunior && m >= h.juniorMinMonth && assistiti >= h.juniorTrigger) {
      hasJunior = true;
      hiringPlan.push({ month: m, monthLabel: label, role: 'Consulente junior',
        cost: h.juniorCost, trigger: h.juniorTrigger + ' clienti assistiti' });
    }

    // --- Domanda a budget pieno (per decidere assunzioni e riduzione ads) ---
    var bGFull = p.google.budgetByPhase[phase] || 0;
    var bMFull = p.meta.budgetByPhase[phase] || 0;
    var bLFull = (m >= p.linkedin.startMonth) ? (p.linkedin.budgetByPhase[phase] || 0) : 0;

    var gClicksFull = bGFull > 0 ? bGFull / p.google.cpc : 0;
    var gSignFull = gClicksFull * p.google.clickToCalc * p.google.calcToBooking;
    var mClicksFull = bMFull > 0 ? bMFull / p.meta.cpc : 0;
    var mSignFull = mClicksFull * p.meta.clickToCalc * p.meta.calcToBooking;
    var lClicksFull = bLFull > 0 ? bLFull / p.linkedin.cpc : 0;
    var lSignFull = lClicksFull * p.linkedin.clickToCalc * p.linkedin.calcToBooking;

    var seoV = p.seo.baseVisits * Math.pow(1 + p.seo.growthRate, m - 1);
    var seoSign = seoV * p.seo.visitToCalc * p.seo.calcToBooking;
    var socV = p.social.baseVisits * Math.pow(1 + p.social.growthRate, m - 1);
    var socSign = socV * p.social.visitToCalc * p.social.calcToBooking;

    var totalPayingPrev = cApp + cMon + cLive;
    var refSign = (m >= p.referral.startMonth) ? totalPayingPrev * p.referral.ratePerClient * p.referral.bookingRate : 0;
    var borSign = p.borrowed.bookingsByPhase[phase] || 0;

    if (isPreRelease) {
      gSignFull = 0; mSignFull = 0; lSignFull = 0; seoSign = 0; socSign = 0; refSign = 0;
      bGFull = 0; bMFull = 0; bLFull = 0;
      if (phase !== 4) borSign = 0;
    }

    var totSignFull = gSignFull + mSignFull + lSignFull + seoSign + socSign + refSign + borSign;
    var newPayingFull = (totSignFull * p.checkupToPaid + freeUsers * p.freeBaseConvMonthly) * risk.clientMult;
    var newLiveFull = newPayingFull * mixLive;

    // --- Utilizzo slot Live: domanda vs ore disponibili ---
    var liveUtil = maxNewLive > 0 ? newLiveFull / maxNewLive : 0;

    // --- Assunzione consulente quando gli slot Live superano l'85% ---
    if (m >= h.firstConsultantMonth && hiredConsultants < h.maxConsultants
        && liveUtil > 0.85 && (m - lastConsultantHireMonth) >= 3) {
      hiredConsultants++;
      lastConsultantHireMonth = m;
      consultantHours = hiredConsultants * h.consultantHoursPerWeek * 4.33;
      totHours = fHours + consultantHours + juniorHours;
      hoursForOnboarding = Math.max(0, totHours - liveCareHours);
      maxNewLive = p.hoursOnboarding > 0 ? hoursForOnboarding / p.hoursOnboarding : 999;
      liveUtil = maxNewLive > 0 ? newLiveFull / maxNewLive : 0;
      hiringPlan.push({ month: m, monthLabel: label,
        role: 'Consulente #' + hiredConsultants,
        cost: h.consultantCost,
        trigger: 'slot Live al ' + Math.round(liveUtil * 100) + '% dopo assunzione' });
    }

    // --- Budget intelligente: riduci ads quando gli slot Live saturano ---
    var budgetFactor = 1.0;
    if (p.budgetCapAdjust && m >= 13 && liveUtil > p.budgetCapThreshold) {
      budgetFactor = Math.max(0.05, 1 - (liveUtil - p.budgetCapThreshold) / (1 - p.budgetCapThreshold));
    }

    // --- Applica il fattore budget ---
    var bG = bGFull * budgetFactor;
    var bM = bMFull * budgetFactor;
    var bL = bLFull * budgetFactor;
    var gClicks = bG > 0 ? bG / p.google.cpc : 0;
    var gSign = gClicks * p.google.clickToCalc * p.google.calcToBooking;
    var mClicks = bM > 0 ? bM / p.meta.cpc : 0;
    var mSign = mClicks * p.meta.clickToCalc * p.meta.calcToBooking;
    var lClicks = bL > 0 ? bL / p.linkedin.cpc : 0;
    var lSign = lClicks * p.linkedin.clickToCalc * p.linkedin.calcToBooking;
    if (isPreRelease) { gSign = 0; mSign = 0; lSign = 0; bG = 0; bM = 0; bL = 0; }

    var totSign = gSign + mSign + lSign + seoSign + socSign + refSign + borSign;
    var newFree = totSign;

    // --- Conversioni: dai nuovi Check-up e dalla base gratuita ---
    var convFromNew = newFree * p.checkupToPaid * risk.clientMult;
    var convFromBase = freeUsers * p.freeBaseConvMonthly * risk.clientMult;
    var newPaying = convFromNew + convFromBase;

    var newLiveRaw = newPaying * mixLive;
    var newLive = (m >= 13) ? Math.min(newLiveRaw, maxNewLive) : newLiveRaw;
    var liveOverflow = newLiveRaw - newLive;   // domanda Live non servibile → resta Monitor
    var newApp = newPaying * p.fasce.mixApp;
    var newMon = newPaying * p.fasce.mixMonitor + liveOverflow;
    var capLimited = newLiveRaw > newLive + 0.5;

    // --- Churn per fascia ---
    var churnA = cApp * p.fasce.churnApp * risk.churnMult;
    var churnM = cMon * p.fasce.churnMonitor * risk.churnMult;
    var churnL = cLive * p.fasce.churnLive * risk.churnMult;
    var churn = churnA + churnM + churnL;

    cApp = Math.max(0, cApp + newApp - churnA);
    cMon = Math.max(0, cMon + newMon - churnM);
    cLive = Math.max(0, cLive + newLive - churnL);

    // --- Lista d'attesa a M0 (ripartita sul mix) ---
    var waitingListBoost = 0;
    if (m === 13) {
      waitingListBoost = Math.round(p.waitingList.count * p.waitingList.conversionRate);
      cApp += waitingListBoost * p.fasce.mixApp;
      cMon += waitingListBoost * p.fasce.mixMonitor;
      cLive += waitingListBoost * mixLive;
    }

    // --- Base gratuita: entra chi non converte, esce chi si abbona ---
    freeUsers = Math.max(0, freeUsers - convFromBase + (newFree - convFromNew));

    var totalClients = cApp + cMon + cLive;
    assistiti = cMon + cLive;

    // --- Attribuzione clienti per canale (per il CAC) ---
    var paidConvRate = p.checkupToPaid * risk.clientMult;
    var gClients = gSign * paidConvRate;
    var mClients = mSign * paidConvRate;
    var lClients = lSign * paidConvRate;
    gCumSpend += bG; gCumClients += gClients;
    mCumSpend += bM; mCumClients += mClients;
    lCumSpend += bL; lCumClients += lClients;

    // --- Costi ---
    var constCost = constitutionForMonth(m, p.constitution, p.appCosts);
    var opCost = opBase * risk.costMult;

    // Costi app e IA: hosting da quando l'app è in Alpha (M-3), IA per ogni Check-up generato
    var appCost = 0;
    if (m >= 10) appCost += p.appCosts.hostingMensile;
    appCost += newFree * p.appCosts.aiCostPerCheckup;
    appCost *= risk.costMult;

    var persCost = p.personnel.founderComp * p.personnel.numFounders * (1 + p.personnel.inpsRate / 3);
    persCost += hiredConsultants * h.consultantCost;
    if (hasBackOffice) persCost += h.backOfficeCost;
    if (hasContent) persCost += h.contentCost;
    if (hasJunior) persCost += h.juniorCost;

    var mktCost = (bG + bM + bL) * risk.costMult;

    // --- Mutuo: addebitato ogni 6 mesi dal mese 1 ---
    var mortgageCost = 0;
    if (p.mortgage.enabled && m % 6 === 0) {
      if (m <= p.mortgage.preAmortMonths) {
        mortgageCost = p.mortgage.principal * p.mortgage.rate / 2;
      } else {
        var rSemi = p.mortgage.rate / 2;
        var nSemi = Math.ceil(p.mortgage.amortMonths / 6);
        mortgageCost = rSemi > 0
          ? p.mortgage.principal * rSemi / (1 - Math.pow(1 + rSemi, -nSemi))
          : p.mortgage.principal / nSemi;
      }
    }

    // --- Ricavi: abbonamenti mensili per fascia ---
    var mrrApp = cApp * p.fasce.priceApp;
    var mrrMon = cMon * p.fasce.priceMonitor;
    var mrrLive = cLive * p.fasce.priceLive;
    var mrr = mrrApp + mrrMon + mrrLive;
    var arr = mrr * 12;
    var arpuEff = totalClients > 0 ? arr / totalClients : 0;

    // --- Fiscalità: provisione mensile IRES + IRAP (stima rolling 12 mesi) ---
    var totCostPreTax = constCost + opCost + appCost + persCost + mktCost + mortgageCost;
    revWindow12.push(mrr);
    costWindow12.push(totCostPreTax);
    if (revWindow12.length > 12) { revWindow12.shift(); costWindow12.shift(); }
    var trailingProfit = Math.max(0,
      revWindow12.reduce(function(s, v) { return s + v; }, 0) -
      costWindow12.reduce(function(s, v) { return s + v; }, 0));
    var taxCost = 0;
    if (p.taxation.enabled && m >= 13) {
      taxCost = trailingProfit * p.taxation.iresRate / 12
        + Math.max(0, mrr - opCost) * p.taxation.irapRate;
    }
    var totCost = totCostPreTax + taxCost;

    // --- AUM monitorato (solo Monitor + Live) + benchmark S&P 500 ---
    if (m >= 13) {
      monitoredAUM *= (1 + sp500Monthly);
      var newAssist = newMon + newLive + (m === 13 ? waitingListBoost * (p.fasce.mixMonitor + mixLive) : 0);
      var churnAssist = churnM + churnL;
      var prevAssist = assistiti - newAssist + churnAssist;
      if (prevAssist > 0 && churnAssist > 0) {
        monitoredAUM -= monitoredAUM * (churnAssist / prevAssist);
      }
      monitoredAUM += newAssist * p.aum.avgPerClient;
    }
    var totalAUM = monitoredAUM;
    if (m === 13) { sp500BenchmarkValue = totalAUM; }
    else if (m > 13) { sp500BenchmarkValue *= (1 + sp500Monthly); }

    revCum += mrr;
    costCum += totCost;

    var netBurn = totCost - mrr;
    cash -= netBurn;
    if (cash < cashMin) { cashMin = cash; cashMinMonth = m; }

    var staffCount = p.personnel.numFounders + hiredConsultants + (hasBackOffice?1:0) + (hasContent?1:0) + (hasJunior?1:0);

    results.push({
      month: m, monthLabel: label, phase: phase, phaseName: phaseName, isPreRelease: isPreRelease,
      googleClicks: gClicks, googleBookings: gSign, googleBudget: bG,
      metaClicks: mClicks, metaBookings: mSign, metaBudget: bM,
      linkedinClicks: lClicks, linkedinBookings: lSign, linkedinBudget: bL,
      seoVisits: seoV, seoBookings: seoSign, socialVisits: socV, socialBookings: socSign,
      referralBookings: refSign, borrowedBookings: borSign,
      totalSignups: totSign, newFreeUsers: newFree, freeUsers: freeUsers,
      newPaying: newPaying, newApp: newApp, newMonitor: newMon, newLive: newLive,
      maxNewLive: maxNewLive,
      churnedClients: churn,
      clientsApp: cApp, clientsMonitor: cMon, clientsLive: cLive,
      totalClients: totalClients, assistiti: assistiti,
      constitutionCosts: constCost, operatingCosts: opCost, appCosts: appCost,
      personnelCosts: persCost, marketingCosts: mktCost,
      mortgageCost: mortgageCost, taxCost: taxCost, totalCosts: totCost,
      waitingListBoost: waitingListBoost,
      mrr: mrr, mrrApp: mrrApp, mrrMonitor: mrrMon, mrrLive: mrrLive,
      arr: arr, arpuEff: arpuEff,
      totalAUM: totalAUM, sp500BenchmarkValue: sp500BenchmarkValue,
      netBurn: netBurn, cashRemaining: cash,
      revenueCumulative: revCum, costsCumulative: costCum,
      founderHours: fHours, totalHours: totHours,
      capacityLimited: capLimited,
      liveUtilization: liveUtil, budgetFactor: budgetFactor,
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
