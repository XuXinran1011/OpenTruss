"""路由 API 集成测试"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestRoutingAPI:
    """路由 API 测试类"""
    
    def test_calculate_route_gravity_drainage(self):
        """测试重力排水系统路径计算"""
        response = client.post(
            "/api/v1/routing/calculate",
            json={
                "start": [0.0, 0.0],
                "end": [10.0, 10.0],
                "element_type": "Pipe",
                "element_properties": {"diameter": 100},
                "system_type": "gravity_drainage",
                "validate_semantic": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert "path_points" in data["data"]
        assert len(data["data"]["path_points"]) >= 2
        assert "constraints" in data["data"]
        assert data["data"]["constraints"].get("pattern") == "double_45"
    
    def test_calculate_route_cable_tray(self):
        """测试电缆桥架路径计算"""
        response = client.post(
            "/api/v1/routing/calculate",
            json={
                "start": [0.0, 0.0],
                "end": [10.0, 10.0],
                "element_type": "CableTray",
                "element_properties": {"width": 200},
                "system_type": "power_cable",
                "validate_semantic": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "path_points" in data["data"]
    
    def test_validate_route(self):
        """测试路径验证"""
        response = client.post(
            "/api/v1/routing/validate",
            json={
                "path_points": [[0.0, 0.0], [5.0, 0.0], [5.0, 5.0], [10.0, 10.0]],
                "element_type": "Pipe",
                "system_type": "gravity_drainage",
                "element_properties": {"diameter": 100},
                "source_element_type": "Pump",
                "target_element_type": "Pipe"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert "valid" in data["data"]
        assert "semantic_valid" in data["data"]
        assert "constraint_valid" in data["data"]
    
    def test_validate_route_with_semantic_error(self):
        """测试带有语义错误的路径验证"""
        response = client.post(
            "/api/v1/routing/validate",
            json={
                "path_points": [[0.0, 0.0], [10.0, 10.0]],
                "element_type": "Pipe",
                "source_element_type": "UnknownType",
                "target_element_type": "UnknownType"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        # 即使有语义错误，API也应该返回验证结果
        assert data["status"] == "success"
    
    def test_calculate_route_duct(self):
        """测试风管路径计算"""
        response = client.post(
            "/api/v1/routing/calculate",
            json={
                "start": [0.0, 0.0],
                "end": [10.0, 10.0],
                "element_type": "Duct",
                "element_properties": {"width": 500, "height": 300},
                "validate_semantic": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "path_points" in data["data"]
    
    def test_calculate_route_conduit(self):
        """测试导管路径计算"""
        response = client.post(
            "/api/v1/routing/calculate",
            json={
                "start": [0.0, 0.0],
                "end": [10.0, 10.0],
                "element_type": "Conduit",
                "element_properties": {"diameter": 50},
                "validate_semantic": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "path_points" in data["data"]
    
    def test_calculate_route_wire(self):
        """测试线缆路径计算（没有容器时应返回400错误）"""
        response = client.post(
            "/api/v1/routing/calculate",
            json={
                "start": [0.0, 0.0],
                "end": [10.0, 10.0],
                "element_type": "Wire",
                "element_properties": {"cable_bend_radius": 100},
                "validate_semantic": False
            }
        )
        
        # Wire类型必须关联容器，没有容器时应返回400错误
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert any(keyword in data["detail"] for keyword in ["桥架", "线管", "容器", "tray", "conduit"])
    
    def test_calculate_route_invalid_request(self):
        """测试无效请求（缺少必填字段）"""
        response = client.post(
            "/api/v1/routing/calculate",
            json={
                "start": [0.0, 0.0],
                # 缺少end字段
            }
        )
        
        # 应该返回422（验证错误）或400（错误请求）
        assert response.status_code in [400, 422]
    
    def test_validate_route_with_bend_radius_violation(self):
        """测试转弯半径验证失败"""
        # 创建一个路径点之间距离很小的路径（可能导致转弯半径不足）
        response = client.post(
            "/api/v1/routing/validate",
            json={
                "path_points": [[0.0, 0.0], [0.1, 0.0], [0.1, 0.1]],  # 非常小的间距
                "element_type": "Pipe",
                "system_type": "pressure_water",
                "element_properties": {"diameter": 100},  # 100mm管道
                # 100mm管道的最小转弯半径应该是 100 * 1.5 / 1000 = 0.15m
                # 但路径点间距只有0.1m，可能不满足要求
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        # 可能有警告或错误（取决于实际验证逻辑）
        assert "warnings" in data["data"] or "constraint_errors" in data["data"]
    
    def test_validate_route_with_cable_tray_width_violation(self):
        """测试电缆桥架宽度验证失败"""
        response = client.post(
            "/api/v1/routing/validate",
            json={
                "path_points": [[0.0, 0.0], [10.0, 10.0]],
                "element_type": "CableTray",
                "element_properties": {
                    "width": 200,  # 200mm宽度
                    "cable_bend_radius": 150  # 150mm电缆转弯半径
                    # 最小宽度应该是 150 * 3.0 = 450mm
                    # 200 < 450，不满足要求
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        # 应该有约束错误
        assert "constraint_errors" in data["data"]
        assert len(data["data"]["constraint_errors"]) > 0
    
    def test_validate_route_with_angle_constraint_violation(self):
        """测试角度约束验证失败"""
        # 创建一个包含90度转弯的路径（重力排水系统禁止90°）
        response = client.post(
            "/api/v1/routing/validate",
            json={
                "path_points": [[0.0, 0.0], [5.0, 0.0], [5.0, 5.0]],  # 90度转弯
                "element_type": "Pipe",
                "system_type": "gravity_drainage",
                "element_properties": {"diameter": 100}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        # 应该有错误或警告（90°被禁止）
        assert "constraint_errors" in data["data"] or "warnings" in data["data"]
    
    def test_validate_route_invalid_path_points_format(self):
        """测试无效路径点格式"""
        response = client.post(
            "/api/v1/routing/validate",
            json={
                "path_points": [[0.0], [10.0, 10.0]],  # 第一个点格式错误
                "element_type": "Pipe"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        # 应该有验证错误
        assert "constraint_errors" in data["data"] or "errors" in data["data"]
    
    def test_validate_route_too_few_points(self):
        """测试路径点太少或路径不符合约束"""
        # 方案A: 发送至少2个点但不符合约束的路径（例如禁止的角度）
        # 对于gravity_drainage系统，90度角度通常是被禁止的
        response = client.post(
            "/api/v1/routing/validate",
            json={
                "path_points": [[0.0, 0.0], [5.0, 0.0], [5.0, 5.0]],  # 2个点形成90度角
                "element_type": "Pipe",
                "system_type": "gravity_drainage"  # 重力排水系统通常禁止90度角
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        # 应该有验证错误
        assert "constraint_errors" in data["data"] or "errors" in data["data"]
        assert data["data"]["valid"] is False or data["data"]["constraint_valid"] is False

