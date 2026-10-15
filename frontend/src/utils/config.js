/**
 * 全局配置
 */

// 后端 API 基础 URL（用于构建静态文件地址）
// 默认为相对路径，部署时可改为绝对域名
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

// 上传文件大小限制 (MB)
export const UPLOAD_MAX_SIZE_MB = 10

// 允许上传的图片类型
export const ALLOWED_IMAGE_TYPES = [
  'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp',
]
