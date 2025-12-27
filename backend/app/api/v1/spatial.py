"""空间管理 API

提供空间（Space）相关的管理接口，包括空间限制设置等
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends, Path

from app.models.api.routing import (
    SpaceRestrictionsRequest,
    SpaceRestrictionsResponse,
)
from app.models.api.spatial import (
    SpaceIntegratedHangerRequest,
    SpaceIntegratedHangerResponse,
)
from app.services.spatial import SpatialService
from app.core.exceptions import NotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/spaces", tags=["spatial"])


def get_spatial_service() -> SpatialService:
    """获取空间服务实例（依赖注入）"""
    return SpatialService()


@router.put(
    "/{space_id}/mep-restrictions",
    response_model=dict,
    summary="设置空间限制",
    description="设置空间禁止MEP管线穿过（MEP专业负责人和总工权限）"
)
async def set_space_mep_restrictions(
    space_id: str = Path(..., description="空间ID"),
    request: SpaceRestrictionsRequest = ...,
    service: SpatialService = Depends(get_spatial_service)
) -> Dict[str, Any]:
    """设置空间MEP限制"""
    try:
        result = service.set_space_mep_restrictions(
            space_id=space_id,
            forbid_horizontal_mep=request.forbid_horizontal_mep,
            forbid_vertical_mep=request.forbid_vertical_mep
        )
        
        return {
            "status": "success",
            "data": SpaceRestrictionsResponse(
                space_id=result["space_id"],
                forbid_horizontal_mep=result["forbid_horizontal_mep"],
                forbid_vertical_mep=result["forbid_vertical_mep"],
                updated_at=result["updated_at"]
            ).model_dump()
        }
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Failed to set space MEP restrictions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"设置空间限制失败: {str(e)}"
        )


@router.get(
    "/{space_id}/mep-restrictions",
    response_model=dict,
    summary="获取空间限制",
    description="获取空间的MEP限制设置"
)
async def get_space_mep_restrictions(
    space_id: str = Path(..., description="空间ID"),
    service: SpatialService = Depends(get_spatial_service)
) -> Dict[str, Any]:
    """获取空间MEP限制"""
    try:
        result = service.get_space_mep_restrictions(space_id)
        
        return {
            "status": "success",
            "data": result
        }
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Failed to get space MEP restrictions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取空间限制失败: {str(e)}"
        )


@router.put(
    "/{space_id}/integrated-hanger",
    response_model=dict,
    summary="设置空间综合支吊架",
    description="设置空间是否使用综合支吊架"
)
async def set_space_integrated_hanger(
    space_id: str = Path(..., description="空间ID"),
    request: SpaceIntegratedHangerRequest = ...,
    service: SpatialService = Depends(get_spatial_service)
) -> Dict[str, Any]:
    """设置空间综合支吊架配置"""
    try:
        result = service.set_space_integrated_hanger(
            space_id=space_id,
            use_integrated_hanger=request.use_integrated_hanger
        )
        
        return {
            "status": "success",
            "data": SpaceIntegratedHangerResponse(
                space_id=result["space_id"],
                use_integrated_hanger=result["use_integrated_hanger"],
                updated_at=result.get("updated_at")
            ).model_dump()
        }
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Failed to set space integrated hanger: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"设置空间综合支吊架失败: {str(e)}"
        )


@router.get(
    "/{space_id}/integrated-hanger",
    response_model=dict,
    summary="获取空间综合支吊架配置",
    description="获取空间的综合支吊架配置"
)
async def get_space_integrated_hanger(
    space_id: str = Path(..., description="空间ID"),
    service: SpatialService = Depends(get_spatial_service)
) -> Dict[str, Any]:
    """获取空间综合支吊架配置"""
    try:
        result = service.get_space_integrated_hanger(space_id)
        
        return {
            "status": "success",
            "data": result
        }
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Failed to get space integrated hanger: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取空间综合支吊架配置失败: {str(e)}"
        )

