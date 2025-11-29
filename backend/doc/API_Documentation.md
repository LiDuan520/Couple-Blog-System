# 情侣博客系统 - API 接口文档

## 文档信息
- **API 版本**: v1.0.0
- **基础 URL**: `http://localhost:8000/api/v1`
- **文档更新**: 2024-01-XX
- **认证方式**: Bearer Token (JWT)

---

## 目录
1. [通用说明](#1-通用说明)
2. [认证接口](#2-认证接口)
3. [用户接口](#3-用户接口)
4. [博客接口](#4-博客接口)
5. [错误码说明](#5-错误码说明)

---

## 1. 通用说明

### 1.1 请求格式
- **Content-Type**: `application/json`
- **字符编码**: UTF-8
- **请求方法**: GET, POST, PUT, DELETE

### 1.2 响应格式
所有接口统一返回 JSON 格式：

**成功响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    // 响应数据
  }
}
```

**错误响应**:
```json
{
  "code": 400,
  "message": "错误描述",
  "error": {
    "code": "ERROR_CODE",
    "message": "详细错误信息"
  }
}
```

### 1.3 认证说明
除登录、注册接口外，所有接口需要在请求头中携带 Token：

```
Authorization: Bearer {token}
```

### 1.4 分页参数
列表接口支持分页：

| 参数 | 类型 | 必填 | 说明 | 默认值 |
|------|------|------|------|--------|
| page | integer | 否 | 页码 | 1 |
| page_size | integer | 否 | 每页数量 | 10 |
| max_page_size | integer | - | 最大每页数量 | 100 |

**分页响应格式**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [],
    "total": 100,
    "page": 1,
    "page_size": 10,
    "total_pages": 10
  }
}
```

---

## 2. 认证接口

### 2.1 用户注册

**接口地址**: `POST /auth/register`

**接口描述**: 新用户注册账号

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名，3-50个字符，仅支持字母、数字、下划线 |
| email | string | 是 | 邮箱地址，需符合邮箱格式 |
| password | string | 是 | 密码，至少8位，包含字母和数字 |
| nickname | string | 否 | 昵称，默认使用用户名 |

**请求示例**:
```json
{
  "username": "couple2024",
  "email": "couple@example.com",
  "password": "Love2024!",
  "nickname": "我们的回忆"
}
```

**响应示例**:
```json
{
  "code": 201,
  "message": "注册成功",
  "data": {
    "id": 1,
    "username": "couple2024",
    "email": "couple@example.com",
    "nickname": "我们的回忆",
    "avatar": null,
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

**错误码**:
- `400`: 参数错误
- `409`: 用户名或邮箱已存在
- `422`: 数据验证失败

---

### 2.2 用户登录

**接口地址**: `POST /auth/login`

**接口描述**: 用户登录，获取访问令牌

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名或邮箱 |
| password | string | 是 | 密码 |

**请求示例**:
```json
{
  "username": "couple2024",
  "password": "Love2024!"
}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": {
      "id": 1,
      "username": "couple2024",
      "email": "couple@example.com",
      "nickname": "我们的回忆",
      "avatar": null
    }
  }
}
```

**错误码**:
- `401`: 用户名或密码错误
- `400`: 账号被禁用
- `422`: 参数验证失败

---

### 2.3 用户登出

**接口地址**: `POST /auth/logout`

**接口描述**: 用户登出，使 Token 失效

**请求头**:
```
Authorization: Bearer {token}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "登出成功"
}
```

**错误码**:
- `401`: 未授权

---

### 2.4 获取当前用户信息

**接口地址**: `GET /auth/me`

**接口描述**: 获取当前登录用户的信息

**请求头**:
```
Authorization: Bearer {token}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "username": "couple2024",
    "email": "couple@example.com",
    "nickname": "我们的回忆",
    "avatar": "https://example.com/avatar.jpg",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

**错误码**:
- `401`: 未授权或 Token 无效

---

## 3. 用户接口

### 3.1 更新用户信息

**接口地址**: `PUT /users/me`

**接口描述**: 更新当前用户的信息

**请求头**:
```
Authorization: Bearer {token}
```

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| nickname | string | 否 | 昵称 |
| avatar | string | 否 | 头像 URL |

**请求示例**:
```json
{
  "nickname": "新的昵称",
  "avatar": "https://example.com/new-avatar.jpg"
}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "更新成功",
  "data": {
    "id": 1,
    "username": "couple2024",
    "email": "couple@example.com",
    "nickname": "新的昵称",
    "avatar": "https://example.com/new-avatar.jpg",
    "updated_at": "2024-01-15T11:00:00Z"
  }
}
```

---

### 3.2 修改密码

**接口地址**: `PUT /users/me/password`

**接口描述**: 修改当前用户的密码

**请求头**:
```
Authorization: Bearer {token}
```

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| old_password | string | 是 | 旧密码 |
| new_password | string | 是 | 新密码，至少8位，包含字母和数字 |

**请求示例**:
```json
{
  "old_password": "Love2024!",
  "new_password": "NewPass2024!"
}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "密码修改成功"
}
```

**错误码**:
- `400`: 旧密码错误
- `422`: 新密码不符合要求

---

## 4. 博客接口

### 4.1 创建博客

**接口地址**: `POST /blogs`

**接口描述**: 创建新的博客文章

**请求头**:
```
Authorization: Bearer {token}
```

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 是 | 标题，1-200个字符 |
| content | string | 是 | 内容，支持 Markdown，最大 10000 字符 |
| tags | array[string] | 否 | 标签列表，每个标签 1-20 个字符 |
| is_public | boolean | 否 | 是否公开，默认 false |

**请求示例**:
```json
{
  "title": "我们的第一次旅行",
  "content": "今天是我们第一次一起旅行，去了...",
  "tags": ["旅行", "回忆", "美好"],
  "is_public": false
}
```

