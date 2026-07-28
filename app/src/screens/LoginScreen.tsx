import { useState } from 'react';
import type { FormEvent } from 'react';
import Logo from '../components/Logo';
import { useApp } from '../state/AppContext';
import { esisteUtente } from '../state/storage';
import './LoginScreen.css';

const PUNTI = [
  'Consulenza indipendente a parcella: nessuna provvigione dai prodotti che ti consigliamo.',
  'I tuoi soldi restano sul tuo conto. Noi diciamo cosa fare, non mettiamo le mani sul capitale.',
  'Pensata per chi ha meno di €100.000 da investire, cioè per chi le banche seguono peggio.',
];

function Spunta() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" strokeWidth="2.5" strokeLinecap="round" aria-hidden="true">
      <path d="M20 6L9 17l-5-5" />
    </svg>
  );
}

export default function LoginScreen() {
  const { accediConEmail } = useApp();
  const [modo, setModo] = useState<'accedi' | 'registrati'>('accedi');
  const [nome, setNome] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errore, setErrore] = useState<string | null>(null);

  const registrazione = modo === 'registrati';

  function invia(e: FormEvent) {
    e.preventDefault();

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email.trim())) {
      setErrore('Inserisci un indirizzo email valido.');
      return;
    }
    if (password.length < 8) {
      setErrore('La password deve avere almeno 8 caratteri.');
      return;
    }
    if (registrazione && esisteUtente(email)) {
      setErrore('Esiste già un account con questa email. Passa ad Accedi.');
      return;
    }
    if (!registrazione && !esisteUtente(email)) {
      setErrore('Non troviamo un account con questa email. Creane uno in mezzo minuto.');
      return;
    }

    setErrore(null);
    accediConEmail(email, password, registrazione ? nome : undefined);
  }

  return (
    <main className="login">
      <section className="login-brand">
        <div className="login-brand-glow" aria-hidden="true" />
        <div className="login-brand-line" aria-hidden="true" />

        <div className="login-brand-logo">
          <Logo />
        </div>

        <div>
          <p className="eyebrow">Area clienti</p>
          <p className="login-claim">
            Il tuo patrimonio, <strong>senza conflitti di interesse</strong>.
          </p>
          <ul className="login-punti">
            {PUNTI.map((punto) => (
              <li key={punto}>
                <Spunta />
                <span>{punto}</span>
              </li>
            ))}
          </ul>
        </div>

        <p className="login-nota-albo">
          Proxima SCF S.r.l. — Società di Consulenza Finanziaria iscritta all’Albo OCF, Sezione III
          (art. 18-bis TUF). Prototipo dimostrativo: i dati inseriti restano su questo dispositivo.
        </p>
      </section>

      <section className="login-form-lato">
        <form className="login-form" onSubmit={invia} noValidate>
          <p className="eyebrow">{registrazione ? 'Nuovo account' : 'Bentornato'}</p>
          <h2>{registrazione ? 'Crea il tuo accesso' : 'Accedi al tuo profilo'}</h2>
          <p className="muted" style={{ marginBottom: '1.75rem' }}>
            {registrazione
              ? 'Bastano tre minuti: apri l’account e passi subito al questionario.'
              : 'Se hai già completato il questionario entri direttamente nella tua dashboard.'}
          </p>

          {errore && (
            <p className="login-errore" role="alert">
              {errore}
            </p>
          )}

          {registrazione && (
            <div className="login-campo">
              <label className="field-label" htmlFor="nome">
                Nome
              </label>
              <input
                id="nome"
                className="input"
                type="text"
                autoComplete="given-name"
                value={nome}
                onChange={(e) => setNome(e.target.value)}
                placeholder="Come vuoi essere chiamato"
              />
            </div>
          )}

          <div className="login-campo">
            <label className="field-label" htmlFor="email">
              Email
            </label>
            <input
              id="email"
              className="input"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="nome@esempio.it"
              required
            />
          </div>

          <div className="login-campo">
            <label className="field-label" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              className="input"
              type="password"
              autoComplete={registrazione ? 'new-password' : 'current-password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Almeno 8 caratteri"
              required
            />
          </div>

          <button className="btn btn-primary" type="submit">
            {registrazione ? 'Crea account' : 'Accedi'}
          </button>

          <p className="login-switch">
            {registrazione ? 'Hai già un account?' : 'Prima volta su Proxima?'}{' '}
            <button
              type="button"
              onClick={() => {
                setModo(registrazione ? 'accedi' : 'registrati');
                setErrore(null);
              }}
            >
              {registrazione ? 'Accedi' : 'Crea un account'}
            </button>
          </p>

          <p className="login-demo">
            <strong>Prototipo.</strong> L’autenticazione è simulata: nessuna password viene salvata e
            i dati restano nel localStorage del browser. Va sostituita con l’autenticazione reale
            prima di qualunque uso con clienti.
          </p>
        </form>
      </section>
    </main>
  );
}
