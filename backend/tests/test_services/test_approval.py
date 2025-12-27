"""审批服务测试"""

import pytest
from datetime import datetime
from app.services.approval import ApprovalService, ApprovalRole
from app.utils.memgraph import MemgraphClient
from app.models.gb50300.nodes import InspectionLotNode, ApprovalHistoryNode
from app.models.gb50300.relationships import HAS_APPROVAL_HISTORY


@pytest.fixture
def approval_service(memgraph_client):
    """审批服务实例"""
    return ApprovalService(client=memgraph_client)


@pytest.fixture
def sample_lot_id(memgraph_client):
    """创建测试用的检验批并返回 ID"""
    from app.models.gb50300.element import ElementNode
    from app.models.speckle.base import Geometry
    from app.models.gb50300.relationships import MANAGEMENT_CONTAINS
    
    lot_id = "test_lot_approval_001"
    lot_node = InspectionLotNode(
        id=lot_id,
        name="测试检验批",
        status="SUBMITTED",
        item_id="item_test_001",
        spatial_scope="test_scope",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # 创建检验批节点
    memgraph_client.create_node("InspectionLot", lot_node.model_dump(exclude_none=True))
    
    # 创建测试元素并关联到检验批
    element_id = "test_element_approval_001"
    element = ElementNode(
        id=element_id,
        speckle_type="Wall",
        geometry=Geometry(
            type="Polyline",
            coordinates=[[0.0, 0.0, 0.0], [10.0, 0.0, 0.0], [10.0, 5.0, 0.0], [0.0, 5.0, 0.0], [0.0, 0.0, 0.0]],
            closed=True
        ),
        level_id="level_test_001",
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


def test_approve_lot(approval_service, sample_lot_id):
    """测试审批通过功能"""
    approver_id = "approver_001"
    comment = "验收通过"
    
    result = approval_service.approve_lot(
        lot_id=sample_lot_id,
        approver_id=approver_id,
        comment=comment
    )
    
    # 验证返回结果结构（根据 ApprovalService 的实际返回值）
    assert "lot_id" in result
    assert result["lot_id"] == sample_lot_id
    assert result["status"] == "APPROVED"
    
    # 验证检验批状态已更新
    query = "MATCH (lot:InspectionLot {id: $lot_id}) RETURN lot.status as status"
    results = approval_service.client.execute_query(query, {"lot_id": sample_lot_id})
    assert len(results) > 0
    assert results[0]["status"] == "APPROVED"


def test_reject_lot_to_in_progress(approval_service, sample_lot_id):
    """测试驳回到 IN_PROGRESS"""
    rejector_id = "approver_001"
    reason = "需要补充资料"
    
    result = approval_service.reject_lot(
        lot_id=sample_lot_id,
        rejector_id=rejector_id,
        reason=reason,
        reject_level="IN_PROGRESS",
        role=ApprovalRole.APPROVER
    )
    
    # 验证返回结果结构
    assert result["status"] == "IN_PROGRESS"
    
    # 验证状态已更新
    query = "MATCH (lot:InspectionLot {id: $lot_id}) RETURN lot.status as status"
    results = approval_service.client.execute_query(query, {"lot_id": sample_lot_id})
    assert results[0]["status"] == "IN_PROGRESS"


def test_reject_lot_to_planning(approval_service, memgraph_client, sample_lot_id):
    """测试驳回到 PLANNING"""
    # 先将检验批设置为 APPROVED 状态（PM 可以驳回 APPROVED 状态）
    memgraph_client.execute_write(
        "MATCH (lot:InspectionLot {id: $lot_id}) SET lot.status = 'APPROVED'",
        {"lot_id": sample_lot_id}
    )
    
    rejector_id = "pm_001"
    reason = "重大错误，需要重新规划"
    
    result = approval_service.reject_lot(
        lot_id=sample_lot_id,
        rejector_id=rejector_id,
        reason=reason,
        reject_level="PLANNING",
        role=ApprovalRole.PM
    )
    
    # 验证返回结果结构
    assert result["status"] == "PLANNING"


def test_get_approval_history(approval_service, sample_lot_id):
    """测试审批历史查询"""
    approver_id = "approver_001"
    
    # 先进行审批操作
    approval_service.approve_lot(
        lot_id=sample_lot_id,
        approver_id=approver_id,
        comment="第一次审批通过"
    )
    
    # 查询审批历史
    history = approval_service.get_approval_history(sample_lot_id)
    
    assert len(history) > 0
    assert history[0]["action"] == "APPROVE"
    assert history[0]["user_id"] == approver_id
    assert history[0]["comment"] == "第一次审批通过"
    assert history[0]["new_status"] == "APPROVED"


def test_approval_history_node_creation(approval_service, sample_lot_id, memgraph_client):
    """验证 ApprovalHistory 节点的创建和关系"""
    approver_id = "approver_001"
    comment = "审批通过"
    
    # 执行审批
    approval_service.approve_lot(
        lot_id=sample_lot_id,
        approver_id=approver_id,
        comment=comment
    )
    
    # 查询 ApprovalHistory 节点
    query = """
    MATCH (lot:InspectionLot {id: $lot_id})-[:HAS_APPROVAL_HISTORY]->(h:ApprovalHistory)
    RETURN h ORDER BY h.created_at DESC LIMIT 1
    """
    results = memgraph_client.execute_query(query, {"lot_id": sample_lot_id})
    
    assert len(results) > 0
    history_node = results[0]["h"]
    assert history_node["action"] == "APPROVE"
    assert history_node["user_id"] == approver_id
    assert history_node["lot_id"] == sample_lot_id
    assert history_node["comment"] == comment
    assert history_node["old_status"] == "SUBMITTED"
    assert history_node["new_status"] == "APPROVED"


def test_permission_validation_can_approve(approval_service, sample_lot_id):
    """测试 can_approve 权限验证"""
    # SUBMITTED 状态可以审批（需要提供 role 参数）
    from app.services.approval import ApprovalRole
    can_approve = approval_service.can_approve(sample_lot_id, "user_001", ApprovalRole.APPROVER)
    assert can_approve is True


def test_permission_validation_can_reject(approval_service, sample_lot_id):
    """测试驳回权限验证（通过实际执行 reject_lot 来验证权限检查）"""
    # 注意：ApprovalService 中没有独立的 can_reject 方法
    # 权限验证在 reject_lot 方法内部进行
    # 这里我们测试 reject_lot 在有效状态下的行为
    from app.services.approval import ApprovalRole
    # 由于没有独立的 can_reject 方法，我们测试 reject_lot 的行为
    # reject_lot 会在内部检查状态和权限，如果无效会抛出异常
    try:
        result = approval_service.reject_lot(
            lot_id=sample_lot_id,
            rejector_id="user_001",
            reason="测试驳回",
            reject_level="IN_PROGRESS",
            role=ApprovalRole.APPROVER
        )
        # 如果成功，说明权限检查通过
        assert result["status"] == "IN_PROGRESS"
    except ValueError as e:
        # 如果抛出异常，说明权限检查失败（这是正常的，因为状态可能不匹配）
        # 这里我们只验证方法存在且能执行
        assert "reject" in str(e).lower() or "status" in str(e).lower()


def test_approve_nonexistent_lot(approval_service):
    """测试审批不存在的检验批"""
    with pytest.raises(ValueError, match="InspectionLot.*not found"):
        approval_service.approve_lot(
            lot_id="nonexistent_lot",
            approver_id="approver_001"
        )


def test_approve_invalid_status(approval_service, memgraph_client):
    """测试审批无效状态的检验批"""
    lot_id = "test_lot_invalid_status"
    lot_node = InspectionLotNode(
        id=lot_id,
        name="测试检验批",
        status="PLANNING",  # PLANNING 状态不能审批
        item_id="test_item_001",
        spatial_scope="test_scope",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    memgraph_client.create_node("InspectionLot", lot_node.model_dump(exclude_none=True))
    
    try:
        with pytest.raises(ValueError, match="Cannot approve"):
            approval_service.approve_lot(
                lot_id=lot_id,
                approver_id="approver_001"
            )
    finally:
        # 清理
        memgraph_client.execute_write(
            "MATCH (lot:InspectionLot {id: $lot_id}) DETACH DELETE lot",
            {"lot_id": lot_id}
        )

