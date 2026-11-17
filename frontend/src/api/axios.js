import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5000/api'

export const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: false,
})

// Request interceptor: inject JWT token from localStorage
axiosInstance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('ruralb2b_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// Response interceptor: handle 401 globally (clear token & redirect to login)
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Jangan clear otomatis di sini agar halaman yang membutuhkan auth
      // dapat menanganinya sendiri. Tandai saja agar komponen tahu.
      window.dispatchEvent(new CustomEvent('auth:unauthorized'))
    }
    return Promise.reject(error)
  },
)

export default axiosInstance
