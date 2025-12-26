"""规则管理 API 模型

定义规则管理相关的请求和响应模型
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class RulePreviewRequest(BaseModel):
    """规则预览请求"""
    rule_type: Literal["BY_LEVEL", "BY_ZONE", "BY_LEVEL_AND_ZONE"] = Field(
        ...,
        description="规则类型"
    )
    item_id: str = Field(..., description="分项 ID")


class RulePreviewResponse(BaseModel):
    """规则预览响应"""
    rule_type: str = Field(..., description="规则类型")
    estimated_lots: int = Field(..., description="预估创建的检验批数量")
    groups: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="分组信息列表，每个分组包含 key, count, label"
    )


class RuleInfo(BaseModel):
    """规则信息"""
    rule_type: str = Field(..., description="规则类型")
    name: str = Field(..., description="规则名称")
    description: str = Field(..., description="规则描述")


class RuleListResponse(BaseModel):
    """规则列表响应"""
    rules: List[RuleInfo] = Field(default_factory=list, description="规则列表")

