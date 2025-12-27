"""数据校验模块

提供 Pydantic 自定义验证器和 IFC 约束校验
"""

from typing import Any, List, Tuple, Dict, Optional, TYPE_CHECKING
from pydantic import field_validator, model_validator, ValidationInfo
from decimal import Decimal
import logging
import json

from app.models.speckle.base import Geometry, Geometry2D, normalize_coordinates

if TYPE_CHECKING:
    from app.utils.memgraph import MemgraphClient

logger = logging.getLogger(__name__)


# IFC 标准约束
IFC_MIN_LENGTH = 0.01  # 最小长度（米）
IFC_MAX_LENGTH = 10000.0  # 最大长度（米）
IFC_MIN_HEIGHT = 0.01  # 最小高度（米）
IFC_MAX_HEIGHT = 1000.0  # 最大高度（米，用于 Walls/Columns 的拉伸距离）
IFC_MAX_CROSS_SECTION_DEPTH = 2.0  # 最大横截面深度（米，用于 Beams/Pipes）
IFC_MIN_ANGLE = 0.0  # 最小角度（度）
IFC_MAX_ANGLE = 360.0  # 最大角度（度）

# 构件类型分类（用于 height 验证）
EXTRUSION_ELEMENT_TYPES = {"Wall", "Column", "Floor", "Ceiling", "Roof"}  # height 表示拉伸距离
CROSS_SECTION_ELEMENT_TYPES = {"Beam", "Pipe", "Duct", "CableTray", "Conduit"}  # height 表示横截面深度

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
        """验证坐标数据（支持 2D 和 3D 输入）
        
        Args:
            coordinates: 坐标列表，可以是 2D [[x, y], ...] 或 3D [[x, y, z], ...]
            info: 验证上下文信息
            
        Returns:
            验证后的 3D 坐标列表 [[x, y, z], ...]（2D 输入自动补 z=0.0）
            
        Raises:
            ValueError: 坐标不符合要求
        """
        if not isinstance(coordinates, list):
            raise ValueError("坐标必须是列表")
        
        if len(coordinates) < 2:
            raise ValueError("坐标至少需要2个点")
        
        # 使用 normalize_coordinates 规范化坐标（2D→3D 转换）
        try:
            normalized = normalize_coordinates(coordinates)
        except ValueError as e:
            raise ValueError(f"坐标规范化失败: {e}")
        
        # 验证每个坐标点（现在应该是 3D）
        for i, point in enumerate(normalized):
            if not isinstance(point, (list, tuple)):
                raise ValueError(f"坐标点 {i} 必须是列表或元组")
            
            if len(point) != 3:
                raise ValueError(f"坐标点 {i} 必须包含3个值 (x, y, z)，got {len(point)}")
            
            x, y, z = point
            if (not isinstance(x, (int, float)) or 
                not isinstance(y, (int, float)) or 
                not isinstance(z, (int, float))):
                raise ValueError(f"坐标点 {i} 的值必须是数字")
            
            # 检查坐标范围（合理的建筑尺寸范围）
            if abs(x) > IFC_MAX_LENGTH or abs(y) > IFC_MAX_LENGTH:
                raise ValueError(f"坐标点 {i} 的 X 或 Y 超出允许范围 (最大 {IFC_MAX_LENGTH} 米)")
            
            # Z 坐标范围检查（允许负值，如地下室）
            if abs(z) > IFC_MAX_HEIGHT:
                raise ValueError(f"坐标点 {i} 的 Z 超出允许范围 (最大 {IFC_MAX_HEIGHT} 米)")
        
        return normalized
    
    @staticmethod
    def validate_polyline_closed(geometry: Geometry) -> Geometry:
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
            
            # 检查首尾点是否相同（3D 坐标比较）
            first = coords[0]
            last = coords[-1]
            # 确保是 3D 坐标进行比较（使用数值比较，避免浮点误差）
            if len(first) != 3 or len(last) != 3:
                raise ValueError("坐标点必须是 3D [x, y, z]")
            # 允许小的浮点误差
            if (abs(first[0] - last[0]) > 1e-6 or 
                abs(first[1] - last[1]) > 1e-6 or 
                abs(first[2] - last[2]) > 1e-6):
                raise ValueError("标记为闭合的 Polyline，首尾点必须相同（3D 坐标）")
        
        return geometry


