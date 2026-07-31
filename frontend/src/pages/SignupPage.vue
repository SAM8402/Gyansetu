<template>
  <div class="flex items-center justify-center min-h-[75vh]">
    <div class="w-full max-w-md border border-gray-200 dark:border-gray-800 rounded-lg p-8 bg-white dark:bg-gray-900 shadow-sm">
      <h1 class="text-2xl font-bold text-center text-blue-600 dark:text-blue-400 mb-1">Gyansetu</h1>
      <p class="text-sm text-center text-gray-500 dark:text-gray-400 mb-6">Create a new teacher account</p>

      <div class="mb-4">
        <label class="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1.5 block">Full Name</label>
        <input 
          v-model="name" 
          type="text" 
          placeholder="John Doe" 
          class="border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg px-3 py-2 text-sm w-full outline-none focus:border-blue-500 dark:focus:border-blue-400 transition" 
        />
      </div>

      <div class="mb-4">
        <label class="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1.5 block">Email Address</label>
        <input 
          v-model="email" 
          type="email" 
          placeholder="teacher@school.edu" 
          class="border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg px-3 py-2 text-sm w-full outline-none focus:border-blue-500 dark:focus:border-blue-400 transition" 
        />
      </div>

      <div class="mb-4">
        <label class="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1.5 block">Password</label>
        <input 
          v-model="password" 
          type="password" 
          placeholder="At least 6 characters" 
          class="border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg px-3 py-2 text-sm w-full outline-none focus:border-blue-500 dark:focus:border-blue-400 transition" 
        />
      </div>

      <div class="mb-5">
        <label class="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1.5 block">Confirm Password</label>
        <input 
          v-model="confirmPassword" 
          type="password" 
          placeholder="Re-enter password" 
          @keyup.enter="handleSignup"
          class="border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg px-3 py-2 text-sm w-full outline-none focus:border-blue-500 dark:focus:border-blue-400 transition" 
        />
      </div>

      <p v-if="error" class="text-sm text-red-500 mb-4 text-center font-medium">{{ error }}</p>

      <button 
        class="w-full bg-blue-600 text-white text-sm font-semibold rounded-lg px-4 py-2.5 hover:bg-blue-700 disabled:bg-gray-200 dark:disabled:bg-gray-800 disabled:text-gray-400 dark:disabled:text-gray-600 transition shadow-sm" 
        @click="handleSignup" 
        :disabled="loading"
      >
        {{ loading ? 'Creating account...' : 'Create Account' }}
      </button>

      <div class="mt-6 text-center text-xs text-gray-500 dark:text-gray-400">
        Already have an account? 
        <router-link to="/login" class="text-blue-600 dark:text-blue-400 font-semibold hover:underline">Sign in</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()

const name = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const error = ref('')
const loading = ref(false)

async function handleSignup() {
  error.value = ''
  if (!name.value.trim()) {
    error.value = 'Please enter your name'
    return
  }
  if (!email.value.trim()) {
    error.value = 'Please enter your email address'
    return
  }
  if (!password.value || password.value.length < 6) {
    error.value = 'Password must be at least 6 characters'
    return
  }
  if (password.value !== confirmPassword.value) {
    error.value = 'Passwords do not match'
    return
  }

  loading.value = true
  try {
    await auth.register(name.value.trim(), email.value.trim(), password.value)
    router.push('/dashboard')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to create account. Email may already be registered.'
  } finally {
    loading.value = false
  }
}
</script>
