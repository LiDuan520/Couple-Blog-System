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
    UPDATE_PASSWORD: '/users/me/password',
    UPLOAD_AVATAR: '/users/me/avatar',
  },
  // Couple
  COUPLE: {
    ME: '/couples/me',
    DELETE: '/couples/me',
    INVITES: '/couples/invites',
    MY_INVITE: '/couples/invites/me',
    REVOKE_INVITE: '/couples/invites/me',
    ACCEPT: '/couples/accept',
  },
  // Anniversary
  ANNIVERSARY: {
    LIST: '/anniversaries',
    CREATE: '/anniversaries',
    DETAIL: (id) => `/anniversaries/${id}`,
    UPDATE: (id) => `/anniversaries/${id}`,
    DELETE: (id) => `/anniversaries/${id}`,
  },
  // Album
  ALBUM: {
    LIST: '/albums',
    CREATE: '/albums',
    DETAIL: (id) => `/albums/${id}`,
    UPDATE: (id) => `/albums/${id}`,
    DELETE: (id) => `/albums/${id}`,
    UPLOAD_PHOTO: (albumId) => `/albums/${albumId}/photos`,
    LIST_PHOTOS: (albumId) => `/albums/${albumId}/photos`,
    DELETE_PHOTO: (photoId) => `/albums/photos/${photoId}`,
    UPDATE_PHOTO: (photoId) => `/albums/photos/${photoId}`,
  },
  // Timeline
  TIMELINE: {
    LIST: '/timeline',
  },
  // Dashboard
  DASHBOARD: {
    GET: '/dashboard',
  },
}
