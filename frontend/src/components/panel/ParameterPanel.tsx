/** 参数修正面板组件 */

'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useWorkbenchStore } from '@/stores/workbench';
import { getElementDetail, updateElement, batchLiftElements, ElementDetail } from '@/services/elements';
import { useLiftMode } from '@/hooks/useLiftMode';
import { useToastContext } from '@/providers/ToastProvider';
import { cn } from '@/lib/utils';

export function ParameterPanel() {
  const { selectedElementIds, mode } = useWorkbenchStore();
  const queryClient = useQueryClient();
  const { batchLift, isLifting, error: liftError, clearError: clearLiftError } = useLiftMode();
  const { showToast } = useToastContext();
  const [lastBatchSuccess, setLastBatchSuccess] = useState(false);
  const [localValues, setLocalValues] = useState({
    height: '',
    baseOffset: '',
    material: '',
  });

  // 显示错误和警告提示
  useEffect(() => {
    if (liftError) {
      // 根据错误消息判断是错误还是警告（部分成功）
      const isWarning = liftError.message.includes('成功更新') && liftError.message.includes('失败');
      showToast(liftError.message, isWarning ? 'warning' : 'error');
      clearLiftError();
      setLastBatchSuccess(false);
    }
  }, [liftError, showToast, clearLiftError]);

  // 显示批量操作成功提示（全部成功时）
  useEffect(() => {
    if (!isLifting && !liftError && lastBatchSuccess && selectedElementIds.length > 1) {
      showToast(`成功更新 ${selectedElementIds.length} 个构件`, 'success');
      setLastBatchSuccess(false);
    }
  }, [isLifting, liftError, lastBatchSuccess, selectedElementIds.length, showToast]);

  // 获取第一个选中构件的详情（单个编辑时）
  const firstElementId = selectedElementIds[0];
  const { data: elementDetail } = useQuery({
    queryKey: ['element', firstElementId],
    queryFn: () => getElementDetail(firstElementId),
    enabled: !!firstElementId && selectedElementIds.length === 1,
  });

  // 更新本地值（使用useEffect避免在render中直接调用setState）
  useEffect(() => {
    if (elementDetail && selectedElementIds.length === 1) {
      setLocalValues({
        height: elementDetail.height?.toString() || '',
        baseOffset: elementDetail.base_offset?.toString() || '',
        material: elementDetail.material || '',
      });
    } else if (selectedElementIds.length !== 1) {
      // 如果不是单个选择，清空本地值
      setLocalValues({ height: '', baseOffset: '', material: '' });
    }
  }, [elementDetail, selectedElementIds.length]);

  // 单个构件更新
  const updateMutation = useMutation({
    mutationFn: (data: { height?: number; base_offset?: number; material?: string }) =>
      updateElement(firstElementId!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['element', firstElementId] });
      queryClient.invalidateQueries({ queryKey: ['elements'] });
      showToast('参数更新成功', 'success');
    },
    onError: (error: unknown) => {
      const errorMessage = error instanceof Error ? error.message : '参数更新失败';
      showToast(errorMessage, 'error');
    },
  });

  // 批量 Lift 更新（使用 hook）
  // 注意：batchLiftMutation 已由 useLiftMode hook 管理

  const handleSave = () => {
    if (mode === 'lift' && selectedElementIds.length > 1) {
      // 批量操作
      setLastBatchSuccess(true); // 标记批量操作开始
      batchLift(
        localValues.height ? parseFloat(localValues.height) : undefined,
        localValues.baseOffset ? parseFloat(localValues.baseOffset) : undefined,
        localValues.material || undefined
      );
      // 清空表单
      setLocalValues({ height: '', baseOffset: '', material: '' });
    } else if (firstElementId) {
      // 单个更新
      updateMutation.mutate({
        height: localValues.height ? parseFloat(localValues.height) : undefined,
        base_offset: localValues.baseOffset ? parseFloat(localValues.baseOffset) : undefined,
        material: localValues.material || undefined,
      });
    }
  };

  const handleCancel = () => {
    if (elementDetail) {
      setLocalValues({
        height: elementDetail.height?.toString() || '',
        baseOffset: elementDetail.base_offset?.toString() || '',
        material: elementDetail.material || '',
      });
    } else {
      setLocalValues({ height: '', baseOffset: '', material: '' });
    }
  };

  if (selectedElementIds.length === 0) {
    return (
      <div className="p-4 text-sm text-zinc-500 text-center">请选择一个构件</div>
    );
  }

  const isBatchMode = mode === 'lift' && selectedElementIds.length > 1;

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-zinc-200">
        <h3 className="text-sm font-medium text-zinc-900">
          {isBatchMode
            ? `批量操作 (${selectedElementIds.length} 个构件)`
            : `构件: ${firstElementId}`}
        </h3>
        {elementDetail && (
          <div className="mt-2 space-y-1 text-xs text-zinc-600">
            <div>类型: {elementDetail.speckle_type}</div>
            <div>状态: {elementDetail.status}</div>
            {elementDetail.level_id && <div>楼层: {elementDetail.level_id}</div>}
          </div>
        )}
      </div>

      <div className="flex-1 overflow-auto p-4 space-y-4">
        {/* Z 轴参数（Lift Mode） */}
        {(mode === 'lift' || mode === 'trace') && (
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-zinc-900">Z 轴参数</h4>

            <div>
              <label className="block text-xs text-zinc-600 mb-1">高度 (m)</label>
              <input
                type="number"
                step="0.01"
                value={localValues.height}
                onChange={(e) => setLocalValues({ ...localValues, height: e.target.value })}
                className="w-full px-3 py-1.5 text-sm border border-zinc-300 rounded focus:outline-none focus:ring-2 focus:ring-zinc-900 focus:border-transparent"
                placeholder="3.0"
              />
            </div>

            <div>
              <label className="block text-xs text-zinc-600 mb-1">基础偏移 (m)</label>
              <input
                type="number"
                step="0.01"
                value={localValues.baseOffset}
                onChange={(e) => setLocalValues({ ...localValues, baseOffset: e.target.value })}
                className="w-full px-3 py-1.5 text-sm border border-zinc-300 rounded focus:outline-none focus:ring-2 focus:ring-zinc-900 focus:border-transparent"
                placeholder="0.0"
              />
            </div>

            <div>
              <label className="block text-xs text-zinc-600 mb-1">材质</label>
              <input
                type="text"
                value={localValues.material}
                onChange={(e) => setLocalValues({ ...localValues, material: e.target.value })}
                className="w-full px-3 py-1.5 text-sm border border-zinc-300 rounded focus:outline-none focus:ring-2 focus:ring-zinc-900 focus:border-transparent"
                placeholder="concrete"
              />
            </div>
          </div>
        )}

        {/* Trace Mode 特定信息 */}
        {mode === 'trace' && elementDetail && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-zinc-900">拓扑信息</h4>
            {elementDetail.connected_elements && elementDetail.connected_elements.length > 0 && (
              <div className="text-xs text-zinc-600">
                连接的构件: {elementDetail.connected_elements.length} 个
              </div>
            )}
          </div>
        )}
      </div>

      {/* 操作按钮 */}
      <div className="p-4 border-t border-zinc-200 space-y-2">
        <button
          onClick={handleSave}
          disabled={updateMutation.isPending || isLifting}
          className="w-full px-4 py-2 text-sm font-medium text-white bg-zinc-900 hover:bg-zinc-800 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {updateMutation.isPending || isLifting ? '保存中...' : '保存'}
        </button>
        <button
          onClick={handleCancel}
          className="w-full px-4 py-2 text-sm font-medium text-zinc-700 bg-zinc-100 hover:bg-zinc-200 rounded transition-colors"
        >
          取消
        </button>
      </div>
    </div>
  );
}

