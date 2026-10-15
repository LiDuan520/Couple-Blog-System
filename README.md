# 情侣博客系统 (Couple Blog System)

一个专为情侣设计的私密博客平台，支持文字、图片、Markdown、时间轴等多种形式的内容记录。

> v1.0 · 已完成 MVP：注册/登录/资料/博客 CRUD/列表分页/标签/搜索/缓存/限流/测试覆盖。

---

## ✨ 功能一览

| 模块 | 功能 |
|---|---|
| **认证** | 注册 / JSON 登录 / OAuth2 表单登录（Swagger）/ 记住我 / 刷新 token / 改密 / 登出（Redis 黑名单） |
| **用户** | 查看 / 修改资料 / 上传头像（PNG/JPG，大小限制）/ 限流 / 邮箱唯一性 |
| **博客** | 创建 / 列表（分页/标签/搜索/排序） / 详情 / 更新 / 软删除 / 公开主页 / Redis 缓存 |
| **安全** | JWT (HS256) + bcrypt + Redis 黑名单 + 安全响应头 (CSP / X-Frame-Options) + 输入校验 + 限流 + 审计日志 |
| **可观测** | 结构化日志 + 请求日志中间件 + 健康检查 `/health` |

---

## 🚀 一键启动（开发环境）

### 前置条件
- Docker + Docker Compose
- Node.js 18+（仅前端开发需要）
- Python 3.10+（仅后端开发需要）

### 1. 启动数据库

```bash
docker-compose up -d
```

会启动 PostgreSQL (5432) / MongoDB (27017) / Redis (6379)。

### 2. 启动后端

```bash
cd backend
cp .env.example .env             # 按需修改
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

- API: <http://localhost:8000/api/v1>
- Swagger UI: <http://localhost:8000/api/docs>
- ReDoc: <http://localhost:8000/api/redoc>
- 健康检查: <http://localhost:8000/health>

### 3. 启动前端

```bash
cd frontend
cp .env.example .env.local        # 默认 VITE_API_TARGET=http://localhost:8000
npm install
npm run dev
```

前端开发服务器: <http://localhost:3000>（自动代理到后端 8000）

### 4. 跑测试

```bash
cd backend && pytest -v           # 110 tests, 0 dependencies required
```

---

## 📁 项目结构

```
/workspace
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/             # 路由聚合
│   │   ├── core/               # 基础设施（DB/Redis/security/异常/中间件/校验/日志）
│   │   ├── modules/            # 业务模块：auth / user / blog
│   │   ├── shared/             # 跨模块共享（常量/装饰器/工具/类型）
│   │   ├── config.py           # Pydantic Settings
│   │   └── main.py             # FastAPI 入口（lifespan + 中间件 + 路由）
│   ├── tests/                  # pytest 集成测试（110 用例）
│   ├── doc/                    # 后端文档（PRD/设计/API）
│   ├── .env.example
│   ├── pytest.ini
│   └── requirements.txt
│
├── frontend/                   # React + Vite 前端
│   ├── src/
│   │   ├── api/                # axios client + 端点常量 + 各模块 API
│   │   ├── pages/              # 页面（Login/Register/Dashboard/BlogList/...）
│   │   ├── router/             # 路由 + 守卫
│   │   ├── store/              # Zustand 全局状态（auth 等）
│   │   └── utils/              # 工具（错误处理/校验/安全/Markdown）
│   ├── doc/                    # 前端文档
│   └── package.json
│
├── docs/                       # 项目级文档
│   └── 开发实施计划.md           # 模块拆分与执行计划
│
├── docker-compose.yml          # 数据库编排
├── DEPLOYMENT.md               # 生产环境部署
└── README.md
```

---

## 🧪 测试

```bash
cd backend
pytest                              # 全部测试
pytest tests/test_auth.py -v        # 单文件
pytest -k change_password -v        # 关键字筛选
pytest --tb=short                   # 简短回溯
```

测试栈：**pytest 7 + pytest-asyncio + httpx + fakeredis + mongomock_motor + SQLite (in-memory) + bcrypt<4.1**

完整覆盖：auth (注册/登录/refresh/logout/change-password)、users (资料/头像/邮箱唯一性)、blog (CRUD/分页/缓存/软删除)、validators、security、rate_limit。

---

## 🔐 环境变量

后端 `backend/.env.example`（复制为 `.env` 后按需修改）：

| 变量 | 默认 | 说明 |
|---|---|---|
| `SECRET_KEY` | change-me | 应用密钥（生产必须改） |
| `JWT_SECRET_KEY` | change-me | JWT 签名密钥（生产必须改） |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | 30 | 普通 token 有效期 |
| `JWT_REMEMBER_ME_EXPIRE_MINUTES` | 10080 | 记住我有效期（7 天） |
| `RATE_LIMIT_LOGIN_PER_MIN` | 10 | 登录限流阈值 |
| `RATE_LIMIT_WRITE_PER_MIN` | 60 | 写操作限流阈值 |
| `AVATAR_MAX_SIZE_MB` | 2 | 头像最大 MB |
| `CORS_ORIGINS` | ["http://localhost:3000", ...] | 允许的跨域来源 |

前端 `frontend/.env.local`：

| 变量 | 默认 | 说明 |
|---|---|---|
| `VITE_API_TARGET` | http://localhost:8000 | 开发时后端地址（Vite proxy 转发到） |

---

## ❓ 常见问题 FAQ

**Q: 启动后端报 `ModuleNotFoundError: No module named 'pydantic_settings'`？**
A: 两种解法：① `pip install pydantic-settings`（推荐，与 Pydantic v1 兼容）；② 把 `config.py` 的 `from pydantic_settings import BaseSettings` 改为 `from pydantic import BaseSettings`（仅 Pydantic v1）。

**Q: `passlib` 报 `module 'bcrypt' has no attribute '__about__'`？**
A: passlib 1.7.4 与 bcrypt 4.x 不兼容。固定 `bcrypt<4.1`：`pip install 'bcrypt<4.1'`。`requirements.txt` 已注明但需手动 pin。

**Q: 跑测试报 `redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379`？**
A: 测试用 fakeredis，不应连真实 Redis。检查 `tests/conftest.py` 是否正确加载（pytest 需从 `backend/` 目录运行，pytest.ini 也在该目录）。

**Q: 注册时 `IntegrityError: UNIQUE constraint failed: users.email`？**
A: 邮箱已存在。换一个，或先 `docker-compose down -v` 清掉 PostgreSQL volume。

**Q: 前端代理不生效？**
A: 确认 `frontend/vite.config.js` 的 `server.proxy['/api']` 指向 `VITE_API_TARGET` 或默认 `http://localhost:8000`。`vite.config.js` 已设 `host: true`，外网/容器内访问无需额外配置。

