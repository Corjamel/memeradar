<script setup>
// Situatie & stuurgegevens bij één winkel (AM/kantoor) — v71 sitswitch/setStatus
// (r.2905), setKlanten (r.2677), setBeDone (r.2673). De situatie is normaal
// automatisch (statusKey); hier kan een AM 'm handmatig overschrijven, het
// aantal vaste klanten bijhouden en break-even markeren als terugverdiend.
import { computed, ref } from 'vue'
import { useTappunten } from '../store.js'
import { STATUS, statusKey, beDone, flessenVerkocht } from '../../rekenhart/logic.js'
import { checkMilestones } from '../../beloningen/logic.js'

const props = defineProps({ tappunt: { type: Object, required: true }, marge: { type: Number, default: 1 } })
const emit = defineEmits(['bijgewerkt'])
const st = useTappunten()
const fout = ref('')
const bezig = ref(false)
const klantenIn = ref(props.tappunt.klanten || 0)

const t = computed(() => props.tappunt)
const auto = computed(() => statusKey({ ...t.value, statusManual: '' }, props.marge))
const KEUZES = ['nieuw', 'groeit', 'stagneert', 'top']

async function bewaar(t2, joVoor = null) {
  bezig.value = true; fout.value = ''
  try {
    let n = t2
    if (joVoor != null) { const r = checkMilestones(t2, joVoor, props.marge); if (r) n = r.t2 }
    await st.bewaar(n); emit('bijgewerkt', n)
  } catch (e) { fout.value = 'Opslaan mislukt: ' + e.message }
  bezig.value = false
}

async function zetStatus(v) { await bewaar({ ...t.value, statusManual: v }) }
async function zetKlanten() { await bewaar({ ...t.value, klanten: Math.max(0, parseInt(klantenIn.value) || 0) }) }
async function markeerBe() {
  const vandaag = new Date().toISOString().slice(0, 10)
  await bewaar({ ...t.value, beDone: true, beDoneAt: vandaag, vieringen: [...(t.value.vieringen || []), { type: 'be', at: vandaag }] })
}
</script>

<template>
  <section class="blok">
    <h2>🎛️ Situatie & sturing</h2>
    <p v-if="fout" class="fout" role="alert">{{ fout }}</p>

    <div class="rij">
      <span class="lbl">Situatie</span>
      <button class="ss" :class="{ aan: !t.statusManual }" type="button" data-test="sit-auto" @click="zetStatus('')">
        Auto · {{ STATUS[auto].l }}
      </button>
      <button v-for="k in KEUZES" :key="k" class="ss" :class="{ aan: t.statusManual === k }" type="button"
              :disabled="bezig" :data-test="'sit-' + k" @click="zetStatus(k)">{{ STATUS[k].l }}</button>
    </div>

    <div class="rij2">
      <label class="veld">Vaste klanten
        <input v-model="klantenIn" type="number" min="0" data-test="klanten-in" @change="zetKlanten" />
      </label>
      <div v-if="t.be" class="beblok">
        <span class="mo">Break-even: <b>{{ flessenVerkocht(t) }}</b>/{{ t.be.bottles }} flessen</span>
        <button v-if="!beDone(t)" class="knop" type="button" :disabled="bezig" data-test="markeer-be" @click="markeerBe">Markeer als terugverdiend</button>
        <span v-else class="badge groen" data-test="be-behaald">✓ terugverdiend{{ t.beDoneAt ? ' · ' + t.beDoneAt : '' }}</span>
      </div>
    </div>
  </section>
</template>

<style scoped>
.blok{background:#fff;border:1px solid var(--line);border-radius:16px;padding:18px 22px;margin-top:14px}
h2{margin:0 0 12px;font-size:16px}
.rij{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.lbl{font-size:12.5px;font-weight:800;color:var(--grey);text-transform:uppercase;letter-spacing:.05em;margin-right:4px}
.ss{background:var(--cream);border:1.5px solid var(--line);border-radius:999px;padding:6px 13px;font-size:12.5px;font-weight:700;color:var(--grey);cursor:pointer}
.ss.aan{border-color:var(--coral);background:var(--soft);color:var(--coral-d)}
.rij2{display:flex;gap:18px;flex-wrap:wrap;align-items:flex-end;margin-top:14px}
.veld{display:flex;flex-direction:column;gap:5px;font-size:12.5px;font-weight:700;color:var(--grey)}
.veld input{padding:8px 10px;border:1.5px solid var(--line);border-radius:10px;font-size:14px;max-width:120px}
.veld input:focus{border-color:var(--coral)}
.beblok{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.mo{color:var(--grey);font-size:12.5px}
.mo b{color:var(--ink)}
.knop{background:var(--coral);color:#fff;border:0;border-radius:10px;padding:8px 14px;font-weight:800;cursor:pointer;font-size:13px}
.knop:disabled{opacity:.6}
.badge.groen{background:var(--green-soft);color:#2c5a12;font-size:11.5px;font-weight:800;border-radius:6px;padding:3px 10px}
.fout{color:#b3261e;font-size:13px}
</style>
