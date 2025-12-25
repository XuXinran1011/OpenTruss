/**
 * 检验批管理面板
 * 
 * 用于查看和管理检验批
 */

'use client';

import { useState } from 'react';
import { useItemDetailForLots, useLotElements, useUpdateLotStatus, useRemoveElementsFromLot, useAssignElementsToLot } from '@/hooks/useLotStrategy';
import { InspectionLotStatus } from '@/types';
import { cn } from '@/lib/utils';
import { useHierarchyStore } from '@/stores/hierarchy';
import { ElementSelector } from './ElementSelector';

interface LotManagementPanelProps {
  itemId: string | null;
}

const STATUS_LABELS: Record<InspectionLotStatus, string> = {
  PLANNING: '规划中',
  IN_PROGRESS: '清洗中',
  SUBMITTED: '待审批',
  APPROVED: '已验收',
  PUBLISHED: '已发布',
};

const STATUS_COLORS: Record<InspectionLotStatus, string> = {
  PLANNING: 'bg-zinc-400',
  IN_PROGRESS: 'bg-blue-500',
  SUBMITTED: 'bg-yellow-500',
  APPROVED: 'bg-green-500',
  PUBLISHED: 'bg-emerald-600',
};

const STATUS_TRANSITIONS: Record<InspectionLotStatus, InspectionLotStatus[]> = {
  PLANNING: ['IN_PROGRESS'],
  IN_PROGRESS: ['SUBMITTED'],
  SUBMITTED: ['APPROVED'],
  APPROVED: ['PUBLISHED'],
  PUBLISHED: [],
};

