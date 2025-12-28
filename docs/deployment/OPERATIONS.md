# OpenTruss 运维手册

## 1. 概述

本文档提供 OpenTruss 系统的运维指南，包括监控、故障排查、性能调优和日常维护。

---

## 2. 系统监控

### 2.1 监控指标

#### 2.1.1 系统指标

| 指标 | 正常范围 | 告警阈值 | 说明 |
|------|---------|---------|------|
| CPU 使用率 | < 70% | > 85% | 持续 5 分钟 |
| 内存使用率 | < 80% | > 90% | 持续 5 分钟 |
| 磁盘使用率 | < 80% | > 90% | - |
| 磁盘 I/O | < 80% | > 90% | 持续 5 分钟 |
| 网络带宽 | < 80% | > 90% | 持续 5 分钟 |

#### 2.1.2 应用指标

| 指标 | 正常范围 | 告警阈值 | 说明 |
|------|---------|---------|------|
| API 响应时间 (P95) | < 200ms | > 500ms | 持续 5 分钟 |
| API 错误率 | < 1% | > 5% | 持续 5 分钟 |
| 数据库查询时间 | < 100ms | > 500ms | 持续 5 分钟 |
| 活跃连接数 | < 1000 | > 2000 | - |

#### 2.1.3 业务指标

| 指标 | 说明 |
|------|------|
| 检验批数量 | 按状态统计 |
| 构件数量 | 按状态统计 |
| 用户活跃度 | 日活跃用户数 |
| 审批进度 | 各分部验收进度 |

### 2.2 监控工具

**Prometheus + Grafana**:
- 指标收集: Prometheus
- 可视化: Grafana
- 告警: Alertmanager

**日志聚合**:
- ELK Stack (Elasticsearch, Logstash, Kibana)
- 或 Loki + Grafana

### 2.3 告警规则

**Prometheus 告警规则** (`alerts.yml`):

```yaml
groups:
  - name: opentruss_alerts
    rules:
      - alert: HighCPUUsage
        expr: cpu_usage > 85
        for: 5m
        annotations:
          summary: "CPU 使用率过高"
          description: "CPU 使用率超过 85%，持续 5 分钟"
      
      - alert: HighAPIErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "API 错误率过高"
          description: "API 错误率超过 5%，持续 5 分钟"
      
      - alert: DatabaseSlowQuery
        expr: memgraph_query_duration_seconds > 0.5
        for: 5m
        annotations:
          summary: "数据库查询缓慢"
          description: "数据库查询时间超过 500ms"
```

---

## 3. 日志管理

### 3.1 日志级别

- **DEBUG**: 详细调试信息
- **INFO**: 一般信息
- **WARNING**: 警告信息
- **ERROR**: 错误信息
- **CRITICAL**: 严重错误

### 3.2 日志位置

| 服务 | 日志路径 |
|------|---------|
| 后端 | `/app/logs/opentruss.log` |
| Memgraph | `/var/log/memgraph/` |
| Nginx | `/var/log/nginx/` |

### 3.3 日志查看

```bash
# 查看后端日志
docker-compose logs -f backend

# 查看最近 100 行
docker-compose logs --tail=100 backend

# 查看特定时间段的日志
docker-compose logs --since="2024-01-01T00:00:00" backend

# 搜索错误日志
docker-compose logs backend | grep ERROR
```

### 3.4 日志轮转

配置 Logrotate (`/etc/logrotate.d/opentruss`):

```
/app/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 root root
    sharedscripts
    postrotate
        docker-compose restart backend
    endscript
}
```

---

## 4. 故障排查

### 4.1 常见问题

#### 问题 1: API 响应缓慢

**症状**: API 响应时间超过 500ms

**排查步骤**:
1. 检查系统资源（CPU、内存）
2. 查看数据库查询性能
3. 检查网络延迟
4. 查看应用日志

**解决方案**:
- 优化数据库查询
- 增加缓存
- 扩容服务器资源

#### 问题 2: 数据库连接失败

**症状**: 无法连接到 Memgraph

**排查步骤**:
```bash
# 检查 Memgraph 容器状态
docker-compose ps memgraph

# 检查端口是否开放
netstat -an | grep 7687

# 检查 Memgraph 日志
docker-compose logs memgraph
```

**解决方案**:
- 重启 Memgraph 容器
- 检查网络配置
- 验证连接字符串

#### 问题 3: 内存泄漏

**症状**: 内存使用持续增长

**排查步骤**:
1. 使用 `docker stats` 查看容器内存
2. 分析应用日志
3. 使用内存分析工具

**解决方案**:
- 修复内存泄漏代码
- 增加内存限制
- 重启容器

#### 问题 4: 磁盘空间不足

**症状**: 磁盘使用率超过 90%

**排查步骤**:
```bash
# 查看磁盘使用
df -h

# 查找大文件
du -sh /var/lib/docker/volumes/*

# 清理 Docker 资源
docker system prune -a
```

**解决方案**:
- 清理日志文件
- 清理 Docker 镜像和容器
- 扩容磁盘

### 4.2 故障处理流程

1. **发现问题**: 通过监控告警或用户反馈
2. **确认问题**: 验证问题是否真实存在
3. **定位问题**: 查看日志、监控指标
4. **解决问题**: 应用修复方案
5. **验证修复**: 确认问题已解决
6. **记录问题**: 更新故障记录

---

## 5. 性能调优

### 5.1 数据库优化

#### 5.1.1 索引优化

```cypher
// 为常用查询字段创建索引
CREATE INDEX ON :Element(id);
CREATE INDEX ON :Element(level_id);
CREATE INDEX ON :Element(inspection_lot_id);
CREATE INDEX ON :InspectionLot(status);
```

#### 5.1.2 查询优化