class IFCConstraintValidator:
    """IFC 标准约束验证器"""
    
    @staticmethod
    def validate_height(height: float | None, info: ValidationInfo = None, speckle_type: str | None = None) -> float | None:
        """验证高度值是否符合 IFC 标准
        
        根据构件类型应用不同的验证逻辑：
        - Walls/Columns: height 表示拉伸距离，验证范围 0.01 - 1000.0 米
        - Beams/Pipes: height 表示横截面深度，验证范围 0.01 - 2.0 米
        
        Args:
            height: 高度值（米）
            info: 验证上下文信息（Pydantic ValidationInfo，可选）
            speckle_type: 构件类型（可选，如果提供则使用类型特定的验证规则）
            
        Returns:
            验证后的高度值
            
        Raises:
            ValueError: 高度不符合 IFC 标准
        """
        if height is None:
            return None
        
        if not isinstance(height, (int, float)):
            raise ValueError("高度必须是数字")
        
        # 尝试从 ValidationInfo 获取 speckle_type
        if speckle_type is None and info is not None:
            try:
                # 在 Pydantic v2 中，可以通过 info.data 访问父模型数据
                if hasattr(info, 'data') and info.data:
                    speckle_type = info.data.get('speckle_type')
            except (AttributeError, KeyError):
                pass
        
        # 根据构件类型确定最大高度
        if speckle_type and speckle_type in CROSS_SECTION_ELEMENT_TYPES:
            # Beams/Pipes: 横截面深度，通常不超过 2 米
            max_height = IFC_MAX_CROSS_SECTION_DEPTH
            height_meaning = "横截面深度"
        else:
            # Walls/Columns 等: 拉伸距离，可以使用较大的范围
            max_height = IFC_MAX_HEIGHT
            height_meaning = "拉伸距离" if (speckle_type and speckle_type in EXTRUSION_ELEMENT_TYPES) else "高度"
        
        if height < IFC_MIN_HEIGHT:
            raise ValueError(f"高度 {height} 小于最小允许值 {IFC_MIN_HEIGHT} 米")
        
        if height > max_height:
            raise ValueError(
                f"{height_meaning} {height} 超过最大允许值 {max_height} 米"
                f"（{speckle_type or '该构件类型'}）"
            )
        
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
    def validate_geometry_length(geometry: Geometry) -> Geometry:
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
        
        # 计算所有线段的总长度（3D 距离）
        total_length = 0.0
        for i in range(len(coords) - 1):
            p1 = coords[i]
            p2 = coords[i + 1]
            # 3D 距离计算
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            dz = p2[2] - p1[2] if len(p2) >= 3 else 0.0
            length = (dx ** 2 + dy ** 2 + dz ** 2) ** 0.5
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


