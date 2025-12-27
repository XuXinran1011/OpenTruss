"""Workbench Service 测试"""

import pytest
from app.services.workbench import WorkbenchService
from app.services.ingestion import IngestionService
from app.utils.memgraph import MemgraphClient
from app.services.schema import initialize_schema
from app.models.speckle.architectural import Wall
from app.models.speckle.base import Geometry
from app.models.api.elements import (
    TopologyUpdateRequest,
    ElementUpdateRequest,
    BatchLiftRequest,
    ClassifyRequest,
)


@pytest.fixture(scope="module")
def memgraph_client():
    """创建 Memgraph 客户端"""
    client = MemgraphClient()
    initialize_schema(client)
    return client


@pytest.fixture
def workbench_service(memgraph_client):
    """创建 WorkbenchService 实例"""
    return WorkbenchService(client=memgraph_client)


@pytest.fixture
def ingestion_service(memgraph_client):
    """创建 IngestionService 实例"""
    return IngestionService(client=memgraph_client)


@pytest.fixture
def test_element(ingestion_service):
    """创建测试用的构件"""
    wall = Wall(
        speckle_type="Wall",
        geometry=Geometry(
            type="Polyline",
            coordinates=[[0, 0, 0], [10, 0, 0], [10, 5, 0], [0, 5, 0], [0, 0, 0]],
            closed=True
        ),
        level_id="level_test_workbench",
    )
    element = ingestion_service.ingest_speckle_element(wall, "test_project_workbench")
    return element.id


def test_query_elements(workbench_service, test_element):
    """测试查询构件列表"""
    from app.models.api.elements import ElementQueryParams
    
    params = ElementQueryParams(
        page=1,
        page_size=20,
    )
    
    result = workbench_service.query_elements(params)
    
    assert "items" in result
    assert "total" in result
    assert result["total"] >= 1
    assert len(result["items"]) >= 1


def test_query_elements_with_filters(workbench_service, test_element):
    """测试带筛选条件的构件查询"""
    from app.models.api.elements import ElementQueryParams
    
    # 按 speckle_type 筛选
    params = ElementQueryParams(
        speckle_type="Wall",
        page=1,
        page_size=20,
    )
    
    result = workbench_service.query_elements(params)
    
    assert result["total"] >= 1
    for item in result["items"]:
        assert item.speckle_type == "Wall"


def test_get_element(workbench_service, test_element):
    """测试获取构件详情"""
    element = workbench_service.get_element(test_element)
    
    assert element is not None
    assert element.id == test_element
    assert element.speckle_type == "Wall"


def test_get_element_not_found(workbench_service):
    """测试获取不存在的构件"""
    element = workbench_service.get_element("nonexistent_element")
    
    assert element is None


def test_get_unassigned_elements(workbench_service, test_element):
    """测试获取未分配构件列表"""
    result = workbench_service.get_unassigned_elements(page=1, page_size=20)
    
    assert "items" in result
    assert "total" in result
    assert result["total"] >= 1


def test_update_element_topology(workbench_service, test_element):
    """测试更新构件拓扑关系（Trace Mode）"""
    new_geometry = Geometry(
        type="Polyline",
        coordinates=[[0, 0, 0], [15, 0, 0], [15, 5, 0], [0, 5, 0], [0, 0, 0]],
        closed=True
    )
    
    request = TopologyUpdateRequest(
        geometry=new_geometry,
        connected_elements=[],
    )
    
    result = workbench_service.update_element_topology(test_element, request)
    
    assert result["id"] == test_element
    assert result["topology_updated"] is True
    
    # 验证几何数据已更新
    element = workbench_service.get_element(test_element)
    assert element.geometry.coordinates == new_geometry.coordinates


def test_update_element_topology_with_connections(workbench_service, ingestion_service):
    """测试更新构件拓扑关系（包含连接关系）"""
    # 创建两个构件
    wall1 = Wall(
        speckle_type="Wall",
        geometry=Geometry(
            type="Polyline",
            coordinates=[[0, 0, 0], [10, 0, 0], [10, 5, 0], [0, 5, 0], [0, 0, 0]],
            closed=True
        ),
        level_id="level_test_workbench",
    )
    element1 = ingestion_service.ingest_speckle_element(wall1, "test_project_workbench")
    
    wall2 = Wall(
        speckle_type="Wall",
        geometry=Geometry(
            type="Polyline",
            coordinates=[[10, 0, 0], [20, 0, 0], [20, 5, 0], [10, 5, 0], [10, 0, 0]],
            closed=True
        ),
        level_id="level_test_workbench",
    )
    element2 = ingestion_service.ingest_speckle_element(wall2, "test_project_workbench")
    
    # 更新拓扑，建立连接关系
    request = TopologyUpdateRequest(
        connected_elements=[element2.id],
    )
    
    result = workbench_service.update_element_topology(element1.id, request)
    
    assert result["topology_updated"] is True
    
    # 验证连接关系已创建
    element = workbench_service.get_element(element1.id)
    assert element2.id in element.connected_elements


