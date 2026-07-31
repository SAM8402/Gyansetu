<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-xl font-semibold text-gray-900 dark:text-gray-100">Your Documents</h1>
      <router-link to="/upload" class="bg-blue-600 text-white text-sm font-medium rounded-lg px-4 py-2 hover:bg-blue-700 shadow-sm transition">Upload new</router-link>
    </div>

    <div v-if="loading" class="border border-gray-200 dark:border-gray-800 rounded-lg p-6 bg-white dark:bg-gray-900"><LoadingSkeleton height="160px" /></div>

    <div v-else-if="jobs.length === 0" class="border border-gray-200 dark:border-gray-800 rounded-lg p-12 text-center text-gray-400 dark:text-gray-500 bg-white dark:bg-gray-900">
      No documents yet. Upload one to get started.
    </div>

    <div v-else class="border border-gray-200 dark:border-gray-800 rounded-lg overflow-hidden bg-white dark:bg-gray-900 shadow-sm">
      <div v-for="job in jobs" :key="job.id" class="flex items-center justify-between px-5 py-3.5 border-b border-gray-100 dark:border-gray-800 last:border-b-0 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800/60 transition" @click="$router.push(`/results/${job.id}`)">
        <div class="flex flex-col gap-0.5">
          <span class="text-sm font-medium text-gray-900 dark:text-gray-100">{{ job.file_name }}</span>
          <span class="text-xs text-gray-400 dark:text-gray-500">Created {{ new Date(job.created_at).toLocaleDateString() }}</span>
        </div>
        <div class="flex items-center gap-3">
          <span :class="['text-xs font-medium uppercase px-3 py-1 rounded-full', statusClass(job.status)]">{{ job.status }}</span>
          <button
            @click.stop="handleDelete(job.id, job.file_name)"
            class="text-gray-400 hover:text-red-600 dark:hover:text-red-400 p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-950/40 transition"
            title="Delete Document"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useJobsStore } from '../stores/jobs'
import LoadingSkeleton from '../components/common/LoadingSkeleton.vue'

const jobsStore = useJobsStore()
const { jobs, loading } = storeToRefs(jobsStore)
const { fetchJobs, removeJob } = jobsStore

function statusClass(s) {
  return { completed: 'bg-green-100 text-green-700', processing: 'bg-blue-100 text-blue-700', pending: 'bg-yellow-100 text-yellow-700', failed: 'bg-red-100 text-red-700' }[s] || 'bg-gray-100 text-gray-500'
}

async function handleDelete(id, fileName) {
  if (confirm(`Are you sure you want to delete "${fileName}"?`)) {
    await removeJob(id)
  }
}

onMounted(fetchJobs)
</script>
