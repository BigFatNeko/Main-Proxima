import type { ReactNode } from 'react';
import Logo from './Logo';
import { useApp } from '../state/AppContext';
import './AppShell.css';

interface Props {
  children: ReactNode;
  /** Contenuto opzionale a destra nella barra, prima del pulsante di uscita. */
  azioni?: ReactNode;
  stretta?: boolean;
}

export default function AppShell({ children, azioni, stretta = false }: Props) {
  const { stato, esci } = useApp();

  return (
    <div className="shell">
      <header className="shell-top">
        <Logo dimensione={30} />

        <div className="shell-utente">
          {azioni}
          {stato && (
            <p className="shell-nome">
              {stato.utente.nome}
              <span>{stato.utente.email}</span>
            </p>
          )}
          <button className="btn btn-quiet" type="button" onClick={esci}>
            Esci
          </button>
        </div>
      </header>

      <main className={stretta ? 'shell-main stretta' : 'shell-main'}>{children}</main>

      <footer className="shell-piede">
        Proxima SCF S.r.l. · Albo OCF Sezione III · Prototipo dimostrativo con dati simulati — non
        costituisce raccomandazione di investimento.
      </footer>
    </div>
  );
}
