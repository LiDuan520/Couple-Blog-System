# AGENTS.md

> 适用于本仓库（情侣博客 / 恋爱平台 v2）的 AI 代理协作规范。任何 AI/自动化代理（Claude、Codex、内部脚本等）在编写、修改或评审本项目代码前，请先阅读本文件。

---

## 1. 项目概览

- **名称**：情侣博客系统（Couple Blog System）
- **当前版本**：v2.0（恋爱平台改造，已完成 M-10 ~ M-14）
- **目标**：为情侣提供一个私密的内容记录平台 —— 文字博客、纪念日、相册、聚合时间轴、伴侣绑定、恋爱天数统计。
- **架构形态**：单体仓库（backend + frontend + docs + docker-compose）。

### v1 / v2 兼容边界

- **v1**：用户 / 博客（author 维度缓存）。
- **v2**：在 v1 之上叠加 couple / anniversary / album / timeline / dashboard（couple 维度缓存 + v1 author 维度缓存并存）。
- **规则**：v1 路径必须保留可用；v2 新字段（`Blog.couple_id` / `User.couple_id`）一律 **可空**，不得硬改成 NOT NULL。

---

## 2. 目录结构（关键节点）

```
/workspace
├── AGENTS.md                      ← 本文件
├── README.md                      ← 用户面向的快速上手
├── DEPLOYMENT.md                  ← 生产部署（Nginx + Gunicorn + Docker Compose）
├── docker-compose.yml             ← PostgreSQL / MongoDB / Redis
├── docs/                          ← 跨端顶层文档
│   ├── PRD_v2_恋爱平台.md
│   ├── 开发实施计划.md            ← M-10 ~ M-15 拆分
│   └── 技术设计_恋爱平台改造.md   ← 主参考
│
├── backend/                       ← FastAPI 后端
│   ├── app/
│   │   ├── main.py                ← 入口（注册全局 handler、lifespan、StaticFiles）
│   │   ├── config.py              ← Pydantic Settings
│   │   ├── api/v1/router.py       ← 聚合 8 个模块的路由
│   │   ├── core/                  ← 基础设施
│   │   │   ├── cache.py           ← invalidate_couple_caches（统一缓存失效）
│   │   │   ├── database.py        ← SQLAlchemy 2.0 session
│   │   │   ├── redis_client.py    ← 缓存 + 黑名单 + 限流
│   │   │   ├── exceptions.py      ← BaseAPIException 体系
│   │   │   ├── middleware.py      ← 请求日志 / 安全响应头
│   │   │   ├── security.py        ← JWT + bcrypt
│   │   │   ├── logging_config.py  ← 结构化日志 + audit_log
│   │   │   └── validators.py
│   │   ├── modules/               ← 业务模块（每个都遵循 router/service/repository 3 层）
│   │   │   ├── auth/  user/  blog/                ← v1
│   │   │   └── couple/ anniversary/ album/
│   │   │       timeline/ dashboard/               ← v2
│   │   └── shared/                ← constants / decorators / types / utils
│   ├── tests/                     ← pytest（conftest 全局 patch fakeredis + mongomock）
│   ├── requirements.txt
│   ├── pytest.ini
│   ├── doc/                       ← Backend_Design / PRD / API 文档
│   └── static/photos/             ← 用户上传图片（按 couple_id 子目录）
│
└── frontend/                      ← React + Vite 前端
    ├── package.json
    ├── vite.config.js
    ├── .eslintrc.js
    ├── src/
    │   ├── main.jsx               ← ChakraProvider + theme
    │   ├── App.jsx
    │   ├── router/index.jsx       ← AppLayout + 受保护路由
    │   ├── api/                   ← Axios 客户端 + 各模块 endpoints
    │   ├── store/                 ← Zustand（authStore 已扩展 couple 字段）
    │   ├── styles/theme.js        ← Chakra UI 粉紫少女主题
    │   ├── components/            ← layout / common
    │   ├── pages/                 ← Dashboard / Couple / Anniversaries / Albums / Timeline / Blog* / Login / Register / Profile
    │   └── utils/                 ← validation / errorHandler / markdown 等
    └── doc/                       ← Frontend_Design / PRD / API 文档
```

---

## 3. 技术栈速览

### 后端

| 领域 | 选型 |
|---|---|
| 语言 | Python 3.10+ |
| Web 框架 | FastAPI 0.95+ |
| ORM | SQLAlchemy 2.0 风格（`select()` / `Session.execute`） |
| 校验 | Pydantic 1.10（已为 v2 兼容做准备，但不要在本次升级中切到 v2） |
| 关系库 | PostgreSQL 15 |
| 文档库 | MongoDB 7（Motor 异步驱动） |
| 缓存 / 黑名单 / 限流 | Redis 7（redis-py） |
| 测试 | pytest + fakeredis + mongomock_motor + SQLite in-memory |

