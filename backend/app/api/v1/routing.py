"""路由 API

提供 MEP 路径规划和验证接口
"""

import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends, Query

from app.models.api.routing import (
    RoutingRequest,
    RoutingResponse,
    ValidationRequest,
    ValidationResponse,
    BatchRoutingRequest,
    BatchRoutingResponse,
    CompleteRoutingPlanningRequest,
    RevertRoutingPlanningRequest,
    CoordinationRequest,
    CoordinationResponse,
    AdjustedElement,
)
from app.services.routing import FlexibleRouter, RoutingService
from app.services.coordination import CoordinationService
from app.services.spatial import SpatialService
from app.core.validators import MEPRoutingValidator
from app.core.mep_routing_config import get_mep_routing_config
from app.core.brick_validator import get_brick_validator
from app.core.cable_capacity_validator import CableCapacityValidator
from app.core.exceptions import SpatialServiceError, RoutingServiceError
from app.utils.spatial_filter import calculate_route_bbox
from app.utils.memgraph import get_memgraph_client, MemgraphClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/routing", tags=["routing"])


def get_routing_service() -> FlexibleRouter:
    """获取路径规划服务实例（依赖注入）"""
    return FlexibleRouter()


def get_routing_status_service() -> RoutingService:
    """获取路由规划状态管理服务实例（依赖注入）"""
    return RoutingService()


def get_coordination_service() -> CoordinationService:
    """获取管线综合排布服务实例（依赖注入）"""
    return CoordinationService()


def get_spatial_service() -> SpatialService:
    """获取空间服务实例（依赖注入）"""
    return SpatialService()


def get_cable_capacity_validator(
    client: MemgraphClient = Depends(get_memgraph_client)
) -> CableCapacityValidator:
    """获取桥架容量验证器实例（依赖注入）"""
    return CableCapacityValidator(client)


@router.post(
    "/calculate",
    response_model=dict,
    summary="计算路径",
    description="计算符合约束的 MEP 路径，返回路径点列表（不包含具体配件信息）"
)
async def calculate_route(
    request: RoutingRequest,
    service: FlexibleRouter = Depends(get_routing_service),
    spatial_service: SpatialService = Depends(get_spatial_service)
) -> Dict[str, Any]:
    """计算路径"""
    try:
        # 从数据库查询障碍物
        obstacles = None
        if request.level_id:
            # 根据起点和终点计算边界框（带缓冲区）
            route_bbox = calculate_route_bbox(
                (request.start[0], request.start[1]),
                (request.end[0], request.end[1]),
                buffer_ratio=0.1  # 10% 缓冲区
            )
            
            obstacles_result = spatial_service.get_obstacles(
                level_id=request.level_id,
                bbox=list(route_bbox),  # 传递计算出的边界框
                obstacle_types=["Beam", "Column", "Wall", "Slab", "Space"]
            )
            # 提取Geometry对象列表
            obstacles = [obs["geometry"] for obs in obstacles_result.get("obstacles", []) if obs.get("geometry")]
            logger.debug(f"Found {len(obstacles)} obstacles in bbox {route_bbox}")
        
        result = service.route(
            start=(request.start[0], request.start[1]),
            end=(request.end[0], request.end[1]),
            element_type=request.element_type,
            element_properties=request.element_properties,
            system_type=request.system_type,
            obstacles=obstacles,
            validate_semantic=request.validate_semantic,
            source_element_type=request.source_element_type,
            target_element_type=request.target_element_type,
            element_id=request.element_id,
            level_id=request.level_id,
            validate_room_constraints=request.validate_room_constraints,
            validate_slope=request.validate_slope
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
    except (SpatialServiceError, RoutingServiceError) as e:
        logger.error(f"Service error in calculate route: {e.message}", exc_info=True, extra={"details": e.details})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message  # 使用异常消息，已经是对用户友好的消息
        )
    except Exception as e:
        logger.error(f"Unexpected error in calculate route: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="路径计算时发生意外错误，请稍后重试或联系技术支持"
        )


