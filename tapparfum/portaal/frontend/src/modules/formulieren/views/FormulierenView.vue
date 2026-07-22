<script setup>
// Formulieren — de 7 v71-akkoord-/checklistformulieren. AM/kantoor vult ze
// samen met de ondernemer in; per winkel opgeslagen in t.forms. Kies eerst een
// winkel, dan een formulier; yes/no-vragen, keuzevragen en vrije velden.
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useTappunten } from '../../tappunten/store.js'
import { FORMS } from '../data.js'

const st = useTappunten()
const fout = ref('')
const melding = ref('')
const bezig = ref(false)
const winkel = ref('')
const formId = ref('')
const inv = reactive({})          // huidige invoer { veldKey: waarde }

const tappunt = computed(() => st.items.find(t => t.snelstart === winkel.value) || null)
const form = computed(() => FORMS.find(f => f.id === formId.value) || null)
// Compleetheid: hoeveel yes/no-vragen zijn beantwoord?
const jaNee = computed(() => {
  if (!form.value) return []
  const uit = []
  form.value.secties.forEach(s => (s.yesno || []).forEach(y => uit.push(y[0])))
  return uit
})
const beantwoord = computed(() => jaNee.value.filter(k => inv[k]).length)

onMounted(async () => {
  if (!st.items.length) await st.laad()
  if (st.items.length) winkel.value = st.items[0].snelstart
})

// Bij wisselen van winkel of formulier: laad de opgeslagen antwoorden.
function laadInvoer() {
  Object.keys(inv).forEach(k => delete inv[k])
  if (!tappunt.value || !form.value) return
  const opgeslagen = ((tappunt.value.forms || {})[form.value.id]) || {}
  Object.assign(inv, opgeslagen)
}
watch([winkel, formId], laadInvoer)

async function opslaan() {
  if (!tappunt.value || !form.value || bezig.value) return
  bezig.value = true; fout.value = ''; melding.value = ''
  try {
    const forms = { ...(tappunt.value.forms || {}), [form.value.id]: { ...inv } }
    const t2 = { ...tappunt.value, forms }
    await st.bewaar(t2)
    const i = st.items.findIndex(x => x.snelstart === t2.snelstart)
    if (i >= 0) st.items[i] = t2
    melding.value = '✓ Formulier opgeslagen'
  } catch (e) { fout.value = 'Opslaan mislukt: ' + e.message }
  bezig.value = false
}
</script>

<template>
  <div>
    <h1>📋 Formulieren</h1>
    <p class="sub">De officiële voorwaarden- en checklistformulieren — samen met de ondernemer invullen en vastleggen.</p>
    <p v-if="fout" class="fout" role="alert">{{ fout }}</p>

    <div class="kiezers">
      <label>Winkel
        <select v-model="winkel" data-test="form-winkel">
          <option v-for="t in st.items" :key="t.snelstart" :value="t.snelstart">{{ t.name }}</option>
        </select>
      </label>
      <label>Formulier
        <select v-model="formId" data-test="form-kies">
          <option value="">— kies een formulier —</option>
          <option v-for="f in FORMS" :key="f.id" :value="f.id">{{ f.naam }}</option>
        </select>
      </label>
    </div>

    <div v-if="form" class="kaart">
      <h2>{{ form.titel }}</h2>
      <p class="desc">{{ form.desc }}</p>
      <p v-if="jaNee.length" class="voortgang" data-test="form-voortgang">{{ beantwoord }}/{{ jaNee.length }} voorwaarden beantwoord</p>

      <section v-for="(s, si) in form.secties" :key="si" class="sectie">
        <h3>{{ s.t }}</h3>

        <!-- vrije velden -->
        <label v-for="v in (s.velden || [])" :key="v[1]" class="veld">
          {{ v[2] }}
          <textarea v-if="v[0] === 'textarea'" v-model="inv[v[1]]" rows="2" :data-test="'fv-' + v[1]"></textarea>
          <input v-else :type="v[0] === 'number' ? 'number' : (v[0] === 'date' ? 'date' : 'text')" v-model="inv[v[1]]" :data-test="'fv-' + v[1]" />
        </label>

        <!-- keuzevragen -->
        <div v-for="o in (s.opts || [])" :key="o[0]" class="opt">
          <span class="vraag">{{ o[1] }}</span>
          <div class="keuzes">
            <button v-for="keuze in o[2]" :key="keuze" class="keuze" :class="{ aan: inv[o[0]] === keuze }" type="button"
                    :data-test="'fo-' + o[0] + '-' + keuze" @click="inv[o[0]] = keuze">{{ keuze }}</button>
          </div>
        </div>

        <!-- yes/no -->
        <div v-for="y in (s.yesno || [])" :key="y[0]" class="yesno" :data-test="'fy-' + y[0]">
          <span class="vraag">{{ y[1] }}</span>
          <div class="jn">
            <button class="jbtn ja" :class="{ aan: inv[y[0]] === 'ja' }" type="button" :data-test="'fy-' + y[0] + '-ja'" @click="inv[y[0]] = 'ja'">Ja</button>
            <button class="jbtn nee" :class="{ aan: inv[y[0]] === 'nee' }" type="button" :data-test="'fy-' + y[0] + '-nee'" @click="inv[y[0]] = 'nee'">Nee</button>
          </div>
        </div>
      </section>

      <div class="acties">
        <button class="btn" type="button" :disabled="bezig" data-test="form-opslaan" @click="opslaan">{{ bezig ? 'Bezig…' : 'Formulier opslaan' }}</button>
        <span v-if="melding" class="melding" role="status" data-test="form-melding">{{ melding }}</span>
      </div>
    </div>
    <p v-else class="stil">Kies een formulier om te beginnen.</p>
  </div>
