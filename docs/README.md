# OpenTruss 文档中心

欢迎来到 OpenTruss 文档中心！本文档提供了项目所有文档的导航和索引。

## 📚 文档导航

### 🎯 快速开始

- [README.md](../README.md) - 项目概览和快速开始指南
- [开发环境搭建](development/DEVELOPMENT.md) - 详细的开发环境配置步骤
- [CONTRIBUTING.md](../CONTRIBUTING.md) - 贡献指南和开发流程

### 🏗️ 架构与设计

- [技术架构文档](ARCHITECTURE.md) - 系统架构和技术选型
- [架构图表](architecture/README.md) - 可视化架构图和流程图
  - [系统架构图](architecture/diagrams-architecture.md) - 系统架构图、数据模型图和流程图
  - [设计图表](architecture/diagrams.md) - 设计图表集合
- [架构决策记录 (ADR)](adr/) - 重要架构决策的记录
  - [ADR-0001: Graph-First 架构决策](adr/0001-graph-first-architecture.md)
  - [ADR-0002: Memgraph 选择](adr/0002-memgraph-choice.md)
  - [ADR-0003: HITL 工作流设计](adr/0003-hitl-workflow.md)

### 📋 API 文档

- [API 参考文档](api/index.md) - RESTful API 完整参考
- [API 使用指南](api/usage.md) - API 快速开始和使用示例
- [支吊架 API](api/hangers.md) - 支吊架生成和管理 API

### 💻 开发指南

- [开发环境搭建](development/DEVELOPMENT.md) - 本地开发环境配置
- [代码规范](development/CODING_STANDARDS.md) - Python/前端代码规范
- [AI 代理技能](development/AGENTS.md) - OpenTruss AI 代理技能说明
- [依赖说明](development/DEPENDENCIES.md) - 项目依赖列表

### 🧪 测试文档

- [测试文档](testing/README.md) - 测试策略、E2E测试和性能测试完整指南
  - [E2E 测试指南](testing/E2E_TESTING.md) - Playwright E2E 测试详细说明
  - [性能测试指南](testing/PERFORMANCE_TESTING.md) - Locust 和 k6 性能测试详细说明
- [测试报告](testing/reports/) - E2E 测试报告

### 🚀 部署与运维

- [部署文档](deployment/DEPLOYMENT.md) - 生产环境部署指南
- [运维手册](deployment/OPERATIONS.md) - 监控、故障排查、性能调优
- [监控指南](deployment/MONITORING.md) - Prometheus 和 Grafana 监控配置

### 📖 用户文档

- [用户手册](guides/USER_MANUAL.md) - 各角色操作指南
- [UI/UX 设计文档](guides/UI_DESIGN.md) - 界面设计和交互规范

### 🔧 功能特性

- [MEP 路由规划系统](features/README.md) - MEP路由规划完整文档索引
  - [系统概述与API](features/MEP_ROUTING.md) - MEP路径规划系统概述、架构和API接口
  - [路由规划详细规格](features/MEP_ROUTING_DETAILED.md) - 路由规划详细规格文档
  - [管线综合排布规格](features/MEP_COORDINATION.md) - 3D管线综合排布详细规格
  - [MEP系统优先级配置](features/MEP_SYSTEM_PRIORITY.md) - MEP系统优先级配置文档
  - [穿墙/穿楼板节点生成](features/MEP_PENETRATION.md) - 穿墙/穿楼板节点生成规则

### 🎓 规则引擎

- [规则引擎文档](rules/README.md) - 规则引擎完整文档索引
  - [规则引擎架构与开发指南](rules/RULE_ENGINE.md) - 规则引擎设计和实现
  - [规则配置示例](rules/RULE_CONFIG_EXAMPLES.md) - 规则配置文件示例

### 📊 参考文档

- [产品需求文档 (PRD)](references/PRD.md) - 项目需求和功能规格
- [数据库 Schema](references/SCHEMA.md) - Memgraph 数据模型
- [阶段参考文档](references/PHASE_REFERENCE.md) - 开发阶段参考信息
- [OpenSkills 使用指南](references/OPENSKILLS_GUIDE.md) - OpenSkills 工具使用说明

### 📝 报告文档

- [代码审查报告](reports/CODE_REVIEW_REPORT.md) - 项目代码审查报告
- [支吊架服务代码审查](reports/HANGER_SERVICE_CODE_REVIEW.md) - 支吊架服务代码审查报告

### 🔗 集成文档

- [GitHub Actions 配置](GITHUB_ACTIONS_SETUP.md) - CI/CD 工作流配置

