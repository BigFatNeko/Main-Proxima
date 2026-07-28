const euro = new Intl.NumberFormat('it-IT', {
  style: 'currency',
  currency: 'EUR',
  maximumFractionDigits: 0,
});

const euroDecimali = new Intl.NumberFormat('it-IT', {
  style: 'currency',
  currency: 'EUR',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

export function formattaEuro(valore: number, decimali = false): string {
  return decimali ? euroDecimali.format(valore) : euro.format(valore);
}

/** Percentuale con segno esplicito, usata per i rendimenti. */
export function formattaPercentuale(valore: number, decimali = 1): string {
  const segno = valore > 0 ? '+' : '';
  return `${segno}${valore.toFixed(decimali).replace('.', ',')}%`;
}

/** Differenza in punti percentuali fra due rendimenti. */
export function formattaPunti(valore: number, decimali = 1): string {
  const segno = valore > 0 ? '+' : '';
  return `${segno}${valore.toFixed(decimali).replace('.', ',')} pp`;
}

export function formattaData(iso: string): string {
  return new Date(iso).toLocaleDateString('it-IT', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}

export function formattaMeseCorto(iso: string): string {
  return new Date(iso).toLocaleDateString('it-IT', { month: 'short', year: '2-digit' });
}
