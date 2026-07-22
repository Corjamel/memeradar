<script setup>
// Nieuwe producten — lanceringen met fase-tijdlijn & adoptie-meting (v71).
// Partner: ziet de tijdlijn en meldt "wij hebben besteld" (t.prodBesteld).
// AM/kantoor: ziet de adoptie per product en vinkt per winkel af.
// Kantoor: beheert de lanceringen (naam, fase, verwachte leverdatum).
import { computed, onMounted, reactive, ref } from 'vue'
import { useAuth } from '../../../stores/auth.js'
import { useTappunten } from '../../tappunten/store.js'
import { haalCentral } from '../../beheer/api.js'
import { haalProducten, bewaarProducten, actieveProducten, prodLeverbaar, PROD_FASES } from '../api.js'

const auth = useAuth()
const st = useTappunten()
const alle = ref([])            // incl. gearchiveerd (kantoor)
const shopUrl = ref('')
const fout = ref('')
const melding = ref('')
const bezig = ref(false)
const bewerkId = ref(null)
const vorm = reactive({ naam: '', desc: '', artnr: '', verwacht: '', fase: 0 })

const producten = computed(() => auth.isKantoor ? alle.value : actieveProducten(alle.value))
const eigen = computed(() => auth.isPartner ? (st.items[0] || null) : null)

onMounted(async () => {
  try {
    if (!st.items.length) await st.laad()
    alle.value = await haalProducten()
    shopUrl.value = String(await haalCentral('shopUrl') || '')
    // Partner: alles wat je nu ziet is "gezien" (v71 prodGezienP — meldingen weg).
    if (eigen.value) {
      const gz = eigen.value.prodGezienP || []
      const nieuw = actieveProducten(alle.value).map(p => p.id).filter(id => !gz.includes(id))
      if (nieuw.length) {
        const t2 = { ...eigen.value, prodGezienP: [...gz, ...nieuw] }
        await st.bewaar(t2)
      }
    }
  } catch (e) { fout.value = 'Kon producten niet laden: ' + e.message }
})

function besteld(t, p) { return !!(t && t.prodBesteld && t.prodBesteld[p.id] && t.prodBesteld[p.id].done) }

// v71 setProdBesteld: eenmalig zetten + logboek-notitie; uitzetten wist de markering.
async function zetBesteld(t, p, aan, by) {
  if (bezig.value) return
  bezig.value = true; fout.value = ''
  try {
    const prodBesteld = { ...(t.prodBesteld || {}) }
    let logboek = t.logboek || []
    if (aan) {
      if (prodBesteld[p.id]) { bezig.value = false; return }
      prodBesteld[p.id] = { done: true, at: new Date().toISOString().slice(0, 10), by }
      logboek = [...logboek, {
        id: 'l' + Date.now().toString(36), at: new Date().toISOString().slice(0, 10),
        type: 'notitie', txt: '🧴 Besteld: ' + p.naam + (by === 'partner' ? ' (zelf)' : '')
      }]
    } else { delete prodBesteld[p.id] }
    const t2 = { ...t, prodBesteld, logboek }
    await st.bewaar(t2)
    if (eigen.value && t.snelstart === eigen.value.snelstart) Object.assign(eigen.value, t2)
  } catch (e) { fout.value = 'Opslaan mislukt: ' + e.message }
  bezig.value = false
}

// Adoptie over de zichtbare winkels (AM: portefeuille, kantoor: netwerk).
function adoptie(p) {
  const n = st.items.length
  const b = st.items.filter(t => besteld(t, p)).length
  return { n, b, pct: n ? Math.round(b / n * 100) : 0 }
}

// ---- kantoor: beheer ----
function startBewerk(p) {
  bewerkId.value = p.id
  Object.assign(vorm, { naam: p.naam, desc: p.desc || '', artnr: p.artnr || '', verwacht: p.verwacht || '', fase: +p.fase || 0 })
}
function resetVorm() { bewerkId.value = null; Object.assign(vorm, { naam: '', desc: '', artnr: '', verwacht: '', fase: 0 }) }

async function bewaarLijst(lijst, ok) {
  bezig.value = true; fout.value = ''; melding.value = ''
  try { await bewaarProducten(lijst); alle.value = lijst; melding.value = ok }
  catch (e) { fout.value = 'Opslaan mislukt: ' + e.message }
  bezig.value = false
}

async function opslaan() {
  const naam = vorm.naam.trim()
  if (!naam || bezig.value) return
  const velden = { naam, desc: vorm.desc.trim(), artnr: vorm.artnr.trim(), verwacht: vorm.verwacht, fase: Math.max(0, Math.min(3, +vorm.fase || 0)) }
  let lijst
  if (bewerkId.value) {
    lijst = alle.value.map(p => p.id === bewerkId.value ? { ...p, ...velden } : p)
  } else {
    const p = { id: 'p' + Date.now().toString(36), ...velden, at: new Date().toISOString().slice(0, 10), archived: false }
    lijst = [p, ...alle.value]
  }
  await bewaarLijst(lijst, bewerkId.value ? '✓ Product bijgewerkt — bestellingen en adoptie blijven staan.' : `✓ "${naam}" staat live — AM's en partners zien de tijdlijn nu.`)
  resetVorm()
}

