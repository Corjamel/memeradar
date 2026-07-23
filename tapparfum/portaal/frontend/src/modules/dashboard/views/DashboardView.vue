<script setup>
// Startscherm per rol: kantoor (netwerk-cockpit), AM (mijn winkels), partner
// (eigen winkel). Alleen weergave — alle data komt RLS-gescoped uit de modules.
import { computed, onMounted, ref } from 'vue'
import { useAuth } from '../../../stores/auth.js'
import { useTappunten } from '../../tappunten/store.js'
import { haalWinkelvragen } from '../../winkelvragen/api.js'
import { haalAgenda } from '../../agenda/api.js'
import { haalRekenConfig } from '../../beloningen/api.js'
import { levelOf, jaaromzet, beDone, flessenVerkocht, winkelOmzetInfo, statusKey } from '../../rekenhart/logic.js'
import { inkoopJaar, bestelStil } from '../../bestellingen/logic.js'
import { setupComplete, setupCount, SETUP_TOTAL } from '../../setup/logic.js'
import { basisScore, BASIS_MAX, officieel, monthsElapsed } from '../../punten/logic.js'
import { REWARDS, rewUnlocked } from '../../beloningen/logic.js'
import { SPOTLIGHT, USPS } from '../../geurbib/spotlight.js'
import { stuurWinkelvraag } from '../../winkelvragen/api.js'
import { haalActies, isActief } from '../../acties/api.js'
import { haalProducten, actieveProducten } from '../../producten/api.js'
import { doetMee, heeftRes } from '../../acties/logic.js'
import { haalTaken } from '../../taken/api.js'
import { haalAms } from '../api.js'
import { eur0 } from '../../../lib/format.js'
import FlesMeter from '../../../components/FlesMeter.vue'

const auth = useAuth()
const st = useTappunten()
const vragen = ref([])
const agenda = ref([])
const ams = ref([])
const marge = ref(1)
const taken = ref([])
const acties = ref([])
const producten = ref([])
const fout = ref('')

onMounted(async () => {
  try {
    if (!st.items.length) await st.laad()
    ;[vragen.value, agenda.value] = await Promise.all([haalWinkelvragen(), haalAgenda()])
    if (auth.isKantoor) ams.value = await haalAms()
    if (auth.isPartner) {
      marge.value = (await haalRekenConfig()).marge
      ;[acties.value, producten.value] = await Promise.all([haalActies().catch(() => []), haalProducten().catch(() => [])])
    } else taken.value = await haalTaken()
  } catch (e) { fout.value = 'Kon het overzicht niet volledig laden: ' + e.message }
})

const omzetTot = computed(() => st.items.reduce((s, t) => s + (Number(t.jaaromzet) || 0), 0))
const blok = computed(() => st.items.filter(t => t.geblokkeerd).length)
const openVragen = computed(() => vragen.value.filter(v => v.status === 'open').length)
const openTaken = computed(() => taken.value.filter(t => !t.klaar).length)
const komend = computed(() => agenda.value
  .filter(i => i.status === 'voorgesteld' || i.status === 'geaccepteerd')
  .sort((a, b) => (a.datum < b.datum ? -1 : 1)).slice(0, 3))
const WINKEL = computed(() => Object.fromEntries(st.items.map(t => [t.snelstart, t.name])))
const perAm = computed(() => {
  const naam = Object.fromEntries(ams.value.map(a => [a.id, a.naam]))
  const m = new Map()
  for (const t of st.items) {
    const k = t.am_id || '-'
    if (!m.has(k)) m.set(k, { naam: naam[k] || 'Geen AM', n: 0, omzet: 0 })
    const r = m.get(k); r.n++; r.omzet += Number(t.jaaromzet) || 0
  }
  return [...m.values()].sort((a, b) => b.omzet - a.omzet)
})
const topWinkels = computed(() => [...st.items]
  .sort((a, b) => (Number(b.jaaromzet) || 0) - (Number(a.jaaromzet) || 0)).slice(0, 5))

// Kantoor-cockpit: stagnerende winkels (aandachtslijst) + bestellingen-KPI's.
const stagneerders = computed(() => (auth.isKantoor || auth.isAm)
  ? st.items.filter(t => statusKey(t, marge.value) === 'stagneert')
      .sort((a, b) => (Number(b.jaaromzet) || 0) - (Number(a.jaaromzet) || 0))
  : [])
