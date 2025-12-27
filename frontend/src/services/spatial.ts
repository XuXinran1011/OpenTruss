/** 空间 API 服务 */

import { apiGet, apiPut } from './api';
import { ApiResponse } from './api';

/**
 * 设置空间综合支吊架请求
 */
export interface SetSpaceIntegratedHangerRequest {
  use_integrated_hanger: boolean;
}

/**
 * 空间综合支吊架配置响应
 */
export interface SpaceIntegratedHangerResponse {
  space_id: string;
  use_integrated_hanger: boolean;
  updated_at?: string;
}

/**
 * 设置空间综合支吊架
 */
export async function setSpaceIntegratedHanger(
  spaceId: string,
  request: SetSpaceIntegratedHangerRequest
): Promise<SpaceIntegratedHangerResponse> {
  const response = await apiPut<ApiResponse<SpaceIntegratedHangerResponse>>(
    `/api/v1/spaces/${spaceId}/integrated-hanger`,
    request
  );

  return response.data;
}

/**
 * 获取空间综合支吊架配置
 */
export async function getSpaceIntegratedHanger(
  spaceId: string
): Promise<SpaceIntegratedHangerResponse> {
  const response = await apiGet<ApiResponse<SpaceIntegratedHangerResponse>>(
    `/api/v1/spaces/${spaceId}/integrated-hanger`
  );

  return response.data;
}
