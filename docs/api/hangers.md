# 支吊架 API 文档

## 概述

支吊架 API 提供了自动生成和管理 MEP 元素支吊架的功能，支持根据标准图集自动计算支吊架位置、生成综合支吊架等。

## 端点

### 生成支吊架

**POST** `/api/v1/hangers/generate`

为指定的 MEP 元素自动生成支吊架。

**请求体：**
```json
{
  "element_ids": ["element_001", "element_002"],
  "seismic_grade": "7度",  // 可选：抗震等级（6度、7度、8度、9度）
  "create_nodes": true  // 可选：是否创建节点到数据库，默认为 true
}
```

**响应：**
```json
{
  "status": "success",
  "data": {
    "generated_hangers": [
      {
        "id": "hanger_001",
        "hanger_type": "吊架",
        "standard_code": "03s402",
        "detail_code": "03s402-1",
        "position": [5.0, 2.0, 3.5],
        "supported_element_id": "element_001",
        "supported_element_type": "Pipe",
        "support_interval": 3.0,
        "seismic_grade": "7度"
      }
    ],
    "warnings": [],
    "errors": []
  }
}
```

**支持的标准图集：**
- `03s402`: 室内管道支架及吊架
- `08k132`: 金属、非金属风管支吊架
- `04D701-3`: 电缆桥架安装

### 生成综合支吊架

**POST** `/api/v1/hangers/generate-integrated`

为指定空间内的成排管线生成共用综合支吊架。

**请求体：**
```json
{
  "space_id": "space_001",
  "element_ids": ["pipe_001", "duct_001", "cable_tray_001"],
  "seismic_grade": "7度",  // 可选
  "create_nodes": true
}
```

**响应：**
```json
{
  "status": "success",
  "data": {
    "generated_integrated_hangers": [
      {
        "id": "integrated_hanger_001",
        "hanger_type": "吊架",
        "standard_code": "GB50981-2014",
        "detail_code": "综合支吊架-通用-1",
        "position": [5.0, 2.0, 3.5],
        "supported_element_ids": ["pipe_001", "duct_001"],
        "supported_element_types": ["Pipe", "Duct"],
        "support_interval": 3.0,
        "seismic_grade": "7度"
      }
    ],
    "warnings": [],
    "errors": []
  }
}
```

### 查询支吊架

**GET** `/api/v1/hangers/query?element_id={element_id}&space_id={space_id}`

查询指定元素或空间的支吊架信息。

**查询参数：**
- `element_id` (可选): MEP 元素 ID
- `space_id` (可选): 空间 ID

**响应：**
```json
{
  "status": "success",
  "data": {
    "hangers": [
      {
        "id": "hanger_001",
        "hanger_type": "吊架",
        "standard_code": "03s402",
        "detail_code": "03s402-1",
        "position": [5.0, 2.0, 3.5],
        "supported_element_id": "element_001",
        "support_interval": 3.0
      }
    ],
    "integrated_hangers": [
      {
        "id": "integrated_hanger_001",
        "hanger_type": "吊架",
        "standard_code": "GB50981-2014",
        "detail_code": "综合支吊架-通用-1",
        "position": [5.0, 2.0, 3.5],
        "supported_element_ids": ["pipe_001", "duct_001"],
        "supported_element_types": ["Pipe", "Duct"]
      }
    ]
  }
}
```

## 空间综合支吊架配置

### 设置空间综合支吊架

**PUT** `/api/v1/spaces/{space_id}/integrated-hanger`

设置空间是否使用综合支吊架。

**请求体：**
```json
{
  "use_integrated_hanger": true
}
```

**响应：**
```json
{
  "status": "success",
  "data": {
    "space_id": "space_001",
    "use_integrated_hanger": true,
    "updated_at": "2024-01-01T12:00:00Z"
  }
}
```

## 错误处理

所有端点遵循标准的错误响应格式：

```json
{
  "detail": "错误消息"
}
```

常见错误：
- `400 Bad Request`: 请求参数错误
- `404 Not Found`: 元素或空间不存在
- `500 Internal Server Error`: 服务器内部错误

## 支吊架间距规则

支吊架间距根据元素类型和规格自动计算：

### 管道（Pipe）
- DN15-DN25: 最大间距 2.5m
- DN32-DN40: 最大间距 3.0m
- DN50-DN80: 最大间距 4.0m
- DN100-DN150: 最大间距 5.0m
- DN200+: 最大间距 6.0m

### 风管（Duct）
- 小截面（宽度≤400mm）: 最大间距 3.0m
- 中截面（400mm<宽度≤1250mm）: 最大间距 3.75m
- 大截面（宽度>1250mm）: 最大间距 4.5m

### 电缆桥架（CableTray）
- 宽度 50-100mm: 最大间距 1.5m
- 宽度 100-200mm: 最大间距 2.0m
- 宽度 200-400mm: 最大间距 2.5m
- 宽度 400mm+: 最大间距 3.0m

## 抗震要求

根据《建筑机电工程抗震设计规范》（GB50981-2014）：

- **6度**: 无需特殊抗震支吊架
- **7度及以上**: 需要抗震支吊架，间距按比例减小

---

**最后更新**：2025-12-28  
**文档版本**：1.0  
**维护者**：OpenTruss 开发团队