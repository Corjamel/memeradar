<script setup>
import { computed, ref, watch, onMounted, onUnmounted } from 'vue'
import { useAuth } from './stores/auth.js'
import { useTappunten } from './modules/tappunten/store.js'
import { useRouter, useRoute } from 'vue-router'
import ZoekOverlay from './components/ZoekOverlay.vue'
import ToastHost from './components/ToastHost.vue'
import WelkomOverlay from './components/WelkomOverlay.vue'
import { ICONS } from './lib/icons.js'
import { haalWinkelvragen } from './modules/winkelvragen/api.js'
import { haalTaken } from './modules/taken/api.js'
import { haalCentral } from './modules/beheer/api.js'
import { applyBrand } from './lib/brand.js'

const auth = useAuth()
const router = useRouter()
const route = useRoute()
const ROL_LABEL = { kantoor: 'Kantoor', am: 'Accountmanager', partner: 'Partner' }
const zoekOpen = ref(false)

// Welkom-rondleiding (v71): eerste login per rol toont de tour; daarna
// terug te halen via de ❓ in de topbar. "Gezien" staat in localStorage.
const welkomOpen = ref(false)
const welkomForce = ref(false)
function welkomGezien() {
  // Test-escape: de e2e-suite onderdrukt de rondleiding zodat de modal geen
  // klikken opvangt. In productie is dit vlaggetje er niet.
  if (typeof window !== 'undefined' && window.__TP_NO_WELKOM) return true
  try {
    const email = String((auth.user && auth.user.email) || '').toLowerCase()
    return localStorage.getItem('tp_welkom::' + auth.role + '::' + email) === '1'
  } catch (e) { return true }
}
function toonWelkom() { welkomForce.value = true; welkomOpen.value = true }
// Op zowel ingelogd als rol letten: de rol wordt ná het zetten van de user
// asynchroon bepaald, dus pas als die er is weten we welke rondleiding past.
watch(() => [auth.ingelogd, auth.role], ([ja, rol]) => {
  if (ja && rol && !welkomGezien()) { welkomForce.value = false; welkomOpen.value = true }
}, { immediate: true })

// Nav-tellers (v71 .bdg): open meldingen op Berichten, open taken op Taken.
// Ververst bij elke navigatie zodat de badge meteen zakt na een actie.
const openVragen = ref(0)
const openTaken = ref(0)
async function laadBadges() {
  if (!auth.ingelogd) { openVragen.value = 0; openTaken.value = 0; return }
  try {
    const v = await haalWinkelvragen()
    openVragen.value = (v || []).filter(x => x.status === 'open').length
  } catch { openVragen.value = 0 }
  if (auth.role !== 'partner') {
    try {
      const t = await haalTaken()
      openTaken.value = (t || []).filter(x => !x.klaar).length
    } catch { openTaken.value = 0 }
  } else openTaken.value = 0
}
watch(() => [auth.ingelogd, route.name], laadBadges, { immediate: true })
const badges = computed(() => ({ berichten: openVragen.value, taken: openTaken.value }))

// Titel in de topbar = het label van de actieve navigatie-ingang.
const TITELS = {
  home: 'Mijn winkels', vandaag: 'Vandaag', trajecten: 'Trajecten', winkels: 'Winkels',
  winkel: 'Winkel', 'winkel-partner': 'Partnerweergave', agenda: 'Agenda', bezoeken: 'Bezoeken', berichten: 'Berichten', acties: 'Acties',
  beloningen: 'Beloningen', game: 'Sales Game', producten: 'Producten', bestellen: 'Bestellen',
  geuren: 'Geurbibliotheek', community: 'Community', academy: 'Academy', kennisbank: 'Kennisbank',
  proces: 'Proces', formulieren: 'Formulieren', bestellingen: 'Bestellingen', deals: 'Deals',
  taken: 'Taken', calculator: 'Calculator', analyse: 'Analyse', team: 'Accountmanagers', beheer: 'Beheer'
}
// Kantoor kan de schermtitels overschrijven (central 'teksten', v71 title.<route>).
const teksten = ref({})
const titel = computed(() => teksten.value['title.' + route.name] || TITELS[route.name] || 'TapParfum')
// De navigatie-labels mogen dezelfde override volgen (title.<route>).
function navLabel(naam, standaard) { return teksten.value['title.' + naam] || standaard }

