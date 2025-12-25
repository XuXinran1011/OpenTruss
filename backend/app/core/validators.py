"""数据校验模块

提供 Pydantic 自定义验证器和 IFC 约束校验
"""

from typing import Any
from pydantic import field_validator, model_validator, ValidationInfo
from decimal import Decimal

from app.models.speckle.base import Geometry2D, SpeckleBuiltElementBase


# IFC 标准约束
IFC_MIN_LENGTH = 0.01  # 最小长度（米）
IFC_MAX_LENGTH = 10000.0  # 最大长度（米）
IFC_MIN_HEIGHT = 0.01  # 最小高度（米）
IFC_MAX_HEIGHT = 1000.0  # 最大高度（米）
IFC_MIN_ANGLE = 0.0  # 最小角度（度）
IFC_MAX_ANGLE = 360.0  # 最大角度（度）

# 允许的构件类型（根据 IFC 标准）
ALLOWED_SPECKLE_TYPES = {
    # 建筑元素
    "Wall", "Floor", "Ceiling", "Roof", "Column",
    # 结构元素
    "Beam", "Brace", "Structure", "Rebar",
    # MEP 元素
    "Duct", "Pipe", "CableTray", "Conduit", "Wire",
    # 空间元素
    "Level", "Room", "Space", "Zone", "Area",
    # 其他元素
    "Opening", "Topography", "GridLine", "Profile", "Network",
    "View", "Alignment", "Baseline", "Featureline", "Station"
}


class GeometryValidator:
    """几何数据验证器"""
    
    @staticmethod
    def validate_coordinates(coordinates: list, info: ValidationInfo) -> list:
        """验证坐标数据
        
        Args:
            coordinates: 坐标列表
            info: 验证上下文信息
            
        Returns:
            验证后的坐标列表
            
        Raises:
            ValueError: 坐标不符合要求
        """
        if not isinstance(coordinates, list):
            raise ValueError("坐标必须是列表")
        
        if len(coordinates) < 2:
            raise ValueError("坐标至少需要2个点")
        
        # 验证每个坐标点
        for i, point in enumerate(coordinates):
            if not isinstance(point, (list, tuple)):
                raise ValueError(f"坐标点 {i} 必须是列表或元组")
            
            if len(point) != 2:
                raise ValueError(f"坐标点 {i} 必须包含2个值 (x, y)")
            
            x, y = point
            if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
                raise ValueError(f"坐标点 {i} 的值必须是数字")
            
            # 检查坐标范围（合理的建筑尺寸范围）
            if abs(x) > IFC_MAX_LENGTH or abs(y) > IFC_MAX_LENGTH:
                raise ValueError(f"坐标点 {i} 超出允许范围 (最大 {IFC_MAX_LENGTH} 米)")
        
        return coordinates
    
    @staticmethod
    def validate_polyline_closed(geometry: Geometry2D) -> Geometry2D:
        """验证 Polyline 是否闭合
        
        Args:
            geometry: 几何对象
            
        Returns:
            验证后的几何对象
            
        Raises:
            ValueError: Polyline 未闭合但标记为闭合
        """
        if geometry.type == "Polyline" and geometry.closed:
            coords = geometry.coordinates
            if len(coords) < 3:
                raise ValueError("闭合的 Polyline 至少需要3个点")
            
            # 检查首尾点是否相同
            first = coords[0]
            last = coords[-1]
            if first != last:
                raise ValueError("标记为闭合的 Polyline，首尾点必须相同")
        
        return geometry


