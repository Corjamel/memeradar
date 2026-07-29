<script setup>
// Team & activiteit (v71 kteam + kactFeed) — voor kantoor het hele netwerk,
// voor een AM de eigen portefeuille (RLS bepaalt de uitsnede). Per
// accountmanager een uitklapbare drilldown met een AM-score, de winkels op
// omzet, en per stagnerende winkel een opdracht-knop naar de AM. Daaronder de
// netwerkbrede activiteitenfeed.
import { computed, onMounted, ref } from 'vue'
import { useAuth } from '../../../stores/auth.js'
import { useToast } from '../../../stores/toast.js'
import { useTappunten } from '../../tappunten/store.js'
import { eur0 } from '../../../lib/format.js'
import { haalAms } from '../../dashboard/api.js'
import { stuurBericht } from '../../berichten/api.js'
import { statusKey, STATUS, jaaromzet, levelOf } from '../../rekenhart/logic.js'
import { omzetGroei } from '../../punten/logic.js'
import { doetMee, heeftRes } from '../../acties/logic.js'
import { dagenSindsBezoek, afsprakenOpen, LOG_TYPES } from '../../logboek/logic.js'
import { haalRekenConfig } from '../../beloningen/api.js'
import { haalCentral } from '../../beheer/api.js'
import { amScore } from '../logic.js'

const auth = useAuth()
const toast = useToast()
const st = useTappunten()
const ams = ref([])
const marge = ref(1)
const acties = ref([])           // niet-gearchiveerde campagnes (voor de uitvoering-component)
const actDagen = ref(90)         // activatievenster (v71 regels.actDagen)
const fout = ref('')
const melding = ref('')
const open = ref(null)
const opdrachtVoor = ref(null)   // snelstart
const opdrachtTxt = ref('')

onMounted(async () => {
  try {
    if (!st.items.length) await st.laad()
    if (auth.isKantoor) ams.value = await haalAms()
    marge.value = (await haalRekenConfig()).marge
    try { acties.value = (await haalCentral('acties')) || [] } catch { acties.value = [] }
    const ad = parseInt(auth.regels && auth.regels.actDagen, 10)
    if (ad > 0 && ad <= 365) actDagen.value = ad
  } catch (e) { fout.value = 'Kon het team niet laden: ' + e.message }
})

// AM-score: exact het v71-model (5 genormaliseerde componenten, gewogen). De
// weging komt uit central 'regels' (kantoor stelt 'm in de Regels-editor bij).
const scoreOpts = computed(() => ({
  weging: (auth.regels && auth.regels.weging) || null,
  acties: acties.value, actDagen: actDagen.value
}))

const perAm = computed(() => {
  const naam = Object.fromEntries(ams.value.map(a => [a.id, a.naam]))
  const m = new Map()
  st.items.forEach(t => {
    const k = t.am_id || '-'
    if (!m.has(k)) m.set(k, { id: k, naam: naam[k] || 'Geen AM', winkels: [] })
    m.get(k).winkels.push(t)
  })
  return [...m.values()].map(g => {
    const omzet = g.winkels.reduce((s, t) => s + jaaromzet(t), 0)
    const cnt = { nieuw: 0, groeit: 0, stagneert: 0, top: 0 }
    g.winkels.forEach(t => cnt[statusKey(t, marge.value)]++)
    const sc = amScore(g.winkels, scoreOpts.value)
    return { ...g, omzet, cnt, score: sc.score, scoreComp: sc.comp, winkels: [...g.winkels].sort((a, b) => jaaromzet(b) - jaaromzet(a)) }
  }).sort((a, b) => b.score - a.score)
})

// Activiteitenfeed: logboek + bestellingen + afgeronde afspraken, chronologisch.
const feed = computed(() => {
  const uit = []
  st.items.forEach(t => {
    ;(t.logboek || []).forEach(e => uit.push({ at: e.at, ic: LOG_TYPES[e.type]?.ic || '📝', naam: t.name, snelstart: t.snelstart, txt: e.txt }))
    ;(t.bestellingen || []).forEach(b => uit.push({ at: b.at, ic: '📦', naam: t.name, snelstart: t.snelstart, txt: `Bestelling ${eur0(b.totaal)}${b.ref ? ' · #' + b.ref : ''}` }))
    ;(t.afspraken || []).filter(a => a.done).forEach(a => uit.push({ at: a.doneAt || a.at, ic: '✓', naam: t.name, snelstart: t.snelstart, txt: `Afspraak afgerond: ${a.txt}` }))
  })
  return uit.filter(x => x.at).sort((a, b) => (a.at < b.at ? 1 : -1)).slice(0, 40)
})

