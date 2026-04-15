/* ============================================================
   Proxima Funnel Model — Bottom-Up
   Index 1..24 = strategy month -6..+18
   Phase boundaries (index): 1-3 F1 | 4-6 F2 | 7-9 F3 | 10-12 F4 | 13-24 F5
   ============================================================ */

window.PROXIMA = window.PROXIMA || {};

window.PROXIMA.getPhase = function (m) {
  if (m <= 3) return 1;
  if (m <= 6) return 2;
  if (m <= 9) return 3;
  if (m <= 12) return 4;
  return 5;
};

window.PROXIMA.phaseLabel = function (p) {
  return ["", "Pre-lancio", "Alpha", "Beta", "Early Access", "Lancio Pubblico"][p] || "";
};

// Strategy top-down targets (from 04-revenue-forecast.md) for comparison
// indexed by model month (1..24 = strategy month -6..+18)
window.PROXIMA.strategyTargets = {
  clients: {
    1: 0, 2: 0, 3: 0, 4: 3, 5: 7, 6: 12,
    7: 20, 8: 30, 9: 42, 10: 53, 11: 67, 12: 84,
    13: 108, 14: 135, 15: 163, 16: 191, 17: 217, 18: 245,
    19: 277, 20: 312, 21: 349, 22: 387, 23: 425, 24: 509
  },
  milestoneClients: { 13: 108, 19: 277, 24: 509 },
  milestoneARR: { 13: 52920, 19: 135730, 24: 249410 }
};

// Default parameters — tweakable via UI sliders
window.PROXIMA.defaultParams = function () {
  return {
    // ---------- Funnel: Google Ads ----------
    google: {
      cpc: 1.80,
      clickToCalc: 0.60,      // % click che arriva al calcolatore
      calcToBooking: 0.08,    // % uso calc → prenotazione
      budgetByPhase: [0, 0, 0, 1000, 2200, 3500]  // [_, F1, F2, F3, F4, F5]
    },
    // ---------- Funnel: Meta Ads ----------
    meta: {
      cpc: 0.90,
      clickToCalc: 0.35,
      calcToBooking: 0.05,
      budgetByPhase: [0, 0, 0, 800, 1300, 1800]
    },
    // ---------- Funnel: LinkedIn Ads ----------
    linkedin: {
      cpc: 6.00,
      clickToCalc: 0.50,
      calcToBooking: 0.06,
      budgetByPhase: [0, 0, 0, 0, 0, 700],
      startMonth: 15   // index 15 = strategy month +9
    },
    // ---------- Funnel: SEO Organic ----------
    seo: {
      baseVisits: 30,         // visite/mese al mese 1
      growthRate: 0.22,       // crescita compound mensile
      visitToCalc: 0.18,      // % visite che usa calcolatore
      calcToBooking: 0.06
    },
    // ---------- Funnel: Social Organic ----------
    social: {
      baseVisits: 60,
      growthRate: 0.14,
      visitToCalc: 0.10,
      calcToBooking: 0.04
    },
    // ---------- Referral ----------
    referral: {
      ratePerClient: 0.06,    // % clienti attivi che porta 1 referral/mese
      bookingRate: 0.80,      // % referral che prenota check-up
      startMonth: 15          // index 15 = strategy month +9
    },
    // ---------- Borrowed (PR / podcast / eventi) ----------
    borrowed: {
      bookingsByPhase: [0, 1, 3, 6, 10, 14]  // prenotazioni/mese per fase
    },
    // ---------- Post-funnel ----------
    showRate: 0.75,             // % prenotazioni che si presenta
    checkupToClient: 0.35,      // % check-up completati → cliente pagante
    // ---------- Capacity ----------
    founderHoursPerWeek: 20,
    hoursPerClient: 3.5,
    secondConsultantStartMonth: 20,   // strategy month +14
    secondConsultantHoursPerWeek: 20,
    // ---------- Business ----------
    arpu: 490,
    churnMonthly: 0.01,
    // ---------- Fixed monthly ops cost (tool + freelance + infra) ----------
    // Not used for clients, only for cumulative spend tracking
    fixedSpendByPhase: [0, 4667, 7333, 11667, 12667, 4083]  // approx each fase budget / #months
  };
};

