<script setup>
// TapParfum Academy — v71 (r.3371-3415): 6 cursussen, 28 lessen, voortgang in
// t.academy = { cursusKey: { lesIndex: true } }. Eerst leren, dan verdienen:
// de beloningen-engine eist per spaarcadeau de bijbehorende training, dus elke
// afgevinkte les kan een beloning vrijspelen (checkBeloningen draait mee).
import Icoon from '../../../components/Icoon.vue'
import { computed, onMounted, reactive, ref } from 'vue'
import { useAuth } from '../../../stores/auth.js'
import { useTappunten } from '../../tappunten/store.js'
import { COURSES, academyPct, checkBeloningen } from '../../beloningen/logic.js'
import { haalRekenConfig } from '../../beloningen/api.js'
import { LESINHOUD, ACADEMY_VIDEOS, videoCloudBron } from '../data.js'

const auth = useAuth()
const st = useTappunten()
const fout = ref('')
const bezig = ref(false)
const marge = ref(1)
const gekozen = ref('')          // AM/kantoor: snelstart van de gekozen winkel
const open = ref(null)           // cursuskey waarvan de lessen open staan
const openLes = ref('')          // 'cursuskey-lesindex' waarvan de lestekst open staat
const viering = ref('')

function lesStof(c, i) { return (LESINHOUD[c[0]] || [])[i] || null }
function toggleLes(c, i) {
  const k = c[0] + '-' + i
  openLes.value = openLes.value === k ? '' : k
}

/* Videotheek: alleen kijken (geen download-knop, nodownload in de speler).
   Ontbreekt het lokale bestand, dan schakelt de bron door naar Supabase. */
const vsrc = reactive({})
function vidFout(v) {
  const alt = videoCloudBron(v.src)
  if (alt && vsrc[v.src] !== alt) vsrc[v.src] = alt
}

const CAT_KLEUR = { Onboarding: '#f9c5af', Verkoop: '#bfe3fb', Tool: '#ecdfc6', Beleving: '#dcd9e8' }

onMounted(async () => {
  try {
    // Winkels en rekenconfig zijn onafhankelijk — parallel laden.
    const [, cfg] = await Promise.all([
      st.items.length ? Promise.resolve() : st.laad(),
      haalRekenConfig().catch(() => null)
    ])
    if (cfg) marge.value = cfg.marge
    if (!auth.isPartner && st.items.length) gekozen.value = st.items[0].snelstart
  } catch (e) { fout.value = 'Kon de Academy niet laden: ' + e.message }
})

const t = computed(() => auth.isPartner
  ? (st.items[0] || null)
  : (st.items.find(x => x.snelstart === gekozen.value) || null))

const TOTAAL = COURSES.reduce((a, c) => a + c[4].length, 0)
const gedaan = computed(() => {
  if (!t.value) return 0
  const ac = t.value.academy || {}
  return COURSES.reduce((a, c) => a + c[4].filter((_, i) => (ac[c[0]] || {})[i]).length, 0)
})
const overall = computed(() => TOTAAL ? Math.round(gedaan.value / TOTAAL * 100) : 0)

function lesAf(c, i) { return !!(((t.value.academy || {})[c[0]] || {})[i]) }
function cursusN(c) { const d = (t.value.academy || {})[c[0]] || {}; return c[4].filter((_, i) => d[i]).length }

/* v71 setAcademy: les togglen + meteen de beloningen-check draaien. */
async function vink(c, i, v) {
  if (bezig.value || !t.value) return
  bezig.value = true; fout.value = ''; viering.value = ''
  try {
    const academy = { ...(t.value.academy || {}) }
    academy[c[0]] = { ...(academy[c[0]] || {}), [i]: !!v }
    if (!v) delete academy[c[0]][i]
    let t2 = { ...t.value, academy }
    const uit = checkBeloningen(t2, marge.value)
    if (uit) { t2 = uit.t2; viering.value = uit.nieuw.map(n => n.r).join(' · ') }
    await st.bewaar(t2)
    if (auth.isPartner) st.items[0] = t2
    else { const idx = st.items.findIndex(x => x.snelstart === t2.snelstart); if (idx >= 0) st.items[idx] = t2 }
  } catch (e) { fout.value = 'Opslaan mislukt: ' + e.message }
  bezig.value = false
}
</script>

