# OpenTruss 数据库 Schema 文档

## 1. 概述

OpenTruss 使用 Memgraph 作为 LPG (Labeled Property Graph) 数据库，存储符合 GB50300 国标的层级结构数据和构件信息。

### 1.1 图数据库特点

- **节点 (Node)**: 实体（如 Project、Building、Element）
- **关系 (Relationship)**: 实体之间的连接（如 CONTAINS、HAS_LOT）
- **属性 (Property)**: 节点和关系的键值对数据
- **标签 (Label)**: 节点的类型标识（如 :Project、:Element）

### 1.2 查询语言

使用 **Cypher** 查询语言，类似于 SQL 但专为图数据设计。

---

## 2. 节点类型定义

### 2.1 Project (项目)

**标签**: `:Project`

**属性**:
| 属性名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `id` | String | 是 | 唯一标识符 |
| `name` | String | 是 | 项目名称 |
| `description` | String | 否 | 项目描述 |
| `created_at` | DateTime | 是 | 创建时间 |
| `updated_at` | DateTime | 是 | 更新时间 |

**示例**:
```cypher
CREATE (p:Project {
  id: "project_001",
  name: "某住宅小区项目",
  description: "总建筑面积 10 万平方米",
  created_at: datetime(),
  updated_at: datetime()
})
```

### 2.2 Building (单体)

**标签**: `:Building`

**属性**:
| 属性名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `id` | String | 是 | 唯一标识符 |
| `name` | String | 是 | 单体名称（如：1#楼） |
| `project_id` | String | 是 | 所属项目 ID |
| `created_at` | DateTime | 是 | 创建时间 |
| `updated_at` | DateTime | 是 | 更新时间 |

**示例**:
```cypher
CREATE (b:Building {
  id: "building_001",
  name: "1#楼",
  project_id: "project_001",
  created_at: datetime(),
  updated_at: datetime()
})
```

### 2.3 Division (分部)

**标签**: `:Division`

**属性**:
| 属性名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `id` | String | 是 | 唯一标识符 |
| `name` | String | 是 | 分部名称（如：主体结构） |
| `building_id` | String | 是 | 所属单体 ID |
| `created_at` | DateTime | 是 | 创建时间 |
| `updated_at` | DateTime | 是 | 更新时间 |

### 2.4 SubDivision (子分部)

**标签**: `:SubDivision`

**属性**:
| 属性名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `id` | String | 是 | 唯一标识符 |
| `name` | String | 是 | 子分部名称（如：砌体结构） |
| `division_id` | String | 是 | 所属分部 ID |
| `created_at` | DateTime | 是 | 创建时间 |
| `updated_at` | DateTime | 是 | 更新时间 |

### 2.5 Item (分项)

**标签**: `:Item`

**属性**:
| 属性名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `id` | String | 是 | 唯一标识符 |
| `name` | String | 是 | 分项名称（如：填充墙砌体） |
| `sub_division_id` | String | 是 | 所属子分部 ID |
| `created_at` | DateTime | 是 | 创建时间 |
| `updated_at` | DateTime | 是 | 更新时间 |

**特殊节点**: `Unassigned Item`
- 用于暂存无法确定归属的构件
- ID 固定为 `"unassigned_item"`

### 2.6 InspectionLot (检验批)

**标签**: `:InspectionLot`

**属性**:
| 属性名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `id` | String | 是 | 唯一标识符 |
| `name` | String | 是 | 检验批名称 |
| `item_id` | String | 是 | 所属分项 ID |
| `spatial_scope` | String | 是 | 空间范围（如：Level:F1） |
| `status` | String | 是 | 状态（PLANNING/IN_PROGRESS/SUBMITTED/APPROVED/PUBLISHED） |
| `created_at` | DateTime | 是 | 创建时间 |
| `updated_at` | DateTime | 是 | 更新时间 |

