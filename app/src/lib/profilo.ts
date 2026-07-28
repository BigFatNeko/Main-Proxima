import { DOMANDE, SEZIONI } from '../data/questionario';
import { ORDINE_PROFILI } from '../data/pacchetti';
import type {
  AreaMifid,
  Domanda,
  EsitoProfilazione,
  FasciaPatrimonio,
  ProfiloId,
  PunteggiAree,
  Risposte,
  Vincolo,
} from '../types';

/** Punteggio massimo ottenibile in una domanda. */
function massimoDomanda(d: Domanda): number {
  if (d.tipo === 'multipla') return d.opzioni.reduce((tot, o) => tot + o.punti, 0);
  return Math.max(...d.opzioni.map((o) => o.punti));
}

/** Punteggio ottenuto in una domanda, dato lo stato delle risposte. */
function punteggioDomanda(d: Domanda, risposte: Risposte): number {
  const r = risposte[d.id];
  if (r === undefined) return 0;
  const scelte = Array.isArray(r) ? r : [r];
  return d.opzioni.filter((o) => scelte.includes(o.id)).reduce((tot, o) => tot + o.punti, 0);
}

/** Punteggio 0-100 di un'area MiFID. */
function punteggioArea(area: AreaMifid, risposte: Risposte): number {
  const domande = DOMANDE.filter((d) => d.area === area);
  const ottenuto = domande.reduce((tot, d) => tot + punteggioDomanda(d, risposte), 0);
  const massimo = domande.reduce((tot, d) => tot + massimoDomanda(d), 0);
  if (massimo === 0) return 0;
  return Math.round((ottenuto / massimo) * 100);
}

export function calcolaPunteggi(risposte: Risposte): PunteggiAree {
  return {
    capacita: punteggioArea('situazione-finanziaria', risposte),
    conoscenza: punteggioArea('conoscenza-esperienza', risposte),
    orizzonte: punteggioArea('obiettivi', risposte),
    tolleranza: punteggioArea('tolleranza-rischio', risposte),
    sostenibilita: punteggioArea('sostenibilita', risposte),
  };
}

/** Soglia massima di punteggio associata a ciascun profilo. */
const TETTO_PROFILO: Record<ProfiloId, number> = {
  conservativo: 19,
  prudente: 39,
  equilibrato: 59,
  dinamico: 79,
  aggressivo: 100,
};

export function profiloDaPunteggio(punteggio: number): ProfiloId {
  return ORDINE_PROFILI.find((p) => punteggio <= TETTO_PROFILO[p]) ?? 'aggressivo';
}

/**
 * Vincoli di adeguatezza. La logica MiFID non è una media: un solo elemento
 * critico (orizzonte corto, nessun fondo di emergenza, conoscenza assente)
 * abbassa il profilo indipendentemente da quanto rischio la persona dica di
 * tollerare.
 */
function applicaVincoli(
  grezzo: number,
  punteggi: PunteggiAree,
  risposte: Risposte,
): { punteggio: number; vincoli: Vincolo[] } {
  const vincoli: Vincolo[] = [];
  let punteggio = grezzo;

  /* Un vincolo va spiegato al cliente se limita il punteggio che le sue
     risposte avrebbero prodotto, anche quando un altro vincolo più severo ha
     già abbassato il profilo: sono due ragioni distinte, entrambe vere. */
  const limita = (tetto: ProfiloId, area: AreaMifid, motivo: string) => {
    const max = TETTO_PROFILO[tetto];
    if (grezzo > max) vincoli.push({ area, motivo });
    if (punteggio > max) punteggio = max;
  };

  if (risposte['ob-orizzonte'] === 'a') {
    limita(
      'conservativo',
      'obiettivi',
      'Ti servono i soldi entro 2 anni: su questo orizzonte non possiamo esporti alle oscillazioni dei mercati azionari.',
    );
  }

  if (risposte['sf-emergenza'] === 'a') {
    limita(
      'prudente',
      'situazione-finanziaria',
      'Non hai ancora un fondo di emergenza: prima di alzare il rischio va costruito, altrimenti un imprevisto ti costringe a vendere nel momento peggiore.',
    );
  }

  if (punteggi.conoscenza < 30) {
    limita(
      'prudente',
      'conoscenza-esperienza',
      'La tua esperienza con gli strumenti finanziari è ancora limitata: partiamo da un portafoglio semplice e alziamo il rischio quando avrai visto come si comporta.',
    );
  }

  if (punteggi.tolleranza < 25) {
    limita(
      'prudente',
      'tolleranza-rischio',
      'Dalle tue risposte una perdita significativa ti creerebbe disagio reale: un portafoglio che ti fa vendere nel panico è peggio di uno meno redditizio.',
    );
  }

  if (risposte['ob-liquidita'] === 'a') {
    limita(
      'equilibrato',
      'obiettivi',
      'È molto probabile che tu debba disinvestire in anticipo: teniamo una quota più alta di strumenti stabili.',
    );
  }

  if (punteggi.capacita < 30) {
    limita(
      'equilibrato',
      'situazione-finanziaria',
      'La tua capacità di assorbire una perdita è contenuta: il portafoglio deve restare proporzionato al capitale che puoi permetterti di rischiare.',
    );
  }

  return { punteggio, vincoli };
}

const FASCE: FasciaPatrimonio[] = ['fino-20k', '20k-50k', '50k-100k', 'oltre-100k'];

function fasciaPatrimonio(risposte: Risposte): FasciaPatrimonio {
  const r = risposte['sf-patrimonio'];
  const id = Array.isArray(r) ? r[0] : r;
  return FASCE.find((f) => f === id) ?? 'fino-20k';
}

export function profila(risposte: Risposte): EsitoProfilazione {
  const punteggi = calcolaPunteggi(risposte);

  const grezzo = Math.round(
    punteggi.tolleranza * 0.4 + punteggi.orizzonte * 0.35 + punteggi.capacita * 0.25,
  );

  const { punteggio, vincoli } = applicaVincoli(grezzo, punteggi, risposte);

  return {
    profilo: profiloDaPunteggio(punteggio),
    punteggioRischio: punteggio,
    punteggioGrezzo: grezzo,
    punteggi,
    vincoli,
    fasciaPatrimonio: fasciaPatrimonio(risposte),
    preferenzaEsg: punteggi.sostenibilita >= 50,
  };
}

/** Tutte le domande hanno una risposta valida? Le multiple accettano l'insieme vuoto. */
export function questionarioCompleto(risposte: Risposte): boolean {
  return DOMANDE.every((d) => {
    const r = risposte[d.id];
    if (d.tipo === 'multipla') return Array.isArray(r);
    return typeof r === 'string' && r.length > 0;
  });
}

export function sezioneCompleta(indice: number, risposte: Risposte): boolean {
  return SEZIONI[indice].domande.every((d) => {
    const r = risposte[d.id];
    if (d.tipo === 'multipla') return Array.isArray(r);
    return typeof r === 'string' && r.length > 0;
  });
}
