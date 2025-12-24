/**
 * Toast 通知组件
 * 
 * 用于显示操作成功/失败的提示信息
 */

'use client';

import { useEffect } from 'react';
import { cn } from '@/lib/utils';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface ToastProps {
  message: string;
  type?: ToastType;
  duration?: number;
  onClose?: () => void;
  visible?: boolean;
}

export function Toast({ 
  message, 
  type = 'info', 
  duration = 3000,
  onClose,
  visible = true 
}: ToastProps) {
  useEffect(() => {
    if (visible && duration > 0 && onClose) {
      const timer = setTimeout(() => {
        onClose();
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [visible, duration, onClose]);

  if (!visible) return null;

  const typeStyles = {
    success: 'bg-emerald-50 border-emerald-200 text-emerald-800',
    error: 'bg-red-50 border-red-200 text-red-800',
    warning: 'bg-amber-50 border-amber-200 text-amber-800',
    info: 'bg-blue-50 border-blue-200 text-blue-800',
  };

  const iconStyles = {
    success: '✓',
    error: '✕',
    warning: '⚠',
    info: 'ℹ',
  };

  return (
    <div
      className={cn(
        'fixed top-4 right-4 z-50 px-4 py-3 rounded-lg border shadow-lg',
        'flex items-center gap-2 min-w-[300px] max-w-[500px]',
        'animate-in slide-in-from-top-5 fade-in-0',
        typeStyles[type]
      )}
      role="alert"
    >
      <span className="text-lg font-bold">{iconStyles[type]}</span>
      <p className="flex-1 text-sm font-medium">{message}</p>
      {onClose && (
        <button
          onClick={onClose}
          className="ml-2 text-current opacity-60 hover:opacity-100 transition-opacity"
          aria-label="关闭"
        >
          ✕
        </button>
      )}
    </div>
  );
}

/**
 * Toast 容器组件
 * 用于管理多个 Toast 通知
 */
export interface ToastItem {
  id: string;
  message: string;
  type?: ToastType;
  duration?: number;
}

interface ToastContainerProps {
  toasts: ToastItem[];
  onRemove: (id: string) => void;
}

export function ToastContainer({ toasts, onRemove }: ToastContainerProps) {
  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      {toasts.map((toast) => (
        <Toast
          key={toast.id}
          message={toast.message}
          type={toast.type}
          duration={toast.duration}
          onClose={() => onRemove(toast.id)}
          visible={true}
        />
      ))}
    </div>
  );
}

