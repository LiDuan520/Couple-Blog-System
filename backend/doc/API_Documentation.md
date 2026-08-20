# 情侣博客系统 - API 接口文档

> 与 `app/main.py` + `app/api/v1/router.py` + 各模块 `router.py` 实际路由完全对齐。
> 最后更新：2026-08-20（v1.0.0）

## 文档信息
- **API 版本**: v1.0.0
- **基础 URL**: `http://<host>:8000/api/v1`
- **认证方式**: Bearer Token (JWT, HS256)
- **交互文档**: `GET /api/docs` (Swagger UI) · `GET /api/redoc` (ReDoc) · `GET /api/openapi.json`

---

## 目录
1. [通用说明](#1-通用说明)
2. [认证接口 `/auth`](#2-认证接口-auth)
3. [用户接口 `/users`](#3-用户接口-users)
4. [博客接口 `/blogs`](#4-博客接口-blogs)
5. [基础设施接口](#5-基础设施接口)
6. [错误码与响应格式](#6-错误码与响应格式)
7. [限流策略](#7-限流策略)
8. [Curl 速查](#8-curl-速查)

---

## 1. 通用说明

### 1.1 请求头
| Header | 必填 | 说明 |
|---|---|---|
| `Content-Type` | 除 GET 外必填 | 默认 `application/json`；上传头像用 `multipart/form-data` |
| `Authorization` | 多数接口必填 | `Bearer <token>` |

### 1.2 响应格式

**成功响应**：直接返回 Pydantic 序列化的 JSON 对象（**不**套 `{code, message, data}` 包装）。

```json
{
  "id": 1,
  "username": "alice",
  "email": "alice@test.com",
  "nickname": "Alice",
  "avatar": null,
  "is_active": true,
  "created_at": "2026-08-20T12:00:00Z"
}
```

**204 No Content**：DELETE 改密/登出成功，响应体为空。

**错误响应**（由 `ExceptionHandlerMiddleware` 统一处理 `BaseAPIException`）：

```json
{
  "error": {
    "code": "AUTH_ERROR",
    "message": "Invalid username or password"
  }
}
```

Pydantic 校验失败（FastAPI 默认）：

```json
{
  "detail": [
    { "loc": ["body", "password"], "msg": "...", "type": "value_error" }
  ]
}
```

### 1.3 分页参数
| 参数 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `page` | int | 1 | 页码（≥1） |
| `page_size` | int | 10 | 每页（1-100） |

分页响应：

```json
{ "items": [...], "total": 25, "page": 1, "page_size": 10, "total_pages": 3 }
```

### 1.4 时间格式
所有时间戳为 ISO 8601 UTC（`Z` 后缀）。

---

## 2. 认证接口 `/auth`

### 2.1 注册

**`POST /api/v1/auth/register`** · 限流：写操作 60/min · 状态：201

请求体：
```json
{
  "username": "alice",            // 3-50 字符，^[A-Za-z0-9_]+$
  "email": "alice@test.com",      // EmailStr
  "password": "Alice1234",        // ≥8 字符，含字母+数字
  "nickname": "Alice"             // 可选
}
```

响应（`UserResponse`）：
```json
{
  "id": 1, "username": "alice", "email": "alice@test.com", "nickname": "Alice",
  "avatar": null, "is_active": true, "created_at": "2026-08-20T12:00:00Z"
}
```

错误：422（验证失败）/ 422（Username/Email 已存在，返回 `ValidationError`）

---

### 2.2 登录（JSON，前端用）

**`POST /api/v1/auth/login-json`** · 限流：登录 10/min · 状态：200

请求体：
```json
{
  "username": "alice",
  "password": "Alice1234",
  "remember_me": false             // 可选，默认 false。true 时延长 token 有效期
}
```

响应（`Token`）：
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800,              // 秒；remember_me=true 时为 604800
  "user": { "id": 1, "username": "alice", "email": "...", "nickname": "...",
            "avatar": null, "is_active": true, "created_at": "..." }
}
```

错误：401（用户名或密码错） / 401（账号未激活） / 422 / 429（限流）

---

### 2.3 登录（OAuth2 form，Swagger 用）

**`POST /api/v1/auth/login`** · 限流：登录 10/min · 状态：200

`Content-Type: application/x-www-form-urlencoded`

| 字段 | 必填 | 说明 |
|---|---|---|
| `username` | 是 | 用户名 |
| `password` | 是 | 密码 |
| `scope` | 否 | 包含字符串 `remember_me` 即开启记住我 |

Swagger Authorize 按钮走这里。响应同上。

---

### 2.4 刷新 token

**`POST /api/v1/auth/refresh`** · Auth · 状态：200

响应（`Token`，无 `user` 字段）：
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

错误：401

---

### 2.5 获取当前用户

**`GET /api/v1/auth/me`** · Auth · 状态：200

响应同 `UserResponse`（见 2.1）。

---

### 2.6 修改密码

**`POST /api/v1/auth/change-password`** · Auth · 状态：204

请求体：
```json
{
  "old_password": "Alice1234",
  "new_password": "New12345"      // 同样要 ≥8 字符 + 字母数字
}
```

成功后所有该用户 token 失效（清除 `token:<user_id>`），需重新登录。

错误：401（旧密码错） / 422（新密码不合规） / 401（未授权）

---

### 2.7 登出

**`POST /api/v1/auth/logout`** · Auth · 状态：204

把当前 token 加入 Redis 黑名单（`blacklist:<token>`，TTL 与原 token 一致），立即失效。

错误：401

---

## 3. 用户接口 `/users`

### 3.1 获取我的资料

**`GET /api/v1/users/me`** · Auth · 状态：200

响应同 `UserResponse`。

---

### 3.2 更新我的资料

**`PUT /api/v1/users/me`** · Auth · 状态：200

请求体（`UserUpdate`，所有字段可选）：
```json
{
  "nickname": "新昵称",            // 1-100 字符
  "email": "newalice@test.com"    // EmailStr；唯一性校验，不能与他人重复
}
```

响应：`UserResponse`（更新后的值）。

错误：422（邮箱已被他人占用） / 401

---

### 3.3 上传头像

**`POST /api/v1/users/me/avatar`** · Auth · `multipart/form-data` · 状态：200

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `file` | file | 是 | 扩展名 png/jpg/jpeg/gif/webp；大小 ≤ `AVATAR_MAX_SIZE_MB`（默认 2MB） |

响应（`AvatarResponse`）：
```json
{ "avatar_url": "/static/avatars/1_1692456000.png" }
```

文件实际写到 `AVATAR_DIR`（默认 `static/avatars/`），URL 由后端返回相对路径，前端拼接 baseURL。

错误：400（扩展名/大小不合规） / 401

---

## 4. 博客接口 `/blogs`

> 存储：MongoDB（异步，Motor）。`blog_id` 为 ObjectId 字符串。

### 4.1 创建博客

**`POST /api/v1/blogs/`** · Auth · 限流：写 60/min · 状态：201

请求体（`BlogCreate`）：
```json
{
  "title": "第一次旅行",            // 1-200
  "content": "今天我们...",        // 1-10000（支持 Markdown）
  "tags": ["旅行", "回忆"],         // 可选，≤10 个，每个 1-20
  "is_public": false               // 默认 false（私密）
}
```

响应（`BlogResponse`）：
```json
{
  "id": "65a1b2c3d4e5f6g7h8i9j0k1",
  "title": "第一次旅行",
  "content": "今天我们...",
  "tags": ["旅行", "回忆"],
  "is_public": false,
  "author_id": 1,
  "is_deleted": false,
  "created_at": "2026-08-20T12:00:00Z",
  "updated_at": "2026-08-20T12:00:00Z"
}
```

错误：422 / 401 / 429

---

### 4.2 博客列表（自己的）

**`GET /api/v1/blogs/`** · Auth

| Query | 类型 | 默认 | 说明 |
|---|---|---|---|
| `page` | int | 1 | ≥1 |
| `page_size` | int | 10 | 1-100 |
| `tag` | string | — | 精确匹配单个标签 |
| `search` | string | — | 标题/内容模糊搜索 |
| `sort` | enum | `created_at` | `created_at` \| `updated_at` |
| `order` | enum | `desc` | `asc` \| `desc` |

响应：`BlogListResponse`

> 缓存：Redis key `blogs:list:user:<id>:<query_hash>`，TTL 60s。写操作（创建/更新/删除）会 invalidate。

---

### 4.3 公开博客列表（他人的）

**`GET /api/v1/blogs/public/{author_id}`** · Auth

| 路径 | 类型 | 说明 |
|---|---|---|
| `author_id` | int | 作者用户 ID |

仅返回 `is_public=true` 且 `is_deleted=false` 的博客。分页参数同 4.2。

---

### 4.4 博客详情

**`GET /api/v1/blogs/{blog_id}`** · Auth

仅作者可看自己全部博客（含 `is_public=false`）。他人访问私密博客 → 403 / 404。

---

### 4.5 更新博客

**`PUT /api/v1/blogs/{blog_id}`** · Auth · 限流：写 60/min · 状态：200

请求体（`BlogUpdate`，所有字段可选）：
```json
{
  "title": "更新后的标题",
  "content": "更新后的内容",
  "tags": ["新标签"],
  "is_public": true
}
```

响应：`BlogResponse`。

错误：404（不存在） / 403（非作者） / 422

---

### 4.6 删除博客（软删）

**`DELETE /api/v1/blogs/{blog_id}`** · Auth · 限流：写 60/min · 状态：204

设置 `is_deleted=true`（保留数据，便于恢复）。列表/详情接口默认过滤掉。

错误：404 / 403

---

## 5. 基础设施接口

| Method | Path | Auth | 说明 |
|---|---|---|---|
| GET | `/` | ❌ | 返回 `{ "message": "情侣博客 API", "version": "1.0.0" }` |
| GET | `/health` | ❌ | 健康检查，返回 `{ "status": "healthy" }` |
| GET | `/api/docs` | ❌ | Swagger UI |
| GET | `/api/redoc` | ❌ | ReDoc |
| GET | `/api/openapi.json` | ❌ | OpenAPI schema |
| GET | `/static/...` | ❌ | 头像等静态资源（Nginx 直出） |

---

## 6. 错误码与响应格式

### 6.1 HTTP 状态码

| 状态 | 含义 |
|---|---|
| 200 | OK |
| 201 | Created |
| 204 | No Content（登出、改密、删除） |
| 400 | 请求参数错误（业务自定义） |
| 401 | 未授权 / Token 无效 / 黑名单 |
| 403 | 禁止访问（非作者） |
| 404 | 资源不存在 |
| 422 | 数据验证失败（Pydantic） |
| 429 | 限流（`RATE_LIMIT_LOGIN_PER_MIN` / `RATE_LIMIT_WRITE_PER_MIN`） |
| 500 | 服务器内部错误 |

### 6.2 业务错误码（`error.code` 字段）

| 错误码 | HTTP | 含义 |
|---|---|---|
| `VALIDATION_ERROR` | 422 | 业务校验失败（密码弱、用户名已存在等） |
| `AUTH_ERROR` | 401 | 认证失败（密码错、token 失效） |
| `AUTHORIZATION_ERROR` | 403 | 授权失败（访问他人资源） |
| `NOT_FOUND` | 404 | 资源不存在 |
| `INTERNAL_ERROR` | 500 | 服务器内部错误（异常统一返回 `Internal server error`，细节进日志） |

> Pydantic 422 不走 `ExceptionHandlerMiddleware`，直接返回 FastAPI 默认的 `{ "detail": [...] }`。

---

## 7. 限流策略

通过 `app/api/rate_limit.py` 的装饰器实现，键基于 `user_id` 或 IP（未登录场景）。

| 接口 | 默认阈值 | 配置 |
|---|---|---|
| `POST /auth/login*` | 10 次/分钟 | `RATE_LIMIT_LOGIN_PER_MIN` |
| `POST /auth/register` | 60 次/分钟 | `RATE_LIMIT_WRITE_PER_MIN` |
| `POST /blogs/` | 60 次/分钟 | `RATE_LIMIT_WRITE_PER_MIN` |
| `PUT /blogs/{id}` | 60 次/分钟 | `RATE_LIMIT_WRITE_PER_MIN` |
| `DELETE /blogs/{id}` | 60 次/分钟 | `RATE_LIMIT_WRITE_PER_MIN` |

超限返回 HTTP 429。

---

## 8. Curl 速查

```bash
# 0. 变量
BASE=http://localhost:8000/api/v1

# 1. 注册
curl -X POST $BASE/auth/register -H 'Content-Type: application/json' -d '{
  "username":"alice","email":"alice@test.com","password":"Alice1234"
}'

# 2. 登录（拿 token）
TOKEN=$(curl -s -X POST $BASE/auth/login-json -H 'Content-Type: application/json' -d '{
  "username":"alice","password":"Alice1234","remember_me":true
}' | jq -r '.access_token')

# 3. 拿自己
curl $BASE/auth/me -H "Authorization: Bearer $TOKEN"

# 4. 写博客
curl -X POST $BASE/blogs/ -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{
  "title":"hi","content":"hello","tags":["测试"],"is_public":true
}'

# 5. 列博客
curl "$BASE/blogs/?page=1&page_size=10" -H "Authorization: Bearer $TOKEN"

# 6. 改密
curl -X POST $BASE/auth/change-password -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{
  "old_password":"Alice1234","new_password":"New12345"
}'

# 7. 登出
curl -X POST $BASE/auth/logout -H "Authorization: Bearer $TOKEN" -i
```

---

## 9. 版本历史

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0.0 | 2026-08-20 | 初版，与实施计划接口契约对齐 |
