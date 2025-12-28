# OpenTruss 系统设计图表

本文档包含 OpenTruss 系统的核心设计图表，用于指导系统开发和团队协作。

---

## 1. 检验批状态机图 (Inspection Lot State Machine)

检验批是 OpenTruss 的核心验收单元，其状态流转遵循严格的工程管理规范。

```mermaid
stateDiagram-v2
    [*] --> PLANNING: 创建检验批
    
    PLANNING --> IN_PROGRESS: 检验批创建完成\n(Approver 完成规则配置)
    
    IN_PROGRESS --> IN_PROGRESS: Editor 数据清洗\n(Trace/Lift/Classify)
    
    IN_PROGRESS --> SUBMITTED: 所有构件完整性验证通过\n✓ 高度(height)\n✓ 材质(material)\n✓ 闭合拓扑(closed_topology)
    
    SUBMITTED --> APPROVED: Approver 审批通过
    
    SUBMITTED --> IN_PROGRESS: Approver 驳回\n(需修正数据)
    
    APPROVED --> PUBLISHED: 导出 IFC 完成
    
    APPROVED --> IN_PROGRESS: PM 一键驳回\n(熔断机制)
    
    APPROVED --> PLANNING: PM 一键驳回\n(严重问题需重新规划)
    
    PUBLISHED --> [*]: 流程结束
    
    note right of IN_PROGRESS
        阻断逻辑：
        只有当检验批内所有构件
        都具备完整几何信息时，
        才允许提交审批
    end note
    
    note right of SUBMITTED
        审批节点：
        Approver 可批准或驳回
        PM 拥有熔断权限
    end note
```

### 状态说明

- **PLANNING（规划中）**：检验批已创建，但尚未开始数据清洗工作
- **IN_PROGRESS（清洗中）**：Editor 正在进行数据清洗、参数补全和拓扑修复
- **SUBMITTED（待审批）**：数据完整性验证通过，等待 Approver 审批
- **APPROVED（已验收）**：Approver 审批通过，检验批已验收
- **PUBLISHED（已发布）**：IFC 模型已成功导出，流程完成

### 关键转换条件

1. **PLANNING → IN_PROGRESS**：Approver 完成检验批规则配置，系统自动创建检验批节点
2. **IN_PROGRESS → SUBMITTED**：系统验证所有构件具备完整几何信息（高度、材质、闭合拓扑）
3. **SUBMITTED → APPROVED**：Approver 审批通过
4. **驳回路径**：
   - Approver 可驳回至 IN_PROGRESS（需修正数据）
   - PM 可一键驳回至 IN_PROGRESS 或 PLANNING（熔断机制）

---

## 2. 业务流程泳道图 (Business Process Swimlane)

展示从数据摄入到 IFC 导出的完整业务流程，涉及多个角色的协作。

```mermaid
flowchart TD
    subgraph AI_Agent["🤖 AI Agent (上游系统)"]
        A1[识别施工图 DWG]
        A2[生成非结构化识别结果]
        A3[发送 Speckle Objects]
    end
    
    subgraph System["⚙️ System (系统自动处理)"]
        S1[接收 POST /ingest]
        S2[宽进策略：允许空值]
        S3[暂存到 Unassigned Item]
        S4[规则引擎执行]
        S5[自动聚合构件]
        S6[创建 Inspection Lot 节点]
        S7[验证完整性]
        S8[生成 IFC 模型]
    end
    
    subgraph Editor["👷 Editor (分部工程师)"]
        E1[打开 HITL Workbench]
        E2[Trace Mode: 修复 2D 拓扑]
        E3[Lift Mode: 批量设置 Z 轴]
        E4[Classify Mode: 拖拽归类]
        E5[提交检验批]
    end
    
    subgraph Approver["👔 Approver (专业负责人/总工)"]
        AP1[选择分项工程]
        AP2[定义划分规则]
        AP3[配置空间维度]
        AP4[人工微调构件]
        AP5[审批检验批]
    end
    
    subgraph PM["📊 PM (项目经理)"]
        P1[监控验收进度]
        P2[查看各分部状态]
        P3[一键驳回]
    end
    
    A1 --> A2
    A2 --> A3
    A3 -->|POST /ingest| S1
    S1 --> S2
    S2 --> S3
    
    S3 --> E1
    E1 --> E2
    E2 --> E3
    E3 --> E4
    E4 --> E5
    
    E5 --> AP1
    AP1 --> AP2
    AP2 --> AP3
    AP3 --> S4
    S4 --> S5
    S5 --> S6
    S6 --> AP4
    AP4 --> S7
    S7 --> AP5
    
    AP5 -->|审批通过| S8
    AP5 -->|驳回| E2
    
    S8 --> P1
    P1 --> P2
    P2 -->|发现问题| P3
    P3 -->|熔断| E2
    
    style AI_Agent fill:#e1f5ff
    style System fill:#f0f0f0
    style Editor fill:#fff4e6
    style Approver fill:#e8f5e9
    style PM fill:#fce4ec
```

