"""构件 API 测试"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.utils.memgraph import MemgraphClient
from app.services.schema import initialize_schema
from app.services.ingestion import IngestionService
from app.models.speckle.base import Geometry


client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    """设置测试数据库"""
    memgraph_client = MemgraphClient()
    initialize_schema(memgraph_client)
    yield
    # 清理测试数据（如果需要）


@pytest.fixture
def test_element_id():
    """创建测试构件并返回 ID"""
    memgraph_client = MemgraphClient()
    ingestion_service = IngestionService(memgraph_client)
    
    # 创建一个测试 Speckle Wall 元素
    from app.models.speckle.architectural import Wall
    
    wall = Wall(
        speckle_type="Wall",
        geometry=Geometry(
            type="Polyline",
            coordinates=[[0, 0, 0], [10, 0, 0], [10, 5, 0], [0, 5, 0], [0, 0, 0]],
            closed=True
        ),
        level_id="level_default_test_project_001",
    )
    
    element = ingestion_service.ingest_speckle_element(wall, "test_project_001")
    return element.id


def test_get_elements(test_element_id):
    """测试获取构件列表"""
    response = client.get("/api/v1/elements")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "data" in data
    assert "items" in data["data"]
    assert "total" in data["data"]


def test_get_element(test_element_id):
    """测试获取构件详情"""
    response = client.get(f"/api/v1/elements/{test_element_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "data" in data
    assert data["data"]["id"] == test_element_id


def test_get_element_not_found():
    """测试获取不存在的构件"""
    response = client.get("/api/v1/elements/nonexistent_element")
    assert response.status_code == 404


def test_update_element(test_element_id):
    """测试更新构件参数（Lift Mode）"""
    update_data = {
        "height": 3.5,
        "base_offset": 0.1,
        "material": "concrete"
    }
    response = client.patch(f"/api/v1/elements/{test_element_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "data" in data
    assert "updated_fields" in data["data"]


def test_batch_lift_elements(test_element_id):
    """测试批量设置 Z 轴参数"""
    batch_data = {
        "element_ids": [test_element_id],
        "height": 3.0,
        "base_offset": 0.0,
        "material": "brick"
    }
    response = client.post("/api/v1/elements/batch-lift", json=batch_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "data" in data
    assert data["data"]["updated_count"] >= 0


def test_get_unassigned_elements():
    """测试获取未分配构件列表"""
    response = client.get("/api/v1/elements/unassigned")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "data" in data
    assert "items" in data["data"]


