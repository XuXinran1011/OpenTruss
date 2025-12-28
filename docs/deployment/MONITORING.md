# OpenTruss 监控指南

本文档介绍如何使用 Prometheus 和 Grafana 监控 OpenTruss 系统的性能和健康状态。

## 概述

OpenTruss 使用 Prometheus 进行指标收集，使用 Grafana 进行可视化展示。监控系统可以帮助：

- 跟踪 API 请求的性能和错误率
- 监控 Memgraph 查询性能
- 观察工作流操作统计
- 了解系统资源使用情况

## 架构

```
OpenTruss Backend (FastAPI)
    ↓ (暴露 /metrics 端点)
Prometheus (指标收集和存储)
    ↓ (查询)
Grafana (可视化和告警)
```

---

**最后更新**：2025-12-28  
**文档版本**：1.0  
**维护者**：OpenTruss 开发团队

## 快速开始

### 1. 启动监控服务

使用 Docker Compose 启动监控服务：

```bash
# 启动所有服务（包括监控）
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d

# 或仅启动监控服务（需要先启动 backend）
docker-compose -f docker-compose.monitoring.yml up -d
```

### 2. 访问监控界面

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001
  - 默认用户名: `admin`
  - 默认密码: `admin`

### 3. 查看指标

在 Prometheus 中，可以查询以下指标：

```
# API 请求总数
opentruss_api_requests_total

# API 请求延迟
opentruss_api_request_duration_seconds

# Memgraph 查询延迟
opentruss_memgraph_query_duration_seconds

# 构件数量
opentruss_elements_total

# 检验批数量
opentruss_inspection_lots_total
```

## 指标说明

### API 指标

#### `opentruss_api_requests_total`

API 请求总数计数器。

**标签**:
- `method`: HTTP 方法 (GET, POST, PUT, DELETE)
- `endpoint`: API 端点路径
- `status`: HTTP 状态码

**示例查询**:
```promql
# 每分钟请求数
rate(opentruss_api_requests_total[1m])

# 按状态码统计
sum by (status) (opentruss_api_requests_total)

# 按端点统计
sum by (endpoint) (opentruss_api_requests_total)
```

#### `opentruss_api_request_duration_seconds`

API 请求延迟直方图。

**标签**:
- `method`: HTTP 方法
- `endpoint`: API 端点路径

**示例查询**:
```promql
# 平均延迟
rate(opentruss_api_request_duration_seconds_sum[5m]) / rate(opentruss_api_request_duration_seconds_count[5m])

# P95 延迟
histogram_quantile(0.95, rate(opentruss_api_request_duration_seconds_bucket[5m]))

# P99 延迟
histogram_quantile(0.99, rate(opentruss_api_request_duration_seconds_bucket[5m]))
```

### Memgraph 指标

#### `opentruss_memgraph_query_duration_seconds`

Memgraph 查询延迟。

**标签**:
- `query_type`: 查询类型 (如: "get_element", "update_topology")

**示例查询**:
```promql
# 平均查询延迟
rate(opentruss_memgraph_query_duration_seconds_sum[5m]) / rate(opentruss_memgraph_query_duration_seconds_count[5m])
```

#### `opentruss_memgraph_queries_total`

Memgraph 查询总数。

**标签**:
- `query_type`: 查询类型
- `status`: 状态 (success/error)

**示例查询**:
```promql
# 查询错误率
rate(opentruss_memgraph_queries_total{status="error"}[5m]) / rate(opentruss_memgraph_queries_total[5m])
```

### 业务指标

#### `opentruss_elements_total`

构件总数（当前值）。

**标签**:
- `status`: 构件状态 (Draft/Verified)

**示例查询**:
```promql
# 所有构件总数
sum(opentruss_elements_total)

# 按状态统计
sum by (status) (opentruss_elements_total)
```

#### `opentruss_inspection_lots_total`

检验批总数（当前值）。

**标签**:
- `status`: 检验批状态

**示例查询**:
```promql
# 所有检验批总数
sum(opentruss_inspection_lots_total)
```

#### `opentruss_workflow_operations_total`

工作流操作总数。

**标签**:
- `operation_type`: 操作类型 (trace, lift, classify, approve, reject)
- `status`: 状态 (success/error)

