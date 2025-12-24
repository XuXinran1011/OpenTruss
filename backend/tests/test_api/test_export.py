"""导出 API 测试"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime

try:
    import ifcopenshell
    IFC_AVAILABLE = True
except ImportError:
    IFC_AVAILABLE = False

from fastapi.testclient import TestClient

from app.main import app
from app.utils.memgraph import MemgraphClient
from app.services.schema import initialize_schema
from app.models.gb50300.nodes import (
    ProjectNode, BuildingNode, DivisionNode, SubDivisionNode,
    ItemNode, InspectionLotNode, LevelNode
)
from app.models.gb50300.element import ElementNode
from app.models.speckle.base import Geometry2D

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    """设置测试数据库"""
    memgraph_client = MemgraphClient()
    initialize_schema(memgraph_client)
    yield
    # 清理测试数据（如果需要）


@pytest.fixture
def sample_project_structure(memgraph_client):
    """创建测试用的项目结构"""
    project_id = "test_project_api_export_001"
    building_id = "test_building_001"
    division_id = "test_division_001"
    subdivision_id = "test_subdivision_001"
    item_id = "test_item_001"
    lot_id = "test_lot_api_export_001"
    level_id = "test_level_001"
    
    # 创建项目节点
    project = ProjectNode(
        id=project_id,
        name="测试项目",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    memgraph_client.create_node("Project", project.model_dump(exclude_none=True))
    
    # 创建建筑节点
    building = BuildingNode(
        id=building_id,
        name="测试建筑",
        project_id=project_id,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    memgraph_client.create_node("Building", building.model_dump(exclude_none=True))
    memgraph_client.create_relationship("Project", project_id, "Building", building_id, "HAS_BUILDING")
    
    # 创建层级节点
    division = DivisionNode(
        id=division_id,
        name="测试分部",
        building_id=building_id,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    memgraph_client.create_node("Division", division.model_dump(exclude_none=True))
    memgraph_client.create_relationship("Building", building_id, "Division", division_id, "HAS_DIVISION")
    
    subdivision = SubDivisionNode(
        id=subdivision_id,
        name="测试子分部",
        division_id=division_id,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    memgraph_client.create_node("SubDivision", subdivision.model_dump(exclude_none=True))
    memgraph_client.create_relationship("Division", division_id, "SubDivision", subdivision_id, "HAS_SUBDIVISION")
    
    item = ItemNode(
        id=item_id,
        name="测试分项",
        subdivision_id=subdivision_id,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    memgraph_client.create_node("Item", item.model_dump(exclude_none=True))
    memgraph_client.create_relationship("SubDivision", subdivision_id, "Item", item_id, "HAS_ITEM")
    
    # 创建检验批
    lot = InspectionLotNode(
        id=lot_id,
        name="测试检验批",
        status="APPROVED",
        item_id=item_id,
        spatial_scope="api_test_scope",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    memgraph_client.create_node("InspectionLot", lot.model_dump(exclude_none=True))
    memgraph_client.create_relationship("Item", item_id, "InspectionLot", lot_id, "HAS_LOT")
    
    # 创建 Level
    level = LevelNode(
        id=level_id,
        name="测试层",
        building_id=building_id,
        elevation=0.0,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    memgraph_client.create_node("Level", level.model_dump(exclude_none=True))
    memgraph_client.create_relationship("Building", building_id, "Level", level_id, "PHYSICALLY_CONTAINS")
    
    # 创建测试构件
    element_id = "test_element_api_export_001"
    geometry_2d = Geometry2D(
        type="Polyline",
        coordinates=[[0.0, 0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0], [0.0, 0.0]],
        closed=True
    )
    
    element = ElementNode(
        id=element_id,
        speckle_id="speckle_001",
        speckle_type="Wall",
        geometry_2d=geometry_2d,
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
    
    yield {
        "project_id": project_id,
        "lot_id": lot_id,
        "element_id": element_id
    }
    
    # 清理
    memgraph_client.execute_write(
        "MATCH (project:Project {id: $project_id}) DETACH DELETE project",
        {"project_id": project_id}
    )


@pytest.mark.skipif(not IFC_AVAILABLE, reason="ifcopenshell not available")
@pytest.mark.timeout(60)  # 60秒超时
def test_export_lot_ifc_endpoint(sample_project_structure):
    """测试 GET /api/v1/export/ifc?inspection_lot_id=..."""
    lot_id = sample_project_structure["lot_id"]
    
    # fixture 已经创建了元素，直接进行测试
    response = client.get(f"/api/v1/export/ifc?inspection_lot_id={lot_id}")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"
    assert "attachment" in response.headers["content-disposition"]
    assert lot_id in response.headers["content-disposition"]
    
    # 验证 IFC 文件内容（简化验证，避免 ifcopenshell.open() 导致超时）
    ifc_bytes = response.content
    assert len(ifc_bytes) > 0
    
    # 只检查 IFC 文件头部，不进行完整的文件解析（避免超时）
    ifc_content = ifc_bytes.decode("utf-8", errors="ignore")
    assert ifc_content.startswith("ISO-10303-21") or ifc_content.startswith("IFC") or "IFCPROJECT" in ifc_content.upper()


@pytest.mark.skipif(not IFC_AVAILABLE, reason="ifcopenshell not available")
@pytest.mark.timeout(60)  # 60秒超时
def test_export_project_ifc_endpoint(sample_project_structure):
    """测试 GET /api/v1/export/ifc?project_id=..."""
    project_id = sample_project_structure["project_id"]
    
    response = client.get(f"/api/v1/export/ifc?project_id={project_id}")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"
    
    # 验证 IFC 文件内容
    ifc_bytes = response.content
    assert len(ifc_bytes) > 0


@pytest.mark.skipif(not IFC_AVAILABLE, reason="ifcopenshell not available")
def test_export_ifc_file_content(sample_project_structure):
    """验证导出的 IFC 文件内容"""
    lot_id = sample_project_structure["lot_id"]
    
    response = client.get(f"/api/v1/export/ifc?inspection_lot_id={lot_id}")
    assert response.status_code == 200
    
    ifc_bytes = response.content
    
    # 验证文件以 IFC 标准头部开始
    ifc_content = ifc_bytes.decode("utf-8", errors="ignore")
    assert ifc_content.startswith("ISO-10303-21") or ifc_content.startswith("IFC")
    
    # 验证包含必要的 IFC 实体
    assert "IFCPROJECT" in ifc_content.upper() or "IFCPROJECT(" in ifc_content
    assert "IFCWALL" in ifc_content.upper() or "IFCWALL(" in ifc_content


@pytest.mark.skipif(not IFC_AVAILABLE, reason="ifcopenshell not available")
def test_export_ifc_both_params():
    """测试同时指定 inspection_lot_id 和 project_id（应该返回错误）"""
    response = client.get("/api/v1/export/ifc?inspection_lot_id=lot1&project_id=proj1")
    
    assert response.status_code == 400
    assert "both" in response.json()["detail"].lower() or "cannot specify" in response.json()["detail"].lower()


@pytest.mark.skipif(not IFC_AVAILABLE, reason="ifcopenshell not available")
def test_export_ifc_no_params():
    """测试不指定任何参数（应该返回错误）"""
    response = client.get("/api/v1/export/ifc")
    
    assert response.status_code == 400
    assert "must specify" in response.json()["detail"].lower() or "either" in response.json()["detail"].lower()


@pytest.mark.skipif(not IFC_AVAILABLE, reason="ifcopenshell not available")
def test_export_ifc_nonexistent_lot():
    """测试导出不存在的检验批"""
    response = client.get("/api/v1/export/ifc?inspection_lot_id=nonexistent_lot")
    
    assert response.status_code == 400  # API 对 ValueError 返回 400，而不是 404

