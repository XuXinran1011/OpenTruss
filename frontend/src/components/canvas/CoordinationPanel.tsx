/** 管线综合排布面板 */

'use client';

import { useState } from 'react';
import { useCoordination } from '@/hooks/useCoordination';
import { useToastContext } from '@/providers/ToastProvider';

interface CoordinationPanelProps {
  levelId: string;
  elementIds?: string[];
  onCoordinationComplete?: (result: any) => void;
  onClose?: () => void;
}

/** 获取调整类型的标签 */
function getAdjustmentTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    horizontal_translation: '水平平移',
    vertical_translation: '竖向平移',
    add_bend: '添加弯头',
  };
  return labels[type] || type;
}

export function CoordinationPanel({
  levelId,
  elementIds,
  onCoordinationComplete,
  onClose,
}: CoordinationPanelProps) {
  const { coordinationState, coordinate, clearResult } = useCoordination();
  const { showToast } = useToastContext();
  
  const [priorities, setPriorities] = useState<Record<string, number>>({});
  const [avoidCollisions, setAvoidCollisions] = useState(true);
  const [minimizeBends, setMinimizeBends] = useState(true);
  const [closeToCeiling, setCloseToCeiling] = useState(true);

  const handleCoordinate = async () => {
    try {
      const constraints = {
        priorities: Object.keys(priorities).length > 0 ? priorities : undefined,
        avoid_collisions: avoidCollisions,
        minimize_bends: minimizeBends,
        close_to_ceiling: closeToCeiling,
      };

      const result = await coordinate(levelId, elementIds, constraints);

      if (onCoordinationComplete) {
        onCoordinationComplete(result);
      }
    } catch (error) {
      // Error handled in hook
    }
  };

  const handleClear = () => {
    clearResult();
    setPriorities({});
  };

  return (
    <div className="bg-white border border-zinc-200 rounded-lg shadow-lg p-4 min-w-[400px] max-w-[500px]">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-zinc-900">管线综合排布</h3>
        {onClose && (
          <button
            onClick={onClose}
            className="text-zinc-400 hover:text-zinc-600"
            aria-label="关闭"
          >
            ×
          </button>
        )}
      </div>

      <div className="space-y-4">
        {/* 约束选项 */}
        <div className="space-y-3">
          <div className="flex items-center">
            <input
              type="checkbox"
              id="avoid-collisions"
              checked={avoidCollisions}
              onChange={(e) => setAvoidCollisions(e.target.checked)}
              className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-zinc-300 rounded"
            />
            <label htmlFor="avoid-collisions" className="text-sm font-medium text-zinc-700">
              避开碰撞
            </label>
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="minimize-bends"
              checked={minimizeBends}
              onChange={(e) => setMinimizeBends(e.target.checked)}
              className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-zinc-300 rounded"
            />
            <label htmlFor="minimize-bends" className="text-sm font-medium text-zinc-700">
              最小化翻弯
            </label>
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="close-to-ceiling"
              checked={closeToCeiling}
              onChange={(e) => setCloseToCeiling(e.target.checked)}
              className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-zinc-300 rounded"
            />
            <label htmlFor="close-to-ceiling" className="text-sm font-medium text-zinc-700">
              贴近顶板
            </label>
          </div>
        </div>

        {/* 结果展示 */}
        {coordinationState.result && (
          <div className="space-y-3">
            <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
              <div className="text-sm font-medium text-blue-800 mb-2">
                排布结果摘要
              </div>
              <div className="text-sm text-blue-700 space-y-1">
                <div className="flex justify-between">
                  <span>解决的碰撞数:</span>
                  <span className="font-semibold">{coordinationState.result.collisions_resolved}</span>
                </div>
                <div className="flex justify-between">
                  <span>调整的元素数:</span>
                  <span className="font-semibold">{coordinationState.result.adjusted_elements.length}</span>
                </div>
              </div>
            </div>

            {/* 调整的元素详情（可折叠） */}
            {coordinationState.result.adjusted_elements.length > 0 && (
              <div className="border border-zinc-200 rounded-md overflow-hidden">
                <details className="group">
                  <summary className="px-3 py-2 bg-zinc-50 hover:bg-zinc-100 cursor-pointer text-sm font-medium text-zinc-700 list-none">
                    <div className="flex items-center justify-between">
                      <span>调整的元素详情 ({coordinationState.result.adjusted_elements.length})</span>
                      <span className="text-zinc-400 group-open:rotate-90 transition-transform">▶</span>
                    </div>
                  </summary>
                  <div className="px-3 py-2 bg-white max-h-64 overflow-y-auto space-y-2">
                    {coordinationState.result.adjusted_elements.map((element, index) => (
                      <div key={element.element_id || index} className="border-b border-zinc-100 pb-2 last:border-b-0 last:pb-0">
                        <div className="text-xs font-semibold text-zinc-900 mb-1">
                          元素 ID: {element.element_id}
                        </div>
                        <div className="text-xs text-zinc-600 space-y-0.5">
                          <div className="flex items-center gap-2">
                            <span className="inline-block w-2 h-2 rounded-full bg-blue-500"></span>
                            <span>调整类型: <span className="font-medium">{getAdjustmentTypeLabel(element.adjustment_type)}</span></span>
                          </div>
                          <div className="text-zinc-500 pl-4">
                            {element.adjustment_reason}
                          </div>
                          <div className="text-zinc-400 pl-4 text-xs">
                            原始路径点数: {element.original_path?.length || 0} → 
                            调整后: {element.adjusted_path?.length || 0}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </details>
              </div>
            )}

            {/* 警告信息 */}
            {coordinationState.result.warnings.length > 0 && (
              <div className="bg-amber-50 border border-amber-200 rounded-md p-3">
                <div className="text-sm font-medium text-amber-800 mb-1">
                  警告
                </div>
                <ul className="text-sm text-amber-700 list-disc list-inside space-y-1">
                  {coordinationState.result.warnings.map((warning, index) => (
                    <li key={index}>{warning}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* 错误信息 */}
            {coordinationState.result.errors.length > 0 && (
              <div className="bg-red-50 border border-red-200 rounded-md p-3">
                <div className="text-sm font-medium text-red-800 mb-1">
                  错误
                </div>
                <ul className="text-sm text-red-700 list-disc list-inside space-y-1">
                  {coordinationState.result.errors.map((error, index) => (
                    <li key={index}>{error}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* 错误展示 */}
        {coordinationState.error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-3">
            <div className="text-sm font-medium text-red-800">
              错误: {coordinationState.error}
            </div>
          </div>
        )}

        {/* 操作按钮 */}
        <div className="flex space-x-2 pt-2 border-t border-zinc-200">
          <button
            onClick={handleCoordinate}
            disabled={coordinationState.isLoading}
            className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:bg-zinc-400 disabled:cursor-not-allowed"
          >
            {coordinationState.isLoading ? '排布中...' : '开始综合排布'}
          </button>
          {coordinationState.result && (
            <button
              onClick={handleClear}
              className="px-4 py-2 border border-zinc-300 text-zinc-700 rounded-md hover:bg-zinc-50"
            >
              清除
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