**注意**：Speckle 模型转换相关信息已整合到 [开发环境搭建文档](development/DEVELOPMENT.md#41-speckle-模型python-pydantic) 中。

## 📖 文档分类

### 按角色分类

**👨‍💻 开发者**:
- [开发环境搭建](development/DEVELOPMENT.md)
- [代码规范](development/CODING_STANDARDS.md)
- [测试文档](testing/README.md)
- [API 参考文档](api/index.md)
- [架构文档](ARCHITECTURE.md)

**🔧 运维人员**:
- [部署文档](deployment/DEPLOYMENT.md)
- [运维手册](deployment/OPERATIONS.md)
- [监控指南](deployment/MONITORING.md)

**👤 最终用户**:
- [用户手册](guides/USER_MANUAL.md)
- [API 使用指南](api/usage.md)

**📊 产品经理/架构师**:
- [产品需求文档 (PRD)](references/PRD.md)
- [技术架构文档](ARCHITECTURE.md)
- [架构决策记录 (ADR)](adr/)

### 按主题分类

**🏗️ 架构设计**:
- [技术架构文档](ARCHITECTURE.md)
- [架构图表](architecture/README.md)
- [架构决策记录 (ADR)](adr/)

**💾 数据模型**:
- [数据库 Schema](references/SCHEMA.md)
- [产品需求文档 (PRD)](references/PRD.md)

**🔌 API 接口**:
- [API 参考文档](api/index.md)
- [API 使用指南](api/usage.md)
- [支吊架 API](api/hangers.md)

**🎯 功能特性**:
- [MEP 路由规划系统](features/README.md) - MEP路由规划完整文档
- [规则引擎](rules/README.md) - 规则引擎完整文档

**🧪 测试**:
- [测试文档](testing/README.md) - 测试策略、E2E测试和性能测试完整指南
- [E2E 测试指南](testing/E2E_TESTING.md)
- [性能测试指南](testing/PERFORMANCE_TESTING.md)

**🚀 部署运维**:
- [部署文档](deployment/DEPLOYMENT.md)
- [运维手册](deployment/OPERATIONS.md)
- [监控指南](deployment/MONITORING.md)

## 📁 文档结构

```
docs/
├── README.md                    # 文档索引（本文档）
├── ARCHITECTURE.md              # 技术架构文档
├── GITHUB_ACTIONS_SETUP.md      # CI/CD 配置
├── DISCUSSIONS.md               # 讨论记录
├── architecture/                # 架构图表
│   ├── README.md               # 架构图表索引
│   ├── diagrams-architecture.md # 系统架构图
│   └── diagrams.md             # 设计图表
├── api/                         # API 文档
│   ├── index.md                 # API 参考
│   ├── usage.md                 # API 使用指南
│   └── hangers.md               # 支吊架 API
├── features/                    # 功能特性文档
│   ├── README.md                # MEP路由规划文档索引
│   ├── MEP_ROUTING.md           # 系统概述与API
│   ├── MEP_ROUTING_DETAILED.md  # 路由规划详细规格
│   ├── MEP_COORDINATION.md      # 管线综合排布规格
│   ├── MEP_SYSTEM_PRIORITY.md   # 系统优先级配置
│   └── MEP_PENETRATION.md       # 节点生成规则
├── development/                 # 开发文档
│   ├── DEVELOPMENT.md
│   ├── CODING_STANDARDS.md
│   ├── AGENTS.md
│   └── DEPENDENCIES.md
├── testing/                     # 测试文档
│   ├── README.md                # 测试文档索引（整合了测试策略）
│   ├── E2E_TESTING.md           # E2E测试详细指南
│   ├── PERFORMANCE_TESTING.md   # 性能测试详细指南
│   └── reports/
│       └── E2E_TEST_REPORT.md
├── deployment/                  # 部署运维文档
│   ├── DEPLOYMENT.md
│   ├── OPERATIONS.md
│   └── MONITORING.md
├── guides/                      # 用户指南
│   ├── USER_MANUAL.md
│   └── UI_DESIGN.md
├── rules/                       # 规则引擎文档
│   ├── README.md               # 规则引擎文档索引
│   ├── RULE_ENGINE.md          # 规则引擎架构与开发指南
│   └── RULE_CONFIG_EXAMPLES.md # 规则配置示例
├── references/                  # 参考文档
│   ├── PRD.md
│   ├── SCHEMA.md
│   ├── PHASE_REFERENCE.md
│   └── OPENSKILLS_GUIDE.md
├── reports/                     # 报告文档
│   ├── CODE_REVIEW_REPORT.md
│   └── HANGER_SERVICE_CODE_REVIEW.md
└── adr/                         # 架构决策记录
    ├── 0001-graph-first-architecture.md
    ├── 0002-memgraph-choice.md
    └── 0003-hitl-workflow.md
```

## 🔍 快速查找

### 我想...

- **开始开发** → [开发环境搭建](development/DEVELOPMENT.md)
- **了解架构** → [技术架构文档](ARCHITECTURE.md)
- **使用 API** → [API 使用指南](api/usage.md)
- **查看 API 参考** → [API 参考文档](api/index.md)
- **部署项目** → [部署文档](deployment/DEPLOYMENT.md)
- **运行测试** → [测试文档](testing/README.md)
- **了解规则引擎** → [规则引擎文档](rules/README.md)
- **查看需求文档** → [产品需求文档 (PRD)](references/PRD.md)

---

**文档版本**：2.0  
**最后更新**：2025-12-28  
**维护者**：OpenTruss 开发团队
