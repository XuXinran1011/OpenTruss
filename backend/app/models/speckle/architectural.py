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
from .base import SpeckleBuiltElementBase, Geometry2D


class Wall(SpeckleBuiltElementBase):
    """Speckle Wall element
    
    墙体元素，从 Speckle ICurve baseLine 转换为 Geometry2D
    """
    geometry_2d: Geometry2D = Field(..., alias='baseLine', description='2D geometry (converted from ICurve baseLine)')
    height: Optional[float] = Field(None, description='墙体高度')
    elements: Optional[List[Dict[str, Any]]] = Field(None, description='嵌套元素（如门窗等）')
    
    model_config = ConfigDict(populate_by_name=True)


class Floor(SpeckleBuiltElementBase):
    """Speckle Floor element
    
    楼板元素，从 Speckle ICurve outline 转换为 Geometry2D
    """
    geometry_2d: Geometry2D = Field(..., alias='outline', description='2D geometry outline')
    voids: Optional[List[Geometry2D]] = Field(default_factory=list, description='开洞轮廓列表')
    elements: Optional[List[Dict[str, Any]]] = Field(None, description='嵌套元素')
    
    model_config = ConfigDict(populate_by_name=True)


class Ceiling(SpeckleBuiltElementBase):
    """Speckle Ceiling element
    
    吊顶元素
    """
    geometry_2d: Geometry2D = Field(..., alias='outline', description='2D geometry outline')
    voids: Optional[List[Geometry2D]] = Field(default_factory=list, description='开洞轮廓列表')
    elements: Optional[List[Dict[str, Any]]] = Field(None, description='嵌套元素')
    
    model_config = ConfigDict(populate_by_name=True)


class Roof(SpeckleBuiltElementBase):
    """Speckle Roof element
    
    屋顶元素
    """
    geometry_2d: Geometry2D = Field(..., alias='outline', description='2D geometry outline')
    voids: Optional[List[Geometry2D]] = Field(default_factory=list, description='开洞轮廓列表')
    elements: Optional[List[Dict[str, Any]]] = Field(None, description='嵌套元素')
    
    model_config = ConfigDict(populate_by_name=True)


class Column(SpeckleBuiltElementBase):
    """Speckle Column element
    
    柱元素，从 Speckle ICurve baseLine 转换为 Geometry2D（通常为圆形或多边形截面轮廓）
    """
    geometry_2d: Geometry2D = Field(..., alias='baseLine', description='2D geometry (converted from ICurve baseLine)')
    
    model_config = ConfigDict(populate_by_name=True)

