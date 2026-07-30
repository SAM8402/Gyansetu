<template>
  <div class="flex items-center justify-center min-h-[75vh]">
    <div class="w-full max-w-sm border border-gray-200 rounded-lg p-8">
      <h1 class="text-2xl font-bold text-center text-blue-600 mb-1">Gyansetu</h1>
      <p class="text-sm text-center text-gray-400 mb-6">Sign in to your account</p>
      <div class="mb-4">
        <label class="text-xs font-medium text-gray-400 mb-1 block">Email</label>
        <input v-model="email" type="email" placeholder="you@example.com" class="border border-gray-200 rounded-lg px-3 py-2 text-sm w-full outline-none focus:border-blue-500" />
      </div>
      <div class="mb-4">
        <label class="text-xs font-medium text-gray-400 mb-1 block">Password</label>
        <input v-model="password" type="password" placeholder="Enter password" @keyup.enter="handleLogin" class="border border-gray-200 rounded-lg px-3 py-2 text-sm w-full outline-none focus:border-blue-500" />
      </div>
      <p v-if="error" class="text-sm text-red-500 mb-3">{{ error }}</p>
      <button class="w-full bg-blue-600 text-white text-sm font-medium rounded-lg px-4 py-2 hover:bg-blue-700 disabled:bg-gray-200 disabled:text-gray-400" @click="handleLogin" :disabled="loading">
        {{ loading ? 'Signing in...' : 'Sign in' }}
      </button>
    </div>
  </div>
</template>
<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'
const auth = useAuthStore()
const router = useRouter()
const email = ref(''), password = ref(''), error = ref(''), loading = ref(false)
async function handleLogin() {
  error.value = ''; loading.value = true;
  try {
    await auth.login(email.value, password.value)
    router.push('/dashboard')
  } catch (e) { error.value = e.response?.data?.detail || 'Invalid credentials' }
  finally { loading.value = false }
}
</script>
