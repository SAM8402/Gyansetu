import api from './axios'

export const uploadDocument = (formData) => api.post('/upload', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
})
