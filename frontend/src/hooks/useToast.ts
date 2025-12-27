/**
 * Toast 通知 Hook
 * 
 * 用于管理 Toast 通知的显示和隐藏
 */

import { useState, useCallback } from 'react';
import { ToastItem } from '@/components/ui/Toast';

export function useToast() {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  }, []);

  const showToast = useCallback((
    message: string,
    type: ToastItem['type'] = 'info',
    duration: number = 3000
  ) => {
    const id = `${Date.now()}-${Math.random()}`;
    const newToast: ToastItem = {
      id,
      message,
      type,
      duration,
    };

    setToasts((prev) => [...prev, newToast]);

    // 自动移除
    if (duration > 0) {
      setTimeout(() => {
        removeToast(id);
      }, duration);
    }

    return id;
  }, [removeToast]);

  const clearAll = useCallback(() => {
    setToasts([]);
  }, []);

  return {
    toasts,
    showToast,
    removeToast,
    clearAll,
  };
}

