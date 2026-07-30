import api from './axios'

export const listJobs = () => api.get('/jobs')
export const getJob = (id) => api.get(`/jobs/${id}`)
export const downloadTkp = (id) => api.get(`/jobs/${id}/tkp`)
export const deleteJob = (id) => api.delete(`/jobs/${id}`)
