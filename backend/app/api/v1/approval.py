"""审批工作流 API

提供检验批审批和驳回接口
"""

from fastapi import APIRouter, HTTPException, status, Depends

from app.services.approval import ApprovalService, ApprovalRole
from app.models.api.approval import (
    ApproveRequest,
    RejectRequest,
    ApprovalResponse,
    RejectResponse,
    ApprovalHistoryResponse,
    ApprovalHistoryItem,
)
from app.utils.memgraph import get_memgraph_client, MemgraphClient
from app.core.auth import get_current_user, require_approver, require_pm, TokenData

router = APIRouter(prefix="/lots", tags=["approval"])


def get_approval_service(
    client: MemgraphClient = Depends(get_memgraph_client)
) -> ApprovalService:
    """获取 ApprovalService 实例（依赖注入）"""
    return ApprovalService(client=client)


@router.post(
    "/{lot_id}/approve",
    response_model=dict,
    summary="审批通过检验批",
    description="审批通过检验批（Approver 权限），状态从 SUBMITTED 变为 APPROVED"
)
async def approve_lot(
    lot_id: str,
    request: ApproveRequest,
    service: ApprovalService = Depends(get_approval_service),
    current_user: TokenData = Depends(require_approver),
) -> dict:
    """审批通过检验批"""
    try:
        # 使用当前认证用户的信息（而不是请求中的 approver_id）
        result = service.approve_lot(
            lot_id=lot_id,
            approver_id=current_user.user_id,  # 从 token 获取
            comment=request.comment
        )
        
        response = ApprovalResponse(
            lot_id=result["lot_id"],
            status=result["status"],
            approved_by=result.get("approved_by"),
            approved_at=result.get("approved_at"),
            comment=result.get("comment")
        )
        
        return {
            "status": "success",
            "data": response.model_dump()
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve lot: {str(e)}"
        )


@router.post(
    "/{lot_id}/reject",
    response_model=dict,
    summary="驳回检验批",
    description="驳回检验批（Approver/PM 权限）"
)
async def reject_lot(
    lot_id: str,
    request: RejectRequest,
    service: ApprovalService = Depends(get_approval_service),
    current_user: TokenData = Depends(require_approver),
) -> dict:
    """驳回检验批"""
    try:
        # 验证 reject_level
        if request.reject_level not in ["IN_PROGRESS", "PLANNING"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="reject_level must be 'IN_PROGRESS' or 'PLANNING'"
            )
        
        # 从当前用户 token 获取角色（而不是请求中的 role）
        # 如果用户是 PM，可以使用 PM 权限；否则使用 APPROVER 权限
        from app.core.auth import UserRole
        user_role = UserRole(current_user.role)
        
        # 根据用户角色确定 ApprovalRole
        if user_role == UserRole.PM or user_role == UserRole.ADMIN:
            approval_role = ApprovalRole.PM
        else:
            approval_role = ApprovalRole.APPROVER
        
        result = service.reject_lot(
            lot_id=lot_id,
            rejector_id=current_user.user_id,  # 从 token 获取
            reason=request.reason,
            reject_level=request.reject_level,
            role=approval_role
        )
        
        response = RejectResponse(
            lot_id=result["lot_id"],
            status=result["status"],
            rejected_by=result["rejected_by"],
            rejected_at=result["rejected_at"],
            reason=result["reason"],
            reject_level=result["reject_level"]
        )
        
        return {
            "status": "success",
            "data": response.model_dump()
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reject lot: {str(e)}"
        )


@router.get(
    "/{lot_id}/approval-history",
    response_model=dict,
    summary="获取审批历史",
    description="获取检验批的审批历史记录"
)
async def get_approval_history(
    lot_id: str,
    service: ApprovalService = Depends(get_approval_service),
) -> dict:
    """获取审批历史"""
    try:
        history_data = service.get_approval_history(lot_id)
        
        history_items = [
            ApprovalHistoryItem(
                action=item["action"],
                user_id=item["user_id"],
                comment=item.get("comment"),
                old_status=item["old_status"],
                new_status=item["new_status"],
                timestamp=item.get("timestamp") or item.get("created_at", datetime.now().isoformat())  # 兼容 timestamp 和 created_at
            )
            for item in history_data
        ]
        
        response = ApprovalHistoryResponse(
            lot_id=lot_id,
            history=history_items
        )
        
        return {
            "status": "success",
            "data": response.model_dump()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get approval history: {str(e)}"
        )

