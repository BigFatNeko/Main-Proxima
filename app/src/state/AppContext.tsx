import { createContext, useCallback, useContext, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { profila } from '../lib/profilo';
import * as storage from './storage';
import type { ProfiloId, Risposte, SchermataId, StatoUtente } from '../types';

interface ContestoApp {
  stato: StatoUtente | null;
  schermata: SchermataId;
  accediConEmail: (email: string, password: string, nome?: string) => void;
  esci: () => void;
  salvaQuestionario: (risposte: Risposte) => void;
  confermaPacchetto: (pacchetto: ProfiloId) => void;
  rifaiQuestionario: () => void;
  vaiA: (schermata: SchermataId | null) => void;
}

const Contesto = createContext<ContestoApp | null>(null);

/** Schermata di destinazione dato lo stato dell'utente. */
function schermataNaturale(stato: StatoUtente | null): SchermataId {
  if (!stato) return 'login';
  if (!stato.esito) return 'questionario';
  if (!stato.pacchettoScelto) return 'consulente';
  return 'dashboard';
}

export function AppProvider({ children }: { children: ReactNode }) {
  const [stato, setStato] = useState<StatoUtente | null>(() => storage.sessioneAttiva());
  const [forzata, setForzata] = useState<SchermataId | null>(null);

  const aggiorna = useCallback((prossimo: StatoUtente) => {
    storage.salvaUtente(prossimo);
    setStato(prossimo);
  }, []);

  const accediConEmail = useCallback(
    (email: string, _password: string, nome?: string) => {
      const esistente = storage.caricaUtente(email);
      const prossimo: StatoUtente = esistente
        ? { ...esistente, accessi: esistente.accessi + 1 }
        : {
            utente: {
              email: storage.normalizzaEmail(email),
              nome: nome?.trim() || storage.nomeDaEmail(email),
            },
            accessi: 1,
            risposte: null,
            esito: null,
            pacchettoScelto: null,
            sottoscrittoIl: null,
          };

      storage.apriSessione(prossimo.utente.email);
      setForzata(null);
      aggiorna(prossimo);
    },
    [aggiorna],
  );

  const esci = useCallback(() => {
    storage.chiudiSessione();
    setForzata(null);
    setStato(null);
  }, []);

  const salvaQuestionario = useCallback(
    (risposte: Risposte) => {
      if (!stato) return;
      setForzata(null);
      aggiorna({ ...stato, risposte, esito: profila(risposte), pacchettoScelto: null });
    },
    [stato, aggiorna],
  );

  const confermaPacchetto = useCallback(
    (pacchetto: ProfiloId) => {
      if (!stato) return;
      setForzata(null);
      aggiorna({
        ...stato,
        pacchettoScelto: pacchetto,
        sottoscrittoIl: stato.sottoscrittoIl ?? new Date().toISOString(),
      });
    },
    [stato, aggiorna],
  );

  const rifaiQuestionario = useCallback(() => {
    if (!stato) return;
    setForzata(null);
    aggiorna({ ...stato, risposte: null, esito: null, pacchettoScelto: null });
  }, [stato, aggiorna]);

  const valore = useMemo<ContestoApp>(
    () => ({
      stato,
      schermata: forzata ?? schermataNaturale(stato),
      accediConEmail,
      esci,
      salvaQuestionario,
      confermaPacchetto,
      rifaiQuestionario,
      vaiA: setForzata,
    }),
    [stato, forzata, accediConEmail, esci, salvaQuestionario, confermaPacchetto, rifaiQuestionario],
  );

  return <Contesto.Provider value={valore}>{children}</Contesto.Provider>;
}

export function useApp(): ContestoApp {
  const contesto = useContext(Contesto);
  if (!contesto) throw new Error('useApp va usato dentro <AppProvider>');
  return contesto;
}
