import { PACCHETTI } from './pacchetti';
import type { FasciaPatrimonio, ProfiloId } from '../types';

/**
 * Serie di performance dimostrative.
 *
 * DATI FINTI, generati in modo deterministico dal profilo: stesso profilo →
 * stessa curva a ogni caricamento, così le schermate sono stabili durante le
 * demo. Vanno sostituiti dai valori reali del portafoglio del cliente quando
 * ci sarà il collegamento con il broker.
 */

export interface PuntoSerie {
  /** Primo giorno del mese, ISO. */
  data: string;
  /** Numero indice, base 100 alla sottoscrizione. */
  portafoglio: number;
  benchmark: number;
}

export interface Performance {
  punti: PuntoSerie[];
  capitaleIniziale: number;
  valoreAttuale: number;
  rendimentoPortafoglio: number;
  rendimentoBenchmark: number;
  /** Differenza in punti percentuali fra portafoglio e benchmark. */
  scarto: number;
  /** Costi evitati rispetto a un prodotto bancario medio (1,85% annuo). */
  costiEvitati: number;
  mesi: number;
}

const CAPITALE_FASCIA: Record<FasciaPatrimonio, number> = {
  'fino-20k': 12000,
  '20k-50k': 32000,
  '50k-100k': 68000,
  'oltre-100k': 140000,
};

/** PRNG deterministico: stesso seme → stessa sequenza. */
function mulberry32(seme: number): () => number {
  let a = seme;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Normale standard via Box-Muller. */
function normale(rand: () => number): number {
  const u = Math.max(rand(), 1e-9);
  const v = rand();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

function seme(profilo: ProfiloId, fascia: FasciaPatrimonio): number {
  const testo = `${profilo}-${fascia}`;
  let h = 2166136261;
  for (let i = 0; i < testo.length; i += 1) {
    h ^= testo.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

function inizioMese(offsetMesi: number): Date {
  const oggi = new Date();
  return new Date(Date.UTC(oggi.getUTCFullYear(), oggi.getUTCMonth() - offsetMesi, 1));
}

export function calcolaPerformance(
  profilo: ProfiloId,
  fascia: FasciaPatrimonio,
  mesi = 18,
): Performance {
  const pacchetto = PACCHETTI[profilo];
  const rand = mulberry32(seme(profilo, fascia));

  const driftMensile = pacchetto.rendimentoAtteso / 100 / 12;
  const volMensile = pacchetto.volatilita / 100 / Math.sqrt(12);

  /* Il portafoglio reale si discosta dal modello per tre motivi: i costi degli
     strumenti, il tempo che il denaro resta liquido fra un versamento e l'altro,
     e i ribilanciamenti fatti in ritardo rispetto al modello teorico. */
  const attritoMensile = pacchetto.terMedio / 100 / 12 + 0.0004;
  const trackingError = volMensile * 0.18;

  const punti: PuntoSerie[] = [];
  let indiceBenchmark = 100;
  let indicePortafoglio = 100;

  for (let m = 0; m <= mesi; m += 1) {
    if (m > 0) {
      const shockComune = normale(rand);
      const shockSpecifico = normale(rand);
      indiceBenchmark *= 1 + driftMensile + volMensile * shockComune;
      indicePortafoglio *=
        1 + driftMensile - attritoMensile + volMensile * shockComune + trackingError * shockSpecifico;
    }
    punti.push({
      data: inizioMese(mesi - m).toISOString(),
      portafoglio: Math.round(indicePortafoglio * 100) / 100,
      benchmark: Math.round(indiceBenchmark * 100) / 100,
    });
  }

  const capitaleIniziale = CAPITALE_FASCIA[fascia];
  const ultimo = punti[punti.length - 1];
  const anni = mesi / 12;

  return {
    punti,
    capitaleIniziale,
    valoreAttuale: Math.round((capitaleIniziale * ultimo.portafoglio) / 100),
    rendimentoPortafoglio: Math.round((ultimo.portafoglio - 100) * 10) / 10,
    rendimentoBenchmark: Math.round((ultimo.benchmark - 100) * 10) / 10,
    scarto: Math.round((ultimo.portafoglio - ultimo.benchmark) * 10) / 10,
    costiEvitati: Math.round(capitaleIniziale * (0.0185 - pacchetto.terMedio / 100) * anni),
    mesi,
  };
}
