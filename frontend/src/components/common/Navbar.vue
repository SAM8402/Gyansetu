<template>
  <nav class="fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-200">
    <div class="max-w-5xl mx-auto px-6 h-14 flex items-center justify-between">
      <router-link to="/dashboard" class="text-lg font-bold text-blue-600">Gyansetu</router-link>
      <div v-if="auth.isAuthenticated" class="flex items-center gap-4">
        <router-link to="/dashboard" class="text-sm text-gray-500 hover:text-blue-600">Dashboard</router-link>
        <router-link to="/upload" class="text-sm text-gray-500 hover:text-blue-600">Upload</router-link>
        <button class="text-sm px-4 py-1.5 rounded-lg border border-gray-200 text-gray-700 hover:bg-gray-50" @click="logout">Log out</button>
      </div>
    </div>
  </nav>
</template>
<script setup>
import { useAuthStore } from '../../stores/auth'
import { useRouter } from 'vue-router'
const auth = useAuthStore()
const router = useRouter()
function logout() { auth.logout(); router.push('/login') }
</script>
