---
name: opentruss-architecture
description: OpenTruss 项目架构、设计理念和核心技术栈指南
---

# OpenTruss 架构技能

当你需要了解或修改 OpenTruss 项目的架构、设计决策或技术栈时，参考本技能。

## 核心理念

**"Graph First, Geometry Generated"**（图逻辑优先，几何由生成而来）

OpenTruss 是一个面向建筑施工行业的生成式 BIM 中间件，致力于解决 CAD-to-BIM 逆向重构中的"最后一公里"问题。

## 双模架构 (LPG + RDF)

### Runtime Layer (LPG - 属性图)
- **技术**: Memgraph (Cypher 查询语言)
- **作用**: 高性能计算与状态管理
- **存储内容**:
  - 构件的几何属性、实时状态（Draft/Verified）、置信度
  - 2D 拓扑连接关系
  - 支持复杂的图遍历查询
- **典型场景**: 工程师在前端拖拽墙体节点时，LPG 负责毫秒级更新拓扑关系

### Semantic Layer (RDF - 资源描述框架)
- **技术**: Ontology Mapping (本体映射)
- **作用**: 语义标准化
- **映射规则**: LPG 中的节点标签和关系严格映射 RDF 本体
- **示例**:
  - LPG Node: `:Building` → RDF: `bot:Building`
  - LPG Node: `:Element {speckle_type: "Wall"}` → RDF: `ifc:Wall`
  - LPG Relationship: `-[:CONTAINS]->` → RDF: `bot:containsElement`

## 数据层级（GB50300 标准）

严格遵循 GB50300 工程质量验收标准，六级层级结构：

```
项目 (Project)
  └─ 单体 (Building)
      └─ 分部 (Division)
          └─ 子分部 (SubDivision)
              └─ 分项 (Item)
                  └─ 检验批 (InspectionLot)
                      └─ 构件 (Element)
```

## 技术栈

### 后端
- **Web 框架**: FastAPI 0.100+
- **图数据库**: Memgraph 2.10+
- **Python 版本**: 3.10+
- **数据验证**: Pydantic 2.0+
- **IFC 处理**: ifcopenshell

### 前端
- **框架**: Next.js 14+ (React, 支持 SSR 和客户端渲染)
- **样式**: Tailwind CSS 4.0+
- **语言**: TypeScript 5.0+
- **可视化**: D3.js 7.0+ (2D 拓扑可视化)
- **图形渲染**: Canvas API (高性能渲染)
- **状态管理**: Zustand 4.0+

### 基础设施
- **容器化**: Docker
- **编排**: Docker Compose
- **监控**: Prometheus + Grafana

## 系统分层架构

1. **前端层**: HITL Workbench UI, Canvas 画布, Hierarchy Tree
2. **API 层**: FastAPI 服务, 认证授权, 验证服务
3. **业务逻辑层**: 
   - 数据摄入服务
   - HITL 工作台服务
   - 规则引擎
   - 审批工作流服务
   - IFC 导出服务
   - MEP 路由规划服务
   - 管线综合排布服务
4. **数据层**: Memgraph (LPG 数据库), RDF 映射层

## 关键设计决策

### 宽进严出策略
- **宽进**: 允许 `height`, `material`, `inspection_lot_id` 为空
- **暂存**: 无法确定归属的构件挂载到 Unassigned Item

### HITL 工作台三种模式
- **Trace Mode**: 修复 2D 拓扑
- **Lift Mode**: 批量设置 Z 轴参数
- **Classify Mode**: 拖拽构件归类

### 规则引擎分层防御
- **Phase 1**: 语义校验（防止违反常识的连接）
- **Phase 2**: 构造校验（角度吸附、Z轴完整性检查）
- **Phase 3**: 空间校验（物理碰撞检测）
- **Phase 4**: 拓扑校验（确保系统逻辑闭环）

## 性能指标

- **API 响应时间**: P95 < 200ms
- **图查询性能**: 复杂查询 < 100ms
- **前端交互响应**: 拖拽操作 < 50ms
- **IFC 导出**: 单检验批 < 5s

## 相关文档

- 详细架构文档: `docs/ARCHITECTURE.md`
- 架构决策记录: `docs/adr/`
- 数据模型: `docs/SCHEMA.md`

## 开发注意事项

1. **图查询优化**: 使用索引加速查询，避免全图扫描
2. **异步优先**: 后端使用 `async/await`
3. **类型安全**: 充分利用 TypeScript 和 Pydantic 类型系统
4. **性能要求**: 前端校验必须在 <16ms 内完成（一帧时间）

