<template>
  <div class="max-w-lg mx-auto">
    <h1 class="text-xl font-semibold mb-6 text-gray-900 dark:text-gray-100">Processing Document</h1>
    <div class="border border-gray-200 dark:border-gray-800 rounded-lg p-6 bg-white dark:bg-gray-900 shadow-sm">
      <div class="flex flex-col gap-1.5">
        <div 
          v-for="s in stages" 
          :key="s.num" 
          :class="['flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-300', rowClass(s.num)]"
        >
          <div :class="['w-4 h-4 rounded-full flex items-center justify-center transition-all duration-300 text-white', dotClass(s.num)]">
            <svg v-if="isCompleted(s.num)" class="w-2.5 h-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
              <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <span :class="['text-sm', textClass(s.num)]">{{ s.label }}</span>
        </div>
      </div>

      <div v-if="sseStatus" class="mt-6">
        <div class="flex justify-between items-center text-xs text-gray-500 dark:text-gray-400 mb-1.5">
          <span class="font-medium text-gray-600 dark:text-gray-300">{{ isDone ? 'Pipeline Complete!' : (sseStatus.message || 'Processing...') }}</span>
          <span class="font-semibold" :class="isDone ? 'text-green-600 dark:text-green-400' : 'text-blue-600 dark:text-blue-400'">{{ isDone ? '100%' : (sseStatus.progress || 0) + '%' }}</span>
        </div>
        <div class="h-2 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
          <div 
            :class="['h-full rounded-full transition-all duration-500', isDone ? 'bg-green-500' : 'bg-blue-600']" 
            :style="{ width: (isDone ? 100 : (sseStatus.progress || 0)) + '%' }"
          ></div>
        </div>
      </div>

      <div v-if="isDone || sseStatus?.error" class="mt-6">
        <router-link 
          v-if="isDone && sseStatus?.tkp_url" 
          :to="`/results/${$route.params.id}`" 
          class="w-full text-center bg-green-600 text-white text-sm font-semibold rounded-lg px-4 py-2.5 hover:bg-green-700 transition-colors inline-block shadow-sm"
        >
          View Results →
        </router-link>
        <p v-else-if="sseStatus?.error" class="text-sm text-red-500 font-medium text-center">
          {{ sseStatus.error || 'An error occurred during processing.' }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useJobsStore } from '../stores/jobs'

const route = useRoute()
const jobsStore = useJobsStore()
const { sseStatus } = storeToRefs(jobsStore)
const { connectSSE } = jobsStore
let es = null

const stages = [
  { num: 1, label: 'Document Intelligence' },
  { num: 2, label: 'Educational Classification' },
  { num: 3, label: 'Knowledge Extraction' },
  { num: 4, label: 'Teaching Planning' },
  { num: 5, label: 'Content Generation' },
  { num: 6, label: 'Activity Generation' },
  { num: 7, label: 'Assessment Generation' },
  { num: 8, label: 'Gap Analysis' },
  { num: 9, label: 'Validation' },
  { num: 10, label: 'Publishing' },
]

const isDone = computed(() => {
  return sseStatus.value?.done === true || (sseStatus.value?.stage_number >= 10 && !!sseStatus.value?.tkp_url)
})

function isCompleted(num) {
  if (isDone.value) return true
  if (!sseStatus.value) return false
  const cur = sseStatus.value.stage_number || 0
  return num < cur
}

function rowClass(num) {
  if (isDone.value) return 'bg-green-50/80 dark:bg-green-950/30'
  if (!sseStatus.value) return ''
  const cur = sseStatus.value.stage_number || 0
  if (num < cur) return 'bg-green-50/80 dark:bg-green-950/30'
  if (num === cur) return 'bg-blue-50 dark:bg-blue-950/40'
  return ''
}

function dotClass(num) {
  if (isDone.value) return 'bg-green-500 ring-2 ring-green-200 dark:ring-green-900'
  if (!sseStatus.value) return 'bg-gray-300 dark:bg-gray-700'
  const cur = sseStatus.value.stage_number || 0
  if (num < cur) return 'bg-green-500'
  if (num === cur) return 'bg-blue-600 ring-2 ring-blue-200 dark:ring-blue-900 animate-pulse'
  return 'bg-gray-300 dark:bg-gray-700'
}

function textClass(num) {
  if (isDone.value) return 'text-green-800 dark:text-green-300 font-medium'
  if (!sseStatus.value) return 'text-gray-500 dark:text-gray-400'
  const cur = sseStatus.value.stage_number || 0
  if (num < cur) return 'text-green-700 dark:text-green-400'
  if (num === cur) return 'text-blue-700 dark:text-blue-300 font-semibold'
  return 'text-gray-500 dark:text-gray-400'
}

onMounted(() => { es = connectSSE(route.params.id) })
onUnmounted(() => { if (es) es.close() })
</script>
