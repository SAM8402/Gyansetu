<template>
  <div class="min-h-screen bg-gray-50 text-gray-900 dark:bg-gray-950 dark:text-gray-100 transition-colors duration-200">
    <Navbar />
    <main class="pt-20 pb-12 px-6 max-w-5xl mx-auto">
      <router-view />
    </main>
  </div>
</template>
<script setup>
import { onMounted } from 'vue'
import Navbar from './components/common/Navbar.vue'
import { useTheme } from './composables/useTheme'

const { initTheme } = useTheme()
onMounted(initTheme)
</script>
