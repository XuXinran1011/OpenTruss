"""检验批状态管理 API 测试

测试状态转换限制和验证逻辑
"""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from app.main import app
from app.utils.memgraph import MemgraphClient
from app.services.schema import initialize_schema
from app.models.gb50300.nodes import InspectionLotNode

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
def sample_lot_in_progress(memgraph_client):
    """创建状态为 IN_PROGRESS 的测试检验批"""
    lot_id = "test_lot_status_in_progress"
    lot_node = InspectionLotNode(
        id=lot_id,
        name="测试检验批",
        status="IN_PROGRESS",
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
def sample_lot_submitted(memgraph_client):
    """创建状态为 SUBMITTED 的测试检验批"""
    lot_id = "test_lot_status_submitted"
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


def test_update_status_in_progress_to_submitted(sample_lot_in_progress):
    """测试 IN_PROGRESS -> SUBMITTED 状态转换"""
    lot_id = sample_lot_in_progress
    
    response = client.patch(
        f"/api/v1/lots/{lot_id}/status",
        json={"status": "SUBMITTED"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["old_status"] == "IN_PROGRESS"
    assert data["data"]["new_status"] == "SUBMITTED"


def test_update_status_forbidden_submitted_to_approved(sample_lot_submitted):
    """测试 SUBMITTED -> APPROVED 状态转换被禁止（必须通过审批端点）"""
    lot_id = sample_lot_submitted
    
    response = client.patch(
        f"/api/v1/lots/{lot_id}/status",
        json={"status": "APPROVED"}
    )
    
    # 应该返回 400 错误，因为该转换被禁止
    assert response.status_code == 400
    data = response.json()
    assert "Invalid status transition" in data["detail"] or "invalid" in data["detail"].lower()


def test_update_status_planning_to_in_progress(memgraph_client):
    """测试 PLANNING -> IN_PROGRESS 状态转换"""
    lot_id = "test_lot_status_planning"
    lot_node = InspectionLotNode(
        id=lot_id,
        name="测试检验批",
        status="PLANNING",
        item_id="test_item_001",
        spatial_scope="test_scope",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    try:
        memgraph_client.create_node("InspectionLot", lot_node.model_dump(exclude_none=True))
        
        response = client.patch(
            f"/api/v1/lots/{lot_id}/status",
            json={"status": "IN_PROGRESS"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["old_status"] == "PLANNING"
        assert data["data"]["new_status"] == "IN_PROGRESS"
    finally:
        # 清理
        memgraph_client.execute_write(
            "MATCH (lot:InspectionLot {id: $lot_id}) DETACH DELETE lot",
            {"lot_id": lot_id}
        )


def test_update_status_invalid_transition(memgraph_client):
    """测试无效的状态转换"""
    lot_id = "test_lot_status_invalid"
    lot_node = InspectionLotNode(
        id=lot_id,
        name="测试检验批",
        status="PLANNING",
        item_id="test_item_001",
        spatial_scope="test_scope",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    try:
        memgraph_client.create_node("InspectionLot", lot_node.model_dump(exclude_none=True))
        
        # 尝试直接从 PLANNING 跳到 SUBMITTED（应该失败）
        response = client.patch(
            f"/api/v1/lots/{lot_id}/status",
            json={"status": "SUBMITTED"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid status transition" in data["detail"] or "invalid" in data["detail"].lower()
    finally:
        # 清理
        memgraph_client.execute_write(
            "MATCH (lot:InspectionLot {id: $lot_id}) DETACH DELETE lot",
            {"lot_id": lot_id}
        )
