"""Speckle Structural BuiltElements (自动生成)

本文件包含的类:
  - Beam
  - Brace
  - Structure
  - Rebar
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict
from .base import SpeckleBuiltElementBase, Geometry2D


class Beam(SpeckleBuiltElementBase):
    """Speckle Beam element
    
    梁元素，从 Speckle ICurve baseLine 转换为 Geometry2D（梁中心线）
    """
    geometry_2d: Geometry2D = Field(..., alias='baseLine', description='2D geometry (converted from ICurve baseLine, beam centerline)')
    
    model_config = ConfigDict(populate_by_name=True)


class Brace(SpeckleBuiltElementBase):
    """Speckle Brace element
    
    支撑元素（斜撑），从 Speckle ICurve baseLine 转换为 Geometry2D
    """
    geometry_2d: Geometry2D = Field(..., alias='baseLine', description='2D geometry (converted from ICurve baseLine, brace centerline)')
    
    model_config = ConfigDict(populate_by_name=True)


class Structure(SpeckleBuiltElementBase):
    """Speckle Structure element
    
    结构元素（通用结构构件）
    """
    geometry_2d: Optional[Geometry2D] = Field(None, description='2D geometry')
    
    model_config = ConfigDict(populate_by_name=True)


class Rebar(SpeckleBuiltElementBase):
    """Speckle Rebar element
    
    钢筋元素
    """
    geometry_2d: Optional[Geometry2D] = Field(None, description='2D geometry (rebar shape)')
    
    model_config = ConfigDict(populate_by_name=True)

