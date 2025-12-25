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
 */
export async function logout(): Promise<void> {
  await apiPost('/api/v1/auth/logout');
}

