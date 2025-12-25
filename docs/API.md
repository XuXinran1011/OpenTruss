# OpenTruss API 设计文档

## 1. 概述

OpenTruss 提供 RESTful API，遵循 OpenAPI 3.0 规范。所有 API 端点使用 JSON 格式进行数据交换。

### 1.1 基础信息

- **Base URL**: `https://api.opentruss.com/api/v1` (生产环境)
- **Base URL**: `http://localhost:8000/api/v1` (开发环境)
- **API 版本**: v1
- **数据格式**: JSON
- **字符编码**: UTF-8

### 1.2 通用约定

#### 请求头

```
Content-Type: application/json
Authorization: Bearer <token>
X-API-Version: v1
```

#### 响应格式

**成功响应** (200 OK):
```json
{
  "status": "success",
  "data": { ... },
  "message": "操作成功"
}
```

**错误响应** (4xx/5xx):
```json
{
  "status": "error",
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述",
    "details": { ... }
  }
}
```

#### 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 409 | 资源冲突 |
| 422 | 验证失败 |
| 500 | 服务器错误 |

---

## 2. 认证与授权

### 2.1 认证方式

使用 JWT (JSON Web Token) 进行认证。

#### 获取 Token

**POST** `/auth/login`

**请求体**:
```json
{
  "username": "editor@example.com",
  "password": "password123"
}
```

**响应**:
```json
{
  "status": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "id": "user_001",
      "username": "editor@example.com",
      "role": "editor"
    }
  }
}
```

### 2.2 角色权限

| 角色 | 权限 |
|------|------|
| `editor` | 数据清洗、构件查询、提交检验批 |
| `approver` | 所有 editor 权限 + 规则定义、审批检验批 |
| `pm` | 所有 approver 权限 + 监控、一键驳回 |

### 2.3 单租户私有化部署说明

OpenTruss 当前版本设计为**单租户私有化部署**，适用于企业内部或项目现场部署场景。

#### 2.3.1 用户管理

**当前方案（最小可用）**：
- 用户信息存储在 Memgraph 中（User 节点）或关系型数据库（SQLite/PostgreSQL）
- 管理员通过初始化脚本或配置文件创建初始用户
- 支持通过 API 进行用户管理（需要 PM 权限）

**未来扩展**：
- 可集成 LDAP/Active Directory（企业内网场景）
- 支持 SAML 2.0 / OAuth2 单点登录（SSO）

#### 2.3.2 JWT Token 配置

**Token 有效期**：
- 默认过期时间：3600 秒（1 小时）
- 可通过环境变量 `JWT_EXPIRATION` 配置

**Token 刷新机制（当前版本）**：
- 客户端在 Token 过期前（如剩余时间 < 300 秒）重新调用登录接口获取新 Token
- 未来版本将支持 Refresh Token 机制

**Token 存储**：
- 客户端：建议存储在内存或安全的 HTTP-only Cookie 中
- 服务端：无状态设计，不存储 Token（验证签名即可）

#### 2.3.3 会话策略

**单点登录（SSO）**：
- 当前版本：不支持 SSO，每个设备独立登录
- 未来扩展：可集成企业 SSO 方案

**并发会话**：
- 当前版本：同一用户可同时在多个设备登录
- 安全考虑：如需限制并发会话，可在 User 节点中存储活跃 Token 列表

#### 2.3.4 操作审计日志

**审计范围**：
- 用户登录/登出
- 数据修改操作（创建/更新/删除构件、检验批）
- 审批操作（提交/审批/驳回）
- 导出操作（IFC 导出）

**审计日志存储**：
- 存储在 Memgraph 中（AuditLog 节点）或关系型数据库
- 日志字段：`user_id`, `action`, `resource_type`, `resource_id`, `timestamp`, `ip_address`, `details`

**审计日志查询 API**（PM 权限）：

**GET** `/api/v1/audit-logs`

