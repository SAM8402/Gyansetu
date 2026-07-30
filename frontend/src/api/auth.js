import api from './axios'

export const login = (email, password) => api.post('/auth/login', { email, password })
export const register = (name, email, password, role) => api.post('/auth/register', { name, email, password, role })
export const refreshToken = (refresh_token) => api.post('/auth/refresh', { refresh_token })
