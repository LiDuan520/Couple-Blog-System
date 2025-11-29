# 情侣博客系统 - API 接口文档（前端参考）

## 文档信息
- **API 版本**: v1.0.0
- **基础 URL**: `http://localhost:8000/api/v1`
- **文档更新**: 2024-01-XX
- **认证方式**: Bearer Token (JWT)

> 本文档为前端开发参考，详细接口文档请参考后端文档。

---

## 目录
1. [通用说明](#1-通用说明)
2. [认证接口](#2-认证接口)
3. [用户接口](#3-用户接口)
4. [博客接口](#4-博客接口)

---

## 1. 通用说明

### 1.1 请求配置
```javascript
// Axios 配置示例
const apiClient = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器 - 添加 Token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器 - 统一错误处理
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      // 清除 token，跳转登录
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

### 1.2 响应格式
```typescript
// 成功响应
interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
}

// 分页响应
interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
```

---

## 2. 认证接口

### 2.1 用户注册

**接口**: `POST /auth/register`

**请求示例**:
```javascript
const response = await apiClient.post('/auth/register', {
  username: 'couple2024',
  email: 'couple@example.com',
  password: 'Love2024!',
  nickname: '我们的回忆'
});

// 响应
{
  code: 201,
  message: "注册成功",
  data: {
    id: 1,
    username: "couple2024",
    email: "couple@example.com",
    nickname: "我们的回忆",
    avatar: null,
    is_active: true,
    created_at: "2024-01-15T10:30:00Z"
  }
}
```

### 2.2 用户登录

**接口**: `POST /auth/login`

**请求示例**:
```javascript
const response = await apiClient.post('/auth/login', {
  username: 'couple2024',
  password: 'Love2024!'
});

// 响应
{
  code: 200,
  message: "登录成功",
  data: {
    access_token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    token_type: "bearer",
    expires_in: 1800,
    user: {
      id: 1,
      username: "couple2024",
      email: "couple@example.com",
      nickname: "我们的回忆"
    }
  }
}

// 保存 Token
localStorage.setItem('token', response.data.access_token);
```

### 2.3 用户登出

**接口**: `POST /auth/logout`

**请求示例**:
```javascript
await apiClient.post('/auth/logout');
localStorage.removeItem('token');
```

### 2.4 获取当前用户

**接口**: `GET /auth/me`

**请求示例**:
```javascript
const response = await apiClient.get('/auth/me');
// 响应包含用户完整信息
```

---

## 3. 用户接口

### 3.1 更新用户信息

**接口**: `PUT /users/me`

**请求示例**:
```javascript
const response = await apiClient.put('/users/me', {
  nickname: '新的昵称',
  avatar: 'https://example.com/avatar.jpg'
});
```

### 3.2 修改密码

**接口**: `PUT /users/me/password`

**请求示例**:
```javascript
await apiClient.put('/users/me/password', {
  old_password: 'Love2024!',
  new_password: 'NewPass2024!'
});
```

---

## 4. 博客接口

### 4.1 创建博客

**接口**: `POST /blogs`

**请求示例**:
```javascript
const response = await apiClient.post('/blogs', {
  title: '我们的第一次旅行',
  content: '今天是我们第一次一起旅行，去了...',
  tags: ['旅行', '回忆', '美好'],
  is_public: false
});
```

### 4.2 获取博客列表

**接口**: `GET /blogs`

**请求示例**:
```javascript
// 基础查询
const response = await apiClient.get('/blogs', {
  params: {
    page: 1,
    page_size: 10
  }
});

// 带筛选
const response = await apiClient.get('/blogs', {
  params: {
    page: 1,
    page_size: 10,
    tag: '旅行',
    search: '关键词',
    sort: 'created_at',
    order: 'desc'
  }
});

// 响应
{
  code: 200,
  message: "success",
  data: {
    items: [...],
    total: 25,
    page: 1,
    page_size: 10,
    total_pages: 3
  }
}
```

### 4.3 获取博客详情

**接口**: `GET /blogs/{blog_id}`

**请求示例**:
```javascript
const response = await apiClient.get(`/blogs/${blogId}`);
```

### 4.4 更新博客

**接口**: `PUT /blogs/{blog_id}`

**请求示例**:
```javascript
const response = await apiClient.put(`/blogs/${blogId}`, {
  title: '更新的标题',
  tags: ['新标签']
});
```

### 4.5 删除博客

**接口**: `DELETE /blogs/{blog_id}`

**请求示例**:
```javascript
await apiClient.delete(`/blogs/${blogId}`);
```

---

## 5. React Query 使用示例

### 5.1 查询博客列表

```javascript
import { useQuery } from '@tanstack/react-query';
import { blogAPI } from '@/api/modules/blog.api';

export const useBlogs = (filters = {}) => {
  return useQuery({
    queryKey: ['blogs', 'list', filters],
    queryFn: () => blogAPI.getBlogs(filters),
    staleTime: 5 * 60 * 1000, // 5分钟
  });
};
```

### 5.2 创建博客

```javascript
import { useMutation, useQueryClient } from '@tanstack/react-query';

export const useCreateBlog = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: blogAPI.createBlog,
    onSuccess: () => {
      // 使列表缓存失效，重新获取
      queryClient.invalidateQueries(['blogs', 'list']);
    },
  });
};
```

---

## 6. 错误处理

### 6.1 统一错误处理

```javascript
// utils/errorHandler.js
export const errorHandler = (error) => {
  if (error.response) {
    const { status, data } = error.response;
    
    switch (status) {
      case 400:
        return data?.error?.message || '请求参数错误';
      case 401:
        return '未授权，请重新登录';
      case 403:
        return '没有权限访问';
      case 404:
        return '资源未找到';
      case 422:
        return data?.error?.message || '数据验证失败';
      case 500:
        return '服务器内部错误';
      default:
        return '请求失败';
    }
  } else if (error.request) {
    return '网络错误，请检查网络连接';
  } else {
    return error.message || '未知错误';
  }
};
```

---

**文档状态**: ✅ 已完成
**维护者**: 前端开发团队

