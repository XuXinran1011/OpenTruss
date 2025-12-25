/** IFC 导出 API 服务 */

import { API_CONFIG } from '@/lib/api/config';

export interface ApiResponse<T> {
  status: string;
  data: T;
}

/**
 * 导出检验批为 IFC 文件
 * 返回 Blob 对象，用于下载
 */
export async function exportLotToIFC(lotId: string): Promise<Blob> {
  const response = await fetch(
    `${API_CONFIG.baseURL}/api/v1/export/ifc?inspection_lot_id=${lotId}`,
    {
      method: 'GET',
    }
  );

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: '导出失败' }));
    throw new Error(errorData.detail || `导出失败: ${response.statusText}`);
  }

  return response.blob();
}

/**
 * 导出项目为 IFC 文件
 * 返回 Blob 对象，用于下载
 */
export async function exportProjectToIFC(projectId: string): Promise<Blob> {
  const response = await fetch(
    `${API_CONFIG.baseURL}/api/v1/export/ifc?project_id=${projectId}`,
    {
      method: 'GET',
    }
  );

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: '导出失败' }));
    throw new Error(errorData.detail || `导出失败: ${response.statusText}`);
  }

  return response.blob();
}

/**
 * 批量导出多个检验批为 IFC 文件
 * 返回 Blob 对象，用于下载
 */
export async function batchExportLotsToIFC(lotIds: string[]): Promise<Blob> {
  const response = await fetch(
    `${API_CONFIG.baseURL}/api/v1/export/ifc/batch`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ lot_ids: lotIds }),
    }
  );

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: '批量导出失败' }));
    throw new Error(errorData.detail || `批量导出失败: ${response.statusText}`);
  }

  return response.blob();
}

/**
 * 下载 Blob 为文件
 */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

