import { useEffect, useMemo, useState } from 'react';
import { formattaMeseCorto } from '../lib/format';
import type { PuntoSerie } from '../data/performance';
import './GraficoPerformance.css';

/**
 * Confronto fra il portafoglio del cliente e il benchmark Proxima del suo
 * profilo. Due serie, un solo asse: entrambe sono numeri indice con base 100
 * alla sottoscrizione, quindi la scala è comune per costruzione.
 */

const L = 46; // margine sinistro (asse valori)
const R = 104; // margine destro (etichette di serie a fine linea)
const T = 20;
const B = 34;
const W = 780;
const H = 320;

interface Props {
  punti: PuntoSerie[];
  /** Nome del profilo, usato nell'etichetta del benchmark. */
  profilo: string;
}

function tickPuliti(min: number, max: number): number[] {
  const spanGrezzo = Math.max(max - min, 4);
  const passoIdeale = spanGrezzo / 4;
  const passo = [1, 2, 5, 10, 20, 25, 50].find((p) => p >= passoIdeale) ?? 100;
  const primo = Math.floor(min / passo) * passo;
  const ultimo = Math.ceil(max / passo) * passo;
  const tick: number[] = [];
  for (let v = primo; v <= ultimo + 0.001; v += passo) tick.push(Math.round(v * 100) / 100);
  return tick;
}

/** Sotto questa soglia il grafico occupa poca larghezza reale: serve diradare le etichette. */
function useSchermoStretto(): boolean {
  const [stretto, setStretto] = useState(
    () => typeof window !== 'undefined' && window.matchMedia('(max-width: 700px)').matches,
  );

  useEffect(() => {
    const query = window.matchMedia('(max-width: 700px)');
    const aggiorna = (e: MediaQueryListEvent) => setStretto(e.matches);
    query.addEventListener('change', aggiorna);
    return () => query.removeEventListener('change', aggiorna);
  }, []);

  return stretto;
}

