"""构件管理 API

提供构件查询和操作接口（Trace/Lift/Classify Mode）
"""

import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Query, Depends

from app.services.workbench import WorkbenchService
from app.core.exceptions import NotFoundError, ConflictError, ValidationError
from app.models.api.elements import (
    ElementListResponse,
    ElementQueryParams,
    ElementDetail,
    TopologyUpdateRequest,
    ElementUpdateRequest,
    BatchLiftRequest,
    BatchLiftResponse,
    ClassifyRequest,
    ClassifyResponse,
    BatchElementDetailRequest,
    BatchElementDetailResponse,
    BatchUpdateRequest,
    BatchUpdateResponse,
    BatchDeleteRequest,
    BatchDeleteResponse,
)
from app.utils.memgraph import get_memgraph_client, MemgraphClient


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/elements", tags=["elements"])


def get_workbench_service(
    client: MemgraphClient = Depends(get_memgraph_client)
) -> WorkbenchService:
    """获取 Workbench Service 实例（依赖注入）"""
    return WorkbenchService(client=client)


@router.get(
    "",
    response_model=dict,
    summary="获取构件列表",
    description="查询构件列表，支持多种筛选条件"
)
async def get_elements(
    level_id: Optional[str] = Query(None, description="筛选：楼层 ID"),
    item_id: Optional[str] = Query(None, description="筛选：分项 ID"),
    inspection_lot_id: Optional[str] = Query(None, description="筛选：检验批 ID"),
    status: Optional[str] = Query(None, description="筛选：状态（Draft/Verified）"),
    speckle_type: Optional[str] = Query(None, description="筛选：构件类型"),
    has_height: Optional[bool] = Query(None, description="筛选：是否有高度"),
    has_material: Optional[bool] = Query(None, description="筛选：是否有材质"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="筛选：最小置信度（0.0-1.0）"),
    max_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="筛选：最大置信度（0.0-1.0）"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    service: WorkbenchService = Depends(get_workbench_service),
) -> dict:
    """获取构件列表"""
    params = ElementQueryParams(
        level_id=level_id,
        item_id=item_id,
        inspection_lot_id=inspection_lot_id,
        status=status,  # type: ignore
        speckle_type=speckle_type,
        has_height=has_height,
        has_material=has_material,
        min_confidence=min_confidence,
        max_confidence=max_confidence,
        page=page,
        page_size=page_size,
    )
    
    result = service.query_elements(params)
    
    return {
        "status": "success",
        "data": {
            "items": [item.model_dump() for item in result["items"]],
            "total": result["total"],
            "page": result["page"],
            "page_size": result["page_size"],
        },
    }


@router.get(
    "/unassigned",
    response_model=dict,
    summary="获取未分配构件列表",
    description="获取未分配到检验批的构件列表"
)
async def get_unassigned_elements(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    service: WorkbenchService = Depends(get_workbench_service),
) -> dict:
    """获取未分配构件列表"""
    result = service.get_unassigned_elements(page=page, page_size=page_size)
    
    return {
        "status": "success",
        "data": {
            "items": [item.model_dump() for item in result["items"]],
            "total": result["total"],
            "page": result["page"],
            "page_size": result["page_size"],
        },
    }


@router.get(
    "/{element_id}",
    response_model=dict,
    summary="获取构件详情",
    description="根据构件 ID 获取构件详细信息"
)
async def get_element(
    element_id: str,
    service: WorkbenchService = Depends(get_workbench_service),
) -> dict:
    """获取构件详情"""
    try:
        element = service.get_element(element_id)
        
        if not element:
            raise NotFoundError(
                f"Element not found: {element_id}",
                {"element_id": element_id, "resource_type": "Element"}
            )
        
        return {
            "status": "success",
            "data": element.model_dump(),
        }
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_element: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取构件详情时发生意外错误，请稍后重试或联系技术支持"
        )


@router.patch(
    "/{element_id}/topology",
    response_model=dict,
    summary="更新构件拓扑关系（Trace Mode）",
    description="更新构件的几何坐标和连接关系"
)
async def update_element_topology(
    element_id: str,
    request: TopologyUpdateRequest,
    service: WorkbenchService = Depends(get_workbench_service),
) -> dict:
    """更新构件拓扑关系"""
    try:
        result = service.update_element_topology(element_id, request)
        return {
            "status": "success",
            "data": result,
        }
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )
    except Exception as e:
        logger.error(f"Unexpected error in update_element_topology: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新构件拓扑关系时发生意外错误，请稍后重试或联系技术支持"
        )


