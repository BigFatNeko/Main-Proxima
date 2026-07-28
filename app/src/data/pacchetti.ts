import type { FasciaPatrimonio, Pacchetto, PianoTariffario, ProfiloId } from '../types';

/**
 * Portafogli modello Proxima: cinque combinazioni di ETF a basso costo, una per
 * profilo di rischio. Rendimenti e volatilità sono attese di lungo periodo, non
 * garanzie: servono a far capire l'ordine di grandezza dell'oscillazione.
 *
 * Numeri indicativi da validare con il consulente prima della messa in produzione.
 */
export const PACCHETTI: Record<ProfiloId, Pacchetto> = {
  conservativo: {
    id: 'conservativo',
    nome: 'Proxima Riserva',
    claim: 'Proteggere prima di tutto',
    descrizione:
      'Portafoglio pensato per chi non vuole vedere oscillazioni marcate: la parte azionaria è minima e serve solo a non farsi erodere dall’inflazione.',
    allocazione: [
      { nome: 'Obbligazionario governativo breve termine', peso: 45, tipo: 'difensivo' },
      { nome: 'Obbligazionario aggregato euro', peso: 35, tipo: 'difensivo' },
      { nome: 'Azionario globale', peso: 15, tipo: 'azionario' },
      { nome: 'Liquidità', peso: 5, tipo: 'difensivo' },
    ],
    rendimentoAtteso: 3.1,
    volatilita: 3.5,
    perditaMassima: -4,
    orizzonteMinimoAnni: 2,
    terMedio: 0.14,
    adattoA: ['Orizzonte breve', 'Capitale da preservare', 'Prima esperienza di investimento'],
  },
  prudente: {
    id: 'prudente',
    nome: 'Proxima Prudenza',
    claim: 'Crescere piano, dormire sereno',
    descrizione:
      'Il peso resta sull’obbligazionario, ma un quarto del portafoglio lavora sui mercati azionari globali per dare un rendimento reale positivo.',
    allocazione: [
      { nome: 'Obbligazionario aggregato euro', peso: 45, tipo: 'difensivo' },
      { nome: 'Obbligazionario governativo breve termine', peso: 20, tipo: 'difensivo' },
      { nome: 'Azionario globale', peso: 30, tipo: 'azionario' },
      { nome: 'Liquidità', peso: 5, tipo: 'difensivo' },
    ],
    rendimentoAtteso: 4.2,
    volatilita: 6,
    perditaMassima: -9,
    orizzonteMinimoAnni: 4,
    terMedio: 0.15,
    adattoA: ['Orizzonte 4-6 anni', 'Bassa tolleranza alle perdite', 'Obiettivo definito'],
  },
  equilibrato: {
    id: 'equilibrato',
    nome: 'Proxima Bilanciato',
    claim: 'Il compromesso che regge nel tempo',
    descrizione:
      'Metà azionario e metà obbligazionario: la combinazione più studiata della letteratura finanziaria, adatta a chi ha un orizzonte di medio periodo.',
    allocazione: [
      { nome: 'Azionario globale sviluppato', peso: 40, tipo: 'azionario' },
      { nome: 'Obbligazionario aggregato euro', peso: 35, tipo: 'difensivo' },
      { nome: 'Azionario mercati emergenti', peso: 10, tipo: 'azionario' },
      { nome: 'Obbligazionario governativo breve termine', peso: 10, tipo: 'difensivo' },
      { nome: 'Liquidità', peso: 5, tipo: 'difensivo' },
    ],
    rendimentoAtteso: 5.4,
    volatilita: 9.5,
    perditaMassima: -18,
    orizzonteMinimoAnni: 6,
    terMedio: 0.17,
    adattoA: ['Orizzonte 6-10 anni', 'Accetti oscillazioni moderate', 'Crescita del capitale'],
  },
  dinamico: {
    id: 'dinamico',
    nome: 'Proxima Crescita',
    claim: 'Più mercato, più tempo',
    descrizione:
      'Il portafoglio è guidato dall’azionario globale. Le discese sono più profonde, ma su orizzonti lunghi il premio al rischio ha storicamente pagato.',
    allocazione: [
      { nome: 'Azionario globale sviluppato', peso: 55, tipo: 'azionario' },
      { nome: 'Azionario mercati emergenti', peso: 15, tipo: 'azionario' },
      { nome: 'Obbligazionario aggregato euro', peso: 25, tipo: 'difensivo' },
      { nome: 'Liquidità', peso: 5, tipo: 'difensivo' },
    ],
    rendimentoAtteso: 6.5,
    volatilita: 13,
    perditaMassima: -28,
    orizzonteMinimoAnni: 8,
    terMedio: 0.18,
    adattoA: ['Orizzonte oltre 8 anni', 'Nessun bisogno di liquidità', 'Esperienza consolidata'],
  },
  aggressivo: {
    id: 'aggressivo',
    nome: 'Proxima Orizzonte',
    claim: 'Tutto sul lungo periodo',
    descrizione:
      'Quasi interamente azionario. Va scelto solo se sei consapevole che una discesa del 35% è un evento normale, non un incidente.',
    allocazione: [
      { nome: 'Azionario globale sviluppato', peso: 60, tipo: 'azionario' },
      { nome: 'Azionario mercati emergenti', peso: 20, tipo: 'azionario' },
      { nome: 'Azionario small cap globale', peso: 10, tipo: 'azionario' },
      { nome: 'Obbligazionario aggregato euro', peso: 10, tipo: 'difensivo' },
    ],
    rendimentoAtteso: 7.4,
    volatilita: 16.5,
    perditaMassima: -38,
    orizzonteMinimoAnni: 10,
    terMedio: 0.2,
    adattoA: ['Orizzonte oltre 10 anni', 'Alta tolleranza alle perdite', 'Obiettivo previdenziale'],
  },
};

