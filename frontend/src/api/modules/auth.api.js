import apiClient from '../client'
import { createCancelToken } from '../client'
import { API_ENDPOINTS } from '../endpoints'

const AUTH_REQUEST_ID = 'auth_request'

export const authAPI = {
  // 注册
  register: async (data) => {
    return apiClient.post(API_ENDPOINTS.AUTH.REGISTER, data, {
      cancelToken: createCancelToken(AUTH_REQUEST_ID),
    })
  },
  
  // 登录
  login: async (data) => {
    return apiClient.post(API_ENDPOINTS.AUTH.LOGIN, data, {
      cancelToken: createCancelToken(AUTH_REQUEST_ID),
    })
  },
  
  // 登出
  logout: async () => {
    return apiClient.post(API_ENDPOINTS.AUTH.LOGOUT, {}, {
      cancelToken: createCancelToken(AUTH_REQUEST_ID),
    })
  },
  
  // 获取当前用户
  getCurrentUser: async () => {
    return apiClient.get(API_ENDPOINTS.AUTH.ME, {
      cancelToken: createCancelToken(AUTH_REQUEST_ID),
    })
  },
}

