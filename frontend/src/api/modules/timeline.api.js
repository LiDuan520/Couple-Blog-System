/**
 * Timeline + Dashboard API
 */
import apiClient from '../client'
import { API_ENDPOINTS } from '../endpoints'

export const timelineApi = {
  list: (params = {}) =>
    apiClient.get(API_ENDPOINTS.TIMELINE.LIST, { params }),
}

export const dashboardApi = {
  get: () => apiClient.get(API_ENDPOINTS.DASHBOARD.GET),
}
