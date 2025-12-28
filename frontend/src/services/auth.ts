/** 认证API服务 */

import { apiPost, apiGet, ApiResponse } from './api';
import { TokenInfo } from '@/lib/auth/token';

/**
 * 登录请求
 */
export interface LoginRequest {
  username: string;
  password: string;
}

/**
 * 登录响应
 */
export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: {
    id: string;
    username: string;
    email?: string;
    role: string;
    name?: string;
  };
}

/**
 * 用户信息
 */
export interface UserInfo {
  id: string;
  username: string;
  email?: string;
  role: string;
  name?: string;
}

/**
 * 用户登录
 * 
 * @param credentials - 登录凭据（用户名和密码）
 * @returns Token信息和用户信息
 */
export async function login(credentials: LoginRequest): Promise<TokenInfo> {
  const response = await apiPost<ApiResponse<LoginResponse>>(
    '/api/v1/auth/login',
    credentials
  );
  
  return response.data;
}

/**
 * 获取当前用户信息
 * 
 * @returns 当前用户信息
 */
export async function getCurrentUserInfo(): Promise<UserInfo> {
  const response = await apiGet<ApiResponse<UserInfo>>('/api/v1/auth/me');
  return response.data;
}

/**
 * 用户登出
 * 
 * 即使API调用失败也不会抛出错误，确保logout操作总是成功完成
 */
export async function logout(): Promise<void> {
  try {
    await apiPost('/api/v1/auth/logout');
  } catch (error) {
    // 静默处理错误，确保logout操作不会因为API失败而中断
    // 即使服务器返回错误，也要清除本地token
    console.warn('Logout API call failed, but continuing with local cleanup:', error);
  }
}