async function faseStap(p, d) {
  const lijst = alle.value.map(x => x.id === p.id ? { ...x, fase: Math.max(0, Math.min(3, (+x.fase || 0) + d)) } : x)
  await bewaarLijst(lijst, '✓ Fase bijgewerkt')
}
async function archiveer(p) {
  const lijst = alle.value.map(x => x.id === p.id ? { ...x, archived: !x.archived } : x)
  await bewaarLijst(lijst, p.archived ? '✓ Teruggezet' : '✓ Gearchiveerd')
}
</script>

<template>
  <div>
    <h1>🧴 Nieuwe producten</h1>
    <p class="sub" v-if="auth.isPartner">Wat er aankomt bij TapParfum — en wanneer je het kunt bestellen.</p>
    <p class="sub" v-else>Lanceringen met tijdlijn en adoptie: wie heeft er al besteld?</p>
    <p v-if="fout" class="fout" role="alert">{{ fout }}</p>
    <p v-if="melding" class="melding" role="status">{{ melding }}</p>

    <!-- Kantoor: toevoegen / bewerken -->
    <form v-if="auth.isKantoor" class="kaart vorm" @submit.prevent="opslaan">
      <h2>{{ bewerkId ? 'Product bewerken' : 'Nieuwe lancering' }}</h2>
      <div class="rij">
        <label>Naam<input v-model="vorm.naam" required data-test="prod-naam" /></label>
        <label>Artikelnr.<input v-model="vorm.artnr" class="kort" /></label>
        <label>Verwacht leverbaar<input v-model="vorm.verwacht" type="date" class="kort" data-test="prod-verwacht" /></label>
        <label>Fase
          <select v-model.number="vorm.fase" data-test="prod-fase">
            <option v-for="(f, i) in PROD_FASES" :key="i" :value="i">{{ f }}</option>
          </select>
        </label>
      </div>
      <label>Omschrijving<input v-model="vorm.desc" /></label>
      <div class="acties">
        <button class="btn" type="submit" :disabled="bezig" data-test="prod-opslaan">{{ bewerkId ? 'Bijwerken' : 'Lanceren' }}</button>
        <button v-if="bewerkId" class="btn stil2" type="button" @click="resetVorm">Annuleren</button>
      </div>
    </form>

    <!-- Productkaarten -->
    <div v-for="p in producten" :key="p.id" class="kaart prod" :class="{ archief: p.archived }" data-test="product">
      <div class="kop">
        <b class="naam">{{ p.naam }}</b>
        <span v-if="p.artnr" class="mo">#{{ p.artnr }}</span>
        <span v-if="p.archived" class="badge grijs">gearchiveerd</span>
        <template v-if="auth.isKantoor">
          <button class="klein" type="button" :aria-label="'Fase terug: ' + p.naam" @click="faseStap(p, -1)">◀</button>
          <button class="klein" type="button" :data-test="'fase-plus-' + p.id" :aria-label="'Fase vooruit: ' + p.naam" @click="faseStap(p, 1)">▶</button>
          <button class="klein" type="button" @click="startBewerk(p)">Bewerk</button>
          <button class="klein" type="button" @click="archiveer(p)">{{ p.archived ? 'Terugzetten' : 'Archiveer' }}</button>
        </template>
      </div>
      <p v-if="p.desc" class="mo">{{ p.desc }}</p>

      <!-- Fase-tijdlijn (v71) -->
      <div class="tijdlijn">
        <div v-for="(lbl, i) in PROD_FASES" :key="i" class="stap">
          <div class="streep" :class="{ af: i < (+p.fase || 0), nu: i === (+p.fase || 0) }"></div>
          <div class="lbl" :class="{ af: i < (+p.fase || 0), nu: i === (+p.fase || 0) }">{{ i < (+p.fase || 0) ? '✓ ' : '' }}{{ lbl }}</div>
        </div>
      </div>
      <p class="mid" data-test="tijdlijn-status">
        {{ prodLeverbaar(p) ? '🎉 Nu leverbaar — bestel in het bestelportaal!'
           : (p.verwacht ? 'Verwacht leverbaar: ' + p.verwacht : 'Leverdatum volgt') }}
      </p>

      <!-- Partner: bestellen -->
      <div v-if="auth.isPartner && eigen && prodLeverbaar(p)" class="onder">
        <span v-if="besteld(eigen, p)" class="badge groen" data-test="prod-besteld-badge">✓ Besteld!</span>
        <button v-else class="btn" type="button" :disabled="bezig" :data-test="'prod-bestel-' + p.id"
                @click="zetBesteld(eigen, p, true, 'partner')">✓ Wij hebben besteld</button>
        <a v-if="shopUrl" class="btn stil2" :href="shopUrl" target="_blank" rel="noopener noreferrer">🛒 Bestel →</a>
      </div>

      <!-- AM/kantoor: adoptie + per winkel afvinken -->
      <details v-if="!auth.isPartner" class="adoptie">
        <summary data-test="adoptie">Adoptie: <b>{{ adoptie(p).b }}</b> van {{ adoptie(p).n }} winkels besteld ({{ adoptie(p).pct }}%)</summary>
        <div class="balk"><div class="vul" :style="{ width: adoptie(p).pct + '%' }"></div></div>
        <label v-for="t in st.items" :key="t.snelstart" class="winkelrij">
          <input type="checkbox" :checked="besteld(t, p)" :disabled="bezig"
                 :data-test="'prod-w-' + t.snelstart + '-' + p.id"
                 @change="zetBesteld(t, p, $event.target.checked, 'am')" />
          <span>{{ t.name }}</span>
          <span v-if="besteld(t, p)" class="mo">{{ t.prodBesteld[p.id].at }}<template v-if="t.prodBesteld[p.id].by === 'partner'"> · zelf gemeld</template></span>
        </label>
      </details>
    </div>
    <p v-if="!producten.length" class="stil">Nog geen lanceringen.</p>
  </div>
