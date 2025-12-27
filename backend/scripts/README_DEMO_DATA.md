# 演示数据生成脚本使用指南

## 概述

`create_demo_data.py` 脚本用于在 Agent AI 读图功能实现之前，快速创建完整的演示数据集。脚本会创建符合 GB50300 标准的完整层级结构，包括项目、单体、分部、子分部、分项、检验批和构件。

## 前置条件

### 1. 确保 Memgraph 数据库正在运行

**方式 1: 使用 Docker Compose（推荐）**
```bash
# 在项目根目录
docker-compose up -d memgraph

# 验证 Memgraph 是否运行
docker ps | findstr memgraph
```

**方式 2: 使用 Docker 直接运行**
```bash
docker run -it -p 7687:7687 -p 7444:7444 memgraph/memgraph:latest
```

**验证连接**:
```bash
# Windows PowerShell
curl http://localhost:7444/healthz

# 或访问浏览器
# http://localhost:7444
```

### 2. 确保后端环境已配置

```bash
# 进入后端目录
cd backend

# 确保虚拟环境已激活（如果使用）
# Windows:
.\venv\Scripts\Activate.ps1
# macOS/Linux:
source venv/bin/activate

# 确保依赖已安装
pip install -r requirements.txt
```

### 3. 检查环境变量

确保 `backend/.env` 文件存在并包含 Memgraph 连接配置：

```env
MEMGRAPH_HOST=localhost
MEMGRAPH_PORT=7687
MEMGRAPH_USERNAME=
MEMGRAPH_PASSWORD=
```

如果 `.env` 文件不存在，可以从 `.env.example` 复制：

```bash
# Windows PowerShell
Copy-Item .env.example .env

# macOS/Linux
cp .env.example .env
```

## 使用方法

### 基本用法

在 `backend` 目录下运行：

```bash
cd backend
python -m scripts.create_demo_data
```

### 运行输出示例

```
INFO:app.utils.memgraph:Connected to Memgraph at localhost:7687
INFO:__main__:开始创建演示数据...
INFO:app.services.schema:Initializing OpenTruss schema...
INFO:app.services.schema:Schema initialization completed successfully
INFO:__main__:✓ 创建项目: demo_project
INFO:__main__:✓ 创建单体: demo_building_001
INFO:__main__:✓ 创建楼层: demo_level_f1
INFO:__main__:✓ 创建分部: demo_division_001
INFO:__main__:✓ 创建子分部: demo_subdivision_001
INFO:__main__:✓ 创建分项: demo_item_001
INFO:__main__:✓ 创建检验批: demo_lot_001
INFO:__main__:✓ 创建 5 个构件

============================================================
演示数据创建完成！
============================================================
项目ID: demo_project
单体ID: demo_building_001
楼层ID: demo_level_f1
检验批ID: demo_lot_001
构件数量: 5
构件IDs: demo_element_001, demo_element_002, demo_element_003, demo_element_004, demo_element_005
============================================================

现在可以使用这些数据进行演示和测试了！
```

## 创建的数据结构

脚本会创建以下完整的 GB50300 层级结构：

```
项目 (Project)
└── demo_project - "演示项目"
    └── 单体 (Building)
        └── demo_building_001 - "1#楼"
            ├── 楼层 (Level)
            │   └── demo_level_f1 - "F1" (elevation: 0.0)
            └── 分部 (Division)
                └── demo_division_001 - "主体结构"
                    └── 子分部 (SubDivision)
                        └── demo_subdivision_001 - "砌体结构"
                            └── 分项 (Item)
                                └── demo_item_001 - "填充墙砌体"
                                    └── 检验批 (InspectionLot)
                                        └── demo_lot_001 - "1#楼F1层填充墙砌体检验批"
                                            ├── demo_element_001 - Wall (10m x 0.2m, height: 3.0m)
                                            ├── demo_element_002 - Wall (10m x 0.2m, height: 3.0m)
                                            ├── demo_element_003 - Column (0.5m x 0.5m, height: 3.0m)
                                            ├── demo_element_004 - Floor (20m x 10m, height: 0.2m)
                                            └── demo_element_005 - Wall (20m x 0.2m, height: 3.0m)
```

### 构件详情

脚本会创建 5 个不同类型的构件，每个构件包含：

