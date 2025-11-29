/**
 * API 端点常量
 */
export const API_ENDPOINTS = {
  // 认证
  AUTH: {
    REGISTER: '/auth/register',
    LOGIN: '/auth/login',
    LOGOUT: '/auth/logout',
    ME: '/auth/me',
  },
  // 博客
  BLOG: {
    LIST: '/blogs',
    DETAIL: (id) => `/blogs/${id}`,
    CREATE: '/blogs',
    UPDATE: (id) => `/blogs/${id}`,
    DELETE: (id) => `/blogs/${id}`,
  },
  // 用户
  USER: {
    PROFILE: '/users/me',
    UPDATE_PASSWORD: '/users/me/password',
  },
}

