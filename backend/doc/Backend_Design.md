# 情侣博客系统 - 后端设计文档

## 文档信息
- **文档版本**: v1.0.0
- **创建日期**: 2024-01-XX
- **最后更新**: 2024-01-XX
- **文档作者**: 技术团队
- **审核状态**: 待审核

---

## 目录
1. [系统架构设计](#1-系统架构设计)
2. [项目结构](#2-项目结构)
3. [模块设计](#3-模块设计)
4. [数据库设计](#4-数据库设计)
5. [安全设计](#5-安全设计)
6. [性能优化](#6-性能优化)
7. [部署方案](#7-部署方案)

---

## 1. 系统架构设计

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                        客户端层                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  Web 前端    │  │  移动端 H5   │  │  未来: App   │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
└─────────┼──────────────────┼──────────────────┼─────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
                    ┌────────▼────────┐
                    │   API 网关层     │
                    │   (FastAPI)     │
                    └────────┬────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
    ┌─────▼─────┐    ┌──────▼──────┐    ┌─────▼─────┐
    │ 认证模块   │    │  博客模块    │    │  用户模块  │
    │ (Auth)    │    │  (Blog)     │    │  (User)   │
    └─────┬─────┘    └──────┬──────┘    └─────┬─────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
    ┌─────▼─────┐    ┌──────▼──────┐    ┌─────▼─────┐
    │PostgreSQL │    │  MongoDB    │    │   Redis   │
    │  (用户)    │    │  (博客)     │    │  (缓存)   │
    └───────────┘    └─────────────┘    └───────────┘
```

### 1.2 架构特点

- **前后端分离**: 前端独立部署，通过 RESTful API 通信
- **模块化设计**: 业务模块独立，便于后续拆分为微服务
- **数据分离**: 
  - PostgreSQL: 存储结构化数据（用户信息）
  - MongoDB: 存储非结构化数据（博客内容）
  - Redis: 缓存和会话管理

### 1.3 技术栈选型

#### 后端技术栈
- **框架**: FastAPI 0.104+
- **语言**: Python 3.10+
- **ORM**: SQLAlchemy 2.0+ (PostgreSQL)
- **ODM**: Motor (MongoDB)
- **缓存**: Redis 7+
- **认证**: JWT (python-jose)
- **密码加密**: bcrypt (passlib)
- **API 文档**: Swagger/OpenAPI

---

## 2. 项目结构

```
backend/
├── app/
│   ├── main.py                 # 应用入口
│   ├── config.py               # 配置管理
│   │
│   ├── core/                   # 核心基础设施
│   │   ├── database.py         # 数据库连接（PostgreSQL + MongoDB）
│   │   ├── redis_client.py     # Redis 客户端
│   │   ├── security.py         # 安全工具（JWT、密码加密）
│   │   ├── exceptions.py       # 自定义异常
│   │   ├── middleware.py       # 中间件
│   │   ├── validators.py       # 输入验证
│   │   └── logging_config.py   # 日志配置
│   │
│   ├── modules/                # 业务模块（可独立为微服务）
│   │   ├── auth/               # 认证模块
│   │   │   ├── models.py       # 数据模型（PostgreSQL）
│   │   │   ├── schemas.py      # Pydantic 模式
│   │   │   ├── service.py      # 业务逻辑层
│   │   │   ├── repository.py   # 数据访问层
│   │   │   └── router.py       # API 路由
│   │   │
│   │   ├── blog/               # 博客模块
│   │   │   ├── models.py       # 数据模型（MongoDB）
│   │   │   ├── schemas.py      # Pydantic 模式
│   │   │   ├── service.py      # 业务逻辑层
│   │   │   ├── repository.py   # 数据访问层
│   │   │   └── router.py       # API 路由
│   │   │
│   │   └── user/               # 用户模块
│   │       ├── models.py
│   │       ├── schemas.py
│   │       ├── service.py
│   │       ├── repository.py
│   │       └── router.py
│   │
│   ├── shared/                 # 共享组件
│   │   ├── types.py            # 类型定义
│   │   ├── constants.py        # 常量
│   │   └── utils.py            # 工具函数
│   │
│   └── api/                    # API 层
│       ├── deps.py             # 全局依赖（认证等）
│       └── v1/
│           └── router.py       # 路由聚合
│
├── tests/                      # 测试
├── alembic/                    # 数据库迁移
├── requirements.txt
└── .env.example
```

---

## 3. 模块设计

### 3.1 分层架构

每个模块采用三层架构：

```
┌─────────────┐
│  Router     │  API 路由层（处理 HTTP 请求）
├─────────────┤
│  Service    │  业务逻辑层（业务规则处理）
├─────────────┤
│ Repository  │  数据访问层（数据库操作）
└─────────────┘
```

### 3.2 认证模块 (auth)

**功能职责**:
- 用户注册
- 用户登录（JWT Token 生成）
- 用户登出（Token 黑名单）
- Token 验证

**数据模型** (PostgreSQL):
```python
class User(Base):
    id: int (PK)
    username: str (unique)
    email: str (unique)
    hashed_password: str
    nickname: str
    avatar: str (nullable)
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

**关键设计**:
- 密码使用 bcrypt 加密（10 轮）
- JWT Token 存储在 Redis
- Token 黑名单机制（Redis）

### 3.3 博客模块 (blog)

**功能职责**:
- 博客创建
- 博客查询（列表、详情）
- 博客更新
- 博客删除

**数据模型** (MongoDB):
```javascript
{
  _id: ObjectId,
  title: String,
  content: String,
  tags: [String],
  is_public: Boolean,
  author_id: Integer,  // 关联 PostgreSQL User.id
  created_at: DateTime,
  updated_at: DateTime
}
```

**关键设计**:
- 内容存储在 MongoDB（灵活扩展）
- 作者信息关联 PostgreSQL（数据一致性）
- 支持全文搜索（未来功能）

---

## 4. 数据库设计

### 4.1 PostgreSQL 设计（用户数据）

#### 4.1.1 users 表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTO_INCREMENT | 用户 ID |
| username | VARCHAR(50) | UNIQUE, NOT NULL | 用户名 |
| email | VARCHAR(100) | UNIQUE, NOT NULL | 邮箱 |
| hashed_password | VARCHAR(255) | NOT NULL | 加密密码 |
| nickname | VARCHAR(100) | | 昵称 |
| avatar | VARCHAR(255) | | 头像 URL |
| is_active | BOOLEAN | DEFAULT TRUE | 是否激活 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP | | 更新时间 |

**索引**:
- `idx_users_username`: username
- `idx_users_email`: email

### 4.2 MongoDB 设计（博客数据）

#### 4.2.1 blogs 集合

```javascript
{
  _id: ObjectId,
  title: String,              // 标题
  content: String,            // 内容（Markdown）
  tags: [String],             // 标签数组
  is_public: Boolean,         // 是否公开
  author_id: Integer,         // 作者 ID（关联 PostgreSQL）
  created_at: ISODate,        // 创建时间
  updated_at: ISODate         // 更新时间
}
```

**索引**:
- `idx_author_id`: author_id
- `idx_created_at`: created_at (降序)
- `idx_tags`: tags
- `idx_title_text`: title (文本索引，用于搜索)

### 4.3 Redis 设计（缓存）

#### 4.3.1 Key 设计规范

```
token:{user_id}              → Token 存储（String，TTL: 30分钟）
blacklist:{token}            → Token 黑名单（String，TTL: 30分钟）
user:{user_id}               → 用户信息缓存（Hash，TTL: 1小时）
blogs:list:{user_id}:{page}  → 博客列表缓存（String，TTL: 5分钟）
blog:{blog_id}               → 博客详情缓存（String，TTL: 10分钟）
```

---

## 5. 安全设计

### 5.1 认证安全
- JWT Token 使用 HS256 算法
- Token 存储在 Redis，支持黑名单
- 密码使用 bcrypt（10 轮）

### 5.2 数据安全
- SQL 注入防护：参数化查询
- XSS 防护：输入验证和输出转义
- CSRF 防护：Token 验证（未来功能）

### 5.3 接口安全
- 请求频率限制（未来功能）
- IP 白名单（未来功能）
- HTTPS 传输（生产环境）

---

## 6. 性能优化

### 6.1 数据库优化
- 数据库连接池
- 查询优化（索引、分页）
- 异步处理（MongoDB 异步操作）

### 6.2 缓存策略
- Redis 缓存热点数据
- 缓存失效策略
- 缓存预热（未来功能）

---

## 7. 部署方案

### 7.1 开发环境
- Docker Compose 启动数据库服务
- 后端：`uvicorn app.main:app --reload`

### 7.2 生产环境
- 容器化部署（Docker）
- Nginx 反向代理
- 数据库主从复制（未来功能）
- Redis 集群（未来功能）

### 7.3 监控与日志
- 应用日志（文件 + 标准输出）
- 错误监控（Sentry，未来功能）
- 性能监控（APM，未来功能）

---

## 8. 开发规范

### 8.1 代码规范
- Python: PEP 8, Black 格式化
- Git: Conventional Commits

### 8.2 测试规范
- 单元测试覆盖率 > 80%
- 集成测试覆盖核心流程
- API 测试（Postman/自动化）

### 8.3 文档规范
- 代码注释（Docstring）
- API 文档（Swagger）
- 更新日志（CHANGELOG）

---

## 9. 后续扩展计划

### 9.1 功能扩展
- 图片上传（OSS）
- 视频支持
- 评论系统
- 分享功能

### 9.2 架构扩展
- 微服务拆分
- 消息队列（RabbitMQ/Kafka）
- 服务网格（Istio，未来）

---

**文档状态**: ✅ 已完成
**下一步**: 开始开发实施