def test_update_element_topology_not_found(workbench_service):
    """测试更新不存在的构件拓扑（应该失败）"""
    request = TopologyUpdateRequest(
        connected_elements=[],
    )
    
    with pytest.raises(ValueError, match="Element not found"):
        workbench_service.update_element_topology("nonexistent_element", request)


def test_update_element(workbench_service, test_element):
    """测试更新构件参数（Lift Mode）"""
    request = ElementUpdateRequest(
        height=3.5,
        base_offset=0.1,
        material="concrete",
    )
    
    result = workbench_service.update_element(test_element, request)
    
    assert result["id"] == test_element
    assert "updated_fields" in result
    assert len(result["updated_fields"]) > 0
    
    # 验证数据已更新
    element = workbench_service.get_element(test_element)
    assert element.height == 3.5
    assert element.base_offset == 0.1
    assert element.material == "concrete"


def test_update_element_partial(workbench_service, test_element):
    """测试部分更新构件参数"""
    request = ElementUpdateRequest(
        height=2.5,
        # 不设置 base_offset 和 material
    )
    
    result = workbench_service.update_element(test_element, request)
    
    assert result["id"] == test_element
    # updated_fields 是一个列表，检查是否包含 "height"
    assert any("height" in field for field in result["updated_fields"])
    
    # 验证只有 height 被更新
    element = workbench_service.get_element(test_element)
    assert element.height == 2.5


def test_update_element_not_found(workbench_service):
    """测试更新不存在的构件（应该失败）"""
    request = ElementUpdateRequest(height=3.0)
    
    with pytest.raises(ValueError, match="Element not found"):
        workbench_service.update_element("nonexistent_element", request)


def test_batch_lift_elements(workbench_service, ingestion_service):
    """测试批量设置 Z 轴参数（Lift Mode）"""
    # 创建多个构件
    element_ids = []
    for i in range(3):
        wall = Wall(
            speckle_type="Wall",
            geometry=Geometry(
                type="Polyline",
                coordinates=[[i*10, 0, 0], [(i+1)*10, 0, 0], [(i+1)*10, 5, 0], [i*10, 5, 0], [i*10, 0, 0]],
                closed=True
            ),
            level_id="level_test_workbench",
        )
        element = ingestion_service.ingest_speckle_element(wall, "test_project_workbench")
        element_ids.append(element.id)
    
    request = BatchLiftRequest(
        element_ids=element_ids,
        height=3.0,
        base_offset=0.0,
        material="brick",
    )
    
    result = workbench_service.batch_lift_elements(request)
    
    assert result.updated_count == len(element_ids)
    assert len(result.element_ids) == len(element_ids)
    
    # 验证所有构件都已更新
    for element_id in element_ids:
        element = workbench_service.get_element(element_id)
        assert element.height == 3.0
        assert element.material == "brick"


def test_batch_lift_elements_partial_failure(workbench_service, test_element):
    """测试批量设置 Z 轴参数（部分失败）"""
    request = BatchLiftRequest(
        element_ids=[test_element, "nonexistent_element"],
        height=2.5,
    )
    
    result = workbench_service.batch_lift_elements(request)
    
    # 应该至少更新一个构件
    assert result.updated_count >= 1
    assert test_element in result.element_ids


def test_classify_element(workbench_service, ingestion_service):
    """测试构件归类（Classify Mode）"""
    # 创建测试 Item
    from app.models.gb50300.nodes import ItemNode
    from datetime import datetime
    
    item_id = "item_test_classify"
    item = ItemNode(
        id=item_id,
        name="测试分项",
        subdivision_id="test_subdivision_001",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    workbench_service.client.create_node("Item", item.model_dump(exclude_none=True))
    
    # 创建测试构件
    wall = Wall(
        speckle_type="Wall",
        geometry=Geometry(
            type="Polyline",
            coordinates=[[0, 0, 0], [10, 0, 0], [10, 5, 0], [0, 5, 0], [0, 0, 0]],
            closed=True
        ),
        level_id="level_test_workbench",
    )
    element = ingestion_service.ingest_speckle_element(wall, "test_project_workbench")
    
    # 归类到 Item
    request = ClassifyRequest(item_id=item_id)
    result = workbench_service.classify_element(element.id, request)
    
    assert result.element_id == element.id
    assert result.item_id == item_id
    
    # 验证构件已更新（inspection_lot_id 应为 None）
    updated_element = workbench_service.get_element(element.id)
    assert updated_element.inspection_lot_id is None


def test_classify_element_not_found(workbench_service):
    """测试归类不存在的构件（应该失败）"""
    request = ClassifyRequest(item_id="item_test_001")
    
    with pytest.raises(ValueError, match="Element not found"):
        workbench_service.classify_element("nonexistent_element", request)


def test_classify_element_item_not_found(workbench_service, test_element):
    """测试归类到不存在的 Item（应该失败）"""
    request = ClassifyRequest(item_id="item_nonexistent")
    
    with pytest.raises(ValueError, match="Item not found"):
        workbench_service.classify_element(test_element, request)

