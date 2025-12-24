/** Lift Mode Hook */

import { useState, useCallback, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { batchLiftElements, BatchLiftRequest } from '@/services/elements';
import { useWorkbenchStore } from '@/stores/workbench';
import { ApiError } from '@/services/api';

export interface LiftModeError {
  message: string;
  elementIds?: string[];
}

export function useLiftMode() {
  const queryClient = useQueryClient();
  const { selectedElementIds } = useWorkbenchStore();
  const [error, setError] = useState<LiftModeError | null>(null);

  const batchLiftMutation = useMutation({
    mutationFn: (request: BatchLiftRequest) => batchLiftElements(request),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['elements'] });
      queryClient.invalidateQueries({ queryKey: ['element'] });
      
      // 如果部分更新失败，设置错误（由组件通过 useEffect 显示 Toast）
      if (data.updated_count < variables.element_ids.length) {
        const failedCount = variables.element_ids.length - data.updated_count;
        setError({
          message: `成功更新 ${data.updated_count} 个构件，${failedCount} 个构件更新失败`,
          elementIds: variables.element_ids.filter(id => !data.element_ids.includes(id)),
        });
      } else {
        // 全部成功，清空错误状态
        setError(null);
      }
    },
    onError: (err: unknown) => {
      let errorMessage = '批量设置 Z 轴参数失败';
      if (err instanceof ApiError) {
        errorMessage = err.message || `批量操作失败: ${err.statusCode || '未知错误'}`;
      } else if (err instanceof Error) {
        errorMessage = err.message;
      }
      setError({ message: errorMessage, elementIds: selectedElementIds });
    },
  });

  const batchLift = useCallback((height?: number, baseOffset?: number, material?: string) => {
    // 验证输入
    if (selectedElementIds.length === 0) {
      setError({ message: '请至少选择一个构件' });
      return;
    }

    // 验证参数至少有一个
    if (height === undefined && baseOffset === undefined && !material) {
      setError({ message: '请至少设置一个参数（高度、基础偏移或材质）' });
      return;
    }

    // 验证数值范围
    if (height !== undefined && (height < 0 || height > 1000)) {
      setError({ message: '高度必须在 0-1000 米之间' });
      return;
    }
    if (baseOffset !== undefined && (baseOffset < -100 || baseOffset > 100)) {
      setError({ message: '基础偏移必须在 -100 到 100 米之间' });
      return;
    }

    setError(null);
    batchLiftMutation.mutate({
      element_ids: selectedElementIds,
      height,
      base_offset: baseOffset,
      material,
    });
  }, [selectedElementIds, batchLiftMutation]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    batchLift,
    isLifting: batchLiftMutation.isPending,
    error,
    clearError,
  };
}

