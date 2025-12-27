"""SpatialService 单元测试

测试空间查询服务的功能，包括 Room 和 Space 查询、空间限制设置等
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from app.services.spatial import SpatialService
from app.core.exceptions import NotFoundError, SpatialServiceError
from app.models.speckle.spatial import Room, Space
from app.models.speckle.base import Geometry, Point


@pytest.fixture
def spatial_service():
    """创建 SpatialService 实例"""
    # SpatialService 在初始化时会创建自己的 client，我们需要 mock 它
    with patch('app.services.spatial.MemgraphClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        service = SpatialService()
        # 将 mock 的 client 赋值给 service，以便在测试中使用
        service.client = mock_client
        return service


class TestGetRoomsByLevel:
    """测试 get_rooms_by_level 方法"""
    
    def test_get_rooms_by_level_success(self, spatial_service):
        """测试成功获取楼层内的房间列表"""
        level_id = "level_1"
        spatial_service.client.execute_query.return_value = [
            {
                "id": "room_1",
                "name": "Room 101",
                "speckle_type": "Room",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]]
                }
            },
            {
                "id": "room_2",
                "name": "Room 102",
                "speckle_type": "Room",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[10, 0], [20, 0], [20, 10], [10, 10], [10, 0]]]
                }
            }
        ]
        
        rooms = spatial_service.get_rooms_by_level(level_id)
        
        assert len(rooms) == 2
        assert rooms[0].id == "room_1"
        assert rooms[0].name == "Room 101"
        assert rooms[1].id == "room_2"
        assert rooms[1].name == "Room 102"
        spatial_service.client.execute_query.assert_called_once()
    
    def test_get_rooms_by_level_empty(self, spatial_service):
        """测试楼层内没有房间的情况"""
        level_id = "level_1"
        spatial_service.client.execute_query.return_value = []
        
        rooms = spatial_service.get_rooms_by_level(level_id)
        
        assert len(rooms) == 0
    
    def test_get_rooms_by_level_invalid_level(self, spatial_service):
        """测试无效的楼层 ID"""
        level_id = "invalid_level"
        spatial_service.client.execute_query.return_value = []
        
        rooms = spatial_service.get_rooms_by_level(level_id)
        
        assert len(rooms) == 0


class TestGetSpacesByLevel:
    """测试 get_spaces_by_level 方法"""
    
    def test_get_spaces_by_level_success(self, spatial_service):
        """测试成功获取楼层内的空间列表"""
        level_id = "level_1"
        spatial_service.client.execute_query.return_value = [
            {
                "id": "space_1",
                "name": "Space 101",
                "speckle_type": "Space",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]]
                }
            }
        ]
        
        spaces = spatial_service.get_spaces_by_level(level_id)
        
        assert len(spaces) == 1
        assert spaces[0].id == "space_1"
        assert spaces[0].name == "Space 101"
        spatial_service.client.execute_query.assert_called_once()
    
    def test_get_spaces_by_level_empty(self, spatial_service):
        """测试楼层内没有空间的情况"""
        level_id = "level_1"
        spatial_service.client.execute_query.return_value = []
        
        spaces = spatial_service.get_spaces_by_level(level_id)
        
        assert len(spaces) == 0


class TestGetObstacles:
    """测试 get_obstacles 方法"""
    
    def test_get_obstacles_success(self, spatial_service):
        """测试成功获取障碍物列表"""
        level_id = "level_1"
        bbox = [0.0, 0.0, 100.0, 100.0]
        obstacle_types = ["Beam", "Column"]
        
        spatial_service.client.execute_query.return_value = [
            {
                "id": "beam_1",
                "speckle_type": "Beam",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[0, 0, 0], [10, 0, 0]]
                }
            },
            {
                "id": "column_1",
                "speckle_type": "Column",
                "geometry": {
                    "type": "Point",
                    "coordinates": [5, 5, 0]
                }
            }
        ]
        
        obstacles = spatial_service.get_obstacles(
            level_id=level_id,
            bbox=bbox,
            obstacle_types=obstacle_types
        )
        
        assert len(obstacles) == 2
        assert obstacles[0].id == "beam_1"
        assert obstacles[1].id == "column_1"
        spatial_service.client.execute_query.assert_called_once()
    
    def test_get_obstacles_empty(self, spatial_service):
        """测试没有障碍物的情况"""
        level_id = "level_1"
        bbox = [0.0, 0.0, 100.0, 100.0]
        obstacle_types = ["Beam", "Column"]
        
        spatial_service.client.execute_query.return_value = []
        
        obstacles = spatial_service.get_obstacles(
            level_id=level_id,
            bbox=bbox,
            obstacle_types=obstacle_types
        )
        
        assert len(obstacles) == 0


class TestSetSpaceMepRestrictions:
    """测试 set_space_mep_restrictions 方法"""
    
    def test_set_space_mep_restrictions_success(self, spatial_service):
        """测试成功设置空间 MEP 限制"""
        space_id = "space_1"
        forbid_horizontal_mep = True
        forbid_vertical_mep = False
        
        # Mock 检查空间存在和更新操作
        spatial_service.client.execute_query.side_effect = [
            [{"id": space_id}],  # 第一次查询检查空间存在
            [{"id": space_id}]   # 第二次查询获取更新后的数据
        ]
        
        result = spatial_service.set_space_mep_restrictions(
            space_id=space_id,
            forbid_horizontal_mep=forbid_horizontal_mep,
            forbid_vertical_mep=forbid_vertical_mep
        )
        
        assert result["space_id"] == space_id
        assert result["forbid_horizontal_mep"] == forbid_horizontal_mep
        assert result["forbid_vertical_mep"] == forbid_vertical_mep
        assert "updated_at" in result
    
    def test_set_space_mep_restrictions_not_found(self, spatial_service):
        """测试空间不存在的情况"""
        space_id = "invalid_space"
        spatial_service.client.execute_query.return_value = []
        
        with pytest.raises(NotFoundError) as exc_info:
            spatial_service.set_space_mep_restrictions(
                space_id=space_id,
                forbid_horizontal_mep=True,
                forbid_vertical_mep=False
            )
        
        assert "not found" in exc_info.value.message.lower()


class TestGetSpaceMepRestrictions:
    """测试 get_space_mep_restrictions 方法"""
    
    def test_get_space_mep_restrictions_success(self, spatial_service):
        """测试成功获取空间 MEP 限制"""
        space_id = "space_1"
        spatial_service.client.execute_query.return_value = [
            {
                "id": space_id,
                "forbid_horizontal_mep": True,
                "forbid_vertical_mep": False
            }
        ]
        
        result = spatial_service.get_space_mep_restrictions(space_id)
        
        assert result["space_id"] == space_id
        assert result["forbid_horizontal_mep"] is True
        assert result["forbid_vertical_mep"] is False
    
    def test_get_space_mep_restrictions_not_found(self, spatial_service):
        """测试空间不存在的情况"""
        space_id = "invalid_space"
        spatial_service.client.execute_query.return_value = []
        
        with pytest.raises(NotFoundError) as exc_info:
            spatial_service.get_space_mep_restrictions(space_id)
        
        assert "not found" in exc_info.value.message.lower()


class TestSetSpaceIntegratedHanger:
    """测试 set_space_integrated_hanger 方法"""
    
    def test_set_space_integrated_hanger_success(self, spatial_service):
        """测试成功设置空间综合支吊架配置"""
        space_id = "space_1"
        use_integrated_hanger = True
        
        # Mock 检查空间存在和更新操作
        spatial_service.client.execute_query.side_effect = [
            [{"id": space_id}],  # 第一次查询检查空间存在
            [{"id": space_id}]   # 第二次查询获取更新后的数据
        ]
        
        result = spatial_service.set_space_integrated_hanger(
            space_id=space_id,
            use_integrated_hanger=use_integrated_hanger
        )
        
        assert result["space_id"] == space_id
        assert result["use_integrated_hanger"] == use_integrated_hanger
        assert "updated_at" in result
    
    def test_set_space_integrated_hanger_not_found(self, spatial_service):
        """测试空间不存在的情况"""
        space_id = "invalid_space"
        spatial_service.client.execute_query.return_value = []
        
        with pytest.raises(NotFoundError) as exc_info:
            spatial_service.set_space_integrated_hanger(
                space_id=space_id,
                use_integrated_hanger=True
            )
        
        assert "not found" in exc_info.value.message.lower()


class TestGetSpaceIntegratedHanger:
    """测试 get_space_integrated_hanger 方法"""
    
    def test_get_space_integrated_hanger_success(self, spatial_service):
        """测试成功获取空间综合支吊架配置"""
        space_id = "space_1"
        spatial_service.client.execute_query.return_value = [
            {
                "id": space_id,
                "use_integrated_hanger": True
            }
        ]
        
        result = spatial_service.get_space_integrated_hanger(space_id)
        
        assert result["space_id"] == space_id
        assert result["use_integrated_hanger"] is True
    
    def test_get_space_integrated_hanger_not_found(self, spatial_service):
        """测试空间不存在的情况"""
        space_id = "invalid_space"
        spatial_service.client.execute_query.return_value = []
        
        with pytest.raises(NotFoundError) as exc_info:
            spatial_service.get_space_integrated_hanger(space_id)
        
        assert "not found" in exc_info.value.message.lower()


class TestGetOriginalRouteRooms:
    """测试 get_original_route_rooms 方法"""
    
    def test_get_original_route_rooms_success(self, spatial_service):
        """测试成功获取原始路由Room ID列表"""
        element_id = "element_1"
        spatial_service.client.execute_query.return_value = [
            {"original_route_room_ids": ["room_1", "room_2", "room_3"]}
        ]
        
        room_ids = spatial_service.get_original_route_rooms(element_id)
        
        assert len(room_ids) == 3
        assert room_ids == ["room_1", "room_2", "room_3"]
        spatial_service.client.execute_query.assert_called_once()
    
    def test_get_original_route_rooms_empty(self, spatial_service):
        """测试元素没有原始路由Room的情况"""
        element_id = "element_1"
        spatial_service.client.execute_query.return_value = [
            {"original_route_room_ids": None}
        ]
        
        room_ids = spatial_service.get_original_route_rooms(element_id)
        
        assert len(room_ids) == 0
    
    def test_get_original_route_rooms_json_string(self, spatial_service):
        """测试原始路由Room ID为JSON字符串的情况"""
        import json
        element_id = "element_1"
        spatial_service.client.execute_query.return_value = [
            {"original_route_room_ids": '["room_1", "room_2"]'}
        ]
        
        room_ids = spatial_service.get_original_route_rooms(element_id)
        
        assert len(room_ids) == 2
        assert room_ids == ["room_1", "room_2"]
    
    def test_get_original_route_rooms_comma_separated(self, spatial_service):
        """测试原始路由Room ID为逗号分隔字符串的情况"""
        element_id = "element_1"
        spatial_service.client.execute_query.return_value = [
            {"original_route_room_ids": "room_1, room_2, room_3"}
        ]
        
        room_ids = spatial_service.get_original_route_rooms(element_id)
        
        assert len(room_ids) == 3
        assert room_ids == ["room_1", "room_2", "room_3"]


class TestValidatePathThroughRoomsAndSpaces:
    """测试 validate_path_through_rooms_and_spaces 方法"""
    
    def test_validate_path_through_rooms_and_spaces_valid(self, spatial_service):
        """测试路径通过验证的情况"""
        path_points = [(0.0, 0.0), (10.0, 10.0), (20.0, 20.0)]
        original_route_room_ids = ["room_1", "room_2"]
        level_id = "level_1"
        
        # Mock get_spaces_by_level 返回一个通过验证的Space
        mock_space = Mock()
        mock_space.id = "space_1"
        mock_space.name = "Space 1"
        mock_space.room_id = "room_1"  # 在原始路由Room列表中
        mock_space.geometry = Mock()
        mock_space.geometry.coordinates = [[0.0, 0.0], [30.0, 0.0], [30.0, 30.0], [0.0, 30.0], [0.0, 0.0]]
        mock_space.forbid_horizontal_mep = False
        
        spatial_service.get_spaces_by_level = Mock(return_value=[mock_space])
        spatial_service._path_intersects_space = Mock(return_value=True)
        
        result = spatial_service.validate_path_through_rooms_and_spaces(
            path_points=path_points,
            original_route_room_ids=original_route_room_ids,
            level_id=level_id,
            forbid_horizontal=False
        )
        
        assert result["valid"] is True
        assert len(result["errors"]) == 0
        assert "space_1" in result["passed_spaces"]
    
    def test_validate_path_through_rooms_and_spaces_invalid_room(self, spatial_service):
        """测试路径违反Room约束的情况"""
        path_points = [(0.0, 0.0), (10.0, 10.0)]
        original_route_room_ids = ["room_1"]
        level_id = "level_1"
        
        # Mock get_spaces_by_level 返回一个违反Room约束的Space
        mock_space = Mock()
        mock_space.id = "space_1"
        mock_space.name = "Space 1"
        mock_space.room_id = "room_2"  # 不在原始路由Room列表中
        mock_space.geometry = Mock()
        mock_space.geometry.coordinates = [[0.0, 0.0], [30.0, 0.0], [30.0, 30.0], [0.0, 30.0], [0.0, 0.0]]
        mock_space.forbid_horizontal_mep = False
        
        spatial_service.get_spaces_by_level = Mock(return_value=[mock_space])
        spatial_service._path_intersects_space = Mock(return_value=True)
        
        result = spatial_service.validate_path_through_rooms_and_spaces(
            path_points=path_points,
            original_route_room_ids=original_route_room_ids,
            level_id=level_id,
            forbid_horizontal=False
        )
        
        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert "space_1" in result["blocked_spaces"]
        assert "room_2" in result["violated_rooms"]
    
    def test_validate_path_through_rooms_and_spaces_forbidden_horizontal(self, spatial_service):
        """测试路径穿过禁止水平MEP的空间的情况"""
        path_points = [(0.0, 0.0), (10.0, 10.0)]
        original_route_room_ids = ["room_1"]
        level_id = "level_1"
        
        # Mock get_spaces_by_level 返回一个禁止水平MEP的Space
        mock_space = Mock()
        mock_space.id = "space_1"
        mock_space.name = "Space 1"
        mock_space.room_id = "room_1"
        mock_space.geometry = Mock()
        mock_space.geometry.coordinates = [[0.0, 0.0], [30.0, 0.0], [30.0, 30.0], [0.0, 30.0], [0.0, 0.0]]
        mock_space.forbid_horizontal_mep = True
        
        spatial_service.get_spaces_by_level = Mock(return_value=[mock_space])
        spatial_service._path_intersects_space = Mock(return_value=True)
        
        result = spatial_service.validate_path_through_rooms_and_spaces(
            path_points=path_points,
            original_route_room_ids=original_route_room_ids,
            level_id=level_id,
            forbid_horizontal=True
        )
        
        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert "space_1" in result["blocked_spaces"]
    
    def test_validate_path_through_rooms_and_spaces_insufficient_points(self, spatial_service):
        """测试路径点不足的情况"""
        path_points = [(0.0, 0.0)]  # 只有1个点，不足2个
        original_route_room_ids = ["room_1"]
        level_id = "level_1"
        
        result = spatial_service.validate_path_through_rooms_and_spaces(
            path_points=path_points,
            original_route_room_ids=original_route_room_ids,
            level_id=level_id
        )
        
        assert result["valid"] is True  # 路径点不足时跳过验证，返回valid=True
        assert len(result["warnings"]) > 0


class TestGetObstacles:
    """测试 get_obstacles 方法的边界情况"""
    
    def test_get_obstacles_invalid_level_id(self, spatial_service):
        """测试无效的level_id"""
        with pytest.raises(SpatialServiceError, match="level_id.*不能为空"):
            spatial_service.get_obstacles(level_id="")
    
    def test_get_obstacles_invalid_bbox_format(self, spatial_service):
        """测试无效的bbox格式"""
        level_id = "level_1"
        invalid_bbox = [0.0, 0.0, 10.0]  # 只有3个值，应该是4个
        
        with pytest.raises(SpatialServiceError, match="bbox.*必须包含4个值"):
            spatial_service.get_obstacles(level_id=level_id, bbox=invalid_bbox)
    
    def test_get_obstacles_invalid_bbox_range(self, spatial_service):
        """测试无效的bbox范围（min_x >= max_x 或 min_y >= max_y）"""
        level_id = "level_1"
        invalid_bbox = [10.0, 0.0, 0.0, 10.0]  # min_x >= max_x
        
        # Mock client.execute_query 以避免实际数据库查询
        spatial_service.client.execute_query = Mock(return_value=[])
        
        with pytest.raises(SpatialServiceError, match="bbox.*范围无效"):
            spatial_service.get_obstacles(level_id=level_id, bbox=invalid_bbox)