- **几何信息** (`geometry_2d`): 2D 多边形坐标
- **高度** (`height`): 构件高度（米）
- **基础偏移** (`base_offset`): 基础偏移量（米）
- **材料** (`material`): 材料类型（如 "concrete"）
- **状态** (`status`): 构件状态（"Draft"）
- **关联关系**:
  - 关联到检验批 (`demo_lot_001`)
  - 关联到楼层 (`demo_level_f1`)

## 使用创建的数据

### 1. 通过 API 查询

启动后端服务后，可以通过 API 查询创建的数据：

```bash
# 启动后端服务
cd backend
uvicorn app.main:app --reload

# 在另一个终端查询项目层级
curl http://localhost:8000/api/v1/hierarchy/projects/demo_project/hierarchy

# 查询检验批详情
curl http://localhost:8000/api/v1/inspection-lots/demo_lot_001

# 查询构件列表
curl http://localhost:8000/api/v1/elements?inspection_lot_id=demo_lot_001
```

### 2. 在前端界面查看

1. 启动前端服务：
   ```bash
   cd frontend
   npm run dev
   ```

2. 访问前端界面：
   - 打开浏览器访问 `http://localhost:3000`
   - 导航到层级树视图
   - 展开项目树查看创建的演示数据

### 3. 在 Memgraph 中直接查询

使用 Memgraph Lab 或 Cypher 查询：

```cypher
// 查看项目
MATCH (p:Project {id: "demo_project"})
RETURN p

// 查看完整层级树
MATCH path = (p:Project {id: "demo_project"})-[:PHYSICALLY_CONTAINS|MANAGEMENT_CONTAINS|HAS_LOT*]->(n)
RETURN path

// 查看所有构件
MATCH (e:Element)
WHERE e.inspection_lot_id = "demo_lot_001"
RETURN e.id, e.speckle_type, e.height, e.material
```

## 注意事项

### 1. 幂等性

脚本具有幂等性，可以多次运行而不会创建重复数据：

- 如果节点已存在，脚本会跳过创建
- 如果关系已存在，脚本会跳过创建
- 可以安全地多次运行脚本

### 2. 数据清理

如果需要清理演示数据，可以使用以下 Cypher 查询：

```cypher
// 删除演示项目及其所有相关节点
MATCH (p:Project {id: "demo_project"})
OPTIONAL MATCH path = (p)-[*]->(n)
DETACH DELETE p, n
```

或者删除所有演示数据：

```cypher
// 删除所有以 "demo_" 开头的节点
MATCH (n)
WHERE n.id STARTS WITH "demo_"
DETACH DELETE n
```

### 3. 自定义数据

如果需要创建自定义的演示数据，可以修改脚本中的以下部分：

- **项目信息**: 修改 `create_demo_project()` 方法中的项目名称和描述
- **构件配置**: 修改 `_create_demo_elements()` 方法中的 `element_configs` 列表
- **构件数量**: 修改 `count` 参数（默认 5 个）

## 故障排除

### 问题 1: 连接 Memgraph 失败

**错误信息**:
```
ERROR: Failed to connect to Memgraph
```

**解决方案**:
1. 检查 Memgraph 是否运行: `docker ps`
2. 检查端口是否正确: `netstat -an | findstr 7687` (Windows)
3. 检查 `.env` 文件中的连接配置

### 问题 2: 模块导入错误

**错误信息**:
```
ImportError: cannot import name 'ElementNode' from 'app.models.gb50300.nodes'
```

**解决方案**:
1. 确保在 `backend` 目录下运行脚本
2. 确保使用 `python -m scripts.create_demo_data` 而不是直接运行
3. 检查 Python 路径是否正确

### 问题 3: Schema 初始化失败

**错误信息**:
```
ERROR: Schema initialization failed
```

**解决方案**:
1. 检查 Memgraph 连接是否正常
2. 检查是否有足够的权限创建节点和关系
3. 查看详细错误日志

## 相关文档

- [GB50300 标准文档](../.claude/skills/opentruss-gb50300/SKILL.md)
- [开发指南](../../docs/DEVELOPMENT.md)
- [API 文档](../../docs/API.md)

## 支持

如果遇到问题，请：

1. 查看日志输出获取详细错误信息
2. 检查 Memgraph 数据库状态
3. 查看项目文档和常见问题
4. 提交 Issue 到项目仓库

