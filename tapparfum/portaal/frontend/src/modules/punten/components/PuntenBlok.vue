<script setup>
// Punten & spaarstand bij één winkel (v71: basispunten + bonuspunten).
// Flow: de PARTNER claimt een punt ("wij hebben dit geregeld"), de AM of
// kantoor keurt goed — dan pas telt het. AM/kantoor kan ook direct togglen.
import { computed, ref } from 'vue'
import { useAuth } from '../../../stores/auth.js'
import { useTappunten } from '../../tappunten/store.js'
import {
  BASIS, BASIS_MAX, OFFICIEEL, BONUS_MANUAL, BONUS_MAX,
  basisScore, bonusHandmatig, bonusAuto, actiePunten, totaalScore, officieel,
  omzetGroeiPunten, jaardoelPunten, beOnTimePunten
} from '../logic.js'

const props = defineProps({ tappunt: { type: Object, required: true } })
const emit = defineEmits(['bijgewerkt'])
const auth = useAuth()
const st = useTappunten()
const fout = ref('')
const bezig = ref(false)

const t = computed(() => props.tappunt)
const scores = computed(() => ({
  basis: basisScore(t.value), bonus: bonusHandmatig(t.value), auto: bonusAuto(t.value),
  acties: actiePunten(t.value), totaal: totaalScore(t.value), officieel: officieel(t.value)
}))
const autoUitleg = computed(() => {
  const d = []
  const g = omzetGroeiPunten(t.value); if (g) d.push(`groei +${g}`)
  const j = jaardoelPunten(t.value); if (j) d.push(`jaardoel +${j}`)
  const b = beOnTimePunten(t.value); if (b) d.push(`break-even op tijd +${b}`)
  return d.join(' · ') || 'nog geen automatische punten'
})

async function bewaar(t2) {
  bezig.value = true; fout.value = ''
  try { await st.bewaar(t2); emit('bijgewerkt', t2) }
  catch (e) { fout.value = 'Opslaan mislukt: ' + e.message }
  bezig.value = false
}

function velden(soort) {  // 'bp' | 'bonus'
  return soort === 'bp' ? ['bp', 'bpClaim'] : ['bonus', 'bonusClaim']
}

// partner: claimen / claim intrekken
async function claim(soort, key) {
  const [, ck] = velden(soort)
  const claims = { ...(t.value[ck] || {}) }
  if (claims[key]) delete claims[key]; else claims[key] = true
  await bewaar({ ...t.value, [ck]: claims })
}

// AM/kantoor: goedkeuren (zet punt, wist claim) of punt weer uitzetten
async function zet(soort, key, aan) {
  const [vk, ck] = velden(soort)
  const punten = { ...(t.value[vk] || {}) }
  const claims = { ...(t.value[ck] || {}) }
  if (aan) punten[key] = true; else delete punten[key]
  delete claims[key]
  await bewaar({ ...t.value, [vk]: punten, [ck]: claims })
}

function rijStatus(soort, key) {
  const [vk, ck] = velden(soort)
  if ((t.value[vk] || {})[key]) return 'ok'
  if ((t.value[ck] || {})[key]) return 'claim'
  return 'open'
}
</script>