**Q: 上传头像 413 Payload Too Large？**
A: 检查 `AVATAR_MAX_SIZE_MB`（默认 2MB）。同时检查 Nginx (`client_max_body_size`) / Gunicorn (`--limit-request-field_size`) 是否限制。

**Q: 登录后 `expires_in` 一直为 30？**
A: 前端登录时未传 `remember_me: true`。详见 [API 文档 — 认证接口](./backend/doc/API_Documentation.md)。

**Q: Swagger Authorize 用什么接口？**
A: `POST /api/v1/auth/login`（OAuth2 form 表单）。`remember_me` 通过 `scope` 字段传递，scope 包含 `remember_me` 字符串即开启。前端 JSON 登录走 `/api/v1/auth/login-json`。

**Q: 如何重置数据库？**
```bash
docker-compose down -v          # 删 volume（注意会清空所有数据）
docker-compose up -d
```

---

## 📦 部署到生产

详见 [DEPLOYMENT.md](./DEPLOYMENT.md)：Nginx + Gunicorn (UvicornWorker) + docker-compose.prod.yml。

---

## 📚 文档索引

| 文档 | 用途 |
|---|---|
| [docs/开发实施计划.md](./docs/开发实施计划.md) | 模块拆分、任务清单、接口契约 |
| [DEPLOYMENT.md](./DEPLOYMENT.md) | 生产环境部署指南 |
| [backend/doc/PRD.md](./backend/doc/PRD.md) | 后端产品需求 |
| [backend/doc/Backend_Design.md](./backend/doc/Backend_Design.md) | 后端设计 |
| [backend/doc/API_Documentation.md](./backend/doc/API_Documentation.md) | 后端 API 完整参考 |
| [frontend/doc/PRD.md](./frontend/doc/PRD.md) | 前端产品需求 |
| [frontend/doc/Frontend_Design.md](./frontend/doc/Frontend_Design.md) | 前端设计 |
| [frontend/doc/API_Documentation.md](./frontend/doc/API_Documentation.md) | 前端 API 速查（含 React Query 范例） |

---

## 🛠 技术栈

**后端**: Python 3.10 / FastAPI 0.95 / SQLAlchemy 2 / Pydantic 1.10 / Motor (MongoDB async) / redis-py / python-jose / passlib[bcrypt] / pytest

**前端**: React 18 / Vite 5 / React Router 6 / Zustand 4 / TanStack Query 5 / Axios 1.6 / react-markdown

**基础设施**: PostgreSQL 15 / MongoDB 7 / Redis 7

---

## 📜 许可

MIT
