<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../../../stores/auth.js'

const auth = useAuth()
const router = useRouter()
const modus = ref('in')          // 'in' | 'nieuw' | 'reset'
const bezig = ref(false)
const melding = ref('')

const vorm = reactive({ email: '', wachtwoord: '' })
const nieuw = reactive({ soort: 'winkel', code: '', email: '', wachtwoord: '', wachtwoord2: '' })
const reset = reactive({ email: '' })

function wissel(m) { modus.value = m; melding.value = ''; auth.error = '' }

async function inloggen() {
  if (bezig.value) return
  bezig.value = true
  const ok = await auth.signIn(vorm.email.trim(), vorm.wachtwoord)
  bezig.value = false
  if (ok) router.push({ name: 'home' })
}

async function maakAccount() {
  if (bezig.value) return
  if (nieuw.wachtwoord.length < 8) { auth.error = 'Kies een wachtwoord van minimaal 8 tekens.'; return }
  if (nieuw.wachtwoord !== nieuw.wachtwoord2) { auth.error = 'De wachtwoorden zijn niet gelijk.'; return }
  bezig.value = true; auth.error = ''
  const res = nieuw.soort === 'am'
    ? await auth.signUpAm({ email: nieuw.email.trim(), wachtwoord: nieuw.wachtwoord })
    : await auth.signUpMetCode({ email: nieuw.email.trim(), wachtwoord: nieuw.wachtwoord, code: nieuw.code.trim() })
  bezig.value = false
  if (res === 'ingelogd') router.push({ name: 'home' })
  else if (res === 'bevestig') {
    melding.value = nieuw.soort === 'am'
      ? '✓ Bijna klaar! Check je mailbox en klik op de bevestigingslink. Log daarna hier in — je wordt automatisch gekoppeld als accountmanager.'
      : '✓ Bijna klaar! Check je mailbox en klik op de bevestigingslink. Log daarna hier in — je winkel koppelt dan automatisch.'
    modus.value = 'in'; vorm.email = nieuw.email
  }
}

async function stuurReset() {
  if (bezig.value || !reset.email.trim()) return
  bezig.value = true
  await auth.wachtwoordVergeten(reset.email.trim())
  bezig.value = false
  melding.value = 'Als dit e-mailadres bekend is, is er een resetmail verstuurd. Check je inbox.'
  modus.value = 'in'; vorm.email = reset.email
}
</script>

