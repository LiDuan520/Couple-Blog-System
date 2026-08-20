# 生产环境部署指南

> 本文档介绍如何把 **情侣博客系统** 部署到生产环境。
> 目标：Nginx 反向代理 + Gunicorn (UvicornWorker) + 静态资源分离 + Docker Compose 一键起。

---

## 0. 架构概览

```
                     ┌─────────────────┐
                     │     Nginx       │  :80 / :443
                     │  (TLS, gzip,    │
                     │  static files)  │
                     └────────┬────────┘
                              │ proxy_pass
                ┌─────────────┴──────────────┐
                │                            │
       /static/* │                            │ /api/*
                ▼                            ▼
   ┌──────────────────┐         ┌──────────────────────┐
   │  本地静态目录     │         │   Gunicorn           │
   │  (avatars, etc.) │         │   + UvicornWorker    │  :8000
   └──────────────────┘         │   (FastAPI 进程)     │
                                └────────┬─────────────┘
                                         │
                ┌────────────────────────┼────────────────────────┐
                ▼                        ▼                        ▼
        ┌──────────────┐         ┌──────────────┐         ┌──────────────┐
        │  PostgreSQL  │         │   MongoDB    │         │    Redis     │
        │     :5432    │         │    :27017    │         │    :6379     │
        └──────────────┘         └──────────────┘         └──────────────┘
```

**为什么这套组合？**

- **Nginx**：TLS 终止、gzip、静态资源托管、限流、隐藏真实端口
- **Gunicorn**：进程管理（多 worker 复用），比裸 Uvicorn 更稳
- **UvicornWorker**：Gunicorn 的 worker 类，保留 ASGI 异步性能
- **Docker Compose**：声明式编排，方便滚动升级和迁移

---

## 1. 前置条件

- Linux 服务器（Ubuntu 22.04+ / Debian 12+ / CentOS 9+）
- Docker 24+ 与 Docker Compose v2
- 一个域名（可选，演示用 IP 也行）
- 至少 1GB RAM / 1 vCPU（小流量）

```bash
docker --version        # Docker version 24+
docker compose version  # Docker Compose version v2+
```

---

## 2. 目录约定

```
/opt/couple-blog/
├── docker-compose.prod.yml      # 生产编排
├── .env.prod                    # 生产环境变量（不提交到 git）
├── nginx/
│   ├── nginx.conf               # 主配置
│   └── conf.d/
│       └── couple-blog.conf     # 站点配置
├── backend/
│   ├── Dockerfile
│   ├── app/                     # 代码
│   ├── requirements.txt
│   └── .env.prod
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   └── dist/                    # `npm run build` 产物
└── static/                      # 头像等上传文件（持久化 volume）
```

---

## 3. 准备生产环境变量

### `backend/.env.prod`

```env
APP_NAME=情侣博客
APP_VERSION=1.0.0
DEBUG=false
SECRET_KEY=<用 openssl rand -hex 32 生成>
JWT_SECRET_KEY=<用 openssl rand -hex 32 生成>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REMEMBER_ME_EXPIRE_MINUTES=10080

# 注意：生产数据库使用容器名/服务名作为 host
POSTGRES_USER=couple_blog
POSTGRES_PASSWORD=<强密码>
POSTGRES_DB=couple_blog
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

MONGODB_URL=mongodb://mongodb:27017
MONGODB_DB=couple_blog

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

RATE_LIMIT_LOGIN_PER_MIN=10
RATE_LIMIT_WRITE_PER_MIN=60
AVATAR_MAX_SIZE_MB=2

CORS_ORIGINS=["https://your-domain.com"]
```

### 生成强密钥

```bash
openssl rand -hex 32
```

把输出贴到 `SECRET_KEY` 和 `JWT_SECRET_KEY`（**两者必须不同**）。

---

## 4. 构建后端镜像

### `backend/Dockerfile`

```dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 系统依赖（psycopg2 / motor 需要 gcc 编译时）
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# 依赖
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install 'bcrypt<4.1' && \
    pip install -r requirements.txt

# 代码
COPY app ./app
COPY doc ./doc
COPY pytest.ini .
COPY tests ./tests

# 头像目录（挂载到 volume 持久化）
RUN mkdir -p /app/static/avatars

EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# 启动：Gunicorn + UvicornWorker
# 4 workers 起，可按 CPU 核数调
CMD ["gunicorn", "app.main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "60", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
```

### 构建并冒烟测试

