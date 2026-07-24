<script setup>
// Ritten & locatie-archief (v71 ritten). Losse punt-stempels — géén doorlopende
// tracking: alleen bij Start/Stop werkdag en een check-in bij een winkel wordt
// éénmalig de locatie gepeild. De AM heeft een aan/uit-knop om het loggen te
// pauzeren; dan wordt de handeling wél vastgelegd, zonder coördinaten.
//
// Toegang loopt via RLS (server): kantoor ziet alle AM's, een AM alleen zichzelf,
// een partner niets. Verwijderen mag alleen kantoor (permanent archief).
import { computed, onMounted, ref } from 'vue'
import { useAuth } from '../../../stores/auth.js'
import { useToast } from '../../../stores/toast.js'
import { useTappunten } from '../../tappunten/store.js'
import { haalAms } from '../../dashboard/api.js'
import { haalLocaties, stempel, verwijderLocatie, geoStamp } from '../api.js'
import { groepeerPerDag, TYPE_LABEL, mapsLink } from '../logic.js'

const auth = useAuth()
const toast = useToast()
const st = useTappunten()
const rijen = ref([])
const ams = ref([])
const fout = ref('')
const bezig = ref(false)
const kiesWinkel = ref('')

// Aan/uit-knop: de AM pauzeert het locatie-loggen. Per account in localStorage —
// puur een consent-schakelaar op het eigen apparaat; het peilen gebeurt sowieso
// client-side. Standaard AAN.
const sleutel = computed(() => 'tp_locatie_aan::' + String((auth.user && auth.user.email) || '').toLowerCase())
const locatieAan = ref(true)
function laadToggle() { try { locatieAan.value = localStorage.getItem(sleutel.value) !== '0' } catch (e) { locatieAan.value = true } }
function zetToggle(aan) {
  locatieAan.value = aan
  try { localStorage.setItem(sleutel.value, aan ? '1' : '0') } catch (e) { /* device-lokaal */ }
  toast.info(aan ? 'Locatie vastleggen staat aan' : 'Locatie vastleggen gepauzeerd — handelingen worden zonder locatie gelogd')
}

async function laad() {
  fout.value = ''
  try {
    if (!st.items.length) await st.laad()
    if (auth.isKantoor) ams.value = await haalAms()
    rijen.value = await haalLocaties()
  } catch (e) { fout.value = 'Kon de ritten niet laden: ' + e.message }
}
onMounted(() => { laadToggle(); laad() })

const winkels = computed(() => [...st.items].sort((a, b) => String(a.name).localeCompare(String(b.name))))
const amNaam = computed(() => Object.fromEntries(ams.value.map(a => [a.id, a.naam])))
const winkelNaam = computed(() => Object.fromEntries(st.items.map(t => [t.snelstart, t.name])))

// Loopt er vandaag al een werkdag (start zonder stop)?
const vandaag = new Date().toISOString().slice(0, 10)
const eigenVandaag = computed(() => rijen.value.filter(r => String(r.at).slice(0, 10) === vandaag && (!auth.isKantoor || r.am_id === auth.amId)))
const werkdagLoopt = computed(() => {
  const t = eigenVandaag.value.filter(r => r.type === 'start' || r.type === 'stop')
  const laatste = t.sort((a, b) => String(a.at).localeCompare(String(b.at))).slice(-1)[0]
  return laatste && laatste.type === 'start'
})

// AM: eigen dagen. Kantoor: per AM gegroepeerd, elk met eigen dagen.
const eigenDagen = computed(() => groepeerPerDag(rijen.value))
const perAm = computed(() => {
  const m = new Map()
  rijen.value.forEach(r => { if (!m.has(r.am_id)) m.set(r.am_id, []); m.get(r.am_id).push(r) })
  return [...m.entries()].map(([id, rows]) => ({ id, naam: amNaam.value[id] || 'Accountmanager', dagen: groepeerPerDag(rows) }))
    .sort((a, b) => String(a.naam).localeCompare(String(b.naam)))
})