class MEPRoutingValidator:
    """MEP 路径规划验证器"""
    
    @staticmethod
    def validate_mep_routing_path(
        path_points: List[List[float]],
        element_type: str,
        system_type: Optional[str] = None,
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """验证 MEP 路径是否符合约束
        
        Args:
            path_points: 路径点列表 [[x1, y1], [x2, y2], ...]
            element_type: 元素类型
            system_type: 系统类型
            constraints: 约束字典
        
        Returns:
            验证结果字典
        """
        errors = []
        warnings = []
        
        if not path_points or len(path_points) < 2:
            return {
                "valid": False,
                "errors": ["路径至少需要2个点"],
                "warnings": []
            }
        
        # 检查路径点是否有效
        for i, point in enumerate(path_points):
            if not isinstance(point, (list, tuple)) or len(point) < 2:
                errors.append(f"路径点 {i} 格式错误")
                continue
            
            x, y = point[0], point[1]
            if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
                errors.append(f"路径点 {i} 坐标必须是数字")
        
        if errors:
            return {
                "valid": False,
                "errors": errors,
                "warnings": warnings
            }
        
        # 检查角度约束（如果有）
        if constraints:
            allowed_angles = constraints.get("allowed_angles", [])
            forbidden_angles = constraints.get("forbidden_angles", [])
            
            # 检查路径中的转弯角度
            for i in range(1, len(path_points) - 1):
                p1 = (path_points[i - 1][0], path_points[i - 1][1])
                p2 = (path_points[i][0], path_points[i][1])
                p3 = (path_points[i + 1][0], path_points[i + 1][1])
                
                angle = MEPRoutingValidator._calculate_turn_angle(p1, p2, p3)
                
                # 检查是否在禁止的角度列表中
                for forbidden_angle in forbidden_angles:
                    if abs(angle - forbidden_angle) < 5:  # 5度容差
                        errors.append(
                            f"路径点 {i} 处的转弯角度 {angle:.1f}° 被禁止（系统类型: {system_type}）"
                        )
                
                # 检查是否在允许的角度列表中（如果有约束）
                if allowed_angles:
                    is_allowed = any(abs(angle - allowed_angle) < 5 for allowed_angle in allowed_angles)
                    if not is_allowed:
                        warnings.append(
                            f"路径点 {i} 处的转弯角度 {angle:.1f}° 不在允许的角度列表中"
                        )
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    @staticmethod
    def validate_bend_radius(
        path_points: List[List[float]],
        min_radius: float
    ) -> Dict[str, Any]:
        """验证转弯半径是否符合要求
        
        Args:
            path_points: 路径点列表
            min_radius: 最小转弯半径（米）
        
        Returns:
            验证结果
        """
        errors = []
        warnings = []
        
        if len(path_points) < 3:
            return {
                "valid": True,
                "errors": [],
                "warnings": []
            }
        
        # 简化验证：检查转弯点处的曲率
        for i in range(1, len(path_points) - 1):
            p1 = (path_points[i - 1][0], path_points[i - 1][1])
            p2 = (path_points[i][0], path_points[i][1])
            p3 = (path_points[i + 1][0], path_points[i + 1][1])
            
            # 计算三点形成的角度
            angle = MEPRoutingValidator._calculate_turn_angle(p1, p2, p3)
            
            # 如果角度接近90度，检查转弯半径
            if abs(angle - 90) < 5:
                # 计算实际转弯半径（简化：使用两点间距离的一半）
                dist1 = ((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2) ** 0.5
                dist2 = ((p3[0] - p2[0])**2 + (p3[1] - p2[1])**2) ** 0.5
                actual_radius = min(dist1, dist2) / 2
                
                if actual_radius < min_radius:
                    warnings.append(
                        f"路径点 {i} 处的转弯半径 {actual_radius:.3f}m 小于最小要求 {min_radius:.3f}m"
                    )
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    @staticmethod
    def validate_cable_tray_width(
        width: float,
        cable_bend_radius: float,
        min_width_ratio: float
    ) -> Dict[str, Any]:
        """验证电缆桥架宽度（确保电缆转弯半径可通过）
        
        Args:
            width: 桥架宽度（毫米）
            cable_bend_radius: 电缆转弯半径（毫米）
            min_width_ratio: 最小宽度比
        
        Returns:
            验证结果
        """
        errors = []
        warnings = []
        
        required_min_width = cable_bend_radius * min_width_ratio
        
        if width < required_min_width:
            errors.append(
                f"电缆桥架宽度 {width}mm 小于最小要求 {required_min_width:.1f}mm "
                f"（电缆转弯半径: {cable_bend_radius}mm, 宽度比: {min_width_ratio}）"
            )
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    @staticmethod
    def _calculate_turn_angle(
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        p3: Tuple[float, float]
    ) -> float:
        """计算转弯角度（度）"""
        import math
        
        # 向量1：从p1到p2
        v1 = (p2[0] - p1[0], p2[1] - p1[1])
        # 向量2：从p2到p3
        v2 = (p3[0] - p2[0], p3[1] - p2[1])
        
        # 计算角度
        angle1 = math.atan2(v1[1], v1[0])
        angle2 = math.atan2(v2[1], v2[0])
        
        # 计算角度差（转为度）
        angle_diff = math.degrees(angle2 - angle1)
        
        # 标准化到 [0, 360)
        if angle_diff < 0:
            angle_diff += 360
        
        # 转换为内角（0-180度）
        if angle_diff > 180:
            angle_diff = 360 - angle_diff
        
        return angle_diff


class TopologyValidator:
    """拓扑校验器（规则引擎 Phase 4）
    
    确保系统逻辑闭环：无悬空端点、无孤立子图
    """
    
    def __init__(self, client):
        """初始化拓扑校验器
        
        Args:
            client: MemgraphClient 实例
        """
        self.client = client
    
    def validate_topology(self, lot_id: str) -> Dict[str, Any]:
        """验证检验批的拓扑完整性
        
        Args:
            lot_id: 检验批 ID
        
        Returns:
            {
                "valid": bool,
                "open_ends": List[str],  # 悬空端点元素ID列表
                "isolated_elements": List[str],  # 孤立元素ID列表
                "errors": List[str]
            }
        """
        errors = []
        open_ends = []
        isolated_elements = []
        
        # 1. 获取检验批内的所有元素
        elements_query = """
        MATCH (lot:InspectionLot {id: $lot_id})-[:MANAGEMENT_CONTAINS]->(e:Element)
        RETURN e.id as element_id
        """
        elements_result = self.client.execute_query(elements_query, {"lot_id": lot_id})
        
        if not elements_result:
            # 检验批不存在或没有元素
            return {
                "valid": True,
                "open_ends": [],
                "isolated_elements": [],
                "errors": []
            }
        
        element_ids = [row["element_id"] for row in elements_result]
        
        # 2. 查找悬空端点和孤立元素
        open_ends = self.find_open_ends(element_ids)
        isolated_elements = self.find_isolated_elements(element_ids)
        
        # 3. 生成错误信息
        if open_ends:
            errors.append(f"发现 {len(open_ends)} 个悬空端点")
        
        if isolated_elements:
            errors.append(f"发现 {len(isolated_elements)} 个孤立元素")
        
        valid = len(open_ends) == 0 and len(isolated_elements) == 0
        
        return {
            "valid": valid,
            "open_ends": open_ends,
            "isolated_elements": isolated_elements,
            "errors": errors
        }
    
    def find_open_ends(self, element_ids: List[str]) -> List[str]:
        """查找悬空端点（连接数 < 2 的元素）
        
        悬空端点是指连接数少于2的元素（即只有0个或1个连接）
        对于闭合的拓扑系统，每个元素应该至少有2个连接（起点和终点除外）
        但为了通用性，我们定义悬空端点为连接数 < 2 的元素
        
        Args:
            element_ids: 元素ID列表
        
        Returns:
            悬空端点元素ID列表
        """
        if not element_ids:
            return []
        
        # 查询每个元素的连接数（双向连接）
        # CONNECTED_TO 关系是双向的，我们需要统计所有连接到该元素的关系
        query = """
        MATCH (e:Element)
        WHERE e.id IN $element_ids
        OPTIONAL MATCH (e)-[r1:CONNECTED_TO]-(other:Element)
        WHERE other.id IN $element_ids
        WITH e, count(DISTINCT r1) as connection_count
        WHERE connection_count < 2
        RETURN e.id as element_id, connection_count
        """
        
        result = self.client.execute_query(query, {"element_ids": element_ids})
        open_ends = [row["element_id"] for row in result]
        
        return open_ends
    
    def find_isolated_elements(self, element_ids: List[str]) -> List[str]:
        """查找孤立元素（没有任何连接的元素）
        
        Args:
            element_ids: 元素ID列表
        
        Returns:
            孤立元素ID列表
        """
        if not element_ids:
            return []
        
        # 查询没有任何连接的元素
        query = """
        MATCH (e:Element)
        WHERE e.id IN $element_ids
        OPTIONAL MATCH (e)-[r:CONNECTED_TO]-(other:Element)
        WHERE other.id IN $element_ids
        WITH e, count(r) as connection_count
        WHERE connection_count = 0
        RETURN e.id as element_id
        """
        
        result = self.client.execute_query(query, {"element_ids": element_ids})
        isolated = [row["element_id"] for row in result]
        
        return isolated


class ConstructabilityValidator:
    """构造校验器（规则引擎 Phase 2）
    
    实现角度吸附和Z轴完整性检查
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化构造校验器
        
        Args:
            config_path: 配置文件路径（如果为None，使用默认路径）
        """
        import json
        from pathlib import Path
        
        if config_path is None:
            # 默认配置文件路径
            config_path = Path(__file__).parent.parent / "config" / "rules" / "fitting_standards.json"
        else:
            config_path = Path(config_path)
        
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        import json
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except FileNotFoundError:
            # 如果配置文件不存在，使用默认配置
            logger.warning(f"配置文件不存在: {self.config_path}，使用默认配置")
            return {
                "version": "1.0",
                "angles": {
                    "standard": [45, 90, 180],
                    "tolerance": 5,
                    "allow_custom": False
                },
                "z_axis": {
                    "require_height": True,
                    "require_base_offset": True,
                    "element_types": ["Wall", "Column"]
                }
            }
        except json.JSONDecodeError as e:
            logger.error(f"配置文件解析失败: {e}，使用默认配置")
            return {
                "version": "1.0",
                "angles": {
                    "standard": [45, 90, 180],
                    "tolerance": 5,
                    "allow_custom": False
                },
                "z_axis": {
                    "require_height": True,
                    "require_base_offset": True,
                    "element_types": ["Wall", "Column"]
                }
            }
    
    def validate_angle(self, angle: float) -> Dict[str, Any]:
        """验证角度是否符合标准（45°, 90°, 180°）
        
        Args:
            angle: 角度值（度）
        
        Returns:
            {
                "valid": bool,
                "snapped_angle": Optional[float],  # 吸附后的角度
                "error": Optional[str]
            }
        """
        angle_config = self.config.get("angles", {})
        standard_angles = angle_config.get("standard", [45, 90, 180])
        tolerance = angle_config.get("tolerance", 5)
        allow_custom = angle_config.get("allow_custom", False)
        
        # 标准化角度到 [0, 180] 范围
        normalized_angle = angle % 360
        if normalized_angle > 180:
            normalized_angle = 360 - normalized_angle
        
        # 查找最接近的标准角度
        snapped_angle = self.snap_angle(angle)
        
        if snapped_angle is None:
            # 无法吸附到标准角度
            if allow_custom:
                # 允许自定义角度
                return {
                    "valid": True,
                    "snapped_angle": normalized_angle,
                    "error": None
                }
            else:
                return {
                    "valid": False,
                    "snapped_angle": None,
                    "error": f"角度 {angle:.1f}° 不在标准角度列表中 {standard_angles}，且不允许自定义角度"
                }
        else:
            # 成功吸附到标准角度
            diff = abs(normalized_angle - snapped_angle)
            if diff <= tolerance:
                return {
                    "valid": True,
                    "snapped_angle": snapped_angle,
                    "error": None
                }
            else:
                return {
                    "valid": False,
                    "snapped_angle": snapped_angle,
                    "error": f"角度 {angle:.1f}° 与标准角度 {snapped_angle}° 的差距 {diff:.1f}° 超过容差 {tolerance}°"
                }
    
    def snap_angle(self, angle: float) -> Optional[float]:
        """角度吸附到最近的标准角度
        
        Args:
            angle: 角度值（度）
        
        Returns:
            吸附后的角度，如果无法吸附则返回 None
        """
        angle_config = self.config.get("angles", {})
        standard_angles = angle_config.get("standard", [45, 90, 180])
        tolerance = angle_config.get("tolerance", 5)
        
        # 标准化角度到 [0, 180] 范围
        normalized_angle = angle % 360
        if normalized_angle > 180:
            normalized_angle = 360 - normalized_angle
        
        # 查找最接近的标准角度
        min_diff = float('inf')
        closest_angle = None
        
        for std_angle in standard_angles:
            diff = abs(normalized_angle - std_angle)
            if diff < min_diff:
                min_diff = diff
                closest_angle = std_angle
        
        # 如果最接近的角度在容差范围内，返回该角度
        if closest_angle is not None and min_diff <= tolerance:
            return closest_angle
        
        return None
    
    def validate_z_axis_completeness(self, element: Dict[str, Any]) -> Dict[str, Any]:
        """验证Z轴完整性（height, base_offset是否都存在）
        
        Args:
            element: 元素字典，包含 speckle_type, height, base_offset 等字段
        
        Returns:
            {
                "valid": bool,
                "errors": List[str],
                "warnings": List[str]
            }
        """
        errors = []
        warnings = []
        
        z_axis_config = self.config.get("z_axis", {})
        require_height = z_axis_config.get("require_height", True)
        require_base_offset = z_axis_config.get("require_base_offset", True)
        element_types = z_axis_config.get("element_types", ["Wall", "Column"])
        
        element_type = element.get("speckle_type", "")
        
        # 只检查配置中指定的元素类型
        if element_type not in element_types:
            return {
                "valid": True,
                "errors": [],
                "warnings": []
            }
        
        # 检查 height
        height = element.get("height")
        if require_height and (height is None or height == ""):
            errors.append(f"元素 {element.get('id', 'unknown')} ({element_type}) 缺少必需的 height 属性")
        
        # 检查 base_offset
        base_offset = element.get("base_offset")
        if require_base_offset and (base_offset is None or base_offset == ""):
            errors.append(f"元素 {element.get('id', 'unknown')} ({element_type}) 缺少必需的 base_offset 属性")
        
        # 如果 height 或 base_offset 存在但另一个缺失，给出警告
        if height is not None and base_offset is None:
            warnings.append(f"元素 {element.get('id', 'unknown')} ({element_type}) 有 height 但没有 base_offset，可能影响3D显示")
        elif base_offset is not None and height is None:
            warnings.append(f"元素 {element.get('id', 'unknown')} ({element_type}) 有 base_offset 但没有 height，可能影响3D显示")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def calculate_path_angle(self, path: List[List[float]]) -> float:
        """计算路径角度
        
        Args:
            path: 路径点列表 [[x1, y1], [x2, y2], ...]
        
        Returns:
            角度（度）
        """
        import math
        
        if len(path) < 2:
            return 0.0
        
        start = path[0]
        end = path[-1]
        
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        
        # 计算角度（0-360度）
        angle = math.atan2(dy, dx) * (180 / math.pi)
        if angle < 0:
            angle += 360
        
        # 转换为 0-180 度范围（因为 180° 和 360° 等价）
        if angle > 180:
            angle -= 180
        
        return angle


class SpatialValidator:
    """空间校验器（规则引擎 Phase 3）
    
    实现物理碰撞检测功能，使用 2.5D 包围盒（AABB）算法
    """
    
    def __init__(self, client):
        """初始化空间校验器
        
        Args:
            client: MemgraphClient 实例
        """
        self.client = client
    
    def calculate_bounding_box(self, element: Dict[str, Any]) -> Optional[Dict[str, float]]:
        """从 Element 节点数据计算 3D 包围盒
        
        Args:
            element: Element 节点数据字典
        
        Returns:
            3D 包围盒字典，如果无法计算则返回 None
            {
                "minX": float,
                "minY": float,
                "minZ": float,
                "maxX": float,
                "maxY": float,
                "maxZ": float
            }
        """
        # 解析 geometry（3D 原生）
        geometry_data = element.get("geometry")
        if isinstance(geometry_data, str):
            try:
                geometry_data = json.loads(geometry_data)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse geometry JSON for element {element.get('id')}")
                return None
        
        if not geometry_data or not isinstance(geometry_data, dict):
            return None
        
        coordinates = geometry_data.get("coordinates")
        if not coordinates or len(coordinates) < 2:
            return None
        
        # 计算 2D 包围盒
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')
        
        for coord in coordinates:
            if len(coord) >= 2:
                x = float(coord[0]) if coord[0] is not None else 0.0
                y = float(coord[1]) if coord[1] is not None else 0.0
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
        
        if not (isinstance(min_x, (int, float)) and isinstance(min_y, (int, float)) and
                isinstance(max_x, (int, float)) and isinstance(max_y, (int, float))):
            return None
        
        # 获取 Z 轴信息
        height = element.get("height")
        base_offset = element.get("base_offset")
        
        height = float(height) if height is not None else 0.0
        base_offset = float(base_offset) if base_offset is not None else 0.0
        
        return {
            "minX": min_x,
            "minY": min_y,
            "minZ": base_offset,
            "maxX": max_x,
            "maxY": max_y,
            "maxZ": base_offset + height,
        }
    
    def boxes_overlap(self, box1: Dict[str, float], box2: Dict[str, float]) -> bool:
        """检查两个 3D 包围盒是否重叠
        
        两个 Box 重叠 ⟺ X轴重叠 && Y轴重叠 && Z轴重叠
        
        Args:
            box1: 第一个包围盒
            box2: 第二个包围盒
        
        Returns:
            是否重叠
        """
        # X 轴重叠
        x_overlap = box1["maxX"] >= box2["minX"] and box1["minX"] <= box2["maxX"]
        
        # Y 轴重叠
        y_overlap = box1["maxY"] >= box2["minY"] and box1["minY"] <= box2["maxY"]
        
        # Z 轴重叠
        z_overlap = box1["maxZ"] >= box2["minZ"] and box1["minZ"] <= box2["maxZ"]
        
        return x_overlap and y_overlap and z_overlap
    
    def validate_collisions(self, element_ids: List[str]) -> Dict[str, Any]:
        """检查指定元素列表中的碰撞
        
        Args:
            element_ids: 元素ID列表
        
        Returns:
            {
                "valid": bool,  # 是否有碰撞
                "collisions": List[Dict[str, str]],  # 碰撞的构件对列表
                "errors": List[str]  # 错误信息列表
            }
        """
        if not element_ids:
            return {
                "valid": True,
                "collisions": [],
                "errors": []
            }
        
        # 获取所有元素的完整数据
        elements_query = """
        MATCH (e:Element)
        WHERE e.id IN $element_ids
        RETURN e.id as id, e.geometry as geometry, e.height as height, e.base_offset as base_offset
        """
        elements_result = self.client.execute_query(elements_query, {"element_ids": element_ids})
        
        if not elements_result:
            return {
                "valid": True,
                "collisions": [],
                "errors": []
            }
        
        # 计算所有元素的包围盒
        element_boxes: Dict[str, Dict[str, float]] = {}
        for row in elements_result:
            element_id = row.get("id")
            if not element_id:
                continue
            
            element_dict = {
                "id": element_id,
                "geometry": row.get("geometry"),
                "height": row.get("height"),
                "base_offset": row.get("base_offset"),
            }
            
            bbox = self.calculate_bounding_box(element_dict)
            if bbox:
                element_boxes[element_id] = bbox
        
        # 检查所有元素对之间的碰撞
        collisions: List[Dict[str, str]] = []
        element_id_list = list(element_boxes.keys())
        
        for i in range(len(element_id_list)):
            element_id1 = element_id_list[i]
            box1 = element_boxes[element_id1]
            
            for j in range(i + 1, len(element_id_list)):
                element_id2 = element_id_list[j]
                box2 = element_boxes[element_id2]
                
                if self.boxes_overlap(box1, box2):
                    collisions.append({
                        "element_id_1": element_id1,
                        "element_id_2": element_id2,
                    })
        
        errors = []
        if collisions:
            errors.append(f"发现 {len(collisions)} 个碰撞")
        
        return {
            "valid": len(collisions) == 0,
            "collisions": collisions,
            "errors": errors,
        }