const bestelKpi = computed(() => {
  if (!auth.isKantoor) return null
  const maand = new Date().toISOString().slice(0, 7)
  let inkoop = 0, maandN = 0
  st.items.forEach(t => {
    inkoop += inkoopJaar(t)
    ;(t.bestellingen || []).forEach(b => { if (String(b.at || '').slice(0, 7) === maand) maandN++ })
  })
  return { inkoop, maandN, stil: st.items.filter(t => bestelStil(t)).length }
})
const eigen = computed(() => st.items[0] || null)
const mijnNiveau = computed(() => eigen.value ? levelOf(jaaromzet(eigen.value), marge.value) : null)

/* v71-fasering: waar zit de winkel in de reis? onboarding -> terugverdienen ->
   jaardoel. De faseringskaart toont per fase precies één duidelijke opdracht. */
const fase = computed(() => {
  const t = eigen.value
  if (!auth.isPartner || !t) return null
  if (!setupComplete(t)) {
    return { key: 'onboarding', titel: '🚀 Opstartfase', n: setupCount(t), tot: SETUP_TOTAL,
             pct: Math.round(setupCount(t) / SETUP_TOTAL * 100),
             tekst: `Nog ${SETUP_TOTAL - setupCount(t)} stappen tot een vliegende start — werk de checklist af met je accountmanager.` }
  }
  if (t.be && !beDone(t)) {
    const sold = flessenVerkocht(t)
    return { key: 'breakeven', titel: '📈 Terugverdienfase', n: sold, tot: t.be.bottles,
             pct: Math.min(100, Math.round(sold / t.be.bottles * 100)),
             tekst: `${sold} van ${t.be.bottles} flessen — nog ${Math.max(0, t.be.bottles - sold)} tot je investering eruit is (plan: ±${t.be.perWk} per week).` }
  }
  const doel = (t.goal && t.goal.doel > 0) ? t.goal.doel : (Number(t.doel) || 0)
  if (doel > 0) {
    const jo = jaaromzet(t)
    return { key: 'jaardoel', titel: '🎯 Jaardoel', n: jo, tot: doel,
             pct: Math.min(100, Math.round(jo / doel * 100)),
             tekst: jo >= doel ? 'Jaardoel gehaald — bespreek een nieuw doel met je accountmanager! 🎉'
               : `${eur0(jo)} van ${eur0(doel)}${t.goal && t.goal.flWeek ? ` · richttempo ${t.goal.flWeek} flessen per week` : ''}.` }
  }
  return { key: 'doel-ontbreekt', titel: '🎯 Jaardoel', n: 0, tot: 0, pct: null,
           tekst: 'Er staat nog geen jaardoel — vraag je accountmanager om samen het doel te zetten.' }
})

/* Partner stats-KPI-rij (v71 r.3709): status, basispunten, winkelverkoop, voortgang. */
const stats = computed(() => {
  const t = eigen.value
  if (!auth.isPartner || !t) return null
  const wo = winkelOmzetInfo(t, marge.value, [])
  const inBe = t.be && !beDone(t)
  const sold = flessenVerkocht(t)
  const target = inBe ? t.be.bottles : ((t.goal && t.goal.flJaar) || 0)
  return {
    officieel: officieel(t),
    niveau: levelOf(jaaromzet(t), marge.value).k,
    basis: basisScore(t),
    winkelverkoop: wo.bedrag,
    voortgangLabel: inBe ? 'naar break-even' : 'van jaardoel',
    voortgangPct: target ? Math.min(100, Math.round(sold / target * 100)) : null
  }
})
// Trofeeën-strip: alle spaarcadeaus, behaald of nog te gaan.
const trofeeen = computed(() => {
  const t = eigen.value
  if (!auth.isPartner || !t) return []
  return REWARDS.map(rw => ({ key: rw.key, r: rw.r, ic: rw.ic, gewonnen: rewUnlocked(t, rw) || !!(t.beloond || {})[rw.key] }))
})

// "Deze week"-ring (v71 r.3719): flessen laatste 7 dagen vs weekdoel.
const week = computed(() => {
  const t = eigen.value
  if (!auth.isPartner || !t) return null
  const vanaf = new Date(Date.now() - 6 * 864e5).toISOString().slice(0, 10)
  const flessen = (t.flesLog || []).filter(e => e.at >= vanaf).reduce((s, e) => s + (+e.n || 0), 0)
  let doel = 0
  if (t.goal && t.goal.flWeek) doel = Math.round(t.goal.flWeek)
  else if (t.be && t.be.days) doel = Math.max(1, Math.round(t.be.bottles / (t.be.days / 7)))
  const pct = doel ? Math.min(100, Math.round(flessen / doel * 100)) : 0
  return { flessen, doel, pct, koers: doel > 0 && flessen >= doel }
})

