<template>
  <div class="max-w-lg mx-auto">
    <h1 class="text-xl font-semibold mb-6">Upload Document</h1>
    <div class="border border-gray-200 rounded-lg p-6">
      <div class="mb-4">
        <label class="text-xs font-medium text-gray-400 mb-1 block">File (PDF, DOCX, PPT, TXT)</label>
        <input type="file" @change="onFileChange" accept=".pdf,.docx,.pptx,.txt" class="text-sm" />
      </div>
      <div class="mb-4">
        <label class="text-xs font-medium text-gray-400 mb-1 block">Period duration (minutes)</label>
        <input v-model.number="periodDuration" type="number" min="20" max="120" class="border border-gray-200 rounded-lg px-3 py-2 text-sm w-full outline-none focus:border-blue-500" />
      </div>
      <div class="mb-4">
        <label class="text-xs font-medium text-gray-400 mb-1 block">Number of periods (0 = auto)</label>
        <input v-model.number="numPeriods" type="number" min="0" max="20" class="border border-gray-200 rounded-lg px-3 py-2 text-sm w-full outline-none focus:border-blue-500" />
      </div>
      <div class="mb-4">
        <label class="text-xs font-medium text-gray-400 mb-1 block">Language</label>
        <select v-model="targetLanguage" class="border border-gray-200 rounded-lg px-3 py-2 text-sm w-full outline-none focus:border-blue-500">
          <option>English</option><option>Hindi</option><option>Spanish</option><option>French</option><option>German</option>
        </select>
      </div>
      <div class="mb-4">
        <label class="text-xs font-medium text-gray-400 mb-1 block">Board</label>
        <select v-model="boardAlignment" class="border border-gray-200 rounded-lg px-3 py-2 text-sm w-full outline-none focus:border-blue-500">
          <option>General</option><option>CBSE</option><option>ICSE</option><option>Common Core</option>
        </select>
      </div>
      <p v-if="error" class="text-sm text-red-500 mb-3">{{ error }}</p>
      <button class="w-full bg-blue-600 text-white text-sm font-medium rounded-lg px-4 py-2 hover:bg-blue-700 disabled:bg-gray-200 disabled:text-gray-400" @click="handleUpload" :disabled="uploading || !file">
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
