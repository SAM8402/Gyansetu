import { defineStore } from 'pinia'
import { listJobs, getJob, deleteJob } from '../api/jobs'

export const useJobsStore = defineStore('jobs', {
  state: () => ({
    jobs: [],
    currentJob: null,
    loading: false,
    sseStatus: null,
  }),
  actions: {
    async fetchJobs() {
      this.loading = true
      try {
        const { data } = await listJobs()
        this.jobs = data.jobs
      } finally {
        this.loading = false
      }
    },
    async fetchJob(id) {
      const { data } = await getJob(id)
      this.currentJob = data
      return data
    },
    async removeJob(id) {
      await deleteJob(id)
      this.jobs = this.jobs.filter(j => j.id !== id)
    },
    connectSSE(jobId) {
      const token = localStorage.getItem('teacher_ai_token')
      const es = new EventSource(`/api/stream/${jobId}?token=${token}`)
      es.addEventListener('progress', (e) => {
        this.sseStatus = JSON.parse(e.data)
      })
      es.addEventListener('complete', (e) => {
        this.sseStatus = JSON.parse(e.data)
        this.sseStatus.done = true
        es.close()
        this.fetchJobs()
      })
      es.addEventListener('error', (e) => {
        this.sseStatus = { error: 'Pipeline error', done: true }
        es.close()
      })
      return es
    },
  },
})
