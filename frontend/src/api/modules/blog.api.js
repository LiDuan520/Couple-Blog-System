import apiClient from '../client'
import { createCancelToken } from '../client'
import { API_ENDPOINTS } from '../endpoints'

export const blogAPI = {
  // 获取博客列表
  getBlogs: async (params = {}) => {
    return apiClient.get(API_ENDPOINTS.BLOG.LIST, {
      params,
      cancelToken: createCancelToken('blog_list'),
    })
  },
  
  // 获取博客详情
  getBlog: async (id) => {
    return apiClient.get(API_ENDPOINTS.BLOG.DETAIL(id), {
      cancelToken: createCancelToken(`blog_${id}`),
    })
  },
  
  // 创建博客
  createBlog: async (data) => {
    return apiClient.post(API_ENDPOINTS.BLOG.CREATE, data, {
      cancelToken: createCancelToken('blog_create'),
    })
  },
  
  // 更新博客
  updateBlog: async (id, data) => {
    return apiClient.put(API_ENDPOINTS.BLOG.UPDATE(id), data, {
      cancelToken: createCancelToken(`blog_update_${id}`),
    })
  },
  
  // 删除博客
  deleteBlog: async (id) => {
    return apiClient.delete(API_ENDPOINTS.BLOG.DELETE(id), {
      cancelToken: createCancelToken(`blog_delete_${id}`),
    })
  },
}

