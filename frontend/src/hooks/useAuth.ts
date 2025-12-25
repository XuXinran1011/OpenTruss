/** 认证Hook */

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { login, logout as logoutApi, type LoginRequest } from '@/services/auth';
import { useAuthStore } from '@/stores/auth';
import { ApiError } from '@/services/api';

export interface AuthError {
  message: string;
}

/**
 * 认证Hook
 * 
 * 提供登录、登出和认证状态管理功能
 */
export function useAuth() {
  const router = useRouter();
  const { setAuth, clearAuth, isAuthenticated, currentUser } = useAuthStore();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<AuthError | null>(null);

  /**
   * 登录
   */
  const loginHandler = useCallback(async (credentials: LoginRequest) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const tokenInfo = await login(credentials);
      
      // 存储token并更新状态
      setAuth(tokenInfo);
      
      // 跳转到工作台
      router.push('/workbench');
      
      return tokenInfo;
    } catch (err) {
      let errorMessage = '登录失败，请检查用户名和密码';
      
      if (err instanceof ApiError) {
        errorMessage = err.message || errorMessage;
      } else if (err instanceof Error) {
        errorMessage = err.message;
      }
      
      setError({ message: errorMessage });
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [setAuth, router]);

  /**
   * 登出
   */
  const logoutHandler = useCallback(async () => {
    try {
      // 调用登出API（可选，主要用于记录日志）
      await logoutApi().catch(() => {
        // 即使API调用失败，也要清除本地token
      });
    } finally {
      // 清除本地认证状态
      clearAuth();
      
      // 跳转到登录页
      router.push('/login');
    }
  }, [clearAuth, router]);

  /**
   * 清除错误
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    // 状态
    isAuthenticated,
    currentUser,
    isLoading,
    error,
    
    // 方法
    login: loginHandler,
    logout: logoutHandler,
    clearError,
  };
}

