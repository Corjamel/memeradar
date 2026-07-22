<script setup>
// Acties — netwerkbrede campagnes met het volledige v71-actiedetail:
// deelname (winkel of AM meldt aan), na afloop de feedbackronde
// (werkte het: ja/deels/nee + toelichting) en automatische actiepunten
// die meetellen in de beloningen.
import { computed, onMounted, reactive, ref } from 'vue'
import { useAuth } from '../../../stores/auth.js'
import { useTappunten } from '../../tappunten/store.js'
import { haalActies, bewaarActies, isActief } from '../api.js'
import { doetMee, heeftRes, zetDeelname, actieResSave, actieResStats, videoEmbedUrl } from '../logic.js'
import { checkBeloningen } from '../../beloningen/logic.js'
import { haalRekenConfig } from '../../beloningen/api.js'

const auth = useAuth()
const st = useTappunten()
const alle = ref([])
const marge = ref(1)
const fout = ref('')
const melding = ref('')
const bezig = ref(false)
const vandaag = new Date().toISOString().slice(0, 10)
const nieuw = reactive({ titel: '', omschrijving: '', start: '', eind: '', punten: '', video: '', materialen: '' })
const fb = reactive({})          // feedback-invoer per actie(+winkel): { key: {werkte,tekst} }

const actief = computed(() => alle.value.filter(a => isActief(a)))
// Afgelopen acties waar nog feedback openstaat bij een zichtbare winkel.
const feedbackDue = computed(() => alle.value.filter(a =>
  !a.archived && a.eind && a.eind < vandaag &&
  st.items.some(t => doetMee(t, a.id) && !heeftRes(t, a.id))))
const eigen = computed(() => auth.isPartner ? (st.items[0] || null) : null)
// Afgelopen acties met minstens één geregistreerd resultaat (AM/kantoor-analyse).
const afgelopen = computed(() => alle.value.filter(a =>
  !a.archived && a.eind && a.eind < vandaag && actieResStats(st.items, a.id).afgerond > 0))

async function laad() {
  fout.value = ''
  try {
    alle.value = await haalActies()
    if (!st.items.length) await st.laad()
    // Partner: gezien = melding weg (v71 actiesGezienP).
    if (eigen.value) {
      const gz = eigen.value.actiesGezienP || []
      const nw = actief.value.map(a => a.id).filter(id => !gz.includes(id))
      if (nw.length) await st.bewaar({ ...eigen.value, actiesGezienP: [...gz, ...nw] })
    }
  } catch (e) { fout.value = 'Kon acties niet laden: ' + e.message }
}
onMounted(async () => {
  await laad()
  try { marge.value = (await haalRekenConfig()).marge } catch { /* factor 1 */ }
})

