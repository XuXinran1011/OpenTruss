/**
 * 拓扑校验结果展示面板
 * 
 * 用于显示拓扑校验结果（悬空端点、孤立元素等）
 */

'use client';

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { cn } from '@/lib/utils';

interface TopologyValidationPanelProps {
  lotId: string | null;
  onHighlightElements?: (elementIds: string[]) => void;
}

interface TopologyValidationResult {
  valid: boolean;
  open_ends: string[];
  isolated_elements: string[];
  errors: string[];
}

async function validateTopology(lotId: string): Promise<TopologyValidationResult> {
  const response = await fetch(`/api/v1/validation/topology/validate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ lot_id: lotId }),
  });

  if (!response.ok) {
    throw new Error('Failed to validate topology');
  }

  const result = await response.json();
  return result.data;
}

export function TopologyValidationPanel({ lotId, onHighlightElements }: TopologyValidationPanelProps) {
  const [highlightedElements, setHighlightedElements] = useState<string[]>([]);

  const { data: validationResult, isLoading, error, refetch } = useQuery({
    queryKey: ['topology-validation', lotId],
    queryFn: () => validateTopology(lotId!),
    enabled: !!lotId,
    staleTime: 5000, // 5秒内使用缓存
  });

  useEffect(() => {
    if (validationResult && onHighlightElements) {
      const allHighlighted = [
        ...validationResult.open_ends,
        ...validationResult.isolated_elements,
      ];
      setHighlightedElements(allHighlighted);
      onHighlightElements(allHighlighted);
    } else {
      setHighlightedElements([]);
      onHighlightElements?.([]);
    }
  }, [validationResult, onHighlightElements]);

  if (!lotId) {
    return (
      <div className="p-4 text-sm text-zinc-500 text-center">
        请先选择一个检验批
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="p-4 text-sm text-zinc-500 text-center">
        校验中...
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-sm text-red-600 text-center">
        校验失败: {(error as Error).message}
      </div>
    );
  }

  if (!validationResult) {
    return null;
  }

  const { valid, open_ends, isolated_elements, errors } = validationResult;

  return (
    <div className="h-full flex flex-col">
      {/* 标题 */}
      <div className="p-4 border-b border-zinc-200">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-zinc-900">拓扑校验结果</h3>
          <button
            onClick={() => refetch()}
            className="text-xs text-zinc-600 hover:text-zinc-900"
          >
            刷新
          </button>
        </div>
      </div>

      {/* 内容区域 */}
      <div className="flex-1 overflow-auto p-4 space-y-4">
        {/* 总体状态 */}
        <div
          className={cn(
            'p-3 rounded border',
            valid
              ? 'bg-green-50 border-green-200 text-green-800'
              : 'bg-red-50 border-red-200 text-red-800'
          )}
        >
          <div className="font-medium">
            {valid ? '✓ 拓扑完整' : '✗ 拓扑不完整'}
          </div>
        </div>

        {/* 错误信息 */}
        {errors.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-zinc-700">错误信息</h4>
            <ul className="space-y-1">
              {errors.map((error, index) => (
                <li key={index} className="text-sm text-red-600">
                  {error}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* 悬空端点 */}
        {open_ends.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-zinc-700">
              悬空端点 ({open_ends.length})
            </h4>
            <div className="max-h-40 overflow-auto space-y-1">
              {open_ends.map((elementId) => (
                <div
                  key={elementId}
                  className="text-xs text-zinc-600 p-2 bg-zinc-50 rounded hover:bg-zinc-100 cursor-pointer"
                  onClick={() => onHighlightElements?.([elementId])}
                >
                  {elementId}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 孤立元素 */}
        {isolated_elements.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-zinc-700">
              孤立元素 ({isolated_elements.length})
            </h4>
            <div className="max-h-40 overflow-auto space-y-1">
              {isolated_elements.map((elementId) => (
                <div
                  key={elementId}
                  className="text-xs text-zinc-600 p-2 bg-zinc-50 rounded hover:bg-zinc-100 cursor-pointer"
                  onClick={() => onHighlightElements?.([elementId])}
                >
                  {elementId}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 无问题提示 */}
        {valid && open_ends.length === 0 && isolated_elements.length === 0 && (
          <div className="text-sm text-zinc-500 text-center py-4">
            未发现拓扑问题
          </div>
        )}
      </div>
    </div>
  );
}

