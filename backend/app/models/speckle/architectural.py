"""Speckle Architectural BuiltElements (自动生成)

本文件包含的类:
  - Wall
  - Floor
  - Ceiling
  - Roof
  - Column
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict
from .base import SpeckleBuiltElementBase, Geometry


class Wall(SpeckleBuiltElementBase):
    """Speckle Wall element
    
    墙体元素，从 Speckle ICurve baseLine 转换为 Geometry（3D 原生）
    """
    geometry: Geometry = Field(..., alias='baseLine', description='3D geometry (converted from ICurve baseLine, coordinates: [[x, y, z], ...])')
    height: Optional[float] = Field(None, description='墙体高度')
    elements: Optional[List[Dict[str, Any]]] = Field(None, description='嵌套元素（如门窗等）')
    
    model_config = ConfigDict(populate_by_name=True)


class Floor(SpeckleBuiltElementBase):
    """Speckle Floor element
    
    楼板元素，从 Speckle ICurve outline 转换为 Geometry（3D 原生）
    """
    geometry: Geometry = Field(..., alias='outline', description='3D geometry outline (coordinates: [[x, y, z], ...])')
    voids: Optional[List[Geometry]] = Field(default_factory=list, description='开洞轮廓列表（3D 坐标）')
    elements: Optional[List[Dict[str, Any]]] = Field(None, description='嵌套元素')
    
    model_config = ConfigDict(populate_by_name=True)


class Ceiling(SpeckleBuiltElementBase):
    """Speckle Ceiling element
    
    吊顶元素
    """
    geometry: Geometry = Field(..., alias='outline', description='3D geometry outline (coordinates: [[x, y, z], ...])')
    voids: Optional[List[Geometry]] = Field(default_factory=list, description='开洞轮廓列表（3D 坐标）')
    elements: Optional[List[Dict[str, Any]]] = Field(None, description='嵌套元素')
    
    model_config = ConfigDict(populate_by_name=True)


class Roof(SpeckleBuiltElementBase):
    """Speckle Roof element
    
    屋顶元素
    """
    geometry: Geometry = Field(..., alias='outline', description='3D geometry outline (coordinates: [[x, y, z], ...])')
    voids: Optional[List[Geometry]] = Field(default_factory=list, description='开洞轮廓列表（3D 坐标）')
    elements: Optional[List[Dict[str, Any]]] = Field(None, description='嵌套元素')
    
    model_config = ConfigDict(populate_by_name=True)


class Column(SpeckleBuiltElementBase):
    """Speckle Column element
    
    柱元素，从 Speckle ICurve baseLine 转换为 Geometry（3D 原生，通常为圆形或多边形截面轮廓）
    """
    geometry: Geometry = Field(..., alias='baseLine', description='3D geometry (converted from ICurve baseLine, coordinates: [[x, y, z], ...])')
    
    model_config = ConfigDict(populate_by_name=True)

