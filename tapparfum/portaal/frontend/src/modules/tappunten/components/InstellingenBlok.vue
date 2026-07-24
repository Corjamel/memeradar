<script setup>
// Operationele instellingen bij één winkel (v71 instellingen-blok r.2805) —
// AM/kantoor. De live-datum voedt het maandtempo, de projectie en de
// break-even-streefdatum; het pakket legt vast waarmee de winkel gestart is;
// de notities zijn interne werkaantekeningen (t.notes). Partner ziet dit niet.
import { reactive, ref, watch } from 'vue'
import { useTappunten } from '../store.js'
import { PKG } from '../../calculator/logic.js'

const props = defineProps({ tappunt: { type: Object, required: true } })
const emit = defineEmits(['bijgewerkt'])
const st = useTappunten()
const bezig = ref(false)
const melding = ref('')
const fout = ref('')
const vorm = reactive({ liveDate: '', pkg: '', notes: '' })

function vul(t) {
  vorm.liveDate = t.liveDate || ''
  vorm.pkg = (t.pkg === 0 || t.pkg) ? String(t.pkg) : ''
  vorm.notes = t.notes || ''
}
vul(props.tappunt)
watch(() => props.tappunt, vul)

async function opslaan() {
  if (bezig.value) return
  bezig.value = true; melding.value = ''; fout.value = ''
  try {
    const t2 = {
      ...props.tappunt,
      liveDate: vorm.liveDate || '',
      pkg: vorm.pkg === '' ? null : Number(vorm.pkg),
      notes: vorm.notes || ''
    }
    await st.bewaar(t2)
    emit('bijgewerkt', t2)
    melding.value = '✓ Instellingen opgeslagen'
  } catch (e) { fout.value = 'Opslaan mislukt: ' + e.message }
  bezig.value = false
}
</script>

<template>
  <section class="blok" data-test="instellingen">
    <h2>⚙️ Instellingen</h2>
    <p v-if="fout" class="fout" role="alert">{{ fout }}</p>
    <div class="grid">
      <label>Live sinds
        <input v-model="vorm.liveDate" type="date" data-test="inst-live" />
      </label>
      <label>Startpakket
        <select v-model="vorm.pkg" data-test="inst-pkg">
          <option value="">— geen —</option>
          <option v-for="(p, i) in PKG" :key="i" :value="String(i)">{{ p.n }}</option>
        </select>
      </label>
      <label class="breed">Operationele notities (intern)
        <textarea v-model="vorm.notes" rows="2" placeholder="Interne aantekeningen over deze winkel…" data-test="inst-notes"></textarea>
      </label>
    </div>
    <div class="acties">
      <button class="knop" type="button" :disabled="bezig" data-test="inst-opslaan" @click="opslaan">{{ bezig ? 'Bezig…' : 'Instellingen opslaan' }}</button>
      <router-link :to="{ name: 'formulieren' }" class="lnk">→ Formulieren</router-link>
      <span v-if="melding" class="ok" role="status" data-test="inst-melding">{{ melding }}</span>
    </div>
  </section>
</template>

<style scoped>
.blok{background:#fff;border:1px solid var(--line);padding:18px 22px;margin-top:14px}
h2{margin:0 0 12px;font-size:16px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.breed{grid-column:1 / -1}
label{display:flex;flex-direction:column;gap:5px;font-size:12.5px;font-weight:700;color:var(--grey)}
input,select,textarea{padding:9px 11px;border:1.5px solid var(--line);font-size:14px;font-family:inherit}
input:focus,select:focus,textarea:focus{border-color:var(--coral);outline:none}
.acties{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin-top:12px}
.knop{background:var(--coral);color:#fff;border:0;padding:9px 16px;font-weight:800;cursor:pointer;text-transform:uppercase;letter-spacing:.4px}
.knop:disabled{opacity:.6}
.lnk{color:var(--coral);font-weight:700;text-decoration:none;font-size:13px}
.lnk:hover{text-decoration:underline}
.ok{color:#2c5a12;font-size:13px}
.fout{color:#b3261e;font-size:13px}
@media(max-width:620px){.grid{grid-template-columns:1fr}}
</style>