<template>
  <section class="blok">
    <div class="kop">
      <h2>⭐ Punten & spaarstand</h2>
      <span v-if="scores.officieel" class="badge groen" data-test="punt-officieel">✓ Officieel TapParfum-punt</span>
    </div>
    <div class="chips">
      <span class="chip" data-test="punt-basis">Basis <b>{{ scores.basis }}</b>/{{ BASIS_MAX }}</span>
      <span class="chip" data-test="punt-bonus">Bonus <b>{{ scores.bonus }}</b>/{{ BONUS_MAX }}</span>
      <span class="chip" :title="autoUitleg" data-test="punt-auto">Automatisch <b>{{ scores.auto }}</b></span>
      <span v-if="scores.acties" class="chip">Acties <b>{{ scores.acties }}</b></span>
      <span class="chip totaal" data-test="punt-totaal">Totaal <b>{{ scores.totaal }}</b></span>
    </div>
    <p class="mo">Automatisch: {{ autoUitleg }} · officieel-drempel: {{ OFFICIEEL }} basispunten</p>
    <p v-if="fout" class="fout" role="alert">{{ fout }}</p>

    <template v-for="[soort, titel, LIJST] in [['bp', 'Basispunten', BASIS], ['bonus', 'Bonuspunten', BONUS_MANUAL]]" :key="soort">
      <h3>{{ titel }}</h3>
      <div v-for="[key, label, p] in LIJST" :key="key" class="rij" :class="rijStatus(soort, key)" :data-test="'punt-' + key">
        <span class="pt">{{ p }}</span>
        <span class="lbl">{{ label }}</span>
        <!-- partner -->
        <template v-if="auth.isPartner">
          <span v-if="rijStatus(soort, key) === 'ok'" class="badge groen">✓</span>
          <button v-else-if="rijStatus(soort, key) === 'claim'" class="klein wacht" type="button"
                  :data-test="'claim-' + key" @click="claim(soort, key)">wacht op AM · intrekken</button>
          <button v-else class="klein" type="button" :data-test="'claim-' + key" @click="claim(soort, key)">Claim ✋</button>
        </template>
        <!-- AM / kantoor -->
        <template v-else>
          <button v-if="rijStatus(soort, key) === 'claim'" class="klein keur" type="button"
                  :data-test="'keur-' + key" @click="zet(soort, key, true)">Keur goed ✓</button>
          <button v-if="rijStatus(soort, key) === 'claim'" class="klein" type="button"
                  :aria-label="'Claim afwijzen: ' + key" @click="zet(soort, key, false)">wijs af</button>
          <label v-else class="schakel">
            <input type="checkbox" :checked="rijStatus(soort, key) === 'ok'" :disabled="bezig"
                   :data-test="'zet-' + key" @change="zet(soort, key, $event.target.checked)" />
          </label>
        </template>
      </div>
    </template>
  </section>
</template>

<style scoped>
.blok{background:#fff;border:1px solid var(--line);border-radius:16px;padding:18px 22px;margin-top:14px}
.kop{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
h2{margin:0;font-size:16px;flex:1}
h3{margin:16px 0 6px;font-size:12px;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:var(--grey)}
.chips{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
.chip{background:var(--cream);border:1px solid var(--line);border-radius:999px;padding:4px 12px;font-size:12.5px;color:var(--grey);font-weight:700}
.chip b{color:var(--ink);font-variant-numeric:tabular-nums}
.chip.totaal{background:var(--soft);border-color:var(--coral);color:var(--coral-d)}
.chip.totaal b{color:var(--coral-d)}
.mo{color:var(--grey);font-size:12px;margin:8px 0 0}
.rij{display:flex;align-items:center;gap:10px;padding:7px 0;border-bottom:1px solid var(--line);font-size:13.5px}
.rij:last-child{border-bottom:0}
.rij.ok .lbl{color:var(--grey)}
.rij.claim{background:linear-gradient(90deg,var(--soft),transparent)}
.pt{flex-shrink:0;width:26px;height:26px;border-radius:8px;background:var(--cream);border:1px solid var(--line);display:flex;align-items:center;justify-content:center;font-weight:800;font-size:12px;color:var(--coral-d)}
.lbl{flex:1;min-width:0}
.badge{font-size:11.5px;font-weight:800;border-radius:6px;padding:2px 10px}
.badge.groen{background:var(--green-soft);color:#2c5a12}
.klein{background:none;border:1.5px solid var(--line);border-radius:8px;padding:4px 11px;font-size:12px;font-weight:700;color:var(--grey);cursor:pointer;white-space:nowrap}
.klein:hover{border-color:var(--coral);color:var(--coral-d)}
.klein.keur{border-color:var(--green);color:var(--green)}
.klein.keur:hover{background:var(--green-soft)}
.klein.wacht{border-color:var(--amber);color:#8a6210}
.schakel input{width:17px;height:17px;accent-color:var(--coral)}
.fout{color:#b3261e;font-size:13px}
</style>
