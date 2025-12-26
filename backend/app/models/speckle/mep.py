"""Speckle MEP BuiltElements (自动生成)

本文件包含的类:
  - Duct
  - Pipe
  - CableTray
  - Conduit
  - Wire
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict
from .base import SpeckleBuiltElementBase, Geometry2D


class Duct(SpeckleBuiltElementBase):
    """Speckle Duct element
    
    风管元素，从 Speckle ICurve baseCurve 转换为 Geometry2D（风管中心线）
    
    注意：Speckle 使用 baseCurve（不是 baseLine），API 会在解析时处理兼容性
    """
    geometry_2d: Geometry2D = Field(..., alias='baseCurve', description='2D geometry (converted from ICurve baseCurve, duct centerline). Also accepts "baseLine" for backward compatibility.')
    width: Optional[float] = Field(None, description='风管宽度')
    height: Optional[float] = Field(None, description='风管高度')
    diameter: Optional[float] = Field(None, description='风管直径（圆形风管）')
    length: Optional[float] = Field(None, description='风管长度')
    velocity: Optional[float] = Field(None, description='风速')
    
    model_config = ConfigDict(populate_by_name=True)


class Pipe(SpeckleBuiltElementBase):
    """Speckle Pipe element
    
    管道元素，从 Speckle ICurve baseCurve 转换为 Geometry2D（管道中心线）
    
    注意：Speckle 使用 baseCurve（不是 baseLine），API 会在解析时处理兼容性
    """
    geometry_2d: Geometry2D = Field(..., alias='baseCurve', description='2D geometry (converted from ICurve baseCurve, pipe centerline). Also accepts "baseLine" for backward compatibility.')
    length: Optional[float] = Field(None, description='管道长度')
    diameter: Optional[float] = Field(None, description='管道直径')
    flowrate: Optional[float] = Field(None, alias='flowRate', description='流量')
    relative_roughness: Optional[float] = Field(None, alias='relativeRoughness', description='相对粗糙度')
    slope: Optional[float] = Field(None, description='管道坡度（百分比%，正数表示向下，负数表示向上）')
    
    model_config = ConfigDict(populate_by_name=True)


class CableTray(SpeckleBuiltElementBase):
    """Speckle CableTray element
    
    电缆桥架元素，从 Speckle ICurve baseCurve 转换为 Geometry2D（桥架中心线）
    """
    geometry_2d: Geometry2D = Field(..., alias='baseCurve', description='2D geometry (converted from ICurve baseCurve, cable tray centerline)')
    width: Optional[float] = Field(None, description='桥架宽度')
    height: Optional[float] = Field(None, description='桥架高度')
    length: Optional[float] = Field(None, description='桥架长度')
    
    model_config = ConfigDict(populate_by_name=True)


class Conduit(SpeckleBuiltElementBase):
    """Speckle Conduit element
    
    导管元素，从 Speckle ICurve baseCurve 转换为 Geometry2D（导管中心线）
    """
    geometry_2d: Geometry2D = Field(..., alias='baseCurve', description='2D geometry (converted from ICurve baseCurve, conduit centerline)')
    diameter: Optional[float] = Field(None, description='导管直径')
    length: Optional[float] = Field(None, description='导管长度')
    
    model_config = ConfigDict(populate_by_name=True)


class Wire(SpeckleBuiltElementBase):
    """Speckle Wire element
    
    电线元素，使用 segments 列表表示电线的多段路径
    """
    segments: List[Geometry2D] = Field(..., description='电线路径段列表（每个段为一条 ICurve）')
    
    model_config = ConfigDict(populate_by_name=True)

