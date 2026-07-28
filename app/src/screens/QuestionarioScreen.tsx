import { useMemo, useState } from 'react';
import AppShell from '../components/AppShell';
import { SEZIONI, TOTALE_DOMANDE } from '../data/questionario';
import { sezioneCompleta } from '../lib/profilo';
import { useApp } from '../state/AppContext';
import type { Domanda, Risposte } from '../types';
import './QuestionarioScreen.css';

function OpzioniDomanda({
  domanda,
  risposte,
  onCambia,
}: {
  domanda: Domanda;
  risposte: Risposte;
  onCambia: (valore: string | string[]) => void;
}) {
  const multipla = domanda.tipo === 'multipla';
  const valore = risposte[domanda.id];
  const scelte = multipla ? ((valore as string[] | undefined) ?? []) : [];

  function commuta(idOpzione: string) {
    if (!multipla) {
      onCambia(idOpzione);
      return;
    }
    onCambia(
      scelte.includes(idOpzione) ? scelte.filter((s) => s !== idOpzione) : [...scelte, idOpzione],
    );
  }

  return (
    <fieldset className="q-opzioni">
      <legend className="visually-hidden">{domanda.testo}</legend>
      {domanda.opzioni.map((opzione) => {
        const attiva = multipla ? scelte.includes(opzione.id) : valore === opzione.id;
        return (
          <label key={opzione.id} className={attiva ? 'q-opzione scelta' : 'q-opzione'}>
            <input
              type={multipla ? 'checkbox' : 'radio'}
              name={domanda.id}
              value={opzione.id}
              checked={attiva}
              onChange={() => commuta(opzione.id)}
            />
            <span className="q-opzione-testo">{opzione.testo}</span>
            {opzione.nota && <span className="q-opzione-nota">{opzione.nota}</span>}
          </label>
        );
      })}
    </fieldset>
  );
}

export default function QuestionarioScreen() {
  const { stato, salvaQuestionario } = useApp();
  const [indice, setIndice] = useState(0);
  const [risposte, setRisposte] = useState<Risposte>(() => stato?.risposte ?? {});

  const sezione = SEZIONI[indice];
  const ultima = indice === SEZIONI.length - 1;
  const completa = sezioneCompleta(indice, risposte);

  const risposteDate = useMemo(
    () =>
      Object.entries(risposte).filter(([, v]) => (Array.isArray(v) ? true : Boolean(v))).length,
    [risposte],
  );

  function aggiorna(idDomanda: string, valore: string | string[]) {
    setRisposte((precedenti) => ({ ...precedenti, [idDomanda]: valore }));
  }

  function avanti() {
    if (ultima) {
      salvaQuestionario(risposte);
      return;
    }
    setIndice((i) => i + 1);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function indietro() {
    setIndice((i) => Math.max(0, i - 1));
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  return (
    <AppShell stretta>
      <div className="q-intro">
        <p className="eyebrow">Questionario di adeguatezza</p>
        <h1>Prima di consigliarti qualcosa, dobbiamo conoscerti</h1>
        <p>
          Sono {TOTALE_DOMANDE} domande, circa cinque minuti. Le richiede la normativa MiFID II, ma
          servono soprattutto a noi: senza queste risposte qualunque consiglio sarebbe un tiro a
          indovinare. Rispondi con i numeri veri, non con quelli che vorresti.
        </p>
      </div>

      <div className="q-avanzamento">
        <div className="q-tappe" role="presentation">
          {SEZIONI.map((s, i) => (
            <span
              key={s.area}
              className={`q-tappa ${i < indice ? 'fatta' : ''} ${i === indice ? 'corrente' : ''}`}
            />
          ))}
        </div>
        <div className="q-tappe-testo">
          <span>
            Sezione {indice + 1} di {SEZIONI.length}
          </span>
          <span>
            {risposteDate} risposte su {TOTALE_DOMANDE}
          </span>
        </div>
      </div>

      <section className="card" aria-live="polite">
        <div className="q-sezione-testata">
          <p className="eyebrow">{sezione.titolo}</p>
          <h2>{sezione.descrizione}</h2>
        </div>

        {sezione.domande.map((domanda) => (
          <div className="q-domanda" key={domanda.id}>
            <p className="q-domanda-testo">{domanda.testo}</p>
            {domanda.aiuto && <p className="q-domanda-aiuto">{domanda.aiuto}</p>}
            <OpzioniDomanda
              domanda={domanda}
              risposte={risposte}
              onCambia={(valore) => aggiorna(domanda.id, valore)}
            />
          </div>
        ))}
      </section>

      <div className="q-nav">
        {indice > 0 ? (
          <button className="btn btn-quiet" type="button" onClick={indietro}>
            ← Sezione precedente
          </button>
        ) : (
          <span className="q-nav-nota">Le risposte restano modificabili fino alla fine.</span>
        )}

        <button className="btn btn-primary" type="button" onClick={avanti} disabled={!completa}>
          {ultima ? 'Vedi il tuo profilo' : 'Continua'}
        </button>
      </div>
    </AppShell>
  );
}
