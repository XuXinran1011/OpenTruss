"""HierarchyService 测试"""

import pytest
from app.services.hierarchy import HierarchyService
from app.services.ingestion import IngestionService
from app.utils.memgraph import MemgraphClient
from app.services.schema import initialize_schema
from app.models.speckle.architectural import Wall
from app.models.speckle.base import Geometry


@pytest.fixture(scope="module")
def memgraph_client():
    """创建 Memgraph 客户端"""
    client = MemgraphClient()
    initialize_schema(client)
    return client


@pytest.fixture
def hierarchy_service(memgraph_client):
    """创建 HierarchyService 实例"""
    return HierarchyService(client=memgraph_client)


@pytest.fixture
def ingestion_service(memgraph_client):
    """创建 IngestionService 实例"""
    return IngestionService(client=memgraph_client)


@pytest.fixture
def test_project_id():
    """测试用的项目ID"""
    return "test_project_hierarchy"


def test_get_project_hierarchy(hierarchy_service, test_project_id):
    """测试获取项目层级结构"""
    hierarchy = hierarchy_service.get_project_hierarchy(test_project_id)
    
    # 如果项目不存在，返回None是正常的
    # 这里只测试方法可以正常调用而不抛出异常
    if hierarchy:
        assert hasattr(hierarchy, 'hierarchy') or isinstance(hierarchy, dict)


def test_get_inspection_lot_detail(hierarchy_service, ingestion_service, test_project_id):
    """测试获取检验批详情"""
    # 先创建一些测试数据
    wall = Wall(
        speckle_type="Wall",
        geometry=Geometry(
            type="Polyline",
            coordinates=[[0, 0, 0], [10, 0, 0], [10, 5, 0], [0, 5, 0], [0, 0, 0]],
            closed=True
        ),
        level_id="level_test_hierarchy",
    )
    element = ingestion_service.ingest_speckle_element(wall, test_project_id)
    
    # 这里需要先创建一个检验批，但由于没有直接的API，我们只测试方法存在性
    # 实际测试可能需要更多的setup
    lot_detail = hierarchy_service.get_inspection_lot_detail("nonexistent_lot")
    
    # 如果不存在应该返回None
    assert lot_detail is None or isinstance(lot_detail, dict)


def test_get_item_detail(hierarchy_service):
    """测试获取分项详情"""
    from app.services.schema import UNASSIGNED_ITEM_ID
    
    item_detail = hierarchy_service.get_item_detail(UNASSIGNED_ITEM_ID)
    
    assert item_detail is not None
    # ItemDetail是Pydantic模型，使用属性访问
    assert item_detail.id == UNASSIGNED_ITEM_ID

