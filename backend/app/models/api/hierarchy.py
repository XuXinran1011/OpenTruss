"""层级结构 API 模型

用于层级结构查询 API 的请求和响应模型
"""

from typing import Optional, List, Literal, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from app.models.speckle.base import Geometry2D


class ProjectListItem(BaseModel):
    """项目列表项"""
    id: str = Field(..., description="项目 ID")
    name: str = Field(..., description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    building_count: Optional[int] = Field(0, description="单体数量")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "project_001",
            "name": "某住宅小区项目",
            "description": "某市住宅小区开发项目",
            "building_count": 3,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    })


class ProjectDetail(BaseModel):
    """项目详情"""
    id: str = Field(..., description="项目 ID")
    name: str = Field(..., description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    building_count: Optional[int] = Field(0, description="单体数量")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "project_001",
            "name": "某住宅小区项目",
            "description": "某市住宅小区开发项目",
            "building_count": 3,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    })


class HierarchyNode(BaseModel):
    """层级节点（用于层级树结构）"""
    id: str = Field(..., description="节点 ID")
    label: str = Field(..., description="节点标签（Project/Building/Division/SubDivision/Item/InspectionLot）")
    name: str = Field(..., description="节点名称")
    children: List["HierarchyNode"] = Field(default_factory=list, description="子节点列表")
    metadata: Optional[Dict[str, Any]] = Field(None, description="附加元数据")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "building_001",
            "label": "Building",
            "name": "1#楼",
            "children": [],
            "metadata": {"floor_count": 30}
        }
    })


# 支持递归类型
HierarchyNode.model_rebuild()


class HierarchyResponse(BaseModel):
    """层级树响应"""
    project_id: str = Field(..., description="项目 ID")
    project_name: str = Field(..., description="项目名称")
    hierarchy: HierarchyNode = Field(..., description="层级树根节点")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "project_id": "project_001",
            "project_name": "某住宅小区项目",
            "hierarchy": {
                "id": "project_001",
                "label": "Project",
                "name": "某住宅小区项目",
                "children": []
            }
        }
    })


class BuildingDetail(BaseModel):
    """单体详情"""
    id: str = Field(..., description="单体 ID")
    name: str = Field(..., description="单体名称")
    project_id: str = Field(..., description="所属项目 ID")
    description: Optional[str] = Field(None, description="描述")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "building_001",
            "name": "1#楼",
            "project_id": "project_001",
            "description": "主楼",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    })


class DivisionDetail(BaseModel):
    """分部详情"""
    id: str = Field(..., description="分部 ID")
    name: str = Field(..., description="分部名称")
    building_id: str = Field(..., description="所属单体 ID")
    description: Optional[str] = Field(None, description="描述")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "division_001",
            "name": "主体结构",
            "building_id": "building_001",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    })


class SubDivisionDetail(BaseModel):
    """子分部详情"""
    id: str = Field(..., description="子分部 ID")
    name: str = Field(..., description="子分部名称")
    division_id: str = Field(..., description="所属分部 ID")
    description: Optional[str] = Field(None, description="描述")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "subdivision_001",
            "name": "砌体结构",
            "division_id": "division_001",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    })


class ItemDetail(BaseModel):
    """分项详情"""
    id: str = Field(..., description="分项 ID")
    name: str = Field(..., description="分项名称")
    subdivision_id: str = Field(..., description="所属子分部 ID")
    description: Optional[str] = Field(None, description="描述")
    inspection_lot_count: Optional[int] = Field(0, description="检验批数量")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "item_001",
            "name": "填充墙砌体",
            "subdivision_id": "subdivision_001",
            "inspection_lot_count": 5,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    })


class InspectionLotDetail(BaseModel):
    """检验批详情"""
    id: str = Field(..., description="检验批 ID")
    name: str = Field(..., description="检验批名称")
    item_id: str = Field(..., description="所属分项 ID")
    spatial_scope: Optional[str] = Field(None, description="空间范围（如：Level:F1）")
    status: Literal["PLANNING", "IN_PROGRESS", "SUBMITTED", "APPROVED", "PUBLISHED"] = Field(
        ..., description="状态"
    )
    element_count: Optional[int] = Field(0, description="构件数量")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "lot_001",
            "name": "1#楼F1层填充墙砌体检验批",
            "item_id": "item_001",
            "spatial_scope": "Level:F1",
            "status": "IN_PROGRESS",
            "element_count": 25,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    })


