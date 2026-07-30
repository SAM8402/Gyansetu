import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '../../stores/auth'

vi.mock('../../api/auth', () => ({
  login: vi.fn(),
  register: vi.fn(),
}))

import { login as apiLogin, register as apiRegister } from '../../api/auth'

beforeEach(() => {
  setActivePinia(createPinia())
  localStorage.clear()
  vi.clearAllMocks()
})

describe('auth store', () => {
  it('starts unauthenticated when no token in localStorage', () => {
    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(false)
    expect(store.token).toBeNull()
    expect(store.user).toBeNull()
  })

  it('restores token from localStorage', () => {
    localStorage.setItem('teacher_ai_token', 'test-token')
    localStorage.setItem('teacher_ai_user', JSON.stringify({ email: 'a@b.com' }))
    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(true)
    expect(store.token).toBe('test-token')
    expect(store.user.email).toBe('a@b.com')
  })

  it('login sets token and calls api', async () => {
    apiLogin.mockResolvedValue({ data: { access_token: 'abc', refresh_token: 'xyz' } })
    const store = useAuthStore()
    await store.login('a@b.com', 'pass')
    expect(apiLogin).toHaveBeenCalledWith('a@b.com', 'pass')
    expect(store.token).toBe('abc')
    expect(localStorage.getItem('teacher_ai_token')).toBe('abc')
  })

  it('register sets token and calls api', async () => {
    apiRegister.mockResolvedValue({ data: { access_token: 'def', refresh_token: 'uvw' } })
    const store = useAuthStore()
    await store.register('Alice', 'a@b.com', 'pass')
    expect(apiRegister).toHaveBeenCalledWith('Alice', 'a@b.com', 'pass')
    expect(store.token).toBe('def')
  })

  it('logout clears token and localStorage', () => {
    localStorage.setItem('teacher_ai_token', 'abc')
    localStorage.setItem('teacher_ai_refresh', 'xyz')
    const store = useAuthStore()
    store.token = 'abc'
    store.logout()
    expect(store.token).toBeNull()
    expect(store.user).toBeNull()
    expect(localStorage.getItem('teacher_ai_token')).toBeNull()
    expect(localStorage.getItem('teacher_ai_refresh')).toBeNull()
  })

  it('login with error rejects', async () => {
    apiLogin.mockRejectedValue(new Error('Invalid credentials'))
    const store = useAuthStore()
    await expect(store.login('a@b.com', 'wrong')).rejects.toThrow()
  })
})
