<template>
  <div class="max-w-lg mx-auto">
    <h1 class="text-xl font-semibold mb-6">Processing</h1>
    <div class="border border-gray-200 rounded-lg p-6">
      <div class="flex flex-col gap-1">
        <div v-for="s in stages" :key="s.num" :class="['flex items-center gap-3 px-3 py-2 rounded-lg', rowClass(s.num)]">
          <div :class="['w-2 h-2 rounded-full', dotClass(s.num)]"></div>
          <span class="text-sm">{{ s.label }}</span>
        </div>
      </div>
      <div v-if="sseStatus" class="mt-5">
        <p class="text-sm text-gray-400">{{ sseStatus.message }}</p>
        <div class="mt-2 h-1 bg-gray-100 rounded-full overflow-hidden">
          <div class="h-full bg-blue-600 rounded-full transition-all duration-300" :style="{ width: sseStatus.progress + '%' }"></div>
        </div>
      </div>
      <div v-if="sseStatus?.done" class="mt-5">
        <router-link v-if="sseStatus.tkp_url" :to="`/results/${$route.params.id}`" class="bg-blue-600 text-white text-sm font-medium rounded-lg px-4 py-2 hover:bg-blue-700 inline-block">View results</router-link>
        <p v-else class="text-sm text-gray-400">An error occurred.</p>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useJobsStore } from '../stores/jobs'
const route = useRoute()
const { sseStatus, connectSSE } = useJobsStore()
let es = null
const stages = [
  { num: 1, label: 'Document Intel' }, { num: 2, label: 'Classification' }, { num: 3, label: 'Knowledge Extraction' },
  { num: 4, label: 'Teaching Plan' }, { num: 5, label: 'Content Gen' }, { num: 6, label: 'Activities' },
  { num: 7, label: 'Assessments' }, { num: 8, label: 'Gap Analysis' }, { num: 9, label: 'Validation' }, { num: 10, label: 'Publishing' },
]
function rowClass(num) {
  if (!sseStatus) return ''
  const cur = sseStatus.stage_number || 0
  if (num < cur) return 'bg-green-50'
  if (num === cur) return 'bg-blue-50'
  return ''
}
function dotClass(num) {
  if (!sseStatus) return 'bg-gray-300'
  const cur = sseStatus.stage_number || 0
  if (num < cur) return 'bg-green-500'
  if (num === cur) return 'bg-blue-500'
  return 'bg-gray-300'
}
onMounted(() => { es = connectSSE(route.params.id) })
onUnmounted(() => { if (es) es.close() })
</script>
