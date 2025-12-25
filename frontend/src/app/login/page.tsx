/** 登录页面 */

'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { LoginForm } from '@/components/auth/LoginForm';
import { useAuthStore } from '@/stores/auth';
import { ToastProvider } from '@/providers/ToastProvider';

export default function LoginPage() {
  const router = useRouter();
  const { isAuthenticated, initAuth } = useAuthStore();

  // 初始化认证状态
  useEffect(() => {
    initAuth();
  }, [initAuth]);

  // 如果已登录，重定向到工作台
  useEffect(() => {
    if (isAuthenticated) {
      router.push('/workbench');
    }
  }, [isAuthenticated, router]);

  return (
    <ToastProvider>
      <div className="min-h-screen flex items-center justify-center bg-zinc-50">
        <div className="w-full max-w-md">
          <div className="bg-white rounded-lg shadow-lg p-8">
            {/* Logo/标题 */}
            <div className="text-center mb-8">
              <h1 className="text-2xl font-bold text-zinc-900 mb-2">OpenTruss</h1>
              <p className="text-sm text-zinc-600">面向建筑施工行业的生成式 BIM 中间件</p>
            </div>

            {/* 登录表单 */}
            <LoginForm />
          </div>
        </div>
      </div>
    </ToastProvider>
  );
}