// Vooruitblik/projectie (v71 r.3723): in dit tempo eindig je rond €X -> niveau Y.
const projectie = computed(() => {
  const t = eigen.value
  if (!auth.isPartner || !t) return null
  const jo = jaaromzet(t)
  const m = monthsElapsed(t)
  if (m < 1 || jo <= 0) return null
  const jaarInkoop = Math.round(jo / m * 12)
  const lv = levelOf(jaarInkoop, marge.value)
  return {
    winkelomzet: Math.round(jaarInkoop * (marge.value > 0 ? marge.value : 1)),
    niveau: lv.k, niveauR: lv.r
  }
})

// Berichtenkaart met 4 knoppen (v71 berichtKnopKaart r.3595): vraag/bezoek/
// probleem/retour. De winkelvragen-tabel kent type vraag/probleem/retour; een
// bezoekaanvraag is een 'vraag' met datum, precies als in v71.
const BERICHT_SOORTEN = [
  { k: 'vraag', l: '❓ Vraag', type: 'vraag', pre: '❓ ' },
  { k: 'bezoek', l: '📅 Bezoek', type: 'vraag', pre: '📅 Bezoek aangevraagd — ' },
  { k: 'probleem', l: '⚠️ Probleem', type: 'probleem', pre: '⚠ ' },
  { k: 'retour', l: '📦 Retour', type: 'retour', pre: '📦 Retour — ' }
]
const berSoort = ref('')
const berTxt = ref('')
const berDatum = ref('')
const berFoto = ref(null)
const bezoekMelding = ref('')
function kiesSoort(k) { berSoort.value = k; berTxt.value = ''; berDatum.value = ''; berFoto.value = null; bezoekMelding.value = '' }
async function verstuurBericht() {
  const t = eigen.value
  const cfg = BERICHT_SOORTEN.find(s => s.k === berSoort.value)
  if (!t || !cfg) return
  const kern = cfg.k === 'bezoek' ? ('voorkeur: ' + (berDatum.value || 'z.s.m.')) : berTxt.value.trim()
  if (cfg.k !== 'bezoek' && !kern) { bezoekMelding.value = 'Schrijf eerst een korte toelichting.'; return }
  try {
    await stuurWinkelvraag({ tappunt_snelstart: t.snelstart, type: cfg.type, txt: cfg.pre + kern, foto: cfg.k === 'retour' ? berFoto.value : null })
    bezoekMelding.value = '✓ Verstuurd naar je accountmanager — je krijgt hier antwoord terug.'
    berSoort.value = ''; berTxt.value = ''; berDatum.value = ''; berFoto.value = null
  } catch (e) { bezoekMelding.value = 'Versturen mislukt: ' + e.message }
}

/* Vieringen (v71): mijlpalen die de engine schreef — tonen tot ze weggeklikt
   worden (dismissViering). */
const vieringen = computed(() => auth.isPartner && eigen.value ? (eigen.value.vieringen || []).slice(-3).reverse() : [])
function vierTekst(v) {
  if (v.type === 'level') return `Niveau ${v.k} bereikt — ${v.r}`
  if (v.type === 'doel') return `Jaardoel van ${eur0(v.doel)} gehaald!`
  if (v.type === 'be') return 'Break-even gehaald — jullie investering is terugverdiend!'
  if (v.type === 'beloning') return `Beloning vrijgespeeld: ${v.r}`
  return 'Mijlpaal bereikt'
}
async function wisViering(v) {
  const t = eigen.value
  const t2 = { ...t, vieringen: (t.vieringen || []).filter(x => x !== v) }
  try { await st.bewaar(t2); st.items[0] = t2 } catch (e) { fout.value = 'Opslaan mislukt: ' + e.message }
}

