/** 键盘快捷键 Hook */

'use client';

import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useWorkbenchStore } from '@/stores/workbench';
import { useCanvasStore } from '@/stores/canvas';
import { deleteElement } from '@/services/elements';
import { useToastContext } from '@/providers/ToastProvider';

export function useKeyboardShortcuts() {
  const { mode, setMode, selectedElementIds, setSelectedElementIds } = useWorkbenchStore();
  const { dwgOpacity, setDwgOpacity } = useCanvasStore();
  const queryClient = useQueryClient();
  const { showToast } = useToastContext();

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // 如果焦点在输入框、文本区域等可编辑元素上，不处理快捷键
      const target = event.target as HTMLElement;
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable
      ) {
        return;
      }

      // 处理快捷键
      switch (event.key.toLowerCase()) {
        case 't':
          // T: 切换到 Trace Mode
          event.preventDefault();
          setMode('trace');
          break;

        case 'l':
          // L: 切换到 Lift Mode
          event.preventDefault();
          setMode('lift');
          break;

        case 'c':
          // C: 切换到 Classify Mode
          event.preventDefault();
          setMode('classify');
          break;

        case 'delete':
        case 'backspace':
          // Delete/Backspace: 删除选中构件
          if (selectedElementIds.length > 0) {
            event.preventDefault();
            // 确认对话框
            const confirmed = window.confirm(
              `确定要删除选中的 ${selectedElementIds.length} 个构件吗？此操作不可撤销。`
            );
            if (confirmed) {
              // 批量删除
              Promise.all(
                selectedElementIds.map((id) =>
                  deleteElement(id).catch((error) => {
                    console.error(`Failed to delete element ${id}:`, error);
                    showToast(`删除构件 ${id} 失败: ${error.message}`, 'error');
                    return null;
                  })
                )
              ).then((results) => {
                const successCount = results.filter((r) => r !== null).length;
                const failedCount = selectedElementIds.length - successCount;
                if (successCount > 0) {
                  showToast(
                    `成功删除 ${successCount} 个构件${failedCount > 0 ? `，${failedCount} 个失败` : ''}`,
                    failedCount > 0 ? 'warning' : 'success'
                  );
                  // 刷新相关查询
                  queryClient.invalidateQueries({ queryKey: ['elements'] });
                  queryClient.invalidateQueries({ queryKey: ['hierarchy'] });
                  // 清空选择
                  setSelectedElementIds([]);
                }
              });
            }
          }
          break;

        case '[':
          // [: 减少 DWG 底图透明度
          if (mode === 'trace') {
            event.preventDefault();
            // dwgOpacity 是 0-1 范围，每次减少 0.1
            setDwgOpacity(Math.max(0, dwgOpacity - 0.1));
          }
          break;

        case ']':
          // ]: 增加 DWG 底图透明度
          if (mode === 'trace') {
            event.preventDefault();
            // dwgOpacity 是 0-1 范围，每次增加 0.1
            setDwgOpacity(Math.min(1, dwgOpacity + 0.1));
          }
          break;

        case 'escape':
          // Escape: 清空选择
          if (selectedElementIds.length > 0) {
            event.preventDefault();
            setSelectedElementIds([]);
          }
          break;

        default:
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [mode, setMode, selectedElementIds, setSelectedElementIds, dwgOpacity, setDwgOpacity, queryClient, showToast]);
}

