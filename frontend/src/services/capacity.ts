/** 桥架容量 API 服务 */

import { apiGet } from './api';
import { ApiResponse } from './api';

/**
 * 桥架容量信息
 */
export interface CableTrayCapacity {
  valid: boolean;
  errors: string[];
  warnings: string[];
  power_cable_area: number; // 电力电缆总截面积（平方毫米）
  control_cable_area: number; // 控制电缆总截面积（平方毫米）
  tray_cross_section: number; // 桥架截面积（平方毫米）
  power_cable_ratio: number; // 电力电缆占比（0-1）
  control_cable_ratio: number; // 控制电缆占比（0-1）
}

/**
 * 查询桥架容量
 */
export async function getCableTrayCapacity(trayId: string): Promise<CableTrayCapacity> {
  const response = await apiGet<ApiResponse<CableTrayCapacity>>(
    `/api/v1/routing/cable-tray/${trayId}/capacity`
  );

  return response.data;
}
