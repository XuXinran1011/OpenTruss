# OpenTruss 部署文档

## 1. 概述

本文档提供 OpenTruss 系统的生产环境部署指南，包括 Docker 部署、环境配置和监控设置。

---

## 2. 生产环境要求

### 2.1 硬件要求

| 组件 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | 4 核 | 8 核+ |
| 内存 | 16GB | 32GB+ |
| 磁盘 | 100GB SSD | 500GB+ SSD |
| 网络 | 100Mbps | 1Gbps+ |

### 2.2 软件要求

- **操作系统**: Ubuntu 22.04 LTS / CentOS 8+
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Nginx**: 1.20+ (反向代理)

---

## 3. Docker 部署

### 3.1 Docker Compose 配置

创建 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  memgraph:
    image: memgraph/memgraph:latest
    container_name: opentruss-memgraph
    ports:
      - "7687:7687"
      - "7444:7444"
    volumes:
      - memgraph_data:/var/lib/memgraph
      - memgraph_logs:/var/log/memgraph
    environment:
      - MEMGRAPH_LOG_LEVEL=INFO
    restart: unless-stopped
    # 资源限制
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G
    healthcheck:
      test: ["CMD", "mg_client", "--host", "localhost", "--port", "7687", "--execute", "RETURN 1"]
      interval: 10s
      timeout: 5s
      start_period: 10s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: opentruss-backend
    ports:
      - "8000:8000"
    environment:
      - MEMGRAPH_HOST=memgraph
      - MEMGRAPH_PORT=7687
      - API_DEBUG=False
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    depends_on:
      memgraph:
        condition: service_healthy
    restart: unless-stopped
    volumes:
      - ./backend:/app
      - backend_logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: opentruss-frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_BASE_URL=${API_BASE_URL}
    depends_on:
      - backend
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    container_name: opentruss-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - backend
      - frontend
    restart: unless-stopped

volumes:
  memgraph_data:
  memgraph_logs:
  backend_logs:
```

### 3.2 后端 Dockerfile

`backend/Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# 创建非 root 用户
RUN groupadd -r opentruss && useradd -r -g opentruss opentruss

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建日志目录并设置权限
RUN mkdir -p /app/logs && chown -R opentruss:opentruss /app

# 切换到非 root 用户
USER opentruss

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3.3 前端 Dockerfile

`frontend/Dockerfile`:

```dockerfile
# 构建阶段
FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# 生产阶段
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

---

## 4. 环境变量配置

### 4.1 后端环境变量

创建 `.env.production`:

```env
# 数据库配置
MEMGRAPH_HOST=memgraph
MEMGRAPH_PORT=7687
MEMGRAPH_USER=admin
MEMGRAPH_PASSWORD=your-secure-password

# API 配置
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=False
API_CORS_ORIGINS=https://opentruss.com

# JWT 配置
JWT_SECRET_KEY=your-very-secure-secret-key-min-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRATION=3600

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=/app/logs/opentruss.log

# 其他配置
ENVIRONMENT=production
```

### 4.2 前端环境变量

创建 `frontend/.env.production`:

```env
NEXT_PUBLIC_API_BASE_URL=https://api.opentruss.com/api/v1
NEXT_PUBLIC_WS_URL=wss://api.opentruss.com/ws
```

---

## 5. Nginx 配置

### 5.1 Nginx 主配置

`nginx/nginx.conf`:

```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Gzip 压缩
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript 
               application/json application/javascript application/xml+rss;

    # 上游服务器
    upstream backend {
        server backend:8000;
    }

        upstream frontend {
        server frontend:3000;
    }

    # HTTP 服务器（重定向到 HTTPS）
    server {
        listen 80;
        server_name opentruss.com www.opentruss.com;
        return 301 https://$server_name$request_uri;
    }

    # HTTPS 服务器
    server {
        listen 443 ssl http2;
        server_name opentruss.com www.opentruss.com;

        # SSL 证书
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        # API 代理
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # WebSocket 代理
        location /ws/ {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
        }

        # 前端静态文件
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
    }
}
```

---

## 6. Memgraph 持久化配置

### 6.1 数据持久化

Memgraph 数据存储在 Docker Volume 中：

```bash
# 查看 Volume
docker volume ls | grep memgraph

# 备份数据
docker run --rm -v opentruss_memgraph_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/memgraph-backup-$(date +%Y%m%d).tar.gz /data
```

### 6.2 持久化配置

在 `docker-compose.yml` 中已配置 Volume 挂载，确保数据持久化。

---

## 7. SSL/TLS 配置

### 7.1 获取 SSL 证书

**使用 Let's Encrypt**:

```bash
# 安装 Certbot
sudo apt-get install certbot