**状态枚举**:
- `PLANNING`: 规划中
- `IN_PROGRESS`: 清洗中
- `SUBMITTED`: 待审批
- `APPROVED`: 已验收
- `PUBLISHED`: 已发布

**示例**:
```cypher
CREATE (lot:InspectionLot {
  id: "lot_001",
  name: "1#楼F1层填充墙砌体检验批",
  item_id: "item_001",
  spatial_scope: "Level:F1",
  status: "PLANNING",
  created_at: datetime(),
  updated_at: datetime()
})
```

### 2.7 Element (构件)

**标签**: `:Element`

**属性**:
| 属性名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `id` | String | 是 | 唯一标识符 |
| `speckle_id` | String | 否 | Speckle 原始 ID |
| `speckle_type` | String | 是 | 构件类型（如：Wall、Column） |
| `geometry` | Object | 是 | 3D 原生几何数据（Line/Polyline），坐标格式：[[x, y, z], ...] |
| `height` | Float | 否 | 高度（Walls/Columns: 拉伸距离；Beams/Pipes: 横截面深度） |
| `base_offset` | Float | 否 | 基础偏移（Z 轴起点） |
| `material` | String | 否 | 材质 |
| `level_id` | String | 是 | 所属楼层 ID |
| `zone_id` | String | 否 | 所属区域 ID |
| `inspection_lot_id` | String | 否 | 所属检验批 ID |
| `status` | String | 是 | 状态（Draft/Verified） |
| `confidence` | Float | 否 | AI 识别置信度（0-1） |
| `locked` | Boolean | 是 | 是否锁定（默认: false） |
| `created_at` | DateTime | 是 | 创建时间 |
| `updated_at` | DateTime | 是 | 更新时间 |

**状态枚举**:
- `Draft`: 草稿（数据不完整）
- `Verified`: 已验证（数据完整）

**几何数据格式**:
```json
{
  "type": "Polyline",
  "coordinates": [[0, 0], [10, 0], [10, 5], [0, 5], [0, 0]],
  "closed": true
}
```

**示例**:
```cypher
CREATE (e:Element {
  id: "element_001",
  speckle_type: "Wall",
  geometry: {
    type: "Polyline",
    coordinates: [[0, 0, 0], [10, 0, 0], [10, 5, 0], [0, 5, 0], [0, 0, 0]],
    closed: true
  },
  height: 3.0,
  base_offset: 0.0,
  material: "concrete",
  level_id: "level_f1",
  status: "Draft",
  confidence: 0.85,
  locked: false,
  created_at: datetime(),
  updated_at: datetime()
})
```

### 2.8 Level (楼层)

**标签**: `:Level`

**属性**:
| 属性名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `id` | String | 是 | 唯一标识符 |
| `name` | String | 是 | 楼层名称（如：F1、F2） |
| `elevation` | Float | 否 | 标高 |
| `building_id` | String | 是 | 所属单体 ID |

### 2.9 Zone (区域)

**标签**: `:Zone`

**属性**:
| 属性名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `id` | String | 是 | 唯一标识符 |
| `name` | String | 是 | 区域名称（如：A区、B区） |
| `level_id` | String | 是 | 所属楼层 ID |

### 2.10 System (系统 - MEP 专业系统)

**标签**: `:System`

**属性**:
| 属性名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `id` | String | 是 | 唯一标识符 |
| `name` | String | 是 | 系统名称（如：给水系统、排水系统） |
| `system_type` | String | 是 | 系统类型（如：MEP_WATER_SUPPLY、MEP_DRAINAGE、MEP_ELECTRICAL） |
| `building_id` | String | 是 | 所属单体 ID |
| `created_at` | DateTime | 是 | 创建时间 |
| `updated_at` | DateTime | 是 | 更新时间 |

**说明**: 用于表示 MEP（机电）等专业系统，支持未来扩展。

### 2.11 SubSystem (子系统)

**标签**: `:SubSystem`

