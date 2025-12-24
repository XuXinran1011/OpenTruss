/**
 * 检验批管理 API 服务
 */

import { apiPost, apiPatch, apiGet, ApiResponse } from './api';

export interface CreateLotsByRuleRequest {
  item_id: string;
  rule_type: 'BY_LEVEL' | 'BY_ZONE' | 'BY_LEVEL_AND_ZONE';
}

export interface CreatedLotInfo {
  id: string;
  name: string;
  spatial_scope: string;
  element_count: number;
}

export interface CreateLotsResponse {
  lots_created: CreatedLotInfo[];
  elements_assigned: number;
  total_lots: number;
}

export interface AssignElementsRequest {
  element_ids: string[];
}

export interface AssignElementsResponse {
  lot_id: string;
  assigned_count: number;
  total_requested: number;
}

export interface RemoveElementsRequest {
  element_ids: string[];
}

export interface RemoveElementsResponse {
  lot_id: string;
  removed_count: number;
  total_requested: number;
}

export interface UpdateLotStatusRequest {
  status: 'PLANNING' | 'IN_PROGRESS' | 'SUBMITTED' | 'APPROVED' | 'PUBLISHED';
}

export interface UpdateLotStatusResponse {
  lot_id: string;
  old_status: string;
  new_status: string;
  updated_at: string;
}

export interface LotElementListItem {
  id: string;
  speckle_type: string;
  level_id: string | null;
  zone_id: string | null;
  status: string;
  has_height: boolean;
  has_material: boolean;
}

export interface LotElementsResponse {
  lot_id: string;
  items: LotElementListItem[];
  total: number;
}

/**
 * 根据规则批量创建检验批
 */
export async function createLotsByRule(
  request: CreateLotsByRuleRequest
): Promise<CreateLotsResponse> {
  const response = await apiPost<ApiResponse<CreateLotsResponse>>('/api/v1/lots/create-by-rule', request);
  return response.data;
}

/**
 * 分配构件到检验批
 */
export async function assignElementsToLot(
  lotId: string,
  request: AssignElementsRequest
): Promise<AssignElementsResponse> {
  const response = await apiPost<ApiResponse<AssignElementsResponse>>(`/api/v1/lots/${lotId}/assign-elements`, request);
  return response.data;
}

/**
 * 从检验批移除构件
 */
export async function removeElementsFromLot(
  lotId: string,
  request: RemoveElementsRequest
): Promise<RemoveElementsResponse> {
  const response = await apiPost<ApiResponse<RemoveElementsResponse>>(`/api/v1/lots/${lotId}/remove-elements`, request);
  return response.data;
}

/**
 * 更新检验批状态
 */
export async function updateLotStatus(
  lotId: string,
  request: UpdateLotStatusRequest
): Promise<UpdateLotStatusResponse> {
  const response = await apiPatch<ApiResponse<UpdateLotStatusResponse>>(`/api/v1/lots/${lotId}/status`, request);
  return response.data;
}

/**
 * 获取检验批下的构件列表
 */
export async function getLotElements(lotId: string): Promise<LotElementsResponse> {
  const response = await apiGet<ApiResponse<LotElementsResponse>>(`/api/v1/lots/${lotId}/elements`);
  return response.data;
}
