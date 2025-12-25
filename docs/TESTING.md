# OpenTruss 测试策略文档

## 1. 概述

本文档定义了 OpenTruss 项目的测试策略，确保代码质量和系统可靠性。

### 1.1 测试目标

- **功能正确性**: 确保功能按预期工作
- **代码质量**: 提高代码可维护性
- **回归预防**: 防止新代码破坏现有功能
- **文档作用**: 测试即文档，展示代码用法

### 1.2 测试金字塔

```
        /\
       /  \      E2E Tests (少量)
      /    \
     /______\    Integration Tests (适量)
    /        \
   /__________\  Unit Tests (大量)
```

---

## 2. 测试类型

### 2.1 单元测试 (Unit Tests)

**目标**: 测试单个函数或类的功能

**覆盖率要求**: ≥ 80%

**工具**:
- **Python**: `pytest`
- **前端**: `Jest` + `React Testing Library`

**示例** (Python):
```python
import pytest
from app.services.element_service import ElementService

def test_create_element():
    """测试创建构件"""
    service = ElementService()
    element = service.create_element(
        speckle_type="Wall",
        geometry_2d={"type": "Polyline", "coordinates": [[0, 0], [10, 0]]}
    )
    assert element.id is not None
    assert element.speckle_type == "Wall"
```

**示例** (TypeScript):
```typescript
import { render, screen } from '@testing-library/react';
import { ElementCard } from './ElementCard';

describe('ElementCard', () => {
  it('should render element information', () => {
    const element = {
      id: 'element_001',
      speckleType: 'Wall',
      status: 'Draft',
    };
    
    render(<ElementCard element={element} />);
    
    expect(screen.getByText('element_001')).toBeInTheDocument();
    expect(screen.getByText('Wall')).toBeInTheDocument();
  });
});
```

### 2.2 集成测试 (Integration Tests)

**目标**: 测试多个组件之间的交互

**覆盖率要求**: ≥ 60%

**工具**:
- **Python**: `pytest` + `pytest-asyncio`
- **前端**: `Jest` + `MSW` (Mock Service Worker)

