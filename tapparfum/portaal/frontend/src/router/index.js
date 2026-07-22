// Routes + guards. De guard is UX (waar stuur ik je heen), NIET de beveiliging —
// die zit in RLS. meta.roles bepaalt welke rol een route in de UI mag openen.
import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '../stores/auth.js'

import LoginView from '../modules/auth/views/LoginView.vue'
import DashboardView from '../modules/dashboard/views/DashboardView.vue'
import TappuntenListView from '../modules/tappunten/views/TappuntenListView.vue'
import TappuntDetailView from '../modules/tappunten/views/TappuntDetailView.vue'
import BerichtenView from '../modules/berichten/views/BerichtenView.vue'
import AgendaView from '../modules/agenda/views/AgendaView.vue'
import ActiesView from '../modules/acties/views/ActiesView.vue'
import BeloningenView from '../modules/beloningen/views/BeloningenView.vue'

const ALLE_ROLLEN = ['kantoor', 'am', 'partner']

const routes = [
  { path: '/login', name: 'login', component: LoginView, meta: { publiek: true } },
  { path: '/', name: 'home', component: DashboardView, meta: { roles: ALLE_ROLLEN } },
  { path: '/winkels', name: 'winkels', component: TappuntenListView, meta: { roles: ALLE_ROLLEN } },
  { path: '/winkels/:code', name: 'winkel', component: TappuntDetailView, props: true, meta: { roles: ALLE_ROLLEN } },
  { path: '/berichten', name: 'berichten', component: BerichtenView, meta: { roles: ALLE_ROLLEN } },
  { path: '/agenda', name: 'agenda', component: AgendaView, meta: { roles: ALLE_ROLLEN } },
  { path: '/acties', name: 'acties', component: ActiesView, meta: { roles: ALLE_ROLLEN } },
  { path: '/beloningen', name: 'beloningen', component: BeloningenView, meta: { roles: ALLE_ROLLEN } },
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
