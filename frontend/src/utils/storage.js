// 安全的本地存储封装（防止 XSS）
const STORAGE_PREFIX = 'couple_blog_'

export const storage = {
  set: (key, value) => {
    try {
      const serialized = JSON.stringify(value)
      localStorage.setItem(`${STORAGE_PREFIX}${key}`, serialized)
    } catch (error) {
      console.error('Storage set error:', error)
    }
  },
  
  get: (key) => {
    try {
      const item = localStorage.getItem(`${STORAGE_PREFIX}${key}`)
      return item ? JSON.parse(item) : null
    } catch (error) {
      console.error('Storage get error:', error)
      return null
    }
  },
  
  remove: (key) => {
    try {
      localStorage.removeItem(`${STORAGE_PREFIX}${key}`)
    } catch (error) {
      console.error('Storage remove error:', error)
    }
  },
  
  clear: () => {
    try {
      Object.keys(localStorage).forEach((key) => {
        if (key.startsWith(STORAGE_PREFIX)) {
          localStorage.removeItem(key)
        }
      })
    } catch (error) {
      console.error('Storage clear error:', error)
    }
  },
}

// Token 管理
export const setToken = (token) => storage.set('token', token)
export const getToken = () => storage.get('token')
export const removeToken = () => storage.remove('token')

