/** API 服务基础封装 */

import { API_CONFIG } from '@/lib/api/config';
import { getToken } from '@/lib/auth/token';

/**
 * API 响应基础结构
 */
export interface ApiResponse<T = any> {
  status: string;
  data: T;
}

/**
 * 分页响应
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

/**
 * 通用 API 错误
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public response?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * 通用 fetch 封装
 */
export async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_CONFIG.baseURL}${endpoint}`;
  
  // 获取token并添加到请求头
  const token = getToken();
  const headers: Record<string, string> = {
    ...(API_CONFIG.headers as Record<string, string>),
    ...(options.headers as Record<string, string>),
  };
  
  // 如果存在token，添加Authorization header
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const config: RequestInit = {
    ...options,
    headers,
  };
  
  try {
    const response = await fetch(url, config);
    
    // 处理401未授权错误（token过期或无效）
    if (response.status === 401) {
      // 清除token，让用户重新登录
      if (typeof window !== 'undefined') {
        const { clearToken } = await import('@/lib/auth/token');
        clearToken();
        // 可选：重定向到登录页
        // window.location.href = '/login';
      }
    }
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(
        errorData.detail || `HTTP error! status: ${response.status}`,
        response.status,
        errorData
      );
    }
    
    const data = await response.json();
    return data as T;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(
      `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`
    );
  }
}

/**
 * GET 请求
 */
export async function apiGet<T>(endpoint: string): Promise<T> {
  return apiFetch<T>(endpoint, { method: 'GET' });
}

/**
 * POST 请求
 */
export async function apiPost<T>(endpoint: string, body?: any): Promise<T> {
  return apiFetch<T>(endpoint, {
    method: 'POST',
    body: body ? JSON.stringify(body) : undefined,
  });
}

/**
 * PATCH 请求
 */
export async function apiPatch<T>(endpoint: string, body?: any): Promise<T> {
  return apiFetch<T>(endpoint, {
    method: 'PATCH',
    body: body ? JSON.stringify(body) : undefined,
  });
}

/**
 * DELETE 请求
 */
export async function apiDelete<T>(endpoint: string): Promise<T> {
  return apiFetch<T>(endpoint, { method: 'DELETE' });
}

