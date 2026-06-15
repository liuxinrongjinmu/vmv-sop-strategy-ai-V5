import axios from 'axios'

const API_KEY_STORAGE = 'vmv-sop-api-key'

/**
 * 从 localStorage 获取 API Key，回退到环境变量
 */
const getApiKey = (): string => {
  return localStorage.getItem(API_KEY_STORAGE) || import.meta.env.VITE_API_KEY || ''
}

const baseURL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api`
  : '/api'

const api = axios.create({
  baseURL,
  timeout: 300000
})

/**
 * 请求拦截器：从 localStorage 读取 API Key 并附加到请求头
 */
api.interceptors.request.use(
  (config) => {
    const apiKey = getApiKey()
    if (apiKey) {
      config.headers['X-API-Key'] = apiKey
    }
    return config
  },
  (error) => Promise.reject(error)
)

/**
 * 响应拦截器：401 时清除本地存储的 API Key
 */
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem(API_KEY_STORAGE)
      // 触发全局事件通知App组件
      window.dispatchEvent(new CustomEvent('api-key-invalid'))
    }
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

/**
 * 设置 API Key 到 localStorage
 */
export const setApiKey = (key: string) => {
  localStorage.setItem(API_KEY_STORAGE, key)
}

/**
 * 检查是否已配置 API Key（localStorage 或环境变量）
 */
export const hasApiKey = (): boolean => {
  return !!localStorage.getItem(API_KEY_STORAGE) || !!import.meta.env.VITE_API_KEY
}

export { API_KEY_STORAGE }
export default api
