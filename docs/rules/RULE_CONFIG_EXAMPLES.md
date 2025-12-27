# 规则引擎配置文件示例与说明

本文档提供 OpenTruss 规则引擎配置文件的详细示例和说明。配置文件遵循 **Rule as Code** 原则，应纳入 Git 版本控制。

## 1. 配置文件位置

所有规则引擎配置文件位于：

```
backend/app/config/rules/
  ├── semantic_allowlist.json      # 语义规则配置（规则引擎 Phase 1）
  ├── fitting_standards.json        # 构造标准配置（规则引擎 Phase 2）
  └── version.json                  # 配置版本信息（可选）
```

## 2. 语义规则配置 (semantic_allowlist.json)

### 2.1 配置结构

```json
{
  "version": "1.0",
  "description": "语义连接白名单配置（规则引擎 Phase 1）",
  "rules": {
    "semantic_allowlist": {
      "源构件类型": ["目标构件类型1", "目标构件类型2", ...]
    }
  }
}
```

### 2.2 配置说明

- **version**: 配置文件版本号
- **description**: 配置文件的描述信息
- **semantic_allowlist**: 语义连接白名单，采用键值对结构
  - **键 (Key)**: 源构件类型（Speckle 类型名称）
  - **值 (Value)**: 允许连接的目标构件类型数组

**逻辑**：白名单机制（Allowlist）。未定义的连接即为非法。

### 2.3 完整示例

```json
{
  "version": "1.0",
  "description": "语义连接白名单配置（规则引擎 Phase 1）",
  "rules": {
    "semantic_allowlist": {
      "Objects.BuiltElements.Pipe": [
        "Objects.BuiltElements.Pipe",
        "Objects.BuiltElements.Valve",
        "Objects.BuiltElements.Pump",
        "Objects.BuiltElements.Tank",
        "Objects.BuiltElements.PipeFitting"
      ],
      "Objects.BuiltElements.Wall": [
        "Objects.BuiltElements.Wall",
        "Objects.BuiltElements.Column",
        "Objects.BuiltElements.Beam"
      ],
      "Objects.BuiltElements.Duct": [
        "Objects.BuiltElements.Duct",
        "Objects.BuiltElements.AirTerminal",
        "Objects.BuiltElements.Fan",
        "Objects.BuiltElements.Damper"
      ],
      "Objects.BuiltElements.Cable": [
        "Objects.BuiltElements.Cable",
        "Objects.BuiltElements.ElectricalPanel",
        "Objects.BuiltElements.LightingFixture"
      ]
    }
  }
}
```

### 2.4 配置规则

1. **双向连接**：如果 A 可以连接到 B，B 不一定可以连接到 A（除非在配置中明确声明）
2. **未定义类型**：如果源构件类型不在配置中，默认不允许连接到任何类型
3. **空数组**：如果某个源构件类型的值为空数组 `[]`，表示该类型不能连接到任何其他类型
4. **类型名称**：使用 Speckle Objects 的标准类型名称（`Objects.BuiltElements.*`）

### 2.5 使用示例

**场景**：检查 Pipe 是否可以连接到 Valve

```python
# 后端 Python
from app.services.validators.semantic import SemanticValidator
from pathlib import Path

config_path = Path('backend/app/config/rules/semantic_allowlist.json')
validator = SemanticValidator(config_path)

can_connect = validator.can_connect(
    'Objects.BuiltElements.Pipe',
    'Objects.BuiltElements.Valve'
)
# 返回: True

can_connect = validator.can_connect(
    'Objects.BuiltElements.Pipe',
    'Objects.BuiltElements.Column'
)
# 返回: False
```

```typescript
// 前端 TypeScript
import { SemanticValidator } from '@/lib/rules/SemanticValidator';

const validator = new SemanticValidator(semanticAllowlist);
const canConnect = validator.canConnect(
  'Objects.BuiltElements.Pipe',
  'Objects.BuiltElements.Valve'
);
// 返回: true
```

## 3. 构造标准配置 (fitting_standards.json)

### 3.1 配置结构

```json
{
  "version": "1.0",
  "description": "构造标准配置（规则引擎 Phase 2）",
  "rules": {
    "fitting_standards": {
      "angles": {
        "standard": [90, 45, 180],
        "tolerance": 5,
        "allow_custom": false
      },
      "z_axis": {
        "require_height": true,
        "require_base_offset": true,
        "element_types": ["Wall", "Column"]
      }
    }
  }
}
```

### 3.2 配置说明

#### 3.2.1 角度标准 (angles)

- **standard**: 标准角度数组（单位：度）
  - 常见值：`[90, 45, 180]`（直角、45度角、直线）
  - 可以根据项目需求添加其他标准角度
- **tolerance**: 角度容差（单位：度）
  - 如果当前角度与标准角度的差值在容差范围内，会自动吸附到标准角度
  - 例如：如果标准角度是 90°，容差是 5°，那么 88° 会自动吸附为 90°
- **allow_custom**: 是否允许非标角度
  - `true`: 允许任意角度（仅警告，不阻止）
  - `false`: 只允许标准角度（不符合标准角度时拒绝或强制吸附）

#### 3.2.2 Z 轴完整性 (z_axis)

- **require_height**: 是否要求 height 字段
  - `true`: 必须提供 height 值
  - `false`: height 可以为空
- **require_base_offset**: 是否要求 base_offset 字段
  - `true`: 必须提供 base_offset 值
  - `false`: base_offset 可以为空
- **element_types**: 需要 Z 轴完整性检查的构件类型数组
  - 通常包括：`["Wall", "Column"]`
  - 这些类型的构件必须提供完整的 Z 轴信息才能提交审批

### 3.3 完整示例

