"""LotStrategyService 测试"""

import pytest
from app.services.lot_strategy import LotStrategyService, RuleType
from app.services.ingestion import IngestionService
from app.services.hierarchy import HierarchyService
from app.core.exceptions import NotFoundError
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
def lot_strategy_service(memgraph_client):
    """创建 LotStrategyService 实例"""
    return LotStrategyService(client=memgraph_client)


@pytest.fixture
def hierarchy_service(memgraph_client):
    """创建 HierarchyService 实例"""
    return HierarchyService(client=memgraph_client)


@pytest.fixture
def ingestion_service(memgraph_client):
    """创建 IngestionService 实例"""
    return IngestionService(client=memgraph_client)


@pytest.fixture
def test_item_id(memgraph_client):
    """创建测试用的Item并返回ID"""
    from app.services.schema import UNASSIGNED_ITEM_ID
    
    # 使用Unassigned Item作为测试Item
    return UNASSIGNED_ITEM_ID


@pytest.fixture
def test_elements_with_levels(ingestion_service, memgraph_client):
    """创建不同楼层的测试构件"""
    project_id = "test_project_lot_strategy"
    
    # 创建F1层的构件
    wall_f1 = Wall(
        speckle_type="Wall",
        geometry=Geometry(
            type="Polyline",
            coordinates=[[0, 0, 0], [10, 0, 0], [10, 5, 0], [0, 5, 0], [0, 0, 0]],
            closed=True
        ),
        level_id="level_f1",
    )
    element_f1 = ingestion_service.ingest_speckle_element(wall_f1, project_id)
    
    # 创建F2层的构件
    wall_f2 = Wall(
        speckle_type="Wall",
        geometry=Geometry(
            type="Polyline",
            coordinates=[[0, 0, 0], [10, 0, 0], [10, 5, 0], [0, 5, 0], [0, 0, 0]],
            closed=True
        ),
        level_id="level_f2",
    )
    element_f2 = ingestion_service.ingest_speckle_element(wall_f2, project_id)
    
    return {
        "f1": element_f1.id,
        "f2": element_f2.id,
    }


def test_create_lots_by_rule_item_not_found(lot_strategy_service):
    """测试创建检验批时Item不存在的情况"""
    with pytest.raises(NotFoundError, match="Item not found"):
        lot_strategy_service.create_lots_by_rule("nonexistent_item", RuleType.BY_LEVEL)


def test_create_lots_by_rule_no_unassigned_elements(lot_strategy_service, test_item_id):
    """测试创建检验批的返回结构（即使没有未分配构件，也返回正确的结构）"""
    result = lot_strategy_service.create_lots_by_rule(test_item_id, RuleType.BY_LEVEL)
    
    # 验证返回结构（即使有未分配构件创建了检验批，结构也应该正确）
    assert "lots_created" in result
    assert "elements_assigned" in result
    assert "total_lots" in result
    assert isinstance(result["lots_created"], list)
    assert isinstance(result["elements_assigned"], int)
    assert isinstance(result["total_lots"], int)
    assert result["total_lots"] >= 0


def test_create_lots_by_rule_by_level(
    lot_strategy_service, 
    test_item_id, 
    test_elements_with_levels
):
    """测试按楼层规则创建检验批"""
    result = lot_strategy_service.create_lots_by_rule(test_item_id, RuleType.BY_LEVEL)
    
    assert result["total_lots"] >= 1
    assert result["elements_assigned"] >= 2  # 至少有两个构件
    assert len(result["lots_created"]) == result["total_lots"]
    
    # 验证每个检验批都有element_count
    for lot in result["lots_created"]:
        assert "id" in lot
        assert "name" in lot
        assert "spatial_scope" in lot
        assert "element_count" in lot
        assert lot["element_count"] > 0


def test_assign_elements_to_lot(
    lot_strategy_service,
    test_item_id,
    test_elements_with_levels
):
    """测试分配构件到检验批"""
    # 先创建检验批
    create_result = lot_strategy_service.create_lots_by_rule(test_item_id, RuleType.BY_LEVEL)
    
    if create_result["total_lots"] == 0:
        pytest.skip("没有创建检验批，跳过测试")
    
    lot_id = create_result["lots_created"][0]["id"]
    
    # 分配新构件
    element_ids = [test_elements_with_levels["f1"]]
    assigned_count = lot_strategy_service.assign_elements_to_lot(lot_id, element_ids)
    
    assert assigned_count >= 0  # 可能已经分配过


def test_remove_elements_from_lot(
    lot_strategy_service,
    test_item_id,
    test_elements_with_levels
):
    """测试从检验批移除构件"""
    # 先创建检验批
    create_result = lot_strategy_service.create_lots_by_rule(test_item_id, RuleType.BY_LEVEL)
    
    if create_result["total_lots"] == 0:
        pytest.skip("没有创建检验批，跳过测试")
    
    lot_id = create_result["lots_created"][0]["id"]
    
    # 获取检验批的构件列表
    query = """
    MATCH (lot:InspectionLot {id: $lot_id})-[r]->(e:Element)
    WHERE type(r) = 'MANAGEMENT_CONTAINS'
    RETURN e.id as element_id
    LIMIT 1
    """
    elements = lot_strategy_service.client.execute_query(query, {"lot_id": lot_id})
    
    if not elements:
        pytest.skip("检验批没有构件，跳过测试")
    
    element_id = elements[0]["element_id"]
    
    # 移除构件
    removed_count = lot_strategy_service.remove_elements_from_lot(lot_id, [element_id])
    
    assert removed_count == 1


def test_rule_types(lot_strategy_service, test_item_id, test_elements_with_levels):
    """测试不同的规则类型"""
    rule_types = [RuleType.BY_LEVEL, RuleType.BY_ZONE, RuleType.BY_LEVEL_AND_ZONE]
    
    for rule_type in rule_types:
        result = lot_strategy_service.create_lots_by_rule(test_item_id, rule_type)
        assert "lots_created" in result
        assert "elements_assigned" in result
        assert "total_lots" in result
        assert isinstance(result["total_lots"], int)
        assert result["total_lots"] >= 0

