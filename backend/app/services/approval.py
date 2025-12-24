"""审批工作流服务

负责检验批的审批和驳回操作
"""

import logging
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
from enum import Enum

from app.utils.memgraph import MemgraphClient, convert_neo4j_datetime
from app.models.gb50300.relationships import MANAGEMENT_CONTAINS, HAS_APPROVAL_HISTORY
from app.models.gb50300.nodes import ApprovalHistoryNode

logger = logging.getLogger(__name__)


class ApprovalRole(str, Enum):
    """审批角色"""
    APPROVER = "APPROVER"  # 专业负责人/总工
    PM = "PM"  # 项目经理


class ApprovalAction(str, Enum):
    """审批操作"""
    APPROVE = "APPROVE"  # 审批通过
    REJECT = "REJECT"  # 驳回


class ApprovalService:
    """审批工作流服务"""
    
    def __init__(self, client: Optional[MemgraphClient] = None):
        """初始化服务
        
        Args:
            client: Memgraph 客户端实例（如果为 None，将创建新实例）
        """
        self.client = client or MemgraphClient()
    
    def approve_lot(
        self,
        lot_id: str,
        approver_id: str,
        comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """审批通过检验批
        
        Args:
            lot_id: 检验批 ID
            approver_id: 审批人 ID（简化版，实际应使用 JWT 中的用户信息）
            comment: 审批意见（可选）
            
        Returns:
            Dict: 审批结果
            
        Raises:
            ValueError: 如果检验批不存在或状态不允许审批
        """
        # 验证检验批存在且状态为 SUBMITTED
        lot_query = """
        MATCH (lot:InspectionLot {id: $lot_id})
        RETURN lot.id as id, lot.status as status, lot.name as name
        """
        result = self.client.execute_query(lot_query, {"lot_id": lot_id})
        
        if not result:
            raise ValueError(f"InspectionLot not found: {lot_id}")
        
        lot_data = result[0]
        current_status = lot_data["status"]
        
        if current_status != "SUBMITTED":
            raise ValueError(
                f"Cannot approve lot {lot_id}: current status is {current_status}, "
                "must be SUBMITTED to approve"
            )
        
        # 更新状态为 APPROVED
        update_query = """
        MATCH (lot:InspectionLot {id: $lot_id})
        SET lot.status = 'APPROVED', lot.updated_at = datetime()
        RETURN lot.id as id, lot.status as status
        """
        self.client.execute_query(update_query, {"lot_id": lot_id})
        
        # 记录审批历史
        self._record_approval_history(
            lot_id=lot_id,
            action=ApprovalAction.APPROVE,
            user_id=approver_id,
            comment=comment,
            old_status="SUBMITTED",
            new_status="APPROVED",
            role=ApprovalRole.APPROVER  # 默认角色，实际应从 token 获取
        )
        
        logger.info(f"Lot {lot_id} approved by {approver_id}")
        
        return {
            "lot_id": lot_id,
            "status": "APPROVED",
            "approved_by": approver_id,
            "approved_at": datetime.now().isoformat(),
            "comment": comment
        }
    
    def reject_lot(
        self,
        lot_id: str,
        rejector_id: str,
        reason: str,
        reject_level: Literal["IN_PROGRESS", "PLANNING"],
        role: ApprovalRole = ApprovalRole.APPROVER
    ) -> Dict[str, Any]:
        """驳回检验批
        
        Args:
            lot_id: 检验批 ID
            rejector_id: 驳回人 ID
            reason: 驳回原因
            reject_level: 驳回级别（IN_PROGRESS 或 PLANNING）
            role: 审批角色（APPROVER 或 PM）
            
        Returns:
            Dict: 驳回结果
            
        Raises:
            ValueError: 如果检验批不存在、状态不允许驳回或权限不足
        """
        # 验证检验批存在
        lot_query = """
        MATCH (lot:InspectionLot {id: $lot_id})
        RETURN lot.id as id, lot.status as status, lot.name as name
        """
        result = self.client.execute_query(lot_query, {"lot_id": lot_id})
        
        if not result:
            raise ValueError(f"InspectionLot not found: {lot_id}")
        
        lot_data = result[0]
        current_status = lot_data["status"]
        
        # 权限验证
        if role == ApprovalRole.APPROVER:
            # Approver 只能驳回 SUBMITTED 状态的检验批，且只能驳回到 IN_PROGRESS
            if current_status != "SUBMITTED":
                raise ValueError(
                    f"Cannot reject lot {lot_id}: current status is {current_status}, "
                    "Approver can only reject SUBMITTED lots"
                )
            if reject_level != "IN_PROGRESS":
                raise ValueError(
                    f"Approver can only reject to IN_PROGRESS, not {reject_level}"
                )
        
        elif role == ApprovalRole.PM:
            # PM 可以驳回 APPROVED 状态的检验批，可以驳回到 IN_PROGRESS 或 PLANNING
            if current_status not in ["SUBMITTED", "APPROVED"]:
                raise ValueError(
                    f"Cannot reject lot {lot_id}: current status is {current_status}, "
                    "PM can only reject SUBMITTED or APPROVED lots"
                )
        else:
            raise ValueError(f"Invalid role: {role}")
        
        # 更新状态
        update_query = """
        MATCH (lot:InspectionLot {id: $lot_id})
        SET lot.status = $new_status, lot.updated_at = datetime()
        RETURN lot.id as id, lot.status as status
        """
        self.client.execute_query(update_query, {
            "lot_id": lot_id,
            "new_status": reject_level
        })
        
        # 记录审批历史
        self._record_approval_history(
            lot_id=lot_id,
            action=ApprovalAction.REJECT,
            user_id=rejector_id,
            comment=reason,
            old_status=current_status,
            new_status=reject_level,
            role=role
        )
        
        logger.info(f"Lot {lot_id} rejected by {rejector_id} (role: {role}) to {reject_level}")
        
        return {
            "lot_id": lot_id,
            "status": reject_level,
            "rejected_by": rejector_id,
            "rejected_at": datetime.now().isoformat(),
            "reason": reason,
            "reject_level": reject_level
        }
    
    def get_approval_history(
        self,
        lot_id: str
    ) -> List[Dict[str, Any]]:
        """获取审批历史记录
        
        Args:
            lot_id: 检验批 ID
            
        Returns:
            List[Dict]: 审批历史记录列表（按时间倒序）
        """
        # 查询独立的 ApprovalHistory 节点
        query = """
        MATCH (lot:InspectionLot {id: $lot_id})-[:HAS_APPROVAL_HISTORY]->(history:ApprovalHistory)
        RETURN history.id as id, history.action as action, history.user_id as user_id,
               history.role as role, history.comment as comment,
               history.old_status as old_status, history.new_status as new_status,
               history.created_at as created_at
        ORDER BY history.created_at DESC
        """
        result = self.client.execute_query(query, {"lot_id": lot_id})
        
        if not result:
            return []
        
        history = []
        for r in result:
            created_at = r.get("created_at")
            timestamp_str = convert_neo4j_datetime(created_at).isoformat() if created_at else datetime.now().isoformat()
            history.append({
                "id": r.get("id"),
                "action": r.get("action"),
                "user_id": r.get("user_id"),
                "role": r.get("role"),
                "comment": r.get("comment"),
                "old_status": r.get("old_status"),
                "new_status": r.get("new_status"),
                "timestamp": timestamp_str,
                "created_at": timestamp_str  # 同时提供 created_at 字段以兼容
            })
        
        return history
    
    def _record_approval_history(
        self,
        lot_id: str,
        action: ApprovalAction,
        user_id: str,
        comment: Optional[str],
        old_status: str,
        new_status: str,
        role: ApprovalRole = ApprovalRole.APPROVER
    ) -> None:
        """记录审批历史（创建独立的 ApprovalHistory 节点）
        
        Args:
            lot_id: 检验批 ID
            action: 审批操作（APPROVE 或 REJECT）
            user_id: 用户 ID
            comment: 审批意见或驳回原因
            old_status: 原状态
            new_status: 新状态
            role: 用户角色
        """
        import uuid
        
        # 创建审批历史节点
        history_id = f"history_{uuid.uuid4().hex[:12]}"
        history_node = ApprovalHistoryNode(
            id=history_id,
            lot_id=lot_id,
            action=action.value,
            user_id=user_id,
            role=role.value,
            comment=comment,
            old_status=old_status,
            new_status=new_status,
            created_at=datetime.now()
        )
        
        # 存储节点
        props = history_node.model_dump()
        create_query = """
        MATCH (lot:InspectionLot {id: $lot_id})
        CREATE (history:ApprovalHistory $props)
        CREATE (lot)-[:HAS_APPROVAL_HISTORY]->(history)
        RETURN history.id as id
        """
        self.client.execute_query(create_query, {
            "lot_id": lot_id,
            "props": props
        })
        
        logger.info(f"Created approval history node {history_id} for lot {lot_id}")
    
    def can_approve(
        self,
        lot_id: str,
        user_id: str,
        role: ApprovalRole
    ) -> bool:
        """检查用户是否可以审批检验批
        
        Args:
            lot_id: 检验批 ID
            user_id: 用户 ID
            role: 用户角色
            
        Returns:
            bool: 是否可以审批
        """
        # 查询检验批状态
        lot_query = """
        MATCH (lot:InspectionLot {id: $lot_id})
        RETURN lot.status as status
        """
        result = self.client.execute_query(lot_query, {"lot_id": lot_id})
        
        if not result:
            return False
        
        status = result[0]["status"]
        
        # Approver 可以审批 SUBMITTED 状态的检验批
        if role == ApprovalRole.APPROVER:
            return status == "SUBMITTED"
        
        # PM 可以审批 SUBMITTED 或 APPROVED 状态的检验批（用于驳回已审批的）
        elif role == ApprovalRole.PM:
            return status in ["SUBMITTED", "APPROVED"]
        
        return False