```bash
cd backend
docker build -t couple-blog-backend:latest .
docker run --rm -p 8000:8000 --env-file .env.prod couple-blog-backend:latest
# 浏览器访问 http://localhost:8000/health 应返回 {"status":"healthy"}
```

---

## 5. 构建前端镜像

### `frontend/Dockerfile`（多阶段构建）

```dockerfile
# ---- Stage 1: 构建 ----
FROM node:20-alpine AS builder

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci

COPY . .
ARG VITE_API_TARGET=https://api.your-domain.com
ENV VITE_API_TARGET=$VITE_API_TARGET
RUN npm run build

# ---- Stage 2: nginx 静态托管 ----
FROM nginx:1.27-alpine

# 清空默认站点
RUN rm -rf /usr/share/nginx/html/*

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx-frontend.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD wget -q -O /dev/null http://localhost/ || exit 1
```

### `frontend/nginx-frontend.conf`

```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # SPA：所有未命中的路径都回退到 index.html（前端路由）
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 静态资源缓存
    location ~* \.(?:js|css|woff2?|ttf|otf|eot|ico|png|jpg|jpeg|gif|svg)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # gzip
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/javascript application/xml;
    gzip_min_length 1024;
}
```

### 构建

```bash
cd frontend
docker build -t couple-blog-frontend:latest \
  --build-arg VITE_API_TARGET=https://api.your-domain.com .
```

> 注意：构建时 `VITE_API_TARGET` 会**编译进 JS**。一旦镜像构建好，运行期无法再改。
> 演示用 `https://api.your-domain.com`，如果是 IP 部署可写 `http://<server-ip>`。

---

## 6. Nginx 反向代理配置

### `nginx/conf.d/couple-blog.conf`

```nginx
# ---- 后端 API ----
server {
    listen 80;
    server_name api.your-domain.com;

    # 文件上传大小（与 AVATAR_MAX_SIZE_MB 对齐，留点余量）
    client_max_body_size 10M;

    # 安全头（后端也加了一层，这里再加一道）
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # gzip
    gzip on;
    gzip_types application/json application/javascript text/css;
    gzip_min_length 1024;

    # 限流：每个 IP 每分钟 60 个请求到 /auth/login
    limit_req_zone $binary_remote_addr zone=login:10m rate=10r/m;
    location /api/v1/auth/login {
        limit_req zone=login burst=5 nodelay;
        proxy_pass http://backend:8000;
        include proxy_params;
    }

    # 全局代理
    location / {
        proxy_pass http://backend:8000;
        include proxy_params;
    }
}

# ---- 前端 ----
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location / {
        proxy_pass http://frontend:80;
        include proxy_params;
    }
}
```

### `nginx/proxy_params`（共用）

```nginx
proxy_http_version 1.1;
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header Connection "";

# WebSocket / SSE 用（如未来加入实时通知）
proxy_buffering off;
proxy_read_timeout 300s;
```

### `nginx/nginx.conf`（主配置，引用站点）

```nginx
worker_processes auto;
events { worker_connections 1024; }

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    sendfile      on;
    keepalive_timeout 65;

    include /etc/nginx/conf.d/*.conf;
}
```

---

