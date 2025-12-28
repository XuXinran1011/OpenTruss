"""校验 API

提供规则引擎校验相关的API端点
"""

import logging
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any

from app.models.api.validation import (
    AngleValidationRequest,
    AngleValidationResponse,
    ZAxisValidationRequest,
    ZAxisValidationResponse,
    TopologyValidationRequest,
    TopologyValidationResponse,
    ElementListRequest,
    ElementListResponse,
    PathAngleCalculationRequest,
    PathAngleCalculationResponse,
    SemanticValidationRequest,
    SemanticValidationResponse,
    CollisionValidationRequest,
    CollisionValidationResponse,
    CollisionPair,
)
from app.core.validators import ConstructabilityValidator, TopologyValidator, SpatialValidator
from app.core.brick_validator import get_brick_validator
from app.utils.memgraph import get_memgraph_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/validation", tags=["validation"])


def get_constructability_validator() -> ConstructabilityValidator:
    """获取构造校验器实例（依赖注入）"""
    return ConstructabilityValidator()


def get_topology_validator() -> TopologyValidator:
    """获取拓扑校验器实例（依赖注入）"""
    client = get_memgraph_client()
    return TopologyValidator(client)


@router.post(
    "/constructability/validate-angle",
    response_model=Dict[str, Any],
    summary="验证角度",
    description="验证角度是否符合标准（45°, 90°, 180°），返回吸附后的角度"
)
async def validate_angle(
    request: AngleValidationRequest,
    validator: ConstructabilityValidator = Depends(get_constructability_validator)
) -> Dict[str, Any]:
    """验证角度"""
    try:
        result = validator.validate_angle(request.angle)
        return {
            "status": "success",
            "data": AngleValidationResponse(
                valid=result["valid"],
                snapped_angle=result.get("snapped_angle"),
                error=result.get("error")
            ).model_dump()
        }
    except Exception as e:
        logger.error(f"Failed to validate angle: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"角度验证失败: {str(e)}"
        )


@router.post(
    "/constructability/validate-z-axis",
    response_model=Dict[str, Any],
    summary="验证Z轴完整性",
    description="验证元素的Z轴完整性（height, base_offset是否都存在）"
)
async def validate_z_axis(
    request: ZAxisValidationRequest,
    validator: ConstructabilityValidator = Depends(get_constructability_validator)
) -> Dict[str, Any]:
    """验证Z轴完整性"""
    try:
        result = validator.validate_z_axis_completeness(request.element)
        return {
            "status": "success",
            "data": ZAxisValidationResponse(
                valid=result["valid"],
                errors=result.get("errors", []),
                warnings=result.get("warnings", [])
            ).model_dump()
        }
    except Exception as e:
        logger.error(f"Failed to validate z-axis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Z轴完整性验证失败: {str(e)}"
        )


@router.post(
    "/constructability/calculate-path-angle",
    response_model=Dict[str, Any],
    summary="计算路径角度",
    description="计算路径的角度并返回吸附后的角度"
)
async def calculate_path_angle(
    request: PathAngleCalculationRequest,
    validator: ConstructabilityValidator = Depends(get_constructability_validator)
) -> Dict[str, Any]:
    """计算路径角度"""
    try:
        angle = validator.calculate_path_angle(request.path)
        snapped_angle = validator.snap_angle(angle)
        return {
            "status": "success",
            "data": PathAngleCalculationResponse(
                angle=angle,
                snapped_angle=snapped_angle
            ).model_dump()
        }
    except Exception as e:
        logger.error(f"Failed to calculate path angle: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"路径角度计算失败: {str(e)}"
        )


@router.post(
    "/topology/validate",
    response_model=Dict[str, Any],
    summary="验证拓扑完整性",
    description="验证检验批的拓扑完整性（无悬空端点、无孤立元素）"
)
async def validate_topology(
    request: TopologyValidationRequest,
    validator: TopologyValidator = Depends(get_topology_validator)
) -> Dict[str, Any]:
    """验证拓扑完整性"""
    try:
        result = validator.validate_topology(request.lot_id)
        return {
            "status": "success",
            "data": TopologyValidationResponse(
                valid=result["valid"],
                open_ends=result.get("open_ends", []),
                isolated_elements=result.get("isolated_elements", []),
                errors=result.get("errors", [])
            ).model_dump()
        }
    except Exception as e:
        logger.error(f"Failed to validate topology: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"拓扑验证失败: {str(e)}"
        )