async function stuurOpdracht(t) {
  if (!opdrachtTxt.value.trim()) return
  try {
    await stuurBericht({ aan_am: t.am_id, type: 'taak', txt: `[${t.name}] ${opdrachtTxt.value.trim()}`, van: auth.user?.email || 'kantoor' })
    melding.value = `✓ Opdracht over ${t.name} verstuurd naar de accountmanager.`
    toast.ok(`Opdracht over ${t.name} verstuurd`)
    opdrachtVoor.value = null; opdrachtTxt.value = ''
  } catch (e) { fout.value = 'Versturen mislukt: ' + e.message; toast.fout('Versturen mislukt') }
}
function grow(t) { const g = omzetGroei(t); return g == null ? '—' : (g >= 0 ? '+' : '') + Math.round(g * 100) + '%' }
</script>

<template>
  <div>
    <h1>👥 Team & activiteit</h1>
    <p class="sub">{{ auth.isKantoor ? 'Het hele netwerk per accountmanager, op prestatie gesorteerd.' : 'Jouw portefeuille en de recente activiteit.' }}</p>
    <p v-if="fout" class="fout" role="alert">{{ fout }}</p>
    <p v-if="melding" class="ok" role="status" data-test="team-melding">{{ melding }}</p>

    <!-- Per accountmanager -->
    <div v-for="g in perAm" :key="g.id" class="kaart" data-test="team-am">
      <button class="amkop" type="button" @click="open = open === g.id ? null : g.id">
        <div class="amnaam"><b>{{ g.naam }}</b><span class="score" data-test="am-score">score {{ g.score }}</span></div>
        <div class="ammeta">
          {{ g.winkels.length }} winkels · {{ eur0(g.omzet) }}
          <span v-if="g.cnt.stagneert" class="badge amber">{{ g.cnt.stagneert }} stagneert</span>
          <span v-if="g.cnt.top" class="badge coral">{{ g.cnt.top }} top</span>
          <span class="chev">{{ open === g.id ? '▴' : '▾' }}</span>
        </div>
      </button>
      <div v-if="open === g.id" class="drill">
        <div class="compstrip" data-test="am-score-comp">
          <span v-for="[lab, val] in g.scoreComp" :key="lab" class="compchip"><span class="cl">{{ lab }}</span> <b>{{ val }}</b></span>
        </div>
        <div v-for="t in g.winkels" :key="t.snelstart" class="wrij" data-test="team-winkel">
          <span class="niveau">{{ levelOf(jaaromzet(t), marge).k }}</span>
          <router-link class="wnaam" :to="{ name: 'winkel', params: { code: t.snelstart } }">{{ t.name }}</router-link>
          <span class="badge" :style="{ background: STATUS[statusKey(t, marge)].bg, color: STATUS[statusKey(t, marge)].fg }">{{ STATUS[statusKey(t, marge)].l }}</span>
          <span class="mo">{{ eur0(jaaromzet(t)) }} · groei {{ grow(t) }}<template v-if="afsprakenOpen(t).length"> · {{ afsprakenOpen(t).length }} open afspraken</template></span>
          <button v-if="auth.isKantoor && t.am_id" class="klein" type="button" :data-test="'opdracht-' + t.snelstart" @click="opdrachtVoor = opdrachtVoor === t.snelstart ? null : t.snelstart">Opdracht →</button>
        </div>
        <div v-if="auth.isKantoor && opdrachtVoor && g.winkels.some(w => w.snelstart === opdrachtVoor)" class="opdrachtvorm">
          <input v-model="opdrachtTxt" placeholder="Opdracht aan de accountmanager…" data-test="opdracht-txt" />
          <button class="knop" type="button" data-test="opdracht-verstuur" @click="stuurOpdracht(g.winkels.find(w => w.snelstart === opdrachtVoor))">Versturen</button>
        </div>
      </div>
    </div>
    <p v-if="!perAm.length" class="stil">Geen winkels.</p>

    <!-- Activiteitenfeed -->
    <div class="kaart">
      <h2>Recente activiteit</h2>
      <div v-for="(f, i) in feed" :key="i" class="feedrij" data-test="feed-rij">
        <span class="fic">{{ f.ic }}</span>
        <span class="fdatum">{{ f.at }}</span>
        <router-link class="fnaam" :to="{ name: 'winkel', params: { code: f.snelstart } }">{{ f.naam }}</router-link>
        <span class="ftxt">{{ f.txt }}</span>
      </div>
      <p v-if="!feed.length" class="stil">Nog geen activiteit geregistreerd.</p>
    </div>
  </div>