export function LotManagementPanel({ itemId }: LotManagementPanelProps) {
  const [selectedLotId, setSelectedLotId] = useState<string | null>(null);
  const [showElementSelector, setShowElementSelector] = useState(false);
  const [selectedElementIds, setSelectedElementIds] = useState<string[]>([]);

  const { data: itemDetail, isLoading: isLoadingItem } = useItemDetailForLots(itemId);
  const { data: lotElements, isLoading: isLoadingElements } = useLotElements(selectedLotId || '');
  const updateStatusMutation = useUpdateLotStatus(selectedLotId || '');
  const removeElementsMutation = useRemoveElementsFromLot(selectedLotId || '');
  const assignElementsMutation = useAssignElementsToLot(selectedLotId || '');

  // 从层级数据中获取检验批列表
  const { hierarchyData } = useHierarchyStore();
  const lots: Array<{ id: string; name: string; status: InspectionLotStatus; element_count: number }> = [];
  
  // 从层级树中查找当前Item节点的检验批子节点
  const findItemNode = (node: any): any => {
    if (node.id === itemId && node.label === 'Item') {
      return node;
    }
    for (const child of node.children || []) {
      const found = findItemNode(child);
      if (found) return found;
    }
    return null;
  };
  
  const itemNode = hierarchyData ? findItemNode(hierarchyData) : null;
  if (itemNode && itemNode.children) {
    itemNode.children.forEach((child: any) => {
      if (child.label === 'InspectionLot') {
        lots.push({
          id: child.id,
          name: child.name,
          status: (child.metadata?.status || 'PLANNING') as InspectionLotStatus,
          element_count: child.metadata?.element_count || 0,
        });
      }
    });
  }

  const handleStatusUpdate = async (newStatus: InspectionLotStatus) => {
    if (!selectedLotId) return;

    try {
      await updateStatusMutation.mutateAsync({ status: newStatus });
    } catch (error) {
      console.error('Failed to update lot status:', error);
    }
  };

  const handleRemoveElement = async (elementId: string) => {
    if (!selectedLotId) return;

    try {
      await removeElementsMutation.mutateAsync({ element_ids: [elementId] });
    } catch (error) {
      console.error('Failed to remove element:', error);
    }
  };

  const handleAddElements = async () => {
    if (!selectedLotId || selectedElementIds.length === 0) return;

    try {
      await assignElementsMutation.mutateAsync({ element_ids: selectedElementIds });
      setShowElementSelector(false);
      setSelectedElementIds([]);
    } catch (error) {
      console.error('Failed to add elements:', error);
    }
  };

  const handleCancelElementSelection = () => {
    setShowElementSelector(false);
    setSelectedElementIds([]);
  };

  if (!itemId) {
    return (
      <div className="p-4 text-sm text-zinc-500 text-center">
        请先选择一个分项（Item）
      </div>
    );
  }

  if (isLoadingItem) {
    return (
      <div className="p-4 text-sm text-zinc-500 text-center">
        加载中...
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col relative">
      {/* 标题 */}
      <div className="p-4 border-b border-zinc-200">
        <h3 className="text-sm font-semibold text-zinc-900">检验批管理</h3>
        {itemDetail && (
          <p className="text-xs text-zinc-500 mt-1">
            分项: {itemDetail.name || itemId}
          </p>
        )}
      </div>

      {/* 检验批列表 */}
      <div className="flex-1 overflow-auto">
        {lots.length === 0 ? (
          <div className="p-4 text-sm text-zinc-500 text-center">
            暂无检验批
          </div>
        ) : (
          <div className="p-2 space-y-2">
            {lots.map((lot) => (
              <div
                key={lot.id}
                onClick={() => setSelectedLotId(lot.id)}
                className={cn(
                  'p-3 border rounded cursor-pointer transition-colors',
                  selectedLotId === lot.id
                    ? 'border-zinc-900 bg-zinc-50'
                    : 'border-zinc-200 hover:border-zinc-300'
                )}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="text-sm font-medium text-zinc-900">
                      {lot.name}
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      <span
                        className={cn(
                          'w-2 h-2 rounded-full',
                          STATUS_COLORS[lot.status]
                        )}
                        title={STATUS_LABELS[lot.status]}
                      />
                      <span className="text-xs text-zinc-500">
                        {STATUS_LABELS[lot.status]}
                      </span>
                      <span className="text-xs text-zinc-500">
                        · {lot.element_count} 个构件
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 构件选择器模态框 */}
      {showElementSelector && selectedLotId && (
        <div className="absolute inset-0 bg-white z-10 flex flex-col">
          <ElementSelector
            itemId={itemId}
            excludeLotId={selectedLotId}
            selectedElementIds={selectedElementIds}
            onSelectionChange={setSelectedElementIds}
            onConfirm={handleAddElements}
            onCancel={handleCancelElementSelection}
          />
        </div>
      )}

      {/* 检验批详情 */}
      {selectedLotId && !showElementSelector && (
        <div className="border-t border-zinc-200">
          <div className="p-4 space-y-4 max-h-64 overflow-auto">
            {/* 状态更新 */}
            <div>
              <label className="block text-sm font-medium text-zinc-700 mb-2">
                状态
              </label>
              <div className="flex flex-wrap gap-2">
                {STATUS_TRANSITIONS[lots.find(l => l.id === selectedLotId)?.status || 'PLANNING'].map((status) => (
                  <button
                    key={status}
                    onClick={() => handleStatusUpdate(status)}
                    disabled={updateStatusMutation.isPending}
                    className={cn(
                      'px-3 py-1.5 text-xs font-medium rounded transition-colors',
                      'bg-zinc-100 text-zinc-700 hover:bg-zinc-200',
                      'disabled:bg-zinc-300 disabled:cursor-not-allowed'
                    )}
                  >
                    {STATUS_LABELS[status]}
                  </button>
                ))}
              </div>
            </div>

            {/* 构件列表 */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium text-zinc-700">
                  构件列表 ({lotElements?.total || 0})
                </label>
                <button
                  onClick={() => setShowElementSelector(true)}
                  disabled={assignElementsMutation.isPending}
                  className="px-2 py-1 text-xs font-medium text-zinc-900 bg-zinc-100 hover:bg-zinc-200 rounded transition-colors disabled:bg-zinc-300 disabled:cursor-not-allowed"
                >
                  + 添加构件
                </button>
              </div>
              {isLoadingElements ? (
                <div className="text-xs text-zinc-500">加载中...</div>
              ) : (
                <div className="space-y-1 max-h-32 overflow-auto">
                  {lotElements?.items.map((element) => (
                    <div
                      key={element.id}
                      className="flex items-center justify-between p-2 text-xs bg-zinc-50 rounded"
                    >
                      <div>
                        <div className="font-medium text-zinc-900">
                          {element.id}
                        </div>
                        <div className="text-zinc-500">
                          {element.speckle_type}
                        </div>
                      </div>
                      <button
                        onClick={() => handleRemoveElement(element.id)}
                        disabled={removeElementsMutation.isPending}
                        className="px-2 py-1 text-xs text-red-600 hover:text-red-700 hover:bg-red-50 rounded transition-colors"
                      >
                        移除
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

