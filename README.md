# OpenTruss

> 面向建筑施工行业的生成式 BIM 中间件

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/your-org/opentruss/releases/tag/v1.0.0)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)

**Latest Release**: v1.0.0 (January 1, 2025)

## 目录

- [项目概述](#项目概述)
- [核心特性](#核心特性)
- [快速开始](#快速开始)
  - [环境要求](#环境要求)
  - [安装步骤](#安装步骤)
  - [一键启动（推荐）](#一键启动推荐)
- [项目文档](#项目文档)
  - [设计文档](#设计文档)
  - [开发文档](#开发文档)
  - [部署文档](#部署文档)
  - [用户文档](#用户文档)
- [系统架构](#系统架构)
  - [技术栈](#技术栈)
  - [数据层级](#数据层级)
- [功能模块](#功能模块)
- [开发路线图](#开发路线图)
- [贡献指南](#贡献指南)
- [许可证](#许可证)
- [联系方式](#联系方式)

## 项目概述

OpenTruss 是一个面向建筑施工行业的生成式 BIM 中间件 (Generative BIM Middleware)，致力于解决 CAD-to-BIM 逆向重构中的"最后一公里"问题。

### 核心理念

**"Graph First, Geometry Generated"**（图逻辑优先，几何由生成而来）

通过接收上游 Agentic AI 对施工图（DWG）的非结构化识别结果，OpenTruss 在底层利用 LPG (Memgraph) + RDF 双模架构构建严谨的工程逻辑。通过 HITL (Human-in-the-Loop) 工作台，工程师在一个符合 GB50300 国标的层级体系下进行数据清洗、参数补全与合规性审查，最终编译生成高精度的 IFC 模型。

## 核心特性

- 🏗️ **GB50300 合规**: 严格遵循 GB50300 工程质量验收标准
- 🔄 **双模架构**: LPG + RDF 双模架构，确保高性能和语义标准化
- 🎯 **智能工作台**: HITL 工作台支持 Trace、Lift、Classify 三种模式
- 📋 **检验批管理**: 自动创建检验批，支持规则引擎和人工微调
- ✅ **审批工作流**: 完整的检验批审批流程，支持多角色协作
- 📦 **IFC 导出**: 生成标准 IFC 模型，兼容 Revit/Navisworks

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18.0+
- Docker 20.10+ (可选)
- Memgraph 2.10+

### 安装步骤

1. **克隆仓库**
```bash
git clone https://github.com/your-org/opentruss.git
cd opentruss
```

2. **后端设置**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

4. **前端设置**
```bash
cd frontend
npm install

# 配置前端环境变量
cp .env.example .env.local
# 编辑 .env.local，设置 NEXT_PUBLIC_API_URL
```

5. **启动 Memgraph**
```bash
docker run -it -p 7687:7687 memgraph/memgraph
```

6. **启动服务**

使用 Makefile（推荐）：
```bash
# 启动所有服务
make dev

# 或分别启动
make start-memgraph  # 启动数据库
make start-backend   # 启动后端
make start-frontend  # 启动前端
```

或手动启动：
```bash
# 后端
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
uvicorn app.main:app --reload

# 前端（新终端）
cd frontend
npm run dev
```

访问地址：
- 前端: http://localhost:3000
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

详细安装指南请参考 [开发环境搭建文档](docs/DEVELOPMENT.md)。

### 一键启动（推荐）

> **注意**: 统一启动脚本正在开发中，敬请期待！

对于有经验的开发者，可以使用以下命令快速启动：

```bash
# 使用 Makefile (推荐，跨平台)
make setup   # 初始化环境
make dev     # 启动开发环境

# 或使用脚本
./scripts/setup.sh        # Linux/macOS
./scripts/setup.ps1       # Windows PowerShell
```

更多启动方式请参考 [开发环境搭建文档](docs/DEVELOPMENT.md)。

## 项目文档

> 📚 **完整文档索引**: 查看 [文档中心](docs/README.md)（如果存在）获取完整的文档导航

### 设计文档

### 设计文档

- [产品需求文档 (PRD)](PRD.md) - 项目需求和功能规格
- [技术架构文档](docs/ARCHITECTURE.md) - 系统架构和技术选型
  - [架构图和 ADR](docs/ARCHITECTURE_DIAGRAMS.md) - 系统架构图、数据模型图、架构决策记录（如已创建）
- [系统设计图表](diagrams.md) - 状态机图、泳道图、时序图
- [API 设计文档](docs/API.md) - RESTful API 规范
- [数据库 Schema](docs/SCHEMA.md) - Memgraph 数据模型
- [UI/UX 设计文档](docs/UI_DESIGN.md) - 界面设计和交互规范


### 开发文档

- [开发环境搭建](docs/DEVELOPMENT.md) - 本地开发环境配置
- [代码规范](docs/CODING_STANDARDS.md) - Python/前端代码规范
- [测试策略](docs/TESTING.md) - 测试方法和策略
  - [E2E 测试指南](docs/E2E_TESTING.md) - Playwright E2E 测试
  - [性能测试指南](docs/PERFORMANCE_TESTING.md) - Locust 和 k6 性能测试
- [GitHub Actions 配置](docs/GITHUB_ACTIONS_SETUP.md) - CI/CD 工作流配置

### 部署文档

- [部署文档](docs/DEPLOYMENT.md) - 生产环境部署指南
- [运维手册](docs/OPERATIONS.md) - 监控、故障排查、性能调优

### 用户文档

- [API 使用文档](docs/API_USAGE.md) - API 快速开始和使用示例
- [用户手册](docs/USER_MANUAL.md) - 各角色操作指南

## 系统架构

### 技术栈

**后端**:
- FastAPI - Web 框架
- Memgraph - LPG 图数据库
- Pydantic - 数据验证
- ifcopenshell - IFC 文件处理

**前端**:
- Next.js 14+ - React 框架（支持 SSR 和客户端渲染）
- Tailwind CSS 4.0 - 实用优先的 CSS 框架
- TypeScript - 类型安全
- D3.js - 2D 拓扑可视化
- Canvas API - 高性能渲染

**基础设施**:
- Docker - 容器化
- Nginx - 反向代理
- Prometheus + Grafana - 监控

### 数据层级

遵循 GB50300 标准，六级层级结构：

```
项目 (Project)
  └─ 单体 (Building)
      └─ 分部 (Division)
          └─ 子分部 (SubDivision)
              └─ 分项 (Item)
                  └─ 检验批 (InspectionLot)
                      └─ 构件 (Element)
```

## 功能模块

### 1. 数据摄入 (Ingestion)

- 接收 AI Agent 识别结果
- "宽进严出"策略
- 自动暂存未分配构件

### 2. HITL 工作台 (Workbench)

- **Trace Mode**: 修复 2D 拓扑
- **Lift Mode**: 批量设置 Z 轴参数
- **Classify Mode**: 拖拽构件归类

### 3. 检验批管理 (Inspection Lot)

- 规则引擎自动创建
- 支持按楼层/区域划分
- 人工微调功能

### 4. 审批工作流 (Approval)

- 状态机管理（PLANNING → IN_PROGRESS → SUBMITTED → APPROVED → PUBLISHED）
- 完整性验证
- 多角色审批

### 5. IFC 导出 (Export)

- 按检验批导出
- 标准 IFC 格式
- 兼容主流 BIM 软件

## 开发路线图

- [x] Phase 1: Foundation & Hierarchy (基础架构)
- [x] Phase 2: Ingestion & Editor (数据清洗)
- [x] Phase 3: The Approver's Tool (检验批策划)
- [x] Phase 4: Workflow & Export (交付)

详细路线图请参考 [PRD.md](PRD.md)。

## 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: 添加新功能'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

**详细贡献指南**: 请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解完整的贡献流程、代码规范和测试要求。

相关文档：
- [代码规范文档](docs/CODING_STANDARDS.md) - 详细的代码风格指南
- [测试策略](docs/TESTING.md) - 测试要求和最佳实践

## 许可证

本项目采用 MIT 许可证。详情请查看 [LICENSE](LICENSE) 文件。

## 联系方式

- **项目主页**: https://github.com/XuXinran1011/OpenTruss
- **问题反馈**: https://github.com/XuXinran1011/OpenTruss/issues
- **GitHub Discussions**: https://github.com/XuXinran1011/OpenTruss/discussions (如已启用)

## 致谢

感谢所有为 OpenTruss 项目做出贡献的开发者和用户！

---

*OpenTruss - Graph First, Geometry Generated*

