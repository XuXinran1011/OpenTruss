"""Ingestion Service 测试"""

import pytest
from datetime import datetime
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
def ingestion_service(memgraph_client):
    """创建 IngestionService 实例"""
    return IngestionService(client=memgraph_client)


@pytest.fixture
def sample_wall():
    """创建示例 Wall 元素"""
    return Wall(
        speckle_type="Wall",
        geometry=Geometry(
            type="Polyline",
            coordinates=[[0, 0, 0], [10, 0, 0], [10, 5, 0], [0, 5, 0], [0, 0, 0]],
            closed=True
        ),
        level_id="level_test_f1",
        speckle_id="speckle_wall_test_001",
    )


def test_ingest_speckle_element_success(ingestion_service, sample_wall):
    """测试成功摄入 Speckle 元素"""
    project_id = "test_project_ingestion"
    
    # 先创建 Level（如果不存在）
    from app.models.gb50300.nodes import LevelNode, BuildingNode
    from app.models.gb50300.relationships import PHYSICALLY_CONTAINS
    
    level_id = "level_test_f1"
    level_query = "MATCH (l:Level {id: $level_id}) RETURN l.id as id"
    level_result = ingestion_service.client.execute_query(level_query, {"level_id": level_id})
    
    if not level_result:
        # 创建默认 Building（如果不存在）
        building_id = f"building_default_{project_id}"
        building_query = "MATCH (b:Building {id: $building_id}) RETURN b.id as id"
        building_result = ingestion_service.client.execute_query(building_query, {"building_id": building_id})
        
        if not building_result:
            building = BuildingNode(
                id=building_id,
                name="默认单体",
                project_id=project_id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            ingestion_service.client.create_node("Building", building.model_dump(exclude_none=True))
            ingestion_service.client.create_relationship(
                "Project", project_id,
                "Building", building_id,
                PHYSICALLY_CONTAINS
            )
        
        # 创建 Level
        level = LevelNode(
            id=level_id,
            name="测试楼层",
            elevation=0.0,
            building_id=building_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        ingestion_service.client.create_node("Level", level.model_dump(exclude_none=True))
        ingestion_service.client.create_relationship(
            "Building", building_id,
            "Level", level_id,
            PHYSICALLY_CONTAINS
        )
    
    element = ingestion_service.ingest_speckle_element(sample_wall, project_id)
    
    assert element is not None
    assert element.id is not None
    assert element.speckle_type == "Wall"
    assert element.level_id == "level_test_f1"
    assert element.inspection_lot_id is None  # 未分配


def test_ingest_element_without_inspection_lot(ingestion_service, sample_wall):
    """测试摄入未分配检验批的元素（宽进严出策略）"""
    project_id = "test_project_ingestion"
    
    # 不设置 inspection_lot_id
    element = ingestion_service.ingest_speckle_element(sample_wall, project_id)
    
    assert element.inspection_lot_id is None
    # 应该成功创建，即使没有 inspection_lot_id


def test_ingest_element_with_missing_geometry(ingestion_service):
    """测试摄入缺少几何数据的元素（应该失败）"""
    project_id = "test_project_ingestion"
    
    # 创建一个模拟的 Speckle 元素，没有 geometry_2d 属性
    # 由于 Wall 模型会验证 geometry_2d，我们创建一个简单的对象来模拟
    class MockSpeckleElement:
        speckle_type = "Wall"
        level_id = "level_test_f1"
        # 没有 geometry_2d 属性
    
    mock_element = MockSpeckleElement()
    
    with pytest.raises(ValueError, match="无法从 Speckle 元素提取 geometry"):
        ingestion_service.ingest_speckle_element(mock_element, project_id)


def test_ingest_element_creates_default_level(ingestion_service, sample_wall):
    """测试摄入元素时自动创建默认 Level"""
    project_id = "test_project_new"
    
    # 使用不存在的 level_id
    wall_new_level = Wall(
        speckle_type="Wall",
        geometry=Geometry(
            type="Polyline",
            coordinates=[[0, 0, 0], [5, 0, 0], [5, 3, 0], [0, 3, 0], [0, 0, 0]],
            closed=True
        ),
        level_id="level_nonexistent",
    )
    
    element = ingestion_service.ingest_speckle_element(wall_new_level, project_id)
    
    # 应该创建默认 Level
    assert element.level_id is not None
    # 验证默认 Level 是否存在
    query = "MATCH (l:Level {id: $level_id}) RETURN l.id as id"
    result = ingestion_service.client.execute_query(query, {"level_id": element.level_id})
    assert len(result) > 0


def test_ingest_element_creates_relationships(ingestion_service, sample_wall):
    """测试摄入元素时创建正确的关系"""
    project_id = "test_project_relationships"
    
    element = ingestion_service.ingest_speckle_element(sample_wall, project_id)
    
    # 验证 LOCATED_AT 关系
    query = """
    MATCH (e:Element {id: $element_id})-[r:LOCATED_AT]->(l:Level)
    RETURN l.id as level_id
    """
    result = ingestion_service.client.execute_query(query, {"element_id": element.id})
    assert len(result) > 0
    assert result[0]["level_id"] == element.level_id
    
    # 验证 PHYSICALLY_CONTAINS 关系
    query = """
    MATCH (l:Level)-[r:PHYSICALLY_CONTAINS]->(e:Element {id: $element_id})
    RETURN l.id as level_id
    """
    result = ingestion_service.client.execute_query(query, {"element_id": element.id})
    assert len(result) > 0


def test_ingest_element_with_inspection_lot(ingestion_service, sample_wall):
    """测试摄入已分配检验批的元素"""
    project_id = "test_project_with_lot"
    
    # 先创建一个 InspectionLot
    from app.models.gb50300.nodes import InspectionLotNode
    from datetime import datetime
    
    lot_id = "test_lot_for_ingestion"
    lot = InspectionLotNode(
        id=lot_id,
        name="测试检验批",
        item_id="test_item_001",
        status="PLANNING",
        spatial_scope="Level:F1",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    ingestion_service.client.create_node("InspectionLot", lot.model_dump(exclude_none=True))
    
    # 设置 inspection_lot_id
    sample_wall.inspection_lot_id = lot_id
    
    element = ingestion_service.ingest_speckle_element(sample_wall, project_id)
    
    assert element.inspection_lot_id == lot_id
    
    # 验证 MANAGEMENT_CONTAINS 关系
    query = """
    MATCH (lot:InspectionLot {id: $lot_id})-[r]->(e:Element {id: $element_id})
    WHERE type(r) = 'MANAGEMENT_CONTAINS'
    RETURN e.id as element_id
    """
    result = ingestion_service.client.execute_query(query, {
        "lot_id": lot_id,
        "element_id": element.id
    })
    assert len(result) > 0

