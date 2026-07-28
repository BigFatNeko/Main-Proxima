import type { PunteggiAree } from '../types';
import './PannelloPunteggi.css';

const ETICHETTE: Array<{ chiave: keyof PunteggiAree; nome: string; spiegazione: string }> = [
  {
    chiave: 'capacita',
    nome: 'Capacità di rischio',
    spiegazione: 'Quanta perdita puoi assorbire senza conseguenze sulla tua vita',
  },
  {
    chiave: 'conoscenza',
    nome: 'Conoscenza ed esperienza',
    spiegazione: 'Quanto conosci gli strumenti e quanto hai già operato',
  },
  {
    chiave: 'orizzonte',
    nome: 'Orizzonte e obiettivi',
    spiegazione: 'Quanto tempo hai davanti prima di usare il capitale',
  },
  {
    chiave: 'tolleranza',
    nome: 'Tolleranza al rischio',
    spiegazione: 'Quanto ti pesa emotivamente vedere il portafoglio in rosso',
  },
];

export default function PannelloPunteggi({ punteggi }: { punteggi: PunteggiAree }) {
  return (
    <div className="pp">
      {ETICHETTE.map(({ chiave, nome, spiegazione }) => {
        const valore = punteggi[chiave];
        return (
          <div className="pp-riga" key={chiave}>
            <div className="pp-testa">
              <span className="pp-nome">{nome}</span>
              <span className="pp-valore">{valore}/100</span>
            </div>
            <div
              className="pp-traccia"
              role="img"
              aria-label={`${nome}: ${valore} su 100`}
            >
              <span className="pp-riempimento" style={{ width: `${valore}%` }} />
            </div>
            <p className="pp-spiegazione">{spiegazione}</p>
          </div>
        );
      })}
    </div>
  );
}
