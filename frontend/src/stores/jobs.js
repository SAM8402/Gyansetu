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
      this.sseStatus = { stage_number: 1, progress: 10, message: 'Processing started...', done: false }
      const token = localStorage.getItem('teacher_ai_token')
      const es = new EventSource(`/api/stream/${jobId}?token=${token}`)
      
      es.addEventListener('progress', (e) => {
        try {
          const data = JSON.parse(e.data)
          this.sseStatus = { ...data, done: false }
        } catch (err) {}
      })
      
      es.addEventListener('complete', (e) => {
        try {
          const data = JSON.parse(e.data)
          this.sseStatus = { ...data, done: true, tkp_url: data.tkp_url || `/api/jobs/${jobId}/tkp` }
        } catch (err) {
          this.sseStatus = { done: true, tkp_url: `/api/jobs/${jobId}/tkp` }
        }
        es.close()
        this.fetchJobs()
      })
      
      es.addEventListener('error', async (e) => {
        if (this.sseStatus?.done) {
          es.close()
          return
        }
        try {
          const job = await this.fetchJob(jobId)
          if (job.status === 'completed') {
            this.sseStatus = { done: true, tkp_url: `/api/jobs/${jobId}/tkp` }
            es.close()
            return
          } else if (job.status === 'failed') {
            this.sseStatus = { error: job.error_message || 'Pipeline failed', done: true }
            es.close()
            return
          }
        } catch (err) {}
      })
      return es
    },
  },
})
