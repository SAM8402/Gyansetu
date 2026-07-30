<template>
  <div>
    <Navbar />
    <main class="pt-16 pb-10 px-6 max-w-5xl mx-auto">
      <router-view />
    </main>
  </div>
</template>
<script setup>
import Navbar from './components/common/Navbar.vue'
</script>
