"""支吊架 API 模型

用于支吊架生成和查询 API 的请求和响应模型
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class GenerateHangersRequest(BaseModel):
    """生成支吊架请求"""
    element_ids: List[str] = Field(..., description="元素ID列表")
    seismic_grade: Optional[str] = Field(None, description="抗震等级（6度、7度、8度、9度）")
    create_nodes: bool = Field(default=True, description="是否在数据库中创建节点")


class GenerateIntegratedHangersRequest(BaseModel):
    """生成综合支吊架请求"""
    space_id: str = Field(..., description="空间ID")
    element_ids: List[str] = Field(..., description="要生成综合支吊架的元素ID列表")
    seismic_grade: Optional[str] = Field(None, description="抗震等级（6度、7度、8度、9度）")
    create_nodes: bool = Field(default=True, description="是否在数据库中创建节点")


class HangerInfo(BaseModel):
    """支吊架信息"""
    id: str = Field(..., description="支吊架元素ID")
    position: List[float] = Field(..., description="位置坐标 [x, y, z]")
    hanger_type: str = Field(..., description="支吊架类型（支架或吊架）")
    standard_code: str = Field(..., description="标准图集编号")
    detail_code: str = Field(..., description="详图编号")
    support_interval: Optional[float] = Field(None, description="支撑间距（米）")


class IntegratedHangerInfo(BaseModel):
    """综合支吊架信息"""
    id: str = Field(..., description="综合支吊架元素ID")
    position: List[float] = Field(..., description="位置坐标 [x, y, z]")
    hanger_type: str = Field(..., description="支吊架类型（支架或吊架）")
    standard_code: str = Field(..., description="标准图集编号")
    detail_code: str = Field(..., description="详图编号")
    supported_element_ids: List[str] = Field(..., description="被支撑元素ID列表")
    space_id: str = Field(..., description="所属空间ID")


class GenerateHangersResponse(BaseModel):
    """生成支吊架响应"""
    element_id: str = Field(..., description="元素ID")
    hanger_count: int = Field(..., description="生成的支吊架数量")
    hangers: List[HangerInfo] = Field(..., description="支吊架列表")


class GenerateIntegratedHangersResponse(BaseModel):
    """生成综合支吊架响应"""
    space_id: str = Field(..., description="空间ID")
    hanger_count: int = Field(..., description="生成的综合支吊架数量")
    hangers: List[IntegratedHangerInfo] = Field(..., description="综合支吊架列表")


class ElementHangersResponse(BaseModel):
    """元素的支吊架列表响应"""
    element_id: str = Field(..., description="元素ID")
    hangers: List[HangerInfo] = Field(..., description="支吊架列表")
    integrated_hanger: Optional[IntegratedHangerInfo] = Field(None, description="综合支吊架（如果有）")
