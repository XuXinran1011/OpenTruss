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
from .base import SpeckleBuiltElementBase, Geometry


class Duct(SpeckleBuiltElementBase):
    """Speckle Duct element
    
    风管元素，从 Speckle ICurve baseCurve 转换为 Geometry（3D 原生，风管中心线）
    
    注意：Speckle 使用 baseCurve（不是 baseLine），API 会在解析时处理兼容性
    """
    geometry: Geometry = Field(..., alias='baseCurve', description='3D geometry (converted from ICurve baseCurve, duct centerline, coordinates: [[x, y, z], ...]). Also accepts "baseLine" for backward compatibility.')
    width: Optional[float] = Field(None, description='风管宽度')
    height: Optional[float] = Field(None, description='风管高度')
    diameter: Optional[float] = Field(None, description='风管直径（圆形风管）')
    length: Optional[float] = Field(None, description='风管长度')
    velocity: Optional[float] = Field(None, description='风速')
    
    model_config = ConfigDict(populate_by_name=True)


class Pipe(SpeckleBuiltElementBase):
    """Speckle Pipe element
    
    管道元素，从 Speckle ICurve baseCurve 转换为 Geometry（3D 原生，管道中心线）
    height 表示横截面深度（如果管道有矩形截面），而非空间高程
    
    注意：Speckle 使用 baseCurve（不是 baseLine），API 会在解析时处理兼容性
    """
    geometry: Geometry = Field(..., alias='baseCurve', description='3D geometry (converted from ICurve baseCurve, pipe centerline, coordinates: [[x, y, z], ...]). Also accepts "baseLine" for backward compatibility.')
    length: Optional[float] = Field(None, description='管道长度')
    diameter: Optional[float] = Field(None, description='管道直径')
    flowrate: Optional[float] = Field(None, alias='flowRate', description='流量')
    relative_roughness: Optional[float] = Field(None, alias='relativeRoughness', description='相对粗糙度')
    slope: Optional[float] = Field(None, description='管道坡度（百分比%，正数表示向下，负数表示向上）')
    
    model_config = ConfigDict(populate_by_name=True)


class CableTray(SpeckleBuiltElementBase):
    """Speckle CableTray element
    
    电缆桥架元素，从 Speckle ICurve baseCurve 转换为 Geometry（3D 原生，桥架中心线）
    """
    geometry: Geometry = Field(..., alias='baseCurve', description='3D geometry (converted from ICurve baseCurve, cable tray centerline, coordinates: [[x, y, z], ...])')
    width: Optional[float] = Field(None, description='桥架宽度')
    height: Optional[float] = Field(None, description='桥架高度')
    length: Optional[float] = Field(None, description='桥架长度')
    
    model_config = ConfigDict(populate_by_name=True)


class Conduit(SpeckleBuiltElementBase):
    """Speckle Conduit element
    
    导管元素，从 Speckle ICurve baseCurve 转换为 Geometry（3D 原生，导管中心线）
    """
    geometry: Geometry = Field(..., alias='baseCurve', description='3D geometry (converted from ICurve baseCurve, conduit centerline, coordinates: [[x, y, z], ...])')
    diameter: Optional[float] = Field(None, description='导管直径')
    length: Optional[float] = Field(None, description='导管长度')
    
    model_config = ConfigDict(populate_by_name=True)


class Wire(SpeckleBuiltElementBase):
    """Speckle Wire element
    
    电线元素，使用 segments 列表表示电线的多段路径
    """
    segments: List[Geometry] = Field(..., description='电线路径段列表（每个段为一条 ICurve，3D 坐标）')
    cross_section_area: Optional[float] = Field(None, description='电缆截面积（平方毫米）')
    cable_type: Optional[Literal["电力电缆", "控制电缆"]] = Field(None, description='电缆类型')
    
    model_config = ConfigDict(populate_by_name=True)


class Hanger(SpeckleBuiltElementBase):
    """支吊架元素
    
    根据标准图集自动生成或手动创建
    """
    geometry: Geometry = Field(..., description="支吊架安装位置（点坐标）")
    hanger_type: Literal["支架", "吊架"] = Field(..., description="支吊架类型")
    standard_code: str = Field(..., description="标准图集编号（如：03s402, 08k132, 04D701-3）")
    detail_code: str = Field(..., description="详图编号（如：03s402-1, 08k132-A1）")
    
    # 支吊架参数
    load_capacity: Optional[float] = Field(None, description="承载能力（kg）")
    material: Optional[str] = Field(None, description="材质")
    seismic_grade: Optional[str] = Field(None, description="抗震等级")
    
    # 关联的MEP元素信息
    supported_element_type: str = Field(..., description="被支撑元素类型（Pipe, Duct, CableTray）")
    supported_element_id: Optional[str] = Field(None, description="被支撑元素ID（如果有）")
    support_interval: Optional[float] = Field(None, description="支撑间距（米）")
    
    model_config = ConfigDict(populate_by_name=True)


class IntegratedHanger(SpeckleBuiltElementBase):
    """综合支吊架元素
    
    为空间内的成排管线生成共用综合支吊架
    """
    geometry: Geometry = Field(..., description="综合支吊架安装位置（点坐标）")
    standard_code: str = Field(..., description="标准图集编号")
    detail_code: str = Field(..., description="详图编号")
    supported_element_ids: List[str] = Field(..., description="被支撑元素ID列表")
    space_id: str = Field(..., description="所属空间ID")
    hanger_type: Literal["支架", "吊架"] = Field(..., description="支吊架类型")
    seismic_grade: Optional[str] = Field(None, description="抗震等级")
    
    model_config = ConfigDict(populate_by_name=True)

