import { useMemo } from 'react';
import AppShell from '../components/AppShell';
import GraficoPerformance from '../components/GraficoPerformance';
import { quotaAzionaria } from '../components/PacchettoCard';
import { calcolaPerformance } from '../data/performance';
import { NOME_PROFILO, PACCHETTI, PIANI } from '../data/pacchetti';
import { formattaData, formattaEuro, formattaPercentuale, formattaPunti } from '../lib/format';
import { useApp } from '../state/AppContext';
import './DashboardScreen.css';

export default function DashboardScreen() {
  const { stato, vaiA, rifaiQuestionario } = useApp();

  const scelto = stato?.pacchettoScelto ?? null;
  const esito = stato?.esito ?? null;

  const performance = useMemo(
    () => (scelto && esito ? calcolaPerformance(scelto, esito.fasciaPatrimonio) : null),
    [scelto, esito],
  );

  if (!stato || !esito || !scelto || !performance) return null;

  const pacchetto = PACCHETTI[scelto];
  const piano = PIANI[esito.fasciaPatrimonio];
  const azionario = quotaAzionaria(scelto);
  const sopraBenchmark = performance.scarto >= 0;
  const primoAccesso = stato.accessi <= 1;

  return (
    <AppShell>
      <div className="db-testata">
        <div>
          <p className="eyebrow">{primoAccesso ? 'La tua dashboard' : 'Bentornato'}</p>
          <h1>Ciao {stato.utente.nome}</h1>
          <p className="muted">
            Profilo {NOME_PROFILO[esito.profilo]} · piano {piano.nome} ·{' '}
            {formattaEuro(piano.canoneAnnuo)}/anno. Qui vedi come si sta comportando il tuo
            portafoglio rispetto al modello che abbiamo costruito insieme.
          </p>
        </div>
        <div className="db-pacchetto">
          <span className="badge">{pacchetto.nome}</span>
          {stato.sottoscrittoIl && (
            <p className="db-pacchetto-data" style={{ marginTop: '0.5rem' }}>
              Attivo dal {formattaData(stato.sottoscrittoIl)}
            </p>
          )}
        </div>
      </div>

      {scelto !== esito.profilo && (
        <p className="db-scostamento" role="note">
          Hai scelto <strong>{pacchetto.nome}</strong>, che non coincide con il profilo{' '}
          {NOME_PROFILO[esito.profilo]} emerso dal questionario. Il consulente ne parlerà con te al
          primo check-up: la scelta resta tua, ma va confermata per iscritto.
        </p>
      )}

      <section className="db-kpi" aria-label="Sintesi del portafoglio">
        <div className="db-tile">
          <p className="db-tile-etichetta">Valore attuale</p>
          <p className="db-tile-valore">{formattaEuro(performance.valoreAttuale)}</p>
          <p className="db-tile-nota">
            Capitale iniziale {formattaEuro(performance.capitaleIniziale)}
          </p>
        </div>

        <div className="db-tile">
          <p className="db-tile-etichetta">Rendimento del periodo</p>
          <p
            className={`db-tile-valore ${performance.rendimentoPortafoglio >= 0 ? 'positivo' : 'negativo'}`}
          >
            {formattaPercentuale(performance.rendimentoPortafoglio)}
          </p>
          <p className="db-tile-nota">Ultimi {performance.mesi} mesi, al netto dei costi</p>
        </div>

        <div className="db-tile">
          <p className="db-tile-etichetta">Contro il benchmark</p>
          <p className={`db-tile-valore ${sopraBenchmark ? 'positivo' : 'negativo'}`}>
            {formattaPunti(performance.scarto)}
          </p>
          <p className="db-tile-nota">
            Benchmark {formattaPercentuale(performance.rendimentoBenchmark)}
          </p>
        </div>

        <div className="db-tile">
          <p className="db-tile-etichetta">Costi evitati</p>
          <p className="db-tile-valore">{formattaEuro(performance.costiEvitati)}</p>
          <p className="db-tile-nota">
            Rispetto a un prodotto bancario medio (1,85% annuo) sullo stesso capitale
          </p>
        </div>
      </section>

      <section className="card">
        <GraficoPerformance punti={performance.punti} profilo={NOME_PROFILO[esito.profilo]} />
      </section>

      <div className="db-griglia">
        <section className="card">
          <p className="eyebrow">Composizione</p>
          <h3 style={{ marginTop: '0.4rem' }}>
            {pacchetto.nome} · {azionario}% azionario
          </h3>
          <p className="muted" style={{ fontSize: '0.88rem', marginTop: '0.4rem' }}>
            {pacchetto.descrizione}
          </p>

          <div className="db-allocazione">
            {pacchetto.allocazione.map((classe) => {
              const difensivo = classe.tipo === 'difensivo';
              return (
                <div className="db-classe" key={classe.nome}>
                  <span>{classe.nome}</span>
                  <span className="db-classe-peso">{classe.peso}%</span>
                  <span className="db-classe-traccia">
                    <span
                      style={{
                        width: `${classe.peso}%`,
                        background: difensivo
                          ? 'var(--alloc-difensivo)'
                          : 'var(--alloc-azionario)',
                      }}
                    />
                  </span>
                </div>
              );
            })}
          </div>

          <p className="db-tile-nota" style={{ marginTop: '1.25rem' }}>
            Costo medio degli strumenti {pacchetto.terMedio.toFixed(2).replace('.', ',')}% annuo.
            Nessuna retrocessione: Proxima incassa solo il canone del piano {piano.nome}.
          </p>
        </section>

        <section className="card db-prossimo">
          <p className="eyebrow">Prossimo passo</p>
          <h3 style={{ marginTop: '0.4rem' }}>Il check-up con il consulente</h3>
          <ul className="db-elenco" style={{ color: 'rgba(245,243,238,0.8)' }}>
            <li>Validiamo insieme la proposta generata dal questionario.</li>
            <li>Analizziamo i prodotti che hai già e quanto ti stanno costando davvero.</li>
            <li>Definiamo il piano dei versamenti e le regole di ribilanciamento.</li>
          </ul>
          <button className="btn btn-ghost" type="button">
            Prenota il check-up
          </button>
        </section>
      </div>

      <div className="db-azioni-fondo">
        <button className="btn btn-ghost" type="button" onClick={() => vaiA('consulente')}>
          Rivedi i pacchetti
        </button>
        <button className="btn btn-quiet" type="button" onClick={rifaiQuestionario}>
          La mia situazione è cambiata: rifai il questionario
        </button>
      </div>

      <p className="db-avviso">
        <strong>Dati dimostrativi.</strong> Le performance mostrate sono simulate a partire dal
        profilo e servono a validare l’interfaccia: non rappresentano un portafoglio reale né una
        previsione di rendimento. I rendimenti passati non sono indicativi di quelli futuri.
      </p>
    </AppShell>
  );
}
