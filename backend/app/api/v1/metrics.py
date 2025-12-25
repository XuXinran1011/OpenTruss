"""Metrics API 端点

提供 Prometheus 指标导出端点
"""

from fastapi import APIRouter
from fastapi.responses import Response

from app.core.metrics import get_metrics, get_metrics_content_type

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("", response_class=Response)
async def metrics():
    """Prometheus 指标端点
    
    返回 Prometheus 格式的指标数据
    
    Returns:
        Response: Prometheus 格式的指标数据
    """
    metrics_data = get_metrics()
    return Response(
        content=metrics_data,
        media_type=get_metrics_content_type()
    )

