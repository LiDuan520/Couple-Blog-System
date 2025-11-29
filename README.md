# 情侣博客系统 (Couple Blog System)

一个专为情侣设计的私密博客平台，支持记录文字、图片、时间轴等多种形式的内容。

## 项目简介

本项目采用前后端分离架构，模块化设计，便于后续扩展为微服务架构。

### 技术栈

**后端**:
- Python 3.10+
- FastAPI 0.104+
- PostgreSQL 15+
- MongoDB 7+
- Redis 7+

**前端**:
- React 18+
- Vite 5+
- Zustand 4+
- React Query 5+
- Axios 1.6+

## 项目结构

```
cp/
├── backend/              # 后端项目
│   ├── app/             # 应用代码
│   ├── doc/             # 后端文档
│   ├── tests/           # 测试
│   └── requirements.txt # Python 依赖
│
├── frontend/             # 前端项目
│   ├── src/             # 源代码
│   ├── doc/             # 前端文档
│   └── package.json    # Node 依赖
│
├── docker-compose.yml   # Docker 编排
└── README.md           # 项目说明
```

## 快速开始

### 前置要求

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- Git

### 1. 克隆项目

```bash
git clone <repository-url>
cd cp
```

### 2. 启动数据库服务

```bash
docker-compose up -d
```

### 3. 后端设置

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置数据库连接等信息

# 运行数据库迁移（待实现）
# alembic upgrade head

# 启动后端服务
uvicorn app.main:app --reload --port 8000
```

### 4. 前端设置

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 5. 访问应用

- 前端: http://localhost:3000
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/api/docs

## 开发文档

### 后端文档

- [产品需求文档](./backend/doc/PRD.md)
- [API 接口文档](./backend/doc/API_Documentation.md)
- [后端设计文档](./backend/doc/Backend_Design.md)

### 前端文档

- [产品需求文档](./frontend/doc/PRD.md)
- [API 接口文档](./frontend/doc/API_Documentation.md)
- [前端设计文档](./frontend/doc/Frontend_Design.md)

## 开发规范

### 代码规范

- Python: PEP 8, Black
- JavaScript: ESLint + Prettier
- Git: Conventional Commits

### 分支管理

- `main`: 主分支，生产环境代码
- `develop`: 开发分支
- `feature/*`: 功能分支
- `fix/*`: 修复分支

## 测试

### 后端测试

```bash
cd backend
pytest
```

### 前端测试

```bash
cd frontend
npm test
```

## 部署

### 开发环境

使用 Docker Compose 启动所有服务：

```bash
docker-compose up -d
```

### 生产环境

参考各模块的部署文档。

## 贡献指南

1. Fork 本项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

本项目采用 MIT 许可证。

## 联系方式

如有问题或建议，请提交 Issue 或联系项目维护者。

---

**项目状态**: 🚧 开发中
**版本**: v1.0.0

