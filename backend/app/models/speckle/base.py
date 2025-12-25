"""Speckle BuiltElements 基础模型和通用类型"""

from typing import Optional, List, Dict, Any, Literal, Union
from pydantic import BaseModel, Field, ConfigDict


class Geometry2D(BaseModel):
    """2D 几何数据（OpenTruss 格式）
    
    将 Speckle 的 ICurve 转换为 OpenTruss 的 Geometry2D 格式
    """
    type: Literal["Line", "Polyline"]
    coordinates: List[List[float]] = Field(..., min_length=2, description="坐标点列表 [[x1, y1], [x2, y2], ...]")
    closed: Optional[bool] = Field(None, description="是否闭合（Polyline 专用）")


class SpeckleBuiltElementBase(BaseModel):
    """Speckle BuiltElement 基类
    
    包含所有 Speckle BuiltElements 的通用字段
    """
    # OpenTruss 特定字段
    speckle_id: Optional[str] = Field(None, description="Speckle 原始对象 ID，用于追溯")
    speckle_type: str = Field(..., description="Speckle 元素类型（如：Wall, Beam, Column）")
    
    # 通用字段（大部分 Speckle 元素都有）
    units: Optional[str] = Field(None, description="单位（如：m, ft）")
    
    # OpenTruss 扩展字段（用于数据摄入后的处理）
    level_id: Optional[str] = Field(None, description="所属楼层 ID（从 Speckle Level 对象转换）")
    zone_id: Optional[str] = Field(None, description="所属区域 ID")
    inspection_lot_id: Optional[str] = Field(None, description="所属检验批 ID")
    status: Optional[Literal["Draft", "Verified"]] = Field("Draft", description="构件状态")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="AI 识别置信度")
    
    model_config = ConfigDict(
        # 允许使用字段别名
        populate_by_name=True,
        # 示例值
        json_schema_extra={
            "example": {
                "speckle_type": "Wall",
                "level_id": "level_f1"
            }
        }
    )

