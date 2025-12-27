/** 3D 预览面板组件
 * 
 * 可折叠的 3D 预览窗口，集成到 Workbench 布局中
 */

'use client';

import { useQuery } from '@tanstack/react-query';
import { Preview3D } from './Preview3D';
import { useWorkbenchStore } from '@/stores/workbench';
import { batchGetElementDetails } from '@/services/elements';
import { ElementDetail } from '@/services/elements';

interface Preview3DPanelProps {
  collapsed?: boolean;
  onToggle?: () => void;
}

export function Preview3DPanel({ collapsed = false, onToggle }: Preview3DPanelProps) {
  const { selectedElementIds, setSelectedElementIds } = useWorkbenchStore();
  
  // 获取所有可见元素的详情（用于 3D 预览）
  // 这里简化处理，只获取选中的元素；实际应该获取画布中所有可见元素
  const { data: elementDetails, isLoading } = useQuery({
    queryKey: ['elements', 'details', 'preview3d', selectedElementIds.join(',')],
    queryFn: async () => {
      if (selectedElementIds.length === 0) return [];
      
      // 批量获取元素详情
      const BATCH_SIZE = 100;
      const details: ElementDetail[] = [];
      
      for (let i = 0; i < selectedElementIds.length; i += BATCH_SIZE) {
        const batch = selectedElementIds.slice(i, i + BATCH_SIZE);
        const batchDetails = await batchGetElementDetails(batch);
        details.push(...batchDetails.items);
      }
      
      return details;
    },
    enabled: selectedElementIds.length > 0 && !collapsed,
    staleTime: 5000, // 5秒缓存
  });
  
  const elements = elementDetails || [];
  
  if (collapsed) {
    return (
      <div className="h-full w-12 bg-zinc-50 border-l border-zinc-200 flex flex-col items-center justify-center">
        <button
          onClick={onToggle}
          className="text-zinc-500 hover:text-zinc-700 p-2"
          aria-label="展开 3D 预览"
          title="展开 3D 预览"
        >
          <svg
            className="w-6 h-6 transform rotate-90"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 19l-7-7 7-7"
            />
          </svg>
        </button>
      </div>
    );
  }
  
  return (
    <div className="h-full w-96 bg-white border-l border-zinc-200 flex flex-col">
      {/* 头部 */}
      <div className="flex items-center justify-between p-3 border-b border-zinc-200 bg-zinc-50">
        <h3 className="text-sm font-semibold text-zinc-900">3D 预览</h3>
        <div className="flex items-center gap-2">
          <span className="text-xs text-zinc-500">
            {elements.length} 个构件
          </span>
          {onToggle && (
            <button
              onClick={onToggle}
              className="text-zinc-400 hover:text-zinc-600 text-lg leading-none"
              aria-label="折叠 3D 预览"
            >
              ×
            </button>
          )}
        </div>
      </div>
      
      {/* 3D 预览内容 */}
      <div className="flex-1 relative">
        {isLoading ? (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-sm text-zinc-500">加载中...</div>
          </div>
        ) : elements.length === 0 ? (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-sm text-zinc-500 text-center px-4">
              请在画布中选择构件以查看 3D 预览
            </div>
          </div>
        ) : (
          <Preview3D
            elements={elements}
            selectedElementIds={selectedElementIds}
            onElementClick={(elementId) => {
              // 3D 场景选择 → 2D 画布聚焦
              setSelectedElementIds([elementId]);
            }}
            height={undefined} // 使用父容器高度
            width={undefined} // 使用父容器宽度
          />
        )}
      </div>
    </div>
  );
}
