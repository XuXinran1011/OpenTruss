# OpenTruss 测试文档

本文档整合了 OpenTruss 项目的所有测试相关文档，包括测试策略、E2E测试指南和性能测试指南。

## 目录

- [1. 测试策略概述](#1-测试策略概述)
- [2. 单元测试](#2-单元测试)
- [3. 集成测试](#3-集成测试)
- [4. E2E测试](#4-e2e测试)
- [5. 性能测试](#5-性能测试)
- [6. 测试报告](#6-测试报告)

---

## 1. 测试策略概述

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

## 2. 单元测试

### 2.1 概述

**目标**: 测试单个函数或类的功能

**覆盖率要求**: ≥ 80%

**工具**:
- **Python**: `pytest`
- **前端**: `Jest` + `React Testing Library`

### 2.2 Python 单元测试示例

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

### 2.3 TypeScript 单元测试示例

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

### 2.4 运行单元测试

```bash
# Python 后端
cd backend
pytest

# 前端
cd frontend
npm test
```

---

## 3. 集成测试

### 3.1 概述

**目标**: 测试多个组件之间的交互

**覆盖率要求**: ≥ 60%

**工具**:
- **Python**: `pytest` + `pytest-asyncio`
- **前端**: `Jest` + `MSW` (Mock Service Worker)

### 3.2 API 集成测试示例

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
            "rule": {"type": "by_level"}
        }
    )
    assert response.status_code == 201
    assert response.json()["status"] == "success"
```

### 3.3 运行集成测试

```bash
# Python 后端
cd backend
pytest tests/test_integration/

# 前端
cd frontend
npm run test:integration
```

---

## 4. E2E测试

详细内容请参考 [E2E测试指南](./E2E_TESTING.md)

### 4.1 概述

E2E（端到端）测试使用 Playwright 进行，测试完整的用户工作流程。

### 4.2 前置要求

1. **Node.js**: 版本 20 或更高
2. **Playwright**: 通过npm安装
3. **运行环境**: 
   - 后端服务运行在 `http://localhost:8000`
   - 前端服务运行在 `http://localhost:3000`
   - Memgraph数据库运行在 `localhost:7687`

### 4.3 安装

```bash
cd frontend
npm install
npx playwright install --with-deps
```

### 4.4 运行测试

```bash
# 运行所有E2E测试
npm run test:e2e

# 运行特定测试文件
npx playwright test e2e/auth.spec.ts
npx playwright test e2e/workbench.spec.ts

# 以UI模式运行（推荐用于调试）
npm run test:e2e:ui

# 以调试模式运行
npm run test:e2e:debug
```

### 4.5 测试结构

```
frontend/e2e/
├── helpers/              # 辅助函数
│   ├── auth.ts          # 认证辅助函数
│   ├── test-data.ts     # 测试数据生成
│   └── api.ts           # API调用辅助函数
├── auth.spec.ts         # 认证流程测试
├── workbench.spec.ts    # Workbench基础功能测试
├── trace-mode.spec.ts   # Trace模式测试
├── lift-mode.spec.ts    # Lift模式测试
├── classify-mode.spec.ts # Classify模式测试
├── lot-strategy.spec.ts  # 检验批策略测试
├── lot-management.spec.ts # 检验批管理测试
├── approval-workflow.spec.ts # 审批工作流测试
└── export.spec.ts       # IFC导出测试
```

---

## 5. 性能测试

详细内容请参考 [性能测试指南](./PERFORMANCE_TESTING.md)

### 5.1 概述

OpenTruss 使用 Locust 和 k6 进行性能测试。

### 5.2 Locust 性能测试

#### 安装

```bash
cd backend
pip install -r requirements-dev.txt
```

#### 运行测试

```bash
# 启动Locust Web UI
locust -f tests/performance/locust/auth_load_test.py --host http://localhost:8000

# Headless模式（无UI）
locust -f tests/performance/locust/auth_load_test.py \
  --host http://localhost:8000 \
  --users 50 \
  --spawn-rate 5 \
  --run-time 5m \
  --headless \
  --html reports/locust_report.html
```

#### 可用的测试脚本

- `auth_load_test.py`: 认证API性能测试
- `elements_load_test.py`: 构件API性能测试
- `hierarchy_load_test.py`: 层级结构API性能测试
- `lots_load_test.py`: 检验批API性能测试
- `approval_load_test.py`: 审批API性能测试
- `comprehensive_load_test.py`: 综合性能测试

### 5.3 k6 性能测试

#### 安装

```bash
# Windows (使用Chocolatey)
choco install k6

# Linux/Mac
# https://k6.io/docs/getting-started/installation/
```

#### 运行测试

```bash
# 运行单个测试脚本
k6 run tests/performance/k6/auth_test.js

# 使用环境变量
API_BASE_URL=http://localhost:8000 k6 run tests/performance/k6/auth_test.js
```

#### 性能指标

- **响应时间**: 平均、最小、最大、P50、P95、P99
- **吞吐量**: RPS (Requests Per Second)
- **错误率**: 失败的请求百分比
- **并发用户数**: 当前活跃的虚拟用户数

---

## 6. 测试报告

E2E测试报告请参考 [测试报告目录](./reports/)

### 6.1 查看报告

- **Locust**: 访问 `http://localhost:8089` 查看实时报告
- **k6**: 测试完成后在终端显示报告
- **Playwright**: 使用 `npm run test:e2e:report` 查看HTML报告

### 6.2 持续集成

测试集成到 CI/CD 流程中，每次提交代码时自动运行测试。详见 [GitHub Actions 配置](../GITHUB_ACTIONS_SETUP.md)。

---

## 相关文档

- [E2E测试详细指南](./E2E_TESTING.md) - Playwright E2E 测试详细说明
- [性能测试详细指南](./PERFORMANCE_TESTING.md) - Locust 和 k6 性能测试详细说明
- [测试报告](./reports/) - E2E 测试报告
- [GitHub Actions 配置](../GITHUB_ACTIONS_SETUP.md) - CI/CD 工作流配置
- [开发文档](../development/DEVELOPMENT.md) - 开发环境搭建

---

*文档版本：2.0*  
*最后更新：2025-12-27*  
*维护者：OpenTruss 开发团队