async function toevoegen() {
  if (bezig.value) return
  if (!nieuw.titel.trim()) { fout.value = 'Geef de actie een titel.'; return }
  bezig.value = true; fout.value = ''
  try {
    const arr = [{
      id: 'act-' + Date.now(), titel: nieuw.titel.trim(), omschrijving: nieuw.omschrijving.trim(),
      start: nieuw.start || null, eind: nieuw.eind || null,
      punten: Math.max(0, +nieuw.punten || 0), video: nieuw.video.trim(), materialen: nieuw.materialen.trim(),
      archived: false
    }, ...alle.value]
    await bewaarActies(arr)
    Object.assign(nieuw, { titel: '', omschrijving: '', start: '', eind: '', punten: '', video: '', materialen: '' })
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

async function bewaar(t2) {
  bezig.value = true; fout.value = ''
  try { await st.bewaar(t2) } catch (e) { fout.value = 'Opslaan mislukt: ' + e.message }
  bezig.value = false
}

async function deelname(t, a, aan) {
  await bewaar(zetDeelname(t, a.id, aan, auth.isPartner ? 'partner' : 'am'))
}

/* Feedback opslaan; toegekende punten kunnen een beloning vrijspelen. */
async function feedback(t, a, key) {
  const inv = fb[key] || {}
  if (!inv.werkte) { fout.value = 'Kies eerst of de actie gewerkt heeft.'; return }
  const res = actieResSave(t, a, inv.werkte, inv.tekst, auth.isPartner ? 'partner' : 'am')
  if (!res) return
  let t2 = res.t2
  const uit = checkBeloningen(t2, marge.value)
  if (uit) t2 = uit.t2
  await bewaar(t2)
  melding.value = `✓ Feedback opgeslagen${res.punten ? ` — +${res.punten} actiepunten toegekend` : ''}`
  delete fb[key]
}

function stats(a) { return actieResStats(st.items, a.id) }
function meeTelling(a) { return st.items.filter(t => doetMee(t, a.id)).length }
function video(a) { return videoEmbedUrl(a.video) }
</script>

<template>
  <div>
    <h1>Acties</h1>
    <p class="sub" v-if="auth.isKantoor">Netwerkbrede campagnes — met deelname, feedbackronde en actiepunten.</p>
    <p class="sub" v-else-if="auth.isPartner">Doe mee met de lopende campagnes — na afloop vertel je kort of het werkte en verdien je actiepunten.</p>
    <p class="sub" v-else>Rol campagnes uit bij je winkels en vul na afloop de feedback in.</p>
    <p v-if="fout" class="fout" role="alert">{{ fout }}</p>
    <p v-if="melding" class="melding" role="status" data-test="actie-melding">{{ melding }}</p>

    <!-- Kantoor: nieuwe actie -->
    <form v-if="auth.magActiesBeheren" class="kaart nieuw" @submit.prevent="toevoegen">
      <label>Titel<input v-model="nieuw.titel" required placeholder="Bijv. Zomeractie 2026" data-test="actie-titel" /></label>
      <label>Omschrijving<textarea v-model="nieuw.omschrijving" rows="2" placeholder="Wat houdt de actie in?"></textarea></label>
      <div class="rij">
        <label>Start<input v-model="nieuw.start" type="date" /></label>
        <label>Einde<input v-model="nieuw.eind" type="date" /></label>
        <label>Actiepunten<input v-model="nieuw.punten" type="number" min="0" placeholder="0" data-test="actie-punten" /></label>
      </div>
      <div class="rij">
        <label>Actievideo (YouTube/Vimeo)<input v-model="nieuw.video" placeholder="https://youtu.be/…" /></label>
        <label>Materialen<input v-model="nieuw.materialen" placeholder="poster, flyers, social-post…" /></label>
      </div>
      <button class="btn" type="submit" :disabled="bezig" data-test="actie-toevoegen">{{ bezig ? 'Bezig…' : 'Actie plaatsen' }}</button>
    </form>

    <!-- Feedbackronde: afgelopen acties met openstaand resultaat -->
    <template v-for="a in feedbackDue" :key="'fb' + a.id">
      <div class="kaart fbdue" data-test="feedback-due">
        <b>📊 «{{ a.titel }}» is afgelopen — hoe werkte het?</b>
        <template v-for="t in st.items" :key="t.snelstart">
          <div v-if="doetMee(t, a.id) && !heeftRes(t, a.id)" class="fbrij" :data-test="'fb-' + t.snelstart + '-' + a.id">
            <b v-if="!auth.isPartner">{{ t.name }}</b>
            <select v-model="(fb[a.id + t.snelstart] ||= {}).werkte" :data-test="'fb-werkte-' + t.snelstart">
              <option disabled :value="undefined">werkte het?</option>
              <option value="ja">✓ Ja, werkte goed</option>
              <option value="deels">± Deels</option>
              <option value="nee">✗ Nee</option>
            </select>
            <input v-model="(fb[a.id + t.snelstart] ||= {}).tekst" placeholder="korte toelichting (optioneel)" class="lang" />
            <button class="klein" type="button" :disabled="bezig" :data-test="'fb-opslaan-' + t.snelstart"
                    @click="feedback(t, a, a.id + t.snelstart)">Opslaan{{ +a.punten > 0 ? ` (+${a.punten} ptn)` : '' }}</button>
          </div>
        </template>
      </div>
    </template>

    <!-- Resultaat-analyse afgelopen acties (AM/kantoor) -->
    <div v-if="!auth.isPartner && afgelopen.length" class="kaart">
      <b>📊 Resultaten afgelopen acties</b>
      <div v-for="a in afgelopen" :key="'st' + a.id" class="statrij" :data-test="'stats-' + a.id">
        <b>{{ a.titel }}</b>
        <span class="mo">{{ stats(a).afgerond }} afgerond · {{ stats(a).ja }}× ja · {{ stats(a).deels }}× deels · {{ stats(a).nee }}× nee · {{ stats(a).punten }} punten uitgekeerd</span>
        <details v-if="stats(a).fb.length" class="fbdetail">
          <summary>feedback ({{ stats(a).fb.length }})</summary>
          <p v-for="f in stats(a).fb" :key="f.tn + f.at" class="mo">
            <b>{{ f.tn }}</b> — {{ f.werkte }}<template v-if="f.tekst">: «{{ f.tekst }}»</template> · {{ f.at }}
          </p>
        </details>
      </div>
    </div>

    <p v-if="!actief.length && !fout" class="stil">Geen lopende acties.</p>
    <div v-for="a in actief" :key="a.id" class="kaart item" data-test="actie">
      <div class="itemkop">
        <b>📣 {{ a.titel }}</b>
        <span v-if="+a.punten > 0" class="chip" data-test="actie-chip-punten">+{{ a.punten }} punten</span>
        <span class="meta" v-if="a.start || a.eind">{{ a.start || '…' }} t/m {{ a.eind || '…' }}</span>
        <span v-if="!auth.isPartner" class="meta" data-test="actie-mee">{{ meeTelling(a) }}/{{ st.items.length }} doen mee</span>
        <button v-if="auth.magActiesBeheren" class="archief" type="button" data-test="actie-archiveer" @click="archiveer(a)">archiveer</button>
      </div>
      <p v-if="a.omschrijving" class="txt">{{ a.omschrijving }}</p>
      <p v-if="a.materialen" class="mo">🧰 Materialen: {{ a.materialen }}</p>
      <iframe v-if="video(a)?.embed" :src="video(a).embed" title="Actievideo" class="video" allowfullscreen loading="lazy"></iframe>
      <a v-else-if="video(a)?.link" class="klein" :href="video(a).link" target="_blank" rel="noopener noreferrer">▶ Bekijk actievideo →</a>

      <!-- Deelname: partner voor de eigen winkel, AM/kantoor per winkel -->
      <div v-if="auth.isPartner && eigen" class="deelname">
        <span v-if="doetMee(eigen, a.id)" class="badge groen" data-test="mee-badge">✓ Jullie doen mee!</span>
        <button v-else class="btn" type="button" :disabled="bezig" :data-test="'meedoen-' + a.id"
                @click="deelname(eigen, a, true)">✋ Wij doen mee</button>
      </div>
      <details v-else-if="st.items.length" class="uitrol">
        <summary>Uitrollen per winkel ({{ meeTelling(a) }}/{{ st.items.length }})</summary>
        <label v-for="t in st.items" :key="t.snelstart" class="winkelrij">
          <input type="checkbox" :checked="doetMee(t, a.id)" :disabled="bezig || heeftRes(t, a.id)"
                 :data-test="'mee-' + t.snelstart + '-' + a.id"
                 @change="deelname(t, a, $event.target.checked)" />
          <span>{{ t.name }}</span>
          <span v-if="doetMee(t, a.id)" class="mo">sinds {{ t.actieDeelname[a.id].at }}{{ t.actieDeelname[a.id].by === 'partner' ? ' · zelf aangemeld' : '' }}</span>
        </label>
      </details>
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
input,textarea,select{padding:9px 11px;border:1.5px solid var(--line);border-radius:10px;font-size:14px;font-family:inherit}
input:focus,textarea:focus,select:focus{border-color:var(--coral)}
.btn{align-self:flex-start;background:var(--coral);color:#fff;border:0;border-radius:10px;padding:9px 16px;font-weight:800;cursor:pointer}
.btn:disabled{opacity:.6}
.itemkop{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.chip{background:var(--soft);color:var(--coral-d);font-size:11px;font-weight:800;border-radius:999px;padding:3px 10px}
.meta{color:var(--grey);font-size:12.5px}
.archief{margin-left:auto;background:none;border:1.5px solid var(--line);border-radius:8px;padding:4px 10px;font-size:12px;font-weight:700;color:var(--grey);cursor:pointer}
.archief:hover{border-color:var(--coral);color:var(--coral)}
.txt{margin:8px 0 0;font-size:14px}
.mo{color:var(--grey);font-size:12.5px;margin:6px 0 0}
.video{width:100%;aspect-ratio:16/9;border:0;border-radius:12px;margin-top:10px}
.deelname{margin-top:10px}
.badge{font-size:11.5px;font-weight:800;border-radius:6px;padding:3px 10px}
.badge.groen{background:var(--green-soft);color:#2c5a12}
.uitrol{margin-top:10px;border-top:1px solid var(--line);padding-top:8px}
.uitrol summary{cursor:pointer;font-size:13px;color:var(--grey);font-weight:700}
.winkelrij{display:flex;flex-direction:row;align-items:center;gap:9px;padding:6px 0;border-bottom:1px solid var(--line);font-size:13.5px;cursor:pointer;font-weight:400;color:var(--ink)}
.winkelrij:last-child{border-bottom:0}
.winkelrij input{width:16px;height:16px;accent-color:var(--coral)}
.winkelrij .mo{margin:0 0 0 auto}
.fbdue{border-left:4px solid var(--amber)}
.fbrij{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:10px}
.fbrij .lang{flex:1;min-width:170px}
.klein{background:none;border:1.5px solid var(--line);border-radius:8px;padding:6px 12px;font-size:12.5px;font-weight:700;color:var(--grey);cursor:pointer;text-decoration:none;display:inline-block;margin-top:8px}
.klein:hover{border-color:var(--coral);color:var(--coral-d)}
.fout{color:#b3261e}
.melding{color:#2c5a12;font-size:13px}
.stil{color:var(--grey)}
</style>
