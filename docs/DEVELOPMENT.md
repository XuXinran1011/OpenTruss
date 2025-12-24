# OpenTruss 开发环境搭建指南

## 1. 环境要求

### 1.1 系统要求

- **操作系统**: Windows 10/11, macOS 10.15+, Linux (Ubuntu 20.04+)
- **内存**: 最低 8GB，推荐 16GB+
- **磁盘空间**: 最低 10GB 可用空间

### 1.2 必需软件

| 软件 | 版本要求 | 说明 |
|------|---------|------|
| Python | 3.10+ | 后端开发语言 |
| Node.js | 18.0+ | 前端开发环境 |
| Docker | 20.10+ | 容器化部署（可选） |
| Docker Compose | 2.0+ | 容器编排（可选） |
| Git | 2.30+ | 版本控制 |

### 1.3 推荐工具

- **IDE**: VS Code / PyCharm
- **数据库客户端**: Memgraph Lab / Neo4j Browser
- **API 测试**: Postman / Insomnia
- **终端**: Windows Terminal / iTerm2

---

## 2. 后端环境搭建

### 2.1 Python 环境

#### 2.1.1 安装 Python

**Windows**:
1. 访问 [Python 官网](https://www.python.org/downloads/)
2. 下载 Python 3.10+ 安装包
3. 安装时勾选 "Add Python to PATH"

**macOS**:
```bash
# 使用 Homebrew
brew install python@3.10
```

**Linux**:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip
```

#### 2.1.2 创建虚拟环境

```bash
# 进入项目目录
cd OpenTruss

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 2.2 安装项目依赖

```bash
# 安装后端依赖
pip install -r requirements.txt

# 或使用开发依赖
pip install -r requirements-dev.txt
```

**主要依赖**:
- `fastapi`: Web 框架
- `uvicorn`: ASGI 服务器
- `pymemgraph`: Memgraph 客户端
- `pydantic`: 数据验证
- `ifcopenshell`: IFC 文件处理

### 2.3 配置环境变量

创建 `.env` 文件：

```env
# 数据库配置
MEMGRAPH_HOST=localhost
MEMGRAPH_PORT=7687
MEMGRAPH_USER=admin
MEMGRAPH_PASSWORD=password

# API 配置
API_HOST=0.0.0.0
API_PORT=8000

# 认证配置
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
```

---

## 3. 前端环境搭建

### 3.1 Node.js 环境

#### 3.1.1 安装 Node.js

**Windows/macOS**: 从 [Node.js 官网](https://nodejs.org/) 下载安装包

**Linux**:
```bash
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

#### 3.1.2 验证安装

```bash
node --version  # 应显示 v18.0.0 或更高
npm --version   # 应显示 9.0.0 或更高
```

### 3.2 安装前端依赖

```bash
cd frontend
npm install
```

---

## 4. 代码生成：Speckle 模型和 TypeScript API

### 4.1 Speckle 模型（Python Pydantic）

Speckle BuiltElements 的 Pydantic 模型已经预生成在 `backend/app/models/speckle/` 目录中。

如果 Speckle 更新了 BuiltElements 定义，可以重新生成：

```bash
# 1. 从 GitHub 获取最新的 Speckle .cs 文件
python scripts/fetch_speckle_built_elements.py

# 2. 转换为 Pydantic 模型
python scripts/convert_speckle_to_pydantic.py
```

### 4.2 TypeScript API 客户端生成

TypeScript 类型和 API 客户端通过 FastAPI 的 OpenAPI schema 自动生成：

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

生成的 TypeScript 代码将保存在 `frontend/src/lib/api/` 目录中。

**注意**: 
- 生成的 TypeScript 代码应该添加到 `.gitignore`，每次构建时重新生成
- 或者提交到版本控制（推荐），以确保团队使用一致的 API 类型定义

---

## 5. 项目结构

```
OpenTruss/
├── backend/              # 后端代码
│   ├── app/
│   │   ├── api/            # API 路由
│   │   │   └── v1/         # API v1
│   │   │       └── ingest.py
│   │   ├── core/           # 核心配置
│   │   ├── models/         # 数据模型
│   │   │   └── speckle/    # Speckle BuiltElements 模型
│   │   │       ├── base.py
│   │   │       ├── architectural.py
│   │   │       ├── structural.py
│   │   │       ├── mep.py
│   │   │       ├── spatial.py
│   │   │       └── other.py
│   │   ├── services/       # 业务逻辑
│   │   ├── utils/          # 工具函数
│   │   └── main.py         # FastAPI 应用入口
│   ├── tests/              # 测试代码
│   ├── requirements.txt    # Python 依赖
│   └── main.py             # 应用入口
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── components/     # React 组件
│   │   ├── app/            # Next.js App Router 页面（或 pages/）
│   │   ├── lib/
│   │   │   └── api/        # 生成的 TypeScript API 客户端
│   │   ├── services/       # API 服务
│   │   └── utils/          # 工具函数
│   ├── package.json        # Node 依赖
│   ├── next.config.js      # Next.js 配置
│   └── tailwind.config.js  # Tailwind CSS 配置
├── docs/                   # 文档
├── scripts/                # 工具脚本
│   ├── fetch_speckle_built_elements.py
│   ├── convert_speckle_to_pydantic.py
│   ├── verify_openapi_schema.py
│   └── generate_typescript_api.*
└── docker-compose.yml      # Docker 编排
```

---

## 6. 启动开发环境

### 6.1 使用 Docker Compose（推荐）

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 6.2 手动启动

**终端 1 - 启动 Memgraph**:
```bash
docker run -it -p 7687:7687 memgraph/memgraph
```

**终端 2 - 启动后端**:
```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**终端 3 - 启动前端**:
```bash
cd frontend
npm run dev
```

### 6.3 验证启动

- **后端 API**: http://localhost:8000/docs (Swagger UI)
- **前端应用**: http://localhost:3000 (Next.js 默认端口)
- **Memgraph**: localhost:7687

---

## 7. 开发工具配置

### 7.1 VS Code 配置

创建 `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "[python]": {
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  },
  "[typescript]": {
    "editor.formatOnSave": true
  },
  "[typescriptreact]": {
    "editor.formatOnSave": true
  }
}
```

### 7.2 Git 配置

创建 `.gitignore`:

```gitignore
# Python
venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info/
dist/
build/

# 环境变量
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# 临时文件
temp/
*.log

# 生成的 TypeScript API（可选，如果提交到版本控制则注释掉）
frontend/src/lib/api/

# Node
node_modules/
.next/
out/
```

---

## 8. 开发工作流

### 8.1 后端开发

1. **创建新功能分支**
   ```bash
   git checkout -b feature/your-feature
   ```

2. **运行测试**
   ```bash
   cd backend
   pytest
   ```

3. **代码格式化**
   ```bash
   black .
   isort .
   ```

4. **提交代码**
   ```bash
   git add .
   git commit -m "feat: your feature description"
   ```

### 8.2 前端开发

1. **生成/更新 TypeScript API**
   ```bash
   # 确保后端服务运行
   python scripts/verify_openapi_schema.py
   npm run generate-api
   ```

2. **运行开发服务器**
   ```bash
   npm run dev
   ```

3. **代码检查**
   ```bash
   npm run lint
   ```

### 8.3 API 开发

1. **定义 Pydantic 模型** (在 `backend/app/models/` 中)
2. **创建 API 端点** (在 `backend/app/api/v1/` 中)
3. **验证 OpenAPI schema** (运行 `python scripts/verify_openapi_schema.py`)
4. **生成 TypeScript 客户端** (运行 `npm run generate-api`)
5. **在前端使用生成的 API 客户端**

---

## 9. 常见问题

### 9.1 Python 依赖安装失败

**问题**: `pip install` 失败

**解决方案**:
- 使用国内镜像: `pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`
- 升级 pip: `python -m pip install --upgrade pip`

### 9.2 Memgraph 连接失败

**问题**: 无法连接到 Memgraph

**解决方案**:
- 检查 Memgraph 是否运行: `docker ps`
- 检查端口是否正确: 默认 7687
- 检查防火墙设置

### 9.3 TypeScript 代码生成失败

**问题**: `npm run generate-api` 失败

**解决方案**:
- 确保 FastAPI 服务正在运行
- 检查 `temp/openapi.json` 文件是否存在
- 尝试手动运行: `python scripts/verify_openapi_schema.py`

---

## 10. 下一步

- 阅读 [代码规范文档](docs/CODING_STANDARDS.md)
- 查看 [API 设计文档](docs/API.md)
- 参考 [测试策略文档](docs/TESTING.md)