**属性**:
| 属性名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `id` | String | 是 | 唯一标识符 |
| `name` | String | 是 | 子系统名称 |
| `system_id` | String | 是 | 所属系统 ID |
| `created_at` | DateTime | 是 | 创建时间 |
| `updated_at` | DateTime | 是 | 更新时间 |

---

## 3. 关系类型定义

OpenTruss 支持三种不同维度的从属关系，使用不同的关系类型区分，确保语义清晰和查询性能：

1. **物理从属（PHYSICALLY_CONTAINS）**：表示空间物理层级关系
2. **管理从属（MANAGEMENT_CONTAINS）**：表示 GB50300 验收管理层级关系
3. **专业逻辑从属（SYSTEM_CONTAINS）**：表示 MEP 等专业系统逻辑层级关系

**重要说明**：同一个 Element 节点可以同时连接到多个维度的父节点，例如：
- 一个墙构件可能同时属于：物理层级（F1层）、管理层级（填充墙砌体检验批）、专业系统（给水系统）

### 3.1 物理从属关系

#### PHYSICALLY_CONTAINS (物理包含)

**方向**: 父节点 → 子节点

**关系类型**: `:PHYSICALLY_CONTAINS`

**说明**: 表示空间物理层级包含关系

**关系链**:
```
Project -[:PHYSICALLY_CONTAINS]-> Building
Building -[:PHYSICALLY_CONTAINS]-> Level
Building -[:PHYSICALLY_CONTAINS]-> Zone
Level -[:PHYSICALLY_CONTAINS]-> Zone
Zone -[:PHYSICALLY_CONTAINS]-> Element
Level -[:PHYSICALLY_CONTAINS]-> Element  (直接位于楼层)
```

**示例**:
```cypher
// 项目包含单体
MATCH (p:Project {id: "project_001"}), (b:Building {id: "building_001"})
CREATE (p)-[:PHYSICALLY_CONTAINS]->(b)

// 单体包含楼层
MATCH (b:Building {id: "building_001"}), (l:Level {id: "level_f1"})
CREATE (b)-[:PHYSICALLY_CONTAINS]->(l)

// 楼层包含元素
MATCH (l:Level {id: "level_f1"}), (e:Element {id: "element_001"})
CREATE (l)-[:PHYSICALLY_CONTAINS]->(e)
```

### 3.2 管理从属关系

#### MANAGEMENT_CONTAINS (管理包含)

**方向**: 父节点 → 子节点

**关系类型**: `:MANAGEMENT_CONTAINS`

**说明**: 表示 GB50300 验收管理层级包含关系

**关系链**:
```
Project -[:MANAGEMENT_CONTAINS]-> Building
Building -[:MANAGEMENT_CONTAINS]-> Division
Division -[:MANAGEMENT_CONTAINS]-> SubDivision
SubDivision -[:MANAGEMENT_CONTAINS]-> Item
Item -[:HAS_LOT]-> InspectionLot  (使用 HAS_LOT 表示检验批关联)
InspectionLot -[:MANAGEMENT_CONTAINS]-> Element
```

**示例**:
```cypher
// 项目包含单体（管理维度）
MATCH (p:Project {id: "project_001"}), (b:Building {id: "building_001"})
CREATE (p)-[:MANAGEMENT_CONTAINS]->(b)

// 分部包含子分部
MATCH (div:Division {id: "div_001"}), (subdiv:SubDivision {id: "subdiv_001"})
CREATE (div)-[:MANAGEMENT_CONTAINS]->(subdiv)

// 检验批包含元素
MATCH (lot:InspectionLot {id: "lot_001"}), (e:Element {id: "element_001"})
CREATE (lot)-[:MANAGEMENT_CONTAINS]->(e)
```

**注意**: Item 与 InspectionLot 之间使用 `:HAS_LOT` 关系（见 3.4），因为检验批是分项与空间的交集，而非严格的层级包含。

### 3.3 专业系统从属关系（未来扩展）

