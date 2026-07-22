// Gedeelde formatteerders.
export const eur0 = (n) =>
  new Intl.NumberFormat('nl-NL', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 })
    .format(Number(n) || 0)
