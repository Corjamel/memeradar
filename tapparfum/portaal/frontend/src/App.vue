<script setup>
import { ref } from 'vue'
import { useAuth } from './stores/auth.js'
import { useTappunten } from './modules/tappunten/store.js'
import { useRouter } from 'vue-router'
import ZoekOverlay from './components/ZoekOverlay.vue'
const auth = useAuth()
const router = useRouter()
const ROL_LABEL = { kantoor: 'Kantoor', am: 'Accountmanager', partner: 'Partner' }
const zoekOpen = ref(false)
async function uitloggen() {
  await auth.signOut()
  // Module-stores leegmaken: de volgende gebruiker op dit apparaat mag nooit
  // data van de vorige sessie in het geheugen aantreffen.
  useTappunten().$reset()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="app">
    <header v-if="auth.ingelogd" class="topbar">
      <span class="brand" translate="no">TAPPARFUM</span>
      <nav class="mainnav" aria-label="Hoofdmenu">
        <router-link :to="{ name: 'home' }">Start</router-link>
        <router-link v-if="auth.role !== 'partner'" :to="{ name: 'vandaag' }">Vandaag</router-link>
        <router-link v-if="auth.role !== 'partner'" :to="{ name: 'trajecten' }">Trajecten</router-link>
        <router-link :to="{ name: 'winkels' }">Winkels</router-link>
        <router-link :to="{ name: 'agenda' }">Agenda</router-link>
        <router-link :to="{ name: 'berichten' }">Berichten</router-link>
        <router-link :to="{ name: 'acties' }">Acties</router-link>
        <router-link :to="{ name: 'beloningen' }">Beloningen</router-link>
        <router-link :to="{ name: 'producten' }">Producten</router-link>
        <router-link v-if="auth.role === 'partner'" :to="{ name: 'bestellen' }">Bestellen</router-link>
        <router-link :to="{ name: 'academy' }">Academy</router-link>
        <router-link v-if="auth.role !== 'partner'" :to="{ name: 'bestellingen' }">Bestellingen</router-link>
        <router-link v-if="auth.role !== 'partner'" :to="{ name: 'deals' }">Deals</router-link>
        <router-link v-if="auth.role !== 'partner'" :to="{ name: 'taken' }">Taken</router-link>
        <router-link v-if="auth.role !== 'partner'" :to="{ name: 'calculator' }">Calculator</router-link>
        <router-link v-if="auth.role !== 'partner'" :to="{ name: 'analyse' }">Analyse</router-link>
        <router-link v-if="auth.magBeheer" :to="{ name: 'beheer' }">Beheer</router-link>
      </nav>
      <span class="spacer"></span>
      <button v-if="auth.role !== 'partner'" class="zoek" type="button" aria-label="Zoeken"
              data-test="zoek-knop" @click="zoekOpen = true">🔍</button>
      <span class="rol">{{ ROL_LABEL[auth.role] || auth.role }}</span>
      <button class="btn" @click="uitloggen">Uitloggen</button>
    </header>
    <main class="content">
      <router-view />
    </main>
    <ZoekOverlay v-if="zoekOpen" @sluit="zoekOpen = false" />
  </div>
</template>

<style scoped>
.topbar{position:sticky;top:0;z-index:30;display:flex;align-items:center;gap:16px;padding:12px 18px;border-bottom:1px solid var(--line);background:rgba(255,255,255,.94);backdrop-filter:blur(8px);flex-wrap:wrap}
.brand{font-weight:800;letter-spacing:.16em;color:var(--coral);font-size:15px}
.mainnav{display:flex;gap:4px;flex-wrap:wrap}
.mainnav a{color:var(--ink);text-decoration:none;font-weight:700;font-size:13.5px;padding:6px 10px;border-radius:8px}
.mainnav a:hover{background:var(--cream)}
.mainnav a.router-link-active{color:var(--coral-d);background:var(--soft)}
.spacer{flex:1}
.zoek{background:var(--cream);border:1px solid var(--line);border-radius:10px;padding:6px 11px;font-size:14px;cursor:pointer}
.zoek:hover{border-color:var(--coral)}
.rol{font-size:12px;color:var(--grey);font-weight:800;letter-spacing:.06em;text-transform:uppercase;background:var(--cream);border:1px solid var(--line);border-radius:999px;padding:4px 12px}
.content{max-width:1000px;margin:0 auto;padding:20px}
.btn{background:var(--coral);color:#fff;border:0;border-radius:10px;padding:8px 14px;font-weight:800;cursor:pointer}
.btn:hover{background:var(--coral-d)}
</style>
