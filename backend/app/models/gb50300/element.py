"""Element 节点模型

从 Speckle BuiltElement 转换而来的 OpenTruss Element 节点
"""

from datetime import datetime
from typing import Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

from app.models.speckle.base import Geometry2D


class ElementNode(BaseModel):
    """构件节点
    
    标签: :Element
    
    从 Speckle BuiltElement 转换而来的 OpenTruss Element
    """
    id: str = Field(..., description="唯一标识符")
    speckle_id: Optional[str] = Field(None, description="Speckle 原始对象 ID，用于追溯")
    speckle_type: str = Field(..., description="构件类型（如：Wall、Column）")
    geometry_2d: Geometry2D = Field(..., description="2D 几何数据（Line/Polyline）")
    
    # 3D Lift 参数（可选，在 Draft 状态下可以为空）
    height: Optional[float] = Field(None, description="高度（3D Lift 参数）")
    base_offset: Optional[float] = Field(None, description="基础偏移（3D Lift 参数）")
    material: Optional[str] = Field(None, description="材质")
    
    # 归属关系
    level_id: str = Field(..., description="所属楼层 ID")
    zone_id: Optional[str] = Field(None, description="所属区域 ID")
    inspection_lot_id: Optional[str] = Field(None, description="所属检验批 ID")
    
    # MEP 系统类型（可选）
    mep_system_type: Optional[str] = Field(
        None,
        description="MEP 系统类型（如：gravity_drainage, pressure_water, power_cable）"
    )
    
    # 状态和元数据
    status: Literal["Draft", "Verified"] = Field(default="Draft", description="状态")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="AI 识别置信度（0-1）")
    locked: bool = Field(default=False, description="是否锁定")
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "element_001",
                "speckle_id": "speckle_wall_001",
                "speckle_type": "Wall",
                "geometry_2d": {
                    "type": "Polyline",
                    "coordinates": [[0, 0], [10, 0], [10, 5], [0, 5], [0, 0]],
                    "closed": True
                },
                "height": 3.0,
                "base_offset": 0.0,
                "material": "concrete",
                "level_id": "level_f1",
                "status": "Draft",
                "confidence": 0.85
            }
        }
    )
    
    def to_cypher_properties(self) -> Dict[str, Any]:
        """转换为 Cypher 查询可用的属性字典
        
        Returns:
            Dict: 节点属性字典
        """
        # Pydantic v2 使用 model_dump，v1 使用 dict
        try:
            props = self.model_dump(exclude_none=True)
        except AttributeError:
            # Pydantic v1 兼容
            props = self.dict(exclude_none=True)
        
        # 将 geometry_2d 对象转换为字典（如果还不是字典）
        geometry = props.get("geometry_2d")
        if geometry and hasattr(geometry, "model_dump"):
            props["geometry_2d"] = geometry.model_dump()
        elif geometry and hasattr(geometry, "dict"):
            # Pydantic v1 兼容
            props["geometry_2d"] = geometry.dict()
        
        # datetime 对象在 Memgraph 中会自动处理
        # 保留为 datetime 对象，Memgraph 驱动会自动转换
        
        return props