export const ORDINE_PROFILI: ProfiloId[] = [
  'conservativo',
  'prudente',
  'equilibrato',
  'dinamico',
  'aggressivo',
];

export const NOME_PROFILO: Record<ProfiloId, string> = {
  conservativo: 'Conservativo',
  prudente: 'Prudente',
  equilibrato: 'Equilibrato',
  dinamico: 'Dinamico',
  aggressivo: 'Aggressivo',
};

/**
 * Piani tariffari per fascia di patrimonio.
 * Allineati a PROXIMA-Main/01-strategia/piano-di-lancio/04-revenue-forecast.md.
 */
export const PIANI: Record<FasciaPatrimonio, PianoTariffario> = {
  'fino-20k': {
    id: 'fino-20k',
    nome: 'Essenziale',
    patrimonio: 'Fino a €20.000',
    canoneAnnuo: 250,
    incluso: [
      'Portafoglio modello e piano di versamenti',
      'Check-up annuale in video call',
      'Dashboard e alert di ribilanciamento',
    ],
  },
  '20k-50k': {
    id: '20k-50k',
    nome: 'Progresso',
    patrimonio: 'Tra €20.000 e €50.000',
    canoneAnnuo: 500,
    incluso: [
      'Tutto il piano Essenziale',
      'Due check-up all’anno',
      'Analisi dei costi dei prodotti che già possiedi',
      'Supporto via email con risposta in 2 giorni lavorativi',
    ],
  },
  '50k-100k': {
    id: '50k-100k',
    nome: 'Completo',
    patrimonio: 'Tra €50.000 e €100.000',
    canoneAnnuo: 800,
    incluso: [
      'Tutto il piano Progresso',
      'Check-up trimestrale',
      'Pianificazione fiscale delle plusvalenze',
      'Analisi previdenziale e assicurativa',
    ],
  },
  'oltre-100k': {
    id: 'oltre-100k',
    nome: 'Patrimoniale',
    patrimonio: 'Oltre €100.000',
    canoneAnnuo: 1200,
    incluso: [
      'Tutto il piano Completo',
      'Consulente dedicato e incontri su richiesta',
      'Pianificazione successoria',
      'Consolidamento di più conti e intestazioni',
    ],
  },
};
