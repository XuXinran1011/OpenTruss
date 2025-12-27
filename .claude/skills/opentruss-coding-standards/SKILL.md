---
name: opentruss-coding-standards
description: OpenTruss 项目代码规范和最佳实践指南
---

# OpenTruss 代码规范技能

当你编写或审查 OpenTruss 项目代码时，遵循本技能中的规范。

## Python 代码规范

### 命名规范

**变量和函数**: 使用小写字母和下划线
```python
user_name = "john"
def get_user_by_id(user_id: str) -> User:
    pass
```

**类名**: 使用 PascalCase
```python
class InspectionLotNode:
    pass

class ElementService:
    pass
```

**常量**: 使用大写字母和下划线
```python
MAX_RETRY_COUNT = 3
DEFAULT_TIMEOUT = 30
```

**私有成员**: 使用单下划线前缀
```python
class MyClass:
    def __init__(self):
        self._internal_var = None
    
    def _private_method(self):
        pass
```

### 类型注解

**必须使用类型注解**:
```python
from typing import Optional, List, Dict

def process_elements(
    elements: List[ElementNode],
    lot_id: Optional[str] = None
) -> Dict[str, int]:
    """处理构件列表"""
    pass
```

### 代码格式化

使用 **Black** 进行代码格式化：
```bash
black .
black --check .  # 检查格式
```

配置 (`pyproject.toml`):
```toml
[tool.black]
line-length = 88
target-version = ['py310']
```

### 导入顺序

```python
# 1. 标准库
import os
import sys
from typing import List, Optional

# 2. 第三方库
from fastapi import APIRouter, Depends
from pymemgraph import Memgraph

# 3. 本地模块
from app.models import ElementNode
from app.services import ElementService
```

### 文档字符串

使用 Google 风格文档字符串：
```python
def create_inspection_lot(
    item_id: str,
    spatial_scope: str,
    rule: Dict[str, Any]
) -> InspectionLotNode:
    """创建检验批
    
    Args:
        item_id: 分项 ID
        spatial_scope: 空间范围（如：Level:F1）
        rule: 划分规则
        
    Returns:
        创建的检验批节点
        
    Raises:
        ValueError: 当 item_id 不存在时
    """
    pass
```

### 错误处理

使用具体的异常类型：
```python
try:
    result = process_data(data)
except ValueError as e:
    logger.error(f"数据验证失败: {e}")
    raise
except Exception as e:
    logger.exception("未知错误")
    raise RuntimeError("处理失败") from e
```

## TypeScript 代码规范

### 类型定义

**使用接口定义类型**:
```typescript
interface ElementNode {
  id: string;
  speckleType: string;
  height?: number;
  baseOffset?: number;
  status: 'Draft' | 'Verified';
}
```

**使用类型别名**:
```typescript
type InspectionLotStatus = 
  | 'PLANNING' 
  | 'IN_PROGRESS' 
  | 'SUBMITTED' 
  | 'APPROVED' 
  | 'PUBLISHED';
```

### 组件规范

**函数组件**:
```typescript
import React from 'react';

interface ElementCardProps {
  element: ElementNode;
  onSelect?: (id: string) => void;
}

export const ElementCard: React.FC<ElementCardProps> = ({
  element,
  onSelect
}) => {
  const handleClick = () => {
    onSelect?.(element.id);
  };

  return (
    <div onClick={handleClick}>
      {/* ... */}
    </div>
  );
};
```

### 命名规范

- **组件**: PascalCase (`ElementCard`)
- **函数/变量**: camelCase (`getElementById`)
- **常量**: UPPER_SNAKE_CASE (`MAX_ELEMENTS`)
- **类型/接口**: PascalCase (`ElementNode`)

### 代码格式化

使用 **Prettier** 和 **ESLint**:
```bash
npm run lint
npm run format
```

## Git 工作流

### 提交规范

遵循 **Conventional Commits** 规范：

**格式**:
```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型**:
- `feat`: 新功能
- `fix`: 修复问题
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具相关

**示例**:
```bash
feat(api): 添加检验批创建接口

实现了 POST /api/v1/inspection-lots/strategy 端点，
支持按规则自动创建检验批。

Closes #123
```

### 分支策略

- `main`: 生产环境代码
- `develop`: 开发环境代码
- `feature/功能名称`: 新功能开发
- `bugfix/问题描述`: 问题修复
- `hotfix/紧急修复`: 紧急修复

## 最佳实践

### 后端最佳实践

- **使用依赖注入**: FastAPI 的 `Depends`
- **异步优先**: 使用 `async/await`
- **错误处理**: 使用自定义异常和统一错误响应
- **日志记录**: 使用结构化日志
- **配置管理**: 使用环境变量和 Pydantic Settings

### 前端最佳实践

- **组件复用**: 提取可复用组件
- **状态管理**: 合理使用 Zustand
- **性能优化**: 使用 React.memo、useMemo、useCallback
- **错误边界**: 使用 Error Boundary 捕获错误
- **类型安全**: 充分利用 TypeScript 类型系统

## 代码审查检查清单

### 功能检查
- [ ] 代码实现了需求
- [ ] 边界情况已处理
- [ ] 错误处理完善
- [ ] 性能考虑合理

### 代码质量
- [ ] 遵循代码规范
- [ ] 命名清晰易懂
- [ ] 注释充分（特别是复杂逻辑）
- [ ] 无重复代码

### 测试
- [ ] 单元测试覆盖
- [ ] 集成测试通过
- [ ] 测试用例充分

## 相关文档

- 完整代码规范: `docs/CODING_STANDARDS.md`
- 开发环境搭建: `docs/DEVELOPMENT.md`