class IFCConstraintValidator:
    """IFC 标准约束验证器"""
    
    @staticmethod
    def validate_height(height: float | None, info: ValidationInfo) -> float | None:
        """验证高度值是否符合 IFC 标准
        
        Args:
            height: 高度值（米）
            info: 验证上下文信息
            
        Returns:
            验证后的高度值
            
        Raises:
            ValueError: 高度不符合 IFC 标准
        """
        if height is None:
            return None
        
        if not isinstance(height, (int, float)):
            raise ValueError("高度必须是数字")
        
        if height < IFC_MIN_HEIGHT:
            raise ValueError(f"高度 {height} 小于最小允许值 {IFC_MIN_HEIGHT} 米")
        
        if height > IFC_MAX_HEIGHT:
            raise ValueError(f"高度 {height} 超过最大允许值 {IFC_MAX_HEIGHT} 米")
        
        return float(height)
    
    @staticmethod
    def validate_base_offset(offset: float | None, info: ValidationInfo) -> float | None:
        """验证基础偏移值
        
        Args:
            offset: 偏移值（米）
            info: 验证上下文信息
            
        Returns:
            验证后的偏移值
        """
        if offset is None:
            return None
        
        if not isinstance(offset, (int, float)):
            raise ValueError("基础偏移必须是数字")
        
        # 允许负偏移（如地下室）
        if abs(offset) > IFC_MAX_HEIGHT:
            raise ValueError(f"基础偏移 {offset} 超出允许范围")
        
        return float(offset)
    
    @staticmethod
    def validate_speckle_type(speckle_type: str, info: ValidationInfo) -> str:
        """验证 Speckle 类型是否符合允许的类型列表
        
        Args:
            speckle_type: Speckle 类型字符串
            info: 验证上下文信息
            
        Returns:
            验证后的类型字符串
            
        Raises:
            ValueError: 类型不在允许列表中
        """
        if not isinstance(speckle_type, str):
            raise ValueError("Speckle 类型必须是字符串")
        
        if speckle_type not in ALLOWED_SPECKLE_TYPES:
            raise ValueError(
                f"不支持的 Speckle 类型: {speckle_type}. "
                f"允许的类型: {', '.join(sorted(ALLOWED_SPECKLE_TYPES))}"
            )
        
        return speckle_type
    
    @staticmethod
    def validate_geometry_length(geometry: Geometry2D) -> Geometry2D:
        """验证几何图形的尺寸是否符合 IFC 标准
        
        Args:
            geometry: 几何对象
            
        Returns:
            验证后的几何对象
            
        Raises:
            ValueError: 几何尺寸不符合要求
        """
        coords = geometry.coordinates
        if len(coords) < 2:
            return geometry
        
        # 计算所有线段的总长度
        total_length = 0.0
        for i in range(len(coords) - 1):
            p1 = coords[i]
            p2 = coords[i + 1]
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            length = (dx ** 2 + dy ** 2) ** 0.5
            total_length += length
        
        # 检查总长度
        if total_length < IFC_MIN_LENGTH:
            raise ValueError(
                f"几何图形总长度 {total_length:.4f} 米小于最小允许值 {IFC_MIN_LENGTH} 米"
            )
        
        if total_length > IFC_MAX_LENGTH:
            raise ValueError(
                f"几何图形总长度 {total_length:.4f} 米超过最大允许值 {IFC_MAX_LENGTH} 米"
            )
        
        return geometry


class GB50300Validator:
    """GB50300 标准验证器"""
    
    @staticmethod
    def validate_item_id(item_id: str | None, info: ValidationInfo) -> str | None:
        """验证分项 ID 格式
        
        Args:
            item_id: 分项 ID
            info: 验证上下文信息
            
        Returns:
            验证后的分项 ID
        """
        if item_id is None:
            return None
        
        if not isinstance(item_id, str):
            raise ValueError("分项 ID 必须是字符串")
        
        if not item_id.strip():
            raise ValueError("分项 ID 不能为空")
        
        # GB50300 分项 ID 通常以 'item_' 开头
        if not item_id.startswith("item_") and item_id != "UNASSIGNED_ITEM_ID":
            raise ValueError("分项 ID 格式不正确，应以 'item_' 开头")
        
        return item_id
    
    @staticmethod
    def validate_inspection_lot_id(lot_id: str | None, info: ValidationInfo) -> str | None:
        """验证检验批 ID 格式
        
        Args:
            lot_id: 检验批 ID
            info: 验证上下文信息
            
        Returns:
            验证后的检验批 ID
        """
        if lot_id is None:
            return None
        
        if not isinstance(lot_id, str):
            raise ValueError("检验批 ID 必须是字符串")
        
        if not lot_id.strip():
            raise ValueError("检验批 ID 不能为空")
        
        # 检验批 ID 通常以 'lot_' 开头
        if not lot_id.startswith("lot_"):
            raise ValueError("检验批 ID 格式不正确，应以 'lot_' 开头")
        
        return lot_id


def create_element_validator(cls: type) -> type:
    """为 Element 模型创建验证器装饰器
    
    这个函数可以用于在 Element 模型类上添加验证器
    
    Usage:
        @create_element_validator
        class ElementUpdateRequest(BaseModel):
            ...
    """
    # 这里返回原始类，实际验证器应该通过 field_validator 或 model_validator 添加
    return cls

