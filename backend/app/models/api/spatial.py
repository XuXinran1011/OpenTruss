"""空间 API 模型

用于空间管理 API 的请求和响应模型
"""

from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class SpaceIntegratedHangerRequest(BaseModel):
    """设置空间综合支吊架请求"""
    use_integrated_hanger: bool = Field(..., description="是否使用综合支吊架")


class SpaceIntegratedHangerResponse(BaseModel):
    """空间综合支吊架配置响应"""
    space_id: str = Field(..., description="空间ID")
    use_integrated_hanger: bool = Field(..., description="是否使用综合支吊架")
    updated_at: Optional[str] = Field(None, description="更新时间")
