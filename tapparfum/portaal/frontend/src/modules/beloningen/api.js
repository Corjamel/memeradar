// API-laag Beloningen: haalt de netwerk-rekenconfig op waarmee het rekenhart
// (niveaus/status) en de beloningen-engine rekenen. Kantoor beheert beide
// waarden onder Beheer → Instellingen; iedereen leest ze.
import { haalCentral } from '../beheer/api.js'
import { STANDAARD_MATEN } from '../kassa/api.js'

export async function haalRekenConfig() {
  const [m, fm] = await Promise.all([haalCentral('margeFactor'), haalCentral('flesMaten')])
  const marge = Number(m) > 0 ? Number(m) : 1
  const maten = Array.isArray(fm) && fm.length ? fm : STANDAARD_MATEN
  return { marge, maten }
}
