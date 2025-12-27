"""IFC 导出 API

提供检验批和项目的 IFC 文件导出接口
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.responses import Response

from app.services.export import ExportService
from app.models.api.export import BatchExportRequest
from app.core.exceptions import NotFoundError, ValidationError
from app.utils.memgraph import get_memgraph_client, MemgraphClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/export", tags=["export"])


def get_export_service(
    client: MemgraphClient = Depends(get_memgraph_client)
) -> ExportService:
    """获取 ExportService 实例（依赖注入）"""
    return ExportService(client=client)


@router.get(
    "/ifc",
    response_class=Response,
    summary="导出 IFC 文件",
    description="导出检验批或项目为 IFC 文件"
)
async def export_ifc(
    inspection_lot_id: Optional[str] = Query(None, description="检验批 ID（导出单个检验批）"),
    project_id: Optional[str] = Query(None, description="项目 ID（导出整个项目）"),
    service: ExportService = Depends(get_export_service),
) -> Response:
    """导出 IFC 文件"""
    # 参数验证（在 try-except 之外，直接抛出 HTTPException）
    if inspection_lot_id and project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot specify both inspection_lot_id and project_id"
        )
    
    if not inspection_lot_id and not project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must specify either inspection_lot_id or project_id"
        )
    
    try:
        if inspection_lot_id:
            ifc_bytes = service.export_lot_to_ifc(inspection_lot_id)
            filename = f"lot_{inspection_lot_id}.ifc"
        else:
            ifc_bytes = service.export_project_to_ifc(project_id)
            filename = f"project_{project_id}.ifc"
        
        return Response(
            content=ifc_bytes,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except (NotFoundError, ValidationError) as e:
        status_code = status.HTTP_404_NOT_FOUND if isinstance(e, NotFoundError) else status.HTTP_400_BAD_REQUEST
        logger.warning(f"Export validation failed (inspection_lot_id={inspection_lot_id}, project_id={project_id}): {e.message}")
        raise HTTPException(
            status_code=status_code,
            detail=e.message
        )
    except HTTPException:
        # 重新抛出 HTTPException，不要捕获它
        raise
    except Exception as e:
        # 其他异常通常是系统错误（如 IFC 库错误、内存不足等）
        error_message = f"导出 IFC 文件时发生错误: {str(e)}"
        logger.error(f"Failed to export IFC (inspection_lot_id={inspection_lot_id}, project_id={project_id}): {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{error_message}。如果此问题持续出现，请联系技术支持。"
        )


@router.post(
    "/ifc/batch",
    response_class=Response,
    summary="批量导出 IFC 文件",
    description="批量导出多个检验批为 IFC 文件（合并为一个文件）"
)
async def batch_export_ifc(
    request: BatchExportRequest,
    service: ExportService = Depends(get_export_service),
) -> Response:
    """批量导出 IFC 文件"""
    try:
        lot_ids = request.lot_ids
        
        # 使用多检验批合并导出功能
        ifc_bytes = service._export_multiple_lots_to_ifc(lot_ids)
        filename = f"batch_{len(lot_ids)}_lots.ifc"
        
        return Response(
            content=ifc_bytes,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except (NotFoundError, ValidationError) as e:
        status_code = status.HTTP_404_NOT_FOUND if isinstance(e, NotFoundError) else status.HTTP_400_BAD_REQUEST
        logger.warning(f"Batch export validation failed (lot_ids={request.lot_ids}): {e.message}")
        raise HTTPException(
            status_code=status_code,
            detail=e.message
        )
    except Exception as e:
        # 其他异常通常是系统错误
        error_message = f"批量导出 IFC 文件时发生错误: {str(e)}"
        logger.error(f"Failed to batch export IFC (lot_ids={request.lot_ids}): {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{error_message}。如果此问题持续出现，请联系技术支持。"
        )