<template>
  <div class="wrap">
    <!-- Inloggen (iedereen: kantoor, accountmanager én winkel — je account bepaalt wat je ziet) -->
    <form v-if="modus === 'in'" class="card" @submit.prevent="inloggen">
      <div class="brand">TAPPARFUM</div>
      <h1>Portaal</h1>
      <p class="uitleg">Eén login voor iedereen — kantoor, accountmanagers en winkels. Je account bepaalt automatisch wat je ziet.</p>
      <label>E-mail
        <input v-model="vorm.email" type="email" autocomplete="username" required placeholder="jij@voorbeeld.nl" />
      </label>
      <label>Wachtwoord
        <input v-model="vorm.wachtwoord" type="password" autocomplete="current-password" required placeholder="••••••••" />
      </label>
      <p v-if="melding" class="okmsg" role="status">{{ melding }}</p>
      <p v-if="auth.error" class="err" role="alert">{{ auth.error }}</p>
      <button class="btn" type="submit" :disabled="bezig">{{ bezig ? 'Bezig…' : 'Inloggen' }}</button>
      <div class="links">
        <a role="button" tabindex="0" data-test="naar-nieuw" @click="wissel('nieuw')" @keydown.enter="wissel('nieuw')">🏬 Eerste keer? Winkel-account aanmaken</a>
        <a role="button" tabindex="0" data-test="naar-reset" @click="wissel('reset')" @keydown.enter="wissel('reset')">Wachtwoord vergeten?</a>
      </div>
    </form>

    <!-- Eerste keer: winkel (snelstartcode) of uitgenodigde accountmanager -->
    <form v-else-if="modus === 'nieuw'" class="card" @submit.prevent="maakAccount">
      <div class="brand">TAPPARFUM</div>
      <h1>Account aanmaken</h1>
      <div class="soortkeuze">
        <label class="soort" :class="{ aan: nieuw.soort === 'winkel' }">
          <input v-model="nieuw.soort" type="radio" value="winkel" data-test="soort-winkel" />🏬 Ik ben een winkel
        </label>
        <label class="soort" :class="{ aan: nieuw.soort === 'am' }">
          <input v-model="nieuw.soort" type="radio" value="am" data-test="soort-am" />🚗 Ik ben accountmanager
        </label>
      </div>
      <p v-if="nieuw.soort === 'winkel'" class="uitleg">Vul de <b>snelstartcode</b> in die je van je accountmanager kreeg — je winkel koppelt automatisch aan je nieuwe account.</p>
      <p v-else class="uitleg">Gebruik het <b>e-mailadres waarop kantoor je heeft uitgenodigd</b> — je wordt dan automatisch gekoppeld.</p>
      <label v-if="nieuw.soort === 'winkel'">Snelstartcode
        <input v-model="nieuw.code" :required="nieuw.soort === 'winkel'" placeholder="bijv. kl-123" data-test="su-code" />
      </label>
      <label>E-mail
        <input v-model="nieuw.email" type="email" autocomplete="username" required placeholder="winkel@voorbeeld.nl" data-test="su-email" />
      </label>
      <label>Wachtwoord (min. 8 tekens)
        <input v-model="nieuw.wachtwoord" type="password" autocomplete="new-password" required data-test="su-pass" />
      </label>
      <label>Wachtwoord nogmaals
        <input v-model="nieuw.wachtwoord2" type="password" autocomplete="new-password" required data-test="su-pass2" />
      </label>
      <p v-if="auth.error" class="err" role="alert">{{ auth.error }}</p>
      <button class="btn" type="submit" :disabled="bezig" data-test="su-maak">{{ bezig ? 'Bezig…' : 'Account aanmaken →' }}</button>
      <div class="links"><a role="button" tabindex="0" @click="wissel('in')" @keydown.enter="wissel('in')">← Terug naar inloggen</a></div>
    </form>

    <!-- Wachtwoord vergeten -->
    <form v-else class="card" @submit.prevent="stuurReset">
      <div class="brand">TAPPARFUM</div>
      <h1>Wachtwoord vergeten</h1>
      <p class="uitleg">Vul je e-mailadres in; je krijgt een mail met een link om een nieuw wachtwoord in te stellen.</p>
      <label>E-mail
        <input v-model="reset.email" type="email" required placeholder="jij@voorbeeld.nl" data-test="reset-email" />
      </label>
      <button class="btn" type="submit" :disabled="bezig" data-test="reset-stuur">{{ bezig ? 'Bezig…' : 'Stuur resetmail →' }}</button>
      <div class="links"><a role="button" tabindex="0" @click="wissel('in')" @keydown.enter="wissel('in')">← Terug naar inloggen</a></div>
    </form>
  </div>
</template>

<style scoped>
.wrap{min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
.card{background:#fff;border:1px solid var(--line);border-radius:16px;padding:28px;width:100%;max-width:380px;box-shadow:0 8px 30px rgba(0,0,0,.06);display:flex;flex-direction:column;gap:12px}
.brand{font-weight:800;letter-spacing:.16em;color:var(--coral)}
h1{margin:0;font-size:22px}
.uitleg{margin:0;font-size:13px;color:var(--grey)}
label{display:flex;flex-direction:column;gap:5px;font-size:13px;font-weight:700;color:var(--grey)}
input{padding:10px 12px;border:1.5px solid var(--line);border-radius:10px;font-size:15px}
input:focus{outline:none;border-color:var(--coral)}
.err{color:#b3261e;font-size:13px;margin:0}
.okmsg{color:#2c5a12;font-size:13px;margin:0;background:#f4faf0;border-radius:8px;padding:8px 10px}
.btn{margin-top:6px;background:var(--coral);color:#fff;border:0;border-radius:10px;padding:11px;font-weight:800;font-size:15px;cursor:pointer}
.btn:disabled{opacity:.6;cursor:default}
.links{display:flex;flex-direction:column;gap:6px;margin-top:4px}
.links a{color:var(--coral);font-weight:700;font-size:13px;cursor:pointer}
.links a:hover{text-decoration:underline}
.soortkeuze{display:flex;gap:8px}
.soort{flex:1;flex-direction:row;align-items:center;gap:8px;border:1.5px solid var(--line);border-radius:10px;padding:10px;font-size:13px;cursor:pointer}
.soort.aan{border-color:var(--coral);background:#fdeee7;color:var(--ink)}
.soort input{width:16px;height:16px;accent-color:var(--coral)}
</style>
