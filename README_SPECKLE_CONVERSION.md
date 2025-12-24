# Speckle BuiltElements 转换说明

本文档说明如何将 Speckle BuiltElements 转换为 OpenTruss 数据模型。

## 概述

已将所有 Speckle BuiltElements 的 C# 类转换为：
1. **Python Pydantic 模型**（位于 `backend/app/models/speckle/`）
2. **TypeScript 类型定义**（通过 FastAPI OpenAPI schema 自动生成）

## 文件结构

```
backend/app/models/speckle/
├── __init__.py          # 导出所有模型
├── base.py              # 基础类和通用类型（Geometry2D, SpeckleBuiltElementBase）
├── architectural.py     # 建筑元素（Wall, Floor, Ceiling, Roof, Column）
├── structural.py        # 结构元素（Beam, Brace, Structure, Rebar）
├── mep.py               # MEP 元素（Duct, Pipe, CableTray, Conduit, Wire）
├── spatial.py           # 空间元素（Level, Room, Space, Zone, Area）
└── other.py             # 其他元素（Opening, Topography, GridLine, Profile, Network, View, Alignment, Baseline, Featureline, Station）
```

## 支持的 Speckle 元素类型

### 建筑元素 (Architectural)
- `Wall` - 墙体
- `Floor` - 楼板
- `Ceiling` - 吊顶
- `Roof` - 屋顶
- `Column` - 柱

### 结构元素 (Structural)
- `Beam` - 梁
- `Brace` - 支撑（斜撑）
- `Structure` - 结构元素（通用）
- `Rebar` - 钢筋

### MEP 元素
- `Duct` - 风管
- `Pipe` - 管道
- `CableTray` - 电缆桥架
- `Conduit` - 导管
- `Wire` - 电线

### 空间元素 (Spatial)
- `Level` - 楼层
- `Room` - 房间
- `Space` - 空间（MEP 空间）
- `Zone` - 区域
- `Area` - 面积

### 其他元素
- `Opening` - 洞口
- `Topography` - 地形
- `GridLine` - 网格线
- `Profile` - 剖面/轮廓
- `Network` - 网络
- `View` - 视图
- `Alignment` - 路线对齐（Civil）
- `Baseline` - 基线（Civil）
- `Featureline` - 特征线（Civil）
- `Station` - 桩号（Civil）

## 类型映射规则

### C# → Python/Pydantic

| C# 类型 | Python/Pydantic 类型 | 说明 |
|---------|---------------------|------|
| `ICurve` | `Geometry2D` | 转换为 OpenTruss 的 Geometry2D 格式 |
| `Level?` | `Optional[str]` | 转换为 level_id（字符串） |
| `double?` | `Optional[float]` | 可选浮点数 |
| `string?` | `Optional[str]` | 可选字符串 |
| `List<Base>` | `List[Dict[str, Any]]` | 嵌套元素列表 |
| `List<ICurve>` | `List[Geometry2D]` | 几何列表（如 voids） |

### 字段映射

| Speckle 字段 | OpenTruss 字段 | 说明 |
|-------------|---------------|------|
| `baseLine` | `geometry_2d` | 使用 alias 支持两种命名 |
| `outline` | `geometry_2d` | 使用 alias 支持两种命名 |
| `level` | `level_id` | Level 对象转换为字符串 ID |

## 使用示例

### Python (FastAPI)

```python
from app.models.speckle import Wall, Geometry2D

# 创建 Wall 元素
wall = Wall(
    speckle_type="Wall",
    speckle_id="speckle_001",
    geometry_2d=Geometry2D(
        type="Polyline",
        coordinates=[[0, 0], [10, 0], [10, 5], [0, 5], [0, 0]],
        closed=True
    ),
    height=3.0,
    units="m",
    level_id="level_f1"
)
```

### API 请求（JSON）

```json
{
  "project_id": "project_001",
  "elements": [
    {
      "speckle_type": "Wall",
      "baseLine": {
        "type": "Polyline",
        "coordinates": [[0, 0], [10, 0], [10, 5], [0, 5], [0, 0]],
        "closed": true
      },
      "height": 3.0,
      "units": "m",
      "level_id": "level_f1"
    }
  ]
}
```

### TypeScript（自动生成）

```typescript
import { Wall, Geometry2D } from '@/lib/api';

const wall: Wall = {
  speckleType: 'Wall',
  speckleId: 'speckle_001',
  geometry2d: {
    type: 'Polyline',
    coordinates: [[0, 0], [10, 0], [10, 5], [0, 5], [0, 0]],
    closed: true
  },
  height: 3.0,
  units: 'm',
  levelId: 'level_f1'
};
```

## 重新生成模型

如果 Speckle 更新了 BuiltElements 定义，可以重新生成：

```bash
# 1. 从 GitHub 获取最新的 Speckle .cs 文件
python scripts/fetch_speckle_built_elements.py

# 2. 转换为 Pydantic 模型
python scripts/convert_speckle_to_pydantic.py

# 3. 验证并生成 TypeScript
python scripts/verify_openapi_schema.py
npm run generate-api  # 在前端目录中
```

## 注意事项

1. **字段别名**: 使用 `alias` 支持 Speckle 的 `baseLine`/`outline` 命名，同时内部使用 `geometry_2d`
2. **可选字段**: 遵循"宽进严出"策略，大部分字段为 Optional
3. **类型转换**: `ICurve` 转换为 `Geometry2D`，`Level` 对象转换为 `level_id` 字符串
4. **向后兼容**: API 同时支持 `baseLine`/`outline` 和 `geometry_2d` 两种命名方式

