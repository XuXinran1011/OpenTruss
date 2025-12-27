"""Prometheus 指标导出模块

用于收集和导出系统性能指标
"""

from typing import Dict, Any
from prometheus_client import Counter, Histogram, Gauge, Info
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
import time

# API 请求指标
api_request_count = Counter(
    "opentruss_api_requests_total",
    "Total number of API requests",
    ["method", "endpoint", "status"]
)

api_request_duration = Histogram(
    "opentruss_api_request_duration_seconds",
    "API request duration in seconds",
    ["method", "endpoint"]
)

# 业务指标
elements_total = Gauge(
    "opentruss_elements_total",
    "Total number of elements in the database",
    ["status"]
)

inspection_lots_total = Gauge(
    "opentruss_inspection_lots_total",
    "Total number of inspection lots",
    ["status"]
)

# Memgraph 查询指标
memgraph_query_duration = Histogram(
    "opentruss_memgraph_query_duration_seconds",
    "Memgraph query duration in seconds",
    ["query_type"]
)

memgraph_query_count = Counter(
    "opentruss_memgraph_queries_total",
    "Total number of Memgraph queries",
    ["query_type", "status"]
)

# 工作流指标
workflow_operations_total = Counter(
    "opentruss_workflow_operations_total",
    "Total number of workflow operations",
    ["operation_type", "status"]
)

# 系统信息
system_info = Info(
    "opentruss_system",
    "OpenTruss system information"
)

# 初始化系统信息
system_info.info({
    "version": "1.0.0",
    "description": "OpenTruss - Graph First BIM Middleware",
    "release_date": "2025-01-01"
})


def record_api_request(method: str, endpoint: str, status_code: int, duration: float):
    """记录 API 请求指标"""
    api_request_count.labels(method=method, endpoint=endpoint, status=str(status_code)).inc()
    api_request_duration.labels(method=method, endpoint=endpoint).observe(duration)


def record_memgraph_query(query_type: str, duration: float, success: bool = True):
    """记录 Memgraph 查询指标"""
    memgraph_query_duration.labels(query_type=query_type).observe(duration)
    memgraph_query_count.labels(query_type=query_type, status="success" if success else "error").inc()
    
    # 记录慢查询（超过 1 秒）
    if duration > 1.0:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Slow query detected: {query_type} took {duration:.3f}s")
    """记录 Memgraph 查询指标"""
    status = "success" if success else "error"
    memgraph_query_count.labels(query_type=query_type, status=status).inc()
    memgraph_query_duration.labels(query_type=query_type).observe(duration)


def record_workflow_operation(operation_type: str, success: bool = True):
    """记录工作流操作指标"""
    status = "success" if success else "error"
    workflow_operations_total.labels(operation_type=operation_type, status=status).inc()


def update_element_count(status: str, count: int):
    """更新构件数量指标"""
    elements_total.labels(status=status).set(count)


def update_inspection_lot_count(status: str, count: int):
    """更新检验批数量指标"""
    inspection_lots_total.labels(status=status).set(count)


def get_metrics() -> bytes:
    """获取 Prometheus 格式的指标数据"""
    return generate_latest()


def get_metrics_content_type() -> str:
    """获取指标内容的 Content-Type"""
    return CONTENT_TYPE_LATEST