**优化前**:
```cypher
MATCH (e:Element)
WHERE e.level_id = "level_f1"
RETURN e
```

**优化后**:
```cypher
MATCH (e:Element)
USING INDEX e:Element(level_id)
WHERE e.level_id = "level_f1"
RETURN e
```

#### 5.1.3 连接池配置

```python
# 配置 Memgraph 连接池
from pymemgraph import Memgraph

db = Memgraph(
    host="localhost",
    port=7687,
    max_connections=20,  # 最大连接数
    connection_timeout=30
)
```

### 5.2 应用优化

#### 5.2.1 异步处理

使用异步 I/O 提高并发性能：

```python
from fastapi import FastAPI
import asyncio

app = FastAPI()

@app.get("/api/v1/elements")
async def get_elements():
    # 异步查询数据库
    result = await db.execute_async(query)
    return result
```

#### 5.2.2 缓存策略

使用 Redis 缓存热点数据：

```python
import redis

redis_client = redis.Redis(host='localhost', port=6379)

def get_elements_cached(item_id: str):
    cache_key = f"elements:{item_id}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # 查询数据库
    elements = db.query_elements(item_id)
    
    # 缓存结果（TTL: 5 分钟）
    redis_client.setex(cache_key, 300, json.dumps(elements))
    return elements
```

### 5.3 前端优化

- **代码分割**: 按路由分割代码
- **懒加载**: 延迟加载非关键组件
- **虚拟滚动**: 处理大量列表数据
- **防抖节流**: 优化用户输入

---

## 6. 备份与恢复

### 6.1 备份策略

#### 6.1.1 数据备份

**全量备份**: 每天凌晨 2 点
**增量备份**: 每小时

**备份脚本** (`scripts/backup.sh`):

```bash
#!/bin/bash
BACKUP_DIR="/backup/opentruss"
DATE=$(date +%Y%m%d_%H%M%S)

# 备份 Memgraph 数据
docker run --rm \
  -v opentruss_memgraph_data:/data \
  -v $BACKUP_DIR:/backup \
  alpine tar czf /backup/memgraph-$DATE.tar.gz /data

# 上传到云存储（可选）
# aws s3 cp $BACKUP_DIR/memgraph-$DATE.tar.gz s3://opentruss-backups/
```

#### 6.1.2 配置备份

备份配置文件和环境变量：

```bash
tar czf config-backup-$DATE.tar.gz \
  .env.production \
  nginx/nginx.conf \
  docker-compose.yml
```

### 6.2 恢复流程

#### 6.2.1 数据恢复

```bash
# 1. 停止服务
docker-compose down

# 2. 恢复数据
docker run --rm \
  -v opentruss_memgraph_data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/memgraph-20240101_020000.tar.gz -C /

# 3. 启动服务
docker-compose up -d

# 4. 验证恢复
docker-compose exec backend python scripts/verify_data.py
```

#### 6.2.2 灾难恢复

1. **准备备用服务器**
2. **恢复数据备份**
3. **恢复配置文件**
4. **启动服务**
5. **验证系统功能**

---

## 7. 安全维护

### 7.1 定期更新

- **系统更新**: 每月检查系统更新
- **依赖更新**: 每季度更新依赖包
- **安全补丁**: 及时应用安全补丁

### 7.2 密钥轮换

- **JWT Secret**: 每季度轮换
- **数据库密码**: 每半年轮换
- **SSL 证书**: 每年更新

### 7.3 访问控制

- **最小权限原则**: 只授予必要权限
- **定期审计**: 检查用户权限
- **日志审计**: 记录所有操作

---

## 8. 容量规划

### 8.1 数据增长预测

根据历史数据预测未来增长：

| 指标 | 当前 | 3 个月后 | 6 个月后 |
|------|------|---------|---------|
| 项目数 | 10 | 15 | 25 |
| 构件数 | 100K | 200K | 400K |
| 检验批数 | 1K | 2K | 4K |

### 8.2 扩容策略

- **垂直扩容**: 增加服务器资源
- **水平扩容**: 增加服务器数量
- **数据库分片**: 按项目分片（未来）

---

## 9. 日常维护任务

### 9.1 每日任务

- [ ] 检查系统监控告警
- [ ] 查看错误日志
- [ ] 检查磁盘空间
- [ ] 验证备份是否成功

### 9.2 每周任务

- [ ] 检查系统性能指标
- [ ] 审查安全日志
- [ ] 更新文档
- [ ] 测试备份恢复

### 9.3 每月任务

- [ ] 系统更新
- [ ] 依赖更新
- [ ] 性能优化评估
- [ ] 容量规划评估

---

## 10. 应急响应

### 10.1 应急联系

- **技术负责人**: [联系方式]
- **运维团队**: [联系方式]
- **安全团队**: [联系方式]

### 10.2 应急流程

1. **确认问题严重性**
2. **通知相关人员**
3. **启动应急响应**
4. **记录处理过程**
5. **事后总结**

---

## 11. 运维工具

### 11.1 常用命令

```bash
# 查看容器状态
docker-compose ps

# 查看资源使用
docker stats

# 进入容器
docker-compose exec backend bash

# 重启服务
docker-compose restart backend

# 查看日志
docker-compose logs -f backend
```

### 11.2 监控脚本

创建监控脚本 (`scripts/monitor.sh`):

```bash
#!/bin/bash
# 检查系统健康状态

# 检查容器状态
docker-compose ps | grep -v "Up"

# 检查磁盘空间
df -h | awk '$5 > 90 {print}'

# 检查内存使用
free -h

# 检查 API 健康
curl -f http://localhost/health || echo "API 不健康"
```

---

**最后更新**：2025-12-28  
**文档版本**：1.0  
**维护者**：OpenTruss 开发团队

