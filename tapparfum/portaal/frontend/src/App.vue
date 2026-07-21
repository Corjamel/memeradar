<script setup>
import { useAuth } from './stores/auth.js'
import { useRouter } from 'vue-router'
const auth = useAuth()
const router = useRouter()
const ROL_LABEL = { kantoor: 'Kantoor', am: 'Accountmanager', partner: 'Partner' }
async function uitloggen() { await auth.signOut(); router.push({ name: 'login' }) }
</script>

<template>
  <div class="app">
    <header v-if="auth.ingelogd" class="topbar">
      <span class="brand">TAPPARFUM</span>
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
.topbar{display:flex;align-items:center;gap:12px;padding:12px 18px;border-bottom:1px solid #eee;background:#fff}
.brand{font-weight:800;letter-spacing:.14em;color:#e2694f}
.spacer{flex:1}
.rol{font-size:13px;color:#777;font-weight:700}
.content{max-width:1000px;margin:0 auto;padding:20px}
.btn{background:#e2694f;color:#fff;border:0;border-radius:8px;padding:7px 12px;font-weight:700;cursor:pointer}
.btn:hover{filter:brightness(1.05)}
</style>
