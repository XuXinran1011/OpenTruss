# Phase 1 测试验证指南

本指南帮助您验证 Phase 1 的所有实现功能。

## 快速开始

### 1. 环境准备

```bash
# 1. 确保 Python 3.10+ 已安装
python --version

# 2. 进入后端目录
cd backend

# 3. 创建虚拟环境（如果还没有）
python -m venv venv

# 4. 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 5. 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 开发依赖（包含 pytest）

# 6. 确保 .env 文件存在（已从 .env.example 创建）
# 如果需要，手动创建 backend/.env 文件
```

### 2. 启动 Memgraph

**方式 1: 使用 Docker Compose**
```bash
# 在项目根目录
docker-compose up -d memgraph
```

**方式 2: 使用 Docker 直接运行**
```bash
docker run -it -p 7687:7687 -p 7444:7444 memgraph/memgraph:latest
```

**验证 Memgraph 运行**:
```bash
# Windows PowerShell
docker ps | Select-String memgraph

# 或访问
curl http://localhost:7444/healthz
```

### 3. 运行测试脚本

**方式 1: 直接运行 Python 脚本**
```bash
cd backend
python tests/test_manual_verification.py
```

**方式 2: 使用 pytest**
```bash
cd backend
pytest tests/test_manual_verification.py -v -s
```

## 测试步骤详解

### 测试 1: 模块导入测试

验证所有 Python 模块可以正确导入。

**预期结果**:
- ✅ 所有模块导入成功
- ✅ 配置读取正常

### 测试 2: Memgraph 连接测试

验证能够连接到 Memgraph 数据库。

**前提条件**: Memgraph 必须正在运行

**预期结果**:
- ✅ 连接成功
- ✅ 可以执行查询

**如果失败**:
- 检查 Memgraph 是否运行: `docker ps`
- 检查端口: `netstat -an | findstr 7687` (Windows)
- 检查 `.env` 文件配置

### 测试 3: Schema 初始化测试

验证 Schema 初始化服务能够创建索引和默认节点。

**预期结果**:
- ✅ Schema 初始化成功
- ✅ Unassigned Item 节点存在
- ✅ 默认层级结构已创建

### 测试 4: FastAPI 应用启动测试

**步骤**:
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**验证**:
1. 访问 http://localhost:8000/docs - 应该显示 Swagger UI
2. 访问 http://localhost:8000/health - 应该返回 `{"status": "healthy"}`
3. 检查日志，确认 Schema 初始化成功

### 测试 5: Ingestion API 测试

**使用 Swagger UI**:
1. 访问 http://localhost:8000/docs
2. 找到 `POST /api/v1/ingest` 端点
3. 点击 "Try it out"
4. 使用以下测试数据:

```json
{
  "project_id": "test_project_001",
  "elements": [
    {
      "speckle_type": "Wall",
      "geometry_2d": {
        "type": "Polyline",
        "coordinates": [[0, 0], [10, 0], [10, 5], [0, 5], [0, 0]],
        "closed": true
      },
      "level_id": "level_f1"
    }
  ]
}
```

5. 点击 "Execute"
6. 检查响应

**使用 curl**:
```bash
curl -X POST "http://localhost:8000/api/v1/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "test_project_001",
    "elements": [
      {
        "speckle_type": "Wall",
        "geometry_2d": {
          "type": "Polyline",
          "coordinates": [[0, 0], [10, 0], [10, 5], [0, 5], [0, 0]],
          "closed": true
        },
        "level_id": "level_f1"
      }
    ]
  }'
```

**验证数据存储**:

使用 Memgraph Lab 或 Neo4j Browser 连接到 localhost:7687，执行:

```cypher
// 查询所有 Element
MATCH (e:Element)
RETURN e.id, e.speckle_type, e.level_id
LIMIT 10;

// 查询 Element 的关系
MATCH (e:Element)-[r]->(n)
RETURN e.id, type(r), labels(n), n.id;
```

## 常见问题

### 问题 1: pymemgraph 导入错误

**错误**: `ModuleNotFoundError: No module named 'pymemgraph'`

**解决**: 
```bash
pip install pymemgraph
```

**注意**: 如果 `pymemgraph` 包不存在或 API 不匹配，可能需要使用 `neo4j` 驱动替代。Memgraph 兼容 Neo4j 的 Bolt 协议。

### 问题 2: Memgraph 连接失败

**错误**: `ConnectionError: Cannot connect to Memgraph`

**检查清单**:
- [ ] Memgraph Docker 容器正在运行
- [ ] 端口 7687 未被占用
- [ ] `.env` 文件中的 `MEMGRAPH_HOST` 和 `MEMGRAPH_PORT` 正确
- [ ] 防火墙未阻止连接

### 问题 3: Schema 初始化失败

**检查**:
- 查看应用启动日志
- 使用 Memgraph Lab 检查是否有错误
- 验证 Cypher 语法是否正确

### 问题 4: 数据摄入失败

**检查**:
- 验证请求数据格式是否正确
- 检查 Element 节点的 geometry_2d 序列化
- 查看应用日志中的错误信息

## 下一步

测试验证通过后：
1. 记录测试结果
2. 修复发现的问题
3. 编写自动化测试用例
4. 继续 Phase 2 开发

