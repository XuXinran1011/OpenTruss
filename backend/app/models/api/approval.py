"""审批工作流 API 模型"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from pydantic import ConfigDict


class ApproveRequest(BaseModel):
    """审批请求"""
    comment: Optional[str] = Field(None, description="审批意见")
    # approver_id 已移除，从 JWT token 中获取
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "comment": "验收通过"
        }
    })


class RejectRequest(BaseModel):
    """驳回请求"""
    reason: str = Field(..., description="驳回原因")
    reject_level: str = Field(..., description="驳回级别（IN_PROGRESS 或 PLANNING）")
    # rejector_id 和 role 已移除，从 JWT token 中获取
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "reason": "数据质量问题，需要重新检查",
            "reject_level": "IN_PROGRESS"
        }
    })


class ApprovalResponse(BaseModel):
    """审批响应"""
    lot_id: str = Field(..., description="检验批 ID")
    status: str = Field(..., description="新状态")
    approved_by: Optional[str] = Field(None, description="审批人 ID")
    approved_at: Optional[str] = Field(None, description="审批时间")
    comment: Optional[str] = Field(None, description="审批意见")


class RejectResponse(BaseModel):
    """驳回响应"""
    lot_id: str = Field(..., description="检验批 ID")
    status: str = Field(..., description="新状态")
    rejected_by: str = Field(..., description="驳回人 ID")
    rejected_at: str = Field(..., description="驳回时间")
    reason: str = Field(..., description="驳回原因")
    reject_level: str = Field(..., description="驳回级别")


class ApprovalHistoryItem(BaseModel):
    """审批历史记录项"""
    action: str = Field(..., description="操作（APPROVE 或 REJECT）")
    user_id: str = Field(..., description="用户 ID")
    comment: Optional[str] = Field(None, description="审批意见或驳回原因")
    old_status: str = Field(..., description="原状态")
    new_status: str = Field(..., description="新状态")
    timestamp: str = Field(..., description="时间戳")


class ApprovalHistoryResponse(BaseModel):
    """审批历史响应"""
    lot_id: str = Field(..., description="检验批 ID")
    history: List[ApprovalHistoryItem] = Field(..., description="审批历史记录列表")


class BatchApproveRequest(BaseModel):
    """批量审批请求"""
    lot_ids: List[str] = Field(..., description="检验批 ID 列表", min_length=1)
    comment: Optional[str] = Field(None, description="审批意见（应用到所有检验批）")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "lot_ids": ["lot_001", "lot_002", "lot_003"],
            "comment": "批量审批通过"
        }
    })


class BatchApproveResult(BaseModel):
    """批量审批结果项"""
    lot_id: str = Field(..., description="检验批 ID")
    status: Optional[str] = Field(None, description="新状态（成功时）")
    approved_by: Optional[str] = Field(None, description="审批人 ID（成功时）")
    approved_at: Optional[str] = Field(None, description="审批时间（成功时）")
    error: Optional[str] = Field(None, description="错误信息（失败时）")


class BatchApproveResponse(BaseModel):
    """批量审批响应"""
    success: List[BatchApproveResult] = Field(..., description="成功审批的检验批列表")
    failed: List[BatchApproveResult] = Field(..., description="审批失败的检验批列表")
    total: int = Field(..., description="总数")
