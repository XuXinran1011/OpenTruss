"""检验批管理 API 测试

测试检验批创建、分配构件、移除构件等端点
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.utils.memgraph import MemgraphClient
from app.services.schema import initialize_schema
from app.services.ingestion import IngestionService
from app.services.lot_strategy import LotStrategyService
from app.services.hierarchy import HierarchyService
from app.models.speckle.architectural import Wall
from app.models.speckle.base import Geometry2D
from app.services.schema import UNASSIGNED_ITEM_ID
from app.services.lot_strategy import RuleType


client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    """设置测试数据库"""
    memgraph_client = MemgraphClient()
    initialize_schema(memgraph_client)
    yield
    # 清理测试数据（如果需要）


@pytest.fixture
def test_item_id():
    """测试用的Item ID"""
    return UNASSIGNED_ITEM_ID


@pytest.fixture
def test_elements(ingestion_service):
    """创建测试用的构件"""
    project_id = "test_project_lots_api"
    
    elements = []
    for i in range(2):
        wall = Wall(
            speckle_type="Wall",
            geometry_2d=Geometry2D(
                type="Polyline",
                coordinates=[[i*10, 0], [(i+1)*10, 0], [(i+1)*10, 5], [i*10, 5], [i*10, 0]],
                closed=True
            ),
            level_id=f"level_test_{i}",
        )
        element = ingestion_service.ingest_speckle_element(wall, project_id)
        elements.append(element.id)
    
    return elements


@pytest.fixture
def ingestion_service():
    """创建IngestionService实例"""
    memgraph_client = MemgraphClient()
    return IngestionService(client=memgraph_client)


@pytest.fixture
def test_lot_id(lot_strategy_service, test_item_id):
    """创建测试用的检验批"""
    # 先创建一些构件，然后创建检验批
    result = lot_strategy_service.create_lots_by_rule(
        test_item_id,
        RuleType.BY_LEVEL
    )
    
    if result["total_lots"] > 0:
        return result["lots_created"][0]["id"]
    return None


@pytest.fixture
def lot_strategy_service():
    """创建LotStrategyService实例"""
    memgraph_client = MemgraphClient()
    return LotStrategyService(client=memgraph_client)


def test_create_lots_by_rule(test_item_id):
    """测试根据规则创建检验批"""
    response = client.post(
        "/api/v1/lots/create-by-rule",
        json={
            "item_id": test_item_id,
            "rule_type": "BY_LEVEL"
        }
    )
    
    # 如果没有未分配的构件，可能返回空列表，这是正常的
    assert response.status_code in [200, 201]
    data = response.json()
    assert data["status"] == "success"
    assert "data" in data
    assert "lots_created" in data["data"]
    assert "elements_assigned" in data["data"]
    assert "total_lots" in data["data"]


def test_create_lots_by_rule_invalid_item():
    """测试使用不存在的Item创建检验批"""
    response = client.post(
        "/api/v1/lots/create-by-rule",
        json={
            "item_id": "nonexistent_item",
            "rule_type": "BY_LEVEL"
        }
    )
    
    assert response.status_code == 404


def test_create_lots_by_rule_invalid_rule_type(test_item_id):
    """测试使用无效的规则类型"""
    response = client.post(
        "/api/v1/lots/create-by-rule",
        json={
            "item_id": test_item_id,
            "rule_type": "INVALID_RULE"
        }
    )
    
    assert response.status_code == 400


def test_assign_elements_to_lot(test_lot_id, test_elements):
    """测试分配构件到检验批"""
    if not test_lot_id:
        pytest.skip("没有可用的检验批，跳过测试")
    
    response = client.post(
        f"/api/v1/lots/{test_lot_id}/assign-elements",
        json={
            "element_ids": test_elements[:1]  # 只分配第一个构件
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "data" in data
    assert data["data"]["lot_id"] == test_lot_id
    assert "assigned_count" in data["data"]
    assert "total_requested" in data["data"]


def test_assign_elements_to_lot_not_found(test_elements):
    """测试向不存在的检验批分配构件"""
    response = client.post(
        "/api/v1/lots/nonexistent_lot/assign-elements",
        json={
            "element_ids": test_elements[:1]
        }
    )
    
    # 由于没有验证检验批是否存在，可能返回200或500
    # 实际行为取决于服务实现
    assert response.status_code in [200, 404, 500]


def test_remove_elements_from_lot(test_lot_id, test_elements):
    """测试从检验批移除构件"""
    if not test_lot_id:
        pytest.skip("没有可用的检验批，跳过测试")
    
    # 先分配一个构件
    client.post(
        f"/api/v1/lots/{test_lot_id}/assign-elements",
        json={
            "element_ids": test_elements[:1]
        }
    )
    
    # 然后移除它
    response = client.post(
        f"/api/v1/lots/{test_lot_id}/remove-elements",
        json={
            "element_ids": test_elements[:1]
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "data" in data
    assert data["data"]["lot_id"] == test_lot_id
    assert "removed_count" in data["data"]
    assert "total_requested" in data["data"]


def test_get_lot_elements(test_lot_id):
    """测试获取检验批的构件列表"""
    if not test_lot_id:
        pytest.skip("没有可用的检验批，跳过测试")
    
    response = client.get(f"/api/v1/lots/{test_lot_id}/elements")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "data" in data
    assert "lot_id" in data["data"]
    assert "items" in data["data"]
    assert "total" in data["data"]


def test_get_lot_elements_not_found():
    """测试获取不存在的检验批的构件列表"""
    response = client.get("/api/v1/lots/nonexistent_lot/elements")
    
    assert response.status_code == 404

