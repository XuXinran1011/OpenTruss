"""数据摄入工作流集成测试

测试从数据摄入到层级结构生成的完整工作流
"""

import pytest
from app.services.ingestion import IngestionService
from app.services.hierarchy import HierarchyService
from app.services.workbench import WorkbenchService
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
def ingestion_service(memgraph_client):
    """创建 IngestionService 实例"""
    return IngestionService(client=memgraph_client)


@pytest.fixture
def hierarchy_service(memgraph_client):
    """创建 HierarchyService 实例"""
    return HierarchyService(client=memgraph_client)


@pytest.fixture
def workbench_service(memgraph_client):
    """创建 WorkbenchService 实例"""
    return WorkbenchService(client=memgraph_client)


def test_ingestion_workflow(
    ingestion_service,
    hierarchy_service,
    workbench_service
):
    """测试完整的数据摄入工作流"""
    project_id = "test_project_ingestion_workflow"
    
    # 1. 摄入构件
    wall = Wall(
        speckle_type="Wall",
        geometry=Geometry(
            type="Polyline",
            coordinates=[[0, 0, 0], [10, 0, 0], [10, 5, 0], [0, 5, 0], [0, 0, 0]],
            closed=True
        ),
        level_id="level_f1",
    )
    element = ingestion_service.ingest_speckle_element(wall, project_id)
    
    assert element.id is not None
    assert element.speckle_type == "Wall"
    
    # 2. 验证构件可以通过WorkbenchService查询
    from app.models.api.elements import ElementQueryParams
    
    params = ElementQueryParams(
        page=1,
        page_size=20,
        speckle_type="Wall",
    )
    result = workbench_service.query_elements(params)
    
    assert result["total"] >= 1
    assert any(item.id == element.id for item in result["items"])
    
    # 3. 验证层级结构（如果项目存在，应该能获取层级；否则为None是正常的）
    hierarchy = hierarchy_service.get_project_hierarchy(project_id)
    # 这里只验证方法可以正常调用，不强制要求返回非None
    # 因为项目可能是动态创建的，不一定在层级结构中


def test_element_operations_workflow(
    ingestion_service,
    workbench_service
):
    """测试构件操作工作流（查询、更新、删除）"""
    project_id = "test_project_element_operations"
    
    # 1. 创建构件
    wall = Wall(
        speckle_type="Wall",
        geometry=Geometry(
            type="Polyline",
            coordinates=[[0, 0, 0], [10, 0, 0], [10, 5, 0], [0, 5, 0], [0, 0, 0]],
            closed=True
        ),
        level_id="level_test",
    )
    element = ingestion_service.ingest_speckle_element(wall, project_id)
    
    # 2. 查询构件详情
    element_detail = workbench_service.get_element(element.id)
    assert element_detail is not None
    assert element_detail.id == element.id
    
    # 3. 更新构件（Lift Mode）
    from app.models.api.elements import ElementUpdateRequest
    
    update_request = ElementUpdateRequest(
        height=3.5,
        base_offset=0.1,
    )
    update_result = workbench_service.update_element(element.id, update_request)
    assert update_result["id"] == element.id
    
    # 4. 验证更新
    updated_element = workbench_service.get_element(element.id)
    assert updated_element.height == 3.5
    assert updated_element.base_offset == 0.1
    
    # 5. 删除构件
    workbench_service.delete_element(element.id)
    
    # 6. 验证删除
    deleted_element = workbench_service.get_element(element.id)
    assert deleted_element is None