### 前端

| 领域 | 选型 |
|---|---|
| 语言 | JavaScript（.jsx，无 TypeScript） |
| 框架 | React 18 + Vite 5 |
| 路由 | React Router 6 |
| 状态 | Zustand 4（不要引入 Redux / MobX） |
| 数据请求 | TanStack Query 5 |
| HTTP | Axios 1.6 |
| UI 库 | Chakra UI 2.10 + Emotion + Framer Motion |
| 图标 | react-icons |
| 日期 | dayjs |
| Markdown | react-markdown + remark-gfm |

---

## 4. 关键命令

### 开发环境启动

```bash
# 1) 启动数据库
docker-compose up -d

# 2) 后端
cd backend
cp .env.example .env
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 3) 前端
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

### 测试与检查

```bash
# 后端
cd backend
pytest -v                    # 跑全部测试（约 168 用例）
pytest tests/test_couple.py  # 单模块

# 前端
cd frontend
npm run lint                 # ESLint
npm run build                # 产物构建
```

### 部署

详见 [DEPLOYMENT.md](./DEPLOYMENT.md)。

---

## 5. 架构约定

### 5.1 后端分层

每个业务模块严格保持 **router / service / repository** 三层：

```
modules/<name>/
├── router.py        ← FastAPI 路由（参数解析、依赖注入、调用 service）
├── service.py       ← 业务逻辑（事务边界在这里）
├── repository.py    ← SQLAlchemy / Motor 数据访问
├── models.py        ← ORM / 文档模型
├── schemas.py       ← Pydantic 请求 / 响应模型
└── dependencies.py  ← 模块级 Depends（可选）
```

- **不在 router 里直接 query DB**。
- **不在 service 里直接构造 Response**，统一由 `*Response` schema 拼装。
- **跨模块 schema 引用** 若出现 Pydantic 循环引用，参考 `backend/app/modules/auth/schemas.py` 里的 `_CoupleBriefForAuth` 私有局部解法。

### 5.2 前端分层

- **路由**：`src/router/index.jsx` — 所有受保护页面用 `AppLayout` 包裹。
- **API**：`src/api/modules/` — 每个后端模块一个文件，按 `endpoints.js` 取路径常量。
- **状态**：Zustand store 在 `src/store/`；**服务器态**走 TanStack Query，**客户端态**走 Zustand。
- **UI**：用 Chakra UI 组件 + `styles/theme.js` 主题，不要新加内联 style（颜色/圆角/阴影一律走 token）。

### 5.3 缓存键规范

| 用途 | 模式 | 示例 |
|---|---|---|
| 博客列表（v1 author） | `cache:blog:list:<author_id>:<sig>` | `cache:blog:list:42:7e3` |
| 博客列表（v2 couple） | `cache:blog:list:couple:<couple_id>:<sig>` | `cache:blog:list:couple:3:7e3` |
| 时间轴 | `cache:timeline:couple:<couple_id>:<sig>` | — |
| 仪表盘 | `cache:dashboard:couple:<couple_id>:<sig>` | — |

**失效统一入口**：`app/core/cache.py` → `invalidate_couple_caches(couple_id, patterns, author_ids)`。任何写操作后必须调用它；**不要手动 `r.delete` 散弹式清缓存**。

### 5.4 异常体系

业务异常一律继承 `BaseAPIException`（`app/core/exceptions.py`），由全局 handler 统一返回：

```json
{ "error": { "code": "COUPLE_ALREADY_BOUND", "message": "..." } }
```

不要在路由里手写 `HTTPException`，也不要让原始异常直接冒泡。

---

## 6. AI 代理工作准则

### 6.1 修改前必读

1. 先通读被改动文件，再下结论。**禁止**基于文件名猜测行为。
2. 涉及 v1/v2 兼容的字段（`Blog.couple_id`、`User.couple_id`、`cache:blog:list:*` 键空间）必须先看 `docs/技术设计_恋爱平台改造.md` 中对应的 M 阶段，再动手。
3. 修改 Pydantic schema 后，**必须跑一遍相关模块的 pytest** 再提交。

### 6.2 修改后必做

- 后端改动：`cd backend && pytest -v tests/test_<module>.py`（受影响模块 + 安全 + 限流相关）。
- 前端改动：`cd frontend && npm run lint`，必要时 `npm run build` 验证产物可构建。
- 写操作涉及缓存：检查是否已调用 `invalidate_couple_caches`，并在测试里加一条 `fakeredis` 断言。

### 6.3 禁止事项

| 禁止 | 原因 |
|---|---|
| 把 `Blog.couple_id` / `User.couple_id` 改成 NOT NULL | 会破坏 v1 数据 |
| 新增 `requirements.txt` / `package.json` 依赖**未与用户确认** | 体积膨胀、安全审计成本 |
| 引入 TypeScript / Redux / 其它 UI 库（MUI / Ant Design） | 与现有栈冲突 |
| 把 bcrypt 升级到 ≥ 4.1 而不动 `requirements.txt` | 已 pin `<4.1`，无明确动机不动 |
| 在 `router.py` 里直接 query ORM | 破坏分层 |
| 用内联 hex 颜色 / 硬编码 spacing | 必须走 Chakra theme token |
| 在测试里连真实 PostgreSQL / MongoDB / Redis | 必须 fakeredis / mongomock / SQLite |

### 6.4 命名 / 风格

- **后端**：模块名小写单数（`couple` 而非 `couples`），类名 PascalCase，函数 snake_case。
- **前端**：`pages/<Page>/<Page>.jsx`，组件 PascalCase，工具函数 camelCase。
- **提交信息**：遵循 Conventional Commits（见第 8 节）。M 阶段工作提交前缀用 Mxx（如 `M14:`）。

### 6.5 Pydantic 循环引用常见解法

新增跨模块 Pydantic 引用时若触发循环：

```python
class _CoupleBriefForAuth(BaseModel):
    id: int
    nickname: Optional[str] = None

