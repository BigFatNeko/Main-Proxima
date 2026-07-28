import { NOME_PROFILO, ORDINE_PROFILI, PACCHETTI, PIANI } from '../data/pacchetti';
import { formattaEuro } from './format';
import type { AzioneBot, EsitoProfilazione, Messaggio, ProfiloId } from '../types';

/**
 * Consulente digitale: motore a regole, deterministico e ispezionabile.
 *
 * Non c'è un modello linguistico dietro. La raccomandazione discende solo
 * dall'esito della profilazione, e ogni frase è tracciabile a una regola —
 * requisito pratico per una SCF, che deve poter ricostruire il perché di ogni
 * proposta fatta al cliente.
 */

let contatore = 0;
function nuovoId(): string {
  contatore += 1;
  return `m${contatore}`;
}

function msgBot(testo: string, allegato?: Messaggio['allegato']): Messaggio {
  return { id: nuovoId(), autore: 'bot', testo, allegato };
}

export function msgUtente(testo: string): Messaggio {
  return { id: nuovoId(), autore: 'utente', testo };
}

/** Profili adiacenti da mostrare accanto al consigliato, per dare contesto. */
function vicinato(profilo: ProfiloId): ProfiloId[] {
  const i = ORDINE_PROFILI.indexOf(profilo);
  const da = Math.max(0, Math.min(i - 1, ORDINE_PROFILI.length - 3));
  return ORDINE_PROFILI.slice(da, da + 3);
}

/**
 * Il profilo più rischioso che il consulente può raccomandare.
 * In presenza di vincoli di adeguatezza non si sale: il tetto è la
 * raccomandazione stessa.
 */
export function tettoRaccomandabile(esito: EsitoProfilazione): ProfiloId {
  if (esito.vincoli.length > 0) return esito.profilo;
  const i = ORDINE_PROFILI.indexOf(esito.profilo);
  return ORDINE_PROFILI[Math.min(i + 1, ORDINE_PROFILI.length - 1)];
}

export function messaggiIniziali(esito: EsitoProfilazione, nome: string): Messaggio[] {
  const pacchetto = PACCHETTI[esito.profilo];
  const messaggi: Messaggio[] = [
    msgBot(
      `Ciao ${nome}, ho letto le tue risposte. Ti mostro come le ho pesate, così puoi contestarmi se qualcosa non ti torna.`,
      { tipo: 'punteggi' },
    ),
  ];

  if (esito.vincoli.length > 0) {
    const elenco = esito.vincoli.map((v) => `• ${v.motivo}`).join('\n');
    messaggi.push(
      msgBot(
        `Il punteggio di rischio delle tue risposte sarebbe ${esito.punteggioGrezzo}/100, ma l’ho abbassato a ${esito.punteggioRischio}/100 per questi motivi:\n\n${elenco}`,
      ),
    );
  } else {
    messaggi.push(
      msgBot(
        `Il tuo punteggio di rischio è ${esito.punteggioRischio}/100 e non ci sono elementi che mi impongano di abbassarlo: situazione finanziaria, orizzonte e tolleranza sono coerenti fra loro.`,
      ),
    );
  }

  messaggi.push(
    msgBot(
      `Il profilo che ne esce è **${NOME_PROFILO[esito.profilo]}**. Il portafoglio che ti propongo è ${pacchetto.nome}: ${pacchetto.claim.toLowerCase()}. Qui sotto trovi anche i due profili vicini, per capire cosa cambia salendo o scendendo di rischio.`,
      { tipo: 'pacchetti', ids: vicinato(esito.profilo), consigliato: esito.profilo },
    ),
  );

  return messaggi;
}

export function azioniDisponibili(esito: EsitoProfilazione, inVista: ProfiloId): AzioneBot[] {
  const azioni: AzioneBot[] = [{ id: 'perche', etichetta: 'Perché proprio questo?' }];

  const i = ORDINE_PROFILI.indexOf(inVista);
  const oltreIlTetto = i >= ORDINE_PROFILI.indexOf(tettoRaccomandabile(esito));
  if (i < ORDINE_PROFILI.length - 1) {
    azioni.push({
      id: 'piu-rischio',
      etichetta: oltreIlTetto ? 'Perché non posso rischiare di più?' : 'E se rischiassi di più?',
    });
  }
  if (i > 0) azioni.push({ id: 'meno-rischio', etichetta: 'Preferirei rischiare meno' });

  azioni.push({ id: 'costi', etichetta: 'Quanto costa il servizio?' });
  azioni.push({ id: 'perdita', etichetta: 'Quanto posso perdere?' });
  azioni.push({ id: 'conferma', etichetta: `Scelgo ${PACCHETTI[inVista].nome}` });

  return azioni;
}

