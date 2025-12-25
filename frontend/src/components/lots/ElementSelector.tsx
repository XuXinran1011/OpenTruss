/**
 * 构件选择器组件
 * 
 * 用于选择构件并添加到检验批
 */

'use client';

import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getElements, ElementListItem } from '@/services/elements';
import { cn } from '@/lib/utils';

interface ElementSelectorProps {
  itemId: string | null;
  excludeLotId?: string | null; // 排除已经在某个检验批中的构件（用于在当前检验批中选择未分配的构件）
  selectedElementIds: string[];
  onSelectionChange: (elementIds: string[]) => void;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ElementSelector({
  itemId,
  excludeLotId,
  selectedElementIds,
  onSelectionChange,
  onConfirm,
  onCancel,
}: ElementSelectorProps) {
  const [searchKeyword, setSearchKeyword] = useState('');

  // 获取该分项下的所有构件
  const { data: elementsData, isLoading } = useQuery({
    queryKey: ['elements', 'for-selector', itemId],
    queryFn: () => getElements({ item_id: itemId || undefined, page: 1, page_size: 1000 }),
    enabled: !!itemId,
  });

  // 过滤出未分配的构件（inspection_lot_id为空或null，或不属于excludeLotId）
  const availableElements = useMemo(() => {
    if (!elementsData?.items) return [];

    return elementsData.items.filter((element) => {
      // 如果指定了excludeLotId，排除属于该检验批的构件（允许选择未分配的构件）
      // 如果没有指定excludeLotId，则显示所有未分配的构件
      const isUnassigned = !element.inspection_lot_id || element.inspection_lot_id === '';
      const notInExcludedLot = !excludeLotId || element.inspection_lot_id !== excludeLotId;

      return isUnassigned && notInExcludedLot;
    });
  }, [elementsData, excludeLotId]);

  // 根据搜索关键词过滤
  const filteredElements = useMemo(() => {
    if (!searchKeyword.trim()) return availableElements;

    const keyword = searchKeyword.toLowerCase();
    return availableElements.filter((element) => {
      return (
        element.id.toLowerCase().includes(keyword) ||
        element.speckle_type.toLowerCase().includes(keyword) ||
        element.level_id?.toLowerCase().includes(keyword)
      );
    });
  }, [availableElements, searchKeyword]);

  const handleToggleElement = (elementId: string) => {
    const newSelection = selectedElementIds.includes(elementId)
      ? selectedElementIds.filter((id) => id !== elementId)
      : [...selectedElementIds, elementId];
    onSelectionChange(newSelection);
  };

  const handleSelectAll = () => {
    if (selectedElementIds.length === filteredElements.length) {
      onSelectionChange([]);
    } else {
      onSelectionChange(filteredElements.map((el) => el.id));
    }
  };

  if (isLoading) {
    return (
      <div className="p-4 text-sm text-zinc-500 text-center">
        加载中...
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* 标题和搜索 */}
      <div className="p-4 border-b border-zinc-200">
        <h3 className="text-sm font-semibold text-zinc-900 mb-3">选择构件</h3>
        <input
          type="text"
          placeholder="搜索构件ID、类型或楼层..."
          value={searchKeyword}
          onChange={(e) => setSearchKeyword(e.target.value)}
          className="w-full px-3 py-1.5 text-sm border border-zinc-300 rounded focus:outline-none focus:ring-2 focus:ring-zinc-900 focus:border-transparent"
        />
        <div className="mt-2 text-xs text-zinc-500">
          共 {filteredElements.length} 个可用构件，已选择 {selectedElementIds.length} 个
        </div>
      </div>

      {/* 构件列表 */}
      <div className="flex-1 overflow-auto p-2">
        {filteredElements.length === 0 ? (
          <div className="p-4 text-sm text-zinc-500 text-center">
            {searchKeyword ? '未找到匹配的构件' : '没有可用的构件'}
          </div>
        ) : (
          <>
            {/* 全选按钮 */}
            <div className="mb-2">
              <button
                onClick={handleSelectAll}
                className="text-xs text-zinc-600 hover:text-zinc-900 underline"
              >
                {selectedElementIds.length === filteredElements.length ? '取消全选' : '全选'}
              </button>
            </div>

            {/* 构件列表 */}
            <div className="space-y-1">
              {filteredElements.map((element) => {
                const isSelected = selectedElementIds.includes(element.id);
                return (
                  <div
                    key={element.id}
                    onClick={() => handleToggleElement(element.id)}
                    className={cn(
                      'p-2 border rounded cursor-pointer transition-colors',
                      isSelected
                        ? 'border-zinc-900 bg-zinc-50'
                        : 'border-zinc-200 hover:border-zinc-300'
                    )}
                  >
                    <div className="flex items-start">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => handleToggleElement(element.id)}
                        onClick={(e) => e.stopPropagation()}
                        className="mt-0.5 mr-2"
                      />
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-zinc-900 truncate">
                          {element.id}
                        </div>
                        <div className="text-xs text-zinc-500 mt-0.5">
                          {element.speckle_type}
                          {element.level_id && ` · ${element.level_id}`}
                        </div>
                        {element.zone_id && (
                          <div className="text-xs text-zinc-400 mt-0.5">
                            区域: {element.zone_id}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </>
        )}
      </div>

      {/* 底部操作按钮 */}
      <div className="p-4 border-t border-zinc-200 flex gap-2">
        <button
          onClick={onCancel}
          className="flex-1 px-4 py-2 text-sm font-medium text-zinc-700 bg-zinc-100 rounded hover:bg-zinc-200 transition-colors"
        >
          取消
        </button>
        <button
          onClick={onConfirm}
          disabled={selectedElementIds.length === 0}
          className={cn(
            'flex-1 px-4 py-2 text-sm font-medium rounded transition-colors',
            'bg-zinc-900 text-white hover:bg-zinc-800',
            'disabled:bg-zinc-400 disabled:cursor-not-allowed'
          )}
        >
          确认 ({selectedElementIds.length})
        </button>
      </div>
    </div>
  );
}