# 获取证书
sudo certbot certonly --standalone -d opentruss.com -d www.opentruss.com
```

### 7.2 配置证书

将证书文件复制到 `nginx/ssl/` 目录：

```bash
cp /etc/letsencrypt/live/opentruss.com/fullchain.pem nginx/ssl/cert.pem
cp /etc/letsencrypt/live/opentruss.com/privkey.pem nginx/ssl/key.pem
```

---

## 8. 监控配置

### 8.1 Prometheus 配置

创建 `monitoring/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'opentruss-backend'
    static_configs:
      - targets: ['backend:8000']
  
  - job_name: 'opentruss-memgraph'
    static_configs:
      - targets: ['memgraph:7444']
```

### 8.2 Grafana 配置

- 数据源: Prometheus
- 仪表板: 自定义 OpenTruss 监控面板

### 8.3 健康检查端点

后端提供健康检查端点：

```python
# app/api/health.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "healthy"}
```

---

## 9. 日志配置

### 9.1 日志收集

使用 ELK Stack 或 Loki 收集日志：

**Docker Compose 添加 Loki**:

```yaml
  loki:
    image: grafana/loki:latest
    volumes:
      - loki_data:/loki
    command: -config.file=/etc/loki/local-config.yaml

  promtail:
    image: grafana/promtail:latest
    volumes:
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - ./monitoring/promtail-config.yml:/etc/promtail/config.yml
    command: -config.file=/etc/promtail/config.yml
```

### 9.2 日志格式

使用结构化日志（JSON 格式）：

```python
import logging
import json

logger = logging.getLogger(__name__)

def log_request(request_id: str, method: str, path: str):
    logger.info(json.dumps({
        "request_id": request_id,
        "method": method,
        "path": path,
        "level": "info"
    }))
```

---

## 10. 部署流程

### 10.1 首次部署

```bash
# 1. 克隆代码
git clone https://github.com/your-org/opentruss.git
cd opentruss

# 2. 配置环境变量
cp .env.example .env.production
# 编辑 .env.production

# 3. 构建镜像
docker-compose build

# 4. 启动服务
docker-compose up -d

# 5. 初始化数据库
docker-compose exec backend python scripts/init_schema.py

# 6. 验证部署
curl http://localhost/health
```

### 10.2 更新部署

```bash
# 1. 拉取最新代码
git pull

# 2. 重新构建
docker-compose build

# 3. 滚动更新
docker-compose up -d --no-deps backend frontend

# 4. 验证更新
docker-compose logs -f backend
```

### 10.3 回滚

```bash
# 回滚到上一个版本
git checkout <previous-commit>
docker-compose build
docker-compose up -d
```

---

## 11. 备份与恢复

### 11.1 数据备份

**自动备份脚本** (`scripts/backup.sh`):

```bash
#!/bin/bash
BACKUP_DIR="/backup/opentruss"
DATE=$(date +%Y%m%d_%H%M%S)

# 备份 Memgraph 数据
docker run --rm -v opentruss_memgraph_data:/data -v $BACKUP_DIR:/backup \
  alpine tar czf /backup/memgraph-$DATE.tar.gz /data

# 备份配置文件
tar czf $BACKUP_DIR/config-$DATE.tar.gz .env.production nginx/

# 清理旧备份（保留 30 天）
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

**定时任务** (Crontab):

```bash
# 每天凌晨 2 点备份
0 2 * * * /path/to/scripts/backup.sh
```

### 11.2 数据恢复

```bash
# 停止服务
docker-compose down

# 恢复 Memgraph 数据
docker run --rm -v opentruss_memgraph_data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/memgraph-20240101_020000.tar.gz -C /

# 启动服务
docker-compose up -d
```

---

## 12. 安全配置

### 12.1 防火墙规则

```bash
# 只开放必要端口
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 12.2 Docker 安全

- 使用非 root 用户运行容器
- 限制容器资源
- 定期更新镜像

### 12.3 密钥管理

- 使用环境变量或密钥管理服务（如 Vault）
- 不在代码中硬编码密钥
- 定期轮换密钥

---

## 13. 性能优化

### 13.1 数据库优化

- 创建必要的索引
- 优化 Cypher 查询
- 使用连接池

### 13.2 应用优化

- 启用 Gzip 压缩
- 使用 CDN 加速静态资源
- 启用 HTTP/2

### 13.3 缓存策略

- 使用 Redis 缓存热点数据
- 设置合理的 TTL
- 缓存失效策略

---

**最后更新**：2025-12-28  
**文档版本**：1.0  
**维护者**：OpenTruss 开发团队

