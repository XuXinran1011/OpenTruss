"""Speckle Spatial BuiltElements (自动生成)

本文件包含的类:
  - Level
  - Room
  - Space
  - Zone
  - Area
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from .base import SpeckleBuiltElementBase, Geometry2D


class Level(SpeckleBuiltElementBase):
    """Speckle Level element
    
    楼层元素（在 OpenTruss 中通常只使用 level_id，但保留完整定义以兼容 Speckle 数据）
    """
    elevation: Optional[float] = Field(None, description='楼层标高')
    name: Optional[str] = Field(None, description='楼层名称')
    
    class Config:
        populate_by_name = True  # Pydantic v2


class Room(SpeckleBuiltElementBase):
    """Speckle Room element
    
    房间元素
    """
    geometry_2d: Optional[Geometry2D] = Field(None, alias='outline', description='房间轮廓')
    name: Optional[str] = Field(None, description='房间名称')
    number: Optional[str] = Field(None, description='房间编号')
    base_point: Optional[List[float]] = Field(None, alias='basePoint', description='基准点坐标 [x, y, z]')
    height: Optional[float] = Field(None, description='房间高度')
    voids: Optional[List[Geometry2D]] = Field(default_factory=list, description='开洞轮廓列表')
    area: Optional[float] = Field(None, description='房间面积')
    volume: Optional[float] = Field(None, description='房间体积')
    
    class Config:
        populate_by_name = True  # Pydantic v2


class Space(SpeckleBuiltElementBase):
    """Speckle Space element
    
    空间元素（MEP 空间）
    """
    geometry_2d: Optional[Geometry2D] = Field(None, alias='outline', description='空间轮廓')
    name: Optional[str] = Field(None, description='空间名称')
    number: Optional[str] = Field(None, description='空间编号')
    base_point: Optional[List[float]] = Field(None, alias='basePoint', description='基准点坐标 [x, y, z]')
    base_offset: Optional[float] = Field(None, description='基础偏移')
    top_level: Optional[str] = Field(None, alias='topLevel', description='顶部楼层 ID（从 Level 对象转换）')
    top_offset: Optional[float] = Field(None, description='顶部偏移')
    voids: Optional[List[Geometry2D]] = Field(default_factory=list, description='开洞轮廓列表')
    space_type: Optional[str] = Field(None, alias='spaceType', description='空间类型')
    zone_name: Optional[str] = Field(None, alias='zoneName', description='区域名称')
    room_id: Optional[str] = Field(None, alias='roomId', description='关联房间 ID')
    phase_name: Optional[str] = Field(None, alias='phaseName', description='阶段名称')
    area: Optional[float] = Field(None, description='空间面积')
    volume: Optional[float] = Field(None, description='空间体积')
    
    class Config:
        populate_by_name = True  # Pydantic v2


class Zone(SpeckleBuiltElementBase):
    """Speckle Zone element
    
    区域元素
    """
    geometry_2d: Optional[Geometry2D] = Field(None, alias='outline', description='区域轮廓')
    name: Optional[str] = Field(None, description='区域名称')
    
    class Config:
        populate_by_name = True  # Pydantic v2


class Area(SpeckleBuiltElementBase):
    """Speckle Area element
    
    面积元素
    """
    geometry_2d: Optional[Geometry2D] = Field(None, alias='outline', description='面积轮廓')
    area: Optional[float] = Field(None, description='面积值')
    name: Optional[str] = Field(None, description='面积名称')
    
    class Config:
        populate_by_name = True  # Pydantic v2

