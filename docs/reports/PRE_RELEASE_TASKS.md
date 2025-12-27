# OpenTruss v1.0.0 发布前待办清单

**创建日期**: 2025-12-27  
**目标发布日期**: 待定  
**当前状态**: 功能开发完成，进入发布准备阶段

---

## 📋 总体进度

- ✅ **功能开发**: 100% 完成（所有 Phase 和核心功能已实现）
- ✅ **代码质量**: 良好（已通过代码审查，部分改进建议已实施）
- ✅ **文档整理**: 100% 完成（文档已重新组织并整合）
- ⚠️ **测试验证**: 待完成（需要运行完整测试套件）
- ⚠️ **安全审计**: 待完成（依赖安全扫描、环境变量配置）
- ⚠️ **构建验证**: 待完成（Docker 镜像构建、生产环境测试）
- ⚠️ **发布准备**: 待完成（Git 标签、GitHub Release）

---

## 🔴 高优先级任务（发布前必须完成）

### 1. 测试验证 ⚠️

#### 1.1 单元测试
- [ ] 运行所有后端单元测试：`pytest backend/tests/`
- [ ] 确保所有测试通过（目标：100% 通过率）
- [ ] 检查测试覆盖率（目标：80%+）
- [ ] 修复任何失败的测试

#### 1.2 集成测试
- [ ] 运行所有集成测试：`pytest backend/tests/test_integration/`
- [ ] 验证 Memgraph 连接和查询功能
- [ ] 验证 API 端点集成
- [ ] 验证数据流（Ingestion → Workbench → Export）

#### 1.3 E2E 测试
- [ ] 运行前端 E2E 测试：`npm run test:e2e`（在 frontend 目录）
- [ ] 验证关键用户流程：
  - [ ] 数据导入（Speckle）
  - [ ] HITL Workbench 三种模式
  - [ ] 检验批创建和审批
  - [ ] IFC 导出
- [ ] 修复任何失败的 E2E 测试

#### 1.4 性能测试
- [ ] 运行 k6 性能测试（在 WSL2 环境）
- [ ] 运行 Locust 压力测试
- [ ] 验证性能指标：
  - [ ] API 响应时间 < 200ms (p95)
  - [ ] 支持 10,000+ 元素的项目
  - [ ] 前端渲染性能 60 FPS
- [ ] 记录性能测试报告

#### 1.5 手动测试
- [ ] 在干净环境中测试安装流程
- [ ] 测试所有核心功能：
  - [ ] 数据摄入
  - [ ] Trace Mode（拓扑修复）
  - [ ] Lift Mode（批量 Z 轴设置）
  - [ ] Classify Mode（构件分类）
  - [ ] 检验批创建（规则引擎）
  - [ ] 审批工作流
  - [ ] IFC 导出
- [ ] 测试错误处理和边界情况

**执行命令**:
```bash
# 后端测试
cd backend
pytest tests/ -v --cov=app --cov-report=html

# 前端测试
cd frontend
npm test
npm run test:e2e

# 性能测试（WSL2）
cd backend/tests/performance
bash run_tests_wsl.sh
```

---

### 2. 安全审计 ⚠️

#### 2.1 依赖安全扫描
- [ ] **Python 依赖**:
  ```bash
  pip install pip-audit
  pip-audit
  # 或使用 safety
  pip install safety
  safety check
  ```
- [ ] **Node.js 依赖**:
  ```bash
  cd frontend
  npm audit
  npm audit fix
  ```
- [ ] 修复所有高危和中危漏洞
- [ ] 记录低危漏洞（评估是否需要在发布前修复）

#### 2.2 环境变量安全配置
- [ ] 生成强 JWT 密钥：`openssl rand -hex 32`
- [ ] 验证 `JWT_SECRET_KEY` 不是默认值
- [ ] 配置生产环境 CORS（不能使用 `*`）
- [ ] 配置 Memgraph 密码（不能使用默认值）
- [ ] 创建 `.env.production` 文件（不提交到 Git）
- [ ] 验证所有敏感信息不在代码中硬编码

#### 2.3 代码安全审查
- [ ] 检查 SQL/Cypher 注入风险（确保使用参数化查询）
- [ ] 检查文件上传验证（大小、类型、内容）
- [ ] 检查错误消息是否泄露敏感信息
- [ ] 验证认证和授权逻辑
- [ ] 检查密码哈希强度（bcrypt rounds ≥ 12）

