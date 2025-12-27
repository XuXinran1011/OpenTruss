# OpenTruss API 使用文档

## 1. 快速开始

### 1.1 获取 API 访问权限

1. 联系管理员获取账号
2. 使用账号登录获取 Token
3. 使用 Token 访问 API

### 1.2 认证

所有 API 请求需要在请求头中包含 Token：

```bash
Authorization: Bearer <your-token>
```

### 1.3 Base URL

- **生产环境**: `https://api.opentruss.com/api/v1`
- **开发环境**: `http://localhost:8000/api/v1`

---

## 2. 认证流程

### 2.1 登录获取 Token

**请求**:
```bash
curl -X POST https://api.opentruss.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your-username",
    "password": "your-password"
  }'
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
      "username": "your-username",
      "role": "editor"
    }
  }
}
```

### 2.2 使用 Token

```bash
TOKEN="your-access-token"

curl -X GET https://api.opentruss.com/api/v1/projects \
  -H "Authorization: Bearer $TOKEN"
```

---

## 3. 常见使用场景

### 3.1 场景 1: 数据摄入

**目标**: 将 AI 识别的 Speckle 构件数据导入系统

**支持的 Speckle 元素类型**:
- 建筑元素: Wall, Floor, Ceiling, Roof, Column
- 结构元素: Beam, Brace, Structure, Rebar
- MEP 元素: Duct, Pipe, CableTray, Conduit, Wire
- 空间元素: Level, Room, Space, Zone, Area
- 其他元素: Opening, Topography, GridLine, Profile, Network, View 等

**步骤**:

1. **准备数据**:
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
    },
    {
      "speckle_type": "Floor",
      "outline": {
        "type": "Polyline",
        "coordinates": [[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]],
        "closed": true
      },
      "level_id": "level_f1"
    }
  ]
}
```

**注意**:
- `Wall`, `Beam`, `Column` 等使用 `baseLine` 字段
- `Floor`, `Ceiling`, `Roof` 等使用 `outline` 字段
- 几何数据格式统一为 `Geometry2D`（type + coordinates + closed）

2. **发送请求**:
```bash
curl -X POST https://api.opentruss.com/api/v1/ingest \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @elements.json
```

3. **处理响应**:
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

### 3.2 场景 2: 查询构件列表

**目标**: 获取某个检验批的所有构件

**步骤**:

1. **查询构件**:
```bash
curl -X GET "https://api.opentruss.com/api/v1/elements?inspection_lot_id=lot_001" \
  -H "Authorization: Bearer $TOKEN"