export interface RispostaBot {
  /** Testo da mostrare come messaggio dell'utente per l'azione scelta. */
  eco: string;
  messaggi: Messaggio[];
  /** Pacchetto su cui si sposta la conversazione. */
  inVista: ProfiloId;
  /** Valorizzato solo quando l'utente conferma la scelta. */
  confermato?: ProfiloId;
}

export function elaboraAzione(
  azione: string,
  esito: EsitoProfilazione,
  inVista: ProfiloId,
): RispostaBot {
  const pacchetto = PACCHETTI[inVista];
  const i = ORDINE_PROFILI.indexOf(inVista);
  const tetto = tettoRaccomandabile(esito);

  switch (azione) {
    case 'perche': {
      const p = esito.punteggi;
      const testo =
        esito.vincoli.length > 0
          ? `Perché il punto debole non è la tua voglia di rischiare, ma il contesto: ${esito.vincoli[0].motivo.toLowerCase()} Con tolleranza ${p.tolleranza}/100 e orizzonte ${p.orizzonte}/100, ${PACCHETTI[esito.profilo].nome} è il portafoglio più aggressivo che posso raccomandarti oggi.`
          : `Perché i tre pilastri sono allineati: capacità di assorbire perdite ${p.capacita}/100, orizzonte ${p.orizzonte}/100, tolleranza ${p.tolleranza}/100. Con questi numeri, un portafoglio ${NOME_PROFILO[esito.profilo].toLowerCase()} ti fa correre il rischio che serve all’obiettivo, senza aggiungerne di gratuito.`;
      return {
        eco: 'Perché proprio questo?',
        inVista,
        messaggi: [
          msgBot(testo),
          msgBot(
            `Sulla parte tecnica: ${pacchetto.descrizione} Il costo interno degli strumenti è dello ${pacchetto.terMedio.toFixed(2).replace('.', ',')}% annuo — per confronto, un fondo bancario comparabile viaggia fra l’1,5% e il 2,2%.`,
          ),
        ],
      };
    }

    case 'piu-rischio': {
      const prossimo = ORDINE_PROFILI[Math.min(i + 1, ORDINE_PROFILI.length - 1)];
      const oltreIlTetto = ORDINE_PROFILI.indexOf(prossimo) > ORDINE_PROFILI.indexOf(tetto);

      if (oltreIlTetto) {
        const motivo = esito.vincoli[0]?.motivo;
        return {
          eco: 'Perché non posso rischiare di più?',
          inVista,
          messaggi: [
            msgBot(
              motivo
                ? `Te lo mostro, ma con una premessa netta: ${PACCHETTI[prossimo].nome} non è adeguato al tuo profilo e come consulenti non possiamo raccomandartelo. ${motivo}`
                : `${PACCHETTI[prossimo].nome} sta due gradini sopra il profilo che è uscito dalle tue risposte: il tuo punteggio di rischio è ${esito.punteggioRischio}/100 e con questi numeri non posso raccomandartelo, anche se nessun vincolo specifico te lo impedisce.`,
            ),
            msgBot(
              'Se lo volessi comunque, servirebbe una scelta consapevole firmata da te, e il consulente dovrebbe registrarla come operazione non conforme alla raccomandazione. Prima però ne parliamo in call: la scelta giusta è quasi sempre rimuovere ciò che ti frena, non ignorarlo.',
              { tipo: 'pacchetti', ids: vicinato(inVista), consigliato: esito.profilo },
            ),
          ],
        };
      }

      const p = PACCHETTI[prossimo];
      return {
        eco: 'E se rischiassi di più?',
        inVista: prossimo,
        messaggi: [
          msgBot(
            `Con ${p.nome} il rendimento atteso sale al ${p.rendimentoAtteso.toFixed(1).replace('.', ',')}% annuo, ma la volatilità passa dal ${pacchetto.volatilita.toFixed(1).replace('.', ',')}% al ${p.volatilita.toFixed(1).replace('.', ',')}% e in un anno negativo puoi vedere un ${p.perditaMassima}%. Ha senso solo se non tocchi il capitale per almeno ${p.orizzonteMinimoAnni} anni.`,
            { tipo: 'pacchetti', ids: vicinato(prossimo), consigliato: esito.profilo },
          ),
        ],
      };
    }

    case 'meno-rischio': {
      const precedente = ORDINE_PROFILI[Math.max(i - 1, 0)];
      const p = PACCHETTI[precedente];
      return {
        eco: 'Preferirei rischiare meno',
        inVista: precedente,
        messaggi: [
          msgBot(
            `Scendere si può sempre: ${p.nome} limita la perdita attesa in un anno negativo al ${p.perditaMassima}%, contro il ${pacchetto.perditaMassima}% di ${pacchetto.nome}. Il prezzo è un rendimento atteso del ${p.rendimentoAtteso.toFixed(1).replace('.', ',')}% invece del ${pacchetto.rendimentoAtteso.toFixed(1).replace('.', ',')}%.`,
            { tipo: 'pacchetti', ids: vicinato(precedente), consigliato: esito.profilo },
          ),
          msgBot(
            'Detto onestamente: su orizzonti lunghi scendere troppo di rischio è a sua volta un rischio, perché l’inflazione erode il capitale. Ma se questo ti permette di restare investito nei momenti brutti, è la scelta giusta.',
          ),
        ],
      };
    }

    case 'costi': {
      const piano = PIANI[esito.fasciaPatrimonio];
      return {
        eco: 'Quanto costa il servizio?',
        inVista,
        messaggi: [
          msgBot(
            `Per la tua fascia di patrimonio (${piano.patrimonio.toLowerCase()}) il piano è ${piano.nome}: ${formattaEuro(piano.canoneAnnuo)} all’anno, tutto compreso.`,
            { tipo: 'tariffa' },
          ),
          msgBot(
            'Siamo una SCF fee-only: incassiamo solo da te, non prendiamo retrocessioni da banche o società di gestione. Non custodiamo i tuoi soldi — restano sul tuo conto, le operazioni le fai tu seguendo il piano.',
          ),
        ],
      };
    }

    case 'perdita': {
      const capitale = { 'fino-20k': 15000, '20k-50k': 35000, '50k-100k': 75000, 'oltre-100k': 150000 }[
        esito.fasciaPatrimonio
      ];
      const perdita = Math.round((capitale * Math.abs(pacchetto.perditaMassima)) / 100);
      return {
        eco: 'Quanto posso perdere?',
        inVista,
        messaggi: [
          msgBot(
            `Con ${pacchetto.nome}, su un capitale indicativo di ${formattaEuro(capitale)}, un anno molto negativo vale circa ${formattaEuro(perdita)} di perdita temporanea (${pacchetto.perditaMassima}%). Non è lo scenario peggiore possibile: è quello che devi mettere in conto come normale.`,
          ),
          msgBot(
            `La domanda vera non è se succederà, ma cosa farai quando succede. Storicamente il capitale si recupera restando investiti — è vendere in quel momento che trasforma una discesa in una perdita definitiva.`,
          ),
        ],
      };
    }

    case 'conferma': {
      const adeguato = inVista === esito.profilo;
      return {
        eco: `Scelgo ${pacchetto.nome}`,
        inVista,
        confermato: inVista,
        messaggi: [
          msgBot(
            adeguato
              ? `Perfetto. ${pacchetto.nome} è attivo sul tuo profilo. Da adesso la dashboard confronta l’andamento del tuo portafoglio con il benchmark Proxima ${NOME_PROFILO[inVista]}, che è il portafoglio modello nella sua versione teorica.`
              : `Registrato: hai scelto ${pacchetto.nome}, diverso dal profilo ${NOME_PROFILO[esito.profilo]} che ti avevo raccomandato. Il consulente ne parlerà con te al primo check-up e la scelta va confermata per iscritto.`,
          ),
          msgBot(
            'Prima di operare fisserai una call con il consulente iscritto all’Albo OCF: quello che hai visto qui è una proposta, la raccomandazione formale te la firma una persona.',
          ),
        ],
      };
    }

    default:
      return { eco: '', inVista, messaggi: [] };
  }
}