@router.post(
    "/validate",
    response_model=dict,
    summary="验证路径",
    description="验证路径是否符合约束和Brick Schema语义规范"
)
async def validate_route(
    request: ValidationRequest
) -> Dict[str, Any]:
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


@router.post(
    "/plan-batch",
    response_model=dict,
    summary="批量路由规划",
    description="批量计算多个路径的路由规划，支持按分项/系统/规格区间筛选"
)
async def plan_batch_routes(
    request: BatchRoutingRequest,
    service: FlexibleRouter = Depends(get_routing_service)
) -> Dict[str, Any]:
    """批量路由规划"""
    try:
        results = []
        success_count = 0
        failure_count = 0
        
        for route_request in request.routes:
            try:
                result = service.route(
                    start=(route_request.start[0], route_request.start[1]),
                    end=(route_request.end[0], route_request.end[1]),
                    element_type=route_request.element_type,
                    element_properties=route_request.element_properties,
                    system_type=route_request.system_type,
                    obstacles=None,
                    validate_semantic=route_request.validate_semantic,
                    source_element_type=route_request.source_element_type,
                    target_element_type=route_request.target_element_type,
                    level_id=request.level_id,
                    validate_room_constraints=request.validate_room_constraints
                )
                
                results.append(RoutingResponse(
                    path_points=[[p[0], p[1]] for p in result["path_points"]],
                    constraints=result.get("constraints", {}),
                    warnings=result.get("warnings", []),
                    errors=result.get("errors", [])
                ))
                success_count += 1
            except RoutingServiceError as e:
                logger.warning(f"Routing service error in batch route: {e.message}", extra={"details": e.details})
                results.append(RoutingResponse(
                    path_points=[],
                    constraints={},
                    warnings=[],
                    errors=[e.message]  # 使用异常消息，已经是对用户友好的消息
                ))
                failure_count += 1
        
        return {
            "status": "success",
            "data": BatchRoutingResponse(
                results=results,
                total=len(request.routes),
                success_count=success_count,
                failure_count=failure_count
            ).model_dump()
        }
    except Exception as e:
        logger.error(f"Failed to plan batch routes: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="批量路由规划时发生意外错误，请稍后重试或联系技术支持"
        )


@router.post(
    "/complete-planning",
    response_model=dict,
    summary="完成路由规划",
    description="标记路由规划完成，将routing_status设置为COMPLETED"
)
async def complete_routing_planning(
    request: CompleteRoutingPlanningRequest,
    service: RoutingService = Depends(get_routing_status_service)
) -> Dict[str, Any]:
    """完成路由规划"""
    try:
        result = service.complete_routing_planning(
            element_ids=request.element_ids,
            original_route_room_ids=request.original_route_room_ids
        )
        
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        logger.error(f"Failed to complete routing planning: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="完成路由规划时发生意外错误，请稍后重试或联系技术支持"
        )


@router.post(
    "/revert-planning",
    response_model=dict,
    summary="退回路由规划",
    description="退回路由规划阶段，将routing_status设置为PLANNING，coordination_status设置为PENDING"
)
async def revert_routing_planning(
    request: RevertRoutingPlanningRequest,
    service: RoutingService = Depends(get_routing_status_service)
) -> Dict[str, Any]:
    """退回路由规划"""
    try:
        result = service.revert_to_routing_planning(
            element_ids=request.element_ids
        )
        
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        logger.error(f"Failed to revert routing planning: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="撤销路由规划时发生意外错误，请稍后重试或联系技术支持"
        )


