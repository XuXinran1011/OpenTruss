"""导出工作流集成测试

测试完整的导出流程：
1. 数据摄入 → 创建检验批 → 审批 → 导出 IFC
2. 验证 IFC 文件中包含正确的几何和属性
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime

try:
    import ifcopenshell
    IFC_AVAILABLE = True
except ImportError:
    IFC_AVAILABLE = False

from app.services.export import ExportService
from app.services.approval import ApprovalService
from app.services.ingestion import IngestionService
from app.utils.memgraph import MemgraphClient
from app.services.schema import initialize_schema
from app.models.gb50300.nodes import (
    ProjectNode, BuildingNode, DivisionNode, SubDivisionNode,
    ItemNode, InspectionLotNode, LevelNode
)
from app.models.gb50300.element import ElementNode
from app.models.speckle.base import Geometry


@pytest.fixture(scope="module")
def setup_integration_db():
    """设置集成测试数据库"""
    memgraph_client = MemgraphClient()
    initialize_schema(memgraph_client)
    yield memgraph_client


@pytest.fixture
def sample_project_for_export(setup_integration_db):
    """创建用于导出测试的完整项目结构"""
    memgraph_client = setup_integration_db
    
    project_id = "integration_export_project_001"
    building_id = "integration_export_building_001"
    division_id = "integration_export_division_001"
    subdivision_id = "integration_export_subdivision_001"
    item_id = "integration_export_item_001"
    lot_id = "integration_export_lot_001"
    level_id = "integration_export_level_001"
    
    # 创建项目层级
    project = ProjectNode(
        id=project_id,
        name="导出集成测试项目",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    memgraph_client.create_node("Project", project.model_dump(exclude_none=True))
    
    building = BuildingNode(
        id=building_id,
        name="导出集成测试建筑",
        project_id=project_id,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    memgraph_client.create_node("Building", building.model_dump(exclude_none=True))
    memgraph_client.create_relationship("Project", project_id, "Building", building_id, "HAS_BUILDING")
    
    division = DivisionNode(
        id=division_id,
        name="导出集成测试分部",
        building_id=building_id,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    memgraph_client.create_node("Division", division.model_dump(exclude_none=True))
    memgraph_client.create_relationship("Building", building_id, "Division", division_id, "HAS_DIVISION")
    
    subdivision = SubDivisionNode(
        id=subdivision_id,
        name="导出集成测试子分部",
        division_id=division_id,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    memgraph_client.create_node("SubDivision", subdivision.model_dump(exclude_none=True))
    memgraph_client.create_relationship("Division", division_id, "SubDivision", subdivision_id, "HAS_SUBDIVISION")
    
    item = ItemNode(
        id=item_id,
        name="导出集成测试分项",
        subdivision_id=subdivision_id,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    memgraph_client.create_node("Item", item.model_dump(exclude_none=True))
    memgraph_client.create_relationship("SubDivision", subdivision_id, "Item", item_id, "HAS_ITEM")
    
    # 创建检验批（初始状态为 PLANNING）
    lot = InspectionLotNode(
        id=lot_id,
        name="导出集成测试检验批",
        status="PLANNING",
        item_id=item_id,
        spatial_scope="export_scope",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    memgraph_client.create_node("InspectionLot", lot.model_dump(exclude_none=True))
    memgraph_client.create_relationship("Item", item_id, "InspectionLot", lot_id, "HAS_LOT")
    
    # 创建 Level
    level = LevelNode(
        id=level_id,
        name="导出集成测试层",
        building_id=building_id,
        elevation=0.0,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    memgraph_client.create_node("Level", level.model_dump(exclude_none=True))
    memgraph_client.create_relationship("Building", building_id, "Level", level_id, "PHYSICALLY_CONTAINS")
    
    yield {
        "project_id": project_id,
        "building_id": building_id,
        "item_id": item_id,
        "lot_id": lot_id,
        "level_id": level_id
    }
    
    # 清理
    memgraph_client.execute_write(
        "MATCH (project:Project {id: $project_id}) DETACH DELETE project",
        {"project_id": project_id}
    )


@pytest.mark.skipif(not IFC_AVAILABLE, reason="ifcopenshell not available")
def test_export_workflow_complete(sample_project_for_export, setup_integration_db):
    """测试完整的导出流程：数据摄入 → 创建检验批 → 审批 → 导出 IFC"""
    memgraph_client = setup_integration_db
    lot_id = sample_project_for_export["lot_id"]
    level_id = sample_project_for_export["level_id"]
    
    # 1. 创建测试构件（模拟数据摄入）
    element_id = "integration_export_element_001"
    geometry = Geometry(
        type="Polyline",
        coordinates=[[0.0, 0.0, 0.0], [10.0, 0.0, 0.0], [10.0, 10.0, 0.0], [0.0, 10.0, 0.0], [0.0, 0.0, 0.0]],
        closed=True
    )
    
    element = ElementNode(
        id=element_id,
        speckle_id="speckle_integration_001",
        speckle_type="Wall",
        geometry=geometry,
        height=3.0,
        base_offset=0.0,
        level_id=level_id,
        inspection_lot_id=lot_id,
        status="Verified",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    memgraph_client.create_node("Element", element.to_cypher_properties())
    memgraph_client.create_relationship("InspectionLot", lot_id, "Element", element_id, "MANAGEMENT_CONTAINS")
    memgraph_client.create_relationship("Element", element_id, "Level", level_id, "LOCATED_AT")
    
    try:
        # 2. 状态转换：PLANNING -> IN_PROGRESS -> SUBMITTED
        memgraph_client.execute_write(
            "MATCH (lot:InspectionLot {id: $lot_id}) SET lot.status = 'SUBMITTED'",
            {"lot_id": lot_id}
        )
        
        # 3. 审批通过
        approval_service = ApprovalService(client=memgraph_client)
        approval_service.approve_lot(
            lot_id=lot_id,
            approver_id="approver_export_001",
            comment="验收通过，可以导出"
        )
        
        # 验证状态为 APPROVED
        query = "MATCH (lot:InspectionLot {id: $lot_id}) RETURN lot.status as status"
        results = memgraph_client.execute_query(query, {"lot_id": lot_id})
        assert results[0]["status"] == "APPROVED"
        
        # 4. 导出 IFC
        export_service = ExportService(client=memgraph_client)
        ifc_bytes = export_service.export_lot_to_ifc(lot_id)
        
        assert len(ifc_bytes) > 0
        
        # 5. 验证 IFC 文件内容
        with tempfile.NamedTemporaryFile(suffix=".ifc", delete=False) as tmp_file:
            tmp_file.write(ifc_bytes)
            tmp_path = Path(tmp_file.name)
        
        try:
            ifc_file = ifcopenshell.open(str(tmp_path))
            
            # 验证包含项目
            projects = ifc_file.by_type("IfcProject")
            assert len(projects) > 0
            
            # 验证包含建筑
            buildings = ifc_file.by_type("IfcBuilding")
            assert len(buildings) > 0
            
            # 验证包含楼层
            storeys = ifc_file.by_type("IfcBuildingStorey")
            assert len(storeys) > 0
            
            # 验证包含墙元素
            walls = ifc_file.by_type("IfcWall")
            assert len(walls) > 0
            
            # 验证墙的几何表示存在
            wall = walls[0]
            assert wall.Representation is not None
            
        finally:
            tmp_path.unlink()
            
    finally:
        # 清理构件
        memgraph_client.execute_write(
            "MATCH (e:Element {id: $element_id}) DETACH DELETE e",
            {"element_id": element_id}
        )


@pytest.mark.skipif(not IFC_AVAILABLE, reason="ifcopenshell not available")
def test_export_ifc_geometry_validation(sample_project_for_export, setup_integration_db):
    """验证 IFC 文件中包含正确的几何和属性"""
    memgraph_client = setup_integration_db
    lot_id = sample_project_for_export["lot_id"]
    level_id = sample_project_for_export["level_id"]
    
    # 创建多个测试构件（不同类型的几何）
    elements_data = [
        {
            "id": "integration_export_element_002",
            "speckle_type": "Wall",
            "geometry": Geometry(
                type="Polyline",
                coordinates=[[0.0, 0.0, 0.0], [5.0, 0.0, 0.0], [5.0, 5.0, 0.0], [0.0, 5.0, 0.0], [0.0, 0.0, 0.0]],
                closed=True
            ),
            "height": 3.0,
            "base_offset": 0.0
        },
        {
            "id": "integration_export_element_003",
            "speckle_type": "Column",
            "geometry": Geometry(
                type="Line",
                coordinates=[[10.0, 10.0, 0.0], [10.0, 13.0, 0.0]],
                closed=False
            ),
            "height": 3.0,
            "base_offset": 0.0
        },
    ]
    
    created_element_ids = []
    
    try:
        # 创建构件
        for elem_data in elements_data:
            element = ElementNode(
                id=elem_data["id"],
                speckle_id=f"speckle_{elem_data['id']}",
                speckle_type=elem_data["speckle_type"],
                geometry=elem_data["geometry"],
                height=elem_data["height"],
                base_offset=elem_data["base_offset"],
                level_id=level_id,
                inspection_lot_id=lot_id,
                status="Verified",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            memgraph_client.create_node("Element", element.to_cypher_properties())
            memgraph_client.create_relationship("InspectionLot", lot_id, "Element", elem_data["id"], "MANAGEMENT_CONTAINS")
            memgraph_client.create_relationship("Element", elem_data["id"], "Level", level_id, "LOCATED_AT")
            created_element_ids.append(elem_data["id"])
        
        # 设置检验批为 APPROVED 状态
        memgraph_client.execute_write(
            "MATCH (lot:InspectionLot {id: $lot_id}) SET lot.status = 'APPROVED'",
            {"lot_id": lot_id}
        )
        
        # 导出 IFC
        export_service = ExportService(client=memgraph_client)
        ifc_bytes = export_service.export_lot_to_ifc(lot_id)
        
        # 验证 IFC 文件
        with tempfile.NamedTemporaryFile(suffix=".ifc", delete=False) as tmp_file:
            tmp_file.write(ifc_bytes)
            tmp_path = Path(tmp_file.name)
        
        try:
            ifc_file = ifcopenshell.open(str(tmp_path))
            
            # 验证包含所有类型的元素
            walls = ifc_file.by_type("IfcWall")
            columns = ifc_file.by_type("IfcColumn")
            
            assert len(walls) > 0, "应该包含墙元素"
            assert len(columns) > 0, "应该包含柱元素"
            
            # 验证每个元素都有几何表示
            for wall in walls:
                assert wall.Representation is not None, "墙应该有几何表示"
            
            for column in columns:
                assert column.Representation is not None, "柱应该有几何表示"
                
        finally:
            tmp_path.unlink()
            
    finally:
        # 清理构件
        for element_id in created_element_ids:
            memgraph_client.execute_write(
                "MATCH (e:Element {id: $element_id}) DETACH DELETE e",
                {"element_id": element_id}
            )

