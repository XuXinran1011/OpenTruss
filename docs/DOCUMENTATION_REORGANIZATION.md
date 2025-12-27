# 文档整理说明

本文档说明了 OpenTruss 项目的文档整理工作，包括新的文档结构和整合的文档。

## 整理日期

2025-12-27

## 更新记录

### 2025-12-27 更新

- **删除重复的Speckle文档**：删除了 `README_SPECKLE_CONVERSION.md` 和 `README_SPECKLE_LOCAL_SETUP.md`
  - 原因：Speckle模型已经完全集成到代码中（`backend/app/models/speckle/`），转换脚本已存在，详细内容已整合到 `docs/development/DEVELOPMENT.md`
  - 关键信息已保留在开发文档的"4.1 Speckle 模型"章节中

## 整理内容

### 1. 创建新的目录结构

按照文档类型和用途，创建了以下目录结构：

```
docs/
├── api/              # API 文档
├── architecture/     # 架构图表
├── deployment/       # 部署运维文档
├── development/      # 开发文档
├── features/         # 功能特性文档
├── guides/           # 用户指南
├── references/       # 参考文档
├── reports/          # 报告文档
├── rules/            # 规则引擎文档
└── testing/          # 测试文档
```

### 2. 整合的文档

#### API 文档整合 ✅
- **旧结构**：
  - `docs/API.md` - API设计文档
  - `docs/API_USAGE.md` - API使用文档
  - `docs/API_HANGERS.md` - 支吊架API文档
  
- **新结构**：
  - `docs/api/index.md` - API完整参考（整合了API.md的内容）
  - `docs/api/usage.md` - API使用指南（从API_USAGE.md移动）
  - `docs/api/hangers.md` - 支吊架API（从API_HANGERS.md移动）

#### 测试文档整合 ✅
- **旧结构**：
  - `docs/TESTING.md` - 测试策略
  - `docs/E2E_TESTING.md` - E2E测试指南
  - `docs/PERFORMANCE_TESTING.md` - 性能测试指南
  
- **新结构**：
  - `docs/testing/README.md` - 测试文档索引（整合了测试策略的核心内容）
  - `docs/testing/E2E_TESTING.md` - E2E测试详细指南（保留详细内容）
  - `docs/testing/PERFORMANCE_TESTING.md` - 性能测试详细指南（保留详细内容）

#### MEP路由文档组织 ✅
- **旧结构**：
  - 5个独立的MEP路由相关文档
  
- **新结构**：
  - `docs/features/README.md` - MEP路由规划文档索引（新增）
  - 保留5个详细文档，通过README.md提供统一入口和导航
  - 这种方式既保持了详细内容的完整性，又提供了清晰的导航结构

#### 架构文档整理 ✅
- **旧结构**：
  - `docs/ARCHITECTURE.md` - 保留在根目录
  - `docs/ARCHITECTURE_DIAGRAMS.md` - 架构图文档
  - `docs/diagrams.md` - 设计图表
  
- **新结构**：
  - `docs/ARCHITECTURE.md` - 保留在根目录
  - `docs/architecture/diagrams-architecture.md` - 从ARCHITECTURE_DIAGRAMS.md移动
  - `docs/architecture/diagrams.md` - 从diagrams.md移动

#### 规则引擎文档整合 ✅
- **旧结构**：
  - `docs/RULE_ENGINE.md` - 规则引擎文档
  - `docs/RULE_CONFIG_EXAMPLES.md` - 规则配置示例
  - `RuleEngine.md` - 根目录重复文档（已删除）
  
- **新结构**：
  - `docs/rules/RULE_ENGINE.md` - 从RULE_ENGINE.md移动
  - `docs/rules/RULE_CONFIG_EXAMPLES.md` - 从RULE_CONFIG_EXAMPLES.md移动
  - 删除了根目录的`RuleEngine.md`（重复文档）

#### 根目录文档移动 ✅
- `CODE_REVIEW_REPORT.md` → `docs/reports/CODE_REVIEW_REPORT.md`
- `HANGER_SERVICE_CODE_REVIEW.md` → `docs/reports/HANGER_SERVICE_CODE_REVIEW.md`
- `AGENTS.md` → `docs/development/AGENTS.md`
- `DEPENDENCIES.md` → `docs/development/DEPENDENCIES.md`

#### 分类文档移动 ✅

**开发文档**：
- `docs/DEVELOPMENT.md` → `docs/development/DEVELOPMENT.md`
- `docs/CODING_STANDARDS.md` → `docs/development/CODING_STANDARDS.md`