async function plaats(type, tappunt_snelstart = null) {
  if (bezig.value) return
  bezig.value = true; fout.value = ''
  try {
    const gps = locatieAan.value ? await geoStamp() : null
    await stempel({ type, tappunt_snelstart, gps })
    if (locatieAan.value && !gps) toast.info('Locatie niet beschikbaar — stempel zonder coördinaten opgeslagen')
    else toast.ok(type === 'start' ? 'Werkdag gestart' : type === 'stop' ? 'Werkdag gestopt' : 'Bezoek ingecheckt')
    kiesWinkel.value = ''
    await laad()
  } catch (e) { fout.value = 'Stempel plaatsen mislukt: ' + e.message; toast.fout('Stempel mislukt') }
  bezig.value = false
}
function checkin() { if (kiesWinkel.value) plaats('bezoek', kiesWinkel.value) }

async function wis(id) {
  if (!auth.isKantoor) return
  try { await verwijderLocatie(id); toast.ok('Stempel verwijderd'); await laad() }
  catch (e) { toast.fout('Verwijderen mislukt: ' + e.message) }
}

function tijd(s) { const m = String(s.at || '').match(/T(\d{2}:\d{2})/); return m ? m[1] : '' }
function winkelLabel(s) { return s.tappunt_snelstart ? (winkelNaam.value[s.tappunt_snelstart] || s.tappunt_snelstart) : '' }
</script>

<template>
  <div>
    <h1>🚗 Ritten & locatie</h1>
    <p class="sub">{{ auth.isKantoor ? 'De werkdag-stempels van alle accountmanagers — permanent archief.' : 'Je eigen werkdag-stempels. Alleen jij en kantoor zien dit.' }}</p>
    <p v-if="fout" class="fout" role="alert">{{ fout }}</p>

    <!-- AM: registratie + aan/uit -->
    <div v-if="!auth.isKantoor" class="kaart werkbalk" data-test="rit-werkbalk">
      <div class="acties">
        <button v-if="!werkdagLoopt" class="knop" type="button" :disabled="bezig" data-test="rit-start" @click="plaats('start')">🟢 Start werkdag</button>
        <button v-else class="knop stop" type="button" :disabled="bezig" data-test="rit-stop" @click="plaats('stop')">⏹ Stop werkdag</button>
        <span v-if="werkdagLoopt" class="loopt" data-test="rit-loopt">Werkdag loopt</span>
        <span class="rek"></span>
        <select v-model="kiesWinkel" class="wsel" aria-label="Winkel voor check-in" data-test="rit-winkel">
          <option value="">Check-in bij winkel…</option>
          <option v-for="t in winkels" :key="t.snelstart" :value="t.snelstart">{{ t.name }}</option>
        </select>
        <button class="knop ghost" type="button" :disabled="bezig || !kiesWinkel" data-test="rit-checkin" @click="checkin">📍 Inchecken</button>
      </div>
      <label class="toggle" data-test="rit-toggle">
        <input type="checkbox" :checked="locatieAan" data-test="rit-toggle-input" @change="zetToggle($event.target.checked)" />
        <span>Locatie vastleggen {{ locatieAan ? 'aan' : 'uit' }}</span>
      </label>
      <p class="note">Locatie wordt alleen gepeild bij start/stop en een check-in — nooit op de achtergrond. Zet je 'm uit, dan worden je handelingen zonder locatie vastgelegd.</p>
    </div>

    <!-- AM: eigen dagen -->
    <template v-if="!auth.isKantoor">
      <div v-for="d in eigenDagen" :key="d.dag" class="kaart dag" data-test="rit-dag">
        <div class="dagkop"><b>{{ d.dag }}</b><span class="mo">{{ d.nBezoek }} bezoek(en)<template v-if="d.km"> · ≈ {{ d.km }} km (hemelsbreed, indicatie)</template></span></div>
        <div v-for="s in d.stempels" :key="s.id" class="stempel" data-test="rit-stempel">
          <span class="tt">{{ tijd(s) }}</span>
          <span class="tp">{{ TYPE_LABEL[s.type] }}</span>
          <span v-if="winkelLabel(s)" class="wn">{{ winkelLabel(s) }}</span>
          <a v-if="mapsLink(s)" class="pin" :href="mapsLink(s)" target="_blank" rel="noopener noreferrer" :title="'±' + (s.acc || '?') + ' m' + (s.loc ? ' · ' + s.loc : '')">📍</a>
          <span v-else class="geenloc">geen locatie</span>
        </div>
      </div>
      <p v-if="!eigenDagen.length" class="stil">Nog geen stempels — start je werkdag om te beginnen.</p>
    </template>

    <!-- Kantoor: per accountmanager -->
    <template v-else>
      <div v-for="a in perAm" :key="a.id" class="kaart" data-test="rit-am">
        <h2>{{ a.naam }}</h2>
        <div v-for="d in a.dagen" :key="d.dag" class="dag" data-test="rit-dag">
          <div class="dagkop"><b>{{ d.dag }}</b><span class="mo">{{ d.nBezoek }} bezoek(en)<template v-if="d.km"> · ≈ {{ d.km }} km</template></span></div>
          <div v-for="s in d.stempels" :key="s.id" class="stempel" data-test="rit-stempel">
            <span class="tt">{{ tijd(s) }}</span>
            <span class="tp">{{ TYPE_LABEL[s.type] }}</span>
            <span v-if="winkelLabel(s)" class="wn">{{ winkelLabel(s) }}</span>
            <a v-if="mapsLink(s)" class="pin" :href="mapsLink(s)" target="_blank" rel="noopener noreferrer" :title="'±' + (s.acc || '?') + ' m'">📍</a>
            <span v-else class="geenloc">geen locatie</span>
            <button class="wis" type="button" :data-test="'rit-wis-' + s.id" title="Verwijderen" @click="wis(s.id)">×</button>
          </div>
        </div>
      </div>
      <p v-if="!perAm.length" class="stil">Nog geen stempels geregistreerd.</p>
    </template>
  </div>