@router.get(
    "/obstacles",
    response_model=dict,
    summary="查询障碍物",
    description="查询指定楼层内的障碍物（用于路由规划）"
)
async def get_obstacles(
    level_id: str = Query(..., description="楼层ID"),
    bbox: Optional[str] = Query(None, description="边界框 [min_x,min_y,max_x,max_y]（可选）"),
    obstacle_types: Optional[str] = Query(None, description="障碍物类型列表，逗号分隔（可选，如：Beam,Column,Wall,Slab,Space）"),
    spatial_service: SpatialService = Depends(get_spatial_service)
) -> Dict[str, Any]:
    """查询障碍物"""
    try:
        # 解析bbox参数
        bbox_list = None
        if bbox:
            try:
                bbox_list = [float(x) for x in bbox.split(",")]
                if len(bbox_list) != 4:
                    raise ValueError("bbox must have 4 values: min_x,min_y,max_x,max_y")
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid bbox format: {str(e)}"
                )
        
        # 解析obstacle_types参数
        types_list = None
        if obstacle_types:
            types_list = [t.strip() for t in obstacle_types.split(",") if t.strip()]
        
        result = spatial_service.get_obstacles(
            level_id=level_id,
            bbox=bbox_list,
            obstacle_types=types_list
        )
        
        # 转换障碍物格式（Geometry需要序列化）
        obstacles_data = []
        for obs in result["obstacles"]:
            obs_data = {
                "id": obs["id"],
                "type": obs["type"],
                "geometry": obs["geometry"].model_dump() if hasattr(obs["geometry"], "model_dump") else obs["geometry"],
                "height": obs.get("height"),
                "base_offset": obs.get("base_offset")
            }
            if obs["type"] == "Space":
                obs_data["forbid_horizontal_mep"] = obs.get("forbid_horizontal_mep", False)
                obs_data["forbid_vertical_mep"] = obs.get("forbid_vertical_mep", False)
            obstacles_data.append(obs_data)
        
        return {
            "status": "success",
            "data": {
                "obstacles": obstacles_data,
                "total": result["total"]
            }
        }
    except Exception as e:
        logger.error(f"Failed to get obstacles: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询障碍物失败: {str(e)}"
        )


@router.get(
    "/cable-tray/{tray_id}/capacity",
    response_model=dict,
    summary="查询桥架容量",
    description="查询桥架内电缆容量使用情况（电力电缆≤40%，控制电缆≤50%）"
)
async def get_cable_tray_capacity(
    tray_id: str,
    validator: CableCapacityValidator = Depends(get_cable_capacity_validator)
) -> Dict[str, Any]:
    """查询桥架内电缆容量使用情况"""
    try:
        result = validator.validate_cable_tray_capacity(tray_id)
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        logger.error(f"Failed to get cable tray capacity: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询桥架容量失败: {str(e)}"
        )


@router.post(
    "/coordination",
    response_model=dict,
    summary="管线综合排布",
    description="进行3D管线综合排布，解决碰撞问题"
)
async def coordinate_layout(
    request: CoordinationRequest,
    service: CoordinationService = Depends(get_coordination_service)
) -> Dict[str, Any]:
    """管线综合排布"""
    try:
        result = service.coordinate_layout(
            level_id=request.level_id,
            element_ids=request.element_ids,
            constraints=request.constraints
        )
        
        # 转换调整后的元素格式
        adjusted_elements = [
            AdjustedElement(
                element_id=adj["element_id"],
                original_path=adj["original_path"],
                adjusted_path=adj["adjusted_path"],
                adjustment_type=adj["adjustment_type"],
                adjustment_reason=adj["adjustment_reason"]
            )
            for adj in result.get("adjusted_elements", [])
        ]
        
        return {
            "status": "success",
            "data": CoordinationResponse(
                adjusted_elements=adjusted_elements,
                collisions_resolved=result.get("collisions_resolved", 0),
                warnings=result.get("warnings", []),
                errors=result.get("errors", [])
            ).model_dump()
        }
    except Exception as e:
        logger.error(f"Failed to coordinate layout: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="管线综合排布时发生意外错误，请稍后重试或联系技术支持"
        )

