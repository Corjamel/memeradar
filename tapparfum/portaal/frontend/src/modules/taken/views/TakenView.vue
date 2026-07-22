<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useAuth } from '../../../stores/auth.js'
import { useTappunten } from '../../tappunten/store.js'
import { haalTaken, nieuweTaak, zetKlaar, haalAms } from '../api.js'

const auth = useAuth()
const st = useTappunten()
const taken = ref([])
const ams = ref([])
const fout = ref('')
const bezig = ref(false)
const nieuw = reactive({ titel: '', deadline: '', tappunt_snelstart: '', am_id: '' })

const WINKEL = computed(() => Object.fromEntries(st.items.map(t => [t.snelstart, t.name])))
const AM_NAAM = computed(() => Object.fromEntries(ams.value.map(a => [a.id, a.naam])))
const open = computed(() => taken.value.filter(t => !t.klaar))
const klaar = computed(() => taken.value.filter(t => t.klaar))
const vandaag = new Date().toISOString().slice(0, 10)

async function laad() {
  fout.value = ''
  try {
    taken.value = await haalTaken()
    if (auth.isKantoor) ams.value = await haalAms()
  } catch (e) { fout.value = 'Kon taken niet laden: ' + e.message }
}
onMounted(async () => {
  if (!st.items.length) await st.laad()
  await laad()
})

async function toevoegen() {
  if (bezig.value) return
  if (!nieuw.titel.trim()) { fout.value = 'Geef de taak een titel.'; return }
  bezig.value = true; fout.value = ''
  try {
    await nieuweTaak({
      titel: nieuw.titel.trim(), deadline: nieuw.deadline || null,
      tappunt_snelstart: nieuw.tappunt_snelstart || null,
      am_id: auth.isKantoor ? (nieuw.am_id || null) : auth.amId
    })
    nieuw.titel = ''; nieuw.deadline = ''; nieuw.tappunt_snelstart = ''; nieuw.am_id = ''
    await laad()
  } catch (e) { fout.value = 'Opslaan mislukt: ' + e.message }
  bezig.value = false
}

async function vink(t, ev) {
  try { await zetKlaar(t.id, ev.target.checked); await laad() }
  catch (e) { fout.value = 'Bijwerken mislukt: ' + e.message }
}
</script>

<template>
  <div>
    <h1>Taken</h1>
    <p class="sub" v-if="auth.isKantoor">Wijs taken toe aan accountmanagers en volg wat er open staat.</p>
    <p class="sub" v-else>Jouw takenlijst — van kantoor en van jezelf.</p>
    <p v-if="fout" class="fout" role="alert">{{ fout }}</p>

    <form class="kaart nieuw" @submit.prevent="toevoegen">
      <div class="rij">
        <label>Taak<input v-model="nieuw.titel" required placeholder="Bijv. Bel Zwolle over de actie" data-test="taak-titel" /></label>
        <label v-if="auth.isKantoor">Voor
          <select v-model="nieuw.am_id" data-test="taak-am">
            <option value="">— kies AM (optioneel) —</option>
            <option v-for="a in ams" :key="a.id" :value="a.id">{{ a.naam }}</option>
          </select>
        </label>
        <label>Winkel (optioneel)
          <select v-model="nieuw.tappunt_snelstart">
            <option value="">—</option>
            <option v-for="t in st.items" :key="t.snelstart" :value="t.snelstart">{{ t.name }}</option>
          </select>
        </label>
        <label>Deadline<input v-model="nieuw.deadline" type="date" /></label>
      </div>
      <button class="btn" type="submit" :disabled="bezig" data-test="taak-toevoegen">{{ bezig ? 'Bezig…' : 'Taak toevoegen' }}</button>
    </form>

    <h2 v-if="open.length">Open ({{ open.length }})</h2>
    <div v-for="t in open" :key="t.id" class="kaart item" data-test="taak-item"
         :class="{ laat: t.deadline && t.deadline < vandaag }">
      <label class="chk">
        <input type="checkbox" :checked="t.klaar" data-test="taak-check" @change="vink(t, $event)" />
        <span class="titel">{{ t.titel }}</span>
      </label>
      <span class="mo">
        <template v-if="t.tappunt_snelstart">{{ WINKEL[t.tappunt_snelstart] || t.tappunt_snelstart }} · </template>
        <template v-if="auth.isKantoor && t.am_id">{{ AM_NAAM[t.am_id] || 'AM' }} · </template>
        <template v-if="t.deadline"><b :class="{ rood: t.deadline < vandaag }">{{ t.deadline }}</b></template>
        <template v-else>geen deadline</template>
      </span>
    </div>
    <p v-if="!open.length && !fout" class="stil">Niets open — lekker bezig. 🎉</p>

    <details v-if="klaar.length" class="hist">
      <summary>Afgerond ({{ klaar.length }})</summary>
      <div v-for="t in klaar" :key="t.id" class="kaart item af" data-test="taak-klaar">
        <label class="chk">
          <input type="checkbox" :checked="true" @change="vink(t, $event)" />
          <span class="titel door">{{ t.titel }}</span>
        </label>
      </div>
    </details>
  </div>
</template>

<style scoped>
h1{margin:0 0 4px;font-size:22px}
h2{font-size:15px;margin:16px 0 8px}
.sub{color:var(--grey);margin:0 0 14px;font-size:13.5px}
.kaart{background:#fff;border:1px solid var(--line);border-radius:14px;padding:14px 16px;margin-bottom:8px}
.nieuw{display:flex;flex-direction:column;gap:10px;margin-bottom:14px}
.rij{display:flex;gap:12px;flex-wrap:wrap}
label{display:flex;flex-direction:column;gap:5px;font-size:12.5px;font-weight:700;color:var(--grey);flex:1;min-width:150px}
select,input[type=text],input[type=date],input:not([type]){padding:9px 11px;border:1.5px solid var(--line);border-radius:10px;font-size:14px;font-family:inherit}
select:focus,input:focus{border-color:var(--coral)}
.btn{align-self:flex-start;background:var(--coral);color:#fff;border:0;border-radius:10px;padding:9px 16px;font-weight:800;cursor:pointer}
.btn:disabled{opacity:.6}
.item{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.item.laat{border-color:#e8b04b}
.chk{display:flex;align-items:center;gap:10px;flex-direction:row;font-weight:400;flex:1;min-width:200px}
.chk input{width:18px;height:18px;accent-color:var(--coral)}
.titel{font-size:14.5px;font-weight:700;color:var(--ink)}
.titel.door{text-decoration:line-through;color:var(--grey)}
.mo{color:var(--grey);font-size:12.5px;margin-left:auto}
.rood{color:#b3261e}
.item.af{opacity:.75}
.hist{margin-top:14px}
.hist summary{cursor:pointer;font-size:13px;color:var(--grey);font-weight:700;margin-bottom:8px}
.fout{color:#b3261e}
.stil{color:var(--grey)}
</style>
