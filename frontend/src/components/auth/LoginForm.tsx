/** 登录表单组件 */

'use client';

import { useState, FormEvent } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useToastContext } from '@/providers/ToastProvider';

export function LoginForm() {
  const { login, isLoading, error, clearError } = useAuth();
  const { showToast } = useToastContext();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    clearError();
    
    if (!username || !password) {
      showToast('请输入用户名和密码', 'error');
      return;
    }
    
    try {
      await login({ username, password });
      showToast('登录成功', 'success');
    } catch (err) {
      // 错误已由useAuth处理，这里可以显示额外的提示
      if (error) {
        showToast(error.message, 'error');
      }
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* 用户名输入 */}
      <div>
        <label htmlFor="username" className="block text-sm font-medium text-zinc-700 mb-2">
          用户名
        </label>
        <input
          id="username"
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          disabled={isLoading}
          className="w-full px-3 py-2 border border-zinc-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-600 focus:border-transparent disabled:bg-zinc-100 disabled:cursor-not-allowed"
          placeholder="请输入用户名"
          autoComplete="username"
          required
        />
      </div>

      {/* 密码输入 */}
      <div>
        <label htmlFor="password" className="block text-sm font-medium text-zinc-700 mb-2">
          密码
        </label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          disabled={isLoading}
          className="w-full px-3 py-2 border border-zinc-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-600 focus:border-transparent disabled:bg-zinc-100 disabled:cursor-not-allowed"
          placeholder="请输入密码"
          autoComplete="current-password"
          required
        />
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-800">
          {error.message}
        </div>
      )}

      {/* 登录按钮 */}
      <button
        type="submit"
        disabled={isLoading}
        className="w-full bg-zinc-900 text-white py-2 px-4 rounded-md hover:bg-zinc-800 focus:outline-none focus:ring-2 focus:ring-orange-600 focus:ring-offset-2 disabled:bg-zinc-400 disabled:cursor-not-allowed transition-colors"
      >
        {isLoading ? '登录中...' : '登录'}
      </button>

      {/* 测试账户提示（开发环境） */}
      {process.env.NODE_ENV === 'development' && (
        <div className="mt-4 p-3 bg-zinc-50 border border-zinc-200 rounded-md text-xs text-zinc-600">
          <p className="font-medium mb-2">测试账户：</p>
          <ul className="space-y-1">
            <li>管理员: admin / admin123</li>
            <li>工程师: editor / editor123</li>
            <li>负责人: approver / approver123</li>
            <li>项目经理: pm / pm123</li>
          </ul>
        </div>
      )}
    </form>
  );
}