```json
{
  "version": "1.0",
  "description": "构造标准配置（规则引擎 Phase 2）",
  "rules": {
    "fitting_standards": {
      "angles": {
        "standard": [90, 45, 180, 30, 60, 135],
        "tolerance": 5,
        "allow_custom": false
      },
      "z_axis": {
        "require_height": true,
        "require_base_offset": true,
        "element_types": ["Wall", "Column", "Beam"]
      },
      "diameters": {
        "standard": [50, 75, 100, 150, 200, 250],
        "tolerance": 5,
        "unit": "mm"
      }
    }
  }
}
```

### 3.4 配置规则

1. **角度标准**：
   - 标准角度应该基于实际工程中常用的角度
   - 容差应该根据项目精度要求设置（通常 3-10 度）
   - `allow_custom=false` 时，系统会强制吸附到最近的标准角度

2. **Z 轴完整性**：
   - 这是"逆向重构"特有的规则
   - 只有指定的构件类型需要 Z 轴完整性检查
   - 如果 `require_height=true` 但构件没有 height 值，提交审批时会报错

3. **扩展性**：
   - 可以添加其他标准配置（如 `diameters`、`materials` 等）
   - 配置结构应该保持向后兼容

### 3.5 使用示例

**场景 1**：角度吸附

```typescript
// 前端 TypeScript
import { ConstructabilityValidator } from '@/lib/rules/ConstructabilityValidator';

const angleStandards = {
  standard: [90, 45, 180],
  tolerance: 5,
  allowCustom: false
};
const validator = new ConstructabilityValidator(angleStandards);

const snappedAngle = validator.snapAngle(88);
// 返回: 90 (88° 在容差范围内，吸附到 90°)

const snappedAngle = validator.snapAngle(100);
// 返回: null (100° 不在任何标准角度的容差范围内，且 allowCustom=false)
```

**场景 2**：Z 轴完整性检查

```python
# 后端 Python
from app.services.validators.completeness import CompletenessValidator
from pathlib import Path

config_path = Path('backend/app/config/rules/fitting_standards.json')
validator = CompletenessValidator(config_path)

element = {
    'id': 'element_001',
    'speckle_type': 'Wall',
    'height': None,  # 缺失
    'base_offset': 0
}

result = validator.validate_element_completeness(element)
# 返回: {
#     "valid": False,
#     "missing_fields": ["height"]
# }
```

## 4. 配置版本管理

### 4.1 版本文件 (version.json)

可选的文件，用于记录配置版本信息：

```json
{
  "version": "1.0.0",
  "last_updated": "2025-01-01T00:00:00Z",
  "changelog": [
    {
      "version": "1.0.0",
      "date": "2025-01-01",
      "changes": [
        "初始版本",
        "添加 Pipe、Wall、Duct 的语义规则",
        "定义角度标准：90°、45°、180°"
      ]
    }
  ]
}
```

### 4.2 配置迁移

当配置版本升级时，应该：

1. 保留旧版本配置文件（重命名为 `*.json.bak`）
2. 创建配置迁移脚本（如 `migrate_config_v1_to_v2.py`）
3. 更新配置文件中的 `version` 字段
4. 在 `version.json` 的 `changelog` 中记录变更

## 5. 最佳实践

### 5.1 Rule as Code

- 配置文件应纳入 Git 版本控制
- 配置变更需要代码审查（Pull Request）
- 使用语义化版本号管理配置版本
- 提供配置迁移脚本，支持版本升级

### 5.2 配置验证

在加载配置时，应该验证配置的有效性：

```python
# backend/app/config/rules/loader.py

def validate_semantic_allowlist(config: dict) -> bool:
    """验证语义规则配置的有效性"""
    if 'rules' not in config:
        return False
    if 'semantic_allowlist' not in config['rules']:
        return False
    # 更多验证逻辑...
    return True
```

### 5.3 配置热加载（可选）

在生产环境中，可以支持配置热加载，无需重启服务：

```python
# backend/app/config/rules/watcher.py

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class RuleConfigWatcher(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith('.json'):
            # 重新加载配置
            reload_config()
```

### 5.4 配置文档化

- 每个配置文件都应该有清晰的 `description` 字段
- 复杂的配置项应该有注释说明（使用 JSON5 格式或单独的文档）
- 提供配置示例和常见场景的使用说明

## 6. 常见问题

### 6.1 如何添加新的构件类型连接规则？

编辑 `semantic_allowlist.json`，在 `semantic_allowlist` 对象中添加新的键值对：

```json
{
  "rules": {
    "semantic_allowlist": {
      "Objects.BuiltElements.NewType": [
        "Objects.BuiltElements.AllowedType1",
        "Objects.BuiltElements.AllowedType2"
      ]
    }
  }
}
```

### 6.2 如何修改角度容差？

编辑 `fitting_standards.json`，修改 `angles.tolerance` 值：

```json
{
  "rules": {
    "fitting_standards": {
      "angles": {
        "tolerance": 10  // 将容差从 5 改为 10
      }
    }
  }
}
```

### 6.3 如何允许非标角度？

设置 `allow_custom: true`：

```json
{
  "rules": {
    "fitting_standards": {
      "angles": {
        "allow_custom": true  // 允许任意角度
      }
    }
  }
}
```

### 6.4 配置文件格式错误怎么办？

使用 JSON 验证工具检查格式：

```bash
# 使用 Python 验证
python -m json.tool backend/app/config/rules/semantic_allowlist.json

# 或使用 jq (Linux/Mac)
jq . backend/app/config/rules/semantic_allowlist.json
```

---

**文档版本**：1.0  
**最后更新**：2024年  
**维护者**：OpenTruss 开发团队