#### SYSTEM_CONTAINS (系统包含)

**方向**: 父节点 → 子节点

**关系类型**: `:SYSTEM_CONTAINS`

**说明**: 表示 MEP 等专业系统的逻辑层级包含关系

**关系链**:
```
Building -[:SYSTEM_CONTAINS]-> System
System -[:SYSTEM_CONTAINS]-> SubSystem
SubSystem -[:SYSTEM_CONTAINS]-> Element
```

**示例**:
```cypher
// 单体包含系统
MATCH (b:Building {id: "building_001"}), (s:System {id: "system_001"})
CREATE (b)-[:SYSTEM_CONTAINS]->(s)

// 系统包含子系统
MATCH (s:System {id: "system_001"}), (subs:SubSystem {id: "subsystem_001"})
CREATE (s)-[:SYSTEM_CONTAINS]->(subs)

// 子系统包含元素
MATCH (subs:SubSystem {id: "subsystem_001"}), (e:Element {id: "element_001"})
CREATE (subs)-[:SYSTEM_CONTAINS]->(e)
```

**说明**: MEP 专业系统关系用于未来扩展，当前 Phase 1-4 阶段可暂不实现，但需要在 Schema 中预留。

### 3.4 空间关系

#### LOCATED_AT (位于)

**方向**: Element → Level/Zone

**关系类型**: `:LOCATED_AT`

**说明**: 表示构件位于某个楼层或区域（与 PHYSICALLY_CONTAINS 互补，提供快速查询路径）

#### LOCATED_AT (位于)

**方向**: Element → Level/Zone

**关系类型**: `:LOCATED_AT`

**说明**: 表示构件位于某个楼层或区域

**示例**:
```cypher
MATCH (e:Element {id: "element_001"}), (l:Level {id: "level_f1"})
CREATE (e)-[:LOCATED_AT]->(l)
```

### 3.3 拓扑关系

#### CONNECTED_TO (连接)

**方向**: Element ↔ Element

**关系类型**: `:CONNECTED_TO`

**说明**: 表示构件之间的拓扑连接关系（2D 拓扑）

**属性**:
| 属性名 | 类型 | 说明 |
|--------|------|------|
| `connection_type` | String | 连接类型（如：adjacent、intersect） |
| `confidence` | Float | 连接置信度 |

**示例**:
```cypher
MATCH (e1:Element {id: "element_001"}), (e2:Element {id: "element_002"})
CREATE (e1)-[:CONNECTED_TO {
  connection_type: "adjacent",
  confidence: 0.9
}]->(e2)
```

### 3.5 检验批关系

#### HAS_LOT (拥有检验批)

**方向**: Item → InspectionLot

**关系类型**: `:HAS_LOT`

**说明**: 表示分项拥有检验批。检验批是分项（Item）与空间（Level/Zone）的交集，因此使用独立的关系类型 `HAS_LOT` 而非 `MANAGEMENT_CONTAINS`，以准确表达这种特殊的关联关系。

**示例**:
```cypher
MATCH (i:Item {id: "item_001"}), (lot:InspectionLot {id: "lot_001"})
CREATE (i)-[:HAS_LOT]->(lot)
```

---

## 4. 索引策略

### 4.1 节点索引

为提高查询性能，为常用查询字段创建索引：

```cypher
// Project 索引
CREATE INDEX ON :Project(id);
CREATE INDEX ON :Project(name);

// Building 索引
CREATE INDEX ON :Building(id);
CREATE INDEX ON :Building(project_id);

// Element 索引
CREATE INDEX ON :Element(id);
CREATE INDEX ON :Element(speckle_type);
CREATE INDEX ON :Element(level_id);
CREATE INDEX ON :Element(inspection_lot_id);
CREATE INDEX ON :Element(status);

// InspectionLot 索引
CREATE INDEX ON :InspectionLot(id);
CREATE INDEX ON :InspectionLot(item_id);
CREATE INDEX ON :InspectionLot(status);
```

