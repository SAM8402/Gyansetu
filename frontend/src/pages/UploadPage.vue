<template>
  <div class="max-w-lg mx-auto">
    <h1 class="text-xl font-semibold mb-6 text-gray-900 dark:text-gray-100">Upload Document</h1>
    <div class="border border-gray-200 dark:border-gray-800 rounded-lg p-6 bg-white dark:bg-gray-900 shadow-sm">
      <div class="mb-4">
        <label class="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1.5 block">File (PDF, DOCX, PPT, TXT)</label>
        <input type="file" @change="onFileChange" accept=".pdf,.docx,.pptx,.txt" class="text-sm text-gray-700 dark:text-gray-300 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-blue-50 file:text-blue-700 dark:file:bg-blue-950/60 dark:file:text-blue-300 hover:file:bg-blue-100 dark:hover:file:bg-blue-900/60 cursor-pointer" />
      </div>
      <div class="mb-4">
        <label class="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1.5 block">Period duration (minutes)</label>
        <input v-model.number="periodDuration" type="number" min="20" max="120" class="border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg px-3 py-2 text-sm w-full outline-none focus:border-blue-500 dark:focus:border-blue-400 transition" />
      </div>
      <div class="mb-4">
        <label class="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1.5 block">Number of periods (0 = auto)</label>
        <input v-model.number="numPeriods" type="number" min="0" max="20" class="border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg px-3 py-2 text-sm w-full outline-none focus:border-blue-500 dark:focus:border-blue-400 transition" />
      </div>
      <div class="mb-4">
        <label class="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1.5 block">Language</label>
        <select v-model="targetLanguage" class="border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg px-3 py-2 text-sm w-full outline-none focus:border-blue-500 dark:focus:border-blue-400 transition">
          <option>English</option><option>Hindi</option><option>Spanish</option><option>French</option><option>German</option>
        </select>
      </div>
      <div class="mb-5">
        <label class="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1.5 block">Board</label>
        <select v-model="boardAlignment" class="border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg px-3 py-2 text-sm w-full outline-none focus:border-blue-500 dark:focus:border-blue-400 transition">
          <option>General</option><option>CBSE</option><option>ICSE</option><option>Common Core</option>
        </select>
      </div>
      <p v-if="error" class="text-sm text-red-500 mb-3">{{ error }}</p>
      <button class="w-full bg-blue-600 text-white text-sm font-semibold rounded-lg px-4 py-2.5 hover:bg-blue-700 disabled:bg-gray-200 dark:disabled:bg-gray-800 disabled:text-gray-400 dark:disabled:text-gray-600 transition" @click="handleUpload" :disabled="uploading || !file">
        {{ uploading ? 'Uploading...' : 'Upload & process' }}
      </button>
    </div>
  </div>
</template>
<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { uploadDocument } from '../api/upload'
const router = useRouter()
const file = ref(null), periodDuration = ref(40), numPeriods = ref(0), targetLanguage = ref('English'), boardAlignment = ref('General'), uploading = ref(false), error = ref('')
function onFileChange(e) { file.value = e.target.files[0] }
async function handleUpload() {
  if (!file.value) return; uploading.value = true; error.value = ''
  const fd = new FormData()
  fd.append('file', file.value)
  fd.append('period_duration', periodDuration.value)
  fd.append('num_periods', numPeriods.value)
  fd.append('target_language', targetLanguage.value)
  fd.append('board_alignment', boardAlignment.value)
  try {
    const { data } = await uploadDocument(fd)
    router.push(`/processing/${data.job_id}`)
  } catch (e) { error.value = e.response?.data?.detail || 'Upload failed' }
  finally { uploading.value = false }
}
</script>
