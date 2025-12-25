/** 层级树节点组件 */

'use client';

import { useState, useEffect } from 'react';
import { HierarchyNode } from '@/services/hierarchy';
import { InspectionLotStatus } from '@/types';
import { useHierarchyStore } from '@/stores/hierarchy';
import { useClassifyMode } from '@/hooks/useClassifyMode';
import { useToastContext } from '@/providers/ToastProvider';
import { useDrag } from '@/contexts/DragContext';
import { cn } from '@/lib/utils';
// 使用内联 SVG 图标替代 @heroicons/react

interface HierarchyTreeNodeProps {
  node: HierarchyNode;
  level?: number;
  onSelect?: (nodeId: string) => void;
}

const STATUS_COLORS: Record<InspectionLotStatus, string> = {
  PLANNING: 'bg-zinc-400',
  IN_PROGRESS: 'bg-blue-500',
  SUBMITTED: 'bg-yellow-500',
  APPROVED: 'bg-green-500',
  PUBLISHED: 'bg-emerald-600',
};

function HierarchyTreeNodeComponent({ node, level = 0, onSelect }: HierarchyTreeNodeProps) {
  const { expandedNodeIds, toggleNode, selectedNodeId } = useHierarchyStore();
  const { classify, isClassifying, error, successCount, failedCount, clearError } = useClassifyMode();
  const { showToast } = useToastContext();
  const { draggedElementIds, setDraggedElementIds } = useDrag();
  const [isDragOver, setIsDragOver] = useState(false);

  // 显示错误和成功提示
  useEffect(() => {
    if (error) {
      showToast(error.message, 'error');
      clearError();
    }
  }, [error, showToast, clearError]);

  useEffect(() => {
    if (successCount > 0 && !isClassifying) {
      if (failedCount > 0) {
        showToast(`成功归类 ${successCount} 个构件，${failedCount} 个失败`, 'warning');
      } else {
        showToast(`成功归类 ${successCount} 个构件`, 'success');
      }
    }
  }, [successCount, failedCount, isClassifying, showToast]);
  
  const isExpanded = expandedNodeIds.has(node.id);
  const isSelected = selectedNodeId === node.id;
  const hasChildren = node.children.length > 0;
  
  // 只有 Item 节点可以作为归类目标
  const isDropTarget = node.label === 'Item';

  // 获取状态指示（如果是检验批）
  const status = node.label === 'InspectionLot' ? node.metadata?.status : null;
  const elementCount = node.metadata?.element_count || 0;
  const inspectionLotCount = node.metadata?.inspection_lot_count || 0;

  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (hasChildren) {
      toggleNode(node.id);
    }
  };

  const handleClick = () => {
    if (onSelect) {
      onSelect(node.id);
    }
  };

  // 拖拽处理
  const handleDragOver = (e: React.DragEvent) => {
    if (!isDropTarget) return;
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    if (!isDropTarget) return;
    e.preventDefault();
    e.stopPropagation();
    // 检查鼠标是否真的离开了元素
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX;
    const y = e.clientY;
    if (x < rect.left || x > rect.right || y < rect.top || y > rect.bottom) {
      setIsDragOver(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    if (!isDropTarget) return;
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    try {
      // 优先从 dataTransfer 获取（HTML5 drag）
      let elementIds: string[] | null = null;
      const elementIdsStr = e.dataTransfer.getData('application/element-ids');
      if (elementIdsStr) {
        elementIds = JSON.parse(elementIdsStr) as string[];
      } else if (draggedElementIds) {
        // 从Context获取（SVG 拖拽）
        elementIds = draggedElementIds;
        setDraggedElementIds(null);
      }

      if (elementIds && elementIds.length > 0) {
        // 调用归类功能（批量归类）
        classify(node.id, elementIds);
      } else {
        showToast('没有可归类的构件', 'warning');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '归类操作失败';
      showToast(errorMessage, 'error');
      console.error('Failed to classify elements:', error);
    }
  };

  return (
    <div>
      <div
        onClick={handleClick}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={cn(
          'flex items-center gap-1.5 px-2 py-1.5 text-sm cursor-pointer hover:bg-zinc-100 transition-all duration-200',
          isSelected && 'bg-zinc-200',
          isDragOver && isDropTarget && 'bg-orange-100 border-2 border-orange-600 border-dashed scale-105 shadow-lg',
          !isDropTarget && 'cursor-default'
        )}
        style={{ paddingLeft: `${level * 16 + 8}px` }}
      >
        {/* 展开/折叠图标 */}
        {hasChildren ? (
          <button
            onClick={handleToggle}
            className="w-4 h-4 flex items-center justify-center text-zinc-500 hover:text-zinc-700"
          >
            {isExpanded ? (
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            ) : (
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            )}
          </button>
        ) : (
          <div className="w-4" />
        )}

        {/* 节点标签图标 */}
        <span className="text-xs text-zinc-400 w-4 text-center">{node.label[0]}</span>

        {/* 节点名称 */}
        <span className="flex-1 truncate">{node.name}</span>

        {/* 状态指示和数量 */}
        <div className="flex items-center gap-1.5">
          {status && (
            <span
              className={cn('w-2 h-2 rounded-full', STATUS_COLORS[status as InspectionLotStatus])}
              title={status}
            />
          )}
          {(elementCount > 0 || inspectionLotCount > 0) && (
            <span className="text-xs text-zinc-500">
              {elementCount > 0 ? elementCount : inspectionLotCount}
            </span>
          )}
        </div>
      </div>

      {/* 子节点 */}
      {hasChildren && isExpanded && (
        <div>
          {node.children.map((child) => (
            <HierarchyTreeNode
              key={child.id}
              node={child}
              level={level + 1}
              onSelect={onSelect}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export { HierarchyTreeNodeComponent as HierarchyTreeNode };