</template>

<style scoped>
h1{margin:0 0 4px;font-size:22px}
h2{margin:0 0 8px;font-size:15px}
.sub{color:var(--grey);margin:0 0 14px;font-size:13.5px}
.kaart{background:#fff;border:1px solid var(--line);border-radius:14px;padding:14px 16px;margin-bottom:12px}
.werkbalk .acties{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.rek{flex:1}
.knop{background:var(--coral);color:#fff;border:0;border-radius:10px;padding:9px 15px;font-weight:800;cursor:pointer;font-size:13px}
.knop.stop{background:var(--ink)}
.knop.ghost{background:#fff;border:1.5px solid var(--line);color:var(--ink)}
.knop:disabled{opacity:.5;cursor:default}
.loopt{color:var(--green);font-weight:800;font-size:12.5px}
.wsel{padding:9px 10px;border:1.5px solid var(--line);border-radius:10px;font-size:13px;min-width:180px}
.toggle{display:inline-flex;align-items:center;gap:8px;margin-top:12px;font-size:13px;font-weight:700;cursor:pointer}
.toggle input{width:16px;height:16px;accent-color:var(--coral)}
.note{font-size:12px;color:var(--grey);background:var(--cream);border:1px solid var(--line);border-radius:10px;padding:9px 11px;margin:10px 0 0}
.dag{margin-top:10px;border-top:1px solid var(--line);padding-top:8px}
.dag:first-of-type{border-top:0;margin-top:0}
.dagkop{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;font-size:13.5px;margin-bottom:4px}
.dagkop .mo{color:var(--grey);font-size:12.5px}
.stempel{display:flex;align-items:center;gap:10px;padding:5px 0;font-size:13.5px;flex-wrap:wrap}
.tt{font-variant-numeric:tabular-nums;color:var(--grey);width:42px;flex-shrink:0}
.tp{font-weight:700}
.wn{color:var(--coral-d);font-weight:700}
.pin{text-decoration:none}
.geenloc{color:var(--grey);font-size:11.5px;font-style:italic}
.wis{margin-left:auto;background:none;border:0;color:var(--coral-d);font-weight:800;font-size:16px;cursor:pointer;line-height:1}
.fout{color:#b3261e}
.stil{color:var(--grey)}
</style>
