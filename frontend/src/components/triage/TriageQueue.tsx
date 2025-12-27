/** 分诊队列组件 */

'use client';

import { useQuery } from '@tanstack/react-query';
import { getElements, ElementListItem } from '@/services/elements';
import { IssueType } from '@/types';
import { useWorkbenchStore } from '@/stores/workbench';
import { useCanvas } from '@/contexts/CanvasContext';
import { cn } from '@/lib/utils';
import { useMemo } from 'react';

interface IssueGroup {
  type: IssueType;
  label: string;
  color: string;
  elements: ElementListItem[];
}

function TriageQueueComponent() {
  const { setSelectedElementIds, addSelectedElementId } = useWorkbenchStore();
  const { canvasRef } = useCanvas();

  // 获取所有构件（用于识别问题）
  const { data: elementsData } = useQuery({
    queryKey: ['elements', 'all'],
    queryFn: () => getElements({ page: 1, page_size: 1000 }), // 获取足够多的数据
  });

  // 单独获取低置信度构件（使用置信度筛选）
  const { data: lowConfidenceData } = useQuery({
    queryKey: ['elements', 'low-confidence'],
    queryFn: () => getElements({ page: 1, page_size: 1000, max_confidence: 0.7 }), // 置信度 < 0.7
  });

  // 分类问题构件（按严重性排序：拓扑错误 > 缺失高度 > 低置信度）
  const issueGroups: IssueGroup[] = [
    {
      type: 'topology_error' as IssueType,
      label: '拓扑错误',
      color: 'bg-red-600',
      elements:
        elementsData?.items.filter((el) => el.status === 'Draft') || [], // 简化：Draft 状态视为可能有拓扑问题
    },
    {
      type: 'z_missing' as IssueType,
      label: '缺失高度',
      color: 'bg-violet-600',
      elements: elementsData?.items.filter((el) => !el.has_height) || [],
    },
    {
      type: 'low_confidence' as IssueType,
      label: '低置信度',
      color: 'bg-amber-600',
      elements: lowConfidenceData?.items || [],
    },
  ]
    .filter((group) => group.elements.length > 0)
    .sort((a, b) => {
      // 按严重性排序：topology_error > z_missing > low_confidence
      const severityOrder: Record<IssueType, number> = {
        topology_error: 0,
        z_missing: 1,
        low_confidence: 2,
      };
      return severityOrder[a.type] - severityOrder[b.type];
    });

  const totalIssues = issueGroups.reduce((sum, group) => sum + group.elements.length, 0);
  
  // 统计信息
  const issueStats = useMemo(() => {
    const stats = {
      topology_error: 0,
      z_missing: 0,
      low_confidence: 0,
    };
    issueGroups.forEach((group) => {
      stats[group.type] = group.elements.length;
    });
    return stats;
  }, [issueGroups]);

  const handleIssueClick = (elementId: string) => {
    addSelectedElementId(elementId);
    // 定位到画布中的构件
    if (canvasRef?.current) {
      canvasRef.current.focusOnElement(elementId);
    }
  };

  const handleGroupDoubleClick = (elements: ElementListItem[]) => {
    const elementIds = elements.map((el) => el.id);
    setSelectedElementIds(elementIds);
    // 定位到所有选中的构件
    if (canvasRef?.current && elementIds.length > 0) {
      canvasRef.current.focusOnElements(elementIds);
    }
  };

  return (
    <div className="h-full flex flex-col border-b border-zinc-200">
      <div className="p-2 border-b border-zinc-200 bg-zinc-100">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium text-zinc-900">分诊队列</h3>
          <span className="text-xs font-semibold text-zinc-700">{totalIssues}</span>
        </div>
        {totalIssues > 0 && (
          <div className="mt-1 flex items-center gap-2 text-xs text-zinc-600">
            {issueStats.topology_error > 0 && (
              <span className="flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-red-600" />
                <span>{issueStats.topology_error}</span>
              </span>
            )}
            {issueStats.z_missing > 0 && (
              <span className="flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-violet-600" />
                <span>{issueStats.z_missing}</span>
              </span>
            )}
            {issueStats.low_confidence > 0 && (
              <span className="flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-600" />
                <span>{issueStats.low_confidence}</span>
              </span>
            )}
          </div>
        )}
      </div>

      <div className="flex-1 overflow-auto">
        {issueGroups.length === 0 ? (
          <div className="p-4 text-sm text-zinc-500 text-center">暂无问题构件</div>
        ) : (
          issueGroups.map((group) => (
            <div key={group.type} className="border-b border-zinc-200">
              <div
                className="flex items-center justify-between p-2 bg-zinc-50 cursor-pointer hover:bg-zinc-100"
                onDoubleClick={() => handleGroupDoubleClick(group.elements)}
              >
                <div className="flex items-center gap-2">
                  <span className={cn('w-2 h-2 rounded-full', group.color)} />
                  <span className="text-sm font-medium text-zinc-900">{group.label}</span>
                </div>
                <span className="text-xs text-zinc-500">{group.elements.length}</span>
              </div>

              <div className="max-h-40 overflow-auto">
                {group.elements.map((element) => (
                  <div
                    key={element.id}
                    onClick={() => handleIssueClick(element.id)}
                    className="px-4 py-1.5 text-xs text-zinc-700 hover:bg-zinc-100 cursor-pointer font-mono"
                  >
                    • {element.id}
                  </div>
                ))}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export { TriageQueueComponent as TriageQueue };