### 流程阶段说明

1. **数据摄入阶段**：AI Agent 识别施工图并发送识别结果，系统采用"宽进严出"策略接收数据
2. **数据清洗阶段**：Editor 在 HITL Workbench 中进行 Trace、Lift、Classify 操作
3. **检验批策划阶段**：Approver 定义划分规则，系统自动聚合构件并创建检验批
4. **审批阶段**：Approver 审批检验批，PM 监控进度并拥有熔断权限
5. **导出阶段**：系统生成 IFC 模型，完成整个流程

---

## 3. 系统交互时序图 (System Interaction Sequence)

### 3.1 检验批创建流程

展示 Approver 创建检验批时，系统各组件之间的交互时序。

```mermaid
sequenceDiagram
    participant Approver as Approver<br/>(专业负责人)
    participant Frontend as Frontend<br/>(HITL Workbench)
    participant API as FastAPI<br/>(后端服务)
    participant RuleEngine as Rule Engine<br/>(规则引擎)
    participant Memgraph as Memgraph<br/>(LPG 数据库)
    
    Approver->>Frontend: 选择分项工程<br/>(如：填充墙砌体)
    Frontend->>API: GET /api/v1/items/{item_id}/elements
    
    API->>Memgraph: MATCH (item:Item)-[:CONTAINS]->(e:Element)<br/>WHERE item.id = $item_id<br/>RETURN e
    Memgraph-->>API: 返回符合条件的构件列表
    API-->>Frontend: 返回构件数据
    
    Frontend->>Approver: 显示构件列表和空间维度选项
    Approver->>Frontend: 定义划分规则<br/>(按 Level 或 Zone 拆分)
    
    Frontend->>API: POST /api/v1/inspection-lots/strategy<br/>{item_id, rule: "by_level"}
    
    API->>RuleEngine: 执行规则引擎<br/>IF Element.level == 'F1' AND<br/>Element.type == 'Wall'<br/>THEN Assign To Lot_001
    
    RuleEngine->>Memgraph: 查询符合条件的构件<br/>MATCH (e:Element)<br/>WHERE e.level_id = 'F1'<br/>AND e.speckle_type = 'Wall'
    Memgraph-->>RuleEngine: 返回构件集合
    
    RuleEngine->>Memgraph: 创建 InspectionLot 节点<br/>CREATE (lot:InspectionLot {<br/>  id: $lot_id,<br/>  name: "1#楼F1层填充墙砌体检验批",<br/>  status: "PLANNING"<br/>})
    
    RuleEngine->>Memgraph: 建立关系<br/>MATCH (item:Item), (lot:InspectionLot),<br/>(e:Element)<br/>WHERE item.id = $item_id<br/>AND lot.id = $lot_id<br/>AND e.id IN $element_ids<br/>CREATE (item)-[:HAS_LOT]->(lot),<br/>(lot)-[:CONTAINS]->(e)
    
    Memgraph-->>RuleEngine: 确认创建成功
    RuleEngine-->>API: 返回检验批信息
    API-->>Frontend: 返回创建结果
    Frontend-->>Approver: 显示检验批创建成功<br/>可进行人工微调
```

### 3.2 审批提交流程

展示 Editor 提交检验批审批时，系统验证和状态更新的完整流程。

