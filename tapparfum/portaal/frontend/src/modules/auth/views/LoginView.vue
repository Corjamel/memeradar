<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../../../stores/auth.js'

/* Eigen campagnebeeld (aangeleverd door kantoor): zet login-hero.jpg in
   public/assets/ en het paneel pakt hem automatisch als achtergrond. */
const hero = ref(false)
onMounted(() => {
  fetch('/assets/login-hero.jpg', { method: 'HEAD' })
    .then(r => { hero.value = r.ok })
    .catch(() => { hero.value = false })
})

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
  <div class="loginsplit">
   <div class="logincard">
    <!-- Visueel paneel (v71-split): rustig — signatuur-gradient, merk en belofte.
         Zodra kantoor hét campagnebeeld aanlevert, komt dat hier als achtergrond
         (login-hero.jpg in public/assets/ neerzetten is genoeg). -->
    <div class="ls-visual" :class="{ metfoto: hero }" aria-hidden="true">
      <div class="ls-veil"></div>
      <div class="ls-txt">
        <div class="ls-brand" translate="no">TAP<b>PARFUM</b></div>
        <div class="ls-concept">Ruiken met je neus,<br>niet je portemonnee.</div>
        <div class="ls-tag">Easy to build, easy to scale — hervulbaar parfum is het nieuwe normaal.</div>
      </div>
    </div>

    <!-- Formulierpaneel -->
    <div class="ls-form">
    <!-- Inloggen (iedereen: kantoor, accountmanager én winkel — je account bepaalt wat je ziet) -->
    <form v-if="modus === 'in'" class="fbox" @submit.prevent="inloggen">
      <div class="brand" translate="no">TAP<b>PARFUM</b></div>
      <h1>Inloggen</h1>
      <p class="uitleg">Eén login voor iedereen — kantoor, accountmanagers en winkels. Je account bepaalt automatisch wat je ziet.</p>
      <label>E-mail
        <input v-model="vorm.email" type="email" autocomplete="username" required placeholder="jij@voorbeeld.nl" />
      </label>
      <label>Wachtwoord
        <input v-model="vorm.wachtwoord" type="password" autocomplete="current-password" required placeholder="••••••••" />
      </label>
      <p v-if="melding" class="okmsg" role="status">{{ melding }}</p>
      <p v-if="auth.error" class="err" role="alert">{{ auth.error }}</p>
      <button class="btn" type="submit" :disabled="bezig">{{ bezig ? 'Bezig…' : 'Inloggen →' }}</button>
      <div class="links">
        <button type="button" data-test="naar-nieuw" @click="wissel('nieuw')">Eerste keer? Account aanmaken</button>
        <button type="button" data-test="naar-reset" @click="wissel('reset')">Wachtwoord vergeten?</button>
      </div>
    </form>

    <!-- Eerste keer: winkel (snelstartcode) of uitgenodigde accountmanager -->
    <form v-else-if="modus === 'nieuw'" class="fbox" @submit.prevent="maakAccount">
      <div class="brand" translate="no">TAP<b>PARFUM</b></div>
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
        <input v-model="nieuw.code" :required="nieuw.soort === 'winkel'" placeholder="bijv. kl-123" autocomplete="off" spellcheck="false" data-test="su-code" />
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
      <div class="links"><button type="button" @click="wissel('in')">← Terug naar inloggen</button></div>
    </form>

    <!-- Wachtwoord vergeten -->
    <form v-else class="fbox" @submit.prevent="stuurReset">
      <div class="brand" translate="no">TAP<b>PARFUM</b></div>
      <h1>Wachtwoord vergeten</h1>
      <p class="uitleg">Vul je e-mailadres in; je krijgt een mail met een link om een nieuw wachtwoord in te stellen.</p>
      <label>E-mail
        <input v-model="reset.email" type="email" required placeholder="jij@voorbeeld.nl" autocomplete="email" data-test="reset-email" />
      </label>
      <button class="btn" type="submit" :disabled="bezig" data-test="reset-stuur">{{ bezig ? 'Bezig…' : 'Stuur resetmail →' }}</button>
      <div class="links"><button type="button" @click="wissel('in')">← Terug naar inloggen</button></div>
    </form>
    </div>
   </div>
  </div>
</template>

<style scoped>
/* v71-inlogscherm: één gecentreerde, afgeronde kaart die op de crème-pagina
   zweeft — links het merkpaneel, rechts het formulier. */
