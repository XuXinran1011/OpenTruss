"""Speckle Structural BuiltElements (自动生成)

本文件包含的类:
  - Beam
  - Brace
  - Structure
  - Rebar
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict
from .base import SpeckleBuiltElementBase, Geometry


class Beam(SpeckleBuiltElementBase):
    """Speckle Beam element
    
    梁元素，从 Speckle ICurve baseLine 转换为 Geometry（3D 原生，梁中心线）
    height 表示横截面深度，而非空间高程
    """
    geometry: Geometry = Field(..., alias='baseLine', description='3D geometry (converted from ICurve baseLine, beam centerline, coordinates: [[x, y, z], ...])')
    
    model_config = ConfigDict(populate_by_name=True)


class Brace(SpeckleBuiltElementBase):
    """Speckle Brace element
    
    支撑元素（斜撑），从 Speckle ICurve baseLine 转换为 Geometry（3D 原生）
    """
    geometry: Geometry = Field(..., alias='baseLine', description='3D geometry (converted from ICurve baseLine, brace centerline, coordinates: [[x, y, z], ...])')
    
    model_config = ConfigDict(populate_by_name=True)


class Structure(SpeckleBuiltElementBase):
    """Speckle Structure element
    
    结构元素（通用结构构件）
    """
    geometry: Optional[Geometry] = Field(None, description='3D geometry (coordinates: [[x, y, z], ...])')
    
    model_config = ConfigDict(populate_by_name=True)


class Rebar(SpeckleBuiltElementBase):
    """Speckle Rebar element
    
    钢筋元素
    """
    geometry: Optional[Geometry] = Field(None, description='3D geometry (rebar shape, coordinates: [[x, y, z], ...])')
    
    model_config = ConfigDict(populate_by_name=True)

