import { ref, onUnmounted } from 'vue'

export function useSSE(jobId) {
  const progress = ref(null)
  const isComplete = ref(false)
  const error = ref(null)
  let es = null

  function connect() {
    const token = localStorage.getItem('teacher_ai_token')
    es = new EventSource(`/api/stream/${jobId}?token=${token}`)
    es.addEventListener('progress', (e) => { progress.value = JSON.parse(e.data) })
    es.addEventListener('complete', (e) => { isComplete.value = true; progress.value = JSON.parse(e.data); es.close() })
    es.addEventListener('error', () => { error.value = 'Connection lost'; es.close() })
  }

  onUnmounted(() => { if (es) es.close() })

  return { progress, isComplete, error, connect }
}
