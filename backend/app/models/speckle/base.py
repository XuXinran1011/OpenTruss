"""Speckle BuiltElements 基础模型和通用类型"""

from typing import Optional, List, Dict, Any, Literal, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator


class Point(BaseModel):
    """3D 点坐标
    
    用于表示空间中的点，z 坐标默认为 0.0（用于 2D 源）
    """
    x: float = Field(..., description="X 坐标")
    y: float = Field(..., description="Y 坐标")
    z: float = Field(default=0.0, description="Z 坐标（默认 0.0）")
    
    def to_list(self) -> List[float]:
        """转换为列表格式 [x, y, z]"""
        return [self.x, self.y, self.z]
    
    @classmethod
    def from_list(cls, coord: List[float]) -> "Point":
        """从列表格式创建 Point
        
        Args:
            coord: 坐标列表，可以是 [x, y] 或 [x, y, z]
        
        Returns:
            Point: 3D 点对象
        """
        if len(coord) == 2:
            return cls(x=coord[0], y=coord[1], z=0.0)
        elif len(coord) == 3:
            z = coord[2] if coord[2] is not None else 0.0
            return cls(x=coord[0], y=coord[1], z=z)
        else:
            raise ValueError(f"Invalid coordinate length: {len(coord)}, expected 2 or 3. Coordinate: {coord}")


def normalize_coordinates(coords: List[List[float]]) -> List[List[float]]:
    """规范化坐标：2D 输入自动补 z=0.0，null z 值默认为 0.0
    
    Args:
        coords: 坐标列表，可以是 2D [[x, y], ...] 或 3D [[x, y, z], ...]
    
    Returns:
        规范化的 3D 坐标列表 [[x, y, z], ...]
    
    Raises:
        ValueError: 如果坐标格式无效
    """
    normalized = []
    for coord in coords:
        if len(coord) == 2:
            # 2D 输入：自动补 z=0.0
            normalized.append([coord[0], coord[1], 0.0])
        elif len(coord) == 3:
            # 3D 输入：处理 null z 值
            z = coord[2] if coord[2] is not None else 0.0
            normalized.append([coord[0], coord[1], z])
        else:
            raise ValueError(f"Invalid coordinate length: {len(coord)}, expected 2 or 3. Coordinate: {coord}")
    return normalized


class Geometry(BaseModel):
    """3D 原生几何数据（OpenTruss 格式）
    
    底层数据模型是 3D 原生的，支持：
    - AI 识别结果（2D 输入，自动补 z=0.0）
    - Revit 导出数据（3D 输入，无损保存）
    
    坐标格式：[[x1, y1, z1], [x2, y2, z2], ...]
    """
    type: Literal["Line", "Polyline"]
    coordinates: List[List[float]] = Field(
        ..., 
        min_length=2, 
        description="3D 坐标点列表 [[x1, y1, z1], [x2, y2, z2], ...]。支持 2D 输入（自动补 z=0.0）"
    )
    closed: Optional[bool] = Field(None, description="是否闭合（Polyline 专用）")
    
    @field_validator('coordinates', mode='before')
    @classmethod
    def validate_and_normalize_coordinates(cls, v: Any) -> List[List[float]]:
        """验证并规范化坐标
        
        支持 2D 和 3D 输入，统一转换为 3D 格式
        """
        if not isinstance(v, list):
            raise ValueError("coordinates must be a list")
        
        # 规范化坐标（2D→3D 转换）
        return normalize_coordinates(v)
    
    @field_validator('coordinates', mode='after')
    @classmethod
    def validate_coordinate_length(cls, v: List[List[float]]) -> List[List[float]]:
        """验证每个坐标点都是 3D（长度为 3）"""
        for i, coord in enumerate(v):
            if len(coord) != 3:
                raise ValueError(f"Coordinate {i} must have 3 elements [x, y, z], got {len(coord)}: {coord}")
        return v


# 向后兼容别名（已废弃，将在后续版本移除）
Geometry2D = Geometry


class SpeckleBuiltElementBase(BaseModel):
    """Speckle BuiltElement 基类
    
    包含所有 Speckle BuiltElements 的通用字段
    """
    # OpenTruss 特定字段
    id: Optional[str] = Field(None, description="元素ID")
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

