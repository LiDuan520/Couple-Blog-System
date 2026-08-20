# 情侣博客系统 - API 接口文档（前端参考）

> 与后端 [API_Documentation.md](../../backend/doc/API_Documentation.md) 对齐。
> 完整字段说明、错误码、限流策略请参考后端文档。本文件仅给前端开发速查。

## 文档信息
- **API 版本**: v1.0.0
- **基础 URL**: `/api/v1`（开发通过 Vite proxy 转发到 `VITE_API_TARGET`，默认 `http://localhost:8000`）
- **认证方式**: Bearer Token (JWT) — 通过 `Authorization: Bearer <token>` 请求头传递
- **响应**：直接 JSON（Pydantic 序列化），**不**带 `{code, message, data}` 包装

---

## 目录
1. [请求客户端（Axios）](#1-请求客户端axios)
2. [认证接口](#2-认证接口)
3. [用户接口](#3-用户接口)
4. [博客接口](#4-博客接口)
5. [错误处理](#5-错误处理)
6. [React Query 范例](#6-react-query-范例)

---

## 1. 请求客户端（Axios）

`frontend/src/api/client.js` 已配置好：

```javascript
import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
})

// 请求拦截：自动注入 token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// 响应拦截：401 跳登录；其他错误统一格式化
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(new Error(errorHandler(error)))
  }
)

export default apiClient
```

> 注意：拦截器返回 `response.data`（即后端的 Pydantic 序列化结果），**不**再嵌套包装。
> 如果后端 4xx 返回 `{ "detail": "..." }`（FastAPI HTTPException）或 `{ "error": { "code", "message" } }`（业务异常），
> `errorHandler` 会分别处理。

### 端点常量

`frontend/src/api/endpoints.js`：

```javascript
export const API_ENDPOINTS = {
  AUTH: {
    REGISTER:        '/auth/register',
    LOGIN:           '/auth/login',         // OAuth2 form（Swagger 用）
    LOGIN_JSON:      '/auth/login-json',    // JSON（前端用）
    LOGOUT:          '/auth/logout',
    REFRESH:         '/auth/refresh',
    CHANGE_PASSWORD: '/auth/change-password',
    ME:              '/auth/me',
  },
  BLOG: {
    LIST:    '/blogs',
    DETAIL:  (id) => `/blogs/${id}`,
    CREATE:  '/blogs',
    UPDATE:  (id) => `/blogs/${id}`,
    DELETE:  (id) => `/blogs/${id}`,
    PUBLIC:  (authorId) => `/blogs/public/${authorId}`,
  },
  USER: {
    PROFILE:         '/users/me',
    UPDATE_PROFILE:  '/users/me',
    UPLOAD_AVATAR:   '/users/me/avatar',
  },
}
```

---

## 2. 认证接口

### 2.1 注册 `POST /auth/register` → 201

```javascript
const user = await apiClient.post('/auth/register', {
  username: 'alice',
  email: 'alice@test.com',
  password: 'Alice1234',
  nickname: 'Alice',  // 可选
})
// user = { id, username, email, nickname, avatar, is_active, created_at }
```

错误：422（参数验证失败 / Username/Email 已存在）

### 2.2 登录（JSON） `POST /auth/login-json` → 200

```javascript
const data = await apiClient.post('/auth/login-json', {
  username: 'alice',
  password: 'Alice1234',
  remember_me: true,   // 延长 token 有效期到 7 天
})
// data = { access_token, token_type, expires_in, user: UserResponse }

localStorage.setItem('token', data.access_token)
// 推荐同时把 user 存到 zustand 的 authStore
```

错误：401（用户名/密码错、账号未激活）/ 422 / 429（限流）

### 2.3 登录（OAuth2 form） `POST /auth/login` → 200

`Content-Type: application/x-www-form-urlencoded`

```javascript
import qs from 'qs'
const data = await apiClient.post(
  '/auth/login',
  qs.stringify({ username: 'alice', password: 'Alice1234' }),
  { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
)
```

> 前端一般不直接用，仅在 Swagger Authorize 或第三方 OAuth 客户端场景使用。

### 2.4 刷新 token `POST /auth/refresh` → 200

```javascript
const data = await apiClient.post('/auth/refresh')
// data = { access_token, token_type, expires_in }
```

### 2.5 获取当前用户 `GET /auth/me` → 200

```javascript
const user = await apiClient.get('/auth/me')
```

### 2.6 修改密码 `POST /auth/change-password` → 204

```javascript
await apiClient.post('/auth/change-password', {
  old_password: 'Alice1234',
  new_password: 'New12345',
})
// 成功后所有 token 失效，需重新登录
```

### 2.7 登出 `POST /auth/logout` → 204

```javascript
await apiClient.post('/auth/logout')
localStorage.removeItem('token')
// 也可重置 zustand 的 authStore
```

---

## 3. 用户接口

### 3.1 获取我的资料 `GET /users/me` → 200

```javascript
const me = await apiClient.get('/users/me')
// { id, username, email, nickname, avatar, is_active, created_at }
```

### 3.2 更新资料 `PUT /users/me` → 200

```javascript
const me = await apiClient.put('/users/me', {
  nickname: '新昵称',
  email: 'newalice@test.com',
})
```

错误：422（邮箱已被他人占用）

### 3.3 上传头像 `POST /users/me/avatar` → 200

`Content-Type: multipart/form-data`

```javascript
const fd = new FormData()
fd.append('file', fileInput.files[0])  // png/jpg/jpeg/gif/webp，≤ AVATAR_MAX_SIZE_MB
const res = await apiClient.post('/users/me/avatar', fd, {
  headers: { 'Content-Type': 'multipart/form-data' },
})
// res = { avatar_url: '/static/avatars/1_1692456000.png' }

// 拼接完整 URL 展示
const fullUrl = `${import.meta.env.VITE_API_TARGET}${res.avatar_url}`
// 或用相对路径：<img src={res.avatar_url} />（走 Vite proxy 同源）
```

错误：400（扩展名/大小不合规）

---

## 4. 博客接口

### 4.1 创建 `POST /blogs` → 201

```javascript
const blog = await apiClient.post('/blogs', {
  title: '第一次旅行',
  content: '今天我们...',   // 支持 Markdown
  tags: ['旅行', '回忆'],
  is_public: false,         // 私密
})
// blog = { id, title, content, tags, is_public, author_id, is_deleted, created_at, updated_at }
```

### 4.2 列表 `GET /blogs` → 200

```javascript
const { items, total, page, page_size, total_pages } = await apiClient.get('/blogs', {
  params: {
    page: 1,
    page_size: 10,
    tag: '旅行',          // 可选
    search: '关键词',     // 可选
    sort: 'created_at',   // 'created_at' | 'updated_at'
    order: 'desc',        // 'asc' | 'desc'
  },
})
```

> 走后端 Redis 缓存（60s），写操作会自动 invalidate。

### 4.3 公开列表 `GET /blogs/public/{author_id}` → 200

```javascript
const list = await apiClient.get(`/blogs/public/${authorId}`, {
  params: { page: 1, page_size: 10 },
})
```

### 4.4 详情 `GET /blogs/{id}` → 200

```javascript
const blog = await apiClient.get(`/blogs/${blogId}`)
```

### 4.5 更新 `PUT /blogs/{id}` → 200

```javascript
const updated = await apiClient.put(`/blogs/${blogId}`, {
  title: '新标题',
  is_public: true,
  // title / content / tags / is_public 都可选
})
```

### 4.6 删除 `DELETE /blogs/{id}` → 204

```javascript
await apiClient.delete(`/blogs/${blogId}`)
```

---

## 5. 错误处理

### 5.1 错误响应格式

后端有两类错误：

1. **业务异常**（被 `ExceptionHandlerMiddleware` 拦截）：

```json
{ "error": { "code": "AUTH_ERROR", "message": "Invalid username or password" } }
```

2. **Pydantic 验证失败**（FastAPI 默认）：

```json
{ "detail": [ { "loc": ["body","password"], "msg": "..." } ] }
```

3. **FastAPI HTTPException**（如 `get_current_user` 401）：

```json
{ "detail": "Could not validate credentials" }
```

### 5.2 统一处理

`frontend/src/utils/errorHandler.js`：

```javascript
export const errorHandler = (error) => {
  if (error.response) {
    const { status, data } = error.response
    // 业务异常
    if (data?.error?.message) return data.error.message
    // Pydantic / HTTPException
    if (typeof data?.detail === 'string') return data.detail
    if (Array.isArray(data?.detail)) return data.detail.map(d => d.msg).join('; ')

    switch (status) {
      case 401: return '未授权，请重新登录'
      case 403: return '没有权限访问'
      case 404: return '资源未找到'
      case 429: return '操作过于频繁，请稍后再试'
      case 500: return '服务器内部错误'
      default:  return '请求失败'
    }
  }
  if (error.request) return '网络错误，请检查网络连接'
  return error.message || '未知错误'
}
```

### 5.3 401 自动跳登录

`apiClient` 拦截器检测到 401 会清 token 并 `window.location.href = '/login'`。

---

## 6. React Query 范例

### 6.1 查询

```javascript
import { useQuery } from '@tanstack/react-query'
import { blogAPI } from '@/api/modules/blog.api'

// 列表
export const useBlogs = (filters = {}) => useQuery({
  queryKey: ['blogs', 'list', filters],
  queryFn: () => blogAPI.getBlogs(filters),
  staleTime: 30 * 1000,  // 30s（后端有 60s 缓存，前端可以激进点失效）
})

// 详情
export const useBlog = (id) => useQuery({
  queryKey: ['blogs', 'detail', id],
  queryFn: () => blogAPI.getBlog(id),
  enabled: !!id,
})
```

### 6.2 变更

```javascript
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { blogAPI } from '@/api/modules/blog.api'

export const useCreateBlog = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: blogAPI.createBlog,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['blogs', 'list'] })
    },
  })
}

export const useUpdateBlog = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }) => blogAPI.updateBlog(id, data),
    onSuccess: (blog) => {
      qc.invalidateQueries({ queryKey: ['blogs', 'list'] })
      qc.setQueryData(['blogs', 'detail', blog.id], blog)
    },
  })
}

export const useDeleteBlog = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: blogAPI.deleteBlog,
    onSuccess: (_, id) => {
      qc.invalidateQueries({ queryKey: ['blogs', 'list'] })
      qc.removeQueries({ queryKey: ['blogs', 'detail', id] })
    },
  })
}
```

### 6.3 乐观更新（更新博客）

```javascript
export const useUpdateBlogOptimistic = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }) => blogAPI.updateBlog(id, data),
    onMutate: async ({ id, data }) => {
      await qc.cancelQueries({ queryKey: ['blogs', 'detail', id] })
      const prev = qc.getQueryData(['blogs', 'detail', id])
      qc.setQueryData(['blogs', 'detail', id], (old) => ({ ...old, ...data }))
      return { prev, id }
    },
    onError: (_err, _vars, ctx) => {
      if (ctx?.prev) qc.setQueryData(['blogs', 'detail', ctx.id], ctx.prev)
    },
    onSettled: (_data, _err, { id }) => {
      qc.invalidateQueries({ queryKey: ['blogs', 'detail', id] })
      qc.invalidateQueries({ queryKey: ['blogs', 'list'] })
    },
  })
}
```

---

## 7. 类型定义（参考 TypeScript）

```typescript
export interface UserResponse {
  id: number
  username: string
  email: string
  nickname: string | null
  avatar: string | null
  is_active: boolean
  created_at: string  // ISO 8601
}

export interface Token {
  access_token: string
  token_type: 'bearer'
  expires_in: number
  user?: UserResponse
}

export interface Blog {
  id: string
  title: string
  content: string
  tags: string[]
  is_public: boolean
  author_id: number
  is_deleted: boolean
  created_at: string
  updated_at: string
}

export interface Paginated<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}
```

---

## 8. 速查表

| 场景 | Method | Path |
|---|---|---|
| 注册 | POST | `/auth/register` |
| JSON 登录 | POST | `/auth/login-json` |
| OAuth2 登录 | POST | `/auth/login` |
| 刷新 | POST | `/auth/refresh` |
| 改密 | POST | `/auth/change-password` |
| 登出 | POST | `/auth/logout` |
| 当前用户 | GET | `/auth/me` |
| 我的资料 | GET | `/users/me` |
| 更新资料 | PUT | `/users/me` |
| 上传头像 | POST | `/users/me/avatar` |
| 博客列表 | GET | `/blogs` |
| 公开博客 | GET | `/blogs/public/{author_id}` |
| 博客详情 | GET | `/blogs/{id}` |
| 创建博客 | POST | `/blogs` |
| 更新博客 | PUT | `/blogs/{id}` |
| 删除博客 | DELETE | `/blogs/{id}` |

---

**文档版本**: v1.0  
**最后更新**: 2026-08-20
