/** 审批工作流 API 服务 */

import { apiPost, apiGet } from './api';

export interface ApproveRequest {
  comment?: string;
  // approver_id 已移除，从 JWT token 中获取
}

export interface ApproveResponse {
  lot_id: string;
  status: string;
  approved_by?: string;
  approved_at?: string;
  comment?: string;
}

export interface RejectRequest {
  reason: string;
  reject_level: 'IN_PROGRESS' | 'PLANNING';
  // rejector_id 和 role 已移除，从 JWT token 中获取
}

export interface RejectResponse {
  lot_id: string;
  status: string;
  rejected_by: string;
  rejected_at: string;
  reason: string;
  reject_level: string;
}

export interface ApprovalHistoryItem {
  action: 'APPROVE' | 'REJECT';
  user_id: string;
  comment?: string;
  old_status: string;
  new_status: string;
  timestamp: string;
}

export interface ApprovalHistoryResponse {
  lot_id: string;
  history: ApprovalHistoryItem[];
}

export interface ApiResponse<T> {
  status: string;
  data: T;
}

/**
 * 审批通过检验批
 */
export async function approveLot(
  lotId: string,
  request: ApproveRequest
): Promise<ApproveResponse> {
  const response = await apiPost<ApiResponse<ApproveResponse>>(
    `/api/v1/lots/${lotId}/approve`,
    request
  );
  return response.data;
}

/**
 * 驳回检验批
 */
export async function rejectLot(
  lotId: string,
  request: RejectRequest
): Promise<RejectResponse> {
  const response = await apiPost<ApiResponse<RejectResponse>>(
    `/api/v1/lots/${lotId}/reject`,
    request
  );
  return response.data;
}

/**
 * 获取审批历史
 */
export async function getApprovalHistory(
  lotId: string
): Promise<ApprovalHistoryResponse> {
  const response = await apiGet<ApiResponse<ApprovalHistoryResponse>>(
    `/api/v1/lots/${lotId}/approval-history`
  );
  return response.data;
}

/**
 * 批量审批请求
 */
export interface BatchApproveRequest {
  lot_ids: string[];
  comment?: string;
}

/**
 * 批量审批结果项
 */
export interface BatchApproveResult {
  lot_id: string;
  status?: string;
  approved_by?: string;
  approved_at?: string;
  error?: string;
}

/**
 * 批量审批响应
 */
export interface BatchApproveResponse {
  success: BatchApproveResult[];
  failed: BatchApproveResult[];
  total: number;
}

/**
 * 批量审批通过检验批
 */
export async function batchApproveLots(
  request: BatchApproveRequest
): Promise<BatchApproveResponse> {
  const response = await apiPost<ApiResponse<BatchApproveResponse>>(
    `/api/v1/lots/batch-approve`,
    request
  );
  return response.data;
}

