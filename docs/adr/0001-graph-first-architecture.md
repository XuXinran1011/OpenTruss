# ADR-0001: Graph-First 架构决策

## 状态

**已采纳** - 2025-01-01

## 背景

OpenTruss 项目需要处理复杂的建筑构件关系和层级结构。传统的关系型数据库在面对以下场景时存在局限性：

1. **复杂关系查询**: 需要频繁查询构件之间的拓扑连接关系
2. **层级结构**: GB50300 标准的六级层级结构（Project → Building → Division → ... → Element）
3. **实时更新**: 用户在 Canvas 中拖拽修复拓扑时需要毫秒级响应
4. **图遍历**: 规则引擎需要执行复杂的图遍历查询来聚合构件

## 决策

采用 **Graph-First** 架构，使用 Memgraph（LPG - Labeled Property Graph）作为主要数据存储。

### 核心原则

1. **所有数据以图的形式存储**: Element、Item、InspectionLot 等都是图中的节点
2. **关系是一等公民**: CONTAINS、CONNECTED_TO、HAS_LOT 等关系是数据模型的核心
3. **几何数据作为属性**: 几何信息存储在节点属性中，而非单独的表
4. **查询优先**: 所有查询操作都通过 Cypher 图查询语言执行

## 理由

### 优势

1. **性能优势**:
   - 图遍历查询在 LPG 中性能优异（O(1) 关系查找）
   - 支持复杂的多跳查询（如查找某个 Item 下的所有 Element）
   - 毫秒级响应时间满足实时交互需求

2. **数据模型匹配**:
   - GB50300 层级结构天然适合图模型
   - 构件拓扑关系（CONNECTED_TO）在图模型中表达更直观
   - 检验批与构件的多对多关系用图表示更清晰

3. **查询灵活性**:
   - Cypher 查询语言表达力强，易于实现复杂业务逻辑
   - 支持规则引擎的图遍历查询
   - 易于扩展新的节点类型和关系类型

4. **可视化友好**:
   - 图数据可以直接映射到 D3.js 可视化
   - 前端 Canvas 的交互操作与后端图操作对应关系清晰

### 劣势

1. **学习曲线**: 团队需要学习 Cypher 查询语言
2. **工具生态**: Memgraph 的工具生态不如 PostgreSQL 成熟
3. **事务支持**: 图数据库的事务语义与传统关系型数据库不同

### 权衡

- **vs 关系型数据库 (PostgreSQL)**: 
  - 关系型数据库在处理复杂关系查询时需要多次 JOIN，性能较差
  - 图数据库在关系查询方面有天然优势

- **vs 文档数据库 (MongoDB)**:
  - 文档数据库适合文档存储，但不适合复杂关系查询
  - 图数据库更适合我们的场景（关系密集型）

- **vs Neo4j**:
  - Memgraph 性能更好，内存占用更小
  - Memgraph 兼容 Neo4j 的 Bolt 协议，迁移成本低
  - Memgraph 开源版本功能完整

## 后果

### 正面影响

1. **开发效率提升**: 复杂的关系查询代码更简洁
2. **性能优异**: 满足了实时交互的性能要求
3. **架构清晰**: Graph-First 理念贯穿整个系统设计

### 负面影响

1. **团队学习成本**: 需要培训团队使用 Cypher
2. **运维复杂度**: 需要专门的 Memgraph 运维知识

### 需要采取的行动

1. ✅ 选择 Memgraph 作为图数据库
2. ✅ 设计图数据模型（节点类型、关系类型）
3. ✅ 实现 MemgraphClient 封装层
4. ✅ 编写 Cypher 查询工具函数
5. ⏳ 培训团队使用 Cypher
6. ⏳ 建立 Memgraph 监控和运维流程

## 参考

- [Memgraph Documentation](https://memgraph.com/docs)
- [Cypher Query Language](https://neo4j.com/developer/cypher/)
- [Graph Databases in Production](https://memgraph.com/blog/graph-databases-production)