// ----- Simulation -----
window.PROXIMA.simulate = function (p, months) {
  months = months || 24;
  const results = [];
  let totalClients = 0;
  let cumulativeRevenue = 0;
  let cumulativeSpend = 0;
  const budgetPaidCumulativeByChannel = { google: 0, meta: 0, linkedin: 0 };

  for (let m = 1; m <= months; m++) {
    const phase = window.PROXIMA.getPhase(m);

    // ---- Budget del mese per canale paid ----
    const bGoogle = p.google.budgetByPhase[phase] || 0;
    const bMeta = p.meta.budgetByPhase[phase] || 0;
    const bLinkedIn = (m >= p.linkedin.startMonth) ? (p.linkedin.budgetByPhase[phase] || 0) : 0;

    // ---- Canale 1: Google Ads ----
    const gClicks = bGoogle / p.google.cpc;
    const gCalc = gClicks * p.google.clickToCalc;
    const gBookings = gCalc * p.google.calcToBooking;

    // ---- Canale 2: Meta Ads ----
    const mClicks = bMeta / p.meta.cpc;
    const mCalc = mClicks * p.meta.clickToCalc;
    const mBookings = mCalc * p.meta.calcToBooking;

    // ---- Canale 3: LinkedIn Ads ----
    const lClicks = bLinkedIn / p.linkedin.cpc;
    const lCalc = lClicks * p.linkedin.clickToCalc;
    const lBookings = lCalc * p.linkedin.calcToBooking;

    // ---- Canale 4: SEO Organico ----
    const seoVisits = p.seo.baseVisits * Math.pow(1 + p.seo.growthRate, m - 1);
    const seoCalc = seoVisits * p.seo.visitToCalc;
    const seoBookings = seoCalc * p.seo.calcToBooking;

    // ---- Canale 5: Social Organico ----
    const socialVisits = p.social.baseVisits * Math.pow(1 + p.social.growthRate, m - 1);
    const socialCalc = socialVisits * p.social.visitToCalc;
    const socialBookings = socialCalc * p.social.calcToBooking;

    // ---- Canale 6: Referral ----
    let refBookings = 0;
    if (m >= p.referral.startMonth) {
      refBookings = totalClients * p.referral.ratePerClient * p.referral.bookingRate;
    }

    // ---- Canale 7: Borrowed (PR / podcast / eventi) ----
    const borrowedBookings = p.borrowed.bookingsByPhase[phase] || 0;

    // ---- Totale prenotazioni ----
    const totalBookings = gBookings + mBookings + lBookings + seoBookings + socialBookings + refBookings + borrowedBookings;

    // ---- Show-rate: check-up effettivamente completati ----
    const actualCheckups = totalBookings * p.showRate;

    // ---- Nuovi clienti teorici (se capacità infinita) ----
    const newClientsTheoretical = actualCheckups * p.checkupToClient;

    // ---- Vincolo capacità ----
    const founderHoursMonth = p.founderHoursPerWeek * 4.33;
    const secondHoursMonth = (m >= p.secondConsultantStartMonth) ? p.secondConsultantHoursPerWeek * 4.33 : 0;
    const totalHours = founderHoursMonth + secondHoursMonth;
    const maxClientsByCapacity = totalHours / p.hoursPerClient;

    const newClients = Math.min(newClientsTheoretical, maxClientsByCapacity);
    const capacityLimited = newClientsTheoretical > maxClientsByCapacity + 0.5;

    // ---- Churn ----
    const churn = totalClients * p.churnMonthly;
    const prevClients = totalClients;
    totalClients = Math.max(0, totalClients + newClients - churn);

    // ---- Revenue ----
    const mrr = totalClients * p.arpu / 12;
    const arr = totalClients * p.arpu;
    cumulativeRevenue += mrr;

    // ---- Spesa ----
    const monthlyPaidSpend = bGoogle + bMeta + bLinkedIn;
    const monthlyFixedSpend = p.fixedSpendByPhase[phase] || 0;
    const monthlySpend = monthlyPaidSpend + monthlyFixedSpend;
    cumulativeSpend += monthlySpend;
    budgetPaidCumulativeByChannel.google += bGoogle;
    budgetPaidCumulativeByChannel.meta += bMeta;
    budgetPaidCumulativeByChannel.linkedin += bLinkedIn;

    // ---- Rapporto nuovi clienti per canale (proporzionale a bookings) ----
    const bookingRatio = (totalBookings > 0) ? newClients / totalBookings : 0;
    const byChannel = {
      google: gBookings * p.showRate * p.checkupToClient * (newClients / Math.max(newClientsTheoretical, 0.0001)),
      meta: mBookings * p.showRate * p.checkupToClient * (newClients / Math.max(newClientsTheoretical, 0.0001)),
      linkedin: lBookings * p.showRate * p.checkupToClient * (newClients / Math.max(newClientsTheoretical, 0.0001)),
      seo: seoBookings * p.showRate * p.checkupToClient * (newClients / Math.max(newClientsTheoretical, 0.0001)),
      social: socialBookings * p.showRate * p.checkupToClient * (newClients / Math.max(newClientsTheoretical, 0.0001)),
      referral: refBookings * p.showRate * p.checkupToClient * (newClients / Math.max(newClientsTheoretical, 0.0001)),
      borrowed: borrowedBookings * p.showRate * p.checkupToClient * (newClients / Math.max(newClientsTheoretical, 0.0001)),
    };

    results.push({
      month: m,
      strategyMonth: m - 6,
      phase,
      traffic: { google: gClicks, meta: mClicks, linkedin: lClicks, seo: seoVisits, social: socialVisits },
      bookings: {
        google: gBookings, meta: mBookings, linkedin: lBookings,
        seo: seoBookings, social: socialBookings,
        referral: refBookings, borrowed: borrowedBookings,
        total: totalBookings
      },
      byChannel,
      actualCheckups,
      newClientsTheoretical,
      maxClientsByCapacity,
      capacityLimited,
      newClients,
      churn,
      prevClients,
      totalClients,
      mrr, arr,
      cumulativeRevenue,
      monthlySpend, monthlyPaidSpend, monthlyFixedSpend,
      cumulativeSpend,
      budgets: { google: bGoogle, meta: bMeta, linkedin: bLinkedIn }
    });
  }

  // Break-even: primo mese in cui cumulativeRevenue >= totalInvestment(180k)
  const TARGET_INVESTMENT = 180000;
  let breakEvenMonth = null;
  for (const r of results) {
    if (r.cumulativeRevenue >= TARGET_INVESTMENT) { breakEvenMonth = r.month; break; }
  }

  // Blended CAC by milestone (cumulative paid spend / cumulative paid-acquired clients)
  const computeBlendedCAC = (upToMonth) => {
    const slice = results.slice(0, upToMonth);
    const totalPaidSpend = slice.reduce((s, r) => s + r.monthlyPaidSpend, 0);
    const totalPaidClients = slice.reduce((s, r) => s + (r.byChannel.google + r.byChannel.meta + r.byChannel.linkedin), 0);
    return totalPaidClients > 0 ? totalPaidSpend / totalPaidClients : 0;
  };

  return {
    results,
    breakEvenMonth,
    cacBlended: { m12: computeBlendedCAC(12), m18: computeBlendedCAC(18), m24: computeBlendedCAC(24) },
    budgetPaidCumulativeByChannel
  };
};