```mermaid
sequenceDiagram
    participant Editor as Editor<br/>(分部工程师)
    participant Frontend as Frontend<br/>(HITL Workbench)
    participant API as FastAPI<br/>(后端服务)
    participant ValidationService as Validation Service<br/>(完整性验证)
    participant Memgraph as Memgraph<br/>(LPG 数据库)
    participant NotificationService as Notification Service<br/>(通知服务)
    participant Approver as Approver<br/>(专业负责人)
    
    Editor->>Frontend: 完成数据清洗<br/>点击"提交审批"
    Frontend->>API: POST /api/v1/inspection-lots/{lot_id}/submit
    
    API->>Memgraph: 查询检验批及其构件<br/>MATCH (lot:InspectionLot)-[:CONTAINS]->(e:Element)<br/>WHERE lot.id = $lot_id<br/>RETURN lot, collect(e) as elements
    Memgraph-->>API: 返回检验批和构件数据
    
    API->>ValidationService: 验证完整性<br/>validate_completeness(elements)
    
    ValidationService->>ValidationService: 检查每个构件：<br/>✓ height IS NOT NULL<br/>✓ material IS NOT NULL<br/>✓ geometry_2d.is_closed == true
    
    alt 验证通过
        ValidationService-->>API: 验证通过
        API->>Memgraph: 更新检验批状态<br/>MATCH (lot:InspectionLot)<br/>WHERE lot.id = $lot_id<br/>SET lot.status = "SUBMITTED"
        Memgraph-->>API: 确认更新
        
        API->>NotificationService: 发送通知<br/>notify_approver(lot_id, approver_id)
        NotificationService->>Approver: 推送通知<br/>"检验批待审批"
        
        API-->>Frontend: 返回成功<br/>{status: "SUBMITTED", message: "已提交审批"}
        Frontend-->>Editor: 显示提交成功
        
    else 验证失败
        ValidationService-->>API: 验证失败<br/>{missing_fields: ["height", "material"]}
        API-->>Frontend: 返回错误<br/>{error: "完整性验证失败",<br/>details: missing_fields}
        Frontend-->>Editor: 显示错误提示<br/>"请补全缺失的字段"
    end
```

### 3.3 PM 熔断流程

展示 PM 执行一键驳回操作时的系统交互。

```mermaid
sequenceDiagram
    participant PM as PM<br/>(项目经理)
    participant Frontend as Dashboard<br/>(监控面板)
    participant API as FastAPI<br/>(后端服务)
    participant Memgraph as Memgraph<br/>(LPG 数据库)
    participant NotificationService as Notification Service<br/>(通知服务)
    participant Editor as Editor<br/>(分部工程师)
    
    PM->>Frontend: 查看验收进度<br/>发现异常
    Frontend->>API: GET /api/v1/inspection-lots?status=SUBMITTED
    API->>Memgraph: 查询待审批检验批
    Memgraph-->>API: 返回检验批列表
    API-->>Frontend: 返回数据
    Frontend-->>PM: 显示进度和异常
    
    PM->>Frontend: 选择检验批<br/>点击"一键驳回"
    Frontend->>API: POST /api/v1/inspection-lots/{lot_id}/reject<br/>{reject_level: "IN_PROGRESS",<br/>reason: "数据质量问题"}
    
    API->>API: 验证 PM 权限<br/>check_pm_permission(user_id)
    
    API->>Memgraph: 更新检验批状态<br/>MATCH (lot:InspectionLot)<br/>WHERE lot.id = $lot_id<br/>SET lot.status = $reject_level,<br/>lot.reject_reason = $reason
    
    Memgraph-->>API: 确认更新
    
    API->>Memgraph: 解锁构件状态<br/>MATCH (lot:InspectionLot)-[:CONTAINS]->(e:Element)<br/>WHERE lot.id = $lot_id<br/>SET e.locked = false
    
    API->>NotificationService: 发送通知<br/>notify_editor(lot_id, editor_id, reason)
    NotificationService->>Editor: 推送通知<br/>"检验批已被驳回，需重新清洗"
    
    API-->>Frontend: 返回成功
    Frontend-->>PM: 显示驳回成功
```

---

## 图表使用说明

### 状态机图
- 用于理解检验批的完整生命周期
- 指导状态转换逻辑的实现
- 明确各角色的操作权限

### 泳道图
- 用于理解端到端的业务流程
- 明确各角色的职责边界
- 指导功能模块的划分

### 时序图
- 用于理解系统组件的交互细节
- 指导 API 设计和数据库操作
- 明确数据流转路径

---

## 技术实现要点

1. **状态机实现**：建议使用状态模式（State Pattern）或状态机库（如 Python 的 `transitions`）
2. **规则引擎**：建议使用可配置的规则引擎（如 `pyknow` 或自定义 DSL）
3. **验证服务**：建议将完整性验证逻辑独立为服务，便于测试和维护
4. **通知机制**：建议使用消息队列（如 RabbitMQ）实现异步通知

---

**最后更新**：2025-12-28  
**文档版本**：1.0  
**维护者**：OpenTruss 开发团队