export default function GraficoPerformance({ punti, profilo }: Props) {
  const [attivo, setAttivo] = useState<number | null>(null);
  const [tabella, setTabella] = useState(false);
  const stretto = useSchermoStretto();
  const passoEtichette = stretto ? 6 : 3;

  const { tick, x, y, dPortafoglio, dBenchmark } = useMemo(() => {
    const valori = punti.flatMap((p) => [p.portafoglio, p.benchmark]);
    const tickCalcolati = tickPuliti(Math.min(...valori), Math.max(...valori));
    const minY = tickCalcolati[0];
    const maxY = tickCalcolati[tickCalcolati.length - 1];

    const fx = (i: number) => L + (i / Math.max(punti.length - 1, 1)) * (W - L - R);
    const fy = (v: number) => T + (1 - (v - minY) / (maxY - minY)) * (H - T - B);

    const linea = (chiave: 'portafoglio' | 'benchmark') =>
      punti.map((p, i) => `${i === 0 ? 'M' : 'L'} ${fx(i).toFixed(1)} ${fy(p[chiave]).toFixed(1)}`).join(' ');

    return {
      tick: tickCalcolati,
      x: fx,
      y: fy,
      dPortafoglio: linea('portafoglio'),
      dBenchmark: linea('benchmark'),
    };
  }, [punti]);

  const ultimo = punti[punti.length - 1];
  const iUltimo = punti.length - 1;

  /* Le due etichette di fine linea si sovrappongono quando le serie chiudono
     vicine: le allontano fino all'altezza minima di riga, senza muovere i
     marcatori, che restano ancorati al dato. */
  const altezzaRiga = stretto ? 26 : 15;
  const yEtichette = (() => {
    const p = y(ultimo.portafoglio);
    const b = y(ultimo.benchmark);
    const distanza = Math.abs(p - b);
    if (distanza >= altezzaRiga) return { portafoglio: p, benchmark: b };
    const spinta = (altezzaRiga - distanza) / 2;
    return p <= b
      ? { portafoglio: p - spinta, benchmark: b + spinta }
      : { portafoglio: p + spinta, benchmark: b - spinta };
  })();

  /* L'indice sotto al cursore: la fascia orizzontale più vicina. */
  function muovi(e: React.MouseEvent<SVGRectElement>) {
    const rect = e.currentTarget.getBoundingClientRect();
    const rapporto = (e.clientX - rect.left) / rect.width;
    const i = Math.round(rapporto * (punti.length - 1));
    setAttivo(Math.min(Math.max(i, 0), punti.length - 1));
  }

  const puntoAttivo = attivo !== null ? punti[attivo] : null;

  return (
    <div className="gp">
      <div className="gp-testata">
        <div>
          <p className="gp-titolo">Il tuo portafoglio e il benchmark Proxima</p>
          <p className="gp-sottotitolo">
            Numeri indice con base 100 alla sottoscrizione. Il benchmark è il portafoglio modello{' '}
            {profilo} nella sua versione teorica, senza costi di esecuzione né ritardi nei
            versamenti.
          </p>
        </div>
        <div className="gp-legenda">
          <span>
            <i className="gp-chiave" style={{ background: 'var(--serie-portafoglio)' }} />
            Il tuo portafoglio
          </span>
          <span>
            <i className="gp-chiave" style={{ background: 'var(--serie-benchmark)' }} />
            Benchmark Proxima
          </span>
        </div>
      </div>

      <div className="gp-tela">
        <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Andamento del portafoglio confrontato con il benchmark Proxima">
          {tick.map((valore) => (
            <g key={valore}>
              <line
                x1={L}
                x2={W - R}
                y1={y(valore)}
                y2={y(valore)}
                stroke="var(--grid)"
                strokeWidth="1"
              />
              <text className="gp-asse" x={L - 10} y={y(valore) + 4} textAnchor="end">
                {valore}
              </text>
            </g>
          ))}

          {punti.map((p, i) =>
            i % passoEtichette === 0 || i === iUltimo ? (
              <text key={p.data} className="gp-asse" x={x(i)} y={H - B + 20} textAnchor="middle">
                {formattaMeseCorto(p.data)}
              </text>
            ) : null,
          )}

          {puntoAttivo && attivo !== null && (
            <line
              x1={x(attivo)}
              x2={x(attivo)}
              y1={T}
              y2={H - B}
              stroke="var(--border-strong)"
              strokeWidth="1"
            />
          )}

          <path d={dBenchmark} fill="none" stroke="var(--serie-benchmark)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          <path d={dPortafoglio} fill="none" stroke="var(--serie-portafoglio)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />

          {puntoAttivo && attivo !== null && (
            <>
              <circle cx={x(attivo)} cy={y(puntoAttivo.benchmark)} r="5" fill="var(--serie-benchmark)" stroke="var(--surface-card)" strokeWidth="2" />
              <circle cx={x(attivo)} cy={y(puntoAttivo.portafoglio)} r="5" fill="var(--serie-portafoglio)" stroke="var(--surface-card)" strokeWidth="2" />
            </>
          )}

          {/* Marcatori ed etichette di fine linea: identità senza colorare il testo. */}
          <circle cx={x(iUltimo)} cy={y(ultimo.benchmark)} r="4.5" fill="var(--serie-benchmark)" stroke="var(--surface-card)" strokeWidth="2" />
          <circle cx={x(iUltimo)} cy={y(ultimo.portafoglio)} r="4.5" fill="var(--serie-portafoglio)" stroke="var(--surface-card)" strokeWidth="2" />

          <text className="gp-etichetta-serie" x={x(iUltimo) + 12} y={yEtichette.portafoglio + 4}>
            {ultimo.portafoglio.toFixed(1).replace('.', ',')}
          </text>
          <text className="gp-etichetta-serie" x={x(iUltimo) + 12} y={yEtichette.benchmark + 4}>
            {ultimo.benchmark.toFixed(1).replace('.', ',')}
          </text>

          <rect
            x={L}
            y={T}
            width={W - L - R}
            height={H - T - B}
            fill="transparent"
            onMouseMove={muovi}
            onMouseLeave={() => setAttivo(null)}
          />
        </svg>

        {puntoAttivo && attivo !== null && (
          <div
            className="gp-tooltip"
            style={{
              left: `${(x(attivo) / W) * 100}%`,
              top: `${(Math.min(y(puntoAttivo.portafoglio), y(puntoAttivo.benchmark)) / H) * 100}%`,
            }}
          >
            <p className="gp-tooltip-data">{formattaMeseCorto(puntoAttivo.data)}</p>
            <p className="gp-tooltip-riga">
              <i className="gp-chiave" style={{ background: 'var(--serie-portafoglio)' }} />
              Tuo portafoglio <b>{puntoAttivo.portafoglio.toFixed(1).replace('.', ',')}</b>
            </p>
            <p className="gp-tooltip-riga">
              <i className="gp-chiave" style={{ background: 'var(--serie-benchmark)' }} />
              Benchmark <b>{puntoAttivo.benchmark.toFixed(1).replace('.', ',')}</b>
            </p>
          </div>
        )}
      </div>

      <div className="gp-azioni">
        <button className="btn btn-quiet" type="button" onClick={() => setTabella((v) => !v)}>
          {tabella ? 'Nascondi i dati' : 'Mostra i dati in tabella'}
        </button>
      </div>

      {tabella && (
        <div className="gp-tabella">
          <table>
            <caption className="visually-hidden">
              Valori mensili del portafoglio e del benchmark, base 100
            </caption>
            <thead>
              <tr>
                <th scope="col">Mese</th>
                <th scope="col">Tuo portafoglio</th>
                <th scope="col">Benchmark Proxima</th>
                <th scope="col">Scarto</th>
              </tr>
            </thead>
            <tbody>
              {[...punti].reverse().map((p) => (
                <tr key={p.data}>
                  <td>{formattaMeseCorto(p.data)}</td>
                  <td>{p.portafoglio.toFixed(1).replace('.', ',')}</td>
                  <td>{p.benchmark.toFixed(1).replace('.', ',')}</td>
                  <td>
                    {(p.portafoglio - p.benchmark > 0 ? '+' : '') +
                      (p.portafoglio - p.benchmark).toFixed(1).replace('.', ',')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