@router.patch(
    "/{element_id}",
    response_model=dict,
    summary="更新构件参数（Lift Mode）",
    description="更新构件的高度、基础偏移和材质"
)
async def update_element(
    element_id: str,
    request: ElementUpdateRequest,
    service: WorkbenchService = Depends(get_workbench_service),
) -> dict:
    """更新构件参数"""
    try:
        result = service.update_element(element_id, request)
        return {
            "status": "success",
            "data": result,
        }
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message,
        )
    except Exception as e:
        logger.error(f"Unexpected error in update_element: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新构件参数时发生意外错误，请稍后重试或联系技术支持"
        )


@router.post(
    "/batch",
    response_model=dict,
    summary="批量获取构件详情",
    description="批量获取多个构件的详细信息，包括连接关系（最多500个）"
)
async def batch_get_elements(
    request: BatchElementDetailRequest,
    service: WorkbenchService = Depends(get_workbench_service),
) -> dict:
    """批量获取构件详情"""
    try:
        result = service.batch_get_elements(request.element_ids)
        response = BatchElementDetailResponse(**result)
        return {
            "status": "success",
            "data": response.model_dump(),
        }
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )
    except Exception as e:
        logger.error(f"Unexpected error in batch_get_elements: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="批量获取构件详情时发生意外错误，请稍后重试或联系技术支持"
        )


@router.post(
    "/batch-lift",
    response_model=dict,
    summary="批量设置 Z 轴参数（Lift Mode）",
    description="批量更新多个构件的高度、基础偏移和材质"
)
async def batch_lift_elements(
    request: BatchLiftRequest,
    service: WorkbenchService = Depends(get_workbench_service),
) -> dict:
    """批量设置 Z 轴参数"""
    try:
        result = service.batch_lift_elements(request)
        return {
            "status": "success",
            "data": result.model_dump(),
        }
    except (NotFoundError, ConflictError, ValidationError) as e:
        status_code = status.HTTP_400_BAD_REQUEST
        if isinstance(e, NotFoundError):
            status_code = status.HTTP_404_NOT_FOUND
        elif isinstance(e, ConflictError):
            status_code = status.HTTP_409_CONFLICT
        raise HTTPException(
            status_code=status_code,
            detail=e.message,
        )
    except Exception as e:
        logger.error(f"Unexpected error in batch_lift_elements: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="批量设置 Z 轴参数时发生意外错误，请稍后重试或联系技术支持"
        )


@router.post(
    "/{element_id}/classify",
    response_model=dict,
    summary="将构件归类到分项（Classify Mode）",
    description="将构件归类到指定的分项"
)
async def classify_element(
    element_id: str,
    request: ClassifyRequest,
    service: WorkbenchService = Depends(get_workbench_service),
) -> dict:
    """将构件归类到分项"""
    try:
        result = service.classify_element(element_id, request)
        return {
            "status": "success",
            "data": result.model_dump(),
        }
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except Exception as e:
        logger.error(f"Unexpected error in classify_element: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="将构件归类到分项时发生意外错误，请稍后重试或联系技术支持"
        )


@router.patch(
    "/batch",
    response_model=dict,
    summary="批量更新构件",
    description="批量更新多个构件的字段（支持事务处理）"
)
async def batch_update_elements(
    request: BatchUpdateRequest,
    service: WorkbenchService = Depends(get_workbench_service),
) -> dict:
    """批量更新构件"""
    try:
        result = service.batch_update_elements(request.element_ids, request.updates)
        response = BatchUpdateResponse(**result)
        return {
            "status": "success",
            "data": response.model_dump(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to batch update elements: {str(e)}"
        )


@router.delete(
    "/batch",
    response_model=dict,
    summary="批量删除构件",
    description="批量删除多个构件及其所有关系（支持级联删除）"
)
async def batch_delete_elements(
    request: BatchDeleteRequest,
    service: WorkbenchService = Depends(get_workbench_service),
) -> dict:
    """批量删除构件"""
    try:
        result = service.batch_delete_elements(request.element_ids)
        response = BatchDeleteResponse(**result)
        return {
            "status": "success",
            "data": response.model_dump(),
        }
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except Exception as e:
        logger.error(f"Unexpected error in batch_delete_elements: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="批量删除构件时发生意外错误，请稍后重试或联系技术支持"
        )


@router.delete(
    "/{element_id}",
    response_model=dict,
    summary="删除构件",
    description="删除指定的构件及其所有关系"
)
async def delete_element(
    element_id: str,
    service: WorkbenchService = Depends(get_workbench_service),
) -> dict:
    """删除构件"""
    try:
        result = service.delete_element(element_id)
        return {
            "status": "success",
            "data": result,
        }
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except Exception as e:
        logger.error(f"Unexpected error in delete_element: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除构件时发生意外错误，请稍后重试或联系技术支持"
        )


