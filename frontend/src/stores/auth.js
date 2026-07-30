import { defineStore } from 'pinia'
import { login as apiLogin, register as apiRegister } from '../api/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('teacher_ai_token') || null,
    user: JSON.parse(localStorage.getItem('teacher_ai_user') || 'null'),
  }),
  getters: {
    isAuthenticated: (state) => !!state.token,
  },
  actions: {
    async login(email, password) {
      const { data } = await apiLogin(email, password)
      this.token = data.access_token
      localStorage.setItem('teacher_ai_token', data.access_token)
      localStorage.setItem('teacher_ai_refresh', data.refresh_token)
    },
    async register(name, email, password) {
      const { data } = await apiRegister(name, email, password)
      this.token = data.access_token
      localStorage.setItem('teacher_ai_token', data.access_token)
      localStorage.setItem('teacher_ai_refresh', data.refresh_token)
    },
    logout() {
      this.token = null
      this.user = null
      localStorage.removeItem('teacher_ai_token')
      localStorage.removeItem('teacher_ai_refresh')
      localStorage.removeItem('teacher_ai_user')
    },
  },
})