/* Nudges (v71: banners voor nieuw & openstaand) — klikbaar, verdwijnen vanzelf. */
const nudges = computed(() => {
  const t = eigen.value
  if (!auth.isPartner || !t) return []
  const uit = []
  const vd = new Date().toISOString().slice(0, 10)
  const nA = acties.value.filter(a => isActief(a) && !(t.actiesGezienP || []).includes(a.id)).length
  if (nA) uit.push({ ic: '📣', txt: nA === 1 ? 'Nieuwe actie van TapParfum' : `${nA} nieuwe acties van TapParfum`, naar: 'acties' })
  const nP = actieveProducten(producten.value).filter(p => !(t.prodGezienP || []).includes(p.id)).length
  if (nP) uit.push({ ic: '🧴', txt: nP === 1 ? 'Nieuw product onderweg — bekijk de tijdlijn' : `${nP} nieuwe producten onderweg`, naar: 'producten' })
  const fb = acties.value.filter(a => !a.archived && a.eind && a.eind < vd && doetMee(t, a.id) && !heeftRes(t, a.id)).length
  if (fb) uit.push({ ic: '📊', txt: 'Actie afgelopen — vertel kort of het werkte (en verdien punten)', naar: 'acties' })
  const afspr = (t.afspraken || []).filter(a => !a.done).length
  if (afspr) uit.push({ ic: '📌', txt: `${afspr} open afspra${afspr === 1 ? 'ak' : 'ken'} met je accountmanager`, naar: 'winkel' })
  return uit
})
const datum = new Intl.DateTimeFormat('nl-NL', { weekday: 'long', day: 'numeric', month: 'long' }).format(new Date())
// Vulmeter (signatuur): voortgang naar het jaardoel, anders naar het volgende niveau.
const meterPct = computed(() => {
  if (!auth.isPartner || !eigen.value) return null
  const jo = Number(eigen.value.jaaromzet) || 0
  const doel = Number(eigen.value.doel) || 0
  if (doel > 0) return Math.min(100, (jo / doel) * 100)
  const lv = mijnNiveau.value
  if (!lv || !lv.nextMin) return null
  return Math.max(0, Math.min(100, ((jo * marge.value - lv.min) / (lv.nextMin - lv.min)) * 100))
})
const meterLabel = computed(() => {
  if (!eigen.value) return ''
  return (Number(eigen.value.doel) || 0) > 0 ? 'van jullie jaardoel'
    : (mijnNiveau.value && mijnNiveau.value.next ? 'naar niveau ' + mijnNiveau.value.next : '')
})
</script>

