/** 
 * Trace Mode Hook
 * 
 * 提供 Trace Mode 下的拓扑更新功能，用于修复 2D 拓扑关系
 */

import { useState, useCallback } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { updateElementTopology, TopologyUpdateRequest } from '@/services/elements';
import { useWorkbenchStore } from '@/stores/workbench';
import { ApiError } from '@/services/api';

/**
 * Trace Mode 错误信息
 */
export interface TraceModeError {
  message: string;
  elementId?: string;
}

/**
 * Trace Mode Hook
 * 
 * 用于在 Trace Mode 下更新构件的拓扑关系（几何坐标和连接关系）
 * 
 * @returns Trace Mode 相关的状态和方法
 * - updateTopology: 更新构件拓扑关系的函数
 * - isUpdating: 是否正在更新
 * - error: 错误信息
 * - clearError: 清除错误信息的函数
 */
export function useTraceMode() {
  const queryClient = useQueryClient();
  const { selectedElementIds } = useWorkbenchStore();
  const [error, setError] = useState<TraceModeError | null>(null);

  const updateTopologyMutation = useMutation({
    mutationFn: ({ elementId, request }: { elementId: string; request: TopologyUpdateRequest }) =>
      updateElementTopology(elementId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['elements'] });
      queryClient.invalidateQueries({ queryKey: ['element'] });
      setError(null);
      // 注意：成功提示由组件通过 useEffect 监听 error 的变化来处理
    },
    onError: (err: unknown) => {
      let errorMessage = '拓扑更新失败';
      if (err instanceof ApiError) {
        errorMessage = err.message || `拓扑更新失败: ${err.statusCode || '未知错误'}`;
      } else if (err instanceof Error) {
        errorMessage = err.message;
      }
      setError({ message: errorMessage });
    },
  });

  const updateTopology = useCallback((elementId: string, request: TopologyUpdateRequest) => {
    // 验证输入
    if (!elementId) {
      setError({ message: '构件 ID 不能为空', elementId });
      return;
    }
    if (request.geometry && (!request.geometry.coordinates || request.geometry.coordinates.length < 2)) {
      setError({ message: '几何坐标无效，至少需要 2 个点', elementId });
      return;
    }
    
    setError(null);
    updateTopologyMutation.mutate({ elementId, request });
  }, [updateTopologyMutation]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    updateTopology,
    isUpdating: updateTopologyMutation.isPending,
    error,
    clearError,
  };
}

