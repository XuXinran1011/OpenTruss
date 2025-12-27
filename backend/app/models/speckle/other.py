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
from pydantic import BaseModel, Field, ConfigDict
from .base import SpeckleBuiltElementBase, Geometry


class Opening(SpeckleBuiltElementBase):
    """Speckle Opening element
    
    洞口元素（门窗洞口等）
    """
    geometry: Optional[Geometry] = Field(None, alias='outline', description='洞口轮廓（3D 坐标）')
    
    model_config = ConfigDict(populate_by_name=True)


class Topography(SpeckleBuiltElementBase):
    """Speckle Topography element
    
    地形元素
    
    注意：源文件使用Mesh类型的baseGeometry，对于OpenTruss的2D工作流，使用Dict简化处理
    """
    base_geometry: Optional[Dict[str, Any]] = Field(None, alias='baseGeometry', description='基础几何（Mesh类型，使用Dict简化）')
    geometry: Optional[Geometry] = Field(None, description='地形几何（3D 坐标）')
    
    model_config = ConfigDict(populate_by_name=True)


class GridLine(SpeckleBuiltElementBase):
    """Speckle GridLine element
    
    网格线元素
    """
    geometry: Geometry = Field(..., alias='baseLine', description='3D geometry (converted from ICurve baseLine, grid line, coordinates: [[x, y, z], ...])')
    label: Optional[str] = Field(None, description='网格线标签')
    
    model_config = ConfigDict(populate_by_name=True)


class Profile(SpeckleBuiltElementBase):
    """Speckle Profile element
    
    剖面/轮廓元素
    """
    curves: Optional[List[Geometry]] = Field(None, description='轮廓曲线列表（3D 坐标）')
    name: Optional[str] = Field(None, description='剖面名称')
    start_station: Optional[float] = Field(None, alias='startStation', description='起始桩号')
    end_station: Optional[float] = Field(None, alias='endStation', description='结束桩号')
    # 保留geometry以兼容旧数据，但主要使用curves
    geometry: Optional[Geometry] = Field(None, description='轮廓几何（兼容字段，主要使用curves，3D 坐标）')
    
    model_config = ConfigDict(populate_by_name=True)


class Network(SpeckleBuiltElementBase):
    """Speckle Network element
    
    网络元素（管道网络等）
    
    注意：源文件中Network已标记为Obsolete，保持简化实现
    """
    name: Optional[str] = Field(None, description='网络名称')
    geometry: Optional[Geometry] = Field(None, description='网络几何（3D 坐标）')
    
    model_config = ConfigDict(populate_by_name=True)


class View(SpeckleBuiltElementBase):
    """Speckle View element
    
    视图元素
    """
    name: Optional[str] = Field(None, description='视图名称')
    
    model_config = ConfigDict(populate_by_name=True)


class Alignment(SpeckleBuiltElementBase):
    """Speckle Alignment element (Civil)
    
    路线对齐元素（Civil 3D）
    
    注意：baseCurve已废弃，主要使用curves属性
    """
    curves: Optional[List[Geometry]] = Field(None, description='路线曲线列表（主要几何属性，3D 坐标）')
    name: Optional[str] = Field(None, description='对齐路线名称')
    start_station: Optional[float] = Field(None, alias='startStation', description='起始桩号')
    end_station: Optional[float] = Field(None, alias='endStation', description='结束桩号')
    profiles: Optional[List[Dict[str, Any]]] = Field(None, description='剖面列表（复杂对象，使用Dict简化）')
    station_equations: Optional[List[float]] = Field(None, alias='stationEquations', description='桩号方程列表')
    station_equation_directions: Optional[List[bool]] = Field(None, alias='stationEquationDirections', description='桩号方程方向列表')
    # 保留geometry以兼容旧数据，但主要使用curves
    geometry: Optional[Geometry] = Field(None, description='对齐路线几何（兼容字段，主要使用curves，3D 坐标）')
    
    model_config = ConfigDict(populate_by_name=True)


class Baseline(SpeckleBuiltElementBase):
    """Speckle Baseline element (Civil)
    
    基线元素（Civil 3D）
    
    注意：Baseline是抽象类，实际使用中可能需要简化处理
    """
    name: Optional[str] = Field(None, description='基线名称')
    is_featureline_based: Optional[bool] = Field(None, alias='isFeaturelineBased', description='是否基于特征线')
    alignment: Optional[Dict[str, Any]] = Field(None, description='水平对齐（复杂对象，使用Dict简化）')
    profile: Optional[Dict[str, Any]] = Field(None, description='垂直剖面（复杂对象，使用Dict简化）')
    featureline: Optional[Dict[str, Any]] = Field(None, description='特征线（复杂对象，使用Dict简化）')
    geometry: Optional[Geometry] = Field(None, description='基线几何（3D 坐标）')
    
    model_config = ConfigDict(populate_by_name=True)


class Featureline(SpeckleBuiltElementBase):
    """Speckle Featureline element (Civil)
    
    特征线元素（Civil 3D）
    """
    curve: Optional[Geometry] = Field(None, description='特征线曲线（主要几何属性，3D 坐标）')
    points: Optional[List[List[float]]] = Field(None, description='点列表（3D点，每个点为[x, y, z]）')
    name: Optional[str] = Field(None, description='特征线名称')
    # 保留geometry以兼容旧数据，但主要使用curve
    geometry: Optional[Geometry] = Field(None, description='特征线几何（兼容字段，主要使用curve，3D 坐标）')
    
    model_config = ConfigDict(populate_by_name=True)


class Station(SpeckleBuiltElementBase):
    """Speckle Station element (Civil)
    
    桩号元素（Civil 3D）
    """
    number: Optional[float] = Field(None, description='桩号值')
    type: Optional[str] = Field(None, description='桩号类型')
    location: Optional[List[float]] = Field(None, description='位置坐标[x, y, z]')
    
    model_config = ConfigDict(populate_by_name=True)

