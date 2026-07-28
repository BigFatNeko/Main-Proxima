/** Tipi condivisi dell'area clienti Proxima. */

export type SchermataId = 'login' | 'questionario' | 'consulente' | 'dashboard';

/* ---------- Questionario MiFID ---------- */

/** Le cinque aree di adeguatezza previste da MiFID II (art. 54-55 Reg. UE 565/2017). */
export type AreaMifid =
  | 'situazione-finanziaria'
  | 'conoscenza-esperienza'
  | 'obiettivi'
  | 'tolleranza-rischio'
  | 'sostenibilita';

export interface OpzioneRisposta {
  id: string;
  testo: string;
  /** Contributo al punteggio dell'area (0-10). */
  punti: number;
  nota?: string;
}

export interface Domanda {
  id: string;
  area: AreaMifid;
  testo: string;
  aiuto?: string;
  tipo: 'singola' | 'multipla';
  opzioni: OpzioneRisposta[];
}

export interface SezioneQuestionario {
  area: AreaMifid;
  titolo: string;
  descrizione: string;
  domande: Domanda[];
}

/** id domanda -> id opzione (singola) oppure elenco di id (multipla). */
export type Risposte = Record<string, string | string[]>;

/* ---------- Profilo calcolato ---------- */

export type ProfiloId = 'conservativo' | 'prudente' | 'equilibrato' | 'dinamico' | 'aggressivo';

export interface PunteggiAree {
  /** Capacità patrimoniale di sopportare perdite (0-100). */
  capacita: number;
  /** Conoscenza ed esperienza finanziaria (0-100). */
  conoscenza: number;
  /** Orizzonte temporale e obiettivi (0-100). */
  orizzonte: number;
  /** Tolleranza soggettiva al rischio (0-100). */
  tolleranza: number;
  /** Interesse per gli investimenti sostenibili (0-100). */
  sostenibilita: number;
}

export interface Vincolo {
  area: AreaMifid;
  motivo: string;
}

export interface EsitoProfilazione {
  profilo: ProfiloId;
  /** Punteggio di rischio finale, dopo l'applicazione dei vincoli (0-100). */
  punteggioRischio: number;
  /** Punteggio prima dei vincoli, utile per spiegare la differenza. */
  punteggioGrezzo: number;
  punteggi: PunteggiAree;
  /** Vincoli MiFID che hanno abbassato il profilo rispetto al grezzo. */
  vincoli: Vincolo[];
  /** Fascia di patrimonio dichiarata, guida la tariffa. */
  fasciaPatrimonio: FasciaPatrimonio;
  preferenzaEsg: boolean;
}

export type FasciaPatrimonio = 'fino-20k' | '20k-50k' | '50k-100k' | 'oltre-100k';

/* ---------- Pacchetti ---------- */

export interface ClasseAttivo {
  nome: string;
  peso: number;
  /** Azionario = motore di rendimento; difensivo = obbligazionario e liquidità. */
  tipo: 'azionario' | 'difensivo';
}

export interface Pacchetto {
  id: ProfiloId;
  nome: string;
  claim: string;
  descrizione: string;
  allocazione: ClasseAttivo[];
  /** Rendimento atteso annuo lordo, in percentuale. */
  rendimentoAtteso: number;
  /** Volatilità annua attesa, in percentuale. */
  volatilita: number;
  /** Perdita massima storica simulata su 12 mesi, in percentuale (negativa). */
  perditaMassima: number;
  orizzonteMinimoAnni: number;
  /** TER medio ponderato degli ETF in portafoglio, in percentuale. */
  terMedio: number;
  adattoA: string[];
}

export interface PianoTariffario {
  id: FasciaPatrimonio;
  nome: string;
  patrimonio: string;
  canoneAnnuo: number;
  incluso: string[];
}

/* ---------- Conversazione con il consulente digitale ---------- */

export type AutoreMessaggio = 'bot' | 'utente';

export interface Messaggio {
  id: string;
  autore: AutoreMessaggio;
  testo: string;
  /** Blocco ricco opzionale mostrato sotto al testo. */
  allegato?:
    | { tipo: 'pacchetti'; ids: ProfiloId[]; consigliato: ProfiloId }
    | { tipo: 'punteggi' }
    | { tipo: 'tariffa' };
}

export interface AzioneBot {
  id: string;
  etichetta: string;
}

/* ---------- Sessione utente ---------- */

export interface Utente {
  nome: string;
  email: string;
}

export interface StatoUtente {
  utente: Utente;
  /** Numero di accessi completati: al 2° accesso si entra dalla dashboard. */
  accessi: number;
  risposte: Risposte | null;
  esito: EsitoProfilazione | null;
  pacchettoScelto: ProfiloId | null;
  /** ISO date della sottoscrizione del pacchetto. */
  sottoscrittoIl: string | null;
}
