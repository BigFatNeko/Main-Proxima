import type { StatoUtente } from '../types';

/**
 * Persistenza fittizia su localStorage.
 *
 * Sostituisce il backend finché non esiste: nessuna password viene mai
 * salvata, l'utente è identificato dalla sola email. Da rimpiazzare con
 * l'autenticazione reale prima di qualunque uso con clienti veri.
 */

const CHIAVE_UTENTI = 'proxima:utenti';
const CHIAVE_SESSIONE = 'proxima:sessione';

type Archivio = Record<string, StatoUtente>;

function leggiArchivio(): Archivio {
  try {
    const grezzo = localStorage.getItem(CHIAVE_UTENTI);
    return grezzo ? (JSON.parse(grezzo) as Archivio) : {};
  } catch {
    return {};
  }
}

function scriviArchivio(archivio: Archivio): void {
  localStorage.setItem(CHIAVE_UTENTI, JSON.stringify(archivio));
}

export function normalizzaEmail(email: string): string {
  return email.trim().toLowerCase();
}

export function caricaUtente(email: string): StatoUtente | null {
  return leggiArchivio()[normalizzaEmail(email)] ?? null;
}

export function salvaUtente(stato: StatoUtente): void {
  const archivio = leggiArchivio();
  archivio[normalizzaEmail(stato.utente.email)] = stato;
  scriviArchivio(archivio);
}

export function esisteUtente(email: string): boolean {
  return caricaUtente(email) !== null;
}

export function apriSessione(email: string): void {
  localStorage.setItem(CHIAVE_SESSIONE, normalizzaEmail(email));
}

export function chiudiSessione(): void {
  localStorage.removeItem(CHIAVE_SESSIONE);
}

export function sessioneAttiva(): StatoUtente | null {
  const email = localStorage.getItem(CHIAVE_SESSIONE);
  return email ? caricaUtente(email) : null;
}

/** Nome di cortesia ricavato dall'email, quando l'utente non lo indica. */
export function nomeDaEmail(email: string): string {
  const locale = normalizzaEmail(email).split('@')[0] ?? '';
  const parola = locale.split(/[._-]/)[0] ?? locale;
  return parola ? parola.charAt(0).toUpperCase() + parola.slice(1) : 'Cliente';
}

/** Azzera tutto: comodo per ripetere una demo da zero. */
export function azzeraTutto(): void {
  localStorage.removeItem(CHIAVE_UTENTI);
  localStorage.removeItem(CHIAVE_SESSIONE);
}
