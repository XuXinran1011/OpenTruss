# OpenTruss 示例数据

本目录包含 OpenTruss 项目的示例数据，用于快速测试和演示。

## 文件说明

- `sample_project.json`: 示例项目数据（GB50300 层级结构）
- `sample_elements.json`: 示例构件数据（墙体、柱子等）
- `load_example_data.py`: 加载示例数据到数据库的脚本

## 使用方法

### 1. 确保 Memgraph 正在运行

```bash
docker-compose up -d memgraph
```

### 2. 加载示例数据

```bash
cd backend
python ../examples/load_example_data.py
```

或者使用脚本：

```bash
# 使用 Makefile
make load-examples

# 或直接运行
python scripts/load_example_data.py
```

### 3. 验证数据

访问 API 查看加载的数据：

```bash
# 获取项目列表
curl http://localhost:8000/api/v1/projects

# 获取构件列表
curl http://localhost:8000/api/v1/elements
```

## 数据结构

### 项目层级结构

示例项目遵循 GB50300 标准的六级层级结构：

```
项目 (Project)
  └─ 1#楼 (Building)
      └─ 主体结构 (Division)
          └─ 砌体结构 (SubDivision)
              └─ 填充墙砌体 (Item)
                  └─ F1层填充墙 (InspectionLot)
                      └─ 构件 (Elements)
```

### 示例构件

示例数据包含以下类型的构件：

- **墙体 (Wall)**: F1 层的填充墙构件
- **柱子 (Column)**: 结构柱构件
- **梁 (Beam)**: 结构梁构件

所有构件都包含：
- 2D 几何数据（Polyline）
- 楼层信息
- 状态信息（Draft/Verified）

## 注意事项

- 示例数据仅用于开发和测试
- 加载示例数据会清空现有数据（可选）
- 确保数据库连接配置正确