**响应示例**:
```json
{
  "code": 201,
  "message": "创建成功",
  "data": {
    "id": "65a1b2c3d4e5f6g7h8i9j0k1",
    "title": "我们的第一次旅行",
    "content": "今天是我们第一次一起旅行，去了...",
    "tags": ["旅行", "回忆", "美好"],
    "is_public": false,
    "author_id": 1,
    "created_at": "2024-01-15T12:00:00Z",
    "updated_at": "2024-01-15T12:00:00Z"
  }
}
```

**错误码**:
- `400`: 参数错误
- `401`: 未授权
- `422`: 数据验证失败

---

### 4.2 获取博客列表

**接口地址**: `GET /blogs`

**接口描述**: 获取当前用户的博客列表

**请求头**:
```
Authorization: Bearer {token}
```

**查询参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | integer | 否 | 页码，默认 1 |
| page_size | integer | 否 | 每页数量，默认 10 |
| tag | string | 否 | 按标签筛选 |
| search | string | 否 | 搜索关键词（标题、内容） |
| sort | string | 否 | 排序方式，`created_at` 或 `updated_at`，默认 `created_at` |
| order | string | 否 | 排序顺序，`asc` 或 `desc`，默认 `desc` |

**请求示例**:
```
GET /blogs?page=1&page_size=10&tag=旅行&sort=created_at&order=desc
```

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "65a1b2c3d4e5f6g7h8i9j0k1",
        "title": "我们的第一次旅行",
        "content": "今天是我们第一次一起旅行，去了...",
        "summary": "今天是我们第一次一起旅行，去了...",
        "tags": ["旅行", "回忆"],
        "is_public": false,
        "author_id": 1,
        "created_at": "2024-01-15T12:00:00Z",
        "updated_at": "2024-01-15T12:00:00Z"
      }
    ],
    "total": 25,
    "page": 1,
    "page_size": 10,
    "total_pages": 3
  }
}
```

---

### 4.3 获取博客详情

**接口地址**: `GET /blogs/{blog_id}`

**接口描述**: 获取单篇博客的详细信息

**请求头**:
```
Authorization: Bearer {token}
```

**路径参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| blog_id | string | 是 | 博客 ID（MongoDB ObjectId） |

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "65a1b2c3d4e5f6g7h8i9j0k1",
    "title": "我们的第一次旅行",
    "content": "今天是我们第一次一起旅行，去了...",
    "tags": ["旅行", "回忆", "美好"],
    "is_public": false,
    "author_id": 1,
    "created_at": "2024-01-15T12:00:00Z",
    "updated_at": "2024-01-15T12:00:00Z"
  }
}
```

**错误码**:
- `404`: 博客不存在
- `403`: 无权限访问（非作者）

---

### 4.4 更新博客

**接口地址**: `PUT /blogs/{blog_id}`

**接口描述**: 更新博客内容

**请求头**:
```
Authorization: Bearer {token}
```

**路径参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| blog_id | string | 是 | 博客 ID |

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 否 | 标题 |
| content | string | 否 | 内容 |
| tags | array[string] | 否 | 标签列表 |
| is_public | boolean | 否 | 是否公开 |

**请求示例**:
```json
{
  "title": "我们的第一次旅行（更新）",
  "tags": ["旅行", "回忆", "美好", "更新"]
}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "更新成功",
  "data": {
    "id": "65a1b2c3d4e5f6g7h8i9j0k1",
    "title": "我们的第一次旅行（更新）",
    "content": "今天是我们第一次一起旅行，去了...",
    "tags": ["旅行", "回忆", "美好", "更新"],
    "updated_at": "2024-01-15T13:00:00Z"
  }
}
```

**错误码**:
- `404`: 博客不存在
- `403`: 无权限（非作者）
- `422`: 数据验证失败

---

### 4.5 删除博客

**接口地址**: `DELETE /blogs/{blog_id}`

**接口描述**: 删除博客

**请求头**:
```
Authorization: Bearer {token}
```

**路径参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| blog_id | string | 是 | 博客 ID |

**响应示例**:
```json
{
  "code": 200,
  "message": "删除成功"
}
```

**错误码**:
- `404`: 博客不存在
- `403`: 无权限（非作者）

---

## 5. 错误码说明

### 5.1 HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 204 | 删除成功（无响应体） |
| 400 | 请求参数错误 |
| 401 | 未授权（Token 无效或过期） |
| 403 | 无权限访问 |
| 404 | 资源不存在 |
| 409 | 资源冲突（如用户名已存在） |
| 422 | 数据验证失败 |
| 500 | 服务器内部错误 |

### 5.2 业务错误码

| 错误码 | 说明 |
|--------|------|
| `VALIDATION_ERROR` | 数据验证失败 |
| `AUTH_ERROR` | 认证失败 |
| `AUTHORIZATION_ERROR` | 授权失败 |
| `NOT_FOUND` | 资源未找到 |
| `DUPLICATE_ERROR` | 资源重复 |
| `INTERNAL_ERROR` | 服务器内部错误 |

### 5.3 错误响应示例

```json
{
  "code": 422,
  "message": "数据验证失败",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "标题不能为空",
    "details": [
      {
        "field": "title",
        "message": "标题不能为空"
      }
    ]
  }
}
```

---

## 6. 接口测试

### 6.1 Swagger 文档
访问 `http://localhost:8000/api/docs` 查看交互式 API 文档

### 6.2 Postman 集合
可导入 Postman Collection 进行接口测试（待提供）

---

## 7. 版本历史

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| v1.0.0 | 2024-01-XX | 初始版本，包含认证和博客基础功能 |

---

**文档状态**: ✅ 已完成
**维护者**: 后端开发团队

