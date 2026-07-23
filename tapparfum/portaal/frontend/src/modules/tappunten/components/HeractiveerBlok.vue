<script setup>
// Heractivatie-blok (v71 padHeractiveren, r.2883) — verschijnt op de
// winkelpagina zodra een winkel stagneert. De AM/kantoor loopt het vaste
// stappenplan langs, kiest een heractivatie-actie + opvolgdatum en vinkt de
// opvolging af. Deelt exact de t.react-datastructuur met de Trajecten-module.
import { reactive, ref } from 'vue'
import { useTappunten } from '../store.js'
import { REACT_ACTIES, reactToevoegen, reactDone } from '../../trajecten/logic.js'

const props = defineProps({ tappunt: { type: Object, required: true } })
const emit = defineEmits(['bijgewerkt'])
const st = useTappunten()
const bezig = ref(false)
const fout = ref('')
const tdef = new Date(Date.now() + 14 * 864e5).toISOString().slice(0, 10)   // standaard: over 2 weken
const inv = reactive({ actie: '', opvolg: tdef })

const STAPPEN = [
  'Bel het tappunt — wat loopt er stroef?',
  'Loop de voorraad-checklist langs (testers, presentatie, voorraad)',
  'Kies hieronder een actie en zet ’m in',
  'Plan opvolging in de agenda'
]

async function bewaar(t2, ok) {
  if (!t2) return
  bezig.value = true; fout.value = ''
  try {
    await st.bewaar(t2)
    emit('bijgewerkt', t2)
    if (ok) { inv.actie = ''; inv.opvolg = tdef }
  } catch (e) { fout.value = 'Opslaan mislukt: ' + e.message }
  bezig.value = false
}
async function vastleggen() {
  if (!inv.actie) { fout.value = 'Kies eerst een actie.'; return }
  await bewaar(reactToevoegen(props.tappunt, inv.actie, inv.opvolg), true)
}
async function vink(idx, v) { await bewaar(reactDone(props.tappunt, idx, v)) }
</script>

<template>
  <section class="blok" data-test="heractiveer">
    <div class="pathnote">⚠ Stagneert — zoek uit wat er misging en heractiveer.</div>
    <div class="stappen">
      <div v-for="(s, i) in STAPPEN" :key="i" class="stap"><b>{{ i + 1 }}</b><span>{{ s }}</span></div>
    </div>
    <p class="mo">Voorraad & presentatie: <router-link :to="{ name: 'formulieren' }" class="lnk">→ open de voorraad-checklist</router-link></p>

    <div class="rij">
      <select v-model="inv.actie" data-test="her-actie">
        <option value="">— kies een heractivatie-actie —</option>
        <option v-for="a in REACT_ACTIES" :key="a" :value="a">{{ a }}</option>
      </select>
      <input v-model="inv.opvolg" type="date" data-test="her-opvolg" aria-label="Opvolgdatum" />
      <button class="knop" type="button" :disabled="bezig" data-test="her-vastleggen" @click="vastleggen">Vastleggen</button>
    </div>
    <p v-if="fout" class="fout" role="alert">{{ fout }}</p>

    <div v-if="(tappunt.react || []).length" class="hist">
      <label v-for="(r, i) in tappunt.react" :key="i" class="react" :class="{ af: r.done }" data-test="her-rij">
        <input type="checkbox" :checked="r.done" :disabled="bezig" :data-test="'her-done-' + i" @change="vink(i, $event.target.checked)" />
        <span>{{ r.date }} · {{ r.actie }}<i v-if="r.opvolg" class="mo"> → opvolgen {{ r.opvolg }}</i></span>
      </label>
    </div>
  </section>
</template>

<style scoped>
.blok{background:#fff;border:1px solid var(--line);padding:18px 20px;margin-top:14px;border-left:4px solid var(--amber)}
.pathnote{font-size:13.5px;font-weight:700;color:var(--amber);margin-bottom:10px}
.stappen{background:var(--soft);padding:12px 14px;margin-bottom:12px}
.stap{display:flex;gap:10px;align-items:baseline;font-size:13px;line-height:1.7}
.stap b{color:var(--coral-d);flex-shrink:0}
.mo{color:var(--grey);font-size:12.5px;margin:0 0 12px}
.lnk{color:var(--coral);font-weight:700;text-decoration:none}
.lnk:hover{text-decoration:underline}
.rij{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
select,input{padding:9px 11px;border:1.5px solid var(--line);font-size:14px;font-family:inherit}
select{flex:1;min-width:200px}
select:focus,input:focus{border-color:var(--coral);outline:none}
.knop{background:var(--coral);color:#fff;border:0;padding:9px 16px;font-weight:800;cursor:pointer;text-transform:uppercase;letter-spacing:.4px}
.knop:disabled{opacity:.6}
.hist{margin-top:12px;border-top:1px solid var(--line);padding-top:8px}
.react{display:flex;align-items:flex-start;gap:9px;padding:5px 0;font-size:13px;cursor:pointer}
.react input{width:16px;height:16px;accent-color:var(--coral);margin-top:1px}
.react.af span{color:var(--grey);text-decoration:line-through}
.react i{font-style:normal}
.fout{color:#b3261e;font-size:13px}
</style>