</template>

<style scoped>
h1{margin:0 0 4px;font-size:22px}
h2{margin:0 0 10px;font-size:15px}
.sub{color:var(--grey);margin:0 0 14px;font-size:13.5px}
.kaart{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px;margin-bottom:12px}
.prod.archief{opacity:.55}
.kop{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.naam{font-size:16px}
.mo{color:var(--grey);font-size:12.5px;margin:4px 0 0}
.badge{font-size:11px;font-weight:800;border-radius:6px;padding:2px 9px}
.badge.groen{background:var(--green-soft);color:#2c5a12}
.badge.grijs{background:var(--cream);color:var(--grey)}
.klein{background:none;border:1.5px solid var(--line);border-radius:8px;padding:3px 9px;font-size:12px;font-weight:700;color:var(--grey);cursor:pointer}
.klein:hover{border-color:var(--coral);color:var(--coral-d)}
.tijdlijn{display:flex;gap:4px;margin-top:12px}
.stap{flex:1;text-align:center}
.streep{height:6px;border-radius:4px;background:var(--line)}
.streep.af{background:var(--green)}
.streep.nu{background:var(--coral-d)}
.lbl{font-size:10.5px;font-weight:600;color:var(--grey);margin-top:4px}
.lbl.af{color:var(--green)}
.lbl.nu{color:var(--coral-d);font-weight:800}
.mid{text-align:center;font-weight:700;font-size:12.5px;color:var(--grey);margin:8px 0 0}
.onder{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:10px}
.btn{background:var(--coral);color:#fff;border:0;border-radius:10px;padding:9px 15px;font-weight:800;cursor:pointer;font-size:13px;text-decoration:none;display:inline-block}
.btn.stil2{background:var(--cream);color:var(--ink);border:1.5px solid var(--line)}
.btn:disabled{opacity:.6}
.adoptie{margin-top:12px;border-top:1px solid var(--line);padding-top:10px}
.adoptie summary{cursor:pointer;font-size:13px;color:var(--grey)}
.balk{height:7px;border-radius:6px;background:#f0ebe3;overflow:hidden;margin:8px 0}
.vul{height:100%;background:var(--coral)}
.winkelrij{display:flex;align-items:center;gap:9px;padding:6px 0;border-bottom:1px solid var(--line);font-size:13.5px;cursor:pointer}
.winkelrij:last-child{border-bottom:0}
.winkelrij input{width:16px;height:16px;accent-color:var(--coral)}
.winkelrij .mo{margin:0 0 0 auto}
.vorm .rij{display:flex;gap:10px;flex-wrap:wrap}
.vorm label{display:flex;flex-direction:column;gap:5px;font-size:12.5px;font-weight:700;color:var(--grey);flex:1;min-width:140px;margin-top:8px}
.vorm input,.vorm select{padding:8px 10px;border:1.5px solid var(--line);border-radius:10px;font-size:13.5px;font-family:inherit}
.vorm input:focus,.vorm select:focus{border-color:var(--coral)}
.kort{max-width:170px}
.acties{display:flex;gap:8px;margin-top:12px}
.fout{color:#b3261e}
.melding{color:var(--grey);font-size:13px}
.stil{color:var(--grey)}
</style>
