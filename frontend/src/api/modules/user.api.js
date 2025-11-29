import apiClient from '../client'
import { createCancelToken } from '../client'
import { API_ENDPOINTS } from '../endpoints'

export const userAPI = {
  // 更新用户信息
  updateProfile: async (data) => {
    return apiClient.put(API_ENDPOINTS.USER.PROFILE, data, {
      cancelToken: createCancelToken('user_update'),
    })
  },
  
  // 修改密码
  updatePassword: async (data) => {
    return apiClient.put(API_ENDPOINTS.USER.UPDATE_PASSWORD, data, {
      cancelToken: createCancelToken('user_password'),
    })
  },
}

