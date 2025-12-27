/** 支吊架 API 服务 */

import { apiGet, apiPost } from './api';
import { ApiResponse } from './api';

/**
 * 生成支吊架请求
 */
export interface GenerateHangersRequest {
  element_ids: string[];
  seismic_grade?: string; // '6度', '7度', '8度', '9度'
  create_nodes?: boolean;
}

/**
 * 生成综合支吊架请求
 */
export interface GenerateIntegratedHangersRequest {
  space_id: string;
  element_ids: string[];
  seismic_grade?: string;
  create_nodes?: boolean;
}

/**
 * 支吊架信息
 */
export interface HangerInfo {
  id: string;
  position: number[]; // [x, y, z]
  hanger_type: '支架' | '吊架';
  standard_code: string;
  detail_code: string;
  support_interval?: number;
}

/**
 * 综合支吊架信息
 */
export interface IntegratedHangerInfo {
  id: string;
  position: number[]; // [x, y, z]
  hanger_type: '支架' | '吊架';
  standard_code: string;
  detail_code: string;
  supported_element_ids: string[];
  space_id: string;
}

/**
 * 生成支吊架响应
 */
export interface GenerateHangersResponse {
  element_id: string;
  hanger_count: number;
  hangers: HangerInfo[];
}

/**
 * 生成综合支吊架响应
 */
export interface GenerateIntegratedHangersResponse {
  space_id: string;
  hanger_count: number;
  hangers: IntegratedHangerInfo[];
}

/**
 * 元素的支吊架列表响应
 */
export interface ElementHangersResponse {
  element_id: string;
  hangers: HangerInfo[];
  integrated_hanger?: IntegratedHangerInfo;
}

/**
 * 生成支吊架
 */
export async function generateHangers(
  request: GenerateHangersRequest
): Promise<{ generated_hangers: HangerInfo[]; warnings: string[]; errors: string[] }> {
  const response = await apiPost<ApiResponse<{
    generated_hangers: HangerInfo[];
    warnings: string[];
    errors: string[];
  }>>('/api/v1/hangers/generate', request);

  return response.data;
}

/**
 * 生成综合支吊架
 */
export async function generateIntegratedHangers(
  request: GenerateIntegratedHangersRequest
): Promise<{ generated_integrated_hangers: IntegratedHangerInfo[]; warnings: string[]; errors: string[] }> {
  const response = await apiPost<ApiResponse<{
    generated_integrated_hangers: IntegratedHangerInfo[];
    warnings: string[];
    errors: string[];
  }>>(
    '/api/v1/hangers/generate-integrated',
    request
  );

  return response.data;
}

/**
 * 查询元素的支吊架
 */
export async function getElementHangers(elementId?: string, spaceId?: string): Promise<{ hangers: HangerInfo[]; integrated_hangers: IntegratedHangerInfo[] }> {
  const queryParams = new URLSearchParams();
  if (elementId) queryParams.append('element_id', elementId);
  if (spaceId) queryParams.append('space_id', spaceId);
  
  const response = await apiGet<ApiResponse<{
    hangers: HangerInfo[];
    integrated_hangers: IntegratedHangerInfo[];
  }>>(
    `/api/v1/hangers/query?${queryParams.toString()}`
  );

  return response.data;
}
