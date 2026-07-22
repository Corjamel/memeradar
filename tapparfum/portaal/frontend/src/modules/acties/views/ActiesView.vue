<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useAuth } from '../../../stores/auth.js'
import { haalActies, bewaarActies, isActief } from '../api.js'

const auth = useAuth()
const alle = ref([])
const fout = ref('')
const bezig = ref(false)
const nieuw = reactive({ titel: '', omschrijving: '', start: '', eind: '' })

const actief = computed(() => alle.value.filter(a => isActief(a)))

async function laad() {
  fout.value = ''
  try { alle.value = await haalActies() }
  catch (e) { fout.value = 'Kon acties niet laden: ' + e.message }
}
onMounted(laad)

async function toevoegen() {
  if (bezig.value) return
  if (!nieuw.titel.trim()) { fout.value = 'Geef de actie een titel.'; return }
  bezig.value = true; fout.value = ''
  try {
    const arr = [{ id: 'act-' + Date.now(), titel: nieuw.titel.trim(), omschrijving: nieuw.omschrijving.trim(), start: nieuw.start || null, eind: nieuw.eind || null, archived: false }, ...alle.value]
    await bewaarActies(arr)
    nieuw.titel = ''; nieuw.omschrijving = ''; nieuw.start = ''; nieuw.eind = ''
    await laad()
  } catch (e) { fout.value = 'Opslaan mislukt: ' + e.message }
  bezig.value = false
}

async function archiveer(a) {
  try {
    const arr = alle.value.map(x => x.id === a.id ? { ...x, archived: true } : x)
    await bewaarActies(arr); await laad()
  } catch (e) { fout.value = 'Archiveren mislukt: ' + e.message }
}
</script>

<template>
  <div>
    <h1>Acties</h1>
    <p class="sub" v-if="auth.isKantoor">Netwerkbrede campagnes — direct zichtbaar voor alle accountmanagers en winkels.</p>
    <p class="sub" v-else>Lopende campagnes vanuit TapParfum.</p>
    <p v-if="fout" class="fout" role="alert">{{ fout }}</p>

    <!-- Kantoor: nieuwe actie -->
    <form v-if="auth.isKantoor" class="kaart nieuw" @submit.prevent="toevoegen">
      <label>Titel<input v-model="nieuw.titel" required placeholder="Bijv. Zomeractie 2026" data-test="actie-titel" /></label>
      <label>Omschrijving<textarea v-model="nieuw.omschrijving" rows="2" placeholder="Wat houdt de actie in?"></textarea></label>
      <div class="rij">
        <label>Start<input v-model="nieuw.start" type="date" /></label>
        <label>Einde<input v-model="nieuw.eind" type="date" /></label>
      </div>
      <button class="btn" type="submit" :disabled="bezig" data-test="actie-toevoegen">{{ bezig ? 'Bezig…' : 'Actie plaatsen' }}</button>
    </form>

    <p v-if="!actief.length && !fout" class="stil">Geen lopende acties.</p>
    <div v-for="a in actief" :key="a.id" class="kaart item" data-test="actie">
      <div class="itemkop">
        <b>📣 {{ a.titel }}</b>
        <span class="meta" v-if="a.start || a.eind">{{ a.start || '…' }} t/m {{ a.eind || '…' }}</span>
        <button v-if="auth.isKantoor" class="archief" type="button" data-test="actie-archiveer" @click="archiveer(a)">archiveer</button>
      </div>
      <p v-if="a.omschrijving" class="txt">{{ a.omschrijving }}</p>
    </div>
  </div>
</template>

<style scoped>
h1{margin:0 0 4px;font-size:22px}
.sub{color:var(--grey);margin:0 0 14px;font-size:13.5px}
.kaart{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px;margin-bottom:12px}
.nieuw{display:flex;flex-direction:column;gap:10px}
.rij{display:flex;gap:12px;flex-wrap:wrap}
label{display:flex;flex-direction:column;gap:5px;font-size:12.5px;font-weight:700;color:var(--grey);flex:1;min-width:140px}
input,textarea{padding:9px 11px;border:1.5px solid var(--line);border-radius:10px;font-size:14px;font-family:inherit}
input:focus,textarea:focus{border-color:var(--coral)}
.btn{align-self:flex-start;background:var(--coral);color:#fff;border:0;border-radius:10px;padding:9px 16px;font-weight:800;cursor:pointer}
.btn:disabled{opacity:.6}
.itemkop{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.meta{color:var(--grey);font-size:12.5px}
.archief{margin-left:auto;background:none;border:1.5px solid var(--line);border-radius:8px;padding:4px 10px;font-size:12px;font-weight:700;color:var(--grey);cursor:pointer}
.archief:hover{border-color:var(--coral);color:var(--coral)}
.txt{margin:8px 0 0;font-size:14px}
.fout{color:#b3261e}
.stil{color:var(--grey)}
</style>
