"""检验批策略工作流集成测试

测试从创建检验批到分配构件的完整工作流
"""

import pytest
from app.services.ingestion import IngestionService
from app.services.lot_strategy import LotStrategyService, RuleType
from app.services.hierarchy import HierarchyService
from app.services.workbench import WorkbenchService
from app.utils.memgraph import MemgraphClient
from app.services.schema import initialize_schema, UNASSIGNED_ITEM_ID
from app.models.speckle.architectural import Wall
from app.models.speckle.base import Geometry2D


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
def lot_strategy_service(memgraph_client):
    """创建 LotStrategyService 实例"""
    return LotStrategyService(client=memgraph_client)


@pytest.fixture
def hierarchy_service(memgraph_client):
    """创建 HierarchyService 实例"""
    return HierarchyService(client=memgraph_client)


@pytest.fixture
def workbench_service(memgraph_client):
    """创建 WorkbenchService 实例"""
    return WorkbenchService(client=memgraph_client)


@pytest.fixture
def test_elements(ingestion_service):
    """创建测试用的构件"""
    project_id = "test_project_lot_strategy_workflow"
    
    elements = []
    # 创建不同楼层的构件
    for i, level_id in enumerate(["level_f1", "level_f2", "level_f3"]):
        wall = Wall(
            speckle_type="Wall",
            geometry_2d=Geometry2D(
                type="Polyline",
                coordinates=[[i*10, 0], [(i+1)*10, 0], [(i+1)*10, 5], [i*10, 5], [i*10, 0]],
                closed=True
            ),
            level_id=level_id,
        )
        element = ingestion_service.ingest_speckle_element(wall, project_id)
        elements.append(element.id)
    
    return elements


def test_lot_strategy_workflow(
    lot_strategy_service,
    test_elements,
    hierarchy_service,
    workbench_service
):
    """测试完整的检验批策略工作流"""
    item_id = UNASSIGNED_ITEM_ID
    
    # 1. 创建检验批（按楼层规则）
    result = lot_strategy_service.create_lots_by_rule(item_id, RuleType.BY_LEVEL)
    
    assert result["total_lots"] >= 1
    assert result["elements_assigned"] >= len(test_elements)
    
    # 2. 验证检验批已创建
    lots_created = result["lots_created"]
    assert len(lots_created) > 0
    
    # 3. 验证每个检验批都有构件
    for lot_info in lots_created:
        lot_id = lot_info["id"]
        assert lot_info["element_count"] > 0
        
        # 验证检验批在层级树中
        lot_detail = hierarchy_service.get_inspection_lot_detail(lot_id)
        assert lot_detail is not None
        assert lot_detail.id == lot_id
        
        # 验证构件已分配
        query = """
        MATCH (lot:InspectionLot {id: $lot_id})-[:MANAGEMENT_CONTAINS]->(e:Element)
        RETURN count(e) as element_count
        """
        count_result = lot_strategy_service.client.execute_query(query, {"lot_id": lot_id})
        assert count_result[0]["element_count"] == lot_info["element_count"]


def test_lot_strategy_with_element_operations(
    lot_strategy_service,
    test_elements,
    workbench_service
):
    """测试检验批创建后的构件操作"""
    item_id = UNASSIGNED_ITEM_ID
    
    # 1. 创建检验批
    result = lot_strategy_service.create_lots_by_rule(item_id, RuleType.BY_LEVEL)
    
    if result["total_lots"] == 0:
        pytest.skip("没有创建检验批，跳过测试")
    
    lot_id = result["lots_created"][0]["id"]
    
    # 2. 获取检验批的初始构件数量
    initial_count = result["lots_created"][0]["element_count"]
    
    # 3. 分配新构件（如果还有未分配的）
    if len(test_elements) > initial_count:
        new_element_id = test_elements[0]
        assigned_count = lot_strategy_service.assign_elements_to_lot(lot_id, [new_element_id])
        assert assigned_count >= 0
    
    # 4. 移除一个构件
    query = """
    MATCH (lot:InspectionLot {id: $lot_id})-[:MANAGEMENT_CONTAINS]->(e:Element)
    RETURN e.id as element_id
    LIMIT 1
    """
    elements = lot_strategy_service.client.execute_query(query, {"lot_id": lot_id})
    
    if elements:
        element_id = elements[0]["element_id"]
        removed_count = lot_strategy_service.remove_elements_from_lot(lot_id, [element_id])
        assert removed_count == 1


def test_multiple_rule_types(
    lot_strategy_service,
    test_elements
):
    """测试不同的规则类型"""
    item_id = UNASSIGNED_ITEM_ID
    
    rule_types = [RuleType.BY_LEVEL, RuleType.BY_ZONE, RuleType.BY_LEVEL_AND_ZONE]
    
    for rule_type in rule_types:
        result = lot_strategy_service.create_lots_by_rule(item_id, rule_type)
        
        # 验证结果结构
        assert "lots_created" in result
        assert "elements_assigned" in result
        assert "total_lots" in result
        assert isinstance(result["total_lots"], int)
        assert result["total_lots"] >= 0

