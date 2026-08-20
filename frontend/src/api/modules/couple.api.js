/**
 * Couple API
 */
import apiClient from '../client'
import { API_ENDPOINTS } from '../endpoints'

export const coupleApi = {
  getMe: () => apiClient.get(API_ENDPOINTS.COUPLE.ME),
  delete: () => apiClient.delete(API_ENDPOINTS.COUPLE.DELETE),

  createInvite: () => apiClient.post(API_ENDPOINTS.COUPLE.INVITES),
  getMyInvite: () => apiClient.get(API_ENDPOINTS.COUPLE.MY_INVITE),
  revokeInvite: () => apiClient.delete(API_ENDPOINTS.COUPLE.REVOKE_INVITE),
  acceptInvite: (code, anniversaryDate) =>
    apiClient.post(API_ENDPOINTS.COUPLE.ACCEPT, {
      code,
      anniversary_date: anniversaryDate,
    }),
}