@router.post(
    "/topology/find-open-ends",
    response_model=Dict[str, Any],
    summary="查找悬空端点",
    description="查找悬空端点（连接数 < 2 的元素）"
)
async def find_open_ends(
    request: ElementListRequest,
    validator: TopologyValidator = Depends(get_topology_validator)
) -> Dict[str, Any]:
    """查找悬空端点"""
    try:
        open_ends = validator.find_open_ends(request.element_ids)
        return {
            "status": "success",
            "data": ElementListResponse(element_ids=open_ends).model_dump()
        }
    except Exception as e:
        logger.error(f"Failed to find open ends: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查找悬空端点失败: {str(e)}"
        )


@router.post(
    "/topology/find-isolated",
    response_model=Dict[str, Any],
    summary="查找孤立元素",
    description="查找孤立元素（没有任何连接的元素）"
)
async def find_isolated(
    request: ElementListRequest,
    validator: TopologyValidator = Depends(get_topology_validator)
) -> Dict[str, Any]:
    """查找孤立元素"""
    try:
        isolated = validator.find_isolated_elements(request.element_ids)
        return {
            "status": "success",
            "data": ElementListResponse(element_ids=isolated).model_dump()
        }
    except Exception as e:
        logger.error(f"Failed to find isolated elements: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查找孤立元素失败: {str(e)}"
        )


@router.post(
    "/semantic/validate-connection",
    response_model=Dict[str, Any],
    summary="验证语义连接",
    description="验证两种元素类型是否可以连接（规则引擎 Phase 1：语义防呆）"
)
async def validate_semantic_connection(
    request: SemanticValidationRequest,
) -> Dict[str, Any]:
    """验证语义连接"""
    try:
        brick_validator = get_brick_validator()
        result = brick_validator.validate_mep_connection(
            request.source_type,
            request.target_type,
            request.relationship
        )
        return {
            "status": "success",
            "data": SemanticValidationResponse(**result).model_dump()
        }
    except Exception as e:
        logger.error(f"Failed to validate semantic connection: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"语义连接验证失败: {str(e)}"
        )


def get_spatial_validator() -> SpatialValidator:
    """获取空间校验器实例（依赖注入）"""
    client = get_memgraph_client()
    return SpatialValidator(client)


@router.post(
    "/spatial/validate-collisions",
    response_model=Dict[str, Any],
    summary="验证碰撞",
    description="检查构件之间的物理碰撞（规则引擎 Phase 3：空间避障）"
)
async def validate_collisions(
    request: CollisionValidationRequest,
    validator: SpatialValidator = Depends(get_spatial_validator)
) -> Dict[str, Any]:
    """验证碰撞"""
    try:
        # 确定要检查的元素ID列表
        element_ids: List[str] = []
        
        if request.lot_id:
            # 从检验批获取元素
            query = """
            MATCH (lot:InspectionLot {id: $lot_id})-[r]->(e:Element)
            WHERE type(r) = 'MANAGEMENT_CONTAINS'
            RETURN e.id as element_id
            """
            result = validator.client.execute_query(query, {"lot_id": request.lot_id})
            element_ids = [row["element_id"] for row in result if row.get("element_id")]
        elif request.element_ids:
            element_ids = request.element_ids
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="必须提供 lot_id 或 element_ids"
            )
        
        if not element_ids:
            return {
                "status": "success",
                "data": CollisionValidationResponse(
                    valid=True,
                    collisions=[],
                    errors=[]
                ).model_dump()
            }
        
        # 执行碰撞检测
        result = validator.validate_collisions(element_ids)
        
        # 转换碰撞对格式
        collision_pairs = [
            CollisionPair(
                element_id_1=coll["element_id_1"],
                element_id_2=coll["element_id_2"]
            )
            for coll in result.get("collisions", [])
        ]
        
        return {
            "status": "success",
            "data": CollisionValidationResponse(
                valid=result["valid"],
                collisions=collision_pairs,
                errors=result.get("errors", [])
            ).model_dump()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate collisions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"碰撞验证失败: {str(e)}"
        )

