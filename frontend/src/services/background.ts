/** 底图管理 API 服务 */

import { apiGet, apiDelete } from './api';
import type { ApiResponse } from './api';
import { API_CONFIG } from '@/lib/api/config';

export interface BackgroundInfo {
  id: string;
  filename: string;
  url: string;
  size: number;
  content_type: string;
  created_at: string;
}

export interface BackgroundListResponse {
  items: BackgroundInfo[];
  total: number;
}

const API_BASE = '/api/v1/background';

/**
 * 上传底图文件
 * 
 * @param file - 要上传的文件
 * @returns 底图信息
 * @throws {ApiError} 如果请求失败
 */
export async function uploadBackground(file: File): Promise<BackgroundInfo> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    headers: {
      // 不要设置 Content-Type，让浏览器自动设置（包含 boundary）
      'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
    },
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '上传失败' }));
    throw new Error(error.detail || `上传失败: ${response.statusText}`);
  }

  const data = await response.json();
  return data;
}

/**
 * 获取底图列表
 * 
 * @returns 底图列表
 * @throws {ApiError} 如果请求失败
 */
export async function listBackgrounds(): Promise<BackgroundListResponse> {
  const response = await apiGet<ApiResponse<BackgroundListResponse>>(API_BASE);
  return response.data;
}

/**
 * 获取底图URL（用于在img标签中使用）
 * 
 * @param backgroundId - 底图ID
 * @returns 底图URL
 */
export function getBackgroundUrl(backgroundId: string): string {
  return `${API_CONFIG.baseURL}${API_BASE}/${backgroundId}`;
}

/**
 * 删除底图
 * 
 * @param backgroundId - 底图ID
 * @returns 删除结果
 * @throws {ApiError} 如果请求失败
 */
export async function deleteBackground(backgroundId: string): Promise<{ id: string; deleted: boolean }> {
  const response = await apiDelete<ApiResponse<{ id: string; deleted: boolean }>>(
    `${API_BASE}/${backgroundId}`
  );
  return response.data;
}

