---
name: opentruss-development
description: OpenTruss 项目开发工作流、环境搭建和常用操作指南
---

# OpenTruss 开发工作流技能

当你需要设置开发环境、运行测试或执行常见开发任务时，参考本技能。

## 环境要求

### 系统要求
- **操作系统**: Windows 10/11, macOS 10.15+, Linux (Ubuntu 20.04+)
- **内存**: 最低 8GB，推荐 16GB+
- **磁盘空间**: 最低 10GB 可用空间

### 必需软件
- **Python**: 3.10+
- **Node.js**: 18.0+
- **Docker**: 20.10+ (可选)
- **Git**: 2.30+

## 快速开始

### 1. 克隆仓库
```bash
git clone https://github.com/your-org/opentruss.git
cd opentruss
```

### 2. 后端设置
```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3. 前端设置
```bash
cd frontend
npm install

# 配置前端环境变量
cp .env.example .env.local
# 编辑 .env.local，设置 NEXT_PUBLIC_API_URL
```

### 4. 启动 Memgraph
```bash
docker run -it -p 7687:7687 memgraph/memgraph
```

### 5. 启动服务

**使用 Makefile（推荐）**:
```bash
make dev  # 启动所有服务
```

**手动启动**:
```bash
# 终端 1 - 后端
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# 终端 2 - 前端
cd frontend
npm run dev
```

### 6. 验证启动
- **后端 API**: http://localhost:8000/docs (Swagger UI)
- **前端应用**: http://localhost:3000
- **Memgraph**: localhost:7687

## 开发工作流

### 后端开发

**创建新功能分支**:
```bash
git checkout -b feature/your-feature
```

**运行测试**:
```bash
cd backend
pytest
pytest tests/test_api/test_approval.py -v  # 运行特定测试
```

**代码格式化**:
```bash
black .
isort .
```

**提交代码**:
```bash
git add .
git commit -m "feat: your feature description"
```

### 前端开发

**生成/更新 TypeScript API**:
```bash
# 确保后端服务运行
python scripts/verify_openapi_schema.py
# Windows PowerShell
.\scripts\generate_typescript_api.ps1
# Linux/macOS
./scripts/generate_typescript_api.sh
```

**运行开发服务器**:
```bash
npm run dev
```

**代码检查**:
```bash
npm run lint
npm run format
```

**运行测试**:
```bash
npm test
npm run test:e2e  # E2E 测试
```

## API 开发流程

1. **定义 Pydantic 模型** (在 `backend/app/models/` 中)
2. **创建 API 端点** (在 `backend/app/api/v1/` 中)
3. **验证 OpenAPI schema**:
   ```bash
   python scripts/verify_openapi_schema.py
   ```
4. **生成 TypeScript 客户端**:
   ```bash
   npm run generate-api
   ```
5. **在前端使用生成的 API 客户端**

## 测试策略

### 后端测试

**单元测试**:
```bash
cd backend
pytest tests/test_services/
```

**API 测试**:
```bash
pytest tests/test_api/
```

**集成测试**:
```bash
pytest tests/test_integration/
```

**性能测试**:
```bash
# Locust
python scripts/run-locust-tests.sh

# k6
./scripts/run-k6-tests.sh
```

### 前端测试

**单元测试**:
```bash
cd frontend
npm test
```

**E2E 测试**:
```bash
npm run test:e2e
```

## 代码生成

### Speckle 模型（Python Pydantic）

如果 Speckle 更新了 BuiltElements 定义，可以重新生成：

```bash
# 1. 从 GitHub 获取最新的 Speckle .cs 文件
python scripts/fetch_speckle_built_elements.py

# 2. 转换为 Pydantic 模型
python scripts/convert_speckle_to_pydantic.py
```

### TypeScript API 客户端生成

```bash
# 1. 启动 FastAPI 服务（确保服务运行在 http://localhost:8000）
cd backend
uvicorn app.main:app --reload

# 2. 在另一个终端验证并下载 OpenAPI schema
python scripts/verify_openapi_schema.py

# 3. 生成 TypeScript 代码
# Windows PowerShell
.\scripts\generate_typescript_api.ps1

# Linux/macOS
chmod +x scripts/generate_typescript_api.sh
./scripts/generate_typescript_api.sh
```

生成的 TypeScript 代码保存在 `frontend/src/lib/api/` 目录中。

## 常用命令

### Docker Compose
```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 数据库操作
```bash
# 连接 Memgraph
docker exec -it memgraph_container mgconsole

# 清空数据库（开发环境）
# 在 mgconsole 中执行
MATCH (n) DETACH DELETE n;
```

### 数据加载
```bash
# 加载示例数据
python scripts/load_example_data.py
```

## 调试技巧

### 后端调试

**使用 VS Code 调试**:
1. 在 `.vscode/launch.json` 中配置调试配置
2. 设置断点
3. 按 F5 启动调试

**查看日志**:
```bash
# 查看后端日志
tail -f backend/logs/app.log
```

### 前端调试

**React DevTools**: 安装 Chrome 扩展
**Next.js 调试**: 使用 VS Code 的调试配置

## 常见问题

### Python 依赖安装失败
```bash
# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 升级 pip
python -m pip install --upgrade pip
```

### Memgraph 连接失败
- 检查 Memgraph 是否运行: `docker ps`
- 检查端口是否正确: 默认 7687
- 检查防火墙设置

### TypeScript 代码生成失败
- 确保 FastAPI 服务正在运行
- 检查 `temp/openapi.json` 文件是否存在
- 尝试手动运行: `python scripts/verify_openapi_schema.py`

## 相关文档

- 完整开发指南: `docs/DEVELOPMENT.md`
- 代码规范: `docs/CODING_STANDARDS.md`
- 测试策略: `docs/TESTING.md`
- API 文档: `docs/API.md`

