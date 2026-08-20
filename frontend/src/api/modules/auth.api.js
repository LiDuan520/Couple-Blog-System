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

  // 登录（JSON 走 /login-json，前端用）
  login: async (data) => {
    return apiClient.post(API_ENDPOINTS.AUTH.LOGIN_JSON, data, {
      cancelToken: createCancelToken(AUTH_REQUEST_ID),
    })
  },

  // 登出
  logout: async () => {
    return apiClient.post(API_ENDPOINTS.AUTH.LOGOUT, {}, {
      cancelToken: createCancelToken(AUTH_REQUEST_ID),
    })
  },

  // 刷新 token
  refresh: async () => {
    return apiClient.post(API_ENDPOINTS.AUTH.REFRESH, {}, {
      cancelToken: createCancelToken(AUTH_REQUEST_ID),
    })
  },

  // 修改密码
  changePassword: async (data) => {
    return apiClient.post(API_ENDPOINTS.AUTH.CHANGE_PASSWORD, data, {
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
