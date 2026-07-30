<template>
  <div class="animate-pulse rounded-lg bg-gray-100" :style="{ width, height }"></div>
</template>
<script setup>
defineProps({ width: { type: String, default: '100%' }, height: { type: String, default: '20px' } })
</script>
