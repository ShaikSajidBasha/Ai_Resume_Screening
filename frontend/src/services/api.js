import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export const authApi = {
  register: (payload) => api.post('/api/auth/register', payload),
  login: (payload) => api.post('/api/auth/login', payload),
}

export const resumeApi = {
  upload: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/api/resumes/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  list: () => api.get('/api/resumes'),
}

export const jobApi = {
  create: (payload) => api.post('/api/job-descriptions', payload),
  list: () => api.get('/api/job-descriptions'),
}

export const analysisApi = {
  analyze: (payload) => api.post('/api/analyses', payload),
  history: () => api.get('/api/analyses'),
  get: (id) => api.get(`/api/analyses/${id}`),
  remove: (id) => api.delete(`/api/analyses/${id}`),
  generateResume: (analysisId) => api.post(`/api/analyses/${analysisId}/generate-resume`),
}

export const generatedResumeApi = {
  get: (id) => api.get(`/api/generated-resumes/${id}`),
  preview: (id) => api.get(`/api/generated-resumes/${id}/preview`),
  selectTemplate: (id, templateName) => api.put(`/api/generated-resumes/${id}/template`, { template_name: templateName }),
  downloadPdf: (id) => api.get(`/api/generated-resumes/${id}/download/pdf`, { responseType: 'blob' }),
  downloadDocx: (id) => api.get(`/api/generated-resumes/${id}/download/docx`, { responseType: 'blob' }),
  reanalyze: (id) => api.post(`/api/generated-resumes/${id}/reanalyze`),
}

export const dashboardApi = {
  get: () => api.get('/api/dashboard'),
}

export function getApiErrorMessage(error, fallback = 'Something went wrong. Please try again.') {
  return error?.response?.data?.detail || fallback
}

export default api
