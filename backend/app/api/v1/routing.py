"""路由 API

提供 MEP 路径规划和验证接口
"""

import logging
from fastapi import APIRouter, HTTPException, status, Depends

from app.models.api.routing import (
    RoutingRequest,
    RoutingResponse,
    ValidationRequest,
    ValidationResponse,
)
from app.services.routing import FlexibleRouter
from app.core.validators import MEPRoutingValidator
from app.core.mep_routing_config import get_mep_routing_config
from app.core.brick_validator import get_brick_validator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/routing", tags=["routing"])


def get_routing_service() -> FlexibleRouter:
    """获取路径规划服务实例（依赖注入）"""
    return FlexibleRouter()


@router.post(
    "/calculate",
    response_model=dict,
    summary="计算路径",
    description="计算符合约束的 MEP 路径，返回路径点列表（不包含具体配件信息）"
)
async def calculate_route(
    request: RoutingRequest,
    service: FlexibleRouter = Depends(get_routing_service)
) -> dict:
    """计算路径"""
    try:
        result = service.route(
            start=(request.start[0], request.start[1]),
            end=(request.end[0], request.end[1]),
            element_type=request.element_type,
            element_properties=request.element_properties,
            system_type=request.system_type,
            obstacles=None,  # TODO: 从数据库查询障碍物
            validate_semantic=request.validate_semantic,
            source_element_type=request.source_element_type,
            target_element_type=request.target_element_type
        )
        
        return {
            "status": "success",
            "data": RoutingResponse(
                path_points=[[p[0], p[1]] for p in result["path_points"]],
                constraints=result.get("constraints", {}),
                warnings=result.get("warnings", []),
                errors=result.get("errors", [])
            ).model_dump()
        }
    except Exception as e:
        logger.error(f"Failed to calculate route: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"路径计算失败: {str(e)}"
        )


@router.post(
    "/validate",
    response_model=dict,
    summary="验证路径",
    description="验证路径是否符合约束和Brick Schema语义规范"
)
async def validate_route(
    request: ValidationRequest
) -> dict:
    """验证路径"""
    errors = []
    warnings = []
    semantic_errors = []
    constraint_errors = []
    
    # 1. Brick Schema 语义验证
    semantic_valid = True
    if request.source_element_type and request.target_element_type:
        brick_validator = get_brick_validator()
        semantic_result = brick_validator.validate_mep_connection(
            request.source_element_type,
            request.target_element_type,
            relationship="feeds"
        )
        semantic_valid = semantic_result["valid"]
        if not semantic_valid:
            semantic_errors.append(semantic_result.get("error", "语义验证失败"))
    
    # 2. 约束验证
    constraint_valid = True
    config_loader = get_mep_routing_config()
    constraints = config_loader.get_constraints(
        request.element_type,
        request.system_type
    )
    
    # 验证路径角度约束
    path_validation = MEPRoutingValidator.validate_mep_routing_path(
        request.path_points,
        request.element_type,
        request.system_type,
        constraints
    )
    
    if not path_validation["valid"]:
        constraint_valid = False
        constraint_errors.extend(path_validation["errors"])
    
    warnings.extend(path_validation["warnings"])
    
    # 验证转弯半径（如果有元素属性）
    if request.element_properties:
        # 获取转弯半径约束
        if request.element_type in ["Pipe", "Duct", "Conduit"]:
            diameter = request.element_properties.get("diameter", 0)
            bend_radius_ratio = config_loader.get_bend_radius_ratio(
                request.element_type,
                diameter
            )
            if bend_radius_ratio:
                min_radius = diameter * bend_radius_ratio / 1000.0  # 转换为米
                radius_validation = MEPRoutingValidator.validate_bend_radius(
                    request.path_points,
                    min_radius
                )
                if not radius_validation["valid"]:
                    constraint_valid = False
                    constraint_errors.extend(radius_validation["errors"])
                warnings.extend(radius_validation["warnings"])
        
        # 验证电缆桥架宽度
        elif request.element_type == "CableTray":
            width = request.element_properties.get("width", 0)
            cable_bend_radius = request.element_properties.get("cable_bend_radius", width)
            min_width_ratio = config_loader.get_min_width_ratio(cable_bend_radius)
            if min_width_ratio:
                width_validation = MEPRoutingValidator.validate_cable_tray_width(
                    width,
                    cable_bend_radius,
                    min_width_ratio
                )
                if not width_validation["valid"]:
                    constraint_valid = False
                    constraint_errors.extend(width_validation["errors"])
                warnings.extend(width_validation["warnings"])
    
    # 合并所有错误和警告
    errors.extend(semantic_errors)
    errors.extend(constraint_errors)
    
    valid = semantic_valid and constraint_valid and len(errors) == 0
    
    return {
        "status": "success",
        "data": ValidationResponse(
            valid=valid,
            semantic_valid=semantic_valid,
            constraint_valid=constraint_valid,
            errors=errors,
            warnings=warnings,
            semantic_errors=semantic_errors,
            constraint_errors=constraint_errors
        ).model_dump()
    }

