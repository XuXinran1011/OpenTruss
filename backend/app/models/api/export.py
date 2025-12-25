"""IFC 导出 API 模型"""

from typing import List
from pydantic import BaseModel, Field
from pydantic import ConfigDict


class BatchExportRequest(BaseModel):
    """批量导出请求"""
    lot_ids: List[str] = Field(..., description="检验批 ID 列表", min_length=1)
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "lot_ids": ["lot_001", "lot_002", "lot_003"]
        }
    })