### 4.2 关系索引

```cypher
// 为关系属性创建索引（如果 Memgraph 支持）
// 注意：Memgraph 的关系索引支持可能有限，需根据实际版本调整
```

---

## 5. 常用 Cypher 查询示例

### 5.1 查询完整层级结构

```cypher
MATCH path = (p:Project {id: "project_001"})-[:CONTAINS*]->(e:Element)
RETURN path
ORDER BY length(path)
```

### 5.2 查询检验批及其构件

```cypher
MATCH (lot:InspectionLot {id: "lot_001"})-[:MANAGEMENT_CONTAINS]->(e:Element)
RETURN lot, collect(e) as elements
```

### 5.3 查询未分配的构件

```cypher
MATCH (e:Element)
WHERE e.inspection_lot_id IS NULL
  OR e.inspection_lot_id = ""
RETURN e
LIMIT 100
```

### 5.4 查询不完整的构件

```cypher
MATCH (e:Element)
WHERE e.height IS NULL
   OR e.material IS NULL
   OR e.status = "Draft"
RETURN e
```

### 5.5 按规则查询构件（规则引擎）

```cypher
// 查询 F1 层的所有墙体构件（使用物理从属关系）
MATCH (e:Element)-[:LOCATED_AT]->(l:Level {name: "F1"})
WHERE e.speckle_type = "Wall"
  AND e.level_id = "level_f1"
RETURN e

// 或使用物理从属关系查询
MATCH (l:Level {name: "F1"})-[:PHYSICALLY_CONTAINS]->(e:Element)
WHERE e.speckle_type = "Wall"
RETURN e
```

### 5.6 更新构件状态

```cypher
MATCH (e:Element {id: "element_001"})
SET e.height = 3.5,
    e.material = "brick",
    e.status = "Verified",
    e.updated_at = datetime()
RETURN e
```

### 5.7 创建检验批并关联构件

```cypher
// 1. 创建检验批
CREATE (lot:InspectionLot {
  id: "lot_001",
  name: "1#楼F1层填充墙砌体检验批",
  item_id: "item_001",
  spatial_scope: "Level:F1",
  status: "PLANNING",
  created_at: datetime(),
  updated_at: datetime()
})

// 2. 关联到分项（使用 HAS_LOT）
MATCH (i:Item {id: "item_001"}), (lot:InspectionLot {id: "lot_001"})
CREATE (i)-[:HAS_LOT]->(lot)

// 3. 关联符合条件的构件（使用 MANAGEMENT_CONTAINS）
MATCH (lot:InspectionLot {id: "lot_001"}), 
      (e:Element)
WHERE e.level_id = "level_f1"
  AND e.speckle_type = "Wall"
  AND e.item_id = "item_001"
CREATE (lot)-[:MANAGEMENT_CONTAINS]->(e)
SET e.inspection_lot_id = "lot_001"
```

### 5.8 查询构件拓扑连接

```cypher
MATCH (e1:Element {id: "element_001"})-[:CONNECTED_TO]-(e2:Element)
RETURN e1, e2
```

### 5.9 统计检验批进度

```cypher
MATCH (lot:InspectionLot)
WHERE lot.item_id = "item_001"
RETURN lot.status, count(lot) as count
ORDER BY lot.status
```

### 5.10 验证检验批完整性

```cypher
MATCH (lot:InspectionLot {id: "lot_001"})-[:MANAGEMENT_CONTAINS]->(e:Element)
WITH lot, collect(e) as elements
WHERE ALL(e IN elements WHERE 
  e.height IS NOT NULL 
  AND e.material IS NOT NULL 
  AND e.geometry_2d.closed = true
)
RETURN lot, size(elements) as element_count
```

---

## 6. RDF 本体映射

### 6.1 节点映射规则

