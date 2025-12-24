"""GB50300 节点模型定义

根据 docs/SCHEMA.md 定义的节点类型
"""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


class ProjectNode(BaseModel):
    """项目节点
    
    标签: :Project
    """
    id: str = Field(..., description="唯一标识符")
    name: str = Field(..., description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "project_001",
                "name": "某住宅小区项目",
                "description": "总建筑面积 10 万平方米"
            }
        }


class BuildingNode(BaseModel):
    """单体节点
    
    标签: :Building
    """
    id: str = Field(..., description="唯一标识符")
    name: str = Field(..., description="单体名称（如：1#楼）")
    project_id: str = Field(..., description="所属项目 ID")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "building_001",
                "name": "1#楼",
                "project_id": "project_001"
            }
        }


class DivisionNode(BaseModel):
    """分部节点
    
    标签: :Division
    """
    id: str = Field(..., description="唯一标识符")
    name: str = Field(..., description="分部名称（如：主体结构）")
    building_id: str = Field(..., description="所属单体 ID")
    description: Optional[str] = Field(None, description="分部描述")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "division_001",
                "name": "主体结构",
                "building_id": "building_001"
            }
        }


class SubDivisionNode(BaseModel):
    """子分部节点
    
    标签: :SubDivision
    """
    id: str = Field(..., description="唯一标识符")
    name: str = Field(..., description="子分部名称（如：砌体结构）")
    division_id: str = Field(..., description="所属分部 ID")
    description: Optional[str] = Field(None, description="子分部描述")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "subdivision_001",
                "name": "砌体结构",
                "division_id": "division_001"
            }
        }


class ItemNode(BaseModel):
    """分项节点
    
    标签: :Item
    """
    id: str = Field(..., description="唯一标识符")
    name: str = Field(..., description="分项名称（如：填充墙砌体）")
    subdivision_id: str = Field(..., description="所属子分部 ID")
    description: Optional[str] = Field(None, description="分项描述")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "item_001",
                "name": "填充墙砌体",
                "subdivision_id": "subdivision_001"
            }
        }


class InspectionLotNode(BaseModel):
    """检验批节点
    
    标签: :InspectionLot
    """
    id: str = Field(..., description="唯一标识符")
    name: str = Field(..., description="检验批名称")
    item_id: str = Field(..., description="所属分项 ID")
    spatial_scope: str = Field(..., description="空间范围（如：Level:F1）")
    status: Literal["PLANNING", "IN_PROGRESS", "SUBMITTED", "APPROVED", "PUBLISHED"] = Field(
        default="PLANNING",
        description="状态"
    )
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "lot_001",
                "name": "1#楼F1层填充墙砌体检验批",
                "item_id": "item_001",
                "spatial_scope": "Level:F1",
                "status": "PLANNING"
            }
        }


class ApprovalHistoryNode(BaseModel):
    """审批历史节点
    
    标签: :ApprovalHistory
    """
    id: str = Field(..., description="唯一标识符")
    lot_id: str = Field(..., description="关联的检验批 ID")
    action: Literal["APPROVE", "REJECT"] = Field(..., description="审批操作")
    user_id: str = Field(..., description="用户 ID")
    role: Literal["APPROVER", "PM"] = Field(..., description="用户角色")
    comment: Optional[str] = Field(None, description="审批意见或驳回原因")
    old_status: str = Field(..., description="原状态")
    new_status: str = Field(..., description="新状态")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "history_001",
                "lot_id": "lot_001",
                "action": "APPROVE",
                "user_id": "user_001",
                "role": "APPROVER",
                "comment": "验收通过",
                "old_status": "SUBMITTED",
                "new_status": "APPROVED"
            }
        }


class LevelNode(BaseModel):
    """楼层节点
    
    标签: :Level
    """
    id: str = Field(..., description="唯一标识符")
    name: str = Field(..., description="楼层名称（如：F1, B1）")
    building_id: str = Field(..., description="所属单体 ID")
    elevation: Optional[float] = Field(None, description="楼层标高（米）")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "level_f1",
                "name": "F1",
                "building_id": "building_001",
                "elevation": 0.0
            }
        }


class ZoneNode(BaseModel):
    """区域节点
    
    标签: :Zone
    """
    id: str = Field(..., description="唯一标识符")
    name: str = Field(..., description="区域名称（如：A区、B区）")
    building_id: str = Field(..., description="所属单体 ID")
    description: Optional[str] = Field(None, description="区域描述")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "zone_a",
                "name": "A区",
                "building_id": "building_001"
            }
        }


class SystemNode(BaseModel):
    """系统节点
    
    标签: :System
    """
    id: str = Field(..., description="唯一标识符")
    name: str = Field(..., description="系统名称（如：给排水系统）")
    building_id: str = Field(..., description="所属单体 ID")
    system_type: str = Field(..., description="系统类型（如：Plumbing, HVAC, Electrical）")
    description: Optional[str] = Field(None, description="系统描述")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "system_001",
                "name": "给排水系统",
                "building_id": "building_001",
                "system_type": "Plumbing"
            }
        }


class SubSystemNode(BaseModel):
    """子系统节点
    
    标签: :SubSystem
    """
    id: str = Field(..., description="唯一标识符")
    name: str = Field(..., description="子系统名称")
    system_id: str = Field(..., description="所属系统 ID")
    description: Optional[str] = Field(None, description="子系统描述")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "subsystem_001",
                "name": "给水子系统",
                "system_id": "system_001"
            }
        }
