import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { authAPI } from '../api/modules/auth.api'
import { setToken, removeToken, getToken } from '../utils/storage'

export const useAuthStore = create(
  persist(
    (set, get) => ({
      // 状态
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      
      // 登录
      login: async (credentials) => {
        set({ isLoading: true, error: null })
        try {
          const response = await authAPI.login(credentials)
          const { access_token, user } = response.data || response
          
          setToken(access_token)
          set({
            user,
            token: access_token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          })
          
          return { success: true }
        } catch (error) {
          set({
            error: error.message,
            isLoading: false,
            isAuthenticated: false,
          })
          return { success: false, error: error.message }
        }
      },
      
      // 注册
      register: async (userData) => {
        set({ isLoading: true, error: null })
        try {
          const response = await authAPI.register(userData)
          set({ isLoading: false })
          return { success: true, data: response.data || response }
        } catch (error) {
          set({
            error: error.message,
            isLoading: false,
          })
          return { success: false, error: error.message }
        }
      },
      
      // 登出
      logout: async () => {
        try {
          await authAPI.logout()
        } catch (error) {
          console.error('Logout error:', error)
        } finally {
          removeToken()
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            error: null,
          })
        }
      },
      
      // 初始化（从本地存储恢复）
      init: async () => {
        const token = getToken()
        if (token) {
          set({ token, isAuthenticated: true })
          try {
            const user = await authAPI.getCurrentUser()
            set({ user: user.data || user, isAuthenticated: true })
          } catch (error) {
            // Token 无效，清除
            removeToken()
            set({ token: null, isAuthenticated: false })
          }
        }
      },
      
      // 清除错误
      clearError: () => set({ error: null }),
    }),
    {
      name: 'auth-storage', // 本地存储 key
      partialize: (state) => ({
        token: state.token,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)

