<script setup>
// Welkom-rondleiding (v71 openWelkom): bij de eerste login per rol vier korte
// stappen die wegwijs maken. "Gezien" onthouden we in localStorage per rol +
// e-mail — puur UX (geen data, geen beveiliging), dus RLS speelt hier niet.
// Altijd terug te halen via de ❓ in de topbar (force).
import { computed } from 'vue'
import { useAuth } from '../stores/auth.js'

const props = defineProps({ force: { type: Boolean, default: false } })
const emit = defineEmits(['sluit'])
const auth = useAuth()

const STAPPEN = {
  partner: [
    ['🏠', 'Jouw dashboard', 'Je omzet, je groeipad en wat er speelt — alles op één scherm.'],
    ['🧾', 'De kassa', 'Tik elke verkoop per flesmaat. Zo zie je welke maten en geuren bij jou lopen.'],
    ['📣', 'Acties & nieuwe producten', 'Doe mee met campagnes en zie wanneer nieuwe geuren leverbaar zijn.'],
    ['🏆', 'De Sales Game', 'Groei het hardst en win de hoofdprijs — het klassement staat op je dashboard.']
  ],
  am: [
    ['☀️', 'Vandaag', 'Je werklijst: wie belt of bezoekt je vandaag? Begin hier, elke dag.'],
    ['👥', 'Mijn winkels', 'Al je klanten. Registreer elk bezoek, telefoontje en mailtje — dat is je bewijs én je bonus.'],
    ['💶', 'Zo verdien je je bonus', 'Elke klant die jij het traject in helpt en die écht actief wordt, telt voor je maandbonus.'],
    ['🏆', 'Sales Game', 'Help je tappunten groeien — jouw winkels op het podium is jouw succes.']
  ],
  kantoor: [
    ['📊', 'Cockpit', 'Alle tappunten van alle accountmanagers, met omzet en status.'],
    ['📣', 'Acties & producten', 'Zet campagnes en lanceringen live — het hele netwerk ziet ze direct.'],
    ['👥', 'Accountmanagers', 'De ranking op groei en activaties — dezelfde meting als hun bonus.'],
    ['⚙️', 'Beheer', 'Accounts, rechten, blokkades, regels en AVG — achter jouw toegang.']
  ]
}
const stappen = computed(() => STAPPEN[auth.role] || STAPPEN.am)
const naam = computed(() => (auth.user && auth.user.email) || '')

function aandeSlag() {
  try { localStorage.setItem(sleutel(), '1') } catch (e) { /* onthouden lukt niet, niet erg */ }
  emit('sluit')
}
function sleutel() { return 'tp_welkom::' + auth.role + '::' + String(naam.value).toLowerCase() }
</script>

<template>
  <div class="welk" role="dialog" aria-modal="true" aria-label="Welkom-rondleiding" data-test="welkom" @click.self="aandeSlag">
    <div class="kaart">
      <button class="dicht" type="button" aria-label="Sluiten" data-test="welkom-sluit" @click="aandeSlag">×</button>
      <div class="kop">👋 Welkom{{ naam ? ', ' + naam : '' }}!</div>
      <p class="intro">Dit is jouw TapParfum-portaal — in vier stappen wegwijs:</p>
      <div v-for="(s, i) in stappen" :key="i" class="stap" data-test="welkom-stap">
        <span class="em">{{ s[0] }}</span>
        <div><b>{{ s[1] }}</b><span class="d">{{ s[2] }}</span></div>
      </div>
      <div class="voet">
        <button class="btn" type="button" data-test="welkom-start" @click="aandeSlag">Aan de slag →</button>
        <span class="note">Terugkijken kan altijd via de ❓ bovenin.</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.welk{position:fixed;inset:0;z-index:8000;background:rgba(42,33,28,.5);display:flex;align-items:center;justify-content:center;padding:20px}
.kaart{background:#fff;border:1px solid var(--line);border-radius:18px;padding:22px 24px;max-width:520px;width:100%;max-height:90vh;overflow:auto;position:relative}
.dicht{position:absolute;top:14px;right:16px;background:none;border:0;font-size:22px;line-height:1;font-weight:800;color:var(--coral-d);cursor:pointer}
.kop{font-family:var(--font-display,inherit);font-size:20px;font-weight:800;margin:0 0 4px}
.intro{color:var(--grey);font-size:13px;margin:0 0 6px}
.stap{display:flex;gap:12px;margin:12px 0}
.em{font-size:22px;flex-shrink:0}
.stap b{display:block;font-size:14.5px}
.stap .d{color:var(--grey);font-size:13.5px}
.voet{display:flex;gap:10px;align-items:center;margin-top:16px;flex-wrap:wrap}
.btn{background:var(--coral);color:#fff;border:0;border-radius:10px;padding:10px 16px;font-weight:800;cursor:pointer;font-size:13.5px}
.btn:hover{background:var(--coral-d)}
.note{color:var(--grey);font-size:12px;margin:0}
</style>