| LPG 节点 | RDF 本体 | 命名空间 |
|---------|---------|---------|
| `:Project` | `bot:Building` | `https://w3id.org/bot#` |
| `:Building` | `bot:Building` | `https://w3id.org/bot#` |
| `:Element {speckle_type: "Wall"}` | `ifc:Wall` | `https://standards.buildingsmart.org/IFC/DEV/IFC4_3/OWL#` |
| `:Element {speckle_type: "Column"}` | `ifc:Column` | `https://standards.buildingsmart.org/IFC/DEV/IFC4_3/OWL#` |
| `:System` | `bot:Building` | `https://w3id.org/bot#` (未来扩展) |
| `:SubSystem` | `bot:Building` | `https://w3id.org/bot#` (未来扩展) |

### 6.2 关系映射规则

| LPG 关系 | RDF 属性 | 命名空间 | 说明 |
|---------|---------|---------|------|
| `-[:PHYSICALLY_CONTAINS]->` | `bot:containsElement` | `https://w3id.org/bot#` | 物理包含关系 |
| `-[:MANAGEMENT_CONTAINS]->` | `bot:containsElement` | `https://w3id.org/bot#` | 管理包含关系（映射到相同 RDF 属性） |
| `-[:SYSTEM_CONTAINS]->` | `bot:containsElement` | `https://w3id.org/bot#` | 系统包含关系（未来扩展） |
| `-[:LOCATED_AT]->` | `bot:hasStorey` | `https://w3id.org/bot#` | 位置关系 |
| `-[:CONNECTED_TO]->` | `ifc:ConnectedTo` | `https://standards.buildingsmart.org/IFC/DEV/IFC4_3/OWL#` | 拓扑连接关系 |
| `-[:HAS_LOT]->` | `bot:containsElement` | `https://w3id.org/bot#` | 检验批关联（映射到相同 RDF 属性） |

**注意**: 三种从属关系在 LPG 层使用不同关系类型以保证查询性能，但在 RDF 映射层可以统一映射到 `bot:containsElement`，因为 RDF 三元组的语义更抽象。

### 6.3 映射实现

映射逻辑在 RDF 映射层实现，将 LPG 查询结果转换为 RDF 三元组，支持导出 IFCOWL。

---

## 7. 数据迁移与备份

### 7.1 数据导出

```cypher
// 导出所有节点和关系
MATCH (n)
OPTIONAL MATCH (n)-[r]->(m)
RETURN n, r, m
```

### 7.2 数据导入

使用 Memgraph 的导入工具或 Cypher 脚本批量导入数据。

### 7.3 备份策略

- **定期备份**: 每日全量备份
- **增量备份**: 每小时增量备份
- **持久化**: 启用 Memgraph 磁盘持久化

---

## 8. 性能优化建议

### 8.1 查询优化

1. **使用索引**: 为常用查询字段创建索引
2. **限制结果集**: 使用 `LIMIT` 限制返回数量
3. **避免全图扫描**: 始终从已知节点开始查询
4. **使用关系方向**: 明确指定关系方向

### 8.2 数据建模优化

1. **合理使用标签**: 避免过多标签导致查询性能下降
2. **属性规范化**: 避免在节点上存储过多冗余数据
3. **关系设计**: 
   - 使用不同关系类型区分三种从属维度（PHYSICALLY_CONTAINS、MANAGEMENT_CONTAINS、SYSTEM_CONTAINS）
   - 明确指定关系方向，避免双向关系
   - 为常用关系模式创建索引（如果 Memgraph 支持关系索引）
4. **多维度查询优化**:
   - 优先使用最符合业务语义的关系类型（如查询物理层级用 PHYSICALLY_CONTAINS）
   - 避免在查询中混用多种关系类型（除非确实需要跨维度查询）
   - 对于需要查询元素的所有父节点的场景，使用 OPTIONAL MATCH 分别查询各维度

---

*文档版本：1.0*  
*最后更新：根据 PRD v4.0 创建*

