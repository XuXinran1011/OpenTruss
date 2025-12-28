# OpenTruss 架构图文档

本文档包含 OpenTruss 项目的可视化架构图，帮助理解系统的整体设计和数据流转。

## 目录

- [系统整体架构](#系统整体架构)
- [Memgraph 数据模型图](#memgraph-数据模型图)
- [数据流转图](#数据流转图)
- [HITL 工作流时序图](#hitl-工作流时序图)

---

## 系统整体架构

### 架构概览

OpenTruss 采用分层架构设计，从用户界面到数据存储层清晰分层：

```mermaid
graph TB
    subgraph UserLayer["用户层"]
        Editor[数据清洗工程师]
        Approver[专业负责人/总工]
        PM[项目经理]
    end
    
    subgraph FrontendLayer["前端层 (Next.js + React)"]
        Workbench[HITL Workbench<br/>工作台]
        Canvas[Canvas 画布<br/>D3.js/Canvas API]
        HierarchyTree[层级树<br/>GB50300结构]
        ParameterPanel[参数面板]
    end
    
    subgraph APILayer["API 层 (FastAPI)"]
        RESTAPI[RESTful API]
        Auth[认证授权<br/>JWT]
        Validation[请求验证<br/>Pydantic]
    end
    
    subgraph BusinessLayer["业务逻辑层"]
        IngestionService[数据摄入服务]
        WorkbenchService[HITL 工作台服务]
        LotStrategyService[检验批策略服务]
        ApprovalService[审批工作流服务]
        ExportService[IFC 导出服务]
        RuleEngine[规则引擎]
    end
    
    subgraph DataLayer["数据层"]
        Memgraph[Memgraph<br/>LPG 图数据库]
        RDFMapper[RDF 映射层<br/>语义标准化]
    end
    
    subgraph ExternalLayer["外部系统"]
        AIAgent[AI Agent<br/>DWG识别]
        BIMSoftware[Revit/Navisworks<br/>IFC导入]
    end
    
    UserLayer --> FrontendLayer
    FrontendLayer --> APILayer
    APILayer --> BusinessLayer
    BusinessLayer --> DataLayer
    AIAgent --> IngestionService
    ExportService --> BIMSoftware
    DataLayer --> RDFMapper
```

### 组件交互关系

```mermaid
graph LR
    subgraph Client["客户端"]
        Browser[浏览器]
    end
    
    subgraph Server["服务器"]
        Nginx[Nginx<br/>反向代理]
        FastAPI[FastAPI 应用]
        Services[业务服务]
    end
    
    subgraph Database["数据库"]
        Memgraph[(Memgraph<br/>LPG数据库)]
    end
    
    Browser -->|HTTP/WebSocket| Nginx
    Nginx -->|代理请求| FastAPI
    FastAPI -->|调用| Services
    Services -->|Cypher查询| Memgraph
    Memgraph -->|结果返回| Services
    Services -->|响应| FastAPI
    FastAPI -->|HTTP响应| Nginx
    Nginx -->|返回| Browser
```

---

## Memgraph 数据模型图

### Graph-First 理念

OpenTruss 的核心是"Graph First"架构，所有数据以图的形式存储和查询：

```mermaid
graph TB
    Project[Project<br/>项目] -->|CONTAINS| Building[Building<br/>单体]
    Building -->|CONTAINS| Division[Division<br/>分部]
    Division -->|CONTAINS| SubDivision[SubDivision<br/>子分部]
    SubDivision -->|CONTAINS| Item[Item<br/>分项]
    Item -->|HAS_LOT| InspectionLot[InspectionLot<br/>检验批]
    InspectionLot -->|CONTAINS| Element1[Element<br/>构件1]
    InspectionLot -->|CONTAINS| Element2[Element<br/>构件2]
    Element1 -->|CONNECTED_TO| Element2
    Element1 -->|LOCATED_AT| Level[Level<br/>楼层]
    Element2 -->|LOCATED_AT| Level
```

### 构件拓扑关系

在 Trace Mode 中，构件之间的拓扑连接关系：

```mermaid
graph LR
    Wall1[Wall 1<br/>墙体1] -->|CONNECTED_TO| Wall2[Wall 2<br/>墙体2]
    Wall2 -->|CONNECTED_TO| Wall3[Wall 3<br/>墙体3]
    Wall3 -->|CONNECTED_TO| Wall4[Wall 4<br/>墙体4]
    Wall4 -->|CONNECTED_TO| Wall1
    Wall1 -->|CONNECTED_TO| Column1[Column 1<br/>柱子1]
    Wall2 -->|CONNECTED_TO| Column2[Column 2<br/>柱子2]
```

### 检验批层级结构示例

```mermaid
graph TD
    P[项目: 某住宅小区]
    P -->|CONTAINS| B1[1#楼]
    P -->|CONTAINS| B2[2#楼]
    
    B1 -->|CONTAINS| D1[分部: 主体结构]
    D1 -->|CONTAINS| SD1[子分部: 砌体结构]
    SD1 -->|CONTAINS| I1[分项: 填充墙砌体]
    
    I1 -->|HAS_LOT| L1[检验批: F1层填充墙]
    I1 -->|HAS_LOT| L2[检验批: F2层填充墙]
    
    L1 -->|CONTAINS| E1[构件: Wall-001]
    L1 -->|CONTAINS| E2[构件: Wall-002]
    L1 -->|CONTAINS| E3[构件: Wall-003]
```

---

## 数据流转图

### 从 Speckle 到 IFC 的完整流程

```mermaid
sequenceDiagram
    participant AI as AI Agent
    participant Ingestion as 数据摄入服务
    participant Memgraph as Memgraph
    participant Workbench as HITL 工作台
    participant Engineer as 数据工程师
    participant Approval as 审批服务
    participant Export as IFC导出服务
    participant BIM as BIM软件
    
    AI->>Ingestion: 发送识别结果<br/>(Speckle格式)
    Ingestion->>Memgraph: 创建Element节点<br/>(状态: DRAFT)
    Memgraph-->>Ingestion: 确认创建
    
    Note over Engineer,Workbench: Trace Mode: 修复2D拓扑
    Engineer->>Workbench: 拖拽修复拓扑
    Workbench->>Memgraph: 更新CONNECTED_TO关系
    Memgraph-->>Workbench: 返回更新结果
    
    Note over Engineer,Workbench: Lift Mode: 设置Z轴
    Engineer->>Workbench: 批量设置Z轴参数
    Workbench->>Memgraph: 更新Element属性
    Memgraph-->>Workbench: 确认更新
    
    Note over Engineer,Workbench: Classify Mode: 归类构件
    Engineer->>Workbench: 拖拽到层级节点
    Workbench->>Memgraph: 创建关系<br/>(Item HAS Element)
    Memgraph-->>Workbench: 确认关系
    
    Note over Approval: 检验批审批流程
    Workbench->>Approval: 提交检验批审批
    Approval->>Memgraph: 验证完整性
    Memgraph-->>Approval: 返回验证结果
    Approval->>Memgraph: 更新状态<br/>(SUBMITTED)
    
    Approval->>Memgraph: 审批通过
    Memgraph-->>Approval: 状态更新<br/>(APPROVED)
    
    Note over Export,BIM: IFC导出
    Engineer->>Export: 请求导出检验批
    Export->>Memgraph: 查询检验批数据
    Memgraph-->>Export: 返回Element数据
    Export->>Export: 生成3D几何<br/>(2D Lift)
    Export->>Export: 生成IFC文件
    Export-->>BIM: 返回IFC文件
```

### 数据摄入流程（宽进严出）

```mermaid
flowchart TD
    Start[AI Agent识别结果] --> Validate{基本验证}
    Validate -->|通过| CreateElement[创建Element节点]
    Validate -->|失败| Reject[拒绝并记录错误]
    
    CreateElement --> SetStatus[设置状态: DRAFT]
    SetStatus --> StoreGraph[存储到Memgraph]
    
    StoreGraph --> CheckAssignment{是否有item_id?}
    CheckAssignment -->|有| LinkToItem[关联到Item节点]
    CheckAssignment -->|无| Unassigned[暂存到UNASSIGNED_ITEM]
    
    LinkToItem --> End1[数据摄入完成]
    Unassigned --> End2[等待人工分类]
```

---

## HITL 工作流时序图

### Trace Mode: 拓扑修复流程

```mermaid
sequenceDiagram
    participant User as 用户
    participant Canvas as Canvas组件
    participant Workbench as Workbench服务
    participant Memgraph as Memgraph
    participant Topology as 拓扑工具
    
    User->>Canvas: 拖拽墙体节点
    Canvas->>Topology: 计算新坐标
    Topology->>Canvas: 返回更新后坐标
    Canvas->>Workbench: 请求更新拓扑
    Workbench->>Memgraph: 更新CONNECTED_TO关系
    Memgraph->>Memgraph: 验证拓扑完整性
    Memgraph-->>Workbench: 返回更新结果
    Workbench-->>Canvas: 确认更新成功
    Canvas-->>User: 视觉反馈
```

### Classify Mode: 构件归类流程

```mermaid
sequenceDiagram
    participant User as 用户
    participant Canvas as Canvas组件
    participant Hierarchy as 层级树
    participant Workbench as Workbench服务
    participant Memgraph as Memgraph
    
    User->>Canvas: 选择构件
    User->>Hierarchy: 拖拽到Item节点
    Hierarchy->>Workbench: 请求分类
    Workbench->>Memgraph: 查询Item信息
    Memgraph-->>Workbench: 返回Item详情
    Workbench->>Memgraph: 创建关系<br/>(Item)-[:CONTAINS]->(Element)
    Memgraph-->>Workbench: 确认关系创建
    Workbench->>Memgraph: 移除UNASSIGNED关系<br/>(如果存在)
    Memgraph-->>Workbench: 确认移除
    Workbench-->>Hierarchy: 更新UI
    Hierarchy-->>User: 显示更新后的层级
```

### 检验批审批流程

```mermaid
stateDiagram-v2
    [*] --> PLANNING: 创建检验批
    
    PLANNING --> IN_PROGRESS: 开始编辑
    IN_PROGRESS --> PLANNING: 取消编辑
    IN_PROGRESS --> SUBMITTED: 提交审批
    
    SUBMITTED --> APPROVED: 审批通过
    SUBMITTED --> REJECTED: 审批驳回
    
    REJECTED --> IN_PROGRESS: 修改后重新提交
    APPROVED --> PUBLISHED: 发布
    
    PUBLISHED --> [*]
```

---

## 技术栈关系图

### 前端技术栈

```mermaid
graph TB
    NextJS[Next.js 14] --> React[React 18]
    NextJS --> TypeScript[TypeScript]
    NextJS --> Tailwind[Tailwind CSS]
    
    Canvas[Canvas API] --> D3[D3.js<br/>图可视化]
    Canvas --> Topology[拓扑工具<br/>topology.ts]
    
    React --> Zustand[Zustand<br/>状态管理]
    React --> ReactQuery[TanStack Query<br/>数据获取]
    
    NextJS --> Canvas
    NextJS --> Hierarchy[Hierarchy Tree]
    NextJS --> Workbench[HITL Workbench]
```

### 后端技术栈

```mermaid
graph TB
    FastAPI[FastAPI] --> Uvicorn[Uvicorn<br/>ASGI服务器]
    FastAPI --> Pydantic[Pydantic<br/>数据验证]
    
    Services[业务服务] --> FastAPI
    Services --> MemgraphClient[Memgraph Client<br/>neo4j驱动]
    
    MemgraphClient --> Memgraph[(Memgraph<br/>图数据库)]
    
    ExportService[Export Service] --> IFC[ifcopenshell<br/>IFC处理]
    
    Services --> ExportService
    Services --> Auth[JWT认证<br/>python-jose]
```

---

## 部署架构图

### Docker Compose 部署

```mermaid
graph TB
    subgraph DockerHost["Docker Host"]
        subgraph Network["opentruss-network"]
            MemgraphContainer[memgraph:7687<br/>图数据库]
            BackendContainer[backend:8000<br/>FastAPI]
            FrontendContainer[frontend:3000<br/>Next.js]
        end
    end
    
    User[用户浏览器] -->|HTTP:3000| FrontendContainer
    FrontendContainer -->|HTTP:8000| BackendContainer
    BackendContainer -->|Bolt:7687| MemgraphContainer
    BackendContainer -->|HTTP:7444| MemgraphContainer
```

### 生产环境部署（建议）

```mermaid
graph TB
    Internet[互联网] --> Nginx[Nginx<br/>反向代理/负载均衡]
    
    Nginx --> Frontend1[Frontend Pod 1]
    Nginx --> Frontend2[Frontend Pod 2]
    
    Frontend1 --> BackendLB[Backend Load Balancer]
    Frontend2 --> BackendLB
    
    BackendLB --> Backend1[Backend Pod 1]
    BackendLB --> Backend2[Backend Pod 2]
    
    Backend1 --> MemgraphCluster[Memgraph Cluster<br/>主从复制]
    Backend2 --> MemgraphCluster
    
    Backend1 --> Prometheus[Prometheus<br/>监控]
    Backend2 --> Prometheus
    Prometheus --> Grafana[Grafana<br/>可视化]
```

---

## 总结

OpenTruss 的架构设计遵循以下原则：

1. **Graph-First**: 所有数据以图的形式存储和查询，支持复杂的关系遍历
2. **分层清晰**: 前端、API、业务逻辑、数据层职责明确
3. **高性能**: Memgraph 提供毫秒级查询响应
4. **标准化**: RDF 映射确保语义一致性
5. **可扩展**: 支持水平扩展和集群部署

更多架构细节请参考 [ARCHITECTURE.md](../ARCHITECTURE.md)。

---

**最后更新**：2025-12-28  
**文档版本**：1.0  
**维护者**：OpenTruss 开发团队

