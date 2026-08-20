/**
 * Anniversary API
 */
import apiClient from '../client'
import { API_ENDPOINTS } from '../endpoints'

export const anniversaryApi = {
  list: (params = {}) =>
    apiClient.get(API_ENDPOINTS.ANNIVERSARY.LIST, { params }),
  create: (data) => apiClient.post(API_ENDPOINTS.ANNIVERSARY.CREATE, data),
  update: (id, data) =>
    apiClient.patch(API_ENDPOINTS.ANNIVERSARY.UPDATE(id), data),
  remove: (id) => apiClient.delete(API_ENDPOINTS.ANNIVERSARY.DELETE(id)),
}