class UserResponse(BaseModel):
    couple: Optional["_CoupleBriefForAuth"] = None
```

参考 `backend/app/modules/auth/schemas.py`。

### 6.6 文件位置

- **新模块** → `backend/app/modules/<name>/{router,service,repository,models,schemas}.py`。
- **新页面** → `frontend/src/pages/<PageName>/<PageName>.jsx`，并在 `router/index.jsx` 注册。
- **新 API** → `frontend/src/api/modules/<name>.api.js` + 在 `endpoints.js` 加路径常量。
- **新文档** → 默认放进 `docs/`、`backend/doc/` 或 `frontend/doc/`，不要在根目录散落。

---

## 7. 常见陷阱

1. **fakeredis / mongomock_motor 必须在 `import app` 之前 patch**。已在 `tests/conftest.py` 处理，新测试不要绕过它。
2. **事务隔离**：pytest 的 `db` fixture 用 `connection.begin() + rollback`，写完测试无需手动回滚；跨测试不能共享 DB 状态。
3. **Couple 顺序**：`user_a_id < user_b_id` 由 `CheckConstraint` 强制；不要在代码里手动排序，靠 DB 报错兜底。
4. **邀请码生成**：用 `secrets.choice(alphabet)`，alphabet 必须去除 `0O1IL` 这些易混字符，长度 8。
5. **静态文件**：用户上传的照片落到 `backend/static/photos/couple_<id>/`，删除 photo 时记得级联清文件。
6. **前端构建产物偏大**：Chakra + emotion 体积偏重（gzip ≈ 239KB），属可接受范围，**不要**因为这个切到更轻的库。
7. **移动端布局**：用 Chakra 的 `useBreakpointValue` 或响应式 prop（`base` / `md`），不要写死 px。

---

## 8. Git 使用标准

### 8.1 分支策略

```
main           ← 生产稳定分支（只接受来自 develop 的 PR，不允许直接 push）
develop        ← 集成分支（所有功能分支 merge 到此）
feat/<name>    ← 新功能分支（从 develop 切出）
fix/<name>     ← 缺陷修复分支（从 develop 切出）
docs/<name>    ← 纯文档分支（从 develop 切出）
chore/<name>   ← 构建 / 依赖 / 配置变更分支（从 develop 切出）
```

- **所有工作分支**（包括 AI 代理创建的分支）必须以 `feat/` `fix/` `docs/` `chore/` 之一为前缀；**禁止**使用 `trae/`、`agent/`、`agents/` 等非标准前缀。
- **所有分支**均从 `develop` 创建；**禁止**直接往 `main` 推代码。
- 完成后通过 PR → `develop`，经过 CI 检查后合并。

### 8.2 Commit Message 规范

遵循 **Conventional Commits**（https://www.conventionalcommits.org）。

**格式**

```
<type>(<scope>): <subject>

[可选 body]

