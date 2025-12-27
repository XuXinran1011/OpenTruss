---
name: opentruss-gb50300
description: GB50300 工程质量验收标准在 OpenTruss 中的实现和应用指南
---

# GB50300 标准技能

当你需要了解或实现与 GB50300 工程质量验收标准相关的功能时，参考本技能。

## GB50300 标准概述

GB50300 是《建筑工程施工质量验收统一标准》，OpenTruss 严格遵循此标准构建数据层级和验收流程。

## 六级层级结构

OpenTruss 的数据模型完全基于 GB50300 标准，形成以下层级结构：

```
项目 (Project)
  └─ 单体 (Building / Unit Project)
      └─ 分部 (Division)
          └─ 子分部 (SubDivision)
              └─ 分项 (Item)
                  └─ 检验批 (InspectionLot)
                      └─ 构件 (Element)
```

### 层级说明

1. **项目 (Project)**: 整个地块开发项目
2. **单体 (Building)**: 独立的建筑物（如：1#楼）
3. **分部 (Division)**: 按专业性质划分（如：主体结构）
4. **子分部 (SubDivision)**: 按材料或工序划分（如：砌体结构）
5. **分项 (Item)**: 按工种/材料划分（如：填充墙砌体）
6. **检验批 (InspectionLot)**: 核心验收单元，通常是"分项"与"空间（楼层/区域）"的交集
7. **构件 (Element)**: 物理实体（如：ID 为 WALL-101 的那堵墙）

## 数据模型实现

### LPG 节点类型

在 Memgraph 中，每个层级对应一个节点类型：

- `:Project` - 项目节点
- `:Building` - 单体节点
- `:Division` - 分部节点
- `:SubDivision` - 子分部节点
- `:Item` - 分项节点
- `:InspectionLot` - 检验批节点
- `:Element` - 构件节点

### 关系类型

- `-[:CONTAINS]->` - 包含关系（如 Project CONTAINS Building）
- `-[:HAS_LOT]->` - 分项到检验批的关系（Item HAS_LOT InspectionLot）
- `-[:LOCATED_AT]->` - 位置关系（Element LOCATED_AT Level）

### 示例查询

**查询项目的所有检验批**:
```cypher
MATCH (p:Project {id: $project_id})-[:CONTAINS*]->(lot:InspectionLot)
RETURN lot
```

**查询检验批的所有构件**:
```cypher
MATCH (lot:InspectionLot {id: $lot_id})-[:CONTAINS]->(e:Element)
RETURN e
```

## 检验批管理

### 检验批的作用

检验批是连接"物理构件"与"管理验收"的关键环节，是验收的基本单元。

### 检验批创建规则

检验批通常按以下维度划分：

1. **按楼层划分**: 同一分项在不同楼层形成不同检验批
   - 示例: "填充墙砌体 - F1层" vs "填充墙砌体 - F2层"

2. **按区域划分**: 同一分项在同一楼层的不同区域
   - 示例: "填充墙砌体 - F1层 - A区" vs "填充墙砌体 - F1层 - B区"

3. **按施工段划分**: 按施工进度划分
   - 示例: "填充墙砌体 - F1层 - 第一施工段"

### 检验批状态机

检验批遵循以下状态流转：

```
PLANNING (规划中)
  ↓
IN_PROGRESS (清洗中)
  ↓
SUBMITTED (待审批)
  ↓
APPROVED (已验收)
  ↓
PUBLISHED (已发布)
```

### 状态转换规则

- `PLANNING` → `IN_PROGRESS`: 负责人手动更新
- `IN_PROGRESS` → `SUBMITTED`: 负责人提交，触发完整性验证
- `SUBMITTED` → `APPROVED`: 必须通过审批端点完成，由 APPROVER 角色执行
- `APPROVED` → `PUBLISHED`: 负责人手动更新
- **驳回操作**: APPROVER 可将 `SUBMITTED` 驳回至 `IN_PROGRESS`；PM 可将 `SUBMITTED` 或 `APPROVED` 驳回至 `IN_PROGRESS` 或 `PLANNING`

## 验收要求

### 完整性验证

检验批提交审批前，必须满足以下完整性要求：

1. **几何完整性**: 所有构件必须具有完整的几何信息
   - `geometry_2d`: 2D 几何路径
   - `height`: 高度参数
   - `base_offset`: 基础偏移

2. **拓扑完整性**: 所有构件必须形成闭合拓扑
   - 无悬空端点
   - 无孤立子图
   - 连接关系正确

3. **语义完整性**: 构件连接必须符合语义规则
   - 水管不能接柱子
   - 管道系统必须形成闭环

### 规则引擎校验

规则引擎在提交时执行以下校验：

- **语义校验**: 防止违反常识的连接
- **构造校验**: 角度吸附、Z轴完整性检查
- **空间校验**: 物理碰撞检测（2.5D 包围盒）
- **拓扑校验**: 确保系统逻辑闭环

## 实现位置

### 后端实现

- **数据模型**: `backend/app/models/gb50300/`
- **检验批服务**: `backend/app/services/inspection_lot.py`
- **审批服务**: `backend/app/services/approval.py`
- **验证服务**: `backend/app/services/validation.py`

### 前端实现

- **层级树组件**: `frontend/src/components/hierarchy/`
- **检验批管理**: `frontend/src/components/inspection-lot/`
- **审批工作流**: `frontend/src/components/approval/`

## 相关文档

- 数据模型 Schema: `docs/SCHEMA.md`
- 架构文档: `docs/ARCHITECTURE.md`
- 规则引擎: `docs/RULE_ENGINE.md`
- API 文档: `docs/API.md`

## 开发注意事项

1. **严格遵循层级**: 任何数据操作都必须遵循 GB50300 层级结构
2. **状态机约束**: 状态转换必须符合状态机规则
3. **完整性验证**: 提交前必须通过所有完整性验证
4. **规则引擎**: 充分利用规则引擎确保数据质量

