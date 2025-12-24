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
    lot_id = "test_lot_api_001"
    lot_node = InspectionLotNode(
        id=lot_id,
        name="测试检验批",
        status="SUBMITTED",
        item_id="test_item_001",
        spatial_scope="test_scope",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    memgraph_client.create_node("InspectionLot", lot_node.model_dump(exclude_none=True))
    
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
    lot_id = "test_lot_status_transitions"
    lot_node = InspectionLotNode(
        id=lot_id,
        name="测试检验批",
        status="PLANNING",
        item_id="test_item_001",
        spatial_scope="test_scope",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    memgraph_client.create_node("InspectionLot", lot_node.model_dump(exclude_none=True))
    
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
        assert response.status_code == 200
        
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
    
    # API 对 ValueError 返回 400 Bad Request，而不是 404
    assert response.status_code == 400
    assert "not found" in response.json()["detail"].lower()

