// Routes + guards. De guard is UX (waar stuur ik je heen), NIET de beveiliging —
// die zit in RLS. meta.roles bepaalt welke rol een route in de UI mag openen.
import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '../stores/auth.js'

import LoginView from '../modules/auth/views/LoginView.vue'
import HomeView from '../modules/tappunten/views/HomeView.vue'

const routes = [
  { path: '/login', name: 'login', component: LoginView, meta: { publiek: true } },
  { path: '/', name: 'home', component: HomeView, meta: { roles: ['kantoor', 'am', 'partner'] } },
  { path: '/:pathMatch(.*)*', redirect: '/' }
]

export const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to) => {
  const auth = useAuth()
  if (!auth.ready) { await auth.init() }        // eerste keer: sessie ophalen

  if (to.meta.publiek) {
    // al ingelogd? login-scherm overslaan
    if (to.name === 'login' && auth.ingelogd) return { name: 'home' }
    return true
  }
  if (!auth.ingelogd) return { name: 'login' }  // niet ingelogd -> naar login
  if (to.meta.roles && !to.meta.roles.includes(auth.role)) return { name: 'home' }
  return true
})
