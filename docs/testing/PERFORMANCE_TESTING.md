# 性能测试指南

## 概述

本文档介绍如何使用Locust和k6对OpenTruss项目进行性能测试。

## 测试工具

### Locust

Locust是一个Python编写的负载测试工具，使用简单，适合API性能测试。

### k6

k6是一个现代化的性能测试工具，使用JavaScript编写测试脚本，性能优秀。

## Locust性能测试

### 安装

```bash
cd backend
pip install -r requirements-dev.txt
```

### 运行测试

#### 基本用法

```bash
# 启动Locust Web UI
locust -f tests/performance/locust/auth_load_test.py --host http://localhost:8000

# Headless模式（无UI）
locust -f tests/performance/locust/auth_load_test.py \
  --host http://localhost:8000 \
  --users 50 \
  --spawn-rate 5 \
  --run-time 5m \
  --headless \
  --html reports/locust_report.html
```

#### 可用的测试脚本

- `auth_load_test.py`: 认证API性能测试
- `elements_load_test.py`: 构件API性能测试
- `hierarchy_load_test.py`: 层级结构API性能测试
- `lots_load_test.py`: 检验批API性能测试
- `approval_load_test.py`: 审批API性能测试
- `comprehensive_load_test.py`: 综合性能测试

#### 使用配置文件

```bash
locust -f tests/performance/locust/auth_load_test.py \
  --config tests/performance/locust.conf
```

### 性能指标

Locust测试会收集以下指标：

- **响应时间**: 平均、最小、最大、P50、P95、P99
- **吞吐量**: RPS (Requests Per Second)
- **错误率**: 失败的请求百分比
- **并发用户数**: 当前活跃的虚拟用户数

### 查看报告

Locust Web UI提供实时图表和统计数据，访问 `http://localhost:8089` 查看。

Headless模式会生成HTML报告，保存在指定路径。

## k6性能测试

### 安装

#### Windows

```powershell
# 使用Chocolatey
choco install k6

# 或下载安装包
# https://github.com/grafana/k6/releases
```

#### Linux/Mac

```bash
# 使用包管理器或下载安装包
# https://k6.io/docs/getting-started/installation/
```

### 运行测试

#### 基本用法

```bash
cd backend/tests/performance/k6

# 运行认证API测试
k6 run --config k6.config.js auth.js

# 运行构件API测试
k6 run --config k6.config.js elements.js

# 运行场景化测试
k6 run --config k6.config.js scenarios.js

# 指定API地址
k6 run --env API_BASE_URL=http://localhost:8000 auth.js
```

#### 压力测试场景

```bash
# 渐进式负载测试
k6 run --env STRESS_TYPE=ramp k6_stress_test.js

# Spike测试（突发流量）
k6 run --env STRESS_TYPE=spike k6_stress_test.js

# 长时间运行稳定性测试
k6 run --env STRESS_TYPE=endurance k6_stress_test.js
```

### 性能指标

k6测试会收集以下指标：

- **http_req_duration**: HTTP请求持续时间
- **http_req_failed**: HTTP请求失败率
- **http_reqs**: HTTP请求总数和RPS
- **自定义指标**: 可在测试脚本中定义

### 查看报告

k6会在控制台输出实时统计信息。可以使用 `--out` 参数导出到其他格式：

```bash
# 导出到JSON
k6 run --out json=results.json script.js

# 导出到InfluxDB
k6 run --out influxdb=http://localhost:8086/k6 script.js
```

## 压力测试

### Locust压力测试

```bash
cd backend/tests/performance/stress

# 运行极限负载测试
locust -f locust_stress_test.py \
  --host http://localhost:8000 \
  --users 500 \
  --spawn-rate 50 \
  --run-time 30m \
  --headless
```

### k6压力测试

```bash
cd backend/tests/performance/stress

# 渐进式负载（达到500用户）
k6 run --env STRESS_TYPE=ramp k6_stress_test.js

# Spike测试（0->200用户在1分钟内）
k6 run --env STRESS_TYPE=spike k6_stress_test.js

# 长时间运行（50用户持续30分钟）
k6 run --env STRESS_TYPE=endurance k6_stress_test.js
```

### 数据库压力测试

```bash
cd backend
python tests/performance/stress/database_stress_test.py
```

## 测试数据准备

### 生成测试数据

```bash
cd backend
python -c "
from tests.performance.fixtures.test_data_generator import TestDataGenerator
from app.utils.memgraph import MemgraphClient

generator = TestDataGenerator(MemgraphClient())
dataset = generator.generate_large_dataset(
    project_id='stress_test_project',
    total_elements=10000,
    batch_size=100
)
print(f'Generated {dataset[\"total_count\"]} elements')
"
```

## 性能基准

### 响应时间目标

- **P50 (中位数)**: < 200ms
- **P95**: < 500ms
- **P99**: < 1000ms

### 吞吐量目标

- **认证API**: > 100 RPS
- **构件查询API**: > 50 RPS
- **层级结构API**: > 30 RPS

### 错误率目标

- **正常负载**: < 1%
- **高负载**: < 5%
- **极限负载**: < 10%

## 性能优化建议

### 后端优化

1. **数据库索引**: 确保关键查询字段已创建索引
2. **查询优化**: 使用分页、限制结果集大小
3. **缓存**: 对频繁访问的数据使用缓存
4. **连接池**: 配置适当的数据库连接池大小
5. **异步处理**: 对耗时操作使用异步处理

### 前端优化

1. **请求合并**: 使用批量API减少请求数
2. **分页加载**: 使用分页而非一次性加载所有数据
3. **视图裁剪**: 只渲染可见区域的元素
4. **防抖/节流**: 对频繁触发的事件使用防抖或节流

## 监控和分析

### 系统指标收集

使用 `MetricsCollector` 收集系统指标：

```python
from tests.performance.utils.metrics_collector import MetricsCollector
import threading
import time

collector = MetricsCollector(interval=1.0)
collector.start()

# 在后台线程中收集
thread = threading.Thread(target=collector.collect_continuously, daemon=True)
thread.start()

# ... 运行性能测试 ...

collector.stop()
summary = collector.get_summary()
print(summary)
```

### 报告生成

使用 `PerformanceReportGenerator` 生成HTML报告：

```python
from tests.performance.utils.report_generator import PerformanceReportGenerator

generator = PerformanceReportGenerator()
report_file = generator.generate_html_report("my_test", metrics)
print(f"Report saved to: {report_file}")
```

## CI/CD集成

性能测试已集成到GitHub Actions工作流中（`.github/workflows/performance-tests.yml`），可以：

1. 定时运行（每天凌晨2点）
2. 手动触发（选择测试类型）

## 故障排查

### 测试失败：连接被拒绝

- 检查后端服务是否正常运行
- 检查API地址是否正确
- 检查防火墙设置

### 性能下降

- 检查数据库连接池是否耗尽
- 检查系统资源使用情况（CPU、内存）
- 检查是否有慢查询

### 内存泄漏

- 长时间运行测试，观察内存使用趋势
- 检查是否有未释放的资源
- 使用内存分析工具（如memory_profiler）

## 参考资料

- [Locust文档](https://docs.locust.io/)
- [k6文档](https://k6.io/docs/)
- [性能测试最佳实践](https://k6.io/docs/guides/performance-testing/)

