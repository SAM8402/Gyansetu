<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-xl font-semibold">Your Documents</h1>
      <router-link to="/upload" class="bg-blue-600 text-white text-sm font-medium rounded-lg px-4 py-2 hover:bg-blue-700">Upload new</router-link>
    </div>

    <div v-if="loading" class="border border-gray-200 rounded-lg p-6"><LoadingSkeleton height="160px" /></div>

    <div v-else-if="jobs.length === 0" class="border border-gray-200 rounded-lg p-12 text-center text-gray-400">
      No documents yet. Upload one to get started.
    </div>

    <div v-else class="border border-gray-200 rounded-lg overflow-hidden">
      <div v-for="job in jobs" :key="job.id" class="flex items-center justify-between px-5 py-3.5 border-b border-gray-100 last:border-b-0 cursor-pointer hover:bg-gray-50" @click="$router.push(`/results/${job.id}`)">
        <div class="flex flex-col gap-0.5">
          <span class="text-sm font-medium">{{ job.file_name }}</span>
          <span class="text-xs text-gray-400">Created {{ new Date(job.created_at).toLocaleDateString() }}</span>
        </div>
        <span :class="['text-xs font-medium uppercase px-3 py-1 rounded-full', statusClass(job.status)]">{{ job.status }}</span>
      </div>
    </div>
  </div>
</template>
<script setup>
import { onMounted } from 'vue'
import { useJobsStore } from '../stores/jobs'
import LoadingSkeleton from '../components/common/LoadingSkeleton.vue'
const { jobs, loading, fetchJobs } = useJobsStore()
function statusClass(s) {
  return { completed: 'bg-green-100 text-green-700', processing: 'bg-blue-100 text-blue-700', pending: 'bg-yellow-100 text-yellow-700', failed: 'bg-red-100 text-red-700' }[s] || 'bg-gray-100 text-gray-500'
}
onMounted(fetchJobs)
</script>
