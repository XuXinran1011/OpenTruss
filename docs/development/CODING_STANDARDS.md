# OpenTruss 代码规范文档

## 1. 概述

本文档定义了 OpenTruss 项目的代码规范，确保代码质量、可维护性和团队协作效率。

---

## 2. Python 代码规范

### 2.1 代码风格

遵循 **PEP 8** Python 代码风格指南。

#### 2.1.1 命名规范

**变量和函数**:
```python
# 使用小写字母和下划线
user_name = "john"
def get_user_by_id(user_id: str) -> User:
    pass
```

**类名**:
```python
# 使用 PascalCase
class InspectionLotNode:
    pass

class ElementService:
    pass
```

**常量**:
```python
# 使用大写字母和下划线
MAX_RETRY_COUNT = 3
DEFAULT_TIMEOUT = 30
```

**私有成员**:
```python
# 使用单下划线前缀
class MyClass:
    def __init__(self):
        self._internal_var = None
    
    def _private_method(self):
        pass
```

#### 2.1.2 类型注解

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

**使用 Pydantic 模型**:
```python
from pydantic import BaseModel

class ElementNode(BaseModel):
    id: str
    speckle_type: str
    height: Optional[float] = None
```

#### 2.1.3 代码格式化

使用 **Black** 进行代码格式化：

```bash
# 安装
pip install black

# 格式化代码
black .

# 检查格式
black --check .
```

**配置** (`pyproject.toml`):
```toml
[tool.black]
line-length = 88
target-version = ['py310']
```

### 2.2 代码组织

#### 2.2.1 导入顺序

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

#### 2.2.2 模块结构

```python
"""
模块文档字符串
"""
# 导入
import ...

# 常量
CONSTANT = "value"

# 类型定义
TypeAlias = str

# 函数和类
def function():
    pass

class MyClass:
    pass
```

### 2.3 注释规范

#### 2.3.1 文档字符串

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

#### 2.3.2 行内注释

```python
# 好的注释：解释"为什么"
# 使用缓存避免重复查询数据库
cached_result = cache.get(key)

# 避免：解释"是什么"（代码已经很清楚）
# 设置高度为 3.0
height = 3.0  # 不好的注释
```

### 2.4 错误处理

#### 2.4.1 异常处理

```python
# 使用具体的异常类型
try:
    result = process_data(data)
except ValueError as e:
    logger.error(f"数据验证失败: {e}")
    raise
except Exception as e:
    logger.exception("未知错误")
    raise RuntimeError("处理失败") from e
```

#### 2.4.2 自定义异常

```python
class OpenTrussError(Exception):
    """基础异常类"""
    pass

class ValidationError(OpenTrussError):
    """验证错误"""
    pass

class DatabaseError(OpenTrussError):
    """数据库错误"""
    pass
```

---

## 3. 前端代码规范

### 3.1 TypeScript 规范

#### 3.1.1 类型定义

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

#### 3.1.2 组件规范

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

#### 3.1.3 命名规范

- **组件**: PascalCase (`ElementCard`)
- **函数/变量**: camelCase (`getElementById`)
- **常量**: UPPER_SNAKE_CASE (`MAX_ELEMENTS`)
- **类型/接口**: PascalCase (`ElementNode`)

### 3.2 代码格式化

使用 **Prettier** 和 **ESLint**:

**配置** (`.prettierrc`):
```json
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 80
}
```

**ESLint 配置** (`.eslintrc.js`):
```javascript
module.exports = {
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react/recommended',
  ],
  rules: {
    '@typescript-eslint/explicit-function-return-type': 'warn',
    'react/prop-types': 'off',
  },
};
```

### 3.3 文件组织

```
src/
├── components/          # 可复用组件
│   ├── ElementCard/
│   │   ├── ElementCard.tsx
│   │   ├── ElementCard.test.tsx
│   │   └── index.ts
├── pages/              # 页面组件
├── services/           # API 服务
├── hooks/              # 自定义 Hooks
├── utils/              # 工具函数
└── types/              # 类型定义
```

---

## 4. Git 工作流

### 4.1 分支策略

**主分支**:
- `main`: 生产环境代码
- `develop`: 开发环境代码

**功能分支**:
- `feature/功能名称`: 新功能开发
- `bugfix/问题描述`: 问题修复
- `hotfix/紧急修复`: 紧急修复

**示例**:
```bash
feature/inspection-lot-management
bugfix/element-topology-error
hotfix/memory-leak-fix
```

### 4.2 提交规范

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

### 4.3 提交消息规范

**好的提交消息**:
```bash
feat(workbench): 实现 Trace Mode 拓扑修复功能
fix(api): 修复检验批状态转换验证逻辑
docs(api): 更新 API 文档中的错误码说明
```

**不好的提交消息**:
```bash
更新代码
修复bug
WIP
```

### 4.4 Pull Request 规范

**PR 标题**:
```
feat: 添加检验批管理功能
```

**PR 描述模板**:
```markdown
## 变更说明
- 添加检验批创建接口
- 实现规则引擎
- 添加单元测试

## 相关 Issue
Closes #123

## 测试
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 手动测试完成

## 截图（如适用）
...
```

---

## 5. 代码审查检查清单

### 5.1 功能检查

- [ ] 代码实现了需求
- [ ] 边界情况已处理
- [ ] 错误处理完善
- [ ] 性能考虑合理

### 5.2 代码质量

- [ ] 遵循代码规范
- [ ] 命名清晰易懂
- [ ] 注释充分（特别是复杂逻辑）
- [ ] 无重复代码

### 5.3 测试

- [ ] 单元测试覆盖
- [ ] 集成测试通过
- [ ] 测试用例充分

### 5.4 文档

- [ ] API 文档更新
- [ ] 代码注释充分
- [ ] README 更新（如适用）

---

## 6. 工具配置

### 6.1 Pre-commit Hooks

使用 **pre-commit** 自动检查代码：

**安装**:
```bash
pip install pre-commit
pre-commit install
```

**配置** (`.prettierrc`):
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.0.0
    hooks:
      - id: prettier
```

### 6.2 IDE 配置

**VS Code** (`.vscode/settings.json`):
```json
{
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true,
    "source.organizeImports": true
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

---

## 7. 最佳实践

### 7.1 后端最佳实践

- **使用依赖注入**: FastAPI 的 `Depends`
- **异步优先**: 使用 `async/await`
- **错误处理**: 使用自定义异常和统一错误响应
- **日志记录**: 使用结构化日志
- **配置管理**: 使用环境变量和 Pydantic Settings

### 7.2 前端最佳实践

- **组件复用**: 提取可复用组件
- **状态管理**: 合理使用状态管理库
- **性能优化**: 使用 React.memo、useMemo、useCallback
- **错误边界**: 使用 Error Boundary 捕获错误
- **类型安全**: 充分利用 TypeScript 类型系统

---

**最后更新**：2025-12-28  
**文档版本**：1.0  
**维护者**：OpenTruss 开发团队