**示例** (API 集成测试):
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_inspection_lot():
    """测试创建检验批"""
    response = client.post(
        "/api/inspection-lots/strategy",
        json={
            "item_id": "item_001",
            "rule": {"type": "by_level"},
        },
        headers={"Authorization": "Bearer test_token"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert len(data["data"]["created_lots"]) > 0
```

### 2.3 E2E 测试 (End-to-End Tests)

**目标**: 测试完整的用户流程

**覆盖率要求**: 关键流程 100%

**工具**:
- **Playwright** 或 **Cypress**

**示例** (E2E 测试):
```typescript
import { test, expect } from '@playwright/test';

test('检验批创建流程', async ({ page }) => {
  // 1. 登录
  await page.goto('/login');
  await page.fill('[name="username"]', 'approver@example.com');
  await page.fill('[name="password"]', 'password');
  await page.click('button[type="submit"]');
  
  // 2. 导航到检验批管理
  await page.click('text=检验批管理');
  
  // 3. 选择分项
  await page.selectOption('[name="item"]', 'item_001');
  
  // 4. 定义规则
  await page.click('input[value="by_level"]');
  
  // 5. 创建检验批
  await page.click('button:has-text("创建检验批")');
  
  // 6. 验证结果
  await expect(page.locator('.success-message')).toBeVisible();
  await expect(page.locator('.inspection-lot-item')).toHaveCount(2);
});
```

---

## 3. 测试场景

### 3.1 数据摄入测试

**场景 1: 正常摄入**
- 输入: 有效的 Speckle Objects
- 预期: 成功创建 Element 节点

**场景 2: 缺失字段**
- 输入: 缺少 height、material 的构件
- 预期: 成功创建，但 status 为 Draft

**场景 3: 无效几何数据**
- 输入: 格式错误的 geometry_2d
- 预期: 返回 422 错误

### 3.2 数据清洗测试

**场景 1: Trace Mode - 修复拓扑**
- 操作: 拖拽构件节点
- 预期: 更新 CONNECTED_TO 关系

**场景 2: Lift Mode - 批量设置 Z 轴**
- 操作: 选择多个构件，设置高度
- 预期: 所有选中构件的高度更新

**场景 3: Classify Mode - 归类构件**
- 操作: 拖拽构件到分项
- 预期: 构件的 item_id 更新

### 3.3 检验批管理测试

**场景 1: 创建检验批策略**
- 输入: 分项 ID + 划分规则
- 预期: 自动创建多个检验批并关联构件

**场景 2: 人工微调**
- 操作: 手动添加/移除构件
- 预期: 检验批的构件列表更新

**场景 3: 锁定机制**
- 操作: 创建检验批后尝试修改构件
- 预期: 锁定状态阻止修改

### 3.4 审批工作流测试

**场景 1: 提交审批 - 完整性验证通过**
- 操作: 提交包含完整构件的检验批
- 预期: 状态变为 SUBMITTED

**场景 2: 提交审批 - 完整性验证失败**
- 操作: 提交包含不完整构件的检验批
- 预期: 返回 422 错误，列出缺失字段

**场景 3: 审批通过**
- 操作: Approver 审批检验批
- 预期: 状态变为 APPROVED

**场景 4: 驳回**
- 操作: Approver/PM 驳回检验批
- 预期: 状态回退，构件解锁

### 3.5 IFC 导出测试

**场景 1: 导出已验收检验批**
- 输入: APPROVED 状态的检验批
- 预期: 成功生成 IFC 文件

**场景 2: 导出未验收检验批**
- 输入: IN_PROGRESS 状态的检验批
- 预期: 返回 422 错误

**场景 3: IFC 文件验证**
- 操作: 导出 IFC 文件
- 预期: 文件可被 Revit/Navisworks 读取

---

## 4. 测试数据管理

### 4.1 测试数据准备

**使用 Fixtures** (pytest):
```python
import pytest
from app.models import ElementNode

@pytest.fixture
def sample_element():
    """示例构件数据"""
    return ElementNode(
        id="element_001",
        speckle_type="Wall",
        geometry_2d={
            "type": "Polyline",
            "coordinates": [[0, 0], [10, 0], [10, 5], [0, 5], [0, 0]]
        },
        level_id="level_f1"
    )

@pytest.fixture
def sample_inspection_lot():
    """示例检验批数据"""
    return {
        "id": "lot_001",
        "name": "1#楼F1层填充墙砌体检验批",
        "item_id": "item_001",
        "spatial_scope": "Level:F1",
        "status": "IN_PROGRESS"
    }
```

### 4.2 测试数据库

**使用测试专用数据库**:
```python
# conftest.py
import pytest
from pymemgraph import Memgraph

@pytest.fixture(scope="session")
def test_db():
    """测试数据库连接"""
    db = Memgraph("localhost", 7687, database="test")
    yield db
    # 清理测试数据
    db.execute("MATCH (n) DETACH DELETE n")
```

### 4.3 数据隔离

- 每个测试用例使用独立的数据
- 测试前后清理数据
- 使用事务回滚（如支持）

---

## 5. Mock 和 Stub

### 5.1 外部服务 Mock

**Mock Memgraph 查询**:
```python
from unittest.mock import Mock, patch

@patch('app.services.element_service.Memgraph')
def test_get_elements(mock_memgraph):
    """测试获取构件列表"""
    # 设置 Mock 返回值
    mock_memgraph.return_value.execute_and_fetch.return_value = [
        {"id": "element_001", "speckle_type": "Wall"}
    ]
    
    service = ElementService()
    elements = service.get_elements()
    
    assert len(elements) == 1
    assert elements[0].id == "element_001"
```

### 5.2 API Mock (前端)

**使用 MSW**:
```typescript
import { rest } from 'msw';
import { setupServer } from 'msw/node';

const server = setupServer(
  rest.get('/api/v1/elements', (req, res, ctx) => {
    return res(
      ctx.json({
        status: 'success',
        data: {
          items: [
            { id: 'element_001', speckleType: 'Wall' }
          ]
        }
      })
    );
  })
);
```

---

## 6. 测试覆盖率

### 6.1 覆盖率目标

| 测试类型 | 覆盖率目标 |
|---------|-----------|
| 单元测试 | ≥ 80% |
| 集成测试 | ≥ 60% |
| E2E 测试 | 关键流程 100% |

### 6.2 覆盖率工具

**Python**:
```bash
# 安装
pip install pytest-cov

# 运行测试并生成报告
pytest --cov=app --cov-report=html
```

**前端**:
```bash
# Jest 配置
npm test -- --coverage
```

### 6.3 覆盖率报告

- 使用 HTML 报告查看详细覆盖率
- CI/CD 中集成覆盖率检查
- 覆盖率低于目标时阻止合并

---

## 7. 性能测试

### 7.1 负载测试

**工具**: `locust` 或 `k6`

**场景**:
- API 响应时间测试
- 并发用户测试
- 数据库查询性能测试

**示例** (Locust):
```python
from locust import HttpUser, task, between

class OpenTrussUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def get_elements(self):
        self.client.get("/api/v1/elements")
    
    @task(3)
    def create_inspection_lot(self):
        self.client.post(
            "/api/v1/inspection-lots/strategy",
            json={"item_id": "item_001", "rule": {"type": "by_level"}}
        )
```

### 7.2 压力测试

- 测试系统在极限负载下的表现
- 识别性能瓶颈
- 验证系统稳定性

---

## 8. CI/CD 集成

### 8.1 GitHub Actions 工作流

项目使用 GitHub Actions 进行自动化测试，包含以下工作流：

- **CI 工作流** (`.github/workflows/ci.yml`): 
  - 前端代码检查和单元测试
  - 后端代码检查和单元测试
  - 集成测试
  - 构建验证
  
- **E2E 测试工作流** (`.github/workflows/e2e.yml`): 
  - 端到端测试
  - 使用 Playwright 测试完整用户流程
  
- **性能测试工作流** (`.github/workflows/performance-tests.yml`): 
  - 使用 Locust 和 k6 进行性能测试
  - 定时运行和手动触发

详细的配置说明请参考 [GitHub Actions 配置指南](./GITHUB_ACTIONS_SETUP.md)。

### 8.2 测试流程

1. **提交前检查**: 本地运行测试确保通过
2. **PR 检查**: CI 自动运行所有测试
3. **合并前**: 必须通过所有测试检查
4. **部署前**: 运行 E2E 测试验证功能

### 8.3 本地运行 CI 检查

在推送代码前，可以在本地运行 CI 检查：

```bash
# 前端
cd frontend
npm run lint          # ESLint 检查
npm run test          # 单元测试
npm run build         # 构建检查

# 后端
cd backend
pytest tests/         # 运行所有测试
pytest --cov=app tests/  # 带覆盖率
```

---

## 9. 测试最佳实践

### 9.1 测试编写原则

- **独立性**: 测试之间不相互依赖
- **可重复**: 每次运行结果一致
- **快速**: 单元测试应该快速执行
- **清晰**: 测试名称和断言清晰表达意图

### 9.2 测试维护

- 定期更新测试用例
- 删除过时的测试
- 重构测试代码
- 保持测试代码质量

### 9.3 测试文档

- 为复杂测试添加注释
- 记录测试场景和预期结果
- 维护测试数据说明

---

## 10. 测试工具清单

### 10.1 Python 测试工具

- `pytest`: 测试框架
- `pytest-asyncio`: 异步测试支持
- `pytest-cov`: 覆盖率工具
- `pytest-mock`: Mock 工具
- `faker`: 测试数据生成

### 10.2 前端测试工具

- `Jest`: 测试框架
- `React Testing Library`: React 组件测试
- `MSW`: API Mock
- `Playwright`: E2E 测试

### 10.3 性能测试工具

- `locust`: 负载测试
- `k6`: 性能测试
- `Apache Bench`: 简单负载测试

---

---

## 11. 相关文档

- [E2E测试指南](E2E_TESTING.md) - 详细的E2E测试使用说明
- [性能测试指南](PERFORMANCE_TESTING.md) - Locust和k6性能测试详细指南

---

*文档版本：1.1*  
*最后更新：增加了E2E测试和性能测试的详细文档链接*

