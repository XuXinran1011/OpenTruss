# OpenTruss 文档中心

欢迎来到 OpenTruss 文档中心！本文档提供了项目所有文档的导航和索引。

## 📚 文档导航

### 🎯 快速开始

- [README.md](../README.md) - 项目概览和快速开始指南
- [开发环境搭建](DEVELOPMENT.md) - 详细的开发环境配置步骤
- [CONTRIBUTING.md](../CONTRIBUTING.md) - 贡献指南和开发流程

### 🏗️ 架构与设计

- [技术架构文档](ARCHITECTURE.md) - 系统架构和技术选型
- [架构图文档](ARCHITECTURE_DIAGRAMS.md) - 可视化架构图和流程图
- [架构决策记录 (ADR)](adr/) - 重要架构决策的记录
  - [ADR-0001: Graph-First 架构决策](adr/0001-graph-first-architecture.md)
  - [ADR-0002: Memgraph 选择](adr/0002-memgraph-choice.md)
  - [ADR-0003: HITL 工作流设计](adr/0003-hitl-workflow.md)

### 📋 需求与规范

- [产品需求文档 (PRD)](../PRD.md) - 项目需求和功能规格
- [API 设计文档](API.md) - RESTful API 规范
- [数据库 Schema](SCHEMA.md) - Memgraph 数据模型
- [UI/UX 设计文档](UI_DESIGN.md) - 界面设计和交互规范

### 💻 开发指南

- [开发环境搭建](DEVELOPMENT.md) - 本地开发环境配置
- [代码规范](CODING_STANDARDS.md) - Python/前端代码规范
- [测试策略](TESTING.md) - 测试方法和策略
  - [E2E 测试指南](E2E_TESTING.md) - Playwright E2E 测试
  - [性能测试指南](PERFORMANCE_TESTING.md) - Locust 和 k6 性能测试
- [GitHub Actions 配置](GITHUB_ACTIONS_SETUP.md) - CI/CD 工作流配置

### 🚀 部署与运维

- [部署文档](DEPLOYMENT.md) - 生产环境部署指南
- [运维手册](OPERATIONS.md) - 监控、故障排查、性能调优
- [监控指南](MONITORING.md) - Prometheus 和 Grafana 监控配置（如已创建）

### 📖 用户文档

- [API 使用文档](API_USAGE.md) - API 快速开始和使用示例
- [用户手册](USER_MANUAL.md) - 各角色操作指南

### 🔧 集成文档

- [Speckle 转换指南](../README_SPECKLE_CONVERSION.md) - Speckle 数据转换说明
- [Speckle 本地设置](../README_SPECKLE_LOCAL_SETUP.md) - Speckle 本地开发环境配置

### 🎓 高级主题

- [规则引擎文档](RULE_ENGINE.md) - 规则引擎设计和实现
- [规则配置示例](RULE_CONFIG_EXAMPLES.md) - 规则配置文件示例
- [阶段参考文档](PHASE_REFERENCE.md) - 开发阶段参考信息

### 🔧 MEP 路由规划

- [MEP路由规划系统](MEP_ROUTING.md) - MEP路径规划系统概述
- [MEP路由规划详细规格](MEP_ROUTING_DETAILED.md) - 路由规划详细规格文档
- [管线综合排布规格](MEP_COORDINATION.md) - 3D管线综合排布详细规格
- [MEP系统优先级配置](MEP_SYSTEM_PRIORITY.md) - MEP系统优先级配置文档
- [穿墙/穿楼板节点生成](MEP_PENETRATION.md) - 穿墙/穿楼板节点生成规则

## 📖 文档分类

### 按角色分类

**👨‍💻 开发者**:
- [开发环境搭建](DEVELOPMENT.md)
- [代码规范](CODING_STANDARDS.md)
- [测试策略](TESTING.md)
- [API 设计文档](API.md)
- [架构文档](ARCHITECTURE.md)

**🔧 运维人员**:
- [部署文档](DEPLOYMENT.md)
- [运维手册](OPERATIONS.md)
- [监控指南](MONITORING.md)（如已创建）

**👤 最终用户**:
- [用户手册](USER_MANUAL.md)
- [API 使用文档](API_USAGE.md)

**📊 产品经理/架构师**:
- [产品需求文档 (PRD)](../PRD.md)
- [技术架构文档](ARCHITECTURE.md)
- [架构决策记录 (ADR)](adr/)

### 按主题分类

**🏗️ 架构设计**:
- [技术架构文档](ARCHITECTURE.md)
- [架构图文档](ARCHITECTURE_DIAGRAMS.md)
- [架构决策记录 (ADR)](adr/)

**💾 数据模型**:
- [数据库 Schema](SCHEMA.md)
- [API 设计文档](API.md)

**🔄 工作流**:
- [用户手册](USER_MANUAL.md) - HITL 工作流说明
- [规则引擎文档](RULE_ENGINE.md)

**🧪 测试**:
- [测试策略](TESTING.md)
- [E2E 测试指南](E2E_TESTING.md)
- [性能测试指南](PERFORMANCE_TESTING.md)

## 🔍 快速查找

### 常见问题

**Q: 如何开始开发？**
A: 查看 [开发环境搭建](DEVELOPMENT.md) 和 [README.md](../README.md) 的快速开始部分。

**Q: 如何理解系统架构？**
A: 先阅读 [技术架构文档](ARCHITECTURE.md)，然后查看 [架构图文档](ARCHITECTURE_DIAGRAMS.md) 的可视化图表。

**Q: 如何贡献代码？**
A: 查看 [CONTRIBUTING.md](../CONTRIBUTING.md) 了解贡献流程。

**Q: API 如何使用？**
A: 查看 [API 设计文档](API.md) 了解 API 规范，[API 使用文档](API_USAGE.md) 提供了使用示例。

**Q: 如何部署到生产环境？**
A: 查看 [部署文档](DEPLOYMENT.md) 了解部署步骤。

## 📝 文档维护

文档会随着项目发展持续更新。如果发现文档问题或有改进建议，请：

1. 提交 Issue 描述问题
2. 提交 PR 直接改进文档
3. 在 GitHub Discussions 中讨论（如已启用）

## 🔗 外部资源

- [GitHub 仓库](https://github.com/XuXinran1011/OpenTruss)
- [Issues](https://github.com/XuXinran1011/OpenTruss/issues)
- [GitHub Discussions](https://github.com/XuXinran1011/OpenTruss/discussions)（如已启用）
- [Memgraph 文档](https://memgraph.com/docs)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Next.js 文档](https://nextjs.org/docs)

---

*最后更新: 2025-01-01*