```

2. **响应**:
```json
{
  "status": "success",
  "data": {
    "items": [
      {
        "id": "element_001",
        "speckle_type": "Wall",
        "height": 3.0,
        "material": "concrete",
        "status": "Verified"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

### 3.3 场景 3: 批量更新 Z 轴参数

**目标**: 为多个构件设置高度和基础偏移

**步骤**:

1. **准备更新数据**:
```json
{
  "element_ids": ["element_001", "element_002", "element_003"],
  "height": 3.0,
  "base_offset": 0.0
}
```

2. **发送请求**:
```bash
curl -X POST https://api.opentruss.com/api/v1/elements/batch-lift \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "element_ids": ["element_001", "element_002"],
    "height": 3.0,
    "base_offset": 0.0
  }'
```

### 3.4 场景 4: 创建检验批

**目标**: 为某个分项创建检验批（Approver 权限）

**步骤**:

1. **定义规则**:
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

2. **发送请求**:
```bash
curl -X POST https://api.opentruss.com/api/v1/inspection-lots/strategy \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "item_id": "item_001",
    "rule": {"type": "by_level"}
  }'
```

3. **响应**:
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

### 3.5 场景 5: 提交检验批审批

**目标**: 提交检验批等待审批（Editor 权限）

**步骤**:

1. **提交请求**:
```bash
curl -X POST https://api.opentruss.com/api/v1/inspection-lots/lot_001/submit \
  -H "Authorization: Bearer $TOKEN"
```

2. **成功响应**:
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

3. **失败响应** (构件不完整):
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

### 3.6 场景 6: 审批检验批

**目标**: 审批通过或驳回检验批（Approver 权限）

**步骤**:

1. **审批通过**:
```bash
curl -X POST https://api.opentruss.com/api/v1/inspection-lots/lot_001/approve \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "comment": "验收通过"
  }'
```

2. **驳回**:
```bash
curl -X POST https://api.opentruss.com/api/v1/inspection-lots/lot_001/reject \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "数据质量问题",
    "reject_level": "IN_PROGRESS"
  }'
```

### 3.7 场景 7: 验证角度和Z轴完整性

**目标**: 使用构造校验 API 验证角度和Z轴参数（规则引擎 Phase 2）

**步骤**:

1. **验证角度**:
```bash
curl -X POST https://api.opentruss.com/api/v1/validation/constructability/validate-angle \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "angle": 88.5
  }'
```

**响应**:
```json
{
  "status": "success",
  "data": {
    "valid": true,
    "snapped_angle": 90,
    "error": null
  }
}
```

2. **验证Z轴完整性**:
```bash
curl -X POST https://api.opentruss.com/api/v1/validation/constructability/validate-z-axis \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "element_id": "element_001",
    "speckle_type": "Wall",
    "height": 3.0,
    "base_offset": 0.0
  }'
```

### 3.8 场景 8: 拓扑校验

**目标**: 使用拓扑校验 API 检查检验批的拓扑完整性（规则引擎 Phase 4）

**步骤**:

1. **验证拓扑完整性**:
```bash
curl -X POST https://api.opentruss.com/api/v1/validation/topology/validate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "lot_id": "lot_001"
  }'
```

**响应**:
```json
{
  "status": "success",
  "data": {
    "valid": false,
    "open_ends": ["element_001", "element_002"],
    "isolated_elements": ["element_003"],
    "errors": [
      "发现 2 个悬空端点",
      "发现 1 个孤立元素"
    ]
  }
}
```

2. **查找悬空端点**:
```bash
curl -X POST https://api.opentruss.com/api/v1/validation/topology/find-open-ends \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "element_ids": ["element_001", "element_002", "element_003"]
  }'
```

3. **查找孤立元素**:
```bash
curl -X POST https://api.opentruss.com/api/v1/validation/topology/find-isolated \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "element_ids": ["element_001", "element_002", "element_003"]
  }'
```

### 3.9 场景 9: 规则管理和预览

**目标**: 获取规则列表和预览规则效果（Approver 权限）

**步骤**:

1. **获取规则列表**:
```bash
curl -X GET https://api.opentruss.com/api/v1/rules \
  -H "Authorization: Bearer $TOKEN"
```

**响应**:
```json
{
  "status": "success",
  "data": {
    "rules": [
      {
        "rule_type": "BY_LEVEL",
        "name": "按楼层划分",
        "description": "根据构件的楼层（Level）自动分组创建检验批",
        "is_custom": false
      },
      {
        "rule_type": "BY_ZONE",
        "name": "按区域划分",
        "description": "根据构件的区域（Zone）自动分组创建检验批",
        "is_custom": false
      },
      {
        "rule_type": "BY_LEVEL_AND_ZONE",
        "name": "按楼层+区域划分",
        "description": "根据楼层和区域的组合自动分组创建检验批",
        "is_custom": false
      }
    ]
  }
}
```

2. **预览规则效果**:
```bash
curl -X POST https://api.opentruss.com/api/v1/rules/preview \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "item_id": "item_001",
    "rule_type": "BY_LEVEL"
  }'
```

**响应**:
```json
{
  "status": "success",
  "data": {
    "rule_type": "BY_LEVEL",
    "estimated_lots": 3,
    "groups": [
      {
        "key": "F1",
        "count": 25,
        "label": "1#楼F1层"
      },
      {
        "key": "F2",
        "count": 30,
        "label": "1#楼F2层"
      }
    ]
  }
}
```

### 3.10 场景 10: 导出 IFC 模型

**目标**: 导出已验收的检验批为 IFC 文件

**步骤**:

1. **请求导出**:
```bash
curl -X GET "https://api.opentruss.com/api/v1/export/ifc?inspection_lot_id=lot_001" \
  -H "Authorization: Bearer $TOKEN" \
  -o project_001.ifc
```

2. **验证文件**:
```bash
# 检查文件大小
ls -lh project_001.ifc

# 使用 ifcopenshell 验证（如已安装）
python -c "import ifcopenshell; ifcopenshell.open('project_001.ifc')"
```

---

## 4. 错误处理

### 4.1 常见错误码

| 错误码 | HTTP 状态码 | 说明 | 解决方案 |
|--------|------------|------|---------|
| `VALIDATION_ERROR` | 422 | 请求参数验证失败 | 检查请求参数格式 |
| `UNAUTHORIZED` | 401 | 未授权 | 检查 Token 是否有效 |
| `FORBIDDEN` | 403 | 无权限 | 检查用户角色权限 |
| `NOT_FOUND` | 404 | 资源不存在 | 检查资源 ID 是否正确 |
| `INCOMPLETE_ELEMENTS` | 422 | 构件信息不完整 | 补全缺失字段 |
| `INVALID_STATE_TRANSITION` | 409 | 无效的状态转换 | 检查当前状态 |
| `RATE_LIMIT_EXCEEDED` | 429 | 请求过于频繁 | 降低请求频率 |

### 4.2 错误响应格式

```json
{
  "status": "error",
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述",
    "details": {
      "field": "具体错误信息"
    }
  }
}
```

### 4.3 处理错误

**Python 示例**:
```python
import requests

try:
    response = requests.post(
        "https://api.opentruss.com/api/v1/inspection-lots/lot_001/submit",
        headers={"Authorization": f"Bearer {token}"}
    )
    response.raise_for_status()
    data = response.json()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 422:
        error = e.response.json()["error"]
        print(f"验证错误: {error['message']}")
        print(f"详情: {error['details']}")
    else:
        print(f"HTTP 错误: {e}")
except Exception as e:
    print(f"其他错误: {e}")
```

---

## 5. SDK 使用（未来）

未来将提供官方 SDK，简化 API 调用：

**Python SDK 示例** (未来):
```python
from opentruss import OpenTrussClient

client = OpenTrussClient(
    base_url="https://api.opentruss.com/v1",
    token="your-token"
)

# 创建检验批
lots = client.inspection_lots.create_strategy(
    item_id="item_001",
    rule={"type": "by_level"}
)

# 提交审批
client.inspection_lots.submit("lot_001")

# 导出 IFC
ifc_file = client.export.ifc(inspection_lot_id="lot_001")
```

---

## 6. 最佳实践

### 6.1 请求优化

- **使用分页**: 大量数据使用分页查询
- **批量操作**: 使用批量接口减少请求次数
- **缓存 Token**: Token 有效期内复用
- **错误重试**: 实现指数退避重试机制

### 6.2 安全建议

- **保护 Token**: 不要将 Token 提交到代码仓库
- **使用 HTTPS**: 生产环境必须使用 HTTPS
- **定期轮换**: 定期更新 Token
- **最小权限**: 使用最小必要权限的账号

### 6.3 性能优化

- **并发请求**: 使用异步请求提高效率
- **连接复用**: 复用 HTTP 连接
- **数据压缩**: 启用 Gzip 压缩

---

## 7. 示例代码

### 7.1 Python 完整示例

```python
import requests
import json

class OpenTrussAPI:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def ingest_elements(self, project_id, elements):
        """数据摄入
        
        Args:
            project_id: 项目 ID
            elements: Speckle 元素列表，每个元素包含：
                - speckle_type: 元素类型（Wall, Beam, Column 等）
                - baseLine 或 outline: 2D 几何数据
                - 其他可选字段（height, units, level_id 等）
        """
        url = f"{self.base_url}/ingest"
        data = {
            "project_id": project_id,
            "elements": elements
        }
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()
    
    def ingest_wall(self, project_id, base_line, height=None, level_id=None):
        """便捷方法：摄入墙体元素"""
        wall_element = {
            "speckle_type": "Wall",
            "baseLine": base_line,
            "height": height,
            "level_id": level_id
        }
        return self.ingest_elements(project_id, [wall_element])
    
    def ingest_beam(self, project_id, base_line, level_id=None):
        """便捷方法：摄入梁元素"""
        beam_element = {
            "speckle_type": "Beam",
            "baseLine": base_line,
            "level_id": level_id
        }
        return self.ingest_elements(project_id, [beam_element])
    
    def get_elements(self, inspection_lot_id=None, page=1, page_size=20):
        """查询构件列表"""
        url = f"{self.base_url}/elements"
        params = {
            "page": page,
            "page_size": page_size
        }
        if inspection_lot_id:
            params["inspection_lot_id"] = inspection_lot_id
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def batch_lift(self, element_ids, height, base_offset):
        """批量设置 Z 轴参数"""
        url = f"{self.base_url}/elements/batch-lift"
        data = {
            "element_ids": element_ids,
            "height": height,
            "base_offset": base_offset
        }
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()
    
    def submit_inspection_lot(self, lot_id):
        """提交检验批审批"""
        url = f"{self.base_url}/inspection-lots/{lot_id}/submit"
        response = requests.post(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def validate_angle(self, angle):
        """验证角度是否符合标准"""
        url = f"{self.base_url}/validation/constructability/validate-angle"
        data = {"angle": angle}
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()
    
    def validate_z_axis(self, element_id, speckle_type, height=None, base_offset=None):
        """验证Z轴完整性"""
        url = f"{self.base_url}/validation/constructability/validate-z-axis"
        data = {
            "element_id": element_id,
            "speckle_type": speckle_type,
            "height": height,
            "base_offset": base_offset
        }
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()
    
    def validate_topology(self, lot_id):
        """验证拓扑完整性"""
        url = f"{self.base_url}/validation/topology/validate"
        data = {"lot_id": lot_id}
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()
    
    def find_open_ends(self, element_ids):
        """查找悬空端点"""
        url = f"{self.base_url}/validation/topology/find-open-ends"
        data = {"element_ids": element_ids}
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()
    
    def find_isolated_elements(self, element_ids):
        """查找孤立元素"""
        url = f"{self.base_url}/validation/topology/find-isolated"
        data = {"element_ids": element_ids}
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()
    
    def get_rules(self):
        """获取规则列表"""
        url = f"{self.base_url}/rules"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def preview_rule(self, item_id, rule_type):
        """预览规则效果"""
        url = f"{self.base_url}/rules/preview"
        data = {
            "item_id": item_id,
            "rule_type": rule_type
        }
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

# 使用示例
api = OpenTrussAPI(
    base_url="https://api.opentruss.com/api/v1",
    token="your-token"
)

# 数据摄入
elements = [
    {
        "speckle_type": "Wall",
        "geometry_2d": {
            "type": "Polyline",
            "coordinates": [[0, 0], [10, 0], [10, 5], [0, 5], [0, 0]]
        },
        "level_id": "level_f1"
    }
]
result = api.ingest_elements("project_001", elements)
print(f"摄入 {result['data']['ingested_count']} 个构件")

# 查询构件
elements_data = api.get_elements(inspection_lot_id="lot_001")
print(f"找到 {elements_data['data']['total']} 个构件")

# 批量设置 Z 轴
api.batch_lift(
    element_ids=["element_001", "element_002"],
    height=3.0,
    base_offset=0.0
)

# 提交审批
api.submit_inspection_lot("lot_001")

# 验证角度
angle_result = api.validate_angle(88.5)
print(f"角度验证结果: {angle_result['data']}")

# 验证Z轴完整性
z_axis_result = api.validate_z_axis(
    element_id="element_001",
    speckle_type="Wall",
    height=3.0,
    base_offset=0.0
)
print(f"Z轴验证结果: {z_axis_result['data']}")

# 拓扑校验
topology_result = api.validate_topology("lot_001")
if not topology_result['data']['valid']:
    print(f"拓扑校验失败: {topology_result['data']['errors']}")
    open_ends = api.find_open_ends(["element_001", "element_002"])
    print(f"悬空端点: {open_ends['data']['element_ids']}")

# 获取规则列表
rules = api.get_rules()
print(f"可用规则: {rules['data']['rules']}")

# 预览规则效果
preview = api.preview_rule("item_001", "BY_LEVEL")
print(f"预计创建 {preview['data']['estimated_lots']} 个检验批")
```

### 7.2 JavaScript 示例

```javascript
class OpenTrussAPI {
  constructor(baseUrl, token) {
    this.baseUrl = baseUrl;
    this.headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }

  async ingestElements(projectId, elements) {
    const response = await fetch(`${this.baseUrl}/ingest`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({
        project_id: projectId,
        elements: elements
      })
    });
    return await response.json();
  }

  async getElements(inspectionLotId = null, page = 1, pageSize = 20) {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString()
    });
    if (inspectionLotId) {
      params.append('inspection_lot_id', inspectionLotId);
    }
    
    const response = await fetch(
      `${this.baseUrl}/elements?${params}`,
      { headers: this.headers }
    );
    return await response.json();
  }

  async batchLift(elementIds, height, baseOffset) {
    const response = await fetch(`${this.baseUrl}/elements/batch-lift`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({
        element_ids: elementIds,
        height: height,
        base_offset: baseOffset
      })
    });
    return await response.json();
  }

  async validateAngle(angle) {
    const response = await fetch(`${this.baseUrl}/validation/constructability/validate-angle`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({ angle })
    });
    return await response.json();
  }

  async validateZAxis(elementId, speckleType, height = null, baseOffset = null) {
    const response = await fetch(`${this.baseUrl}/validation/constructability/validate-z-axis`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({
        element_id: elementId,
        speckle_type: speckleType,
        height,
        base_offset: baseOffset
      })
    });
    return await response.json();
  }

  async validateTopology(lotId) {
    const response = await fetch(`${this.baseUrl}/validation/topology/validate`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({ lot_id: lotId })
    });
    return await response.json();
  }

  async findOpenEnds(elementIds) {
    const response = await fetch(`${this.baseUrl}/validation/topology/find-open-ends`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({ element_ids: elementIds })
    });
    return await response.json();
  }

  async findIsolatedElements(elementIds) {
    const response = await fetch(`${this.baseUrl}/validation/topology/find-isolated`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({ element_ids: elementIds })
    });
    return await response.json();
  }

  async getRules() {
    const response = await fetch(`${this.baseUrl}/rules`, {
      headers: this.headers
    });
    return await response.json();
  }

  async previewRule(itemId, ruleType) {
    const response = await fetch(`${this.baseUrl}/rules/preview`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({
        item_id: itemId,
        rule_type: ruleType
      })
    });
    return await response.json();
  }
}

// 使用示例
const api = new OpenTrussAPI(
  'https://api.opentruss.com/api/v1',
  'your-token'
);

// 数据摄入
const elements = [
  {
    speckle_type: 'Wall',
    geometry_2d: {
      type: 'Polyline',
      coordinates: [[0, 0], [10, 0], [10, 5], [0, 5], [0, 0]]
    },
    level_id: 'level_f1'
  }
];
const result = await api.ingestElements('project_001', elements);
console.log(`摄入 ${result.data.ingested_count} 个构件`);

// 验证角度
const angleResult = await api.validateAngle(88.5);
console.log(`角度验证结果:`, angleResult.data);

// 验证Z轴完整性
const zAxisResult = await api.validateZAxis('element_001', 'Wall', 3.0, 0.0);
console.log(`Z轴验证结果:`, zAxisResult.data);

// 拓扑校验
const topologyResult = await api.validateTopology('lot_001');
if (!topologyResult.data.valid) {
  console.log(`拓扑校验失败:`, topologyResult.data.errors);
  const openEnds = await api.findOpenEnds(['element_001', 'element_002']);
  console.log(`悬空端点:`, openEnds.data.element_ids);
}

// 获取规则列表
const rules = await api.getRules();
console.log(`可用规则:`, rules.data.rules);

// 预览规则效果
const preview = await api.previewRule('item_001', 'BY_LEVEL');
console.log(`预计创建 ${preview.data.estimated_lots} 个检验批`);
```

---

## 8. 支持与反馈

- **API 文档**: 查看 `docs/API.md`
- **问题反馈**: 创建 GitHub Issue
- **技术支持**: 联系技术支持团队

---

*文档版本：1.0*  
*最后更新：根据 PRD v4.0 创建*

