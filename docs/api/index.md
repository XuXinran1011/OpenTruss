# OpenTruss API 参考文档

本文档提供 OpenTruss RESTful API 的完整参考。所有 API 遵循 OpenAPI 3.0 规范，使用 JSON 格式进行数据交换。

## 快速导航

- [API 使用指南](usage.md) - API 快速开始和使用示例
- [支吊架 API](hangers.md) - 支吊架生成和管理 API
- [本文档](#) - API 完整参考（设计文档）

---

## 1. 概述

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

详细的认证配置和用户管理说明请参考 [API 使用指南](usage.md#认证流程)。

---

## 3. 数据模型

### 3.1 Element (构件)

```json
{
  "id": "element_001",
  "speckle_id": "speckle_abc123",
  "speckle_type": "Wall",
  "geometry": {
    "type": "Polyline",
    "coordinates": [[0, 0], [10, 0], [10, 5], [0, 5], [0, 0]]
  },
  "height": 3.0,
  "material": "concrete",
  "level_id": "level_f1",
  "status": "Draft",
  "confidence": 0.95
}
```

### 3.2 InspectionLot (检验批)

```json
{
  "id": "lot_001",
  "name": "1#楼 一层 主体结构 砌体结构 检验批",
  "status": "IN_PROGRESS",
  "rule_type": "by_subdivision",
  "project_id": "project_001",
  "subdivision_id": "subdivision_001",
  "created_at": "2024-01-01T00:00:00Z",
  "submitted_at": null,
  "approved_at": null
}
```

---

## 4. API 端点

### 4.1 数据摄入

#### POST /api/v1/ingest

接收上游 AI Agent 的识别结果，采用"宽进严出"策略。

详细说明请参考 [API 使用指南](usage.md#场景-1-数据摄入)。

### 4.2 层级结构

#### GET /projects

获取项目列表。

#### GET /api/v1/projects/{project_id}/hierarchy

获取项目的完整层级结构。

### 4.3 构件管理

#### GET /elements

查询构件列表。

#### GET /api/v1/elements/{element_id}

获取单个构件详情。

#### DELETE /api/v1/elements/{element_id}

删除指定的构件及其所有关联关系。

#### PATCH /elements/{element_id}

更新构件属性。

#### PATCH /api/v1/elements/{element_id}/topology

更新构件拓扑关系（Trace Mode）。

#### POST /api/v1/elements/batch-lift

批量设置 Z 轴参数（Lift Mode）。

#### POST /api/v1/elements/{element_id}/classify

将构件归类到分项（Classify Mode）。

### 4.4 检验批管理

#### GET /inspection-lots

查询检验批列表。

#### GET /api/v1/inspection-lots/{lot_id}

获取检验批详情。

#### POST /api/v1/inspection-lots/strategy

创建检验批策略（Approver 权限）。

#### POST /api/v1/inspection-lots/{lot_id}/elements

手动添加构件到检验批（人工微调）。

#### DELETE /api/v1/inspection-lots/{lot_id}/elements/{element_id}

从检验批中移除构件。

### 4.5 审批工作流

#### POST /api/v1/inspection-lots/{lot_id}/submit

提交检验批审批（Editor 权限）。

#### POST /api/v1/lots/{lot_id}/approve

审批通过检验批（Approver 权限）。将检验批状态从 `SUBMITTED` 变为 `APPROVED`。

#### POST /api/v1/lots/{lot_id}/reject

驳回检验批。可以将检验批状态从 `SUBMITTED` 或 `APPROVED` 驳回至 `IN_PROGRESS` 或 `PLANNING`。

#### GET /api/v1/lots/{lot_id}/approval-history

获取检验批的审批历史记录。

#### PATCH /api/v1/lots/{lot_id}/status

更新检验批状态。

### 4.6 IFC 导出

#### GET /api/v1/export/ifc

导出 IFC 模型。支持导出单个检验批、多个检验批（批量）或整个项目。

#### POST /api/v1/export/ifc/batch

批量导出多个检验批为单个 IFC 文件（合并导出）。

### 4.7 规则引擎校验 API

规则引擎提供多层次的校验功能，确保数据质量。详细架构设计请参考 [规则引擎文档](../rules/overview.md)。

#### POST /api/v1/validation/semantic-check

语义连接校验（规则引擎 Phase 1）。检查构件类型之间的连接是否合法。

#### POST /api/v1/validation/constructability/validate-angle

构造校验 - 验证角度（规则引擎 Phase 2）。验证角度是否符合标准（45°, 90°, 180°），返回吸附后的角度。

#### POST /api/v1/validation/constructability/validate-z-axis

构造校验 - 验证Z轴完整性（规则引擎 Phase 2）。验证元素的Z轴完整性（height、base_offset是否都存在）。

#### POST /api/v1/validation/constructability/calculate-path-angle

构造校验 - 计算路径角度（规则引擎 Phase 2）。计算路径的角度并返回吸附后的角度。

#### POST /api/v1/validation/topology/validate

拓扑完整性校验（规则引擎 Phase 4）。验证检验批的拓扑完整性（无悬空端点、无孤立元素）。

#### POST /api/v1/validation/topology/find-open-ends

查找悬空端点（规则引擎 Phase 4）。查找指定元素列表中连接数小于2的元素（悬空端点）。

#### POST /api/v1/validation/topology/find-isolated

查找孤立元素（规则引擎 Phase 4）。查找指定元素列表中没有任何连接的元素（孤立元素）。

#### GET /api/v1/rules

获取规则列表。获取所有可用的检验批划分规则列表。

#### POST /api/v1/rules/preview

预览规则效果。预览规则应用后的效果（预估创建的检验批数量和分组信息）。

### 4.8 监控与统计

#### GET /api/v1/dashboard/stats

获取监控统计信息（PM 权限）。

#### GET /api/v1/dashboard/progress

获取验收进度（PM 权限）。

### 4.9 路径规划 API

#### POST /api/v1/routing/calculate

计算路径。详细说明请参考 [MEP 路由规划文档](../features/mep-routing.md)。

#### POST /api/v1/routing/validate

验证路径。

#### GET /api/v1/routing/obstacles

查询障碍物。

#### POST /api/v1/routing/batch

批量路由规划。

#### POST /api/v1/routing/coordination

管线综合排布。

#### PUT /api/v1/spaces/{space_id}/mep-restrictions

设置空间限制。

#### GET /api/v1/routing/priority-config

获取优先级配置。

#### PUT /api/v1/routing/priority-config

更新优先级配置。

#### PUT /api/v1/routing/status

路由规划状态管理。

### 4.10 支吊架 API

详细的支吊架 API 文档请参考 [支吊架 API 文档](hangers.md)。

---

## 5. 错误码参考

| 错误码 | HTTP 状态码 | 说明 |
|--------|-------------|------|
| `INVALID_REQUEST` | 400 | 请求参数错误 |
| `UNAUTHORIZED` | 401 | 未授权 |
| `FORBIDDEN` | 403 | 无权限 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `CONFLICT` | 409 | 资源冲突 |
| `VALIDATION_ERROR` | 422 | 验证失败 |
| `INTERNAL_ERROR` | 500 | 服务器内部错误 |

详细的错误处理说明请参考 [API 使用指南](usage.md#错误处理)。

---

## 6. API 版本管理

### 6.1 版本策略

- 使用 URL 路径版本控制：`/api/v1/`, `/api/v2/`
- 向后兼容的更改不会升级主版本号

### 6.2 版本变更

- **v1.0**: 初始版本

---

## 7. 限流策略

### 7.1 限流规则

- **认证端点**: 5 次/分钟
- **其他端点**: 100 次/分钟

### 7.2 限流响应

```json
{
  "status": "error",
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "请求频率过高，请稍后再试",
    "retry_after": 60
  }
}
```

---

## 8. Webhook 支持（未来）

未来版本将支持 Webhook，用于通知外部系统状态变更。

---

## 相关文档

- [API 使用指南](usage.md) - API 快速开始和使用示例
- [支吊架 API](hangers.md) - 支吊架生成和管理 API
- [规则引擎文档](../rules/overview.md) - 规则引擎架构和设计
- [MEP 路由规划](../features/mep-routing.md) - MEP 路由规划功能文档