<template>
  <div>
    <!-- Held (v71: paarse Academy-banner) -->
    <header class="held">
      <div>
        <p class="eyebrow">TapParfum Academy</p>
        <h1>Word een geurexpert</h1>
        <p class="sub">Korte modules over verkoop, geurnoten en beleving. Je voortgang wordt bewaard{{ auth.isPartner ? '' : ' — per winkel' }}.</p>
      </div>
      <div v-if="t" class="stand">
        <div class="pct" data-test="academy-pct">{{ overall }}%</div>
        <div class="mo" data-test="academy-stand">{{ gedaan }}/{{ TOTAAL }} lessen</div>
      </div>
    </header>
    <p v-if="fout" class="fout" role="alert">{{ fout }}</p>

    <!-- AM/kantoor: winkel kiezen -->
    <label v-if="!auth.isPartner" class="kies">Winkel:
      <select v-model="gekozen" data-test="academy-winkel">
        <option v-for="w in st.items" :key="w.snelstart" :value="w.snelstart">{{ w.name }}</option>
      </select>
    </label>

    <div v-if="viering" class="viering" role="status" data-test="academy-viering">
      🎉 Training afgerond én beloning vrijgespeeld: <b>{{ viering }}</b>
    </div>

    <template v-if="t">
      <!-- Certificaat -->
      <div v-if="overall === 100" class="cert" data-test="academy-cert">
        <span class="vinkje">✓</span>
        <div><b>Academy-certificaat behaald</b>
          <p class="mo">Alle modules voltooid. Sterk werk — je bent nu TapParfum-geurexpert.</p></div>
      </div>

      <!-- Cursuskaarten -->
      <div class="grid">
        <div v-for="c in COURSES" :key="c[0]" class="cursus" data-test="cursus">
          <div class="kopband" :style="{ background: `linear-gradient(135deg, ${CAT_KLEUR[c[1]] || '#f3ddd2'}, #ffffffaa)` }">
            <span class="cat">{{ c[1] }} · {{ c[4].length }} lessen</span>
            <span class="rond">{{ academyPct(t, c[0]) === 100 ? '✓' : '▶' }}</span>
          </div>
          <div class="body">
            <b class="titel">{{ c[2] }}</b>
            <p class="mo">{{ c[3] }}</p>
            <div class="balk"><div class="vul" :class="{ af: academyPct(t, c[0]) === 100 }" :style="{ width: academyPct(t, c[0]) + '%' }"></div></div>
            <div class="voet">
              <span class="mo" :data-test="'cursus-stand-' + c[0]">{{ academyPct(t, c[0]) === 100 ? 'Voltooid ✓' : (cursusN(c) ? cursusN(c) + '/' + c[4].length + ' lessen' : 'Nog niet gestart') }}</span>
              <button class="klein" type="button" :data-test="'cursus-open-' + c[0]"
                      @click="open = open === c[0] ? null : c[0]">{{ open === c[0] ? 'Verberg' : 'Lessen →' }}</button>
            </div>
            <div v-if="open === c[0]" class="lessen">
              <div v-for="(les, i) in c[4]" :key="i" class="lesblok">
                <div class="les" :class="{ af: lesAf(c, i) }">
                  <input type="checkbox" :checked="lesAf(c, i)" :disabled="bezig"
                         :data-test="'les-' + c[0] + '-' + i" @change="vink(c, i, $event.target.checked)" />
                  <button v-if="lesStof(c, i)" class="lestitel" type="button"
                          :data-test="'les-open-' + c[0] + '-' + i" @click="toggleLes(c, i)">
                    {{ les }}<span class="pijl">{{ openLes === c[0] + '-' + i ? '▴' : '▾' }}</span>
                  </button>
                  <span v-else>{{ les }}</span>
                </div>
                <div v-if="openLes === c[0] + '-' + i && lesStof(c, i)" class="stof" :data-test="'les-stof-' + c[0] + '-' + i">
                  <p class="uitleg">{{ lesStof(c, i).d }}</p>
                  <ul>
                    <li v-for="p in lesStof(c, i).p" :key="p">{{ p }}</li>
                  </ul>
                  <p class="tip">💡 {{ lesStof(c, i).tip }}</p>
                  <button v-if="!lesAf(c, i)" class="klaar" type="button" :disabled="bezig"
                          :data-test="'les-klaar-' + c[0] + '-' + i" @click="vink(c, i, true); toggleLes(c, i)">
                    ✓ Les afronden
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
    <p v-else class="stil">Geen winkel gevonden.</p>

    <!-- Videotheek: de officiële merkvideo's — alleen kijken, niet downloaden -->
    <div class="vidkop">
      <div class="vt"><Icoon naam="video" /> Videotheek</div>
      <p class="vsub">De officiële TapParfum-video's bij je training — bekijk ze hier en gebruik wat je ziet op de winkelvloer.</p>
    </div>
    <div class="videos">
      <figure v-for="v in ACADEMY_VIDEOS" :key="v.src" class="vcard" data-test="academy-video">
        <video :src="vsrc[v.src] || v.src" controls controlslist="nodownload noremoteplayback" disablepictureinpicture
               preload="metadata" playsinline @error="vidFout(v)" @contextmenu.prevent></video>
        <figcaption>
          <b>{{ v.t }}</b><small>{{ v.cursus }}</small>
          <p>{{ v.sub }}</p>
        </figcaption>
      </figure>
    </div>
  </div>
</template>

