import type { SezioneQuestionario } from '../types';

/**
 * Questionario di adeguatezza in stile MiFID II.
 *
 * Copre le cinque aree richieste dall'art. 54 Reg. delegato (UE) 2017/565 e
 * dall'art. 39 del Regolamento Intermediari Consob, più le preferenze di
 * sostenibilità obbligatorie dal 2 agosto 2022 (Reg. UE 2021/1253).
 *
 * I `punti` di ogni opzione vanno da 0 a 10 e alimentano il punteggio dell'area
 * (vedi `lib/profilo.ts`). Questa è una bozza di prodotto: i testi definitivi
 * vanno validati dal consulente iscritto all'Albo OCF prima dell'uso reale.
 */
export const SEZIONI: SezioneQuestionario[] = [
  {
    area: 'situazione-finanziaria',
    titolo: 'La tua situazione finanziaria',
    descrizione:
      'Serve a capire quanta perdita puoi permetterti di sostenere senza intaccare la tua vita quotidiana.',
    domande: [
      {
        id: 'sf-reddito',
        area: 'situazione-finanziaria',
        testo: 'Qual è il tuo reddito netto annuo?',
        tipo: 'singola',
        opzioni: [
          { id: 'a', testo: 'Fino a €20.000', punti: 2 },
          { id: 'b', testo: 'Tra €20.000 e €35.000', punti: 5 },
          { id: 'c', testo: 'Tra €35.000 e €60.000', punti: 8 },
          { id: 'd', testo: 'Oltre €60.000', punti: 10 },
        ],
      },
      {
        id: 'sf-risparmio',
        area: 'situazione-finanziaria',
        testo: 'Quanta parte del tuo reddito riesci a risparmiare ogni mese?',
        aiuto: 'Considera la media degli ultimi 12 mesi, non il mese migliore.',
        tipo: 'singola',
        opzioni: [
          { id: 'a', testo: 'Niente, o quasi', punti: 0 },
          { id: 'b', testo: 'Fino al 10%', punti: 4 },
          { id: 'c', testo: 'Tra il 10% e il 25%', punti: 8 },
          { id: 'd', testo: 'Oltre il 25%', punti: 10 },
        ],
      },
      {
        id: 'sf-patrimonio',
        area: 'situazione-finanziaria',
        testo: 'Quanto capitale pensi di destinare agli investimenti?',
        aiuto: 'È il capitale su cui lavoreremo insieme, non tutto il tuo patrimonio.',
        tipo: 'singola',
        opzioni: [
          { id: 'fino-20k', testo: 'Fino a €20.000', punti: 3 },
          { id: '20k-50k', testo: 'Tra €20.000 e €50.000', punti: 6 },
          { id: '50k-100k', testo: 'Tra €50.000 e €100.000', punti: 8 },
          { id: 'oltre-100k', testo: 'Oltre €100.000', punti: 10 },
        ],
      },
      {
        id: 'sf-emergenza',
        area: 'situazione-finanziaria',
        testo: 'Quanti mesi di spese hai da parte come fondo di emergenza?',
        aiuto: 'Liquidità immediatamente disponibile, sul conto o su un deposito svincolabile.',
        tipo: 'singola',
        opzioni: [
          { id: 'a', testo: 'Nessuno', punti: 0 },
          { id: 'b', testo: 'Da 1 a 3 mesi', punti: 4 },
          { id: 'c', testo: 'Da 3 a 6 mesi', punti: 8 },
          { id: 'd', testo: 'Più di 6 mesi', punti: 10 },
        ],
      },
      {
        id: 'sf-impegni',
        area: 'situazione-finanziaria',
        testo: 'Hai impegni finanziari ricorrenti importanti?',
        tipo: 'singola',
        opzioni: [
          { id: 'a', testo: 'Sì, oltre il 40% del reddito (mutuo e/o prestiti)', punti: 1 },
          { id: 'b', testo: 'Sì, tra il 20% e il 40% del reddito', punti: 5 },
          { id: 'c', testo: 'Sì, ma sotto il 20% del reddito', punti: 8 },
          { id: 'd', testo: 'No, nessun impegno rilevante', punti: 10 },
        ],
      },
    ],
  },
  {
    area: 'conoscenza-esperienza',
    titolo: 'Conoscenza ed esperienza',
    descrizione:
      'Non possiamo proporti strumenti che non conosci: è un vincolo di legge, prima ancora che una scelta nostra.',
    domande: [
      {
        id: 'ce-strumenti',
        area: 'conoscenza-esperienza',
        testo: 'Quali di questi strumenti conosci nel loro funzionamento di base?',
        aiuto: 'Seleziona tutti quelli che sapresti spiegare a un amico. Puoi non sceglierne nessuno.',
        tipo: 'multipla',
        opzioni: [
          { id: 'conto', testo: 'Conti deposito e titoli di Stato', punti: 2 },
          { id: 'fondi', testo: 'Fondi comuni e polizze', punti: 2 },
          { id: 'etf', testo: 'ETF e indici', punti: 3 },
          { id: 'azioni', testo: 'Azioni e obbligazioni societarie', punti: 2 },
          { id: 'derivati', testo: 'Derivati, leva, cripto', punti: 1, nota: 'Prodotti complessi' },
        ],
      },
      {
        id: 'ce-esperienza',
        area: 'conoscenza-esperienza',
        testo: 'Da quanto tempo investi?',
        tipo: 'singola',
        opzioni: [
          { id: 'a', testo: 'Non ho mai investito', punti: 0 },
          { id: 'b', testo: 'Da meno di 2 anni', punti: 4 },
          { id: 'c', testo: 'Da 2 a 7 anni', punti: 7 },
          { id: 'd', testo: 'Da più di 7 anni', punti: 10 },
        ],
      },
      {
        id: 'ce-operativita',
        area: 'conoscenza-esperienza',
        testo: 'Con che frequenza hai operato negli ultimi tre anni?',
        tipo: 'singola',
        opzioni: [
          { id: 'a', testo: 'Mai', punti: 0 },
          { id: 'b', testo: 'Qualche operazione sporadica', punti: 4 },
          { id: 'c', testo: 'Versamenti regolari (PAC) o alcune operazioni all’anno', punti: 8 },
          { id: 'd', testo: 'Operazioni frequenti, seguo i mercati', punti: 10 },
        ],
      },
      {
        id: 'ce-formazione',
        area: 'conoscenza-esperienza',
        testo: 'Hai una formazione o un’esperienza professionale in ambito economico-finanziario?',
        tipo: 'singola',
        opzioni: [
          { id: 'a', testo: 'No', punti: 0 },
          { id: 'b', testo: 'Mi informo da autodidatta', punti: 5 },
          { id: 'c', testo: 'Sì, studi o lavoro nel settore', punti: 10 },
        ],
      },
    ],
  },
  {
    area: 'obiettivi',
    titolo: 'Obiettivi e orizzonte',
    descrizione: 'Il tempo a disposizione è la variabile che pesa di più sul risultato finale.',
    domande: [
      {
        id: 'ob-finalita',
        area: 'obiettivi',
        testo: 'Qual è l’obiettivo principale di questo investimento?',
        tipo: 'singola',
        opzioni: [
          { id: 'a', testo: 'Proteggere il capitale dall’inflazione', punti: 2 },
          { id: 'b', testo: 'Un progetto definito (casa, studi, auto)', punti: 4 },
          { id: 'c', testo: 'Costruire un capitale nel lungo periodo', punti: 8 },
          { id: 'd', testo: 'Integrare la pensione', punti: 9 },
        ],
      },
      {
        id: 'ob-orizzonte',
        area: 'obiettivi',
        testo: 'Tra quanto tempo prevedi di utilizzare questo capitale?',
        tipo: 'singola',
        opzioni: [
          { id: 'a', testo: 'Entro 2 anni', punti: 0, nota: 'Orizzonte breve' },
          { id: 'b', testo: 'Tra 2 e 5 anni', punti: 4 },
          { id: 'c', testo: 'Tra 5 e 10 anni', punti: 8 },
          { id: 'd', testo: 'Oltre 10 anni', punti: 10 },
        ],
      },
      {
        id: 'ob-liquidita',
        area: 'obiettivi',
        testo: 'Quanto è probabile che tu debba disinvestire in anticipo?',
        tipo: 'singola',
        opzioni: [
          { id: 'a', testo: 'Molto probabile', punti: 0 },
          { id: 'b', testo: 'Possibile, ma solo per una parte', punti: 5 },
          { id: 'c', testo: 'Improbabile', punti: 10 },
        ],
      },
    ],
  },
  {
    area: 'tolleranza-rischio',
    titolo: 'Tolleranza al rischio',
    descrizione:
      'Qui non ci sono risposte giuste: serve capire come reagisci davvero quando i mercati scendono.',
    domande: [
      {
        id: 'tr-reazione',
        area: 'tolleranza-rischio',
        testo: 'Il tuo portafoglio perde il 20% in tre mesi. Cosa fai?',
        tipo: 'singola',
        opzioni: [
          { id: 'a', testo: 'Vendo tutto: non riesco a dormirci', punti: 0 },
          { id: 'b', testo: 'Vendo una parte per limitare i danni', punti: 3 },
          { id: 'c', testo: 'Non tocco niente e aspetto', punti: 7 },
          { id: 'd', testo: 'Investo altro: i prezzi sono più bassi', punti: 10 },
        ],
      },
      {
        id: 'tr-scenario',
        area: 'tolleranza-rischio',
        testo: 'Quale di questi andamenti a un anno preferiresti per €10.000?',
        aiuto: 'Ogni scenario mostra il risultato in un anno buono e in un anno negativo.',
        tipo: 'singola',
        opzioni: [
          { id: 'a', testo: 'Tra €9.900 e €10.400', punti: 1 },
          { id: 'b', testo: 'Tra €9.400 e €11.000', punti: 4 },
          { id: 'c', testo: 'Tra €8.500 e €12.000', punti: 7 },
          { id: 'd', testo: 'Tra €7.500 e €13.500', punti: 10 },
        ],
      },
      {
        id: 'tr-perdita',
        area: 'tolleranza-rischio',
        testo: 'Qual è la perdita massima che riusciresti a tollerare in un anno?',
        tipo: 'singola',
        opzioni: [
          { id: 'a', testo: 'Nessuna perdita', punti: 0 },
          { id: 'b', testo: 'Fino al 5%', punti: 3 },
          { id: 'c', testo: 'Fino al 15%', punti: 7 },
          { id: 'd', testo: 'Fino al 30% o più', punti: 10 },
        ],
      },
    ],
  },
  {
    area: 'sostenibilita',
    titolo: 'Preferenze di sostenibilità',
    descrizione:
      'Domanda obbligatoria dal 2022. Non influisce sul livello di rischio, ma sulla selezione degli strumenti.',
    domande: [
      {
        id: 'so-interesse',
        area: 'sostenibilita',
        testo: 'Vuoi che il tuo portafoglio integri criteri ambientali, sociali e di governance (ESG)?',
        tipo: 'singola',
        opzioni: [
          { id: 'a', testo: 'No, preferisco non porre vincoli', punti: 0 },
          { id: 'b', testo: 'Sì, ma solo se non peggiora i costi', punti: 6 },
          { id: 'c', testo: 'Sì, è una priorità per me', punti: 10 },
        ],
      },
    ],
  },
];

export const DOMANDE = SEZIONI.flatMap((s) => s.domande);

export const TOTALE_DOMANDE = DOMANDE.length;
