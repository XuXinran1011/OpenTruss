"""MEP 路径规划服务

轻量级路径规划服务，支持不同 MEP 系统类型的特定约束
只返回路径点，不生成具体配件
"""

import math
import logging
from typing import List, Tuple, Optional, Dict, Any

from app.core.mep_routing_config import get_mep_routing_config
from app.core.brick_validator import get_brick_validator
from app.models.speckle.base import Geometry2D

logger = logging.getLogger(__name__)


class FlexibleRouter:
    """灵活的 MEP 路径规划器（支持系统特定约束）"""
    
    def __init__(self):
        self.config_loader = get_mep_routing_config()
        self.brick_validator = get_brick_validator()
    
    def route(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        element_type: str,  # "Pipe", "Duct", "CableTray", "Wire"
        element_properties: Dict[str, Any],  # diameter, width, height 等
        system_type: Optional[str] = None,  # "gravity_drainage", "pressure_water" 等
        obstacles: Optional[List[Geometry2D]] = None,
        validate_semantic: bool = True,
        source_element_type: Optional[str] = None,
        target_element_type: Optional[str] = None
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
        errors = []
        warnings = []
        
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
            result["errors"].extend(errors)
            result["warnings"].extend(warnings)
            return result
        else:
            # 普通系统：使用标准路径规划
            result = self._route_standard(start, end, constraints, obstacles)
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
        obstacles: Optional[List[Geometry2D]]
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
        obstacles: Optional[List[Geometry2D]]
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
        obstacles: Optional[List[Geometry2D]]
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

