"""Speckle Other BuiltElements (自动生成)

本文件包含的类:
  - Opening
  - Topography
  - GridLine
  - Profile
  - Network
  - View
  - Alignment
  - Baseline
  - Featureline
  - Station
"""

from typing import Optional, List, Dict, Any, Literal, Union
from pydantic import BaseModel, Field
from .base import SpeckleBuiltElementBase, Geometry2D


class Opening(SpeckleBuiltElementBase):
    """Speckle Opening element
    
    洞口元素（门窗洞口等）
    """
    geometry_2d: Optional[Geometry2D] = Field(None, alias='outline', description='洞口轮廓')
    
    class Config:
        populate_by_name = True  # Pydantic v2


class Topography(SpeckleBuiltElementBase):
    """Speckle Topography element
    
    地形元素
    """
    geometry_2d: Optional[Geometry2D] = Field(None, description='地形几何')
    
    class Config:
        populate_by_name = True  # Pydantic v2


class GridLine(SpeckleBuiltElementBase):
    """Speckle GridLine element
    
    网格线元素
    """
    geometry_2d: Geometry2D = Field(..., alias='baseLine', description='2D geometry (converted from ICurve baseLine, grid line)')
    name: Optional[str] = Field(None, description='网格线名称')
    
    class Config:
        populate_by_name = True  # Pydantic v2


class Profile(SpeckleBuiltElementBase):
    """Speckle Profile element
    
    剖面/轮廓元素
    """
    geometry_2d: Optional[Geometry2D] = Field(None, description='轮廓几何')
    
    class Config:
        populate_by_name = True  # Pydantic v2


class Network(SpeckleBuiltElementBase):
    """Speckle Network element
    
    网络元素（管道网络等）
    """
    geometry_2d: Optional[Geometry2D] = Field(None, description='网络几何')
    
    class Config:
        populate_by_name = True  # Pydantic v2


class View(SpeckleBuiltElementBase):
    """Speckle View element
    
    视图元素
    """
    name: Optional[str] = Field(None, description='视图名称')
    
    class Config:
        populate_by_name = True  # Pydantic v2


class Alignment(SpeckleBuiltElementBase):
    """Speckle Alignment element (Civil)
    
    路线对齐元素（Civil 3D）
    """
    geometry_2d: Optional[Geometry2D] = Field(None, description='对齐路线几何')
    
    class Config:
        populate_by_name = True  # Pydantic v2


class Baseline(SpeckleBuiltElementBase):
    """Speckle Baseline element (Civil)
    
    基线元素（Civil 3D）
    """
    geometry_2d: Optional[Geometry2D] = Field(None, description='基线几何')
    
    class Config:
        populate_by_name = True  # Pydantic v2


class Featureline(SpeckleBuiltElementBase):
    """Speckle Featureline element (Civil)
    
    特征线元素（Civil 3D）
    """
    geometry_2d: Optional[Geometry2D] = Field(None, description='特征线几何')
    
    class Config:
        populate_by_name = True  # Pydantic v2


class Station(SpeckleBuiltElementBase):
    """Speckle Station element (Civil)
    
    桩号元素（Civil 3D）
    """
    station: Optional[float] = Field(None, description='桩号值')
    
    class Config:
        populate_by_name = True  # Pydantic v2

