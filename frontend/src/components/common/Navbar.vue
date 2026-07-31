<template>
  <nav class="fixed top-0 left-0 right-0 z-50 bg-white/90 dark:bg-gray-900/90 backdrop-blur-md border-b border-gray-200 dark:border-gray-800 transition-colors duration-200">
    <div class="max-w-5xl mx-auto px-6 h-14 flex items-center justify-between">
      <router-link to="/dashboard" class="text-lg font-bold text-blue-600 dark:text-blue-400 flex items-center gap-2">
        <svg class="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
        </svg>
        <span>Gyansetu</span>
      </router-link>

      <div class="flex items-center gap-3">
        <!-- Dark / Light Mode Toggle Button -->
        <button 
          @click="toggleTheme" 
          class="p-2 rounded-lg border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          :title="isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'"
        >
          <!-- Sun Icon for Dark Mode -->
          <svg v-if="isDark" class="w-4 h-4 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
          <!-- Moon Icon for Light Mode -->
          <svg v-else class="w-4 h-4 text-slate-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
          </svg>
        </button>

        <div v-if="auth.isAuthenticated" class="flex items-center gap-3">
          <router-link to="/dashboard" class="text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400">Dashboard</router-link>
          <router-link to="/upload" class="text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400">Upload</router-link>
          <button class="text-sm font-medium px-3.5 py-1.5 rounded-lg border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors" @click="logout">Log out</button>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { useAuthStore } from '../../stores/auth'
import { useRouter } from 'vue-router'
import { useTheme } from '../../composables/useTheme'

const auth = useAuthStore()
const router = useRouter()
const { isDark, toggleTheme } = useTheme()

function logout() { auth.logout(); router.push('/login') }
</script>
