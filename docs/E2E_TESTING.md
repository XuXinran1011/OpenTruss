# E2E测试指南

## 概述

本文档介绍如何使用Playwright进行OpenTruss项目的端到端（E2E）测试。

## 前置要求

1. **Node.js**: 版本 20 或更高
2. **Playwright**: 通过npm安装
3. **运行环境**: 
   - 后端服务运行在 `http://localhost:8000`
   - 前端服务运行在 `http://localhost:3000`
   - Memgraph数据库运行在 `localhost:7687`

## 安装

```bash
cd frontend
npm install
npx playwright install --with-deps
```

## 运行测试

### 运行所有E2E测试

```bash
npm run test:e2e
```

### 运行特定测试文件

```bash
npx playwright test e2e/auth.spec.ts
npx playwright test e2e/workbench.spec.ts
```

### 以UI模式运行（推荐用于调试）

```bash
npm run test:e2e:ui
```

### 以调试模式运行

```bash
npm run test:e2e:debug
```

### 以headed模式运行（显示浏览器）

```bash
npm run test:e2e:headed
```

### 查看测试报告

```bash
npm run test:e2e:report
```

## 测试结构

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

## 测试用例说明

### 1. 认证流程 (`auth.spec.ts`)

- 登录成功/失败场景
- 不同角色的登录测试
- 登出流程
- Token过期处理
- 权限控制验证

### 2. Workbench基础功能 (`workbench.spec.ts`)

- 页面加载
- 层级树渲染
- Canvas视图渲染
- 模式切换
- 快捷键测试

### 3. 工作模式测试

#### Trace Mode (`trace-mode.spec.ts`)
- 拓扑修复
- 构件拖拽调整
- DWG底图上传

#### Lift Mode (`lift-mode.spec.ts`)
- 批量选择构件
- Z轴参数设置（高度、基础偏移、材质）
- 批量应用参数

#### Classify Mode (`classify-mode.spec.ts`)
- 构件归类操作
- 拖拽到分项
- 批量归类

### 4. 检验批相关测试

#### 检验批策略 (`lot-strategy.spec.ts`)
- 规则选择（按楼层/区域/组合）
- 预览结果
- 批量创建检验批

#### 检验批管理 (`lot-management.spec.ts`)
- 检验批列表查看
- 构件分配/移除
- 状态更新

### 5. 审批工作流 (`approval-workflow.spec.ts`)

- 提交审批
- 审批通过/驳回
- 审批历史查看

### 6. IFC导出 (`export.spec.ts`)

- 单个检验批导出
- 批量导出
- 项目导出

## 辅助函数

### 认证辅助函数 (`helpers/auth.ts`)

```typescript
// 以Editor角色登录
await loginAsEditor(page);

// 以Approver角色登录
await loginAsApprover(page);

// 通用登录
await login(page, 'username', 'password');

// 登出
await logout(page);
```

### 测试数据生成 (`helpers/test-data.ts`)

```typescript
// 生成测试项目
const project = generateTestProject();

// 生成测试构件
const element = generateTestElement('Wall');

// 生成批量构件
const elements = generateBatchTestElements(100);
```

### API调用辅助 (`helpers/api.ts`)

```typescript
// 获取认证Token
const token = await getAuthToken('editor', 'editor123');

// 创建测试数据
await createTestProject(token, projectId, name);

// 清理测试数据
await cleanupTestData(token, projectId);
```

## 配置

E2E测试配置位于 `frontend/playwright.config.ts`：

- **baseURL**: 测试基础URL（默认: `http://localhost:3000`）
- **timeout**: 测试超时时间（默认: 30秒）
- **browsers**: 测试浏览器（Chromium, Firefox, WebKit）

可以通过环境变量覆盖：

```bash
PLAYWRIGHT_BASE_URL=http://localhost:3000 npm run test:e2e
```

## 调试技巧

### 1. 使用UI模式

UI模式提供可视化的测试运行界面，方便调试：

```bash
npm run test:e2e:ui
```

### 2. 使用调试模式

调试模式会暂停执行，允许单步调试：

```bash
npm run test:e2e:debug
```

### 3. 查看截图和视频

测试失败时，Playwright会自动保存：
- 截图：`test-results/`
- 视频：`test-results/`（如果启用）

### 4. 使用 `page.pause()`

在测试代码中添加 `await page.pause()` 可以暂停执行并打开Playwright Inspector。

### 5. 查看网络请求

```typescript
// 监听网络请求
page.on('request', request => console.log('Request:', request.url()));
page.on('response', response => console.log('Response:', response.url(), response.status()));
```

## 最佳实践

1. **测试隔离**: 每个测试应该是独立的，不依赖其他测试的状态
2. **等待策略**: 使用 `page.waitForSelector()` 或 `page.waitForURL()` 而不是硬编码的 `sleep()`
3. **选择器**: 优先使用 `data-testid` 属性，其次使用稳定的CSS选择器
4. **错误处理**: 测试应该能够处理异步操作和网络错误
5. **数据清理**: 测试后清理创建的测试数据

## 常见问题

### 测试失败：元素未找到

- 检查元素选择器是否正确
- 增加等待时间
- 使用 `page.waitForSelector()` 等待元素出现

### 测试超时

- 增加 `timeout` 配置
- 检查网络请求是否正常
- 检查后端服务是否正常运行

### 浏览器无法启动

- 运行 `npx playwright install` 安装浏览器
- 检查系统依赖是否已安装

## CI/CD集成

E2E测试已集成到GitHub Actions工作流中（`.github/workflows/e2e.yml`），在每次push和pull request时自动运行。

## 参考资料

- [Playwright文档](https://playwright.dev/)
- [Playwright最佳实践](https://playwright.dev/docs/best-practices)

