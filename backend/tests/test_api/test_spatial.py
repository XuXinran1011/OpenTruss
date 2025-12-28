"""空间管理 API 集成测试

测试空间管理相关的 API 端点
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.utils.memgraph import MemgraphClient
from app.services.schema import initialize_schema
from app.models.speckle.spatial import Space
from app.models.speckle.base import Geometry
from app.models.gb50300.relationships import LOCATED_AT

client = TestClient(app)


@pytest.fixture(scope="module")
def memgraph_client():
    """创建 Memgraph 客户端"""
    try:
        client = MemgraphClient()
        initialize_schema(client)
        return client
    except Exception as e:
        pytest.skip(f"Memgraph 连接失败，跳过测试: {e}")


@pytest.fixture
def test_space(memgraph_client):
    """创建测试用的Space元素"""
    space_id = "test_space_api_001"
    level_id = "test_level_api_001"
    
    # 创建Level（如果不存在）
    level_query = """
    MERGE (level:Level {id: $level_id})
    SET level.name = 'Test Level',
        level.elevation = 0.0,
        level.created_at = datetime(),
        level.updated_at = datetime()
    RETURN level
    """
    memgraph_client.execute_write(level_query, {"level_id": level_id})
    
    # 创建Space
    space_geometry = {
        "type": "Polyline",
        "coordinates": [[0.0, 0.0, 0.0], [10.0, 0.0, 0.0], [10.0, 10.0, 0.0], [0.0, 10.0, 0.0], [0.0, 0.0, 0.0]],
        "closed": True
    }
    
    space_query = """
    MERGE (space:Element {id: $space_id})
    SET space.speckle_type = 'Space',
        space.geometry = $geometry,
        space.level_id = $level_id,
        space.forbid_horizontal_mep = false,
        space.forbid_vertical_mep = false,
        space.use_integrated_hanger = false,
        space.created_at = datetime(),
        space.updated_at = datetime()
    RETURN space
    """
    memgraph_client.execute_write(space_query, {
        "space_id": space_id,
        "level_id": level_id,
        "geometry": space_geometry
    })
    
    # 创建LOCATED_AT关系
    rel_query = """
    MATCH (space:Element {id: $space_id}), (level:Level {id: $level_id})
    MERGE (space)-[:LOCATED_AT]->(level)
    """
    memgraph_client.execute_write(rel_query, {
        "space_id": space_id,
        "level_id": level_id
    })
    
    yield space_id
    
    # 清理
    memgraph_client.execute_write(
        "MATCH (space:Element {id: $space_id}) DETACH DELETE space",
        {"space_id": space_id}
    )
    memgraph_client.execute_write(
        "MATCH (level:Level {id: $level_id}) DETACH DELETE level",
        {"level_id": level_id}
    )


class TestSetSpaceMepRestrictions:
    """测试设置空间MEP限制API"""
    
    def test_set_space_mep_restrictions_success(self, test_space):
        """测试成功设置空间MEP限制"""
        response = client.put(
            f"/api/v1/spaces/{test_space}/mep-restrictions",
            json={
                "forbid_horizontal_mep": True,
                "forbid_vertical_mep": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["space_id"] == test_space
        assert data["data"]["forbid_horizontal_mep"] is True
        assert data["data"]["forbid_vertical_mep"] is False
        assert "updated_at" in data["data"]
    
    def test_set_space_mep_restrictions_not_found(self):
        """测试空间不存在的情况"""
        response = client.put(
            "/api/v1/spaces/nonexistent_space/mep-restrictions",
            json={
                "forbid_horizontal_mep": True,
                "forbid_vertical_mep": False
            }
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestGetSpaceMepRestrictions:
    """测试获取空间MEP限制API"""
    
    def test_get_space_mep_restrictions_success(self, test_space):
        """测试成功获取空间MEP限制"""
        response = client.get(f"/api/v1/spaces/{test_space}/mep-restrictions")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["space_id"] == test_space
        assert "forbid_horizontal_mep" in data["data"]
        assert "forbid_vertical_mep" in data["data"]
    
    def test_get_space_mep_restrictions_not_found(self):
        """测试空间不存在的情况"""
        response = client.get("/api/v1/spaces/nonexistent_space/mep-restrictions")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestSetSpaceIntegratedHanger:
    """测试设置空间综合支吊架API"""
    
    def test_set_space_integrated_hanger_success(self, test_space):
        """测试成功设置空间综合支吊架"""
        response = client.put(
            f"/api/v1/spaces/{test_space}/integrated-hanger",
            json={
                "use_integrated_hanger": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["space_id"] == test_space
        assert data["data"]["use_integrated_hanger"] is True
        assert "updated_at" in data["data"]
    
    def test_set_space_integrated_hanger_not_found(self):
        """测试空间不存在的情况"""
        response = client.put(
            "/api/v1/spaces/nonexistent_space/integrated-hanger",
            json={
                "use_integrated_hanger": True
            }
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestGetSpaceIntegratedHanger:
    """测试获取空间综合支吊架API"""
    
    def test_get_space_integrated_hanger_success(self, test_space):
        """测试成功获取空间综合支吊架配置"""
        response = client.get(f"/api/v1/spaces/{test_space}/integrated-hanger")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["space_id"] == test_space
        assert "use_integrated_hanger" in data["data"]
    
    def test_get_space_integrated_hanger_not_found(self):
        """测试空间不存在的情况"""
        response = client.get("/api/v1/spaces/nonexistent_space/integrated-hanger")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