// Navigatie-opbouw: drie groepen zoals in v71 (Dagelijks / Assortiment & leren /
// Beheer & inzicht). `p` = ook voor partner zichtbaar; anders alleen AM/kantoor.
const isPartner = computed(() => auth.role === 'partner')
const GROEPEN = computed(() => [
  { groep: 'Dagelijks', items: [
    { naam: 'home', label: 'Start', ic: 'dashboard' },
    !isPartner.value && { naam: 'vandaag', label: 'Vandaag', ic: 'vandaag' },
    !isPartner.value && { naam: 'trajecten', label: 'Trajecten', ic: 'refresh' },
    { naam: 'winkels', label: 'Winkels', ic: 'tappunten' },
    { naam: 'agenda', label: 'Agenda', ic: 'agenda' },
    !isPartner.value && { naam: 'bezoeken', label: 'Bezoeken', ic: 'bezoek' },
    { naam: 'berichten', label: 'Berichten', ic: 'inbox' },
    { naam: 'acties', label: 'Acties', ic: 'spark' },
    { naam: 'beloningen', label: 'Beloningen', ic: 'gift' },
    auth.magGameBeheren && { naam: 'game', label: 'Game', ic: 'trofee' }
  ].filter(Boolean) },
  { groep: 'Assortiment & leren', items: [
    { naam: 'producten', label: 'Producten', ic: 'vial' },
    isPartner.value && { naam: 'bestellen', label: 'Bestellen', ic: 'bestellen' },
    { naam: 'geuren', label: 'Geuren', ic: 'geur' },
    { naam: 'merk', label: 'Merk & Assets', ic: 'merk' },
    { naam: 'community', label: 'Community', ic: 'community' },
    { naam: 'academy', label: 'Academy', ic: 'academy' },
    { naam: 'kennisbank', label: 'Kennis', ic: 'kennis' },
    !isPartner.value && { naam: 'proces', label: 'Proces', ic: 'proces' },
    !isPartner.value && { naam: 'formulieren', label: 'Formulieren', ic: 'check' }
  ].filter(Boolean) },
  !isPartner.value && { groep: 'Sturing', items: [
    { naam: 'bestellingen', label: 'Bestellingen', ic: 'bestellen' },
    { naam: 'deals', label: 'Deals', ic: 'procent' },
    { naam: 'taken', label: 'Taken', ic: 'check' },
    { naam: 'calculator', label: 'Calculator', ic: 'calculator' },
    auth.magAnalyse && { naam: 'analyse', label: 'Analyse', ic: 'omzet' },
    auth.magTeam && { naam: 'team', label: 'Team', ic: 'users' },
    auth.magBeheer && { naam: 'beheer', label: 'Beheer', ic: 'spark' }
  ].filter(Boolean) }
].filter(Boolean))

const initialen = computed(() => {
  const e = (auth.user && auth.user.email) || ''
  return e.slice(0, 2).toUpperCase() || 'TP'
})

// "/"-sneltoets opent zoeken (v71 r.4337) — behalve tijdens typen in een veld.
function sneltoets(e) {
  if (e.key !== '/' || !auth.ingelogd || auth.role === 'partner') return
  const t = e.target
  const tag = (t && t.tagName) || ''
  if (/^(INPUT|TEXTAREA|SELECT)$/.test(tag) || (t && t.isContentEditable)) return
  e.preventDefault()
  zoekOpen.value = true
}
onMounted(() => { window.addEventListener('keydown', sneltoets); window.addEventListener('tp-brand', laadBrand) })
onUnmounted(() => { window.removeEventListener('keydown', sneltoets); window.removeEventListener('tp-brand', laadBrand) })

// Huisstijl (central 'brand') netwerkbreed toepassen zodra we ingelogd zijn —
// central is alleen leesbaar voor ingelogde gebruikers.
const logoTekst = ref('TAPPARFUM')
async function laadBrand() {
  try {
    const b = (await haalCentral('brand')) || {}
    applyBrand(b)
    logoTekst.value = b.logoTekst ? String(b.logoTekst).toUpperCase() : 'TAPPARFUM'
  } catch (e) { /* standaard-huisstijl */ }
  try {
    const t = (await haalCentral('teksten')) || {}
    teksten.value = (t && typeof t === 'object') ? t : {}
  } catch (e) { teksten.value = {} }
}
watch(() => auth.ingelogd, (ja) => { if (ja) laadBrand() }, { immediate: true })

async function uitloggen() {
  welkomOpen.value = false
  await auth.signOut()
  // Module-stores leegmaken: de volgende gebruiker op dit apparaat mag nooit
  // data van de vorige sessie in het geheugen aantreffen.
  useTappunten().$reset()
  router.push({ name: 'login' })
}
</script>

<template>
  <div :class="auth.ingelogd ? 'shell' : 'bare'">
    <aside v-if="auth.ingelogd" class="side">
      <div class="logo"><span class="dot"></span><b translate="no">{{ logoTekst }}</b></div>
      <nav class="nav" aria-label="Hoofdmenu">
        <template v-for="g in GROEPEN" :key="g.groep">
          <div class="navgroup">{{ g.groep }}</div>
          <router-link v-for="it in g.items" :key="it.naam" :to="{ name: it.naam }"
                       class="nav-a" active-class="on">
            <span class="ic" v-html="ICONS[it.ic]"></span>{{ navLabel(it.naam, it.label) }}
            <span v-if="badges[it.naam]" class="bdg" :data-test="'bdg-' + it.naam">{{ badges[it.naam] }}</span>
          </router-link>
        </template>
      </nav>
      <div class="profilebox">
        <div class="who">{{ (auth.user && auth.user.email) || 'Ingelogd' }}</div>
        <div class="role">{{ ROL_LABEL[auth.role] || auth.role }}</div>
        <button class="lo" @click="uitloggen">Uitloggen</button>
      </div>
    </aside>

    <div class="col">
      <header v-if="auth.ingelogd" class="topbar">
        <button v-if="route.name !== 'home'" class="tb-terug" type="button" aria-label="Terug"
                data-test="terug-knop" @click="router.back()">←</button>
        <span class="tb-title">{{ titel }}</span>
        <span class="tb-sp"></span>
        <button v-if="auth.role !== 'partner'" class="tb-zoek" type="button" aria-label="Zoeken"
                data-test="zoek-knop" @click="zoekOpen = true"><span class="ic" v-html="ICONS.search"></span></button>
        <button class="tb-help" type="button" aria-label="Rondleiding" title="Rondleiding"
                data-test="help-knop" @click="toonWelkom">❓</button>
        <span class="tb-role rol">{{ ROL_LABEL[auth.role] || auth.role }}</span>
        <span class="tb-av">{{ initialen }}</span>
      </header>
      <main class="content">
        <router-view />
      </main>
    </div>
    <ZoekOverlay v-if="zoekOpen" @sluit="zoekOpen = false" />
    <WelkomOverlay v-if="welkomOpen" :force="welkomForce" @sluit="welkomOpen = false" />
    <ToastHost />
  </div>
