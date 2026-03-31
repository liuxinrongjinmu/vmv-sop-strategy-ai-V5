import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 180000
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export default api
