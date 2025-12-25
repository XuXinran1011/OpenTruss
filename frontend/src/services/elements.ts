/** 构件 API 服务 */

import { apiGet, apiPost, apiPatch } from './api';
import { ApiResponse, PaginatedResponse } from './api';
import { Geometry2D } from '@/types';

/**
 * 构件列表项
 */
export interface ElementListItem {
  id: string;
  speckle_type: string;
  level_id: string;
  inspection_lot_id?: string;
  status: 'Draft' | 'Verified';
  has_height: boolean;
  has_material: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * 构件详情
 */
export interface ElementDetail {
  id: string;
  speckle_id?: string;
  speckle_type: string;
  geometry_2d: Geometry2D;
  height?: number;
  base_offset?: number;
  material?: string;
  level_id: string;
  zone_id?: string;
  inspection_lot_id?: string;
  status: 'Draft' | 'Verified';
  confidence?: number;
  locked: boolean;
  connected_elements?: string[];
  created_at: string;
  updated_at: string;
}

/**
 * 构件查询参数
 */
export interface ElementQueryParams {
  level_id?: string;
  item_id?: string;
  inspection_lot_id?: string;
  status?: 'Draft' | 'Verified';
  speckle_type?: string;
  has_height?: boolean;
  has_material?: boolean;
  min_confidence?: number;
  max_confidence?: number;
  page?: number;
  page_size?: number;
}

/**
 * 拓扑更新请求
 */
export interface TopologyUpdateRequest {
  geometry_2d?: Geometry2D;
  connected_elements?: string[];
}

/**
 * 构件更新请求
 */
export interface ElementUpdateRequest {
  height?: number;
  base_offset?: number;
  material?: string;
}

/**
 * 批量 Lift 请求
 */
export interface BatchLiftRequest {
  element_ids: string[];
  height?: number;
  base_offset?: number;
  material?: string;
}

/**
 * 批量 Lift 响应
 */
export interface BatchLiftResponse {
  updated_count: number;
  element_ids: string[];
}

/**
 * 归类请求
 */
export interface ClassifyRequest {
  item_id: string;
}

/**
 * 归类响应
 */
export interface ClassifyResponse {
  element_id: string;
  item_id: string;
  previous_item_id?: string;
}

/**
 * 查询构件列表
 */
export async function getElements(
  params: ElementQueryParams = {}
): Promise<PaginatedResponse<ElementListItem>> {
  const queryParams = new URLSearchParams();
  
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      queryParams.append(key, String(value));
    }
  });
  
  const response = await apiGet<ApiResponse<PaginatedResponse<ElementListItem>>>(
    `/api/v1/elements?${queryParams.toString()}`
  );
  return response.data;
}

/**
 * 获取未分配构件列表
 */
export async function getUnassignedElements(
  page: number = 1,
  pageSize: number = 20
): Promise<PaginatedResponse<ElementListItem>> {
  const response = await apiGet<ApiResponse<PaginatedResponse<ElementListItem>>>(
    `/api/v1/elements/unassigned?page=${page}&page_size=${pageSize}`
  );
  return response.data;
}

/**
 * 批量获取构件详情
 * 
 * @param elementIds - 构件 ID 列表（最多100个）
 * @returns 构件详情列表和未找到的ID列表
 * @throws {ApiError} 如果请求失败
 */
export async function batchGetElementDetails(elementIds: string[]): Promise<{
  items: ElementDetail[];
  not_found: string[];
}> {
  const response = await apiPost<ApiResponse<{
    items: ElementDetail[];
    not_found: string[];
  }>>('/api/v1/elements/batch', {
    element_ids: elementIds,
  });
  return response.data;
}

/**
 * 获取构件详情
 * 
 * @param elementId - 构件 ID
 * @returns 构件详细信息，包括几何数据、参数、连接关系等
 * @throws {ApiError} 如果构件不存在或请求失败
 */
export async function getElementDetail(elementId: string): Promise<ElementDetail> {
  const response = await apiGet<ApiResponse<ElementDetail>>(
    `/api/v1/elements/${elementId}`
  );
  return response.data;
}

/**
 * 更新构件拓扑关系
 */
export async function updateElementTopology(
  elementId: string,
  request: TopologyUpdateRequest
): Promise<{ id: string; topology_updated: boolean }> {
  const response = await apiPatch<ApiResponse<{ id: string; topology_updated: boolean }>>(
    `/api/v1/elements/${elementId}/topology`,
    request
  );
  return response.data;
}

/**
 * 更新构件参数
 */
export async function updateElement(
  elementId: string,
  request: ElementUpdateRequest
): Promise<{ id: string; updated_fields: string[] }> {
  const response = await apiPatch<ApiResponse<{ id: string; updated_fields: string[] }>>(
    `/api/v1/elements/${elementId}`,
    request
  );
  return response.data;
}

/**
 * 批量设置 Z 轴参数
 */
export async function batchLiftElements(request: BatchLiftRequest): Promise<BatchLiftResponse> {
  const response = await apiPost<ApiResponse<BatchLiftResponse>>(
    '/api/v1/elements/batch-lift',
    request
  );
  return response.data;
}

/**
 * 归类构件
 */
export async function classifyElement(
  elementId: string,
  request: ClassifyRequest
): Promise<ClassifyResponse> {
  const response = await apiPost<ApiResponse<ClassifyResponse>>(
    `/api/v1/elements/${elementId}/classify`,
    request
  );
  return response.data;
}

/**
 * 删除构件
 */
export async function deleteElement(elementId: string): Promise<{ id: string; deleted: boolean }> {
  const response = await apiDelete<ApiResponse<{ id: string; deleted: boolean }>>(
    `/api/v1/elements/${elementId}`
  );
  return response.data;
}

