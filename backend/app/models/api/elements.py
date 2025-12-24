"""构件 API 模型

用于构件查询和操作 API 的请求和响应模型
"""

from typing import Optional, List, Literal, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from app.models.speckle.base import Geometry2D


class ElementListItem(BaseModel):
    """构件列表项（简化版本，用于列表展示）"""
    id: str = Field(..., description="构件 ID")
    speckle_type: str = Field(..., description="构件类型")
    level_id: str = Field(..., description="所属楼层 ID")
    inspection_lot_id: Optional[str] = Field(None, description="所属检验批 ID")
    status: Literal["Draft", "Verified"] = Field(..., description="状态")
    has_height: bool = Field(..., description="是否设置了高度")
    has_material: bool = Field(..., description="是否设置了材质")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "element_001",
            "speckle_type": "Wall",
            "level_id": "level_f1",
            "inspection_lot_id": "lot_001",
            "status": "Draft",
            "has_height": True,
            "has_material": False,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    })


class ElementDetail(BaseModel):
    """构件详情"""
    id: str = Field(..., description="构件 ID")
    speckle_id: Optional[str] = Field(None, description="Speckle 原始对象 ID")
    speckle_type: str = Field(..., description="构件类型")
    geometry_2d: Geometry2D = Field(..., description="2D 几何数据")
    height: Optional[float] = Field(None, description="高度")
    base_offset: Optional[float] = Field(None, description="基础偏移")
    material: Optional[str] = Field(None, description="材质")
    level_id: str = Field(..., description="所属楼层 ID")
    zone_id: Optional[str] = Field(None, description="所属区域 ID")
    inspection_lot_id: Optional[str] = Field(None, description="所属检验批 ID")
    status: Literal["Draft", "Verified"] = Field(..., description="状态")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="AI 识别置信度")
    locked: bool = Field(..., description="是否锁定")
    connected_elements: Optional[List[str]] = Field(default_factory=list, description="连接的构件 ID 列表")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "element_001",
            "speckle_type": "Wall",
            "geometry_2d": {
                "type": "Polyline",
                "coordinates": [[0, 0], [10, 0], [10, 5], [0, 5], [0, 0]],
                "closed": True
            },
            "height": 3.0,
            "base_offset": 0.0,
            "material": "concrete",
            "level_id": "level_f1",
            "status": "Draft",
            "confidence": 0.85,
            "locked": False,
            "connected_elements": ["element_002", "element_003"],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    })


class ElementListResponse(BaseModel):
    """构件列表响应"""
    items: List[ElementListItem] = Field(..., description="构件列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "items": [],
            "total": 0,
            "page": 1,
            "page_size": 20
        }
    })


class ElementQueryParams(BaseModel):
    """构件查询参数（用于 GET 请求的查询参数）"""
    level_id: Optional[str] = Field(None, description="筛选：楼层 ID")
    item_id: Optional[str] = Field(None, description="筛选：分项 ID")
    inspection_lot_id: Optional[str] = Field(None, description="筛选：检验批 ID")
    status: Optional[Literal["Draft", "Verified"]] = Field(None, description="筛选：状态")
    speckle_type: Optional[str] = Field(None, description="筛选：构件类型")
    has_height: Optional[bool] = Field(None, description="筛选：是否有高度")
    has_material: Optional[bool] = Field(None, description="筛选：是否有材质")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")


class TopologyUpdateRequest(BaseModel):
    """拓扑更新请求（Trace Mode）"""
    geometry_2d: Optional[Geometry2D] = Field(None, description="更新的 2D 几何数据")
    connected_elements: Optional[List[str]] = Field(default_factory=list, description="连接的构件 ID 列表")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "geometry_2d": {
                "type": "Polyline",
                "coordinates": [[0, 0], [10, 0], [10, 5], [0, 5], [0, 0]],
                "closed": True
            },
            "connected_elements": ["element_002", "element_003"]
        }
    })


class ElementUpdateRequest(BaseModel):
    """构件更新请求（Lift Mode）"""
    height: Optional[float] = Field(None, description="高度")
    base_offset: Optional[float] = Field(None, description="基础偏移")
    material: Optional[str] = Field(None, description="材质")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "height": 3.0,
            "base_offset": 0.0,
            "material": "concrete"
        }
    })


class BatchLiftRequest(BaseModel):
    """批量 Lift 请求"""
    element_ids: List[str] = Field(..., min_length=1, description="构件 ID 列表")
    height: Optional[float] = Field(None, description="高度")
    base_offset: Optional[float] = Field(None, description="基础偏移")
    material: Optional[str] = Field(None, description="材质")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "element_ids": ["element_001", "element_002"],
            "height": 3.0,
            "base_offset": 0.0,
            "material": "concrete"
        }
    })


class BatchLiftResponse(BaseModel):
    """批量 Lift 响应"""
    updated_count: int = Field(..., description="更新的构件数量")
    element_ids: List[str] = Field(..., description="更新的构件 ID 列表")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "updated_count": 2,
            "element_ids": ["element_001", "element_002"]
        }
    })


class ClassifyRequest(BaseModel):
    """归类请求（Classify Mode）"""
    item_id: str = Field(..., description="目标分项 ID")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "item_id": "item_001"
        }
    })


class ClassifyResponse(BaseModel):
    """归类响应"""
    element_id: str = Field(..., description="构件 ID")
    item_id: str = Field(..., description="目标分项 ID")
    previous_item_id: Optional[str] = Field(None, description="之前的分项 ID（如果有）")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "element_id": "element_001",
            "item_id": "item_001",
            "previous_item_id": None
        }
    })


