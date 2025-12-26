"""路由 API 模型

用于 MEP 路径规划 API 的请求和响应模型
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict


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

