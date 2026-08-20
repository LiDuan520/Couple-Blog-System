/**
 * API 端点常量
 */
export const API_ENDPOINTS = {
  // 认证
  AUTH: {
    REGISTER: '/auth/register',
    LOGIN: '/auth/login',
    LOGIN_JSON: '/auth/login-json',
    LOGOUT: '/auth/logout',
    REFRESH: '/auth/refresh',
    CHANGE_PASSWORD: '/auth/change-password',
    ME: '/auth/me',
  },
  // 博客
  BLOG: {
    LIST: '/blogs',
    DETAIL: (id) => `/blogs/${id}`,
    CREATE: '/blogs',
    UPDATE: (id) => `/blogs/${id}`,
    DELETE: (id) => `/blogs/${id}`,
    PUBLIC: (authorId) => `/blogs/public/${authorId}`,
  },
  // 用户
  USER: {
    PROFILE: '/users/me',
    UPDATE_PROFILE: '/users/me',
    UPDATE_PASSWORD: '/users/me/password', // 复用 auth/change-password
    UPLOAD_AVATAR: '/users/me/avatar',
  },
}