**查询参数**:
- `user_id`: 用户 ID（可选）
- `action`: 操作类型（可选）
- `resource_type`: 资源类型（可选）
- `start_time`: 开始时间（可选）
- `end_time`: 结束时间（可选）
- `page`: 页码（默认: 1）
- `page_size`: 每页数量（默认: 50）

**响应示例**:
```json
{
  "status": "success",
  "data": {
    "items": [
      {
        "id": "audit_001",
        "user_id": "user_001",
        "username": "editor@example.com",
        "action": "UPDATE_ELEMENT",
        "resource_type": "Element",
        "resource_id": "element_001",
        "timestamp": "2024-01-01T10:00:00Z",
        "ip_address": "192.168.1.100",
        "details": {
          "changed_fields": ["height", "material"]
        }
      }
    ],
    "total": 100,
    "page": 1,
    "page_size": 50
  }
}
```

---

## 3. 数据模型

### 3.1 Element (构件)

```json
{
  "id": "element_001",
  "speckle_type": "Wall",
  "geometry_2d": {
    "type": "Polyline",
    "coordinates": [[0, 0], [10, 0], [10, 5], [0, 5], [0, 0]]
  },
  "height": 3.0,
  "base_offset": 0.0,
  "material": "concrete",
  "level_id": "level_f1",
  "inspection_lot_id": "lot_001",
  "status": "Draft",
  "confidence": 0.85,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### 3.2 InspectionLot (检验批)

```json
{
  "id": "lot_001",
  "name": "1#楼F1层填充墙砌体检验批",
  "item_id": "item_001",
  "spatial_scope": "Level:F1",
  "status": "IN_PROGRESS",
  "element_count": 25,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

---

## 4. API 端点

### 4.1 数据摄入

#### POST /api/v1/ingest

接收上游 AI Agent 的识别结果，采用"宽进严出"策略。

**支持的 Speckle 元素类型**:
- **建筑元素**: Wall, Floor, Ceiling, Roof, Column
- **结构元素**: Beam, Brace, Structure, Rebar
- **MEP 元素**: Duct, Pipe, CableTray, Conduit, Wire
- **空间元素**: Level, Room, Space, Zone, Area
- **其他元素**: Opening, Topography, GridLine, Profile, Network, View, Alignment, Baseline, Featureline, Station

**请求体**:
```json
{
  "project_id": "project_001",
  "elements": [
    {
      "speckle_id": "speckle_001",
      "speckle_type": "Wall",
      "baseLine": {
        "type": "Polyline",
        "coordinates": [[0, 0], [10, 0], [10, 5], [0, 5], [0, 0]],
        "closed": true
      },
      "height": 3.0,
      "units": "m",
      "level_id": "level_f1"
    },
    {
      "speckle_type": "Beam",
      "baseLine": {
        "type": "Line",
        "coordinates": [[0, 0], [10, 0]]
      },
      "units": "m",
      "level_id": "level_f1"
    }
  ]
}
```

**字段说明**:
- `speckle_type`: Speckle 元素类型（必填）
- `baseLine` / `outline`: 2D 几何数据，支持 Line 或 Polyline 类型
- `height`: 高度（可选，如 Wall 的高度）
- `units`: 单位（可选，如 "m", "ft"）
- `level_id`: 所属楼层 ID（可选，从 Speckle Level 对象转换而来）

**响应** (201 Created):
```json
{
  "status": "success",
  "data": {
    "ingested_count": 1,
    "unassigned_count": 1,
    "element_ids": ["element_001"]
  }
}
```

**错误响应** (422 Validation Error):
```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数验证失败",
    "details": {
      "elements[0].geometry_2d": "几何数据格式错误"
    }
  }
}
```

---

### 4.2 层级结构

#### GET /projects

获取项目列表。

**查询参数**:
- `page`: 页码（默认: 1）
- `page_size`: 每页数量（默认: 20）

**响应**:
```json
{
  "status": "success",
  "data": {
    "items": [
      {
        "id": "project_001",
        "name": "某住宅小区项目",
        "building_count": 3
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

#### GET /api/v1/projects/{project_id}/hierarchy

获取项目的完整层级结构。

**响应**:
```json
{
  "status": "success",
  "data": {
    "project": {
      "id": "project_001",
      "name": "某住宅小区项目",
      "buildings": [
        {
          "id": "building_001",
          "name": "1#楼",
          "divisions": [
            {
              "id": "division_001",
              "name": "主体结构",
              "sub_divisions": [
                {
                  "id": "subdiv_001",
                  "name": "砌体结构",
                  "items": [
                    {
                      "id": "item_001",
                      "name": "填充墙砌体",
                      "inspection_lot_count": 5
                    }
                  ]
                }
              ]
            }
          ]
        }
      ]
    }
  }
}
```

---

### 4.3 构件管理

#### GET /elements

查询构件列表。

**查询参数**:
- `inspection_lot_id`: 检验批 ID（可选）
- `item_id`: 分项 ID（可选）
- `level_id`: 楼层 ID（可选）
- `status`: 状态（Draft/Verified，可选）
- `speckle_type`: 构件类型（可选）
- `has_height`: 是否有高度（可选，布尔值）
- `has_material`: 是否有材质（可选，布尔值）
- `min_confidence`: 最小置信度（可选，0.0-1.0，用于筛选低置信度构件）
- `max_confidence`: 最大置信度（可选，0.0-1.0，用于筛选低置信度构件）
- `page`: 页码（默认: 1）
- `page_size`: 每页数量（默认: 20，最大: 100）

**响应**:
```json
{
  "status": "success",
  "data": {
    "items": [ ... ],
    "total": 100,
    "page": 1,
    "page_size": 20
  }
}
```

#### GET /api/v1/elements/{element_id}

获取单个构件详情。

**响应**:
```json
{
  "status": "success",
  "data": {
    "id": "element_001",
    "speckle_type": "Wall",
    "geometry_2d": { ... },
    "height": 3.0,
    "base_offset": 0.0,
    "material": "concrete",
    "level_id": "level_f1",
    "inspection_lot_id": "lot_001",
    "status": "Verified"
  }
}
```

#### DELETE /api/v1/elements/{element_id}

删除指定的构件及其所有关联关系。

**路径参数**:
- `element_id`: 构件 ID

**响应** (200 OK):
```json
{
  "status": "success",
  "data": {
    "id": "element_001",
    "deleted": true
  }
}
```

**错误响应** (404 Not Found):
```json
{
  "status": "error",
  "error": {
    "code": "NOT_FOUND",
    "message": "Element not found: element_001"
  }
}
```

**注意事项**:
- 删除操作会同时删除该构件的所有关系（如连接关系）
- 删除操作不可撤销，请谨慎使用
- 如果构件已锁定，删除操作会失败

---

#### PATCH /elements/{element_id}

更新构件属性。

**请求体**:
```json
{
  "height": 3.5,
  "base_offset": 0.1,
  "material": "brick"
}
```

**响应** (200 OK):
```json
{
  "status": "success",
  "data": {
    "id": "element_001",
    "updated_fields": ["height", "base_offset", "material"]
  }
}
```

#### PATCH /api/v1/elements/{element_id}/topology

更新构件拓扑关系（Trace Mode）。

**请求体**:
```json
{
  "geometry_2d": {
    "type": "Polyline",
    "coordinates": [[0, 0], [10, 0], [10, 5], [0, 5], [0, 0]],
    "closed": true
  },
  "connected_elements": ["element_002", "element_003"]
}
```

**字段说明**:

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `geometry_2d` | Geometry2D | 否 | 更新的 2D 几何数据（Line/Polyline） |
| `connected_elements` | string[] | 否 | 连接的构件 ID 列表 |

**请求示例**:
```json
{
  "geometry_2d": {
    "type": "Line",
    "coordinates": [[0, 0], [10, 0]],
    "closed": false
  },
  "connected_elements": ["element_002"]
}
```

**响应**:
```json
{
  "status": "success",
  "data": {
    "id": "element_001",
    "topology_updated": true
  }
}
```

**响应字段说明**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | string | 更新的构件 ID |
| `topology_updated` | boolean | 是否成功更新拓扑 |

**注意事项**:

- 当 `connection_mode` 不为 `align_only` 时，必须提供 `target_endpoint_info` 和 `target_element_id`
- 创建的连接段会从源构件继承 `level_id`、`inspection_lot_id`、`material` 等属性
- 对于 `update_to_diagonal` 模式，系统会自动计算新的 `height` 和 `base_offset` 参数

#### POST /api/v1/elements/batch-lift

批量设置 Z 轴参数（Lift Mode）。

**请求体**:
```json
{
  "element_ids": ["element_001", "element_002"],
  "height": 3.0,
  "base_offset": 0.0
}
```

**响应**:
```json
{
  "status": "success",
  "data": {
    "updated_count": 2
  }
}
```

#### POST /api/v1/elements/{element_id}/classify

将构件归类到分项（Classify Mode）。

**请求体**:
```json
{
  "item_id": "item_001"
}
```

**响应**:
```json
{
  "status": "success",
  "data": {
    "element_id": "element_001",
    "item_id": "item_001"
  }
}
```

---

### 4.4 检验批管理

#### GET /inspection-lots

查询检验批列表。

**查询参数**:
- `item_id`: 分项 ID（可选）
- `status`: 状态（PLANNING/IN_PROGRESS/SUBMITTED/APPROVED/PUBLISHED，可选）
- `page`: 页码
- `page_size`: 每页数量

**响应**:
```json
{
  "status": "success",
  "data": {
    "items": [
      {
        "id": "lot_001",
        "name": "1#楼F1层填充墙砌体检验批",
        "item_id": "item_001",
        "spatial_scope": "Level:F1",
        "status": "IN_PROGRESS",
        "element_count": 25
      }
    ],
    "total": 10,
    "page": 1,
    "page_size": 20
  }
}
```

#### GET /api/v1/inspection-lots/{lot_id}

获取检验批详情。

**响应**:
```json
{
  "status": "success",
  "data": {
    "id": "lot_001",
    "name": "1#楼F1层填充墙砌体检验批",
    "item_id": "item_001",
    "spatial_scope": "Level:F1",
    "status": "IN_PROGRESS",
    "elements": [ ... ],
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

#### POST /api/v1/inspection-lots/strategy

创建检验批策略（Approver 权限）。

**请求体**:
```json
{
  "item_id": "item_001",
  "rule": {
    "type": "by_level",
    "spatial_dimension": "Level"
  },
  "name_template": "{building}楼{level}层{item}检验批"
}
```

**响应** (201 Created):
```json
{
  "status": "success",
  "data": {
    "created_lots": [
      {
        "id": "lot_001",
        "name": "1#楼F1层填充墙砌体检验批",
        "element_count": 25
      },
      {
        "id": "lot_002",
        "name": "1#楼F2层填充墙砌体检验批",
        "element_count": 30
      }
    ],
    "total_created": 2
  }
}
```

#### POST /api/v1/inspection-lots/{lot_id}/elements

手动添加构件到检验批（人工微调）。

**请求体**:
```json
{
  "element_ids": ["element_001", "element_002"]
}
```

**响应**:
```json
{
  "status": "success",
  "data": {
    "lot_id": "lot_001",
    "added_count": 2
  }
}
```

#### DELETE /api/v1/inspection-lots/{lot_id}/elements/{element_id}

从检验批中移除构件。

**响应**:
```json
{
  "status": "success",
  "data": {
    "lot_id": "lot_001",
    "element_id": "element_001",
    "removed": true
  }
}
```

---

### 4.5 审批工作流

#### POST /api/v1/inspection-lots/{lot_id}/submit

提交检验批审批（Editor 权限）。

**响应** (200 OK):
```json
{
  "status": "success",
  "data": {
    "lot_id": "lot_001",
    "status": "SUBMITTED",
    "message": "检验批已提交审批"
  }
}
```

**错误响应** (422 Validation Error):
```json
{
  "status": "error",
  "error": {
    "code": "INCOMPLETE_ELEMENTS",
    "message": "检验批包含不完整的构件",
    "details": {
      "incomplete_elements": [
        {
          "element_id": "element_001",
          "missing_fields": ["height", "material"]
        }
      ]
    }
  }
}
```

#### POST /api/v1/inspection-lots/{lot_id}/approve

审批通过检验批（Approver 权限）。

**请求体**:
```json
{
  "comment": "验收通过"
}
```

**响应**:
```json
{
  "status": "success",
  "data": {
    "lot_id": "lot_001",
    "status": "APPROVED"
  }
}
```

#### POST /api/v1/inspection-lots/{lot_id}/reject

驳回检验批。

**请求体**:
```json
{
  "reason": "数据质量问题",
  "reject_level": "IN_PROGRESS"
}
```

**响应**:
```json
{
  "status": "success",
  "data": {
    "lot_id": "lot_001",
    "status": "IN_PROGRESS",
    "reason": "数据质量问题"
  }
}
```

**权限说明**:
- Approver 可驳回至 `IN_PROGRESS`
- PM 可驳回至 `IN_PROGRESS` 或 `PLANNING`

#### PATCH /api/v1/lots/{lot_id}/status

更新检验批状态。

**请求体**:
```json
{
  "status": "SUBMITTED"
}
```

**响应**:
```json
{
  "status": "success",
  "data": {
    "lot_id": "lot_001",
    "old_status": "IN_PROGRESS",
    "new_status": "SUBMITTED",
    "updated_at": "2025-01-01T12:00:00"
  }
}
```

**状态转换规则**:

允许的转换：
- `PLANNING` → `IN_PROGRESS`
- `IN_PROGRESS` → `SUBMITTED`
- `APPROVED` → `PUBLISHED`

**重要限制**:
- `SUBMITTED` → `APPROVED` **不能**通过此端点完成，必须使用审批端点 `/api/v1/lots/{lot_id}/approve`
- 这确保了审批流程的完整性，避免绕过审批步骤

**完整性验证**:
- 当状态转换为 `SUBMITTED` 时，系统会自动验证检验批内所有构件是否具备完整的几何信息（高度、材质、几何数据）
- 如果有构件数据不完整，状态转换将失败并返回错误

**错误响应** (400 Bad Request):
```json
{
  "detail": "Invalid status transition from SUBMITTED to APPROVED"
}
```

或（完整性验证失败）:
```json
{
  "detail": "Cannot submit lot: 5 elements are missing required data (height, material, or geometry_2d)"
}
```

---

### 4.6 IFC 导出

#### GET /api/v1/export/ifc

导出 IFC 模型。

**查询参数**:
- `inspection_lot_id`: 检验批 ID（可选，不指定则导出整个项目）
- `format`: 导出格式（默认: ifc）

**响应** (200 OK):
- Content-Type: `application/octet-stream`
- Content-Disposition: `attachment; filename="project_001.ifc"`

**错误响应** (422 Validation Error):
```json
{
  "status": "error",
  "error": {
    "code": "EXPORT_ERROR",
    "message": "检验批状态必须为 APPROVED 才能导出"
  }
}
```

---

### 4.8 规则引擎校验 API

规则引擎提供多层次的校验功能，确保数据质量。详细架构设计请参考 [规则引擎架构文档](RULE_ENGINE.md)。

#### POST /api/v1/validation/semantic-check

语义连接校验（规则引擎 Phase 1）。检查构件类型之间的连接是否合法。

**请求体**:
```json
{
  "connections": [
    {
      "source_type": "Objects.BuiltElements.Pipe",
      "target_type": "Objects.BuiltElements.Valve"
    },
    {
      "source_type": "Objects.BuiltElements.Pipe",
      "target_type": "Objects.BuiltElements.Column"
    }
  ]
}
```

**响应** (200 OK):
```json
{
  "status": "success",
  "data": {
    "valid": true,
    "invalid_connections": []
  }
}
```

**错误响应** (422 Validation Error):
```json
{
  "status": "error",
  "error": {
    "code": "INVALID_CONNECTIONS",
    "message": "存在无效的连接",
    "details": {
      "invalid_connections": [
        {
          "source_type": "Objects.BuiltElements.Pipe",
          "target_type": "Objects.BuiltElements.Column",
          "reason": "Invalid connection: Objects.BuiltElements.Pipe cannot connect to Objects.BuiltElements.Column"
        }
      ]
    }
  }
}
```

#### POST /api/v1/validation/completeness-check

完整性校验（规则引擎 Phase 2）。检查构件的 Z 轴完整性（height、base_offset）。

**请求体**:
```json
{
  "element_ids": ["element_001", "element_002"]
}
```

**响应** (200 OK):
```json
{
  "status": "success",
  "data": {
    "valid": true,
    "incomplete_elements": []
  }
}
```

**错误响应** (422 Validation Error):
```json
{
  "status": "error",
  "error": {
    "code": "INCOMPLETE_ELEMENTS",
    "message": "存在不完整的构件",
    "details": {
      "incomplete_elements": [
        {
          "element_id": "element_001",
          "missing_fields": ["height", "base_offset"],
          "element_type": "Wall"
        }
      ]
    }
  }
}
```

#### GET /api/v1/validation/topology-check

拓扑完整性校验（规则引擎 Phase 4）。检查是否存在悬空端点或孤立子图。

**查询参数**:
- `lot_id`: 检验批 ID（可选，不指定则检查整个项目）

**响应** (200 OK):
```json
{
  "status": "success",
  "data": {
    "valid": true,
    "open_ends": [],
    "isolated_elements": []
  }
}
```

**错误响应** (422 Validation Error):
```json
{
  "status": "error",
  "error": {
    "code": "TOPOLOGY_ERRORS",
    "message": "存在拓扑错误",
    "details": {
      "open_ends": [
        {
          "element_id": "pipe_001",
          "degree": 1,
          "reason": "Open pipe end detected"
        }
      ],
      "isolated_elements": [
        {
          "element_id": "pipe_002",
          "reason": "Isolated element"
        }
      ]
    }
  }
}
```

#### GET /api/v1/rules/config

获取规则配置（前端使用）。

**查询参数**:
- `type`: 配置类型 (`semantic` | `fitting` | `all`，默认: `all`)

**响应** (200 OK):
```json
{
  "status": "success",
  "data": {
    "version": "1.0",
    "semantic_allowlist": {
      "Objects.BuiltElements.Pipe": [
        "Objects.BuiltElements.Pipe",
        "Objects.BuiltElements.Valve"
      ]
    },
    "fitting_standards": {
      "angles": {
        "standard": [90, 45, 180],
        "tolerance": 5,
        "allow_custom": false
      }
    }
  }
}
```

**权限说明**:
- 所有已认证用户都可以获取规则配置
- 配置信息不包含敏感数据，可以安全地暴露给前端

---

### 4.9 监控与统计

#### GET /api/v1/dashboard/stats

获取监控统计信息（PM 权限）。

**响应**:
```json
{
  "status": "success",
  "data": {
    "project_count": 5,
    "inspection_lot_stats": {
      "PLANNING": 10,
      "IN_PROGRESS": 25,
      "SUBMITTED": 5,
      "APPROVED": 50,
      "PUBLISHED": 20
    },
    "element_stats": {
      "total": 1000,
      "verified": 800,
      "draft": 200
    }
  }
}
```

#### GET /api/v1/dashboard/progress

获取验收进度（PM 权限）。

**查询参数**:
- `project_id`: 项目 ID（可选）
- `division_id`: 分部 ID（可选）

**响应**:
```json
{
  "status": "success",
  "data": {
    "progress_by_division": [
      {
        "division_id": "division_001",
        "division_name": "主体结构",
        "total_lots": 50,
        "approved_lots": 30,
        "progress_percentage": 60
      }
    ]
  }
}
```

---

## 5. 错误码参考

| 错误码 | HTTP 状态码 | 说明 |
|--------|------------|------|
| `VALIDATION_ERROR` | 422 | 请求参数验证失败 |
| `UNAUTHORIZED` | 401 | 未授权 |
| `FORBIDDEN` | 403 | 无权限 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `INCOMPLETE_ELEMENTS` | 422 | 构件信息不完整 |
| `INVALID_STATE_TRANSITION` | 409 | 无效的状态转换 |
| `EXPORT_ERROR` | 422 | 导出失败 |
| `INTERNAL_ERROR` | 500 | 服务器内部错误 |

---

## 6. API 版本管理

### 6.1 版本策略

- 使用 URL 路径版本控制：`/api/v1/`, `/api/v2/`
- 向后兼容：新版本应保持对旧版本 API 的支持
- 废弃通知：提前 3 个月通知 API 废弃

### 6.2 版本变更

- **v1.0**: 初始版本
- 未来版本将根据需求演进

---

## 7. 限流策略

### 7.1 限流规则

- **认证端点**: 5 次/分钟
- **查询端点**: 100 次/分钟
- **写入端点**: 30 次/分钟
- **导出端点**: 10 次/分钟

### 7.2 限流响应

```json
{
  "status": "error",
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "请求过于频繁，请稍后再试",
    "retry_after": 60
  }
}
```

---

## 8. Webhook 支持（未来）

未来版本将支持 Webhook，用于通知外部系统状态变更。

---

---

## 5. 错误代码定义

### 5.1 通用错误代码

| 错误代码 | HTTP 状态码 | 说明 |
|---------|-----------|------|
| `UNAUTHORIZED` | 401 | 未授权，需要登录 |
| `FORBIDDEN` | 403 | 无权限访问该资源 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `VALIDATION_ERROR` | 422 | 请求参数验证失败 |
| `INTERNAL_ERROR` | 500 | 服务器内部错误 |

### 5.2 规则引擎错误代码

| 错误代码 | HTTP 状态码 | 说明 | 示例场景 |
|---------|-----------|------|---------|
| `INVALID_CONNECTIONS` | 422 | 存在无效的构件连接 | 规则引擎 Phase 1: 语义校验失败，如 Pipe 连接到 Column |
| `INCOMPLETE_ELEMENTS` | 422 | 构件数据不完整 | 规则引擎 Phase 2: Wall 或 Column 缺少 height 字段 |
| `TOPOLOGY_ERRORS` | 422 | 拓扑结构错误 | 规则引擎 Phase 4: 存在悬空端点或孤立子图 |
| `NON_STANDARD_ANGLE` | 422 | 角度不符合标准（警告，非阻断） | 规则引擎 Phase 2: 角度不在标准列表中（如果 allow_custom=false） |
| `SPATIAL_CLASH` | 422 | 空间碰撞（警告，非阻断） | 规则引擎 Phase 3: 构件之间发生重叠 |

### 5.3 错误响应格式

所有错误响应遵循以下格式：

```json
{
  "status": "error",
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述（用户友好）",
    "details": {
      // 可选的详细错误信息
    }
  }
}
```

**示例**：

```json
{
  "status": "error",
  "error": {
    "code": "INVALID_CONNECTIONS",
    "message": "存在无效的连接",
    "details": {
      "invalid_connections": [
        {
          "source_type": "Objects.BuiltElements.Pipe",
          "target_type": "Objects.BuiltElements.Column",
          "reason": "Invalid connection: Objects.BuiltElements.Pipe cannot connect to Objects.BuiltElements.Column"
        }
      ]
    }
  }
}
```

---

*文档版本：1.0*  
*最后更新：根据 PRD v4.0 创建*

