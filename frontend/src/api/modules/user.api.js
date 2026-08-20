import apiClient from '../client'
import { createCancelToken } from '../client'
import { API_ENDPOINTS } from '../endpoints'

export const userAPI = {
  // 获取当前用户资料
  getProfile: async () => {
    return apiClient.get(API_ENDPOINTS.USER.PROFILE, {
      cancelToken: createCancelToken('user_profile'),
    })
  },

  // 更新用户信息（昵称/邮箱）
  updateProfile: async (data) => {
    return apiClient.put(API_ENDPOINTS.USER.UPDATE_PROFILE, data, {
      cancelToken: createCancelToken('user_update'),
    })
  },

  // 上传头像（multipart/form-data）
  uploadAvatar: async (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return apiClient.post(API_ENDPOINTS.USER.UPLOAD_AVATAR, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      cancelToken: createCancelToken('user_avatar'),
    })
  },

  // 头像 URL 拼接辅助（静态资源由后端 /static 暴露，dev 由 vite 代理）
  avatarSrc: (path) => (path ? path : null),
}