</template>

<style scoped>
h1{margin:0 0 4px;font-size:22px}
h2{margin:0 0 6px;font-size:17px}
h3{margin:16px 0 8px;font-size:12.5px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;color:var(--coral-d)}
.sub{color:var(--grey);margin:0 0 14px;font-size:13.5px}
.kiezers{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:14px}
.kiezers label{display:flex;flex-direction:column;gap:5px;font-size:12.5px;font-weight:700;color:var(--grey)}
select{padding:9px 11px;border:1.5px solid var(--line);border-radius:10px;font-size:14px;font-family:inherit;min-width:200px}
select:focus{border-color:var(--coral)}
.kaart{background:#fff;border:1px solid var(--line);border-radius:14px;padding:18px}
.desc{color:var(--grey);font-size:13px;margin:0 0 8px;line-height:1.5}
.voortgang{font-size:12.5px;font-weight:800;color:var(--coral-d);margin:0}
.sectie{border-top:1px solid var(--line);margin-top:8px;padding-top:4px}
.veld{display:flex;flex-direction:column;gap:5px;font-size:13px;font-weight:600;color:var(--ink);margin:10px 0}
.veld input,.veld textarea{padding:8px 10px;border:1.5px solid var(--line);border-radius:9px;font-size:14px;font-family:inherit;font-weight:400}
.veld input:focus,.veld textarea:focus{border-color:var(--coral)}
.opt,.yesno{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;padding:8px 0;border-bottom:1px solid var(--line)}
.vraag{flex:1;min-width:180px;font-size:13.5px;line-height:1.4}
.keuzes,.jn{display:flex;gap:6px;flex-wrap:wrap}
.keuze,.jbtn{border:1.5px solid var(--line);border-radius:8px;padding:6px 12px;font-size:12.5px;font-weight:700;background:#fff;color:var(--grey);cursor:pointer}
.keuze.aan{border-color:var(--coral);background:var(--soft);color:var(--coral-d)}
.jbtn.ja.aan{border-color:var(--green);background:var(--green-soft);color:#2c5a12}
.jbtn.nee.aan{border-color:var(--coral-d);background:#fdeee7;color:var(--coral-d)}
.acties{display:flex;align-items:center;gap:10px;margin-top:16px}
.btn{background:var(--coral);color:#fff;border:0;border-radius:10px;padding:10px 16px;font-weight:800;cursor:pointer}
.btn:disabled{opacity:.6}
.melding{color:#2c5a12;font-size:13px}
.fout{color:#b3261e}
.stil{color:var(--grey)}
</style>
