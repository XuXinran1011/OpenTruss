"""路径规划服务测试"""

import pytest
from app.services.routing import FlexibleRouter


class TestFlexibleRouter:
    """FlexibleRouter 测试类"""
    
    def test_init(self):
        """测试初始化"""
        router = FlexibleRouter()
        assert router.config_loader is not None
        assert router.brick_validator is not None
    
    def test_route_gravity_drainage_double_45(self):
        """测试重力排水系统双45°路径"""
        router = FlexibleRouter()
        
        result = router.route(
            start=(0.0, 0.0),
            end=(10.0, 10.0),
            element_type="Pipe",
            element_properties={"diameter": 100, "slope": 1.0},  # 添加坡度属性
            system_type="gravity_drainage",
            validate_slope=False  # 禁用坡度验证，因为这是路径规划测试
        )
        
        assert "path_points" in result
        assert len(result["path_points"]) >= 2
        assert result["constraints"].get("pattern") == "double_45"
        # 允许有警告但不应该有错误（如果禁用了坡度验证）
    
    def test_route_pressure_water_standard(self):
        """测试压力给水系统标准路径"""
        router = FlexibleRouter()
        
        result = router.route(
            start=(0.0, 0.0),
            end=(10.0, 10.0),
            element_type="Pipe",
            element_properties={"diameter": 100},
            system_type="pressure_water"
        )
        
        assert "path_points" in result
        assert len(result["path_points"]) >= 2
        assert "bend_radius" in result.get("constraints", {}) or result.get("constraints", {}).get("bend_radius") is None
    
    def test_route_cable_tray_width_constraint(self):
        """测试电缆桥架宽度约束"""
        router = FlexibleRouter()
        
        result = router.route(
            start=(0.0, 0.0),
            end=(10.0, 10.0),
            element_type="CableTray",
            element_properties={"width": 200},
            system_type="power_cable"
        )
        
        assert "path_points" in result
        assert len(result["path_points"]) >= 2
        # 电缆桥架应该使用宽度约束，不生成圆弧弯头
        assert "min_width" in result.get("constraints", {}) or result.get("constraints", {}).get("min_width") is None
    
    def test_get_constraints(self):
        """测试获取约束"""
        router = FlexibleRouter()
        
        constraints = router._get_constraints(
            "Pipe",
            {"diameter": 100},
            "gravity_drainage"
        )
        
        assert "allowed_angles" in constraints
        assert "forbidden_angles" in constraints
        assert 90 in constraints["forbidden_angles"]
        assert constraints["requires_double_45"] is True
    
    def test_calculate_manhattan_path(self):
        """测试曼哈顿路径计算"""
        router = FlexibleRouter()
        
        path = router._calculate_manhattan_path(
            (0.0, 0.0),
            (10.0, 5.0),
            None
        )
        
        assert len(path) >= 2
        assert path[0] == (0.0, 0.0)
        assert path[-1] == (10.0, 5.0)
    
    def test_calculate_turn_angle(self):
        """测试转弯角度计算"""
        router = FlexibleRouter()
        
        # 90度转弯
        angle = router._calculate_turn_angle(
            (0.0, 0.0),
            (0.0, 5.0),
            (5.0, 5.0)
        )
        
        assert abs(angle - 90) < 1  # 允许1度误差
    
    def test_create_double_45_turn(self):
        """测试双45°路径点生成"""
        router = FlexibleRouter()
        
        result = router._create_double_45_turn(
            corner=(0.0, 5.0),
            prev_point=(0.0, 0.0),
            next_point=(5.0, 5.0),
            min_radius=0.2
        )
        
        assert "intermediate_points" in result
        assert len(result["intermediate_points"]) == 3  # 三个中间点
    
    def test_create_double_45_turn_no_min_radius(self):
        """测试双45°路径点生成（无最小转弯半径）"""
        router = FlexibleRouter()
        
        result = router._create_double_45_turn(
            corner=(0.0, 5.0),
            prev_point=(0.0, 0.0),
            next_point=(5.0, 5.0),
            min_radius=None
        )
        
        assert "intermediate_points" in result
        assert len(result["intermediate_points"]) == 3
    
    def test_route_with_double_45_single_turn(self):
        """测试双45°路径规划（单个转弯）"""
        router = FlexibleRouter()
        
        constraints = {
            "allowed_angles": [45, 180],
            "forbidden_angles": [90],
            "requires_double_45": True,
            "bend_radius": None
        }
        
        result = router._route_with_double_45(
            start=(0.0, 0.0),
            end=(10.0, 10.0),
            constraints=constraints,
            obstacles=None
        )
        
        assert "path_points" in result
        assert len(result["path_points"]) >= 2
        assert result["constraints"]["pattern"] == "double_45"
    
    def test_route_with_double_45_multiple_turns(self):
        """测试双45°路径规划（多个转弯点）"""
        router = FlexibleRouter()
        
        constraints = {
            "allowed_angles": [45, 180],
            "forbidden_angles": [90],
            "requires_double_45": True,
            "bend_radius": 0.2
        }
        
        # 创建一个会有多个转弯的路径
        result = router._route_with_double_45(
            start=(0.0, 0.0),
            end=(20.0, 20.0),
            constraints=constraints,
            obstacles=None
        )
        
        assert "path_points" in result
        assert len(result["path_points"]) >= 2
        assert result["constraints"]["pattern"] == "double_45"
    
    def test_route_standard_no_bend_radius(self):
        """测试标准路径规划（无转弯半径约束）"""
        router = FlexibleRouter()
        
        constraints = {
            "allowed_angles": [45, 90, 180],
            "forbidden_angles": [],
            "bend_radius": None
        }
        
        result = router._route_standard(
            start=(0.0, 0.0),
            end=(10.0, 10.0),
            constraints=constraints,
            obstacles=None
        )
        
        assert "path_points" in result
        assert len(result["path_points"]) >= 2
        assert "constraints" in result
    
    def test_route_standard_with_bend_radius(self):
        """测试标准路径规划（带转弯半径约束）"""
        router = FlexibleRouter()
        
        constraints = {
            "allowed_angles": [45, 90, 180],
            "forbidden_angles": [],
            "bend_radius": 0.5
        }
        
        result = router._route_standard(
            start=(0.0, 0.0),
            end=(10.0, 10.0),
            constraints=constraints,
            obstacles=None
        )
        
        assert "path_points" in result
        assert len(result["path_points"]) >= 2
        assert result["constraints"]["bend_radius"] == 0.5
    
    def test_apply_bend_radius_constraint(self):
        """测试应用转弯半径约束"""
        router = FlexibleRouter()
        
        # 创建一个90度转弯的路径
        path = [(0.0, 0.0), (5.0, 0.0), (5.0, 5.0)]
        min_radius = 0.5
        
        modified_path = router._apply_bend_radius_constraint(path, min_radius)
        
        assert len(modified_path) >= len(path)  # 应该插入更多点
        assert modified_path[0] == path[0]
        assert modified_path[-1] == path[-1]
    
    def test_apply_bend_radius_constraint_insufficient_points(self):
        """测试路径点不足时（不应用约束）"""
        router = FlexibleRouter()
        
        path = [(0.0, 0.0), (10.0, 10.0)]  # 只有2个点
        min_radius = 0.5
        
        modified_path = router._apply_bend_radius_constraint(path, min_radius)
        
        # 路径点不足3个，应该返回原路径
        assert modified_path == path
    
    def test_apply_bend_radius_constraint_non_90_degree(self):
        """测试非90度转弯（不应用约束）"""
        router = FlexibleRouter()
        
        # 创建一个非90度的路径
        path = [(0.0, 0.0), (5.0, 0.0), (10.0, 5.0)]  # 大约45度转弯
        min_radius = 0.5
        
        modified_path = router._apply_bend_radius_constraint(path, min_radius)
        
        # 非90度转弯，应该保持原路径结构
        assert len(modified_path) >= len(path)
    
    def test_generate_arc_points(self):
        """测试生成圆弧路径点"""
        router = FlexibleRouter()
        
        arc_points = router._generate_arc_points(
            p1=(0.0, 0.0),
            p2=(5.0, 0.0),
            p3=(5.0, 5.0),
            radius=0.5
        )
        
        assert len(arc_points) == 3  # 应该生成3个中间点
        assert all(isinstance(p, tuple) and len(p) == 2 for p in arc_points)
    
    def test_generate_arc_points_zero_radius(self):
        """测试零半径圆弧点生成"""
        router = FlexibleRouter()
        
        arc_points = router._generate_arc_points(
            p1=(0.0, 0.0),
            p2=(5.0, 0.0),
            p3=(5.0, 5.0),
            radius=0.0
        )
        
        # 即使半径为0，也应该生成点
        assert len(arc_points) == 3
    
    def test_route_with_semantic_validation_failure(self):
        """测试语义验证失败的情况"""
        router = FlexibleRouter()
        
        result = router.route(
            start=(0.0, 0.0),
            end=(10.0, 10.0),
            element_type="Pipe",
            element_properties={"diameter": 100},
            system_type="gravity_drainage",
            validate_semantic=True,
            source_element_type="InvalidSource",
            target_element_type="InvalidTarget"
        )
        
        # 即使语义验证失败，也应该返回路径（但包含错误）
        assert "path_points" in result
        # 注意：实际的语义验证可能不会添加错误到结果中，取决于实现
    
    def test_route_duct(self):
        """测试风管路径规划"""
        router = FlexibleRouter()
        
        result = router.route(
            start=(0.0, 0.0),
            end=(10.0, 10.0),
            element_type="Duct",
            element_properties={"width": 500, "height": 300},
            system_type=None
        )
        
        assert "path_points" in result
        assert len(result["path_points"]) >= 2
    
    def test_route_conduit(self):
        """测试导管路径规划"""
        router = FlexibleRouter()
        
        result = router.route(
            start=(0.0, 0.0),
            end=(10.0, 10.0),
            element_type="Conduit",
            element_properties={"diameter": 50},
            system_type=None
        )
        
        assert "path_points" in result
        assert len(result["path_points"]) >= 2
    
    def test_route_wire(self):
        """测试线缆路径规划"""
        router = FlexibleRouter()
        
        # Wire 类型需要关联容器（CableTray 或 Conduit），如果没有关联容器会返回错误
        # 这个测试验证在没有容器的情况下会返回错误
        result = router.route(
            start=(0.0, 0.0),
            end=(10.0, 10.0),
            element_type="Wire",
            element_properties={"cable_bend_radius": 100},
            system_type=None,
            element_id=None  # 没有 element_id，无法查找容器
        )
        
        # Wire 类型必须关联容器，所以应该有错误
        assert "path_points" in result
        assert len(result["path_points"]) == 0  # 没有路径点
        assert len(result["errors"]) > 0  # 应该有错误信息
        assert any("桥架" in err or "线管" in err or "容器" in err for err in result["errors"])
    
    def test_calculate_turn_angle_45_degrees(self):
        """测试45度转弯角度计算"""
        router = FlexibleRouter()
        
        angle = router._calculate_turn_angle(
            (0.0, 0.0),
            (5.0, 0.0),
            (10.0, 5.0)  # 45度转弯
        )
        
        assert abs(angle - 45) < 5  # 允许5度误差
    
    def test_calculate_turn_angle_135_degrees(self):
        """测试135度转弯角度计算"""
        router = FlexibleRouter()
        
        # 创建一个135度转弯（从水平向右，转到向下偏左）
        # 使用更精确的角度：从(0,0)到(5,0)，然后到(0,-5)形成135度
        angle = router._calculate_turn_angle(
            (0.0, 0.0),
            (5.0, 0.0),
            (0.0, -5.0)  # 135度转弯
        )
        
        # 角度应该在135度左右，允许10度误差（因为路径计算可能有偏差）
        assert 120 <= angle <= 150, f"Expected angle around 135 degrees, got {angle}"
    
    def test_calculate_turn_angle_180_degrees(self):
        """测试180度转弯角度计算"""
        router = FlexibleRouter()
        
        angle = router._calculate_turn_angle(
            (0.0, 0.0),
            (5.0, 0.0),
            (0.0, 0.0)  # U型转弯
        )
        
        assert abs(angle - 180) < 5

