import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/login', name: 'Login', component: () => import('../pages/LoginPage.vue'), meta: { guest: true } },
  { path: '/signup', name: 'Signup', component: () => import('../pages/SignupPage.vue'), meta: { guest: true } },
  { path: '/dashboard', name: 'Dashboard', component: () => import('../pages/DashboardPage.vue'), meta: { requiresAuth: true } },
  { path: '/upload', name: 'Upload', component: () => import('../pages/UploadPage.vue'), meta: { requiresAuth: true } },
  { path: '/processing/:id', name: 'Processing', component: () => import('../pages/ProcessingPage.vue'), meta: { requiresAuth: true } },
  { path: '/results/:id', name: 'Results', component: () => import('../pages/ResultsPage.vue'), meta: { requiresAuth: true } },
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('teacher_ai_token')
  if (!token && !to.meta.guest) {
    next('/login')
  } else if (token && to.meta.guest) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
