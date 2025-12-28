"""审批 API 测试"""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from app.main import app
from app.utils.memgraph import MemgraphClient
from app.services.schema import initialize_schema
from app.models.gb50300.nodes import InspectionLotNode
from app.core.auth import create_access_token, UserRole

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    """设置测试数据库"""
    memgraph_client = MemgraphClient()
    initialize_schema(memgraph_client)
    yield
    # 清理测试数据（如果需要）


@pytest.fixture
def memgraph_client():
    """Memgraph 客户端 fixture"""
    return MemgraphClient()


@pytest.fixture
def sample_lot_id(memgraph_client):
    """创建测试用的检验批并返回 ID"""
    from app.models.gb50300.element import ElementNode
    from app.models.speckle.base import Geometry
    from app.models.gb50300.relationships import MANAGEMENT_CONTAINS
    
    lot_id = "test_lot_api_001"
    lot_node = InspectionLotNode(
        id=lot_id,
        name="测试检验批",
        status="SUBMITTED",
        item_id="item_test_001",
        spatial_scope="test_scope",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    memgraph_client.create_node("InspectionLot", lot_node.model_dump(exclude_none=True))
    
    # 创建测试元素并关联到检验批
    element_id = "test_element_api_approval_001"
    element = ElementNode(
        id=element_id,
        speckle_type="Wall",
        geometry=Geometry(
            type="Polyline",
            coordinates=[[0.0, 0.0, 0.0], [10.0, 0.0, 0.0], [10.0, 5.0, 0.0], [0.0, 5.0, 0.0], [0.0, 0.0, 0.0]],
            closed=True
        ),
        level_id="level_test_api_001",
        inspection_lot_id=lot_id,
        status="Draft",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # 将geometry转换为字典格式
    element_dict = element.to_cypher_properties()
    memgraph_client.create_node("Element", element_dict)
    memgraph_client.create_relationship(
        "InspectionLot", lot_id,
        "Element", element_id,
        MANAGEMENT_CONTAINS
    )
    
    yield lot_id
    
    # 清理
    memgraph_client.execute_write(
        "MATCH (lot:InspectionLot {id: $lot_id}) DETACH DELETE lot",
        {"lot_id": lot_id}
    )


@pytest.fixture
def approver_token():
    """创建 Approver 角色的 JWT token"""
    return create_access_token(
        user_id="approver_001",
        username="approver",
        role=UserRole.APPROVER
    )


@pytest.fixture
def pm_token():
    """创建 PM 角色的 JWT token"""
    return create_access_token(
        user_id="pm_001",
        username="pm",
        role=UserRole.PM
    )


def test_approve_lot_endpoint(approver_token, sample_lot_id, memgraph_client):
    """测试 POST /api/v1/lots/{lot_id}/approve"""
    response = client.post(
        f"/api/v1/lots/{sample_lot_id}/approve",
        json={"comment": "验收通过"},
        headers={"Authorization": f"Bearer {approver_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "data" in data
    assert data["data"]["lot_id"] == sample_lot_id
    assert data["data"]["status"] == "APPROVED"
    
    # 验证检验批状态已更新
    query = "MATCH (lot:InspectionLot {id: $lot_id}) RETURN lot.status as status"
    results = memgraph_client.execute_query(query, {"lot_id": sample_lot_id})
    assert results[0]["status"] == "APPROVED"


def test_reject_lot_endpoint(approver_token, sample_lot_id, memgraph_client):
    """测试 POST /api/v1/lots/{lot_id}/reject"""
    response = client.post(
        f"/api/v1/lots/{sample_lot_id}/reject",
        json={
            "reason": "需要补充资料",
            "reject_level": "IN_PROGRESS",
            "role": "APPROVER"
        },
        headers={"Authorization": f"Bearer {approver_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "data" in data
    assert data["data"]["status"] == "IN_PROGRESS"
    
    # 验证检验批状态已更新
    query = "MATCH (lot:InspectionLot {id: $lot_id}) RETURN lot.status as status"
    results = memgraph_client.execute_query(query, {"lot_id": sample_lot_id})
    assert results[0]["status"] == "IN_PROGRESS"


def test_get_approval_history_endpoint(approver_token, sample_lot_id, memgraph_client):
    """测试 GET /api/v1/lots/{lot_id}/approval-history"""
    # 先进行审批操作
    client.post(
        f"/api/v1/lots/{sample_lot_id}/approve",
        json={"comment": "验收通过"},
        headers={"Authorization": f"Bearer {approver_token}"}
    )
    
    # 查询审批历史
    response = client.get(
        f"/api/v1/lots/{sample_lot_id}/approval-history",
        headers={"Authorization": f"Bearer {approver_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "data" in data
    assert "history" in data["data"]
    assert len(data["data"]["history"]) > 0
    assert data["data"]["history"][0]["action"] == "APPROVE"
    assert data["data"]["history"][0]["user_id"] == "approver_001"


def test_approval_status_transitions(approver_token, pm_token, memgraph_client):
    """测试状态转换逻辑"""
    from app.models.gb50300.element import ElementNode
    from app.models.speckle.base import Geometry
    from app.models.gb50300.relationships import MANAGEMENT_CONTAINS
    from app.models.gb50300.nodes import LevelNode, BuildingNode
    from app.models.gb50300.relationships import PHYSICALLY_CONTAINS, LOCATED_AT
    
    # 创建项目结构（Project -> Building -> Level）
    from app.models.gb50300.nodes import ProjectNode
    
    project_id = "test_project_status_transitions"
    building_id = "test_building_status_transitions"
    level_id = "test_level_status_transitions"
    
    # 创建 Project（如果需要）
    if not memgraph_client.execute_query("MATCH (p:Project {id: $project_id}) RETURN p", {"project_id": project_id}):
        project = ProjectNode(
            id=project_id,
            name="测试项目",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        memgraph_client.create_node("Project", project.model_dump(exclude_none=True))
    
    # 创建 Building（如果需要）
    if not memgraph_client.execute_query("MATCH (b:Building {id: $building_id}) RETURN b", {"building_id": building_id}):
        building = BuildingNode(
            id=building_id,
            name="测试建筑",
            project_id=project_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        memgraph_client.create_node("Building", building.model_dump(exclude_none=True))
        memgraph_client.create_relationship("Project", project_id, "Building", building_id, "HAS_BUILDING")
    
    # 创建 Level
    if not memgraph_client.execute_query("MATCH (l:Level {id: $level_id}) RETURN l", {"level_id": level_id}):
        level = LevelNode(
            id=level_id,
            name="测试层",
            building_id=building_id,
            elevation=0.0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        memgraph_client.create_node("Level", level.model_dump(exclude_none=True))
        memgraph_client.create_relationship("Building", building_id, "Level", level_id, PHYSICALLY_CONTAINS)
    
    # 清理可能存在的旧测试数据
    lot_id = "test_lot_status_transitions"
    element_id = "test_element_status_transitions"
    
    memgraph_client.execute_write(
        """
        MATCH (lot:InspectionLot {id: $lot_id})-[r]->(e:Element)
        WHERE type(r) = 'MANAGEMENT_CONTAINS'
        DELETE r
        """,
        {"lot_id": lot_id}
    )
    memgraph_client.execute_write(
        """
        MATCH (lot:InspectionLot {id: $lot_id})
        DELETE lot
        """,
        {"lot_id": lot_id}
    )
    memgraph_client.execute_write(
        """
        MATCH (e:Element {id: $element_id})
        DETACH DELETE e
        """,
        {"element_id": element_id}
    )
    
    lot_node = InspectionLotNode(
        id=lot_id,
        name="测试检验批",
        status="PLANNING",
        item_id="item_test_001",
        spatial_scope="test_scope",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    memgraph_client.create_node("InspectionLot", lot_node.model_dump(exclude_none=True))
    
    # 创建测试构件并关联到检验批
    element_node = ElementNode(
        id=element_id,
        speckle_type="Wall",
        geometry=Geometry(
            type="Polyline",
            coordinates=[[0.0, 0.0, 0.0], [10.0, 0.0, 0.0], [10.0, 5.0, 0.0], [0.0, 5.0, 0.0], [0.0, 0.0, 0.0]],
            closed=True
        ),
        height=3.0,
        base_offset=0.0,
        material="concrete",
        level_id=level_id,
        inspection_lot_id=lot_id,
        status="Draft",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # 使用 to_cypher_properties() 方法
    element_dict = element_node.to_cypher_properties()
    memgraph_client.create_node("Element", element_dict)
    memgraph_client.create_relationship(
        "InspectionLot", lot_id,
        "Element", element_id,
        MANAGEMENT_CONTAINS
    )
    memgraph_client.create_relationship(
        "Element", element_id,
        "Level", level_id,
        LOCATED_AT
    )
    
    try:
        # 1. PLANNING -> IN_PROGRESS (通过更新状态)
        memgraph_client.execute_write(
            "MATCH (lot:InspectionLot {id: $lot_id}) SET lot.status = 'IN_PROGRESS'",
            {"lot_id": lot_id}
        )
        
        # 2. IN_PROGRESS -> SUBMITTED (通过更新状态)
        memgraph_client.execute_write(
            "MATCH (lot:InspectionLot {id: $lot_id}) SET lot.status = 'SUBMITTED'",
            {"lot_id": lot_id}
        )
        
        # 3. SUBMITTED -> APPROVED (通过审批)
        response = client.post(
            f"/api/v1/lots/{lot_id}/approve",
            json={"comment": "验收通过"},
            headers={"Authorization": f"Bearer {approver_token}"}
        )
        if response.status_code != 200:
            print(f"\n=== Approval failed ===")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # 验证状态为 APPROVED
        query = "MATCH (lot:InspectionLot {id: $lot_id}) RETURN lot.status as status"
        results = memgraph_client.execute_query(query, {"lot_id": lot_id})
        assert results[0]["status"] == "APPROVED"
        
        # 4. APPROVED -> PLANNING (PM 可以驳回 APPROVED 状态)
        response = client.post(
            f"/api/v1/lots/{lot_id}/reject",
            json={
                "reason": "重大错误，需要重新规划",
                "reject_level": "PLANNING",
                "role": "PM"
            },
            headers={"Authorization": f"Bearer {pm_token}"}
        )
        assert response.status_code == 200
        
        # 验证状态为 PLANNING
        results = memgraph_client.execute_query(query, {"lot_id": lot_id})
        assert results[0]["status"] == "PLANNING"
        
    finally:
        # 清理
        memgraph_client.execute_write(
            "MATCH (lot:InspectionLot {id: $lot_id}) DETACH DELETE lot",
            {"lot_id": lot_id}
        )


def test_approve_lot_unauthorized(sample_lot_id):
    """测试未授权访问审批端点"""
    response = client.post(
        f"/api/v1/lots/{sample_lot_id}/approve",
        json={"comment": "验收通过"}
        # 没有 Authorization header
    )
    
    assert response.status_code == 401  # Unauthorized (认证失败，不是授权失败)


def test_approve_nonexistent_lot(approver_token):
    """测试审批不存在的检验批"""
    response = client.post(
        "/api/v1/lots/nonexistent_lot/approve",
        json={"comment": "验收通过"},
        headers={"Authorization": f"Bearer {approver_token}"}
    )
    
    # API 对 NotFoundError 返回 404 Not Found
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_approve_invalid_status(approver_token, memgraph_client):
    """测试审批非 SUBMITTED 状态的检验批"""
    lot_id = "test_lot_invalid_status_api"
    lot_node = InspectionLotNode(
        id=lot_id,
        name="测试检验批",
        status="PLANNING",  # PLANNING 状态不能审批
        item_id="item_test_001",
        spatial_scope="test_scope",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    memgraph_client.create_node("InspectionLot", lot_node.model_dump(exclude_none=True))
    
    try:
        response = client.post(
            f"/api/v1/lots/{lot_id}/approve",
            json={"comment": "验收通过"},
            headers={"Authorization": f"Bearer {approver_token}"}
        )
        
        assert response.status_code == 400
        assert "cannot approve" in response.json()["detail"].lower() or "must be submitted" in response.json()["detail"].lower()
    finally:
        memgraph_client.execute_write(
            "MATCH (lot:InspectionLot {id: $lot_id}) DETACH DELETE lot",
            {"lot_id": lot_id}
        )


def test_reject_invalid_level(approver_token, sample_lot_id):
    """测试驳回时使用无效的 reject_level"""
    response = client.post(
        f"/api/v1/lots/{sample_lot_id}/reject",
        json={
            "reason": "测试",
            "reject_level": "INVALID_LEVEL"  # 无效的级别
        },
        headers={"Authorization": f"Bearer {approver_token}"}
    )
    
    assert response.status_code == 400
    assert "reject_level" in response.json()["detail"].lower() or "must be" in response.json()["detail"].lower()


def test_reject_approver_to_planning(approver_token, sample_lot_id):
    """测试 Approver 试图驳回至 PLANNING（应该失败，只有 PM 可以）"""
    response = client.post(
        f"/api/v1/lots/{sample_lot_id}/reject",
        json={
            "reason": "测试",
            "reject_level": "PLANNING"  # Approver 不能驳回至 PLANNING
        },
        headers={"Authorization": f"Bearer {approver_token}"}
    )
    
    # API 应该返回 400，因为 Approver 只能驳回至 IN_PROGRESS
    assert response.status_code == 400
    assert "only reject to in_progress" in response.json()["detail"].lower() or "approver" in response.json()["detail"].lower()


def test_reject_pm_to_planning(pm_token, memgraph_client):
    """测试 PM 驳回至 PLANNING（应该成功）"""
    lot_id = "test_lot_pm_reject"
    lot_node = InspectionLotNode(
        id=lot_id,
        name="测试检验批",
        status="APPROVED",  # PM 可以驳回 APPROVED 状态
        item_id="item_test_001",
        spatial_scope="test_scope",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    memgraph_client.create_node("InspectionLot", lot_node.model_dump(exclude_none=True))
    
    try:
        response = client.post(
            f"/api/v1/lots/{lot_id}/reject",
            json={
                "reason": "重大错误，需要重新规划",
                "reject_level": "PLANNING"
            },
            headers={"Authorization": f"Bearer {pm_token}"}
        )
        
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "PLANNING"
    finally:
        memgraph_client.execute_write(
            "MATCH (lot:InspectionLot {id: $lot_id}) DETACH DELETE lot",
            {"lot_id": lot_id}
        )