</template>

<style scoped>
h1{margin:0 0 4px;font-size:22px}
h2{margin:0 0 10px;font-size:15px}
.sub{color:var(--grey);margin:0 0 14px;font-size:13.5px}
.kaart{background:#fff;border:1px solid var(--line);border-radius:14px;padding:14px 16px;margin-bottom:12px}
.amkop{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;width:100%;background:none;border:0;cursor:pointer;font-family:inherit;text-align:left;padding:0}
.amnaam{display:flex;align-items:center;gap:10px}
.amnaam b{font-size:16px}
.score{background:var(--soft);color:var(--coral-d);font-size:11.5px;font-weight:800;border-radius:999px;padding:3px 10px}
.ammeta{color:var(--grey);font-size:13px;display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.chev{color:var(--coral-d);font-size:12px}
.badge{font-size:11px;font-weight:800;border-radius:6px;padding:2px 8px}
.badge.amber{background:var(--amber);color:#412402}
.badge.coral{background:var(--soft);color:var(--coral-d)}
.drill{margin-top:12px;border-top:1px solid var(--line);padding-top:8px}
.compstrip{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px}
.compchip{background:var(--cream);border:1px solid var(--line);border-radius:999px;padding:3px 10px;font-size:11.5px;color:var(--grey)}
.compchip .cl{font-weight:700}
.compchip b{color:var(--ink)}
.wrij{display:flex;align-items:center;gap:10px;padding:7px 0;border-bottom:1px solid var(--line);font-size:13.5px;flex-wrap:wrap}
.wrij:last-child{border-bottom:0}
.niveau{width:28px;height:28px;flex-shrink:0;border-radius:8px;background:var(--coral);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:12px}
.wnaam{font-weight:700;color:inherit;text-decoration:none}
.wnaam:hover{color:var(--coral-d)}
.mo{color:var(--grey);font-size:12.5px}
.klein{margin-left:auto;background:none;border:1.5px solid var(--line);border-radius:8px;padding:4px 11px;font-size:12px;font-weight:700;color:var(--grey);cursor:pointer}
.klein:hover{border-color:var(--coral);color:var(--coral-d)}
.opdrachtvorm{display:flex;gap:8px;margin-top:10px;flex-wrap:wrap}
.opdrachtvorm input{flex:1;min-width:180px;padding:8px 10px;border:1.5px solid var(--line);border-radius:10px;font-size:13.5px}
.knop{background:var(--coral);color:#fff;border:0;border-radius:10px;padding:8px 14px;font-weight:800;cursor:pointer;font-size:13px}
.feedrij{display:flex;align-items:center;gap:10px;padding:6px 0;border-bottom:1px solid var(--line);font-size:13px}
.feedrij:last-child{border-bottom:0}
.fic{width:22px;text-align:center;flex-shrink:0}
.fdatum{color:var(--grey);font-size:12px;font-variant-numeric:tabular-nums;flex-shrink:0}
.fnaam{font-weight:700;color:inherit;text-decoration:none;flex-shrink:0}
.fnaam:hover{color:var(--coral-d)}
.ftxt{color:var(--grey);min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.ok{color:#2c5a12;font-size:13px}
.fout{color:#b3261e}
.stil{color:var(--grey)}
</style>