[可选 footer]
```

**type 枚举**

| type | 适用场景 |
|---|---|
| `feat` | 新增功能 |
| `fix` | 缺陷修复 |
| `refactor` | 重构（不改变外部行为） |
| `test` | 新增 / 修改测试 |
| `docs` | 文档变更 |
| `chore` | 构建脚本 / 依赖 / 工具链 |
| `style` | 仅格式变更（空格、换行，无逻辑改动） |
| `perf` | 性能优化 |
| `ci` | CI/CD 配置变更 |

**scope 约定（本项目）**

| scope | 对应位置 |
|---|---|
| `auth` | backend/modules/auth |
| `couple` | backend/modules/couple |
| `anniversary` | backend/modules/anniversary |
| `album` | backend/modules/album |
| `timeline` | backend/modules/timeline |
| `dashboard` | backend/modules/dashboard |
| `blog` | backend/modules/blog |
| `user` | backend/modules/user |
| `core` | backend/app/core |
| `ui` | frontend/src/components 或 styles |
| `page` | frontend/src/pages |
| `store` | frontend/src/store |
| `api` | frontend/src/api |
| `infra` | docker-compose / nginx / deployment |

**里程碑阶段提交**：在 subject 前加 `Mxx:` 标记，方便追溯。

```
feat(couple): M11: 邀请码生成与接受绑定接口
fix(timeline): M12: 修复里程碑日期计算差 1 天
```

**示例**

```bash
feat(album): 支持批量上传照片并返回失败列表
fix(auth): 修复登出时 token 未加入 Redis 黑名单
refactor(core): 提取 invalidate_couple_caches 统一缓存失效
test(couple): 补充邀请码过期场景用例
docs: 新增 AGENTS.md 并补充 Git 使用标准
```

### 8.3 提交前检查清单

在执行 `git commit` 前，确认以下项目全部通过：

```bash
# 后端（有改动时）
cd backend && pytest -v

# 前端（有改动时）
cd frontend && npm run lint && npm run build
```

**AI 代理规则**：未通过上述检查的代码**不得提交**；若测试失败，须先修复再 commit。

### 8.4 PR / Merge 规范

- PR 标题格式与 commit message 相同：`<type>(<scope>): <subject>`。
- PR body 需包含：**变更摘要**、**测试情况**（已跑的命令 + 结果）、**破坏性变更**（若有）。
- **Squash merge** 到 develop（保持线性历史），不使用 merge commit。
- 合并后删除工作分支。

### 8.5 .gitignore 注意事项

以下内容已在 `.gitignore` 中，**禁止**强制提交：

- `backend/venv/`、`backend/.env`（含密钥）
- `frontend/node_modules/`、`frontend/dist/`
- `backend/static/photos/`（用户上传图片，不入库）
- `**/__pycache__/`、`**/*.pyc`

### 8.6 禁止事项

| 禁止 | 原因 |
|---|---|
| `git push --force` 到 `main` / `develop` | 会覆盖他人工作 |
| 提交 `.env` / 密钥 / token | 安全风险 |
| 提交 `static/photos/` 中的用户图片 | 隐私 + 仓库体积 |
| 一次 commit 混入多个无关变更 | 难以 review 和回滚 |
| commit message 使用随意描述（如 `fix bug`、`update`、`查看项目情况`） | 无法追溯意图 |
| 分支名以 `trae/`、`agent/`、`agents/` 开头 | 不符合本项目分支命名规范 |

---

## 9. 参考文档

按需阅读，避免重复造轮子：

- [README.md](./README.md) — 项目概览 / 快速上手 / FAQ
- [DEPLOYMENT.md](./DEPLOYMENT.md) — 生产部署（Nginx + Gunicorn + Docker）
- [docs/技术设计_恋爱平台改造.md](./docs/技术设计_恋爱平台改造.md) — v2 改造主设计（M-10 ~ M-15）
- [docs/PRD_v2_恋爱平台.md](./docs/PRD_v2_恋爱平台.md) — 产品需求
- [docs/开发实施计划.md](./docs/开发实施计划.md) — 里程碑拆分
- [backend/doc/Backend_Design.md](./backend/doc/Backend_Design.md) — 后端架构
- [backend/doc/API_Documentation.md](./backend/doc/API_Documentation.md) — 后端 API
- [frontend/doc/Frontend_Design.md](./frontend/doc/Frontend_Design.md) — 前端设计
- [frontend/doc/API_Documentation.md](./frontend/doc/API_Documentation.md) — 前端 API 调用约定

---

## 10. 一句话准则

> **保持分层、保持兼容、保持简洁。任何修改都先跑测试，任何不熟悉的代码先读再改。**
