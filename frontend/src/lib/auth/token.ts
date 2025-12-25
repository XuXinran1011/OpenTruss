/** Token存储和管理工具 */

const TOKEN_KEY = 'opentruss_access_token';
const USER_KEY = 'opentruss_user';

/**
 * Token信息
 */
export interface TokenInfo {
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
 * 存储token
 * 
 * @param tokenInfo - Token信息
 */
export function setToken(tokenInfo: TokenInfo): void {
  if (typeof window === 'undefined') {
    return; // SSR环境
  }
  localStorage.setItem(TOKEN_KEY, tokenInfo.access_token);
  localStorage.setItem(USER_KEY, JSON.stringify(tokenInfo.user));
}

/**
 * 获取token
 * 
 * @returns Token字符串，如果不存在则返回null
 */
export function getToken(): string | null {
  if (typeof window === 'undefined') {
    return null; // SSR环境
  }
  return localStorage.getItem(TOKEN_KEY);
}

/**
 * 获取当前用户信息
 * 
 * @returns 用户信息，如果不存在则返回null
 */
export function getCurrentUser(): TokenInfo['user'] | null {
  if (typeof window === 'undefined') {
    return null; // SSR环境
  }
  const userStr = localStorage.getItem(USER_KEY);
  if (!userStr) {
    return null;
  }
  try {
    return JSON.parse(userStr);
  } catch {
    return null;
  }
}

/**
 * 清除token
 */
export function clearToken(): void {
  if (typeof window === 'undefined') {
    return; // SSR环境
  }
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

/**
 * 检查是否已登录
 * 
 * @returns 是否已登录
 */
export function isAuthenticated(): boolean {
  return getToken() !== null;
}

