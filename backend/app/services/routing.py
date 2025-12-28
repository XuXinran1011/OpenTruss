"""MEP 路径规划服务

轻量级路径规划服务，支持不同 MEP 系统类型的特定约束
只返回路径点，不生成具体配件
"""

import logging
import math
from typing import Any, Dict, List, Optional, Tuple

from app.core.brick_validator import get_brick_validator
from app.core.exceptions import RoutingServiceError
from app.core.mep_routing_config import get_mep_routing_config
from app.models.speckle.base import Geometry
from app.services.spatial import SpatialService
from app.utils.memgraph import MemgraphClient

logger = logging.getLogger(__name__)


class FlexibleRouter:
    """灵活的 MEP 路径规划器（支持系统特定约束）
    
    该类提供轻量级的 MEP 路径规划功能，支持不同系统类型的特定约束（如重力排水系统的双45°弯头模式）。
    只返回路径点，不生成具体配件信息。
    
    主要功能：
    - 支持多种 MEP 元素类型：管道（Pipe）、风管（Duct）、电缆桥架（CableTray）、导管（Conduit）、线缆（Wire）
    - 支持系统特定约束配置（转弯半径、允许角度、禁止角度等）
    - Brick Schema 语义验证
    - Room 和 Space 空间约束验证
    - 坡度约束验证（用于重力流管道）
    
    使用示例：
        ```python
        router = FlexibleRouter()
        result = router.route(
            start=(0.0, 0.0),
            end=(10.0, 10.0),
            element_type="Pipe",
            element_properties={"diameter": 100},
            system_type="gravity_drainage",
            validate_semantic=True,
            validate_room_constraints=True,
            validate_slope=True
        )
        ```
    
    Attributes:
        config_loader: MEP路由配置加载器
        brick_validator: Brick Schema验证器
        spatial_service: 空间查询服务
    """
    
    def __init__(self, spatial_service: Optional[SpatialService] = None, client: Optional[MemgraphClient] = None):
        """初始化路径规划器
        
        Args:
            spatial_service: 空间查询服务实例（可选，如果为None则创建新实例）
            client: Memgraph客户端实例（可选，如果为None则创建新实例）
        """
        self.config_loader = get_mep_routing_config()
        self.brick_validator = get_brick_validator()
        self.spatial_service = spatial_service or SpatialService()
        self.client = client or MemgraphClient()
    
    def route(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        element_type: str,  # "Pipe", "Duct", "CableTray", "Wire"
        element_properties: Dict[str, Any],  # diameter, width, height 等
        system_type: Optional[str] = None,  # "gravity_drainage", "pressure_water" 等
        obstacles: Optional[List[Geometry]] = None,
        validate_semantic: bool = True,
        source_element_type: Optional[str] = None,
        target_element_type: Optional[str] = None,
        element_id: Optional[str] = None,  # 元素ID（用于获取原始路由Room列表）
        level_id: Optional[str] = None,  # 楼层ID（用于查询Space）
        validate_room_constraints: bool = True,  # 是否验证Room约束
        validate_slope: bool = True  # 是否验证坡度约束
    ) -> Dict[str, Any]:
        """
        计算符合约束的路径
        
        Args:
            start: 起点坐标 (x, y)
            end: 终点坐标 (x, y)
            element_type: 元素类型（Pipe, Duct, CableTray, Wire）
            element_properties: 元素属性字典（diameter, width, height 等，单位：毫米）
            system_type: 系统类型（gravity_drainage, pressure_water 等）
            obstacles: 障碍物列表（可选）
            validate_semantic: 是否进行Brick Schema语义验证
            source_element_type: 源元素类型（用于语义验证）
            target_element_type: 目标元素类型（用于语义验证）
        
        Returns:
            {
                "path_points": List[Tuple[float, float]],  # 路径点列表
                "constraints": Dict,  # 约束信息（转弯半径、宽度等）
                "warnings": List[str],  # 警告信息
                "errors": List[str]  # 错误信息
            }
        """
        # 参数验证
        if not start or not end:
            raise RoutingServiceError("起点和终点不能为空")
        
        if len(start) != 2 or len(end) != 2:
            raise RoutingServiceError("起点和终点必须包含2个坐标值: [x, y]")
        
        if start == end:
            raise RoutingServiceError("起点和终点不能相同")
        
        errors = []
        warnings = []
        
        logger.info(f"Calculating route: start={start}, end={end}, element_type={element_type}, system_type={system_type}")
        
        # 0. 对于电缆/电线，检查是否依赖桥架/线管
        if element_type in ["Wire", "Cable"]:
            container_info = self._find_container_element(element_id)
            if container_info:
                container_id, container_type = container_info
                
                # 检查容器的路由状态（只有当状态明确存在且不是COMPLETED时才报错）
                container_status = self._get_container_routing_status(container_id)
                if container_status is not None and container_status != "COMPLETED":
                    raise RoutingServiceError(
                        f"关联的{container_type}尚未完成路由，请先完成{container_type}路由后再进行电缆路由。"
                    )
                
                # 如果是桥架，验证容量
                if container_type == "CableTray":
                    from app.core.cable_capacity_validator import CableCapacityValidator
                    validator = CableCapacityValidator(self.client)
                    capacity_result = validator.validate_cable_tray_capacity(
                        container_id, element_id
                    )
                    if not capacity_result["valid"]:
                        errors.extend(capacity_result["errors"])
                        return {
                            "path_points": [],
                            "constraints": {},
                            "warnings": capacity_result.get("warnings", []),
                            "errors": errors
                        }
                    warnings.extend(capacity_result.get("warnings", []))
                
                # 使用容器元素的路由
                container_route = self._get_element_route(container_id)
                if container_route:
                    return {
                        "path_points": container_route,
                        "constraints": {},
                        "warnings": warnings + ["路由继承自桥架/线管"],
                        "errors": errors
                    }
                else:
                    raise RoutingServiceError("关联的桥架/线管尚未完成路由规划")
            else:
                # 如果没有关联的容器，返回错误
                raise RoutingServiceError("电缆/电线必须首先指定关联的桥架/线管")
        
        # 1. Brick Schema 语义验证（如果提供了源和目标元素类型）
        if validate_semantic and source_element_type and target_element_type:
            validation_result = self.brick_validator.validate_mep_connection(
                source_element_type,
                target_element_type,
                relationship="feeds"
            )
            if not validation_result["valid"]:
                errors.append(f"语义验证失败: {validation_result['error']}")
                if validation_result.get("suggestion"):
                    warnings.append(f"建议使用关系: {validation_result['suggestion']}")
        
        # 2. 获取系统特定约束
        constraints = self._get_constraints(element_type, element_properties, system_type)
        
        # 3. 检查是否需要双45°弯头模式
        if constraints.get("requires_double_45"):
            # 重力排水系统：使用双45°路径点模式
            result = self._route_with_double_45(start, end, constraints, obstacles)
        else:
            # 普通系统：使用标准路径规划
            result = self._route_standard(start, end, constraints, obstacles)
        
        # 4. 验证坡度约束（仅管道）
        if validate_slope and element_type == "Pipe" and system_type:
            slope_validation = self._validate_slope(
                result["path_points"],
                system_type,
                element_properties.get("slope")
            )
            if not slope_validation["valid"]:
                errors.extend(slope_validation["errors"])
            warnings.extend(slope_validation.get("warnings", []))
        
        # 5. 验证Room和Space约束
        if validate_room_constraints and level_id and len(result["path_points"]) >= 2:
            # 获取原始路由经过的Room ID列表
            original_route_room_ids = []
            if element_id:
                original_route_room_ids = self._get_original_route_rooms(element_id)
            
            # 验证路径是否穿过有效的Space和Room
            room_space_validation = self._validate_room_constraints(
                result["path_points"],
                original_route_room_ids,
                level_id,
                element_type
            )
            if not room_space_validation["valid"]:
                errors.extend(room_space_validation["errors"])
            warnings.extend(room_space_validation.get("warnings", []))
        
        result["errors"].extend(errors)
        result["warnings"].extend(warnings)
        return result
    
    def _get_constraints(
        self,
        element_type: str,
        element_properties: Dict[str, Any],
        system_type: Optional[str]
    ) -> Dict[str, Any]:
        """获取系统特定约束"""
        system_rules = self.config_loader.get_constraints(element_type, system_type)
        
        # 根据管径/规格获取转弯半径约束（管道、风管）
        bend_radius = None
        if element_type in ["Pipe", "Duct", "Conduit"]:
            diameter = element_properties.get("diameter", 0)
            bend_radius_ratio = self.config_loader.get_bend_radius_ratio(element_type, diameter)
            if bend_radius_ratio:
                bend_radius = diameter * bend_radius_ratio / 1000.0  # 转换为米
        
        # 电缆桥架宽度约束
        min_width = None
        if element_type == "CableTray":
            # 假设电缆转弯半径为桥架宽度的某个倍数
            cable_bend_radius = element_properties.get("width", 100)  # 默认值
            width_ratio = self.config_loader.get_min_width_ratio(cable_bend_radius)
            if width_ratio:
                min_width = cable_bend_radius * width_ratio / 1000.0  # 转换为米
        
        return {
            "allowed_angles": system_rules.get("allowed_angles", [45, 90, 180]),
            "forbidden_angles": system_rules.get("forbidden_angles", []),
            "bend_radius": bend_radius,
            "min_width": min_width,
            "requires_double_45": system_rules.get("requires_double_45", False)
        }
    
    def _route_with_double_45(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        constraints: Dict[str, Any],
        obstacles: Optional[List[Geometry]]
    ) -> Dict[str, Any]:
        """
        重力排水系统路径规划：使用双45°路径点
        
        策略：
        1. 计算从起点到终点的曼哈顿路径
        2. 在需要90°转弯的地方，用两个45°路径点替代
        3. 确保两个45°路径点之间有足够的距离
        """
        # 1. 计算基础路径（允许90°）
        base_path = self._calculate_manhattan_path(start, end, obstacles)
        
        # 2. 检测路径中的90°转弯点
        modified_path = []
        warnings = []
        
        for i, point in enumerate(base_path):
            modified_path.append(point)
            
            # 检查是否需要在此处插入双45°路径点
            if i < len(base_path) - 1 and i > 0:
                prev_point = base_path[i - 1]
                next_point = base_path[i + 1]
                
                turn_angle = self._calculate_turn_angle(prev_point, point, next_point)
                
                if abs(turn_angle - 90) < 5:  # 检测到90°转弯（允许5°容差）
                    # 插入双45°路径点
                    double_45_result = self._create_double_45_turn(
                        point,
                        prev_point,
                        next_point,
                        constraints.get("bend_radius")
                    )
                    
                    # 添加第一个45°路径点后的中间点
                    modified_path.extend(double_45_result["intermediate_points"])
                    warnings.extend(double_45_result.get("warnings", []))
        
        return {
            "path_points": modified_path,
            "constraints": {
                "bend_radius": constraints.get("bend_radius"),
                "pattern": "double_45"
            },
            "warnings": warnings,
            "errors": []
        }
    
    def _create_double_45_turn(
        self,
        corner: Tuple[float, float],
        prev_point: Tuple[float, float],
        next_point: Tuple[float, float],
        min_radius: Optional[float]
    ) -> Dict[str, Any]:
        """
        创建双45°路径点
        
        只返回路径点坐标，不生成具体弯头配件
        """
        # 计算方向向量
        dir_in = (
            corner[0] - prev_point[0],
            corner[1] - prev_point[1]
        )
        dir_out = (
            next_point[0] - corner[0],
            next_point[1] - corner[1]
        )
        
        # 归一化方向向量
        len_in = math.sqrt(dir_in[0]**2 + dir_in[1]**2)
        len_out = math.sqrt(dir_out[0]**2 + dir_out[1]**2)
        
        if len_in > 0:
            dir_in = (dir_in[0] / len_in, dir_in[1] / len_in)
        if len_out > 0:
            dir_out = (dir_out[0] / len_out, dir_out[1] / len_out)
        
        # 计算45°方向（第一个路径点后的方向）
        angle_in = math.atan2(dir_in[1], dir_in[0])
        angle_45 = angle_in + math.pi / 4  # 45度 = π/4 弧度
        
        # 第一个45°路径点的位置（从corner沿输入方向后退一定距离）
        min_distance = min_radius * 1.5 if min_radius else 0.2  # 最小距离（米）
        first_bend_point = (
            corner[0] - dir_in[0] * min_distance,
            corner[1] - dir_in[1] * min_distance
        )
        
        # 第一个45°路径点后的中间点（沿45°方向前进）
        intermediate_point = (
            first_bend_point[0] + math.cos(angle_45) * min_distance,
            first_bend_point[1] + math.sin(angle_45) * min_distance
        )
        
        # 第二个45°路径点的位置（从intermediate_point沿45°方向前进）
        second_bend_point = (
            intermediate_point[0] + math.cos(angle_45) * min_distance,
            intermediate_point[1] + math.sin(angle_45) * min_distance
        )
        
        return {
            "intermediate_points": [first_bend_point, intermediate_point, second_bend_point],
            "warnings": []
        }
    
    def _route_standard(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        constraints: Dict[str, Any],
        obstacles: Optional[List[Geometry]]
    ) -> Dict[str, Any]:
        """标准路径规划（支持转弯半径约束）"""
        # 计算基础曼哈顿路径
        base_path = self._calculate_manhattan_path(start, end, obstacles)
        
        # 如果存在转弯半径约束，使用圆弧路径替代直角转弯
        bend_radius = constraints.get("bend_radius")
        if bend_radius:
            base_path = self._apply_bend_radius_constraint(base_path, bend_radius)
        
        return {
            "path_points": base_path,
            "constraints": {
                "bend_radius": bend_radius,
                "min_width": constraints.get("min_width")
            },
            "warnings": [],
            "errors": []
        }
    
    def _calculate_manhattan_path(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        obstacles: Optional[List[Geometry]]
    ) -> List[Tuple[float, float]]:
        """
        计算基础曼哈顿路径（仅水平和垂直移动）
        
        简化实现：直接使用起点和终点的中间点
        实际应用中可以使用A*算法或改进的曼哈顿路由
        """
        # 简单的曼哈顿路径：先水平移动，再垂直移动
        path = [start]
        
        # 水平移动
        if abs(start[0] - end[0]) > 0.01:
            path.append((end[0], start[1]))
        
        # 垂直移动
        if abs(start[1] - end[1]) > 0.01:
            path.append(end)
        elif len(path) == 1:
            # 如果起点和终点相同或非常接近，只返回起点
            path.append(end)
        
        return path
    
    def _calculate_turn_angle(
        self,
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        p3: Tuple[float, float]
    ) -> float:
        """计算转弯角度（度）"""
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
    
    def _apply_bend_radius_constraint(
        self,
        path: List[Tuple[float, float]],
        min_radius: float
    ) -> List[Tuple[float, float]]:
        """
        应用转弯半径约束：使用圆弧路径替代直角转弯
        
        简化实现：在转弯点处插入圆弧路径点
        """
        if len(path) < 3:
            return path
        
        modified_path = [path[0]]
        
        for i in range(1, len(path) - 1):
            p1 = path[i - 1]
            p2 = path[i]
            p3 = path[i + 1]
            
            # 检查是否为直角转弯
            turn_angle = self._calculate_turn_angle(p1, p2, p3)
            
            if abs(turn_angle - 90) < 5:  # 90°转弯
                # 在转弯点处插入圆弧路径点
                # 简化处理：插入几个中间点形成圆弧效果
                arc_points = self._generate_arc_points(p1, p2, p3, min_radius)
                modified_path.extend(arc_points)
            else:
                modified_path.append(p2)
        
        modified_path.append(path[-1])
        return modified_path
    
    def _generate_arc_points(
        self,
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        p3: Tuple[float, float],
        radius: float
    ) -> List[Tuple[float, float]]:
        """生成圆弧路径点"""
        # 简化实现：在p2附近插入几个点形成圆弧效果
        # 实际应用中需要精确计算圆弧路径
        
        # 计算方向
        dir_in = (p2[0] - p1[0], p2[1] - p1[1])
        dir_out = (p3[0] - p2[0], p3[1] - p2[1])
        
        len_in = math.sqrt(dir_in[0]**2 + dir_in[1]**2)
        len_out = math.sqrt(dir_out[0]**2 + dir_out[1]**2)
        
        if len_in > 0:
            dir_in = (dir_in[0] / len_in, dir_in[1] / len_in)
        if len_out > 0:
            dir_out = (dir_out[0] / len_out, dir_out[1] / len_out)
        
        # 计算转弯点（使用圆弧）
        # 简化处理：插入几个中间点
        points = []
        num_points = 3  # 插入3个中间点
        
        for i in range(1, num_points + 1):
            t = i / (num_points + 1)
            # 线性插值（简化，实际应该使用圆弧）
            point = (
                p2[0] - dir_in[0] * radius * (1 - t) + dir_out[0] * radius * t,
                p2[1] - dir_in[1] * radius * (1 - t) + dir_out[1] * radius * t
            )
            points.append(point)
        
        return points
    
    def _get_original_route_rooms(self, element_id: str) -> List[str]:
        """获取原始路由经过的Room ID列表
        
        Args:
            element_id: 元素ID
            
        Returns:
            Room ID列表（不是Space ID）
        """
        return self.spatial_service.get_original_route_rooms(element_id)
    
    def _validate_room_constraints(
        self,
        path_points: List[Tuple[float, float]],
        original_route_room_ids: List[str],
        level_id: str,
        element_type: str
    ) -> Dict[str, Any]:
        """验证Room和Space约束
        
        Args:
            path_points: 路径点列表
            original_route_room_ids: 原始路由经过的Room ID列表
            level_id: 楼层ID
            element_type: 元素类型（用于判断是否为水平MEP）
            
        Returns:
            验证结果字典
        """
        # 判断是否为水平MEP（简化：根据element_type判断）
        # 实际的竖向管线判定应该在路径规划之前完成
        forbid_horizontal = element_type in ["Pipe", "Duct", "CableTray", "Conduit", "Wire"]
        
        return self.spatial_service.validate_path_through_rooms_and_spaces(
            path_points,
            original_route_room_ids,
            level_id,
            forbid_horizontal=forbid_horizontal
        )
    
    def _validate_slope(
        self,
        path_points: List[Tuple[float, float]],
        system_type: str,
        slope: Optional[float]
    ) -> Dict[str, Any]:
        """验证坡度约束（仅重力流管道）
        
        Args:
            path_points: 路径点列表
            system_type: 系统类型
            slope: 坡度（百分比%）
            
        Returns:
            验证结果字典
        """
        errors = []
        warnings = []
        
        # 检查是否为重力流系统
        gravity_flow_systems = ["gravity_drainage", "gravity_rainwater", "condensate"]
        if system_type not in gravity_flow_systems:
            # 非重力流系统，不需要验证坡度
            return {
                "valid": True,
                "errors": [],
                "warnings": []
            }
        
        # 重力流管道必须slope > 0（不能倒坡）
        if slope is None:
            errors.append(f"重力流系统 {system_type} 必须设置坡度（slope）属性")
            return {
                "valid": False,
                "errors": errors,
                "warnings": warnings
            }
        
        if slope <= 0:
            errors.append(f"重力流系统 {system_type} 的坡度必须大于0（当前值: {slope}%），不能倒坡")
            return {
                "valid": False,
                "errors": errors,
                "warnings": warnings
            }
        
        # 验证路径方向是否符合坡度要求（简化：只检查路径是否向下）
        if len(path_points) >= 2:
            # 注意：这里的path_points是2D路径，不包含Z坐标
            # 实际的坡度验证应该在3D空间中完成
            # 这里只做基本的坡度值验证
            pass
        
        return {
            "valid": True,
            "errors": [],
            "warnings": warnings
        }
    
    def _get_container_routing_status(self, container_id: str) -> Optional[str]:
        """获取容器的路由状态
        
        Args:
            container_id: 容器元素ID
            
        Returns:
            路由状态字符串（如 'COMPLETED', 'PLANNING'），如果元素不存在则返回 None
        """
        try:
            query = """
            MATCH (container:Element {id: $container_id})
            RETURN container.routing_status as routing_status
            """
            result = self.client.execute_query(query, {"container_id": container_id})
            if not result:
                return None
            
            return result[0].get("routing_status")
        except Exception as e:
            logger.warning(f"Error getting container routing status for {container_id}: {e}")
            return None
    
    def _find_container_element(self, element_id: Optional[str]) -> Optional[Tuple[str, str]]:
        """查找包含该元素的容器元素（用于 Wire/Cable）
        
        Args:
            element_id: 元素ID（Wire 或 Cable）
            
        Returns:
            如果找到容器，返回 (container_id, container_type) 元组，否则返回 None
        """
        if not element_id:
            return None
        
        try:
            # 查询 CONTAINED_IN 关系，找到包含该元素的容器
            query = """
            MATCH (wire:Element {id: $element_id})-[:CONTAINED_IN]->(container:Element)
            WHERE container.speckle_type IN ['CableTray', 'Conduit']
            RETURN container.id as container_id, container.speckle_type as container_type
            LIMIT 1
            """
            result = self.client.execute_query(query, {"element_id": element_id})
            if result:
                row = result[0]
                return (row["container_id"], row["container_type"])
        except Exception as e:
            logger.warning(f"Error finding container element for {element_id}: {e}")
        
        return None
    
    def _get_element_route(self, element_id: str) -> Optional[List[Tuple[float, float]]]:
        """获取元素的路由路径
        
        Args:
            element_id: 元素ID
            
        Returns:
            路径点列表 [(x1, y1), (x2, y2), ...]，如果元素不存在或没有路由信息则返回 None
        """
        try:
            # 查询元素的 geometry，从中提取路径点
            query = """
            MATCH (e:Element {id: $element_id})
            RETURN e.geometry as geometry
            """
            result = self.client.execute_query(query, {"element_id": element_id})
            if not result:
                return None
            
            geometry_data = result[0].get("geometry")
            if not geometry_data:
                return None
            
            # 解析 geometry 数据
            if isinstance(geometry_data, str):
                import json
                try:
                    geometry_data = json.loads(geometry_data)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse geometry JSON for element {element_id}")
                    return None
            
            if not isinstance(geometry_data, dict):
                return None
            
            coordinates = geometry_data.get("coordinates", [])
            if not coordinates:
                return None
            
            # 提取 2D 坐标点（只取 x, y，忽略 z）
            path_points = []
            for coord in coordinates:
                if len(coord) >= 2:
                    path_points.append((float(coord[0]), float(coord[1])))
            
            return path_points if len(path_points) >= 2 else None
            
        except Exception as e:
            logger.warning(f"Error getting element route for {element_id}: {e}")
            return None