**测试文档**：
- `docs/TESTING.md` → 已整合到 `docs/testing/README.md`
- `docs/E2E_TESTING.md` → `docs/testing/E2E_TESTING.md`
- `docs/PERFORMANCE_TESTING.md` → `docs/testing/PERFORMANCE_TESTING.md`
- `docs/E2E_TEST_REPORT.md` → `docs/testing/reports/E2E_TEST_REPORT.md`

**部署运维文档**：
- `docs/DEPLOYMENT.md` → `docs/deployment/DEPLOYMENT.md`
- `docs/OPERATIONS.md` → `docs/deployment/OPERATIONS.md`
- `docs/MONITORING.md` → `docs/deployment/MONITORING.md`

**用户指南**：
- `docs/USER_MANUAL.md` → `docs/guides/USER_MANUAL.md`
- `docs/UI_DESIGN.md` → `docs/guides/UI_DESIGN.md`

**功能特性文档**：
- `docs/MEP_ROUTING.md` → `docs/features/MEP_ROUTING.md`
- `docs/MEP_ROUTING_DETAILED.md` → `docs/features/MEP_ROUTING_DETAILED.md`
- `docs/MEP_COORDINATION.md` → `docs/features/MEP_COORDINATION.md`
- `docs/MEP_SYSTEM_PRIORITY.md` → `docs/features/MEP_SYSTEM_PRIORITY.md`
- `docs/MEP_PENETRATION.md` → `docs/features/MEP_PENETRATION.md`
- 新增 `docs/features/README.md` - MEP路由规划文档索引

**参考文档**：
- `docs/PRD.md` → `docs/references/PRD.md`
- `docs/SCHEMA.md` → `docs/references/SCHEMA.md`
- `docs/PHASE_REFERENCE.md` → `docs/references/PHASE_REFERENCE.md`
- `docs/OPENSKILLS_GUIDE.md` → `docs/references/OPENSKILLS_GUIDE.md`

### 3. 保留在根目录的文档

以下文档保留在 `docs/` 根目录：
- `docs/README.md` - 文档索引（已更新）
- `docs/ARCHITECTURE.md` - 技术架构文档
- `docs/GITHUB_ACTIONS_SETUP.md` - CI/CD 配置
- `docs/DISCUSSIONS.md` - 讨论记录
- `docs/adr/` - 架构决策记录目录（保持不变）

### 4. 更新的文档

- `docs/README.md` - 已更新为新的文档结构索引
- `docs/testing/README.md` - 新增测试文档索引（整合了测试策略）
- `docs/features/README.md` - 新增MEP路由规划文档索引
- `docs/DOCUMENTATION_REORGANIZATION.md` - 本文档，记录整理过程

## 文档链接更新说明

由于文档位置发生了变化，以下文档中的链接可能需要更新：

1. **README.md** - 项目根目录的README.md中的文档链接
2. **其他文档中的交叉引用** - 各文档中引用其他文档的链接

建议在后续提交中逐步更新这些链接。

## 整合策略说明

### 测试文档整合策略

采用**索引文档 + 详细文档**的方式：
- `testing/README.md` - 作为索引文档，包含测试策略的核心内容和各测试类型的概述
- `testing/E2E_TESTING.md` - 保留完整的E2E测试详细指南
- `testing/PERFORMANCE_TESTING.md` - 保留完整的性能测试详细指南

这样既整合了重复内容，又保留了详细文档的完整性。

### MEP路由文档整合策略

采用**索引文档 + 详细文档**的方式：
- `features/README.md` - 作为索引文档，提供统一的导航入口
- 保留5个详细文档，因为它们内容较长且各有侧重：
  - `MEP_ROUTING.md` - 系统概述、架构和API
  - `MEP_ROUTING_DETAILED.md` - 详细的工作流程和约束规则
  - `MEP_COORDINATION.md` - 管线综合排布详细规格
  - `MEP_SYSTEM_PRIORITY.md` - 系统优先级配置详情
  - `MEP_PENETRATION.md` - 节点生成规则

这种方式保持了详细文档的完整性，同时通过索引文档提供了清晰的导航。

## 后续工作

1. ✅ 整合测试文档 - 已完成
2. ✅ 组织MEP路由文档 - 已完成（使用索引文档方式）
3. ⚠️ 更新项目根目录 `README.md` 中的文档链接 - 建议后续完成
4. ⚠️ 更新各文档中的交叉引用链接 - 建议后续完成（如需要）

---

**整理完成日期**: 2025-12-27  
**整理人员**: OpenTruss 开发团队
