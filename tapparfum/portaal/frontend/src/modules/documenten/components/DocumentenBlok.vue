<script setup>
// Documenten bij één winkel: lijst + upload + openen via tijdelijke link.
// Hoort thuis op de winkel-detailpagina.
import { onMounted, ref } from 'vue'
import { lijstDocumenten, uploadDocument, openLink } from '../api.js'

const props = defineProps({ snelstart: { type: String, required: true } })
const docs = ref([])
const fout = ref('')
const bezig = ref(false)

function toonNaam(naam) {
  // opslagnaam is "<tijdstempel>_<originele naam>"
  const i = naam.indexOf('_')
  return i > 0 ? naam.slice(i + 1) : naam
}

async function laad() {
  fout.value = ''
  try { docs.value = await lijstDocumenten(props.snelstart) }
  catch (e) { fout.value = 'Kon documenten niet laden: ' + e.message }
}
onMounted(laad)

async function kies(ev) {
  const f = ev.target.files && ev.target.files[0]
  if (!f || bezig.value) return
  bezig.value = true; fout.value = ''
  try { await uploadDocument(props.snelstart, f); await laad() }
  catch (e) { fout.value = 'Upload mislukt: ' + e.message }
  bezig.value = false
  ev.target.value = ''
}

async function open(naam) {
  try {
    const url = await openLink(props.snelstart, naam)
    window.open(url, '_blank', 'noopener')
  } catch (e) { fout.value = 'Openen mislukt: ' + e.message }
}
</script>

<template>
  <section class="docs">
    <div class="kop">
      <h2>📎 Documenten</h2>
      <label class="upload">
        {{ bezig ? 'Bezig…' : '+ Upload' }}
        <input type="file" hidden data-test="doc-upload" :disabled="bezig" @change="kies" />
      </label>
    </div>
    <p v-if="fout" class="fout" role="alert">{{ fout }}</p>
    <p v-else-if="!docs.length" class="stil">Nog geen documenten. Bestanden zijn privé — alleen deze winkel, de accountmanager en kantoor kunnen erbij.</p>
    <ul v-else class="lijst">
      <li v-for="d in docs" :key="d.name" data-test="doc-item">
        <button class="doclink" @click="open(d.name)">{{ toonNaam(d.name) }}</button>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.docs{background:#fff;border:1px solid var(--line);border-radius:16px;padding:18px 22px;margin-top:14px}
.kop{display:flex;align-items:center;gap:12px}
h2{margin:0;font-size:16px;flex:1}
.upload{background:var(--coral);color:#fff;border-radius:10px;padding:8px 14px;font-weight:800;font-size:13px;cursor:pointer}
.lijst{list-style:none;margin:12px 0 0;padding:0;display:flex;flex-direction:column;gap:6px}
.doclink{background:none;border:0;color:var(--coral);font-weight:700;font-size:14px;cursor:pointer;padding:4px 0;text-align:left}
.doclink:hover{text-decoration:underline}
.fout{color:#b3261e;font-size:13px}
.stil{color:var(--grey);font-size:13px;margin:10px 0 0}
</style>
