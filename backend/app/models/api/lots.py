"""检验批管理 API 模型"""

from typing import List, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field
from pydantic import ConfigDict


# 规则类型（使用字符串常量）
RULE_TYPE_BY_LEVEL = "BY_LEVEL"
RULE_TYPE_BY_ZONE = "BY_ZONE"
RULE_TYPE_BY_LEVEL_AND_ZONE = "BY_LEVEL_AND_ZONE"


class CreateLotsByRuleRequest(BaseModel):
    """根据规则创建检验批请求"""
    item_id: str = Field(..., description="分项 ID")
    rule_type: str = Field(..., description="规则类型（BY_LEVEL / BY_ZONE / BY_LEVEL_AND_ZONE）")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "item_id": "item_001",
            "rule_type": "BY_LEVEL"
        }
    })


class LotPreview(BaseModel):
    """检验批预览信息"""
    spatial_key: str = Field(..., description="空间键（用于标识分组）")
    spatial_scope: str = Field(..., description="空间范围描述")
    element_count: int = Field(..., description="构件数量")
    lot_name: Optional[str] = Field(None, description="检验批名称（预览）")


class CreateLotsPreviewRequest(BaseModel):
    """预览检验批创建请求"""
    item_id: str = Field(..., description="分项 ID")
    rule_type: str = Field(..., description="规则类型")


class CreateLotsPreviewResponse(BaseModel):
    """预览检验批创建响应"""
    item_id: str = Field(..., description="分项 ID")
    item_name: str = Field(..., description="分项名称")
    rule_type: str = Field(..., description="规则类型")
    preview_lots: List[LotPreview] = Field(..., description="预览检验批列表")
    total_elements: int = Field(..., description="总构件数量")


class CreatedLotInfo(BaseModel):
    """创建的检验批信息"""
    id: str = Field(..., description="检验批 ID")
    name: str = Field(..., description="检验批名称")
    spatial_scope: str = Field(..., description="空间范围")
    element_count: int = Field(..., description="构件数量")


class CreateLotsResponse(BaseModel):
    """创建检验批响应"""
    lots_created: List[CreatedLotInfo] = Field(..., description="创建的检验批列表")
    elements_assigned: int = Field(..., description="分配的构件总数")
    total_lots: int = Field(..., description="创建的检验批总数")


class AssignElementsRequest(BaseModel):
    """分配构件请求"""
    element_ids: List[str] = Field(..., description="构件 ID 列表")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "element_ids": ["element_001", "element_002"]
        }
    })


class AssignElementsResponse(BaseModel):
    """分配构件响应"""
    lot_id: str = Field(..., description="检验批 ID")
    assigned_count: int = Field(..., description="成功分配的构件数量")
    total_requested: int = Field(..., description="请求分配的构件总数")


class RemoveElementsRequest(BaseModel):
    """移除构件请求"""
    element_ids: List[str] = Field(..., description="构件 ID 列表")


class RemoveElementsResponse(BaseModel):
    """移除构件响应"""
    lot_id: str = Field(..., description="检验批 ID")
    removed_count: int = Field(..., description="成功移除的构件数量")
    total_requested: int = Field(..., description="请求移除的构件总数")


class UpdateLotStatusRequest(BaseModel):
    """更新检验批状态请求"""
    status: Literal["PLANNING", "IN_PROGRESS", "SUBMITTED", "APPROVED", "PUBLISHED"] = Field(
        ...,
        description="新状态"
    )
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "status": "IN_PROGRESS"
        }
    })


class UpdateLotStatusResponse(BaseModel):
    """更新检验批状态响应"""
    lot_id: str = Field(..., description="检验批 ID")
    old_status: str = Field(..., description="原状态")
    new_status: str = Field(..., description="新状态")
    updated_at: datetime = Field(..., description="更新时间")


class LotElementListItem(BaseModel):
    """检验批构件列表项"""
    id: str = Field(..., description="构件 ID")
    speckle_type: str = Field(..., description="构件类型")
    level_id: Optional[str] = Field(None, description="楼层 ID")
    zone_id: Optional[str] = Field(None, description="区域 ID")
    status: str = Field(..., description="构件状态")
    has_height: bool = Field(..., description="是否有高度参数")
    has_material: bool = Field(..., description="是否有材质信息")


class LotElementsResponse(BaseModel):
    """检验批构件列表响应"""
    lot_id: str = Field(..., description="检验批 ID")
    items: List[LotElementListItem] = Field(..., description="构件列表")
    total: int = Field(..., description="总数量")

