"""审批工作流集成测试

测试完整的审批流程：
1. 创建检验批 → 提交 → 审批 → 查看历史
2. 创建检验批 → 提交 → 驳回 → 重新提交 → 审批
3. 验证 ApprovalHistory 节点在整个流程中的创建
"""

import pytest
from datetime import datetime
from app.services.approval import ApprovalService, ApprovalRole
from app.services.lot_strategy import LotStrategyService
from app.services.ingestion import IngestionService
from app.utils.memgraph import MemgraphClient
from app.services.schema import initialize_schema
from app.models.gb50300.nodes import (
    ProjectNode, BuildingNode, DivisionNode, SubDivisionNode,
    ItemNode, InspectionLotNode, LevelNode
)
from app.models.gb50300.element import ElementNode
from app.models.speckle.base import Geometry2D
from app.models.gb50300.relationships import HAS_APPROVAL_HISTORY


@pytest.fixture(scope="module")
def setup_integration_db():
    """设置集成测试数据库"""
    memgraph_client = MemgraphClient()
    initialize_schema(memgraph_client)
    yield memgraph_client


@pytest.fixture
def sample_project_hierarchy(setup_integration_db):
    """创建完整的项目层级结构"""
    memgraph_client = setup_integration_db
    
    project_id = "integration_project_001"
    building_id = "integration_building_001"
    division_id = "integration_division_001"
    subdivision_id = "integration_subdivision_001"
    item_id = "integration_item_001"
    level_id = "integration_level_001"
    
    # 创建项目
    project = ProjectNode(
        id=project_id,
        name="集成测试项目",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    memgraph_client.create_node("Project", project.model_dump(exclude_none=True))
    
    # 创建建筑
    building = BuildingNode(
        id=building_id,
        name="集成测试建筑",
        project_id=project_id,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    memgraph_client.create_node("Building", building.model_dump(exclude_none=True))
    memgraph_client.create_relationship("Project", project_id, "Building", building_id, "HAS_BUILDING")
    
    # 创建层级
    division = DivisionNode(
        id=division_id,
        name="集成测试分部",
        building_id=building_id,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    memgraph_client.create_node("Division", division.model_dump(exclude_none=True))
    memgraph_client.create_relationship("Building", building_id, "Division", division_id, "HAS_DIVISION")
    
    subdivision = SubDivisionNode(
        id=subdivision_id,
        name="集成测试子分部",
        division_id=division_id,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    memgraph_client.create_node("SubDivision", subdivision.model_dump(exclude_none=True))
    memgraph_client.create_relationship("Division", division_id, "SubDivision", subdivision_id, "HAS_SUBDIVISION")
    
    item = ItemNode(
        id=item_id,
        name="集成测试分项",
        subdivision_id=subdivision_id,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    memgraph_client.create_node("Item", item.model_dump(exclude_none=True))
    memgraph_client.create_relationship("SubDivision", subdivision_id, "Item", item_id, "HAS_ITEM")
    
    # 创建 Level
    level = LevelNode(
        id=level_id,
        name="集成测试层",
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
        "level_id": level_id
    }
    
    # 清理
    memgraph_client.execute_write(
        "MATCH (project:Project {id: $project_id}) DETACH DELETE project",
        {"project_id": project_id}
    )


def test_approval_workflow_complete(sample_project_hierarchy, setup_integration_db):
    """测试完整的审批流程：创建检验批 → 提交 → 审批 → 查看历史"""
    memgraph_client = setup_integration_db
    item_id = sample_project_hierarchy["item_id"]
    level_id = sample_project_hierarchy["level_id"]
    
    # 1. 创建检验批
    lot_id = "integration_lot_001"
    lot_node = InspectionLotNode(
        id=lot_id,
        name="集成测试检验批",
        status="PLANNING",
        item_id=item_id,
        spatial_scope="integration_scope",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    memgraph_client.create_node("InspectionLot", lot_node.model_dump(exclude_none=True))
    memgraph_client.create_relationship("Item", item_id, "InspectionLot", lot_id, "HAS_LOT")
    
    try:
        # 2. 状态转换：PLANNING -> IN_PROGRESS -> SUBMITTED
        memgraph_client.execute_write(
            "MATCH (lot:InspectionLot {id: $lot_id}) SET lot.status = 'IN_PROGRESS'",
            {"lot_id": lot_id}
        )
        
        memgraph_client.execute_write(
            "MATCH (lot:InspectionLot {id: $lot_id}) SET lot.status = 'SUBMITTED'",
            {"lot_id": lot_id}
        )
        
        # 3. 审批通过
        approval_service = ApprovalService(client=memgraph_client)
        approver_id = "approver_integration_001"
        comment = "验收通过"
        
        result = approval_service.approve_lot(
            lot_id=lot_id,
            approver_id=approver_id,
            comment=comment
        )
        
        # approve_lot 返回的字典包含 lot_id, status, approved_by 等，没有 success 键
        assert result["lot_id"] == lot_id
        assert result["status"] == "APPROVED"
        
        # 4. 查看审批历史
        history = approval_service.get_approval_history(lot_id)
        assert len(history) == 1
        assert history[0]["action"] == "APPROVE"
        assert history[0]["user_id"] == approver_id
        assert history[0]["comment"] == comment
        assert history[0]["old_status"] == "SUBMITTED"
        assert history[0]["new_status"] == "APPROVED"
        
        # 5. 验证 ApprovalHistory 节点和关系
        query = """
        MATCH (lot:InspectionLot {id: $lot_id})-[:HAS_APPROVAL_HISTORY]->(h:ApprovalHistory)
        RETURN h
        """
        results = memgraph_client.execute_query(query, {"lot_id": lot_id})
        assert len(results) == 1
        assert results[0]["h"]["action"] == "APPROVE"
        
    finally:
        # 清理
        memgraph_client.execute_write(
            "MATCH (lot:InspectionLot {id: $lot_id}) DETACH DELETE lot",
            {"lot_id": lot_id}
        )


def test_approval_workflow_with_rejection(sample_project_hierarchy, setup_integration_db):
    """测试带驳回的审批流程：创建检验批 → 提交 → 驳回 → 重新提交 → 审批"""
    memgraph_client = setup_integration_db
    item_id = sample_project_hierarchy["item_id"]
    
    # 1. 创建检验批
    lot_id = "integration_lot_002"
    lot_node = InspectionLotNode(
        id=lot_id,
        name="集成测试检验批（驳回流程）",
        status="PLANNING",
        item_id=item_id,
        spatial_scope="integration_scope_reject",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    memgraph_client.create_node("InspectionLot", lot_node.model_dump(exclude_none=True))
    memgraph_client.create_relationship("Item", item_id, "InspectionLot", lot_id, "HAS_LOT")
    
    try:
        # 2. 状态转换到 SUBMITTED
        memgraph_client.execute_write(
            "MATCH (lot:InspectionLot {id: $lot_id}) SET lot.status = 'SUBMITTED'",
            {"lot_id": lot_id}
        )
        
        # 3. 第一次驳回（驳回到 IN_PROGRESS）
        approval_service = ApprovalService(client=memgraph_client)
        rejector_id = "approver_integration_002"
        reason = "需要补充资料"
        
        result = approval_service.reject_lot(
            lot_id=lot_id,
            rejector_id=rejector_id,
            reason=reason,
            reject_level="IN_PROGRESS",
            role=ApprovalRole.APPROVER
        )
        
        # reject_lot 返回的字典包含 lot_id, status, rejected_by 等，没有 success 键
        assert result["lot_id"] == lot_id
        assert result["status"] == "IN_PROGRESS"
        
        # 4. 重新提交（IN_PROGRESS -> SUBMITTED）
        memgraph_client.execute_write(
            "MATCH (lot:InspectionLot {id: $lot_id}) SET lot.status = 'SUBMITTED'",
            {"lot_id": lot_id}
        )
        
        # 5. 审批通过
        approver_id = "approver_integration_003"
        comment = "补充资料后验收通过"
        
        result = approval_service.approve_lot(
            lot_id=lot_id,
            approver_id=approver_id,
            comment=comment
        )
        
        # approve_lot 返回的字典包含 lot_id, status, approved_by 等，没有 success 键
        assert result["lot_id"] == lot_id
        assert result["status"] == "APPROVED"
        
        # 6. 查看审批历史（应该包含驳回和审批两条记录）
        history = approval_service.get_approval_history(lot_id)
        assert len(history) == 2
        
        # 第一条应该是审批通过（时间最新的）
        assert history[0]["action"] == "APPROVE"
        assert history[0]["user_id"] == approver_id
        
        # 第二条应该是驳回
        assert history[1]["action"] == "REJECT"
        assert history[1]["user_id"] == rejector_id
        assert history[1]["comment"] == reason
        
        # 7. 验证 ApprovalHistory 节点数量
        query = """
        MATCH (lot:InspectionLot {id: $lot_id})-[:HAS_APPROVAL_HISTORY]->(h:ApprovalHistory)
        RETURN count(h) as count
        """
        results = memgraph_client.execute_query(query, {"lot_id": lot_id})
        assert results[0]["count"] == 2
        
    finally:
        # 清理
        memgraph_client.execute_write(
            "MATCH (lot:InspectionLot {id: $lot_id}) DETACH DELETE lot",
            {"lot_id": lot_id}
        )


def test_approval_history_node_persistence(sample_project_hierarchy, setup_integration_db):
    """验证 ApprovalHistory 节点的持久化和查询"""
    memgraph_client = setup_integration_db
    item_id = sample_project_hierarchy["item_id"]
    
    lot_id = "integration_lot_003"
    lot_node = InspectionLotNode(
        id=lot_id,
        name="集成测试检验批（历史验证）",
        status="SUBMITTED",
        item_id=item_id,
        spatial_scope="integration_scope_history",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    memgraph_client.create_node("InspectionLot", lot_node.model_dump(exclude_none=True))
    memgraph_client.create_relationship("Item", item_id, "InspectionLot", lot_id, "HAS_LOT")
    
    try:
        approval_service = ApprovalService(client=memgraph_client)
        
        # 执行多次审批操作
        operations = [
            {"action": "APPROVE", "user_id": "user1", "comment": "第一次审批"},
            {"action": "REJECT", "user_id": "user2", "reason": "需要修改", "reject_level": "IN_PROGRESS"},
            {"action": "APPROVE", "user_id": "user3", "comment": "第二次审批"},
        ]
        
        # 先设置状态为 SUBMITTED，然后执行审批
        for i, op in enumerate(operations):
            if op["action"] == "APPROVE":
                memgraph_client.execute_write(
                    "MATCH (lot:InspectionLot {id: $lot_id}) SET lot.status = 'SUBMITTED'",
                    {"lot_id": lot_id}
                )
                approval_service.approve_lot(
                    lot_id=lot_id,
                    approver_id=op["user_id"],
                    comment=op["comment"]
                )
            elif op["action"] == "REJECT":
                # 需要先将状态设置为 APPROVED 才能被 PM 驳回
                if i > 0:  # 不是第一次操作
                    memgraph_client.execute_write(
                        "MATCH (lot:InspectionLot {id: $lot_id}) SET lot.status = 'APPROVED'",
                        {"lot_id": lot_id}
                    )
                    approval_service.reject_lot(
                        lot_id=lot_id,
                        rejector_id=op["user_id"],
                        reason=op["reason"],
                        reject_level=op["reject_level"],
                        role=ApprovalRole.PM
                    )
        
        # 查询所有历史记录
        history = approval_service.get_approval_history(lot_id)
        assert len(history) >= 2  # 至少应该有两次操作
        
        # 验证每条历史记录都包含必要字段
        for record in history:
            assert "action" in record
            assert "user_id" in record
            assert "old_status" in record
            assert "new_status" in record
            assert "timestamp" in record
        
    finally:
        # 清理
        memgraph_client.execute_write(
            "MATCH (lot:InspectionLot {id: $lot_id}) DETACH DELETE lot",
            {"lot_id": lot_id}
        )

