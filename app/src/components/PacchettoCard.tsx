import { NOME_PROFILO, PACCHETTI } from '../data/pacchetti';
import type { ProfiloId } from '../types';
import './PacchettoCard.css';

/** Quota azionaria del pacchetto: è la leva che determina il rischio percepito. */
export function quotaAzionaria(id: ProfiloId): number {
  return PACCHETTI[id].allocazione
    .filter((a) => a.tipo === 'azionario')
    .reduce((tot, a) => tot + a.peso, 0);
}

interface Props {
  id: ProfiloId;
  consigliato?: boolean;
  selezionato?: boolean;
  onScegli?: (id: ProfiloId) => void;
}

export default function PacchettoCard({ id, consigliato, selezionato, onScegli }: Props) {
  const pacchetto = PACCHETTI[id];
  const azionario = quotaAzionaria(id);
  const difensivo = 100 - azionario;

  const classi = ['pk', consigliato ? 'consigliato' : '', selezionato ? 'selezionato' : '']
    .filter(Boolean)
    .join(' ');

  const Elemento = onScegli ? 'button' : 'div';

  return (
    <Elemento
      className={classi}
      {...(onScegli ? { type: 'button' as const, onClick: () => onScegli(id) } : {})}
    >
      <div className="pk-testata">
        <div>
          <p className="pk-profilo">{NOME_PROFILO[id]}</p>
          <p className="pk-nome">{pacchetto.nome}</p>
        </div>
        {consigliato && <span className="badge">Consigliato</span>}
      </div>

      <p className="pk-claim">{pacchetto.claim}</p>

      <div>
        <div className="pk-barra" role="img" aria-label={`${azionario}% azionario, ${difensivo}% difensivo`}>
          <span style={{ width: `${azionario}%`, background: 'var(--alloc-azionario)' }} />
          <span style={{ width: `${difensivo}%`, background: 'var(--alloc-difensivo)' }} />
        </div>
        <div className="pk-legenda" style={{ marginTop: '0.5rem' }}>
          <span>
            <i className="pk-chiave" style={{ background: 'var(--alloc-azionario)' }} />
            Azionario {azionario}%
          </span>
          <span>
            <i className="pk-chiave" style={{ background: 'var(--alloc-difensivo)' }} />
            Difensivo {difensivo}%
          </span>
        </div>
      </div>

      <div className="pk-numeri">
        <div>
          <p className="pk-numero-etichetta">Rendimento atteso</p>
          <p className="pk-numero-valore">
            {pacchetto.rendimentoAtteso.toFixed(1).replace('.', ',')}%
          </p>
        </div>
        <div>
          <p className="pk-numero-etichetta">Anno negativo</p>
          <p className="pk-numero-valore negativo">{pacchetto.perditaMassima}%</p>
        </div>
        <div>
          <p className="pk-numero-etichetta">Volatilità</p>
          <p className="pk-numero-valore">{pacchetto.volatilita.toFixed(1).replace('.', ',')}%</p>
        </div>
        <div>
          <p className="pk-numero-etichetta">Orizzonte minimo</p>
          <p className="pk-numero-valore">{pacchetto.orizzonteMinimoAnni} anni</p>
        </div>
      </div>
    </Elemento>
  );
}
