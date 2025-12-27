"""审批工作流服务

负责检验批的审批和驳回操作
"""

import logging
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
from enum import Enum

from app.utils.memgraph import MemgraphClient, convert_neo4j_datetime
from app.core.exceptions import NotFoundError, ConflictError, ValidationError
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
            NotFoundError: 如果检验批不存在
            ConflictError: 如果状态不允许审批
            ValidationError: 如果检验批为空或数据不完整
        """
        # 验证检验批存在且状态为 SUBMITTED
        lot_query = """
        MATCH (lot:InspectionLot {id: $lot_id})
        RETURN lot.id as id, lot.status as status, lot.name as name
        """
        result = self.client.execute_query(lot_query, {"lot_id": lot_id})
        
        if not result:
            raise NotFoundError(
                f"InspectionLot not found: {lot_id}. Please check the lot ID and try again.",
                {"lot_id": lot_id, "resource_type": "InspectionLot"}
            )
        
        lot_data = result[0]
        current_status = lot_data["status"]
        
        if current_status != "SUBMITTED":
            raise ConflictError(
                f"Cannot approve lot {lot_id}: current status is '{current_status}', "
                "must be 'SUBMITTED' to approve. Please submit the lot first.",
                {"lot_id": lot_id, "current_status": current_status, "required_status": "SUBMITTED"}
            )
        
        # 验证检验批完整性（轻量级验证，确保基本的几何信息完整）
        # 注意：提交时已经做了完整的验证，这里只做基本的完整性检查
        elements_query = """
        MATCH (lot:InspectionLot {id: $lot_id})-[:MANAGEMENT_CONTAINS]->(e:Element)
        RETURN count(e) as element_count,
               count(CASE WHEN e.geometry IS NOT NULL THEN 1 END) as elements_with_geometry,
               count(CASE WHEN e.height IS NOT NULL AND e.base_offset IS NOT NULL THEN 1 END) as elements_with_height
        """
        elements_result = self.client.execute_query(elements_query, {"lot_id": lot_id})
        
        if not elements_result:
            raise ValidationError(
                f"Failed to query elements for lot {lot_id}",
                {"lot_id": lot_id}
            )
        
        result_data = elements_result[0]
        element_count = result_data.get("element_count", 0)
        elements_with_geometry = result_data.get("elements_with_geometry", 0)
        elements_with_height = result_data.get("elements_with_height", 0)
        
        if element_count == 0:
            raise ValidationError(
                f"Cannot approve lot {lot_id}: the lot contains no elements. "
                "Please add elements to the lot before approval.",
                {"lot_id": lot_id, "element_count": 0}
            )
        
        # 检查几何信息完整性
        if elements_with_geometry < element_count:
            missing_count = element_count - elements_with_geometry
            raise ValidationError(
                f"Cannot approve lot {lot_id}: {missing_count} out of {element_count} elements "
                "are missing geometry. All elements must have complete geometry information for approval.",
                {"lot_id": lot_id, "missing_count": missing_count, "total_count": element_count}
            )
        
        if elements_with_height < element_count:
            missing_count = element_count - elements_with_height
            logger.warning(
                f"Lot {lot_id}: {missing_count} out of {element_count} elements are missing height or base_offset. "
                "This may affect 3D visualization and IFC export."
            )
        
        # Brick Schema 语义验证（硬检查）
        semantic_errors = []
        try:
            from app.core.semantic_validator import get_semantic_validator
            from app.models.gb50300.element import ElementNode
            from app.core.ontology import MEMGRAPH_BRICK_RELATIONSHIPS, DEFAULT_RELATIONSHIP
            
            semantic_validator = get_semantic_validator()
            
            # 获取检验批内所有构件的连接关系（支持所有 Brick 关系类型）
            all_relationship_types = list(MEMGRAPH_BRICK_RELATIONSHIPS.keys()) + [DEFAULT_RELATIONSHIP]
            # 构建 Cypher 查询中的关系类型列表字符串
            relationship_types_str = "['" + "', '".join(all_relationship_types) + "']"
            
            connections_query = f"""
            MATCH (lot:InspectionLot {{id: $lot_id}})-[:MANAGEMENT_CONTAINS]->(e1:Element)
            MATCH (e1)-[r]->(e2:Element)
            WHERE type(r) IN {relationship_types_str}
            MATCH (lot)-[:MANAGEMENT_CONTAINS]->(e2)
            RETURN e1.id as source_id, e1.speckle_type as source_type,
                   e2.id as target_id, e2.speckle_type as target_type,
                   type(r) as relationship_type
            """
            connections = self.client.execute_query(connections_query, {"lot_id": lot_id})
            
            # 获取所有元素数据用于验证
            elements_query = """
            MATCH (lot:InspectionLot {id: $lot_id})-[:MANAGEMENT_CONTAINS]->(e:Element)
            RETURN e
            """
            elements_result = self.client.execute_query(elements_query, {"lot_id": lot_id})
            elements_dict = {dict(elem["e"])["id"]: dict(elem["e"]) for elem in elements_result}
            
            # 验证每个连接
            for conn in connections:
                source_id = conn["source_id"]
                target_id = conn["target_id"]
                relationship = conn["relationship_type"]
                
                source_data = elements_dict.get(source_id)
                target_data = elements_dict.get(target_id)
                
                if not source_data or not target_data:
                    continue
                
                # 创建 ElementNode 对象用于验证
                try:
                    source_element = ElementNode(**source_data)
                    target_element = ElementNode(**target_data)
                    
                    # 执行语义验证
                    result = semantic_validator.validate_connection(
                        source_element,
                        target_element,
                        relationship
                    )
                    
                    if not result.valid:
                        error_msg = (
                            f"{source_element.speckle_type} ({source_id}) cannot {relationship} "
                            f"{target_element.speckle_type} ({target_id})"
                        )
                        if result.error:
                            error_msg += f": {result.error}"
                        if result.suggestion:
                            error_msg += f". Suggestion: use {result.suggestion}"
                        semantic_errors.append(error_msg)
                except Exception as e:
                    logger.warning(f"Failed to validate connection {source_id} -> {target_id}: {e}")
                    continue
            
            # 如果有语义错误，阻止审批
            if semantic_errors:
                error_summary = f"Found {len(semantic_errors)} semantic validation errors"
                raise ValidationError(
                    f"Cannot approve lot {lot_id}: {error_summary}. "
                    f"Details: {'; '.join(semantic_errors[:5])}",  # 只显示前5个错误
                    {"lot_id": lot_id, "error_count": len(semantic_errors), "errors": semantic_errors[:5]}
                )
        except ValueError:
            # 重新抛出语义验证错误
            raise
        except Exception as e:
            # 其他错误记录警告但不阻止审批
            logger.warning(f"Semantic validation failed for lot {lot_id}: {e}. Proceeding with approval.")
        
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
    
    def batch_approve_lots(
        self,
        lot_ids: List[str],
        approver_id: str,
        comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """批量审批通过检验批
        
        Args:
            lot_ids: 检验批 ID 列表
            approver_id: 审批人 ID
            comment: 审批意见（可选，应用到所有检验批）
            
        Returns:
            Dict: 批量审批结果，包含成功和失败的列表
        """
        if not lot_ids:
            raise ValidationError(
                "lot_ids 不能为空",
                {"lot_ids": lot_ids}
            )
        
        results = {
            "success": [],
            "failed": [],
            "total": len(lot_ids)
        }
        
        for lot_id in lot_ids:
            try:
                result = self.approve_lot(
                    lot_id=lot_id,
                    approver_id=approver_id,
                    comment=comment
                )
                results["success"].append({
                    "lot_id": lot_id,
                    "status": result["status"],
                    "approved_by": result.get("approved_by"),
                    "approved_at": result.get("approved_at")
                })
            except Exception as e:
                logger.warning(f"Failed to approve lot {lot_id}: {e}")
                results["failed"].append({
                    "lot_id": lot_id,
                    "error": str(e)
                })
        
        logger.info(f"Batch approval completed: {len(results['success'])} succeeded, {len(results['failed'])} failed")
        
        return results
    
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
            NotFoundError: 如果检验批不存在
            ConflictError: 如果状态不允许驳回
            ValidationError: 如果权限不足或参数无效
        """
        # 验证检验批存在
        lot_query = """
        MATCH (lot:InspectionLot {id: $lot_id})
        RETURN lot.id as id, lot.status as status, lot.name as name
        """
        result = self.client.execute_query(lot_query, {"lot_id": lot_id})
        
        if not result:
            raise NotFoundError(
                f"InspectionLot not found: {lot_id}. Please check the lot ID and try again.",
                {"lot_id": lot_id, "resource_type": "InspectionLot"}
            )
        
        lot_data = result[0]
        current_status = lot_data["status"]
        
        # 权限验证
        if role == ApprovalRole.APPROVER:
            # Approver 只能驳回 SUBMITTED 状态的检验批，且只能驳回到 IN_PROGRESS
            if current_status != "SUBMITTED":
                raise ConflictError(
                    f"Cannot reject lot {lot_id}: current status is '{current_status}', "
                    "Approver can only reject SUBMITTED lots. Please wait until the lot is submitted.",
                    {"lot_id": lot_id, "current_status": current_status, "required_status": "SUBMITTED"}
                )
            if reject_level != "IN_PROGRESS":
                raise ValidationError(
                    f"Approver can only reject to 'IN_PROGRESS', not '{reject_level}'. "
                    "Only PM can reject to 'PLANNING'.",
                    {"lot_id": lot_id, "reject_level": reject_level, "allowed_level": "IN_PROGRESS"}
                )
        
        elif role == ApprovalRole.PM:
            # PM 可以驳回 APPROVED 状态的检验批，可以驳回到 IN_PROGRESS 或 PLANNING
            if current_status not in ["SUBMITTED", "APPROVED"]:
                raise ConflictError(
                    f"Cannot reject lot {lot_id}: current status is '{current_status}', "
                    "PM can only reject SUBMITTED or APPROVED lots. "
                    f"Current status '{current_status}' is not eligible for rejection.",
                    {"lot_id": lot_id, "current_status": current_status, "allowed_statuses": ["SUBMITTED", "APPROVED"]}
                )
        else:
            raise ValidationError(
                f"Invalid role: {role}. Must be 'APPROVER' or 'PM'.",
                {"role": str(role), "allowed_roles": ["APPROVER", "PM"]}
            )
        
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