class RoutingService:
    """路由规划服务
    
    处理路由规划状态管理和批量路由规划操作
    """
    
    def __init__(self, client: Optional[MemgraphClient] = None):
        """初始化服务
        
        Args:
            client: Memgraph 客户端实例（如果为 None，将创建新实例）
        """
        self.client = client or MemgraphClient()
        self.router = FlexibleRouter()
    
    def complete_routing_planning(
        self,
        element_ids: List[str],
        original_route_room_ids: Optional[Dict[str, List[str]]] = None
    ) -> Dict[str, Any]:
        """完成路由规划，标记路由规划完成
        
        将指定元素的routing_status设置为COMPLETED，并保存original_route_room_ids
        
        Args:
            element_ids: 元素ID列表
            original_route_room_ids: 元素ID到Room ID列表的映射（可选）
            
        Returns:
            更新结果字典
        """
        updated_count = 0
        
        for element_id in element_ids:
            # 构建更新字段
            update_fields = ["e.routing_status = 'COMPLETED'"]
            update_params: Dict[str, Any] = {"element_id": element_id}
            
            # 如果有原始路由Room ID列表，保存它
            if original_route_room_ids and element_id in original_route_room_ids:
                room_ids = original_route_room_ids[element_id]
                update_fields.append("e.original_route_room_ids = $original_route_room_ids")
                update_params["original_route_room_ids"] = room_ids
            
            # 执行更新
            update_query = f"""
            MATCH (e:Element {{id: $element_id}})
            SET {', '.join(update_fields)}, e.updated_at = datetime()
            RETURN e.id as id
            """
            
            try:
                self.client.execute_write(update_query, update_params)
                updated_count += 1
            except Exception as e:
                logger.error(f"Failed to update routing status for element {element_id}: {e}")
                continue
        
        return {
            "updated_count": updated_count,
            "total_count": len(element_ids),
            "element_ids": element_ids
        }
    
    def revert_to_routing_planning(
        self,
        element_ids: List[str]
    ) -> Dict[str, Any]:
        """退回路由规划阶段
        
        将指定元素的routing_status设置为PLANNING，coordination_status设置为PENDING
        
        Args:
            element_ids: 元素ID列表
            
        Returns:
            更新结果字典
        """
        updated_count = 0
        
        for element_id in element_ids:
            update_query = """
            MATCH (e:Element {id: $element_id})
            SET e.routing_status = 'PLANNING',
                e.coordination_status = 'PENDING',
                e.updated_at = datetime()
            RETURN e.id as id
            """
            
            try:
                self.client.execute_write(update_query, {"element_id": element_id})
                updated_count += 1
            except Exception as e:
                logger.error(f"Failed to revert routing status for element {element_id}: {e}")
                continue
        
        return {
            "updated_count": updated_count,
            "total_count": len(element_ids),
            "element_ids": element_ids
        }