## 7. 生产编排：`docker-compose.prod.yml`

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: couple_blog_postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - couple_blog_net

  mongodb:
    image: mongo:7
    container_name: couple_blog_mongodb
    restart: unless-stopped
    volumes:
      - mongodb_data:/data/db
    healthcheck:
      test: ["CMD", "mongosh", "--quiet", "--eval", "db.adminCommand('ping').ok"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - couple_blog_net

  redis:
    image: redis:7-alpine
    container_name: couple_blog_redis
    restart: unless-stopped
    command: ["redis-server", "--appendonly", "yes"]
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - couple_blog_net

  backend:
    image: couple-blog-backend:latest
    container_name: couple_blog_backend
    restart: unless-stopped
    env_file:
      - ./backend/.env.prod
    volumes:
      - ./static:/app/static
    depends_on:
      postgres:
        condition: service_healthy
      mongodb:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - couple_blog_net
    # 端口不直接暴露，由 nginx 代理
    expose:
      - "8000"

  frontend:
    image: couple-blog-frontend:latest
    container_name: couple_blog_frontend
    restart: unless-stopped
    depends_on:
      - backend
    networks:
      - couple_blog_net
    expose:
      - "80"

  nginx:
    image: nginx:1.27-alpine
    container_name: couple_blog_nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./nginx/proxy_params:/etc/nginx/proxy_params:ro
      - ./static:/usr/share/nginx/html/static:ro   # 让 /static/* 走 nginx
      - ./nginx/certs:/etc/nginx/certs:ro
    depends_on:
      - backend
      - frontend
    networks:
      - couple_blog_net

volumes:
  postgres_data:
  mongodb_data:
  redis_data:

networks:
  couple_blog_net:
    driver: bridge
```

> **重要**：Nginx 容器既代理 API (`api.your-domain.com`) 又代理前端 (`your-domain.com`)，所以 `frontend` 容器不需要对外暴露端口。如果前端想直连（不通过 nginx），再加一个 `ports: ["3000:80"]`。

---

## 8. 启动

```bash
# 1. 准备环境
cd /opt/couple-blog
cp backend/.env.example backend/.env.prod
# 编辑 .env.prod 填入生产值

# 2. 构建镜像
cd backend && docker build -t couple-blog-backend:latest . && cd ..
cd frontend && docker build -t couple-blog-frontend:latest . && cd ..

# 3. 启动所有服务
docker compose -f docker-compose.prod.yml --env-file backend/.env.prod up -d

# 4. 检查健康
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f backend
```

访问：

- 前端：<http://your-domain.com>
- 后端：<http://api.your-domain.com/api/docs>

---

## 9. HTTPS（Let's Encrypt）

### 9.1 申请证书

```bash
# 安装 certbot（宿主机或独立容器）
apt-get install -y certbot

# 80 端口必须可用（先停 nginx 或用 standalone）
certbot certonly --standalone -d your-domain.com -d api.your-domain.com
# 证书存到 /etc/letsencrypt/live/your-domain.com/
```

### 9.2 挂载到 Nginx

更新 `docker-compose.prod.yml` 的 nginx volumes：

```yaml
- /etc/letsencrypt:/etc/nginx/certs:ro
```

更新 `couple-blog.conf`：

```nginx
server {
    listen 443 ssl http2;
    server_name api.your-domain.com;

    ssl_certificate     /etc/nginx/certs/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/nginx/certs/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers on;

    # 其它配置同上 ...
}

# http -> https 跳转
server {
    listen 80;
    server_name your-domain.com api.your-domain.com;
    return 301 https://$host$request_uri;
}
```

### 9.3 自动续期

```bash
# 加入 crontab：每月检查续期
0 3 1 * * certbot renew --quiet && docker exec couple_blog_nginx nginx -s reload
```

---

## 10. 数据库迁移

MVP 阶段没有使用 Alembic（无 schema 变更）。后续要加迁移：

```bash
# 进入 backend 容器
docker exec -it couple_blog_backend bash

# 初始化（仅首次）
alembic init alembic

# 生成迁移
alembic revision --autogenerate -m "create users table"

# 应用迁移
alembic upgrade head
```

---

## 11. 备份与恢复

### PostgreSQL

```bash
# 备份
docker exec couple_blog_postgres pg_dump -U couple_blog couple_blog \
  > backup_$(date +%Y%m%d).sql

# 恢复
cat backup_20260101.sql | docker exec -i couple_blog_postgres psql -U couple_blog couple_blog
```

### MongoDB

```bash
# 备份
docker exec couple_blog_mongodb mongodump --db couple_blog --out /data/backup

# 恢复
docker exec couple_blog_mongodb mongorestore --db couple_blog /data/backup/couple_blog
```

### Redis

```bash
# 触发 AOF 持久化（已开启 appendonly）
docker exec couple_blog_redis redis-cli BGSAVE
# 备份 /var/lib/docker/volumes/.../_data/appendonly.aof
```

### 自动备份（cron）

```cron
0 2 * * * /opt/couple-blog/scripts/backup.sh
```

`scripts/backup.sh`：

```bash
#!/bin/bash
set -e
BACKUP_DIR=/opt/couple-blog/backups/$(date +%Y%m%d)
mkdir -p $BACKUP_DIR
docker exec couple_blog_postgres pg_dump -U couple_blog couple_blog > $BACKUP_DIR/pg.sql
docker exec couple_blog_mongodb mongodump --db couple_blog --out $BACKUP_DIR/mongo --quiet
tar czf $BACKUP_DIR.tar.gz -C $(dirname $BACKUP_DIR) $(basename $BACKUP_DIR)
rm -rf $BACKUP_DIR
# 保留最近 30 天
find /opt/couple-blog/backups -name "*.tar.gz" -mtime +30 -delete
```

---

## 12. 监控

### 12.1 健康检查端点

- 后端：`GET /health` → `{"status":"healthy"}`
- 前端：Nginx `wget -q -O /dev/null http://localhost/`
- 数据库：compose 的 `healthcheck` 配置

### 12.2 日志

```bash
# 实时日志
docker compose -f docker-compose.prod.yml logs -f --tail=100 backend

# 仅错误
docker compose -f docker-compose.prod.yml logs backend | grep ERROR
```

### 12.3 Prometheus 指标（可选）

在 `backend/app/main.py` 加 `prometheus-fastapi-instrumentator`：

```python
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)
```

然后在 `couple-blog.conf` 的 location `/metrics` 暴露给 Prometheus 抓取。

---

## 13. 性能调优

### 13.1 Gunicorn workers

经验值：`(2 × CPU) + 1`。4 核机器 → 9 workers。

```bash
# 启动时覆盖
docker compose -f docker-compose.prod.yml up -d \
  --scale backend=1 \
  # 或改 compose 的 command 参数
```

### 13.2 PostgreSQL

```sql
-- 看慢查询
SELECT * FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 10;

-- 加常用索引
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
```

### 13.3 MongoDB

```javascript
// 在 application 启动时加索引（已在 repository.py 实践）
db.blogs.createIndex({ author_id: 1, is_deleted: 1, created_at: -1 });
db.blogs.createIndex({ tags: 1 });
db.blogs.createIndex({ title: "text", content: "text" });
```

### 13.4 Redis 缓存

- 列表缓存 TTL：60s（写操作 invalidate）
- 黑名单 TTL：与 token 剩余有效期一致

---

## 14. 升级流程

```bash
# 1. 拉新代码
cd /opt/couple-blog && git pull

# 2. 重新构建
docker build -t couple-blog-backend:latest backend/
docker build -t couple-blog-frontend:latest frontend/

# 3. 滚动重启（零停机：先启新后端，再切流量）
docker compose -f docker-compose.prod.yml up -d backend
docker compose -f docker-compose.prod.yml up -d frontend
docker compose -f docker-compose.prod.yml up -d nginx

# 4. 验证
curl https://api.your-domain.com/health
```

---

## 15. 常见故障

| 症状 | 排查 |
|---|---|
| 502 Bad Gateway | 后端未就绪：`docker logs couple_blog_backend`；`docker exec couple_blog_backend curl localhost:8000/health` |
| 上传头像 413 | Nginx `client_max_body_size` 与后端 `AVATAR_MAX_SIZE_MB` 同时调大 |
| 跨域 CORS 报错 | 检查 `CORS_ORIGINS` 是否包含 `https://your-domain.com`（生产域名） |
| 静态头像 404 | 确认 `./static` 已挂载到 backend 的 `/app/static` 和 nginx 的 `/usr/share/nginx/html/static` |
| MongoDB 连不上 | `MONGODB_URL` 用容器名 `mongodb` 而非 `localhost`（在容器内 localhost 指容器自身） |
| JWT 401 但 token 正确 | `JWT_SECRET_KEY` 重启后被改了——所有 token 失效。生产务必固定密钥不轮换。 |
| 磁盘满 | `docker system df` 看占用；`docker system prune -a` 清理无用镜像 |

---

## 16. 安全清单

- [x] HTTPS（Let's Encrypt 自动续期）
- [x] `SECRET_KEY` / `JWT_SECRET_KEY` 至少 32 字节随机
- [x] `DEBUG=false`
- [x] 数据库密码 ≥ 16 字符
- [x] Nginx 安全头（X-Frame-Options / CSP / X-Content-Type-Options）
- [x] 限流（login 10r/m，全局已 60r/m）
- [x] 输入校验（白名单 + SQL/XSS 关键字过滤）
- [x] bcrypt 密码哈希（cost=12）
- [x] JWT 黑名单（Redis）
- [x] 审计日志（auth.login / auth.change_password / 等）
- [x] 依赖定期升级（`pip-audit` / `npm audit`）

---

## 17. 卸载

```bash
# 停服务并删容器、网络
docker compose -f docker-compose.prod.yml down

# 删数据卷（⚠️ 会清空所有数据）
docker compose -f docker-compose.prod.yml down -v
```

---

**文档版本**: v1.0  
**最后更新**: 2026-08-20
