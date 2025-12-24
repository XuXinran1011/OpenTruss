/**
 * Toast 通知提供者
 * 
 * 提供全局的 Toast 通知功能
 */

'use client';

import { createContext, useContext, ReactNode } from 'react';
import { useToast } from '@/hooks/useToast';
import { ToastContainer, ToastItem } from '@/components/ui/Toast';

interface ToastContextType {
  showToast: (message: string, type?: ToastItem['type'], duration?: number) => string;
  removeToast: (id: string) => void;
  clearAll: () => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: ReactNode }) {
  const { toasts, showToast, removeToast, clearAll } = useToast();

  return (
    <ToastContext.Provider value={{ showToast, removeToast, clearAll }}>
      {children}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </ToastContext.Provider>
  );
}

export function useToastContext() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToastContext must be used within ToastProvider');
  }
  return context;
}

