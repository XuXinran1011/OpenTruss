/** 认证状态管理 */

import { create } from 'zustand';
import { getToken, getCurrentUser, clearToken, type TokenInfo } from '@/lib/auth/token';

interface AuthState {
  // 是否已登录
  isAuthenticated: boolean;
  // 当前用户信息
  currentUser: TokenInfo['user'] | null;
  // 设置认证状态
  setAuth: (tokenInfo: TokenInfo) => void;
  // 清除认证状态
  clearAuth: () => void;
  // 初始化认证状态（从localStorage读取）
  initAuth: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: false,
  currentUser: null,
  
  setAuth: (tokenInfo: TokenInfo) => {
    // 存储到localStorage
    const { setToken } = require('@/lib/auth/token');
    setToken(tokenInfo);
    
    // 更新状态
    set({
      isAuthenticated: true,
      currentUser: tokenInfo.user,
    });
  },
  
  clearAuth: () => {
    // 清除localStorage
    clearToken();
    
    // 更新状态
    set({
      isAuthenticated: false,
      currentUser: null,
    });
  },
  
  initAuth: () => {
    // 从localStorage读取
    const token = getToken();
    const user = getCurrentUser();
    
    if (token && user) {
      set({
        isAuthenticated: true,
        currentUser: user,
      });
    } else {
      set({
        isAuthenticated: false,
        currentUser: null,
      });
    }
  },
}));

