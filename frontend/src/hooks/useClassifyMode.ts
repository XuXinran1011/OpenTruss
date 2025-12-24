/** Classify Mode Hook */

import { useState, useCallback } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { classifyElement, ClassifyRequest } from '@/services/elements';
import { useWorkbenchStore } from '@/stores/workbench';
import { ApiError } from '@/services/api';

export interface ClassifyModeError {
  message: string;
  elementId?: string;
  itemId?: string;
}

export function useClassifyMode() {
  const queryClient = useQueryClient();
  const { selectedElementIds, clearSelection } = useWorkbenchStore();
  const [error, setError] = useState<ClassifyModeError | null>(null);
  const [successCount, setSuccessCount] = useState(0);
  const [failedCount, setFailedCount] = useState(0);

  const classifyMutation = useMutation({
    mutationFn: ({ elementId, request }: { elementId: string; request: ClassifyRequest }) =>
      classifyElement(elementId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['elements'] });
      queryClient.invalidateQueries({ queryKey: ['hierarchy'] });
      setSuccessCount(prev => prev + 1);
    },
    onError: (err: unknown, variables) => {
      setFailedCount(prev => prev + 1);
      let errorMessage = '构件归类失败';
      if (err instanceof ApiError) {
        errorMessage = err.message || `归类失败: ${err.statusCode || '未知错误'}`;
      } else if (err instanceof Error) {
        errorMessage = err.message;
      }
      setError({
        message: errorMessage,
        elementId: variables.elementId,
        itemId: variables.request.item_id,
      });
    },
  });

  const classify = useCallback((itemId: string, elementIds?: string[]) => {
    // 验证输入
    if (!itemId) {
      setError({ message: '分项 ID 不能为空' });
      return;
    }

    const idsToClassify = elementIds || selectedElementIds;
    if (idsToClassify.length === 0) {
      setError({ message: '请至少选择一个构件' });
      return;
    }

    // 重置计数
    setSuccessCount(0);
    setFailedCount(0);
    setError(null);

    // 批量归类
    idsToClassify.forEach((elementId) => {
      classifyMutation.mutate({ elementId, request: { item_id: itemId } });
    });

    // 归类后清空选择
    if (!elementIds) {
      clearSelection();
    }
  }, [selectedElementIds, classifyMutation, clearSelection]);

  const clearError = useCallback(() => {
    setError(null);
    setSuccessCount(0);
    setFailedCount(0);
  }, []);

  return {
    classify,
    isClassifying: classifyMutation.isPending,
    error,
    successCount,
    failedCount,
    clearError,
  };
}