<template>
  <div>
    <header class="held">
      <div>
        <p class="eyebrow">TapParfum Portaal · {{ datum }}</p>
        <h1>{{ auth.isKantoor ? 'Kantoor-cockpit' : (auth.isAm ? 'Mijn overzicht' : 'Welkom') }}</h1>
      </div>
      <FlesMeter v-if="meterPct != null" :pct="meterPct" :label="meterLabel" />
    </header>
    <p v-if="fout" class="fout" role="alert">{{ fout }}</p>

    <!-- Tegels -->
    <div class="tegels">
      <div class="tegel" data-test="tile-winkels">
        <div class="cijfer">{{ st.items.length }}</div>
        <div class="lbl">{{ auth.isPartner ? 'winkel' : 'winkels' }}</div>
      </div>
      <div class="tegel" data-test="tile-omzet">
        <div class="cijfer">{{ eur0(omzetTot) }}</div>
        <div class="lbl">jaaromzet</div>
      </div>
      <div class="tegel" data-test="tile-open">
        <div class="cijfer">{{ openVragen }}</div>
        <div class="lbl">open meldingen</div>
      </div>
      <router-link v-if="!auth.isPartner" class="tegel klik" data-test="tile-taken" :to="{ name: 'taken' }">
        <div class="cijfer">{{ openTaken }}</div>
        <div class="lbl">open taken</div>
      </router-link>
      <div v-if="auth.isKantoor" class="tegel" data-test="tile-ams">
        <div class="cijfer">{{ ams.length }}</div>
        <div class="lbl">accountmanagers</div>
      </div>
      <div v-if="auth.isKantoor" class="tegel" data-test="tile-stagneert">
        <div class="cijfer amber">{{ stagneerders.length }}</div>
        <div class="lbl">stagneert</div>
      </div>
      <div v-if="auth.isKantoor" class="tegel" data-test="tile-blok">
        <div class="cijfer">{{ blok }}</div>
        <div class="lbl">geblokkeerd</div>
      </div>
    </div>

    <!-- Kantoor: bestellingen-KPI's -->
    <div v-if="bestelKpi" class="kaart bestelkpi" data-test="bestel-kpi">
      <h2>📦 Bestellingen (team)</h2>
      <div class="kpirij">
        <div class="kpi"><b>{{ eur0(bestelKpi.inkoop) }}</b><span>inkoop dit jaar</span></div>
        <div class="kpi"><b>{{ bestelKpi.maandN }}</b><span>bestellingen deze maand</span></div>
        <div class="kpi"><b :class="{ amber: bestelKpi.stil > 0 }">{{ bestelKpi.stil }}</b><span>60+ dgn geen bestelling</span></div>
      </div>
    </div>

    <!-- Kantoor/AM: stagnatie-aandachtslijst -->
    <div v-if="(auth.isKantoor || auth.isAm) && stagneerders.length" class="kaart" data-test="aandacht">
      <h2>⚠️ Vraagt aandacht — stagnerende tappunten</h2>
      <router-link v-for="t in stagneerders" :key="t.snelstart" class="rij klik" data-test="aandacht-rij"
                   :to="{ name: 'winkel', params: { code: t.snelstart } }">
        <b>{{ t.name }}</b>
        <span class="mo">{{ t.snelstart }}</span>
        <span class="bedrag">{{ eur0(t.jaaromzet) }}</span>
        <span class="pijl">→ heractiveren</span>
      </router-link>
    </div>

    <!-- Partner: stats-KPI-rij -->
    <div v-if="stats" class="pstats" data-test="pstats">
      <div class="pstat"><b :class="{ groen: stats.officieel }">{{ stats.officieel ? '✓ Officieel' : 'Niveau ' + stats.niveau }}</b><span>status</span></div>
      <div class="pstat"><b>{{ stats.basis }}/{{ BASIS_MAX }}</b><span>basispunten</span></div>
      <div class="pstat"><b>{{ eur0(stats.winkelverkoop) }}</b><span>winkelverkoop</span></div>
      <div class="pstat"><b>{{ stats.voortgangPct == null ? '—' : stats.voortgangPct + '%' }}</b><span>{{ stats.voortgangLabel }}</span></div>
    </div>

    <!-- Partner: vieringen (mijlpalen) -->
    <div v-for="(v, i) in vieringen" :key="'v' + i" class="viering" role="status" data-test="viering-banner">
      <span class="ic">🎉</span><span class="ntxt">{{ vierTekst(v) }}</span>
      <button class="dicht" type="button" aria-label="Viering sluiten" :data-test="'viering-weg-' + i" @click="wisViering(v)">×</button>
    </div>

    <!-- Partner: nudges -->
    <router-link v-for="n in nudges" :key="n.txt" class="nudge" data-test="nudge"
                 :to="n.naar === 'winkel' ? { name: 'winkel', params: { code: eigen.snelstart } } : { name: n.naar }">
      <span class="ic">{{ n.ic }}</span><span class="ntxt">{{ n.txt }}</span><span class="pijl">→</span>
    </router-link>

    <!-- Partner: fase-kaart (onboarding -> terugverdienen -> jaardoel) -->
    <div v-if="fase" class="kaart fasekaart" :data-test="'fase-' + fase.key">
      <div class="kop"><h2>{{ fase.titel }}</h2>
        <b v-if="fase.pct != null" class="pct">{{ fase.pct }}%</b>
      </div>
      <div v-if="fase.pct != null" class="balk"><div class="vul" :style="{ width: fase.pct + '%' }"></div></div>
      <p class="regel">{{ fase.tekst }}</p>
      <router-link v-if="eigen" class="link" :to="{ name: 'winkel', params: { code: eigen.snelstart } }">→ Naar je winkelpagina</router-link>
    </div>

    <!-- Partner: deze week + vooruitblik -->
    <div v-if="week && week.doel" class="kaart weekkaart" data-test="weekkaart">
      <div class="weekring" :class="{ koers: week.koers }">
        <b>{{ week.flessen }}</b><small>/ {{ week.doel }}</small>
      </div>
      <div class="weekbody">
        <h2>Deze week</h2>
        <div class="balk"><div class="vul" :style="{ width: week.pct + '%' }"></div></div>
        <p class="regel">{{ week.koers ? 'Op koers 🔥 — weekdoel gehaald!' : `Nog ${Math.max(0, week.doel - week.flessen)} flessen tot je weekdoel.` }}</p>
        <p v-if="projectie" class="regel proj" data-test="projectie">📈 In dit tempo eindig je rond <b>{{ eur0(projectie.winkelomzet) }}</b> — niveau <b>{{ projectie.niveau }}</b> ({{ projectie.niveauR }}).</p>
      </div>
    </div>

    <!-- Partner: trofeeën-strip -->
    <div v-if="trofeeen.length" class="kaart" data-test="trofeeen">
      <h2>🏆 Jullie spaarcadeaus</h2>
      <div class="trofeeen">
        <router-link v-for="tr in trofeeen" :key="tr.key" class="trof" :class="{ gewonnen: tr.gewonnen }" :to="{ name: 'beloningen' }" :title="tr.r">
          <span class="tic">{{ tr.ic }}</span>
          <span class="tstatus">{{ tr.gewonnen ? '✓' : '🔒' }}</span>
        </router-link>
      </div>
    </div>

    <!-- Partner: berichtenkaart (v71 berichtKnopKaart) — vraag/bezoek/probleem/retour -->
    <div v-if="auth.isPartner && eigen" class="kaart" data-test="berichtkaart">
      <h2>💬 Contact met je accountmanager</h2>
      <p class="regel">Een vraag, bezoekverzoek, probleem of retour? Kies waar het over gaat.</p>
      <div class="soorten">
        <button v-for="s in BERICHT_SOORTEN" :key="s.k" type="button" class="soort" :class="{ aan: berSoort === s.k }"
                :data-test="'ber-soort-' + s.k" @click="kiesSoort(s.k)">{{ s.l }}</button>
      </div>
      <div v-if="berSoort" class="bercompose">
        <input v-if="berSoort === 'bezoek'" v-model="berDatum" type="date" data-test="ber-datum" aria-label="Voorkeursdatum" />
        <textarea v-else v-model="berTxt" rows="2" :data-test="'ber-txt'"
                  :placeholder="berSoort === 'retour' ? 'Wat wil je retourneren en waarom?' : (berSoort === 'probleem' ? 'Wat is het probleem?' : 'Je vraag…')"></textarea>
        <label v-if="berSoort === 'retour'" class="foto">📎 Foto (optioneel)
          <input type="file" accept="image/*" data-test="ber-foto" @change="berFoto = $event.target.files[0] || null" />
        </label>
        <button class="link-knop" type="button" data-test="ber-verstuur" @click="verstuurBericht">Versturen →</button>
      </div>
      <p v-if="bezoekMelding" class="ok" role="status" data-test="bezoek-melding">{{ bezoekMelding }}</p>
    </div>

    <!-- Partner: geur van de week -->
    <div v-if="auth.isPartner && eigen" class="kaart spotlight" data-test="spotlight">
      <div class="spkop"><span class="splbl">Geur van de week</span><b>{{ SPOTLIGHT.code }}</b></div>
      <p class="spnaam">{{ SPOTLIGHT.naam }}</p>
      <p class="regel">{{ SPOTLIGHT.tip }}</p>
    </div>

    <!-- Partner: waarom TapParfum -->
    <div v-if="auth.isPartner && eigen" class="usps" data-test="usps">
      <div v-for="u in USPS" :key="u.t" class="usp">
        <span class="uic">{{ u.ic }}</span><b>{{ u.t }}</b><span class="mo">{{ u.m }}</span>
      </div>
    </div>

    <!-- Partner: eigen winkel + niveau -->
    <div v-if="auth.isPartner && eigen" class="kaart" data-test="eigen-kaart">
      <div class="kop"><h2>{{ eigen.name }}</h2><span class="code">code {{ eigen.snelstart }}</span></div>
      <p class="regel">Jaaromzet: <b>{{ eur0(eigen.jaaromzet) }}</b></p>
      <template v-if="mijnNiveau">
        <p class="regel">Niveau:
          <b data-test="niveau-naam">{{ mijnNiveau.k }}</b> — {{ mijnNiveau.r }}
          <template v-if="mijnNiveau.next"> · nog {{ eur0(mijnNiveau.gap) }} tot niveau {{ mijnNiveau.next }}</template>
        </p>
        <div v-if="mijnNiveau.next && meterPct != null" class="balk"><div class="vul" :style="{ width: meterPct + '%' }"></div></div>
      </template>
      <router-link class="link" :to="{ name: 'winkel', params: { code: eigen.snelstart } }">→ Mijn winkelpagina</router-link>
    </div>

    <!-- Kantoor: per accountmanager -->
    <div v-if="auth.isKantoor && perAm.length" class="kaart">
      <h2>Per accountmanager</h2>
      <div v-for="r in perAm" :key="r.naam" class="rij" data-test="am-rij">
        <b>{{ r.naam }}</b>
        <span class="mo">{{ r.n }} winkel{{ r.n === 1 ? '' : 's' }}</span>
        <span class="bedrag">{{ eur0(r.omzet) }}</span>
      </div>
    </div>

    <!-- AM: top-winkels -->
    <div v-if="auth.isAm && topWinkels.length" class="kaart">
      <h2>Jouw winkels (top {{ topWinkels.length }})</h2>
      <router-link v-for="t in topWinkels" :key="t.snelstart" class="rij klik" data-test="top-winkel"
                   :to="{ name: 'winkel', params: { code: t.snelstart } }">
        <b>{{ t.name }}</b>
        <span class="mo">{{ t.snelstart }}</span>
        <span class="bedrag">{{ eur0(t.jaaromzet) }}</span>
      </router-link>
    </div>

    <!-- Iedereen: eerstvolgende bezoeken -->
    <div v-if="komend.length" class="kaart">
      <h2>Eerstvolgend</h2>
      <div v-for="i in komend" :key="i.id" class="rij" data-test="komend-item">
        <b>{{ WINKEL[i.tappunt_snelstart] || i.tappunt_snelstart }}</b>
        <span class="mo">{{ i.type === 'telefoon' ? '📞' : '📍' }} {{ i.datum }}<template v-if="i.tijd"> · {{ i.tijd }}</template></span>
        <span class="mo">{{ i.status === 'voorgesteld' ? 'wacht op winkel' : 'geaccepteerd' }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.held{display:flex;align-items:center;justify-content:space-between;gap:18px;background:linear-gradient(115deg,var(--soft),#fff 72%);border:1px solid var(--line);border-radius:18px;padding:18px 22px;margin-bottom:14px}
.eyebrow{margin:0 0 3px;font-size:11px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:var(--coral-d)}
h1{margin:0;font-size:24px}
h2{margin:0 0 10px;font-size:15px}
.tegels{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-bottom:14px}
.tegel{background:#fff;border:1px solid var(--line);border-radius:14px;padding:14px 16px;color:inherit;text-decoration:none;display:block}
.tegel.klik:hover{border-color:var(--coral)}
.cijfer{font-size:22px;font-weight:800;color:var(--coral)}
.lbl{font-size:12px;color:var(--grey);font-weight:700}
.kaart{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px;margin-bottom:12px}
.viering{display:flex;align-items:center;gap:10px;background:var(--green-soft);border:1px solid #bcd9a0;color:#2c5a12;border-radius:12px;padding:10px 14px;margin-bottom:8px;font-size:13.5px;font-weight:600}
.viering .ntxt{flex:1}
.dicht{background:none;border:0;color:#2c5a12;font-size:17px;font-weight:800;cursor:pointer;line-height:1}
.nudge{display:flex;align-items:center;gap:10px;background:#fff;border:1px solid var(--line);border-left:4px solid var(--coral);border-radius:12px;padding:10px 14px;margin-bottom:8px;color:inherit;text-decoration:none;font-size:13.5px;font-weight:600}
.nudge:hover{border-color:var(--coral)}
.nudge .ntxt{flex:1}
.nudge .pijl{color:var(--coral-d);font-weight:800}
.pstats{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin-bottom:12px}
.pstat{background:#fff;border:1px solid var(--line);border-radius:14px;padding:12px 14px}
.pstat b{display:block;font-size:17px;color:var(--coral-d)}
.pstat b.groen{color:#2c5a12}
.pstat span{font-size:12px;color:var(--grey);font-weight:700}
.trofeeen{display:flex;gap:10px;flex-wrap:wrap}
.trof{position:relative;width:52px;height:52px;border-radius:14px;background:var(--cream);border:1px solid var(--line);display:flex;align-items:center;justify-content:center;font-size:24px;text-decoration:none;filter:grayscale(1);opacity:.55}
.trof.gewonnen{filter:none;opacity:1;border-color:#bcd9a0;background:var(--green-soft)}
.tstatus{position:absolute;bottom:-4px;right:-4px;font-size:12px}
.bezrij{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-top:8px}
.bezrij input{padding:8px 10px;border:1.5px solid var(--line);border-radius:10px;font-size:14px}
.link-knop{background:var(--coral);color:#fff;border:0;border-radius:10px;padding:9px 15px;font-weight:800;cursor:pointer;font-size:13px}
.link-knop:disabled{opacity:.5}
.spotlight{border-left:4px solid var(--coral)}
.spkop{display:flex;align-items:baseline;gap:10px}
.splbl{font-size:10.5px;font-weight:800;text-transform:uppercase;letter-spacing:.08em;color:var(--coral-d)}
.spkop b{font-size:18px}
.spnaam{margin:4px 0;font-weight:700}
.usps{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin-bottom:12px}
.usp{background:#fff;border:1px solid var(--line);border-radius:14px;padding:14px;display:flex;flex-direction:column;gap:3px}
.uic{font-size:22px}
.usp b{font-size:14px}
.ok{color:#2c5a12;font-size:13px;margin:6px 0 0}
.fasekaart{border-left:4px solid var(--coral)}
.fasekaart .pct{margin-left:auto;color:var(--coral-d);font-size:18px;font-variant-numeric:tabular-nums}
.kop{display:flex;align-items:center;gap:10px}
.code{color:var(--grey);font-size:12.5px}
.regel{margin:6px 0;font-size:14px}
.balk{height:8px;border-radius:6px;background:#f0ebe3;overflow:hidden;margin:8px 0}
.vul{height:100%;background:var(--coral)}
.link{color:var(--coral);font-weight:700;text-decoration:none;font-size:13.5px}
.rij{display:flex;align-items:center;gap:12px;padding:8px 0;border-bottom:1px solid var(--line);font-size:14px;color:inherit;text-decoration:none}
.rij:last-child{border-bottom:0}
.rij.klik:hover b{color:var(--coral)}
.mo{color:var(--grey);font-size:12.5px}
.bedrag{margin-left:auto;font-weight:700}
.fout{color:#b3261e}

.weekkaart{display:flex;gap:16px;align-items:center}
.weekring{width:74px;height:74px;border-radius:50%;flex-shrink:0;display:flex;flex-direction:column;align-items:center;justify-content:center;background:var(--soft);border:3px solid var(--coral)}
.weekring.koers{background:var(--green-soft);border-color:var(--green)}
.weekring b{font-size:22px;font-weight:900;line-height:1}
.weekring small{font-size:11px;color:var(--grey);font-weight:700}
.weekbody{flex:1;min-width:0}
.weekbody .balk{height:8px;background:#f0ebe3;overflow:hidden;margin:6px 0}
.weekbody .vul{height:100%;background:var(--coral)}
.proj{color:var(--coral-d);font-weight:600;margin-top:6px}
.soorten{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0}
.soort{background:var(--cream);border:1.5px solid var(--line);padding:8px 13px;font-size:13px;font-weight:700;color:var(--grey);cursor:pointer}
.soort.aan{border-color:var(--coral);background:var(--soft);color:var(--coral-d)}
.bercompose{display:flex;flex-direction:column;gap:8px;max-width:460px}
.bercompose textarea,.bercompose input[type=date]{padding:9px 11px;border:1.5px solid var(--line);font-size:14px;font-family:inherit}
.bercompose textarea:focus,.bercompose input:focus{border-color:var(--coral);outline:none}
.foto{font-size:12.5px;font-weight:700;color:var(--grey);display:flex;flex-direction:column;gap:4px}

.cijfer.amber{color:var(--amber)}
.bestelkpi .kpirij{display:grid;grid-template-columns:repeat(3,1fr);gap:0;border:1px solid var(--line);margin-top:4px}
.bestelkpi .kpi{padding:12px 14px;border-right:1px solid var(--line);display:flex;flex-direction:column;gap:3px}
.bestelkpi .kpi:last-child{border-right:0}
.bestelkpi .kpi b{font-size:20px;font-weight:800;font-variant-numeric:tabular-nums}
.bestelkpi .kpi b.amber{color:var(--amber)}
.bestelkpi .kpi span{font-size:11px;color:var(--grey);text-transform:uppercase;letter-spacing:.4px;font-weight:700}
@media(max-width:620px){.bestelkpi .kpirij{grid-template-columns:1fr}.bestelkpi .kpi{border-right:0;border-bottom:1px solid var(--line)}}
[data-test=aandacht] .rij .pijl{margin-left:auto;color:var(--coral-d);font-weight:700;font-size:12.5px;white-space:nowrap}
[data-test=aandacht]{border-left:4px solid var(--amber)}
</style>