#### 2.4 容器安全
- [ ] 扫描 Docker 镜像漏洞：
  ```bash
  # 使用 Trivy（推荐）
  trivy image opentruss/backend:latest
  trivy image opentruss/frontend:latest
  ```
- [ ] 验证容器以非 root 用户运行（如适用）
- [ ] 检查 Dockerfile 是否包含不必要的包
- [ ] 验证 secrets 不在 Dockerfile 中硬编码

**参考文档**: `SECURITY_CHECKLIST.md`

---

### 3. 构建验证 ⚠️

#### 3.1 Docker 镜像构建
- [ ] 构建后端镜像：`docker build -t opentruss/backend:1.0.0 ./backend`
- [ ] 构建前端镜像：`docker build -t opentruss/frontend:1.0.0 ./frontend`
- [ ] 验证镜像大小合理（优化后）
- [ ] 验证镜像包含必要的文件
- [ ] 测试镜像健康检查

#### 3.2 Docker Compose 生产环境测试
- [ ] 使用 `docker-compose.prod.yml` 启动完整环境
- [ ] 验证所有服务正常启动：
  - [ ] Memgraph 服务健康
  - [ ] 后端 API 健康检查通过
  - [ ] 前端服务可访问
- [ ] 测试服务间通信
- [ ] 验证数据持久化（volumes）
- [ ] 测试服务重启和恢复

#### 3.3 生产环境配置验证
- [ ] 验证环境变量配置正确
- [ ] 测试 HTTPS 配置（如适用）
- [ ] 验证 Nginx 反向代理配置（如使用）
- [ ] 测试日志记录和轮转
- [ ] 验证监控和告警配置

**执行命令**:
```bash
# 构建镜像
docker-compose -f docker-compose.prod.yml build

# 启动生产环境
docker-compose -f docker-compose.prod.yml up -d

# 检查服务状态
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs

# 健康检查
curl http://localhost:8000/health
curl http://localhost:3000
```

---

### 4. 文档验证 ⚠️

#### 4.1 文档完整性检查
- [ ] 验证所有文档链接有效
- [ ] 检查 README.md 中的安装说明
- [ ] 验证 API 文档完整且准确
- [ ] 检查用户手册完整性
- [ ] 验证部署文档步骤可执行

#### 4.2 文档准确性验证
- [ ] 在干净系统上测试安装文档
- [ ] 验证所有代码示例可运行
- [ ] 检查版本号一致性（所有文档中的版本号）
- [ ] 验证发布日期和更新日期

#### 4.3 发布文档准备
- [ ] 更新 `CHANGELOG.md`（确保 [1.0.0] 版本信息完整）
- [ ] 更新 `RELEASE_NOTES.md`（确保所有功能已列出）
- [ ] 验证 `RELEASE_NOTES.md` 中的链接有效
- [ ] 准备发布公告（如需要）

---

## 🟡 中优先级任务（建议完成）

### 5. 代码质量改进

#### 5.1 类型注解完善
- [ ] 检查并补充缺失的返回类型注解
- [ ] 运行 `mypy` 进行类型检查（如配置）
- [ ] 修复类型注解错误

#### 5.2 文档字符串补充
- [ ] 为缺少文档的函数添加文档字符串
- [ ] 统一使用 Google 风格文档字符串
- [ ] 确保包含 Args、Returns、Raises

#### 5.3 错误处理统一
- [ ] 检查是否所有 API 端点使用自定义异常
- [ ] 验证错误响应格式一致
- [ ] 改进错误消息，添加更多上下文

**注意**: 这些改进已在代码审查报告中提出，但可以在发布后持续改进。

---

### 6. 性能优化

#### 6.1 数据库查询优化
- [ ] 根据性能测试结果识别慢查询
- [ ] 优化复杂 Cypher 查询
- [ ] 添加必要的索引（如适用）

#### 6.2 前端性能优化
- [ ] 使用 `React.memo` 优化组件渲染
- [ ] 实现虚拟滚动（大型列表）
- [ ] 优化 Canvas 渲染性能
- [ ] 检查并优化 bundle 大小

**注意**: 性能优化应根据实际测试结果进行，不是发布前必须项。

---

## 🟢 低优先级任务（可选）

### 7. 监控和可观测性