**示例查询**:
```promql
# 按操作类型统计
sum by (operation_type) (opentruss_workflow_operations_total)

# 错误率
rate(opentruss_workflow_operations_total{status="error"}[5m]) / rate(opentruss_workflow_operations_total[5m])
```

## Grafana 仪表板

### 预定义仪表板

监控配置包含预定义的 Grafana 仪表板（位于 `monitoring/grafana/dashboards/`）。

### 创建自定义仪表板

1. 登录 Grafana (http://localhost:3001)
2. 点击 "+" → "Create Dashboard"
3. 添加 Panel
4. 选择 Prometheus 数据源
5. 输入 PromQL 查询表达式

### 推荐仪表板配置

#### API 性能面板

- **请求速率**: `rate(opentruss_api_requests_total[5m])`
- **P95 延迟**: `histogram_quantile(0.95, rate(opentruss_api_request_duration_seconds_bucket[5m]))`
- **错误率**: `rate(opentruss_api_requests_total{status=~"5.."}[5m]) / rate(opentruss_api_requests_total[5m])`

#### Memgraph 性能面板

- **查询速率**: `rate(opentruss_memgraph_queries_total[5m])`
- **平均查询延迟**: `rate(opentruss_memgraph_query_duration_seconds_sum[5m]) / rate(opentruss_memgraph_query_duration_seconds_count[5m])`
- **查询错误率**: `rate(opentruss_memgraph_queries_total{status="error"}[5m]) / rate(opentruss_memgraph_queries_total[5m])`

#### 业务指标面板

- **构件数量趋势**: `opentruss_elements_total`
- **检验批数量趋势**: `opentruss_inspection_lots_total`
- **工作流操作统计**: `sum by (operation_type) (rate(opentruss_workflow_operations_total[5m]))`

## 告警配置

### Prometheus 告警规则

创建 `monitoring/prometheus/alerts.yml`:

```yaml
groups:
  - name: opentruss_alerts
    interval: 30s
    rules:
      - alert: HighAPIErrorRate
        expr: rate(opentruss_api_requests_total{status=~"5.."}[5m]) / rate(opentruss_api_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "API 错误率过高"
          description: "API 错误率超过 5%"

      - alert: HighAPILatency
        expr: histogram_quantile(0.95, rate(opentruss_api_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "API 延迟过高"
          description: "P95 API 延迟超过 1 秒"

      - alert: MemgraphQueryError
        expr: rate(opentruss_memgraph_queries_total{status="error"}[5m]) > 10
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Memgraph 查询错误过多"
          description: "Memgraph 查询错误率超过阈值"
```

然后在 `prometheus.yml` 中启用：

```yaml
rule_files:
  - 'alerts.yml'
```

## 生产环境配置

### 安全配置

1. **更改 Grafana 默认密码**:
   ```bash
   docker exec -it opentruss-grafana grafana-cli admin reset-admin-password <new-password>
   ```

2. **限制 Prometheus 访问**: 使用反向代理或防火墙限制访问

3. **使用 HTTPS**: 在生产环境中配置 SSL/TLS

### 数据保留

在 `docker-compose.monitoring.yml` 中调整 Prometheus 数据保留时间：

```yaml
command:
  - '--storage.tsdb.retention.time=30d'  # 保留30天
```

### 资源限制

为监控服务添加资源限制：

```yaml
services:
  prometheus:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1'
```

## 故障排查

### 指标未显示

1. 检查后端服务是否正常运行
2. 访问 http://localhost:8000/metrics 查看指标端点
3. 检查 Prometheus 配置中的 target 地址

### Grafana 无法连接 Prometheus

1. 检查 Prometheus 服务是否运行
2. 验证 Grafana 数据源配置中的 URL
3. 检查网络连接（确保在同一个 Docker 网络中）

### 指标数据不准确

1. 检查指标标签是否正确
2. 验证 scrape_interval 设置
3. 检查时间同步

---

**最后更新**：2025-12-28  
**文档版本**：1.0  
**维护者**：OpenTruss 开发团队

## 参考

- [Prometheus 文档](https://prometheus.io/docs/)
- [Grafana 文档](https://grafana.com/docs/)
- [Prometheus Client Python](https://github.com/prometheus/client_python)