.loginsplit{min-height:100vh;display:flex;align-items:center;justify-content:center;padding:28px;background:var(--pagebg)}
.logincard{display:grid;grid-template-columns:1.05fr 1fr;width:100%;max-width:920px;min-height:560px;
  background:#fff;border:1px solid var(--line);border-radius:22px;overflow:hidden;
  box-shadow:0 2px 6px rgba(42,33,28,.05),0 30px 60px -30px rgba(42,33,28,.35)}
/* Merkpaneel: signatuur-gradient; met kantoor-beeld (login-hero.jpg) als achtergrond. */
.ls-visual{position:relative;overflow:hidden;background:var(--sig)}
.ls-visual.metfoto{background-image:url('/assets/login-hero.jpg'),var(--sig);background-size:cover;background-position:center;background-repeat:no-repeat}
.ls-veil{position:absolute;inset:0;background:radial-gradient(120% 90% at 85% -10%, rgba(255,255,255,.28), transparent 55%),linear-gradient(160deg, rgba(217,84,60,.15), rgba(42,33,28,.35))}
.metfoto .ls-veil{background:linear-gradient(180deg, rgba(42,33,28,.05) 40%, rgba(42,33,28,.62))}
.ls-txt{position:absolute;left:0;bottom:0;right:0;padding:40px 36px;color:#fff}
.ls-brand{font-weight:800;letter-spacing:.18em;font-size:20px;text-shadow:0 2px 12px rgba(0,0,0,.25)}
.ls-brand b{font-weight:900}
.ls-concept{font-family:var(--font-display);font-weight:600;font-size:clamp(26px,2.6vw,34px);line-height:1.14;margin-top:12px;text-shadow:0 2px 14px rgba(0,0,0,.28);text-wrap:balance}
.ls-tag{margin-top:12px;font-size:14px;font-weight:600;max-width:340px;line-height:1.45;text-shadow:0 1px 8px rgba(0,0,0,.3);opacity:.95}
.ls-form{display:flex;flex-direction:column;justify-content:center;padding:44px 44px}
.fbox{display:flex;flex-direction:column;gap:12px;width:100%}
.brand{font-weight:800;letter-spacing:.16em;color:var(--coral-d);font-size:14px}
.brand b{font-weight:900}
h1{margin:0;font-size:26px;letter-spacing:-.3px;font-family:var(--font-display);font-weight:600}
.uitleg{margin:0;font-size:13.5px;color:var(--grey);line-height:1.55}
label{display:flex;flex-direction:column;gap:5px;font-size:12.5px;font-weight:700;color:var(--grey)}
input{padding:12px 14px;border:1.5px solid var(--line);border-radius:12px;font-size:15px;background:#fff;color:var(--ink)}
input:focus{outline:none;border-color:var(--coral);box-shadow:0 0 0 3px rgba(238,100,77,.15)}
.err{color:#b3261e;font-size:13px;margin:0}
.okmsg{color:#2c5a12;font-size:13px;margin:0;background:#f4faf0;padding:8px 10px;border-radius:10px}
.btn{margin-top:6px;background:var(--coral);color:#fff;border:0;border-radius:999px;padding:12px;font-weight:800;font-size:14.5px;cursor:pointer}
.btn:hover{background:var(--coral-d)}
.btn:disabled{opacity:.6;cursor:default}
.links{display:flex;flex-direction:column;gap:6px;margin-top:4px}
.links button{background:none;border:0;padding:0;text-align:left;color:var(--coral-d);font-weight:700;font-size:13px;cursor:pointer}
.links button:hover{text-decoration:underline}
.soortkeuze{display:flex;gap:8px}
.soort{flex:1;flex-direction:row;align-items:center;gap:8px;border:1.5px solid var(--line);border-radius:12px;padding:10px;font-size:13px;cursor:pointer}
.soort.aan{border-color:var(--coral);background:var(--soft);color:var(--ink)}
.soort input{width:16px;height:16px;accent-color:var(--coral)}
@media(max-width:760px){
  .loginsplit{padding:0}
  .logincard{grid-template-columns:1fr;max-width:520px;min-height:100vh;border-radius:0;border:0}
  .ls-visual{min-height:180px}
  .ls-txt{padding:24px 24px}
  .ls-form{padding:30px 26px}
}
</style>
