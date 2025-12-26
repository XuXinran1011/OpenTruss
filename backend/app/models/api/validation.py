"""校验 API 模型

定义校验相关的请求和响应模型
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class AngleValidationRequest(BaseModel):
    """角度验证请求"""
    angle: float = Field(..., description="角度值（度）", ge=0, le=360)


class AngleValidationResponse(BaseModel):
    """角度验证响应"""
    valid: bool = Field(..., description="是否有效")
    snapped_angle: Optional[float] = Field(None, description="吸附后的角度")
    error: Optional[str] = Field(None, description="错误信息")


class ZAxisValidationRequest(BaseModel):
    """Z轴完整性验证请求"""
    element: Dict[str, Any] = Field(..., description="元素数据字典")


class ZAxisValidationResponse(BaseModel):
    """Z轴完整性验证响应"""
    valid: bool = Field(..., description="是否有效")
    errors: List[str] = Field(default_factory=list, description="错误信息列表")
    warnings: List[str] = Field(default_factory=list, description="警告信息列表")


class TopologyValidationRequest(BaseModel):
    """拓扑验证请求"""
    lot_id: str = Field(..., description="检验批 ID")


class TopologyValidationResponse(BaseModel):
    """拓扑验证响应"""
    valid: bool = Field(..., description="是否有效")
    open_ends: List[str] = Field(default_factory=list, description="悬空端点元素ID列表")
    isolated_elements: List[str] = Field(default_factory=list, description="孤立元素ID列表")
    errors: List[str] = Field(default_factory=list, description="错误信息列表")


class ElementListRequest(BaseModel):
    """元素列表请求"""
    element_ids: List[str] = Field(..., description="元素ID列表")


class ElementListResponse(BaseModel):
    """元素列表响应"""
    element_ids: List[str] = Field(..., description="元素ID列表")


class PathAngleCalculationRequest(BaseModel):
    """路径角度计算请求"""
    path: List[List[float]] = Field(..., description="路径点列表 [[x1, y1], [x2, y2], ...]")


class PathAngleCalculationResponse(BaseModel):
    """路径角度计算响应"""
    angle: float = Field(..., description="角度值（度）")
    snapped_angle: Optional[float] = Field(None, description="吸附后的角度")


class SemanticValidationRequest(BaseModel):
    """语义校验请求"""
    source_type: str = Field(..., description="源元素类型（Speckle 类型）")
    target_type: str = Field(..., description="目标元素类型（Speckle 类型）")
    relationship: str = Field(default="feeds", description="关系类型（feeds, feeds_from, controls 等）")


class SemanticValidationResponse(BaseModel):
    """语义校验响应"""
    valid: bool = Field(..., description="是否可以连接")
    source_type: str = Field(..., description="源元素类型")
    target_type: str = Field(..., description="目标元素类型")
    relationship: str = Field(..., description="关系类型")
    allowed_relationships: List[str] = Field(default_factory=list, description="允许的关系类型列表")
    error: Optional[str] = Field(None, description="错误信息（如果连接无效）")
    suggestion: Optional[str] = Field(None, description="建议的关系类型（如果连接无效）")


class CollisionValidationRequest(BaseModel):
    """碰撞校验请求"""
    lot_id: Optional[str] = Field(None, description="检验批 ID（如果提供，则检查检验批内所有构件）")
    element_ids: Optional[List[str]] = Field(None, description="元素ID列表（如果提供，则检查指定元素）")


class CollisionPair(BaseModel):
    """碰撞对"""
    element_id_1: str = Field(..., description="第一个构件 ID")
    element_id_2: str = Field(..., description="第二个构件 ID")


class CollisionValidationResponse(BaseModel):
    """碰撞校验响应"""
    valid: bool = Field(..., description="是否有碰撞（True 表示无碰撞）")
    collisions: List[CollisionPair] = Field(default_factory=list, description="碰撞的构件对列表")
    errors: List[str] = Field(default_factory=list, description="错误信息列表")

