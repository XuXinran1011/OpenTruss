"""CoordinationService 单元测试

测试管线综合排布服务的功能，包括碰撞检测、管线排布等
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from app.services.coordination import CoordinationService
from app.models.speckle.mep import Pipe, Duct, CableTray
from app.models.speckle.base import Geometry, Point


@pytest.fixture
def coordination_service():
    """创建 CoordinationService 实例"""
    # Mock MemgraphClient、SpatialValidator 和 get_mep_routing_config
    with patch('app.services.coordination.MemgraphClient') as mock_client_class, \
         patch('app.services.coordination.SpatialValidator') as mock_validator_class, \
         patch('app.services.coordination.get_mep_routing_config') as mock_get_config:
        mock_client = Mock()
        mock_validator = Mock()
        mock_client_class.return_value = mock_client
        mock_validator_class.return_value = mock_validator
        
        # Mock config loader with _config property
        mock_config_loader = Mock()
        mock_config_loader._config = {
            "vertical_pipe_detection": {"z_change_threshold": 1.0},
            "system_priority": {"default_priority_levels": []}
        }
        mock_get_config.return_value = mock_config_loader
        
        service = CoordinationService(client=mock_client)
        service.collision_validator = mock_validator
        # Ensure execute_query returns lists
        mock_client.execute_query.return_value = []
        return service


class TestDetectCollisions:
    """测试 detect_collisions 方法"""
    
    def test_detect_collisions_success(self, coordination_service):
        """测试成功检测碰撞"""
        level_id = "level_1"
        element_ids = ["pipe_1", "duct_1"]
        
        # Mock collision_validator.validate_collisions
        coordination_service.collision_validator.validate_collisions.return_value = {
            "collisions": [
                {"element_id_1": "pipe_1", "element_id_2": "duct_1"}
            ]
        }
        
        # Mock _get_element_type
        with patch.object(coordination_service, '_get_element_type') as mock_get_type:
            mock_get_type.side_effect = lambda eid: "Pipe" if eid == "pipe_1" else "Duct"
            
            result = coordination_service.detect_collisions(level_id, element_ids)
            
            assert "collisions" in result
            assert "collision_count" in result
            assert isinstance(result["collisions"], list)
    
    def test_detect_collisions_no_collisions(self, coordination_service):
        """测试没有碰撞的情况"""
        level_id = "level_1"
        element_ids = ["pipe_1", "duct_1"]
        
        coordination_service.collision_validator.validate_collisions.return_value = {
            "collisions": []
        }
        
        with patch.object(coordination_service, '_get_element_type') as mock_get_type:
            mock_get_type.side_effect = lambda eid: "Pipe" if eid == "pipe_1" else "Duct"
            
            result = coordination_service.detect_collisions(level_id, element_ids)
            
            assert result["collision_count"] == 0
            assert len(result["collisions"]) == 0
    
    def test_detect_collisions_empty_elements(self, coordination_service):
        """测试空元素列表"""
        level_id = "level_1"
        element_ids = []
        
        result = coordination_service.detect_collisions(level_id, element_ids)
        
        assert result["collision_count"] == 0
        assert len(result["collisions"]) == 0


class TestCoordinateLayout:
    """测试 coordinate_layout 方法"""
    
    def test_coordinate_layout_no_collisions(self, coordination_service):
        """测试没有碰撞时的排布"""
        level_id = "level_1"
        element_ids = ["pipe_1", "duct_1"]
        
        # Mock detect_collisions 返回空碰撞
        coordination_service.detect_collisions = Mock(return_value={
            "collisions": [],
            "collision_count": 0,
            "beam_column_collisions": [],
            "structure_collisions": [],
            "mep_collisions": []
        })
        
        result = coordination_service.coordinate_layout(level_id, element_ids)
        
        assert "adjusted_elements" in result
        assert result["collisions_resolved"] == 0
        assert isinstance(result["adjusted_elements"], list)
    
    def test_coordinate_layout_with_collisions(self, coordination_service):
        """测试有碰撞时的排布"""
        level_id = "level_1"
        element_ids = ["pipe_1", "duct_1"]
        
        # Mock detect_collisions 返回碰撞
        coordination_service.detect_collisions = Mock(return_value={
            "collisions": [
                {"element_id_1": "pipe_1", "element_id_2": "duct_1", "priority": "mep"}
            ],
            "collision_count": 1,
            "beam_column_collisions": [],
            "structure_collisions": [],
            "mep_collisions": [
                {"element_id_1": "pipe_1", "element_id_2": "duct_1", "priority": "mep"}
            ]
        })
        
        result = coordination_service.coordinate_layout(level_id, element_ids)
        
        assert "adjusted_elements" in result
        assert "collisions_resolved" in result
        assert isinstance(result, dict)


class TestGetSystemPriority:
    """测试 get_system_priority 方法"""
    
    def test_get_system_priority_pipe(self, coordination_service):
        """测试管道优先级"""
        element_id = "pipe_1"
        coordination_service.client.execute_query.return_value = [
            {"speckle_type": "Pipe", "system_type": None}
        ]
        coordination_service.config_loader._config = {
            "system_priority": {"default_priority_levels": []}
        }
        
        priority = coordination_service.get_system_priority(element_id)
        
        assert isinstance(priority, int)
        assert 1 <= priority <= 5
    
    def test_get_system_priority_duct(self, coordination_service):
        """测试风管优先级"""
        element_id = "duct_1"
        coordination_service.client.execute_query.return_value = [
            {"speckle_type": "Duct", "system_type": None}
        ]
        coordination_service.config_loader._config = {
            "system_priority": {"default_priority_levels": []}
        }
        
        priority = coordination_service.get_system_priority(element_id)
        
        assert isinstance(priority, int)
        assert 1 <= priority <= 5
    
    def test_get_system_priority_cable_tray(self, coordination_service):
        """测试桥架优先级"""
        element_id = "cable_tray_1"
        coordination_service.client.execute_query.return_value = [
            {"speckle_type": "CableTray", "system_type": None}
        ]
        coordination_service.config_loader._config = {
            "system_priority": {"default_priority_levels": []}
        }
        
        priority = coordination_service.get_system_priority(element_id)
        
        assert isinstance(priority, int)
        assert 1 <= priority <= 5
