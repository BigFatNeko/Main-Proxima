import { useEffect, useRef, useState } from 'react';
import AppShell from '../components/AppShell';
import PacchettoCard from '../components/PacchettoCard';
import PannelloPunteggi from '../components/PannelloPunteggi';
import { NOME_PROFILO, PACCHETTI, PIANI } from '../data/pacchetti';
import { azioniDisponibili, elaboraAzione, messaggiIniziali, msgUtente } from '../lib/bot';
import { formattaEuro } from '../lib/format';
import { useApp } from '../state/AppContext';
import type { Messaggio, ProfiloId } from '../types';
import './ConsulenteScreen.css';

/** Rende **grassetto** dentro al testo dei messaggi. */
function Testo({ contenuto }: { contenuto: string }) {
  const pezzi = contenuto.split(/\*\*(.+?)\*\*/g);
  return (
    <>
      {pezzi.map((pezzo, i) => (i % 2 === 1 ? <strong key={i}>{pezzo}</strong> : pezzo))}
    </>
  );
}

export default function ConsulenteScreen() {
  const { stato, confermaPacchetto, rifaiQuestionario, vaiA } = useApp();
  const esito = stato?.esito ?? null;

  const [messaggi, setMessaggi] = useState<Messaggio[]>(() =>
    esito ? messaggiIniziali(esito, stato!.utente.nome) : [],
  );
  const [inVista, setInVista] = useState<ProfiloId>(esito?.profilo ?? 'equilibrato');
  const [confermato, setConfermato] = useState<ProfiloId | null>(null);
  const fondo = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fondo.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messaggi]);

  if (!esito || !stato) return null;

  const piano = PIANI[esito.fasciaPatrimonio];

  function esegui(azione: string) {
    if (!esito) return;
    const risposta = elaboraAzione(azione, esito, inVista);
    setMessaggi((precedenti) => [...precedenti, msgUtente(risposta.eco), ...risposta.messaggi]);
    setInVista(risposta.inVista);
    if (risposta.confermato) setConfermato(risposta.confermato);
  }

  function allegatoDi(messaggio: Messaggio) {
    if (!messaggio.allegato || !esito) return null;

    if (messaggio.allegato.tipo === 'punteggi') {
      return <PannelloPunteggi punteggi={esito.punteggi} />;
    }

    if (messaggio.allegato.tipo === 'tariffa') {
      return (
        <div className="bot-tariffa">
          <p className="eyebrow">Piano {piano.nome}</p>
          <p className="bot-tariffa-prezzo">
            {formattaEuro(piano.canoneAnnuo)} <span>/ anno</span>
          </p>
          <ul>
            {piano.incluso.map((voce) => (
              <li key={voce}>{voce}</li>
            ))}
          </ul>
        </div>
      );
    }

    const { ids, consigliato } = messaggio.allegato;
    return (
      <div className="bot-pacchetti">
        {ids.map((id) => (
          <PacchettoCard
            key={id}
            id={id}
            consigliato={id === consigliato}
            selezionato={id === inVista && id !== consigliato}
            onScegli={() => setInVista(id)}
          />
        ))}
      </div>
    );
  }

  return (
    <AppShell
      azioni={
        <button className="btn btn-quiet" type="button" onClick={rifaiQuestionario}>
          Rifai il questionario
        </button>
      }
    >
      <div className="bot-intro">
        <p className="eyebrow">Il tuo consulente digitale</p>
        <h1>
          Profilo {NOME_PROFILO[esito.profilo]} · {esito.punteggioRischio}/100
        </h1>
        <p>
          Questo assistente non è un modello linguistico: applica regole scritte, quindi ogni frase
          che leggi è ricostruibile a partire dalle tue risposte. La raccomandazione formale te la
          firma comunque il consulente iscritto all’Albo OCF.
        </p>
      </div>

      <div className="bot-conversazione">
        {messaggi.map((messaggio) => (
          <div
            className={messaggio.autore === 'utente' ? 'bot-turno utente' : 'bot-turno'}
            key={messaggio.id}
          >
            {messaggio.autore === 'bot' && (
              <span className="bot-avatar" aria-hidden="true">
                PX
              </span>
            )}
            <div
              className={
                messaggio.allegato?.tipo === 'pacchetti' ? 'bot-bolla larga' : 'bot-bolla'
              }
            >
              <Testo contenuto={messaggio.testo} />
              {messaggio.allegato && <div className="bot-allegato">{allegatoDi(messaggio)}</div>}
            </div>
          </div>
        ))}
        <div ref={fondo} />
      </div>

      <div className="bot-azioni">
        {confermato ? (
          <>
            <p className="bot-azioni-titolo">Scelta registrata</p>
            <div className="bot-chip-riga">
              <button
                className="bot-chip principale"
                type="button"
                onClick={() => confermaPacchetto(confermato)}
              >
                Vai alla mia dashboard →
              </button>
              <button className="bot-chip" type="button" onClick={() => setConfermato(null)}>
                Aspetta, voglio riconsiderare
              </button>
            </div>
          </>
        ) : (
          <>
            <p className="bot-azioni-titolo">
              Stai guardando {PACCHETTI[inVista].nome} — cosa vuoi sapere?
            </p>
            <div className="bot-chip-riga">
              {azioniDisponibili(esito, inVista).map((azione) => (
                <button
                  key={azione.id}
                  className={azione.id === 'conferma' ? 'bot-chip principale' : 'bot-chip'}
                  type="button"
                  onClick={() => esegui(azione.id)}
                >
                  {azione.etichetta}
                </button>
              ))}
            </div>
          </>
        )}

        <p className="bot-nota">
          Le risposte sono generate da regole deterministiche sui tuoi punteggi. Il dialogo libero
          con il consulente umano avviene in videochiamata, dove la proposta viene validata o
          corretta.{' '}
          {stato.pacchettoScelto && (
            <button
              className="bot-chip"
              type="button"
              style={{ padding: '0.2rem 0.7rem', fontSize: '0.78rem' }}
              onClick={() => vaiA('dashboard')}
            >
              Torna alla dashboard
            </button>
          )}
        </p>
      </div>
    </AppShell>
  );
}
