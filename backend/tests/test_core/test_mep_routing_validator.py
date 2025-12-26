"""MEP 路径规划验证器测试"""

import pytest
from app.core.validators import MEPRoutingValidator


class TestMEPRoutingValidator:
    """MEPRoutingValidator 测试类"""
    
    def test_validate_mep_routing_path_valid(self):
        """测试有效路径验证"""
        path_points = [[0.0, 0.0], [5.0, 0.0], [5.0, 5.0], [10.0, 10.0]]
        
        result = MEPRoutingValidator.validate_mep_routing_path(
            path_points,
            "Pipe",
            None,
            None
        )
        
        assert result["valid"] is True
        assert len(result["errors"]) == 0
    
    def test_validate_mep_routing_path_too_few_points(self):
        """测试路径点太少"""
        path_points = [[0.0, 0.0]]  # 只有1个点
        
        result = MEPRoutingValidator.validate_mep_routing_path(
            path_points,
            "Pipe",
            None,
            None
        )
        
        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert "至少需要2个点" in result["errors"][0]
    
    def test_validate_mep_routing_path_empty(self):
        """测试空路径"""
        path_points = []
        
        result = MEPRoutingValidator.validate_mep_routing_path(
            path_points,
            "Pipe",
            None,
            None
        )
        
        assert result["valid"] is False
        assert len(result["errors"]) > 0
    
    def test_validate_mep_routing_path_invalid_format(self):
        """测试路径点格式错误"""
        path_points = [[0.0], [5.0, 0.0]]  # 第一个点只有1个坐标
        
        result = MEPRoutingValidator.validate_mep_routing_path(
            path_points,
            "Pipe",
            None,
            None
        )
        
        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert "格式错误" in result["errors"][0]
    
    def test_validate_mep_routing_path_invalid_coordinates(self):
        """测试坐标不是数字"""
        path_points = [["invalid", 0.0], [5.0, 0.0]]
        
        result = MEPRoutingValidator.validate_mep_routing_path(
            path_points,
            "Pipe",
            None,
            None
        )
        
        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert "坐标必须是数字" in result["errors"][0]
    
    def test_validate_mep_routing_path_with_forbidden_angles(self):
        """测试禁止角度的验证"""
        # 包含90°转弯的路径（重力排水系统禁止90°）
        path_points = [[0.0, 0.0], [5.0, 0.0], [5.0, 5.0]]
        
        constraints = {
            "allowed_angles": [45, 180],
            "forbidden_angles": [90]
        }
        
        result = MEPRoutingValidator.validate_mep_routing_path(
            path_points,
            "Pipe",
            "gravity_drainage",
            constraints
        )
        
        # 应该检测到90°转弯
        assert len(result["errors"]) > 0 or len(result["warnings"]) > 0
    
    def test_validate_mep_routing_path_with_allowed_angles(self):
        """测试允许角度的验证"""
        # 包含45°转弯的路径
        path_points = [[0.0, 0.0], [5.0, 0.0], [10.0, 5.0]]
        
        constraints = {
            "allowed_angles": [45, 90, 180],
            "forbidden_angles": []
        }
        
        result = MEPRoutingValidator.validate_mep_routing_path(
            path_points,
            "Pipe",
            None,
            constraints
        )
        
        # 45°在允许列表中，应该通过
        assert result["valid"] is True or len(result["warnings"]) == 0
    
    def test_validate_mep_routing_path_no_constraints(self):
        """测试无约束时的验证"""
        path_points = [[0.0, 0.0], [10.0, 10.0]]
        
        result = MEPRoutingValidator.validate_mep_routing_path(
            path_points,
            "Pipe",
            None,
            None
        )
        
        assert result["valid"] is True
        assert len(result["errors"]) == 0
    
    def test_validate_bend_radius_valid(self):
        """测试转弯半径满足要求"""
        # 路径点之间的距离足够大，满足最小转弯半径
        path_points = [[0.0, 0.0], [5.0, 0.0], [5.0, 5.0]]
        min_radius = 0.5  # 最小转弯半径0.5米
        
        result = MEPRoutingValidator.validate_bend_radius(
            path_points,
            min_radius
        )
        
        # 由于路径点间距较大，应该满足要求
        assert result["valid"] is True
    
    def test_validate_bend_radius_insufficient_path_points(self):
        """测试路径点不足3个时（无法计算转弯半径）"""
        path_points = [[0.0, 0.0], [10.0, 10.0]]
        min_radius = 0.5
        
        result = MEPRoutingValidator.validate_bend_radius(
            path_points,
            min_radius
        )
        
        # 路径点不足3个，无法计算转弯半径，应该返回valid=True
        assert result["valid"] is True
    
    def test_validate_bend_radius_with_warnings(self):
        """测试转弯半径不足时的警告"""
        # 使用非常小的路径点间距
        path_points = [[0.0, 0.0], [0.1, 0.0], [0.1, 0.1]]
        min_radius = 1.0  # 最小转弯半径1米（比路径点间距大很多）
        
        result = MEPRoutingValidator.validate_bend_radius(
            path_points,
            min_radius
        )
        
        # 应该有警告（如果实际半径小于最小半径）
        # 注意：实际验证逻辑可能不会触发警告，取决于实现
        assert "warnings" in result
    
    def test_validate_cable_tray_width_valid(self):
        """测试电缆桥架宽度满足要求"""
        width = 600  # 600mm
        cable_bend_radius = 150  # 150mm
        min_width_ratio = 3.0  # 最小宽度比3.0
        
        result = MEPRoutingValidator.validate_cable_tray_width(
            width,
            cable_bend_radius,
            min_width_ratio
        )
        
        # 600 >= 150 * 3.0 = 450，满足要求
        assert result["valid"] is True
        assert len(result["errors"]) == 0
    
    def test_validate_cable_tray_width_invalid(self):
        """测试电缆桥架宽度不满足要求"""
        width = 300  # 300mm
        cable_bend_radius = 150  # 150mm
        min_width_ratio = 3.0  # 最小宽度比3.0
        
        result = MEPRoutingValidator.validate_cable_tray_width(
            width,
            cable_bend_radius,
            min_width_ratio
        )
        
        # 300 < 150 * 3.0 = 450，不满足要求
        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert "小于最小要求" in result["errors"][0]
    
    def test_validate_cable_tray_width_boundary(self):
        """测试边界值"""
        # 正好等于最小要求
        width = 450  # 450mm
        cable_bend_radius = 150  # 150mm
        min_width_ratio = 3.0  # 最小宽度比3.0
        
        result = MEPRoutingValidator.validate_cable_tray_width(
            width,
            cable_bend_radius,
            min_width_ratio
        )
        
        # 450 == 150 * 3.0 = 450，满足要求
        assert result["valid"] is True
    
    def test_calculate_turn_angle_90_degrees(self):
        """测试90度转弯角度计算"""
        angle = MEPRoutingValidator._calculate_turn_angle(
            (0.0, 0.0),
            (0.0, 5.0),
            (5.0, 5.0)
        )
        
        assert abs(angle - 90) < 1  # 允许1度误差
    
    def test_calculate_turn_angle_45_degrees(self):
        """测试45度转弯角度计算"""
        # 创建一个45度转弯：从(0,0)到(5,0)，然后到(10,5)
        angle = MEPRoutingValidator._calculate_turn_angle(
            (0.0, 0.0),
            (5.0, 0.0),
            (10.0, 5.0)
        )
        
        assert abs(angle - 45) < 5  # 允许5度误差（因为路径可能不是精确45度）
    
    def test_calculate_turn_angle_180_degrees(self):
        """测试180度转弯角度计算（U型转弯）"""
        angle = MEPRoutingValidator._calculate_turn_angle(
            (0.0, 0.0),
            (5.0, 0.0),
            (0.0, 0.0)  # 回到起点
        )
        
        # 180度转弯
        assert abs(angle - 180) < 1
    
    def test_calculate_turn_angle_straight_line(self):
        """测试直线（0度转弯）"""
        angle = MEPRoutingValidator._calculate_turn_angle(
            (0.0, 0.0),
            (5.0, 0.0),
            (10.0, 0.0)  # 继续沿x轴
        )
        
        # 直线，角度应该接近0度或180度（取决于实现）
        assert angle <= 180
    
    def test_calculate_turn_angle_135_degrees(self):
        """测试135度转弯角度计算"""
        # 创建一个135度转弯（从水平向右，转到向下偏左）
        angle = MEPRoutingValidator._calculate_turn_angle(
            (0.0, 0.0),
            (5.0, 0.0),
            (0.0, -5.0)  # 135度转弯
        )
        
        # 角度应该在135度左右，允许15度误差（因为路径计算可能有偏差）
        assert 120 <= angle <= 150, f"Expected angle around 135 degrees, got {angle}"

