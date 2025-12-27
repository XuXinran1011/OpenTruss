# OpenTruss AI Agent Skills

本文档列出了 OpenTruss 项目中可用的 AI 代理技能。这些技能帮助 AI 代理更好地理解项目架构、代码规范和开发流程。

## 可用技能

### opentruss-architecture
**描述**: OpenTruss 项目架构、设计理念和核心技术栈指南

**使用场景**: 
- 需要了解或修改项目架构时
- 理解双模架构（LPG + RDF）设计时
- 了解技术栈选型时
- 查看系统分层架构时

**位置**: `.claude/skills/opentruss-architecture/SKILL.md`

---

### opentruss-coding-standards
**描述**: OpenTruss 项目代码规范和最佳实践指南

**使用场景**:
- 编写新代码时
- 审查代码时
- 需要了解命名规范时
- 需要了解 Git 工作流时

**位置**: `.claude/skills/opentruss-coding-standards/SKILL.md`

---

### opentruss-gb50300
**描述**: GB50300 工程质量验收标准在 OpenTruss 中的实现和应用指南

**使用场景**:
- 实现与 GB50300 标准相关的功能时
- 理解数据层级结构时
- 实现检验批管理功能时
- 实现审批工作流时

**位置**: `.claude/skills/opentruss-gb50300/SKILL.md`

---

### opentruss-development
**描述**: OpenTruss 项目开发工作流、环境搭建和常用操作指南

**使用场景**:
- 设置开发环境时
- 运行测试时
- 执行常见开发任务时
- 调试问题时

**位置**: `.claude/skills/opentruss-development/SKILL.md`

---

## 如何使用

当 AI 代理需要了解项目特定信息时，会自动加载相应的技能文件。技能文件包含详细的指令和上下文信息，帮助 AI 代理：

1. **理解项目架构**: 通过 `opentruss-architecture` 技能了解系统设计
2. **遵循代码规范**: 通过 `opentruss-coding-standards` 技能确保代码质量
3. **实现标准功能**: 通过 `opentruss-gb50300` 技能正确实现 GB50300 相关功能
4. **执行开发任务**: 通过 `opentruss-development` 技能了解开发流程

## 技能维护

技能文件位于 `.claude/skills/` 目录下，每个技能都是一个独立的目录，包含 `SKILL.md` 文件。

**更新技能**:
1. 编辑对应的 `SKILL.md` 文件
2. 确保遵循 Anthropic 的 SKILL.md 格式规范
3. 提交到版本控制

**添加新技能**:
1. 在 `.claude/skills/` 目录下创建新目录
2. 创建 `SKILL.md` 文件，包含技能元数据和指令
3. 更新本 `AGENTS.md` 文件，添加新技能说明

## 相关文档

- 项目架构文档: `docs/ARCHITECTURE.md`
- 代码规范文档: `docs/CODING_STANDARDS.md`
- 开发指南: `docs/DEVELOPMENT.md`
- 数据模型: `docs/SCHEMA.md`

---

*本文档由 OpenSkills 自动生成，最后更新: 2025-12-26*

