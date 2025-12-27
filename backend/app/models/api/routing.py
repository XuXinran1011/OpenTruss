"""路由 API 模型

用于 MEP 路径规划 API 的请求和响应模型
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


class RoutingRequest(BaseModel):
    """路径计算请求"""
    start: List[float] = Field(..., min_length=2, max_length=2, description="起点坐标 [x, y]")
    end: List[float] = Field(..., min_length=2, max_length=2, description="终点坐标 [x, y]")
    element_type: Literal["Pipe", "Duct", "CableTray", "Conduit", "Wire"] = Field(
        ...,
        description="元素类型"
    )
    element_properties: Dict[str, Any] = Field(
        ...,
        description="元素属性（diameter, width, height 等，单位：毫米）"
    )
    system_type: Optional[str] = Field(
        None,
        description="系统类型（如：gravity_drainage, pressure_water, power_cable）"
    )
    source_element_type: Optional[str] = Field(
        None,
        description="源元素类型（用于Brick Schema语义验证）"
    )
    target_element_type: Optional[str] = Field(
        None,
        description="目标元素类型（用于Brick Schema语义验证）"
    )
    validate_semantic: bool = Field(
        default=True,
        description="是否进行Brick Schema语义验证"
    )
    element_id: Optional[str] = Field(
        None,
        description="元素ID（用于获取原始路由Room列表）"
    )
    level_id: Optional[str] = Field(
        None,
        description="楼层ID（用于查询Space和Room）"
    )
    validate_room_constraints: bool = Field(
        default=True,
        description="是否验证Room约束"
    )
    validate_slope: bool = Field(
        default=True,
        description="是否验证坡度约束"
    )
    
    @field_validator('start', 'end')
    @classmethod
    def validate_coordinates(cls, v: List[float]) -> List[float]:
        """验证坐标值
        
        Args:
            v: 坐标列表
            
        Returns:
            List[float]: 验证后的坐标列表
            
        Raises:
            ValueError: 如果坐标无效
        """
        if len(v) != 2:
            raise ValueError("坐标必须包含2个值: [x, y]")
        
        x, y = v[0], v[1]
        
        # 检查坐标是否为数字
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            raise ValueError("坐标值必须是数字")
        
        # 检查坐标范围（合理的建筑坐标范围：-10000 到 10000 米）
        if abs(x) > 10000 or abs(y) > 10000:
            raise ValueError("坐标值超出合理范围: 应在 -10000 到 10000 之间")
        
        return v
    
    @model_validator(mode='after')
    def validate_start_end_different(self) -> 'RoutingRequest':
        """验证起点和终点不能相同
        
        Returns:
            RoutingRequest: 验证后的请求对象
            
        Raises:
            ValueError: 如果起点和终点相同
        """
        if self.start == self.end:
            raise ValueError("起点和终点不能相同")
        return self
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "start": [0.0, 0.0],
            "end": [10.0, 10.0],
            "element_type": "Pipe",
            "element_properties": {
                "diameter": 100
            },
            "system_type": "gravity_drainage",
            "source_element_type": "Pump",
            "target_element_type": "Pipe"
        }
    })


class RoutingResponse(BaseModel):
    """路径计算响应"""
    path_points: List[List[float]] = Field(
        ...,
        description="路径点列表 [[x1, y1], [x2, y2], ...]"
    )
    constraints: Dict[str, Any] = Field(
        ...,
        description="约束信息（bend_radius, min_width 等）"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="警告信息列表"
    )
    errors: List[str] = Field(
        default_factory=list,
        description="错误信息列表"
    )
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "path_points": [[0.0, 0.0], [5.0, 0.0], [5.0, 5.0], [10.0, 10.0]],
            "constraints": {
                "bend_radius": 0.1,
                "pattern": "double_45"
            },
            "warnings": [],
            "errors": []
        }
    })


class ValidationRequest(BaseModel):
    """路径验证请求"""
    path_points: List[List[float]] = Field(
        ...,
        min_length=2,
        description="路径点列表 [[x1, y1], [x2, y2], ...]"
    )
    element_type: Literal["Pipe", "Duct", "CableTray", "Conduit", "Wire"] = Field(
        ...,
        description="元素类型"
    )
    system_type: Optional[str] = Field(
        None,
        description="系统类型"
    )
    element_properties: Optional[Dict[str, Any]] = Field(
        None,
        description="元素属性（用于验证转弯半径、宽度等）"
    )
    source_element_type: Optional[str] = Field(
        None,
        description="源元素类型（用于Brick Schema语义验证）"
    )
    target_element_type: Optional[str] = Field(
        None,
        description="目标元素类型（用于Brick Schema语义验证）"
    )
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "path_points": [[0.0, 0.0], [5.0, 0.0], [5.0, 5.0], [10.0, 10.0]],
            "element_type": "Pipe",
            "system_type": "gravity_drainage",
            "element_properties": {
                "diameter": 100
            },
            "source_element_type": "Pump",
            "target_element_type": "Pipe"
        }
    })


class ValidationResponse(BaseModel):
    """路径验证响应"""
    valid: bool = Field(..., description="验证是否通过")
    semantic_valid: bool = Field(..., description="Brick Schema语义验证是否通过")
    constraint_valid: bool = Field(..., description="约束验证是否通过")
    errors: List[str] = Field(default_factory=list, description="错误信息列表")
    warnings: List[str] = Field(default_factory=list, description="警告信息列表")
    semantic_errors: List[str] = Field(default_factory=list, description="语义验证错误")
    constraint_errors: List[str] = Field(default_factory=list, description="约束验证错误")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "valid": True,
            "semantic_valid": True,
            "constraint_valid": True,
            "errors": [],
            "warnings": [],
            "semantic_errors": [],
            "constraint_errors": []
        }
    })


class BatchRoutingRequest(BaseModel):
    """批量路由规划请求"""
    routes: List[RoutingRequest] = Field(..., min_length=1, description="路由请求列表")
    level_id: Optional[str] = Field(None, description="楼层ID（用于Room/Space验证）")
    validate_room_constraints: bool = Field(default=True, description="是否验证Room约束")


class BatchRoutingResponse(BaseModel):
    """批量路由规划响应"""
    results: List[RoutingResponse] = Field(..., description="路由结果列表")
    total: int = Field(..., description="总数量")
    success_count: int = Field(..., description="成功数量")
    failure_count: int = Field(..., description="失败数量")


class CompleteRoutingPlanningRequest(BaseModel):
    """完成路由规划请求"""
    element_ids: List[str] = Field(..., min_length=1, description="元素ID列表")
    original_route_room_ids: Optional[Dict[str, List[str]]] = Field(
        None,
        description="元素ID到Room ID列表的映射（可选）"
    )


class RevertRoutingPlanningRequest(BaseModel):
    """退回路由规划请求"""
    element_ids: List[str] = Field(..., min_length=1, description="元素ID列表")


class CoordinationRequest(BaseModel):
    """管线综合排布请求"""
    level_id: str = Field(..., description="楼层ID")
    element_ids: Optional[List[str]] = Field(
        None,
        description="要排布的元素ID列表（如果为None，排布该楼层所有MEP元素）"
    )
    constraints: Optional[Dict[str, Any]] = Field(
        None,
        description="约束条件"
    )
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "level_id": "level_f1",
            "element_ids": ["element_001", "element_002"],
            "constraints": {
                "priorities": {
                    "element_001": 1,
                    "element_002": 2
                },
                "avoid_collisions": True,
                "minimize_bends": True,
                "close_to_ceiling": True
            }
        }
    })


class AdjustedElement(BaseModel):
    """调整后的元素"""
    element_id: str = Field(..., description="元素ID")
    original_path: List[List[float]] = Field(..., description="原始路径")
    adjusted_path: List[List[float]] = Field(..., description="调整后的路径")
    adjustment_type: str = Field(..., description="调整类型（horizontal_translation, vertical_translation, add_bend）")
    adjustment_reason: str = Field(..., description="调整原因")


class CoordinationResponse(BaseModel):
    """管线综合排布响应"""
    adjusted_elements: List[AdjustedElement] = Field(..., description="调整后的元素列表")
    collisions_resolved: int = Field(..., description="解决的碰撞数量")
    warnings: List[str] = Field(default_factory=list, description="警告信息")
    errors: List[str] = Field(default_factory=list, description="错误信息")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "adjusted_elements": [
                {
                    "element_id": "element_001",
                    "original_path": [[0, 0], [10, 0]],
                    "adjusted_path": [[0, 0], [5, 0], [5, -0.2], [10, -0.2]],
                    "adjustment_type": "vertical_translation",
                    "adjustment_reason": "避开碰撞"
                }
            ],
            "collisions_resolved": 2,
            "warnings": [],
            "errors": []
        }
    })


class SpaceRestrictionsRequest(BaseModel):
    """空间限制设置请求"""
    forbid_horizontal_mep: bool = Field(default=False, description="禁止水平MEP穿过")
    forbid_vertical_mep: bool = Field(default=False, description="禁止竖向MEP穿过")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "forbid_horizontal_mep": True,
            "forbid_vertical_mep": False
        }
    })


class SpaceRestrictionsResponse(BaseModel):
    """空间限制设置响应"""
    space_id: str = Field(..., description="空间ID")
    forbid_horizontal_mep: bool = Field(..., description="禁止水平MEP穿过")
    forbid_vertical_mep: bool = Field(..., description="禁止竖向MEP穿过")
    updated_at: str = Field(..., description="更新时间")