#### 7.1 Prometheus 指标验证
- [ ] 验证所有 Prometheus 指标正常收集
- [ ] 测试 Grafana 仪表板
- [ ] 验证告警规则配置

#### 7.2 日志系统验证
- [ ] 验证结构化日志格式
- [ ] 测试日志轮转和归档
- [ ] 验证日志级别配置

---

### 8. 持续集成/持续部署（CI/CD）

#### 8.1 GitHub Actions 验证
- [ ] 验证 CI 工作流正常运行
- [ ] 测试自动构建和测试
- [ ] 验证代码质量检查（lint、type check）

#### 8.2 自动化测试
- [ ] 确保所有测试在 CI 中通过
- [ ] 验证测试报告生成
- [ ] 检查测试覆盖率报告

---

## 📦 发布任务（所有前置任务完成后）

### 9. Git 操作

#### 9.1 最终提交
- [ ] 确保所有更改已提交
- [ ] 验证工作目录干净：`git status`
- [ ] 创建最终提交（如有未提交的更改）

#### 9.2 创建 Git 标签
```bash
# 创建带注释的标签
git tag -a v1.0.0 -m "Release v1.0.0 - Initial stable release"

# 推送标签到远程
git push origin v1.0.0
```

#### 9.3 验证标签
- [ ] 验证标签已创建：`git tag -l`
- [ ] 验证标签已推送：在 GitHub 上检查

---

### 10. GitHub Release

#### 10.1 创建 Release
- [ ] 在 GitHub 上创建新 Release
- [ ] **Tag**: `v1.0.0`
- [ ] **Title**: "OpenTruss v1.0.0 - Initial Release"
- [ ] **Description**: 从 `RELEASE_NOTES.md` 复制内容
- [ ] 附加发布说明
- [ ] 标记为 "Latest release"
- [ ] 发布 Release

#### 10.2 Release 内容
- [ ] 包含完整的发布说明
- [ ] 列出主要功能和改进
- [ ] 包含安装和升级指南
- [ ] 包含已知限制和问题
- [ ] 提供支持链接

---

### 11. 发布后验证

#### 11.1 发布验证
- [ ] 验证 Release 在 GitHub 上可访问
- [ ] 测试从 Release 标签安装
- [ ] 验证所有下载链接有效
- [ ] 检查文档链接在 Release 中有效

#### 11.2 监控
- [ ] 监控发布后的错误日志
- [ ] 检查用户反馈
- [ ] 监控性能指标
- [ ] 准备快速响应计划

---

## 📊 任务完成检查表

在开始发布流程前，请确认：

- [ ] ✅ 所有高优先级任务已完成
- [ ] ✅ 所有测试通过
- [ ] ✅ 安全审计通过
- [ ] ✅ 构建验证通过
- [ ] ✅ 文档验证通过
- [ ] ✅ 代码审查完成
- [ ] ✅ 性能测试完成
- [ ] ✅ 手动测试完成

---

## 🚨 已知问题和限制

### 当前已知限制
1. **IFC 导出**: 需要 ifcopenshell（可能有平台特定限制）
2. **大型项目**: >50,000 元素的项目可能需要性能调优
3. **MEP 路由**: 目前仅支持 2D 路由（3D 路由在路线图中）

### 待解决的问题
- 查看 GitHub Issues 了解当前问题列表
- 评估问题严重性，决定是否在发布前修复

---

## 📝 发布决策

在完成所有高优先级任务后，需要做出发布决策：

### 发布条件
- ✅ 所有核心功能正常工作
- ✅ 所有测试通过
- ✅ 安全审计通过
- ✅ 文档完整准确
- ✅ 性能满足要求

### 发布决策流程
1. 审查所有任务完成情况
2. 评估已知问题和限制
3. 决定是否发布或延迟发布
4. 如果发布，执行发布任务
5. 如果延迟，记录原因和计划

---

## 📚 相关文档

- [发布检查清单](../RELEASE_CHECKLIST.md)
- [发布说明](../RELEASE_NOTES.md)
- [变更日志](../CHANGELOG.md)
- [安全清单](../SECURITY_CHECKLIST.md)
- [部署文档](deployment/DEPLOYMENT.md)
- [代码审查报告](CODE_REVIEW_REPORT.md)

---

## 🔄 更新记录

- **2025-12-27**: 创建发布前待办清单

---

**注意**: 此清单应根据项目进展持续更新。建议每周审查一次任务完成情况。
