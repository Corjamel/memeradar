<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useTappunten } from '../store.js'
import { useAuth } from '../../../stores/auth.js'
import DocumentenBlok from '../../documenten/components/DocumentenBlok.vue'
import ContactenBlok from '../../contacten/components/ContactenBlok.vue'
import KassaBlok from '../../kassa/components/KassaBlok.vue'
import SetupBlok from '../../setup/components/SetupBlok.vue'
import PuntenBlok from '../../punten/components/PuntenBlok.vue'
import BeloningBlok from '../../beloningen/components/BeloningBlok.vue'
import BestellingenBlok from '../../bestellingen/components/BestellingenBlok.vue'
import LogboekBlok from '../../logboek/components/LogboekBlok.vue'
import SituatieBlok from '../components/SituatieBlok.vue'
import { haalRekenConfig } from '../../beloningen/api.js'
import VerkoopBlok from '../../verkoop/components/VerkoopBlok.vue'

const props = defineProps({ code: { type: String, required: true } })
const st = useTappunten()
const auth = useAuth()

const vorm = reactive({ snelstart: '', name: '', contact: '', tel: '', email: '', adres: '', plaats: '' })
const bron = ref(null)
const melding = ref('')
const bezig = ref(false)
const marge = ref(1)

function vulVorm(t) {
  bron.value = t
  Object.assign(vorm, {
    snelstart: t.snelstart || '', name: t.name || '', contact: t.contact || '',
    tel: t.tel || '', email: t.email || '', adres: t.adres || '', plaats: t.plaats || ''
  })
}

onMounted(async () => {
  if (!st.items.length) await st.laad()
  const t = st.byCode(props.code)
  if (t) vulVorm(t)
  try { marge.value = (await haalRekenConfig()).marge } catch { /* factor 1 */ }
})

async function opslaan() {
  if (bezig.value || !bron.value) return
  bezig.value = true; melding.value = ''
  try {
    // beschermde velden (geblokkeerd/am_id) blijven van de bron — api stuurt ze nooit mee
    const t = { ...bron.value, ...vorm, snelstart: bron.value.snelstart }
    await st.bewaar(t)
    bron.value = t
    melding.value = '✓ Opgeslagen'
  } catch (e) { melding.value = 'Opslaan mislukt: ' + e.message }
  bezig.value = false
}

async function wisselBlokkade() {
  if (!bron.value) return
  try {
    await st.blokkade(bron.value.snelstart, !bron.value.geblokkeerd)
    bron.value = st.byCode(bron.value.snelstart)
    melding.value = bron.value.geblokkeerd ? 'Winkel geblokkeerd.' : 'Winkel gedeblokkeerd.'
  } catch (e) { melding.value = 'Actie mislukt: ' + e.message }
}
</script>

<template>
  <div v-if="!bron" class="stil">
    <p>Winkel «{{ props.code }}» niet gevonden (of je hebt er geen toegang toe).</p>
    <router-link :to="{ name: 'winkels' }">← Terug naar winkels</router-link>
  </div>

  <div v-else>
    <router-link class="terug" :to="{ name: 'winkels' }">← Winkels</router-link>
    <div class="kaart">
      <div class="kop">
        <h1>{{ bron.name }}</h1>
        <span class="code">code {{ bron.snelstart }}</span>
        <span v-if="bron.geblokkeerd" class="badge" data-test="blok-badge">geblokkeerd</span>
      </div>

      <form class="vorm" @submit.prevent="opslaan">
        <label>Winkelnaam<input v-model="vorm.name" required /></label>
        <label>Contactpersoon<input v-model="vorm.contact" /></label>
        <label>Telefoon<input v-model="vorm.tel" type="tel" /></label>
        <label>E-mail<input v-model="vorm.email" type="email" /></label>
        <label>Adres<input v-model="vorm.adres" /></label>
        <label>Plaats<input v-model="vorm.plaats" /></label>

        <div class="acties">
          <button class="btn" type="submit" :disabled="bezig">{{ bezig ? 'Bezig…' : 'Opslaan' }}</button>
          <button v-if="auth.isKantoor" class="btn donker" type="button" data-test="blok-knop" @click="wisselBlokkade">
            {{ bron.geblokkeerd ? 'Deblokkeer winkel' : 'Blokkeer winkel' }}
          </button>
          <span v-if="melding" class="melding" role="status">{{ melding }}</span>
        </div>
      </form>
    </div>

    <SituatieBlok v-if="!auth.isPartner" :tappunt="bron" :marge="marge" @bijgewerkt="bron = $event" />
    <SetupBlok :tappunt="bron" @bijgewerkt="bron = $event" />
    <KassaBlok :tappunt="bron" @bijgewerkt="bron = $event" />
    <VerkoopBlok :tappunt="bron" @bijgewerkt="bron = $event" />
    <PuntenBlok :tappunt="bron" @bijgewerkt="bron = $event" />
    <BeloningBlok :tappunt="bron" @bijgewerkt="bron = $event" />
    <BestellingenBlok :tappunt="bron" @bijgewerkt="bron = $event" />
    <LogboekBlok :tappunt="bron" @bijgewerkt="bron = $event" />
    <ContactenBlok :snelstart="bron.snelstart" />
    <DocumentenBlok :snelstart="bron.snelstart" />
  </div>
</template>

<style scoped>
.terug{display:inline-block;margin-bottom:10px;color:var(--coral);font-weight:700;text-decoration:none}
.kaart{background:#fff;border:1px solid var(--line);border-radius:16px;padding:22px}
.kop{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:14px}
h1{margin:0;font-size:20px}
.code{color:var(--grey);font-size:13px}
.badge{background:#333;color:#fff;font-size:11px;font-weight:700;border-radius:6px;padding:2px 8px}
.vorm{display:grid;grid-template-columns:1fr 1fr;gap:12px}
label{display:flex;flex-direction:column;gap:5px;font-size:12.5px;font-weight:700;color:var(--grey)}
input{padding:9px 11px;border:1.5px solid var(--line);border-radius:10px;font-size:14px}
input:focus{border-color:var(--coral)}
.acties{grid-column:1 / -1;display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-top:6px}
.btn{background:var(--coral);color:#fff;border:0;border-radius:10px;padding:10px 16px;font-weight:800;cursor:pointer}
.btn.donker{background:#333}
.btn:disabled{opacity:.6}
.melding{font-size:13px;color:var(--grey)}
.stil{color:var(--grey)}
@media (max-width:640px){ .vorm{grid-template-columns:1fr} }
</style>
