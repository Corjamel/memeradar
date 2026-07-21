<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../../../stores/auth.js'

const auth = useAuth()
const router = useRouter()
const email = ref('')
const wachtwoord = ref('')
const bezig = ref(false)

async function inloggen() {
  if (bezig.value) return
  bezig.value = true
  const ok = await auth.signIn(email.value.trim(), wachtwoord.value)
  bezig.value = false
  if (ok) router.push({ name: 'home' })
}
</script>

<template>
  <div class="wrap">
    <form class="card" @submit.prevent="inloggen">
      <div class="brand">TAPPARFUM</div>
      <h1>Portaal</h1>
      <label>E-mail
        <input v-model="email" type="email" autocomplete="username" required placeholder="jij@voorbeeld.nl" />
      </label>
      <label>Wachtwoord
        <input v-model="wachtwoord" type="password" autocomplete="current-password" required placeholder="••••••••" />
      </label>
      <p v-if="auth.error" class="err" role="alert">{{ auth.error }}</p>
      <button class="btn" type="submit" :disabled="bezig">
        {{ bezig ? 'Bezig…' : 'Inloggen' }}
      </button>
    </form>
  </div>
</template>

<style scoped>
.wrap{min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
.card{background:#fff;border:1px solid var(--line);border-radius:16px;padding:28px;width:100%;max-width:360px;box-shadow:0 8px 30px rgba(0,0,0,.06);display:flex;flex-direction:column;gap:12px}
.brand{font-weight:800;letter-spacing:.16em;color:var(--coral)}
h1{margin:0 0 6px;font-size:22px}
label{display:flex;flex-direction:column;gap:5px;font-size:13px;font-weight:700;color:var(--grey)}
input{padding:10px 12px;border:1.5px solid var(--line);border-radius:10px;font-size:15px}
input:focus{outline:none;border-color:var(--coral)}
.err{color:#b3261e;font-size:13px;margin:0}
.btn{margin-top:6px;background:var(--coral);color:#fff;border:0;border-radius:10px;padding:11px;font-weight:800;font-size:15px;cursor:pointer}
.btn:disabled{opacity:.6;cursor:default}
</style>
