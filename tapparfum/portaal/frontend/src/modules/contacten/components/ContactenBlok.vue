<script setup>
// Contactpersonen bij één winkel — blok op de winkel-detailpagina.
import { onMounted, reactive, ref } from 'vue'
import { useAuth } from '../../../stores/auth.js'
import { haalContacten, voegContactToe, verwijderContact } from '../api.js'

const props = defineProps({ snelstart: { type: String, required: true } })
const auth = useAuth()
const contacten = ref([])
const fout = ref('')
const bezig = ref(false)
const toon = ref(false)
const nieuw = reactive({ naam: '', functie: '', tel: '', email: '' })

async function laad() {
  fout.value = ''
  try { contacten.value = await haalContacten(props.snelstart) }
  catch (e) { fout.value = 'Kon contacten niet laden: ' + e.message }
}
onMounted(laad)

async function toevoegen() {
  if (bezig.value || !nieuw.naam.trim()) return
  bezig.value = true; fout.value = ''
  try {
    await voegContactToe({ tappunt_snelstart: props.snelstart, ...nieuw, naam: nieuw.naam.trim() })
    nieuw.naam = ''; nieuw.functie = ''; nieuw.tel = ''; nieuw.email = ''
    toon.value = false
    await laad()
  } catch (e) { fout.value = 'Opslaan mislukt: ' + e.message }
  bezig.value = false
}

async function weg(c) {
  try { await verwijderContact(c.id); await laad() }
  catch (e) { fout.value = 'Verwijderen mislukt: ' + e.message }
}
</script>

<template>
  <section class="blok">
    <div class="kop">
      <h2>👤 Contactpersonen</h2>
      <button class="knop" type="button" data-test="contact-nieuw" @click="toon = !toon">{{ toon ? 'Annuleer' : '+ Contact' }}</button>
    </div>
    <p v-if="fout" class="fout" role="alert">{{ fout }}</p>

    <form v-if="toon" class="vorm" @submit.prevent="toevoegen">
      <input v-model="nieuw.naam" required placeholder="Naam *" data-test="contact-naam" />
      <input v-model="nieuw.functie" placeholder="Functie" />
      <input v-model="nieuw.tel" type="tel" placeholder="Telefoon" />
      <input v-model="nieuw.email" type="email" placeholder="E-mail" />
      <button class="knop vol" type="submit" :disabled="bezig" data-test="contact-opslaan">{{ bezig ? 'Bezig…' : 'Opslaan' }}</button>
    </form>

    <p v-if="!contacten.length && !fout" class="stil">Nog geen contactpersonen vastgelegd.</p>
    <div v-for="c in contacten" :key="c.id" class="rij" data-test="contact-item">
      <b>{{ c.naam }}</b>
      <span class="mo">
        <template v-if="c.functie">{{ c.functie }}</template>
        <template v-if="c.tel"> · {{ c.tel }}</template>
        <template v-if="c.email"> · {{ c.email }}</template>
      </span>
      <button v-if="!auth.isPartner" class="weg" type="button" data-test="contact-verwijder" title="Verwijderen" @click="weg(c)">✕</button>
    </div>
  </section>
</template>

<style scoped>
.blok{background:#fff;border:1px solid var(--line);border-radius:16px;padding:18px 22px;margin-top:14px}
.kop{display:flex;align-items:center;gap:12px}
h2{margin:0;font-size:16px;flex:1}
.knop{background:var(--coral);color:#fff;border:0;border-radius:10px;padding:8px 14px;font-weight:800;font-size:13px;cursor:pointer}
.knop.vol{grid-column:1 / -1;justify-self:start}
.knop:disabled{opacity:.6}
.vorm{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:12px}
input{padding:9px 11px;border:1.5px solid var(--line);border-radius:10px;font-size:13.5px;font-family:inherit}
input:focus{outline:none;border-color:var(--coral)}
.rij{display:flex;align-items:center;gap:10px;padding:9px 0;border-bottom:1px solid var(--line);font-size:14px}
.rij:last-child{border-bottom:0}
.mo{color:var(--grey);font-size:12.5px;flex:1}
.weg{background:none;border:0;color:var(--grey);cursor:pointer;font-size:14px;padding:2px 6px}
.weg:hover{color:#b3261e}
.fout{color:#b3261e;font-size:13px}
.stil{color:var(--grey);font-size:13px;margin:10px 0 0}
@media (max-width:640px){ .vorm{grid-template-columns:1fr} }
</style>
