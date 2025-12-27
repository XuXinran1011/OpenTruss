# GitHub Actions 配置指南

本文档说明如何配置和使用 OpenTruss 项目的 GitHub Actions 工作流。

## 概述

项目包含以下 GitHub Actions 工作流：

1. **CI 工作流** (`.github/workflows/ci.yml`) - 持续集成
2. **E2E 测试工作流** (`.github/workflows/e2e.yml`) - 端到端测试
3. **性能测试工作流** (`.github/workflows/performance-tests.yml`) - 性能测试

## 工作流说明

### 1. CI 工作流 (`ci.yml`)

**触发条件**:
- 推送到 `main` 或 `develop` 分支
- 创建 Pull Request 到 `main` 或 `develop` 分支
- 手动触发 (`workflow_dispatch`)

**包含的作业**:

#### 前端作业
- **frontend-lint**: 运行 ESLint 检查代码质量
- **frontend-unit-tests**: 运行 Jest 单元测试并生成覆盖率报告
- **frontend-build**: 构建 Next.js 应用，验证构建成功

#### 后端作业
- **backend-lint**: 运行 Ruff、Black 和 MyPy 检查代码质量
- **backend-unit-tests**: 运行 Pytest 单元测试，生成覆盖率报告
- **backend-integration-tests**: 运行 API 和集成测试

#### 状态汇总
- **ci-status**: 汇总所有检查的结果状态

### 2. E2E 测试工作流 (`e2e.yml`)

**触发条件**:
- 推送到 `main` 或 `develop` 分支
- 创建 Pull Request 到 `main` 或 `develop` 分支
- 手动触发 (`workflow_dispatch`)

**包含的步骤**:
1. 设置 Memgraph 数据库服务
2. 安装后端依赖并初始化数据库
3. 启动后端服务器
4. 安装前端依赖并构建应用
5. 启动前端服务器
6. 安装 Playwright
7. 运行 E2E 测试
8. 上传测试报告和结果

### 3. 性能测试工作流 (`performance-tests.yml`)

**触发条件**:
- 定时运行（每天 UTC 时间 2:00）
- 手动触发，可选择测试类型（Locust 或 k6）

**包含的步骤**:
1. 设置 Memgraph 数据库服务
2. 启动后端服务器
3. 运行 Locust 或 k6 性能测试
4. 上传性能测试报告

## 必需的 GitHub Secrets

当前工作流**不需要**额外的 secrets，但如果你想自定义某些配置，可以添加以下 secrets：

### 可选 Secrets

- `NEXT_PUBLIC_API_URL`: 前端 API URL（默认使用 `http://localhost:8000`）
- `CODECOV_TOKEN`: Codecov token（用于上传代码覆盖率报告）

## 代码质量工具配置（可选）

### 后端代码质量工具

CI 工作流支持以下 Python 代码质量工具（需要手动配置）：

1. **Ruff**: 快速的 Python linter 和 formatter
   ```bash
   pip install ruff
   ruff init
   ```

2. **Black**: Python 代码格式化工具
   ```bash
   pip install black
   ```

3. **MyPy**: Python 静态类型检查
   ```bash
   pip install mypy
   ```

如果未配置这些工具，CI 工作流中的 linting 步骤会跳过，不会导致构建失败。

### 前端代码质量工具

前端已经配置了 ESLint（通过 Next.js），无需额外配置。

## 代码覆盖率

CI 工作流会自动上传代码覆盖率到 Codecov（如果配置了 Codecov token）。

### 配置 Codecov（可选）

1. 访问 [Codecov](https://codecov.io/) 并连接你的 GitHub 仓库
2. 获取仓库的 Codecov token
3. 在 GitHub 仓库设置中添加 Secret：
   - Settings → Secrets and variables → Actions → New repository secret
   - Name: `CODECOV_TOKEN`
   - Value: 你的 Codecov token

如果未配置 Codecov token，工作流仍然会运行，但不会上传覆盖率报告。

## 运行工作流

### 自动运行

工作流会在以下情况自动运行：
- 推送代码到 `main` 或 `develop` 分支
- 创建 Pull Request 到 `main` 或 `develop` 分支
- E2E 和性能测试也会自动运行

### 手动运行

1. 访问 GitHub 仓库的 Actions 标签页
2. 选择要运行的工作流
3. 点击 "Run workflow" 按钮
4. 选择分支和参数（如果有）
5. 点击 "Run workflow"

## 查看结果

### 在工作流页面查看

1. 访问 GitHub 仓库的 Actions 标签页
2. 点击具体的工作流运行记录
3. 查看每个作业的执行结果
4. 下载构建产物和测试报告（如果可用）

### 查看测试报告

- **前端单元测试覆盖率**: 在 `frontend-unit-tests` 作业中查看
- **后端单元测试覆盖率**: 下载 `backend-coverage-html` 产物
- **E2E 测试报告**: 下载 `playwright-report` 产物
- **性能测试报告**: 下载 `performance-reports` 产物

## 故障排除

### CI 工作流失败

**前端 Lint 失败**:
- 检查 ESLint 错误并修复代码风格问题
- 运行 `npm run lint` 本地检查

**前端构建失败**:
- 检查构建错误日志
- 确保所有依赖都已正确安装
- 检查环境变量配置

**后端 Lint 失败**:
- 运行 `ruff check .` 检查问题
- 运行 `ruff format .` 自动修复格式问题
- 运行 `black .` 格式化代码

**单元测试失败**:
- 查看测试输出日志
- 在本地运行失败的测试：`pytest tests/path/to/test_file.py -v`
- 检查测试覆盖率是否低于阈值

### E2E 测试失败

**服务启动失败**:
- 检查 Memgraph 服务是否正常启动
- 检查后端服务器是否正常启动
- 检查前端构建是否成功

**测试超时**:
- 检查 `playwright.config.ts` 中的超时设置
- 增加等待时间或优化测试代码

**测试不稳定**:
- 检查是否有竞态条件
- 增加适当的等待和重试逻辑

### 性能测试失败

**Locust 测试失败**:
- 检查后端服务器是否正常运行
- 检查测试配置是否正确
- 查看 Locust 报告了解性能瓶颈

**k6 测试失败**:
- 确保 k6 已正确安装
- 检查 k6 脚本配置是否正确
- 查看 k6 输出了解性能指标

## 优化建议

1. **并行执行**: CI 工作流中的作业已经并行执行，以加快速度
2. **缓存**: 已配置 Node.js 和 Python 依赖缓存
3. **选择性运行**: 可以使用路径过滤，只在相关文件更改时运行测试
4. **矩阵测试**: 可以添加矩阵策略测试多个 Python/Node.js 版本
5. **通知**: 可以添加 Slack/Email 通知，在工作流失败时发送提醒

## 工作流文件位置

```
.github/workflows/
├── ci.yml                  # CI 工作流（单元测试、代码检查、构建）
├── e2e.yml                 # E2E 测试工作流
└── performance-tests.yml   # 性能测试工作流
```

## 相关文档

- [测试文档](testing/README.md) - 测试策略、E2E测试和性能测试完整指南
- [E2E 测试指南](testing/E2E_TESTING.md)
- [性能测试指南](testing/PERFORMANCE_TESTING.md)

