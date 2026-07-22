<script setup>
// Geurbibliotheek — alle geuren, doorzoekbaar en per lijn (v71). De partner
// kan direct een refill bijbestellen: dat landt als melding bij de AM.
import { computed, ref } from 'vue'
import { useAuth } from '../../../stores/auth.js'
import { useTappunten } from '../../tappunten/store.js'
import { stuurWinkelvraag } from '../../winkelvragen/api.js'
import { FRAGS, LIJNEN, NOTECARDS, MERK_ASSETS } from '../data.js'

const auth = useAuth()
const st = useTappunten()
const zoek = ref('')
const lijn = ref('Alle')
const melding = ref('')
const fout = ref('')
const bezig = ref('')

const lijst = computed(() => {
  const q = zoek.value.trim().toLowerCase()
  return FRAGS.filter(fr =>
    (lijn.value === 'Alle' || fr[1] === lijn.value) &&
    (!q || (fr[0] + ' ' + fr[3]).toLowerCase().includes(q)))
})

async function refill(code) {
  const eigen = st.items[0]
  if (!eigen || bezig.value) return
  bezig.value = code; fout.value = ''; melding.value = ''
  try {
    await stuurWinkelvraag({ tappunt_snelstart: eigen.snelstart, type: 'vraag', txt: `🧴 Refill besteld: ${code} — graag bijbestellen.` })
    melding.value = `✓ Refill ${code} doorgegeven aan je accountmanager.`
  } catch (e) { fout.value = 'Doorgeven mislukt: ' + e.message }
  bezig.value = ''
}
</script>

<template>
  <div>
    <h1>🌸 Geurbibliotheek</h1>
    <p class="sub">Alle geuren — zoek op code of geurnoot, of filter per lijn. Verkoop op geurnoten: dat is dé conversie naar een vaste klant.</p>

    <!-- Geurnoten-strip -->
    <div class="noten">
      <div v-for="n in NOTECARDS" :key="n[1]" class="noot">
        <span class="ic">{{ n[0] }}</span><b>{{ n[1] }}</b><span class="mo">{{ n[2] }}</span>
      </div>
    </div>

    <div class="balk">
      <input v-model="zoek" type="search" placeholder="Zoek op code of geurnoot…" data-test="geur-zoek" />
      <div class="chips">
        <button v-for="l in LIJNEN" :key="l" class="chip" :class="{ aan: lijn === l }" type="button" :data-test="'lijn-' + l" @click="lijn = l">{{ l }}</button>
      </div>
    </div>
    <p v-if="melding" class="ok" role="status" data-test="refill-melding">{{ melding }}</p>
    <p v-if="fout" class="fout" role="alert">{{ fout }}</p>

    <div class="grid">
      <div v-for="fr in lijst" :key="fr[0]" class="geur" data-test="geur-kaart">
        <div class="gkop"><b class="code">{{ fr[0] }}</b><span class="lijnbadge">{{ fr[1] }}</span></div>
        <p class="noten-txt">{{ fr[3] }}</p>
        <div class="gvoet">
          <span class="prijs">€ {{ fr[2] }}</span>
          <button v-if="auth.isPartner" class="klein" type="button" :disabled="bezig === fr[0]" :data-test="'refill-' + fr[0]" @click="refill(fr[0])">
            {{ bezig === fr[0] ? '…' : '🧴 Bestel refill' }}
          </button>
        </div>
      </div>
    </div>
    <p v-if="!lijst.length" class="stil">Geen geuren gevonden.</p>

    <!-- Merk & materialen -->
    <h2 class="merk-kop">🎨 Merk & materialen</h2>
    <p class="sub">De officiële TapParfum-materialen. De bestanden staan in de gedeelde Dropbox / op het B2B-portaal (retail-brands.nl) — vraag je accountmanager om toegang.</p>
    <div class="assets">
      <div v-for="a in MERK_ASSETS" :key="a.t" class="asset" data-test="merk-asset">
        <span class="aic">{{ a.ic }}</span><b>{{ a.t }}</b><span class="mo">{{ a.fmt }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
h1{margin:0 0 4px;font-size:22px}
h2.merk-kop{margin:24px 0 4px;font-size:18px}
.sub{color:var(--grey);margin:0 0 14px;font-size:13.5px}
.noten{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px}
.noot{display:flex;flex-direction:column;align-items:center;gap:1px;background:#fff;border:1px solid var(--line);border-radius:12px;padding:8px 14px;min-width:78px}
.noot .ic{font-size:20px}
.noot b{font-size:12.5px}
.mo{color:var(--grey);font-size:11px}
.balk{display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-bottom:10px}
input[type=search]{flex:1;min-width:200px;max-width:320px;padding:9px 12px;border:1.5px solid var(--line);border-radius:10px;font-size:14px}
input:focus{border-color:var(--coral)}
.chips{display:flex;gap:6px;flex-wrap:wrap}
.chip{background:#fff;border:1.5px solid var(--line);border-radius:999px;padding:6px 12px;font-size:12.5px;font-weight:700;color:var(--grey);cursor:pointer}
.chip.aan{border-color:var(--coral);background:var(--soft);color:var(--coral-d)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px}
.geur{background:#fff;border:1px solid var(--line);border-radius:14px;padding:14px}
.gkop{display:flex;align-items:center;gap:8px}
.code{font-size:17px;letter-spacing:.03em}
.lijnbadge{margin-left:auto;background:var(--soft);color:var(--coral-d);font-size:11px;font-weight:800;border-radius:6px;padding:2px 9px}
.noten-txt{font-size:13px;color:var(--grey);margin:8px 0 12px;line-height:1.4;min-height:36px}
.gvoet{display:flex;align-items:center;justify-content:space-between;gap:8px}
.prijs{font-weight:800;color:var(--ink)}
.klein{background:none;border:1.5px solid var(--line);border-radius:8px;padding:5px 11px;font-size:12px;font-weight:700;color:var(--grey);cursor:pointer}
.klein:hover{border-color:var(--coral);color:var(--coral-d)}
.klein:disabled{opacity:.6}
.assets{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px}
.asset{display:flex;flex-direction:column;gap:2px;background:#fff;border:1px solid var(--line);border-radius:12px;padding:14px}
.aic{font-size:24px}
.asset b{font-size:14px}
.ok{color:#2c5a12;font-size:13px}
.fout{color:#b3261e}
.stil{color:var(--grey)}
</style>