<style scoped>
.held{display:flex;align-items:center;justify-content:space-between;gap:18px;flex-wrap:wrap;background:linear-gradient(125deg,#e6e2f2,#f1eef8);border-radius:18px;padding:20px 24px;margin-bottom:14px}
.eyebrow{margin:0;font-size:11px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:#6a5f93}
h1{margin:4px 0;font-size:22px;color:#3a2f5a}
.sub{color:#6a5f93;margin:0;font-size:13.5px}
.stand{text-align:center;min-width:110px}
.pct{font-size:34px;font-weight:900;color:var(--coral-d);line-height:1}
.mo{color:var(--grey);font-size:12.5px;margin:4px 0 0}
.kies{display:flex;align-items:center;gap:8px;font-size:13px;font-weight:700;color:var(--grey);margin-bottom:12px}
.kies select{padding:8px 10px;border:1.5px solid var(--line);border-radius:10px;font-size:13.5px;font-family:inherit}
.viering{background:var(--green-soft);border:1px solid #bcd9a0;color:#2c5a12;border-radius:12px;padding:10px 14px;margin-bottom:12px;font-size:13.5px}
.cert{display:flex;align-items:center;gap:14px;background:linear-gradient(120deg,var(--soft),#fff);border:1px solid var(--coral);border-radius:14px;padding:16px;margin-bottom:12px}
.vinkje{width:46px;height:46px;border-radius:14px;background:var(--coral);color:#fff;display:flex;align-items:center;justify-content:center;font-size:22px;flex-shrink:0}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:14px}
.cursus{background:#fff;border:1px solid var(--line);border-radius:16px;overflow:hidden;display:flex;flex-direction:column}
.kopband{height:74px;display:flex;align-items:flex-end;justify-content:space-between;padding:12px 16px}
.cat{font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.1em;color:#4a4238}
.rond{width:34px;height:34px;border-radius:50%;background:rgba(255,255,255,.9);display:flex;align-items:center;justify-content:center;color:var(--coral-d);font-size:15px}
.body{padding:14px 16px 16px;display:flex;flex-direction:column;flex:1}
.titel{font-size:15.5px;line-height:1.3}
.body .mo{min-height:34px;line-height:1.45;margin:6px 0 10px}
.balk{height:8px;border-radius:6px;background:#f0ebe3;overflow:hidden}
.vul{height:100%;background:var(--coral)}
.vul.af{background:var(--green)}
.voet{display:flex;justify-content:space-between;align-items:center;margin-top:10px}
.klein{background:none;border:1.5px solid var(--line);border-radius:8px;padding:5px 12px;font-size:12.5px;font-weight:700;color:var(--grey);cursor:pointer}
.klein:hover{border-color:var(--coral);color:var(--coral-d)}
.lessen{margin-top:12px;border-top:1px solid var(--line);padding-top:8px;display:flex;flex-direction:column}
.les{display:flex;align-items:flex-start;gap:9px;padding:6px 0;font-size:13.5px;cursor:pointer}
.les input{width:16px;height:16px;accent-color:var(--coral);margin-top:1px;flex-shrink:0}
.les.af span,.les.af .lestitel{color:var(--grey)}
.lestitel{background:none;border:0;padding:0;font:inherit;color:inherit;cursor:pointer;text-align:left;display:flex;align-items:center;gap:6px}
.lestitel:hover{color:var(--coral-d)}
.lestitel .pijl{color:var(--coral-d);font-size:11px}
.stof{background:var(--cream);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin:2px 0 8px 25px;font-size:12.5px;line-height:1.55}
.stof .uitleg{margin:0 0 8px}
.stof ul{margin:0 0 8px;padding-left:18px;display:flex;flex-direction:column;gap:3px}
.stof .tip{margin:0;background:#fff;border:1px dashed var(--peach);border-radius:8px;padding:7px 10px;color:var(--coral-d);font-weight:600}
.klaar{margin-top:10px;background:var(--coral);color:#fff;border:0;border-radius:8px;padding:7px 14px;font-weight:800;font-size:12.5px;cursor:pointer}
.klaar:hover{background:var(--coral-d)}
.klaar:disabled{opacity:.6}
.fout{color:#b3261e}
.stil{color:var(--grey)}
/* Videotheek */
.vidkop{margin:22px 0 10px}
.vt{font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:1px;color:var(--coral-d)}
.vsub{color:var(--grey);font-size:12.5px;margin:4px 0 0}
.videos{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
@media(max-width:900px){.videos{grid-template-columns:repeat(2,1fr)}}
@media(max-width:560px){.videos{grid-template-columns:1fr}}
.vcard{margin:0;background:#fff;border:1px solid var(--line);border-radius:16px;overflow:hidden;display:flex;flex-direction:column}
.vcard video{width:100%;aspect-ratio:9/16;max-height:340px;object-fit:cover;background:#1c1512;display:block}
.vcard figcaption{padding:10px 14px 12px}
.vcard b{font-size:13.5px}
.vcard small{display:block;font-weight:700;font-size:10.5px;text-transform:uppercase;letter-spacing:.6px;color:var(--coral-d);margin-top:2px}
.vcard p{margin:4px 0 0;color:var(--grey);font-size:12px;line-height:1.45}
</style>
