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
      couple: null,  // v2: 当前用户的 couple 简报（含 partner/anniversary_date/days_together）
      isAuthenticated: false,
      isLoading: false,
      error: null,

      // 登录
      login: async ({ username, password, remember_me = false }) => {
        set({ isLoading: true, error: null })
        try {
          const response = await authAPI.login({ username, password, remember_me })
          const data = response.data || response
          const { access_token, user } = data

          setToken(access_token)
          set({
            user,
            couple: user?.couple || null,
            token: access_token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          })
          return { success: true, data }
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
          await authAPI.register(userData)
          // FIX-F-01: 注册成功后自动登录
          const result = await get().login({
            username: userData.username,
            password: userData.password,
            remember_me: false,
          })
          return result
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
            couple: null,
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
            set({
              user: user.data || user,
              couple: (user.data || user)?.couple || null,
              isAuthenticated: true,
            })
          } catch (error) {
            // Token 无效，清除
            removeToken()
            set({ token: null, isAuthenticated: false })
          }
        }
      },

      // 刷新 couple 简报（被 Couple 页等调用）
      refreshCouple: () => {
        return authAPI.getCurrentUser().then((res) => {
          const u = res.data || res
          set({ user: u, couple: u?.couple || null })
        })
      },

      // 标记已绑定
      setCouple: (couple) => set({ couple }),

      // 修改密码
      changePassword: async ({ old_password, new_password }) => {
        set({ isLoading: true, error: null })
        try {
          await authAPI.changePassword({ old_password, new_password })
          set({ isLoading: false })
          return { success: true }
        } catch (error) {
          set({ error: error.message, isLoading: false })
          return { success: false, error: error.message }
        }
      },

      // 更新当前用户（被 profile 页等调用）
      updateUser: (userData) => set({ user: { ...(get().user || {}), ...userData } }),

      // 清除错误
      clearError: () => set({ error: null }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        token: state.token,
        user: state.user,
        couple: state.couple,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)
