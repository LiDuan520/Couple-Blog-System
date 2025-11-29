import axios from 'axios'
import { getToken, removeToken } from '../utils/storage'
import { errorHandler } from '../utils/errorHandler'

// 创建 axios 实例
const apiClient = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器（统一错误处理）
apiClient.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    // 401 未授权，清除 token 并跳转登录
    if (error.response?.status === 401) {
      removeToken()
      window.location.href = '/login'
      return Promise.reject(new Error('未授权，请重新登录'))
    }
    
    // 统一错误处理
    const errorMessage = errorHandler(error)
    return Promise.reject(new Error(errorMessage))
  }
)

// 请求取消控制器（防止内存泄露）
const cancelTokenSources = new Map()

export const createCancelToken = (requestId) => {
  // 如果已存在，先取消之前的请求
  if (cancelTokenSources.has(requestId)) {
    cancelTokenSources.get(requestId).cancel('Request cancelled')
  }
  
  const source = axios.CancelToken.source()
  cancelTokenSources.set(requestId, source)
  return source.token
}

export const cancelRequest = (requestId) => {
  if (cancelTokenSources.has(requestId)) {
    cancelTokenSources.get(requestId).cancel('Request cancelled')
    cancelTokenSources.delete(requestId)
  }
}

export default apiClient