</template>

<style scoped>
.shell{display:grid;grid-template-columns:248px 1fr;min-height:100vh}
.side{background:#fff;border-right:1px solid var(--line);display:flex;flex-direction:column;position:sticky;top:0;height:100vh}
.logo{display:flex;align-items:center;gap:10px;padding:22px 22px 18px;font-weight:800;letter-spacing:.16em;font-size:16px;text-transform:uppercase;border-bottom:1px solid var(--line)}
.logo b{color:var(--ink)}
.logo .dot{width:14px;height:14px;border-radius:50%;background:var(--sig);flex-shrink:0}
.nav{flex:1;padding:8px 0;overflow:auto}
.navgroup{font-size:10px;font-weight:800;letter-spacing:1.2px;color:var(--grey);text-transform:uppercase;padding:14px 22px 5px}
.nav-a{display:flex;align-items:center;gap:11px;padding:11px 22px;font-size:13.5px;font-weight:600;color:var(--ink-2);text-decoration:none;border-left:3px solid transparent}
.nav-a:hover{background:var(--soft)}
.nav-a.on{border-left-color:var(--coral);color:var(--coral);background:var(--soft)}
.ic{width:20px;height:20px;display:inline-flex;align-items:center;justify-content:center;flex-shrink:0}
.ic :deep(svg){width:19px;height:19px}
.bdg{margin-left:auto;background:var(--coral);color:#fff;font-size:10px;font-weight:800;min-width:18px;text-align:center;border-radius:9px;padding:1px 6px}
.profilebox{border-top:1px solid var(--line);padding:14px 18px}
.profilebox .who{font-size:12px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.profilebox .role{font-size:11px;color:var(--grey);text-transform:uppercase;letter-spacing:.5px;margin-top:1px}
.profilebox .lo{margin-top:10px;background:none;border:0;color:var(--coral-d);font-weight:800;font-size:11px;text-transform:uppercase;letter-spacing:.4px;cursor:pointer;padding:0}
.profilebox .lo:hover{text-decoration:underline}
.col{min-width:0}
.topbar{display:flex;align-items:center;gap:14px;padding:14px 32px;background:rgba(255,255,255,.86);backdrop-filter:saturate(1.2) blur(8px);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:20}
.tb-title{font-size:16px;font-weight:800;letter-spacing:-.2px;color:var(--ink)}
.tb-terug{background:#fff;border:1.5px solid var(--line);width:34px;height:34px;border-radius:8px;display:inline-flex;align-items:center;justify-content:center;cursor:pointer;color:var(--ink);font-size:16px;font-weight:800;flex-shrink:0}
.tb-terug:hover{border-color:var(--coral);color:var(--coral)}
.tb-sp{flex:1}
.tb-zoek,.tb-help{background:#fff;border:1.5px solid var(--line);width:34px;height:34px;display:inline-flex;align-items:center;justify-content:center;cursor:pointer;color:var(--ink)}
.tb-help{border-radius:8px;font-size:15px}
.tb-zoek:hover,.tb-help:hover{border-color:var(--coral);color:var(--coral)}
.tb-role{display:inline-flex;align-items:center;font-size:11.5px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;color:var(--coral-d);background:var(--soft);padding:6px 12px;border-radius:999px}
.tb-av{width:34px;height:34px;border-radius:50%;background:linear-gradient(135deg,var(--coral),var(--coral-d));color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:12px}
.content{padding:26px 32px 60px;max-width:1100px}
.bare{min-height:100vh}
.bare .content{padding:0;max-width:none}
@media(max-width:760px){
  .shell{grid-template-columns:1fr}
  .side{position:static;height:auto}
  .nav{display:flex;flex-wrap:wrap;padding:4px}
  .nav-a{border-left:none;border-bottom:3px solid transparent}
  .nav-a.on{border-left:none;border-bottom-color:var(--coral)}
  .navgroup{width:100%}
  .topbar{padding:12px 18px}
  .tb-title{display:none}
  .content{padding:18px}
}
</style>
