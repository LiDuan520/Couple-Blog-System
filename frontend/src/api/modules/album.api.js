/**
 * Album API
 */
import apiClient from '../client'
import { API_ENDPOINTS } from '../endpoints'

export const albumApi = {
  list: () => apiClient.get(API_ENDPOINTS.ALBUM.LIST),
  create: (data) => apiClient.post(API_ENDPOINTS.ALBUM.CREATE, data),
  update: (id, data) => apiClient.patch(API_ENDPOINTS.ALBUM.UPDATE(id), data),
  remove: (id) => apiClient.delete(API_ENDPOINTS.ALBUM.DELETE(id)),

  // Photos
  listPhotos: (albumId, params = {}) =>
    apiClient.get(API_ENDPOINTS.ALBUM.LIST_PHOTOS(albumId), { params }),
  uploadPhoto: (albumId, formData) =>
    apiClient.post(API_ENDPOINTS.ALBUM.UPLOAD_PHOTO(albumId), formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  updatePhoto: (photoId, data) =>
    apiClient.patch(API_ENDPOINTS.ALBUM.UPDATE_PHOTO(photoId), data),
  removePhoto: (photoId) =>
    apiClient.delete(API_ENDPOINTS.ALBUM.DELETE_PHOTO(photoId)),
}
