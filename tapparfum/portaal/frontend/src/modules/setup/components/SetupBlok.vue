<script setup>
// Opstartchecklist bij één winkel. v71-regels: de PARTNER vinkt af, de AM en
// kantoor kijken mee (read-only) en kunnen de checklist overslaan voor een
// bestaande winkel. Fase 4-5 gaan pas open zodra de demodag gepland is.
import { computed, ref } from 'vue'
import { useAuth } from '../../../stores/auth.js'
import { useTappunten } from '../../tappunten/store.js'
import { SETUP, SETUP_TOTAL, setupDone, setupCount, setupComplete, faseOpen, setupIsForm, setupFormNaam } from '../logic.js'

const props = defineProps({ tappunt: { type: Object, required: true } })
const emit = defineEmits(['bijgewerkt'])
const auth = useAuth()
const st = useTappunten()
const fout = ref('')
const bezig = ref(false)

const aantal = computed(() => setupCount(props.tappunt))
const klaar = computed(() => setupComplete(props.tappunt))
const pct = computed(() => Math.round((aantal.value / SETUP_TOTAL) * 100))

async function bewaar(t2) {
  bezig.value = true; fout.value = ''
  try { await st.bewaar(t2); emit('bijgewerkt', t2) }
  catch (e) { fout.value = 'Opslaan mislukt: ' + e.message }
  bezig.value = false
}

async function vink(si, ai, ev) {
  if (!auth.isPartner) { ev.preventDefault(); return }   // alleen de partner vinkt (v71)
  if (setupIsForm(si, ai)) { ev.preventDefault(); return } // formuliergekoppeld — niet handmatig
  const t = props.tappunt
  const done = { ...((t.setup && t.setup.done) || {}) }
  const key = `${si}-${ai}`
  if (ev.target.checked) done[key] = true; else delete done[key]
  await bewaar({ ...t, setup: { ...(t.setup || {}), done } })
}

async function skip() {
  const t = props.tappunt
  await bewaar({ ...t, setup: { ...(t.setup || {}), skipped: !(t.setup && t.setup.skipped) } })
}
</script>

<template>
  <section class="blok" :class="{ af: klaar }">
    <div class="kop">
      <h2>🚀 Opstartchecklist</h2>
      <span class="stand" data-test="setup-stand">{{ aantal }}/{{ SETUP_TOTAL }}</span>
      <span v-if="klaar" class="badge" data-test="setup-klaar">✓ {{ tappunt.setup && tappunt.setup.skipped ? 'overgeslagen' : 'afgerond' }}</span>
    </div>
    <div class="balk"><div class="vul" :style="{ width: pct + '%' }"></div></div>
    <p v-if="fout" class="fout" role="alert">{{ fout }}</p>
    <p v-if="!auth.isPartner" class="note">De winkel vinkt zelf af; jij kijkt mee.
      <button class="skipknop" type="button" data-test="setup-skip" @click="skip">
        {{ tappunt.setup && tappunt.setup.skipped ? 'Overslaan ongedaan maken' : 'Overslaan (bestaande winkel)' }}
      </button>
    </p>

    <details v-for="(s, si) in SETUP" :key="s.nr" class="fase" :open="!klaar && faseOpen(tappunt, si) && si === 0">
      <summary>
        <b>Fase {{ s.nr }} · {{ s.titel }}</b>
        <span class="mo">{{ s.acties.filter((_, ai) => setupDone(tappunt, si, ai)).length }}/{{ s.acties.length }}</span>
        <span v-if="!faseOpen(tappunt, si)" class="slot" data-test="setup-slot">🔒 na demodag plannen</span>
      </summary>
      <label v-for="(a, ai) in s.acties" :key="ai" class="stap" :class="{ dicht: !faseOpen(tappunt, si) }">
        <input type="checkbox" :checked="setupDone(tappunt, si, ai)"
               :disabled="bezig || !auth.isPartner || !faseOpen(tappunt, si) || setupIsForm(si, ai)"
               :data-test="'setup-' + si + '-' + ai" @change="vink(si, ai, $event)" />
        <span :class="{ door: setupDone(tappunt, si, ai) }">{{ a }}
          <template v-if="setupIsForm(si, ai)">
            <router-link class="viaform" :to="{ name: 'formulieren' }" :data-test="'setup-form-' + si + '-' + ai">
              via formulier: {{ setupFormNaam(si, ai) }} →
            </router-link>
          </template>
        </span>
      </label>
    </details>
  </section>
</template>

<style scoped>
.blok{background:#fff;border:1px solid var(--line);border-radius:16px;padding:18px 22px;margin-top:14px}
.blok.af{border-color:#bcd9a0}
.kop{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
h2{margin:0;font-size:16px;flex:1}
.stand{font-weight:800;color:var(--coral-d);font-variant-numeric:tabular-nums}
.badge{background:var(--green-soft);color:#2c5a12;font-size:11.5px;font-weight:800;border-radius:6px;padding:2px 10px}
.balk{height:8px;border-radius:6px;background:var(--cream);overflow:hidden;margin:10px 0}
.vul{height:100%;background:var(--coral);transition:width .4s ease}
.note{font-size:12.5px;color:var(--grey);background:var(--cream);border:1px solid var(--line);border-radius:10px;padding:8px 12px;display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin:0 0 8px}
.skipknop{background:none;border:1.5px solid var(--line);border-radius:8px;padding:4px 10px;font-size:12px;font-weight:700;color:var(--grey);cursor:pointer}
.skipknop:hover{border-color:var(--coral);color:var(--coral-d)}
.fase{border-bottom:1px solid var(--line);padding:8px 0}
.fase:last-child{border-bottom:0}
summary{display:flex;align-items:center;gap:10px;cursor:pointer;font-size:14px;list-style-position:inside}
.mo{color:var(--grey);font-size:12px;font-variant-numeric:tabular-nums}
.slot{margin-left:auto;font-size:11.5px;color:var(--amber);font-weight:700}
.stap{display:flex;align-items:flex-start;gap:10px;padding:6px 0 6px 22px;font-size:13.5px;cursor:pointer}
.stap.dicht{opacity:.5}
.stap input{width:17px;height:17px;accent-color:var(--coral);flex-shrink:0;margin-top:1px}
.door{color:var(--grey);text-decoration:line-through}
.viaform{display:inline-block;margin-left:6px;font-size:11.5px;font-weight:800;color:var(--coral-d);text-decoration:none}
.viaform:hover{text-decoration:underline}
.fout{color:#b3261e;font-size:13px}
</style>
