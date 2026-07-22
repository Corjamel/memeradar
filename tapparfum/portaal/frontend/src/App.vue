<script setup>
import { useAuth } from './stores/auth.js'
import { useTappunten } from './modules/tappunten/store.js'
import { useRouter } from 'vue-router'
const auth = useAuth()
const router = useRouter()
const ROL_LABEL = { kantoor: 'Kantoor', am: 'Accountmanager', partner: 'Partner' }
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
      <span class="brand">TAPPARFUM</span>
      <nav class="mainnav">
        <router-link :to="{ name: 'home' }">Start</router-link>
        <router-link :to="{ name: 'winkels' }">Winkels</router-link>
        <router-link v-if="auth.role !== 'partner'" :to="{ name: 'berichten' }">Berichten</router-link>
      </nav>
      <span class="spacer"></span>
      <span class="rol">{{ ROL_LABEL[auth.role] || auth.role }}</span>
      <button class="btn" @click="uitloggen">Uitloggen</button>
    </header>
    <main class="content">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.topbar{display:flex;align-items:center;gap:16px;padding:12px 18px;border-bottom:1px solid #eee;background:#fff;flex-wrap:wrap}
.brand{font-weight:800;letter-spacing:.14em;color:#e2694f}
.mainnav{display:flex;gap:4px}
.mainnav a{color:#21343f;text-decoration:none;font-weight:700;font-size:13.5px;padding:6px 10px;border-radius:8px}
.mainnav a:hover{background:#faf3ef}
.mainnav a.router-link-active{color:#e2694f;background:#fdeee7}
.spacer{flex:1}
.rol{font-size:13px;color:#777;font-weight:700}
.content{max-width:1000px;margin:0 auto;padding:20px}
.btn{background:#e2694f;color:#fff;border:0;border-radius:8px;padding:7px 12px;font-weight:700;cursor:pointer}
.btn:hover{filter:brightness(1.05)}
</style>
