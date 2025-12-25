/** 路由保护组件 */

'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/auth';

interface AuthGuardProps {
  children: React.ReactNode;
}

/**
 * 认证保护组件
 * 
 * 检查用户是否已登录，未登录时重定向到登录页
 */
export function AuthGuard({ children }: AuthGuardProps) {
  const router = useRouter();
  const { isAuthenticated, initAuth } = useAuthStore();

  // 初始化认证状态
  useEffect(() => {
    initAuth();
  }, [initAuth]);

  // 检查认证状态
  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, router]);

  // 如果未登录，不渲染子组件
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-zinc-50">
        <div className="text-center">
          <p className="text-zinc-600">正在跳转到登录页...</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

