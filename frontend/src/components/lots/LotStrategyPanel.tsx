/**
 * 检验批策略配置面板
 * 
 * 用于配置和创建检验批
 */

'use client';

import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useCreateLotsByRule } from '@/hooks/useLotStrategy';
import { useItemDetailForLots } from '@/hooks/useLotStrategy';
import { getElements, ElementListItem } from '@/services/elements';
import { cn } from '@/lib/utils';

interface LotStrategyPanelProps {
  itemId: string | null;
  onCreated?: () => void;
}

const RULE_TYPES = [
  { value: 'BY_LEVEL', label: '按楼层划分', description: '根据构件的楼层（Level）自动分组创建检验批' },
  { value: 'BY_ZONE', label: '按区域划分', description: '根据构件的区域（Zone）自动分组创建检验批' },
  { value: 'BY_LEVEL_AND_ZONE', label: '按楼层+区域划分', description: '根据楼层和区域的组合自动分组创建检验批' },
] as const;

export function LotStrategyPanel({ itemId, onCreated }: LotStrategyPanelProps) {
  const [selectedRuleType, setSelectedRuleType] = useState<'BY_LEVEL' | 'BY_ZONE' | 'BY_LEVEL_AND_ZONE'>('BY_LEVEL');
  
  const { data: itemDetail, isLoading: isLoadingItem } = useItemDetailForLots(itemId);
  const createLotsMutation = useCreateLotsByRule();

  // 获取该分项下的所有构件（用于预览统计）
  const { data: elementsData } = useQuery({
    queryKey: ['elements', 'for-preview', itemId],
    queryFn: () => getElements({ item_id: itemId || undefined, page: 1, page_size: 1000 }),
    enabled: !!itemId,
  });

  // 计算预览信息：未分配的构件统计
  const previewInfo = useMemo(() => {
    if (!elementsData?.items) {
      return {
        unassignedCount: 0,
        estimatedLots: 0,
        groups: [] as Array<{ key: string; count: number; label: string }>,
      };
    }

    // 过滤出未分配的构件
    const unassignedElements = elementsData.items.filter(
      (el: ElementListItem) => !el.inspection_lot_id || el.inspection_lot_id === ''
    );

    if (unassignedElements.length === 0) {
      return {
        unassignedCount: 0,
        estimatedLots: 0,
        groups: [],
      };
    }

    // 根据规则类型分组
    const groupsMap = new Map<string, number>();
    
    unassignedElements.forEach((el: ElementListItem) => {
      let groupKey = '';
      let groupLabel = '';

      switch (selectedRuleType) {
        case 'BY_LEVEL':
          groupKey = el.level_id || '未知楼层';
          groupLabel = `楼层: ${groupKey}`;
          break;
        case 'BY_ZONE':
          // 注意：ElementListItem可能没有zone_id，这里我们只能基于已有的数据
          // 如果有zone_id字段，使用它；否则使用一个占位符
          groupKey = 'zone_unknown'; // 这里需要从详细数据获取zone_id，暂时用占位符
          groupLabel = '区域分组';
          break;
        case 'BY_LEVEL_AND_ZONE':
          const zoneKey = 'zone_unknown'; // 同上
          groupKey = `${el.level_id || '未知楼层'}_${zoneKey}`;
          groupLabel = `${el.level_id || '未知楼层'} - 区域分组`;
          break;
      }

      groupsMap.set(groupKey, (groupsMap.get(groupKey) || 0) + 1);
    });

    const groups = Array.from(groupsMap.entries()).map(([key, count]) => ({
      key,
      count,
      label: groupsMap.size === 1 ? '未分配构件' : key.replace('_', ' - '),
    }));

    return {
      unassignedCount: unassignedElements.length,
      estimatedLots: groups.length,
      groups,
    };
  }, [elementsData, selectedRuleType]);

  const handleCreate = async () => {
    if (!itemId) return;

    try {
      await createLotsMutation.mutateAsync({
        item_id: itemId,
        rule_type: selectedRuleType,
      });
      
      if (onCreated) {
        onCreated();
      }
    } catch (error) {
      console.error('Failed to create lots:', error);
    }
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
    <div className="h-full flex flex-col">
      {/* 标题 */}
      <div className="p-4 border-b border-zinc-200">
        <h3 className="text-sm font-semibold text-zinc-900">检验批策略配置</h3>
        {itemDetail && (
          <p className="text-xs text-zinc-500 mt-1">
            分项: {itemDetail.name || itemId}
          </p>
        )}
      </div>

      {/* 内容区域 */}
      <div className="flex-1 overflow-auto p-4 space-y-4">
        {/* 规则类型选择 */}
        <div>
          <label className="block text-sm font-medium text-zinc-700 mb-2">
            划分规则
          </label>
          <div className="space-y-2">
            {RULE_TYPES.map((rule) => (
              <label
                key={rule.value}
                className={cn(
                  'block p-3 border rounded cursor-pointer transition-colors',
                  selectedRuleType === rule.value
                    ? 'border-zinc-900 bg-zinc-50'
                    : 'border-zinc-300 hover:border-zinc-400'
                )}
              >
                <div className="flex items-start">
                  <input
                    type="radio"
                    name="rule_type"
                    value={rule.value}
                    checked={selectedRuleType === rule.value}
                    onChange={(e) => setSelectedRuleType(e.target.value as typeof selectedRuleType)}
                    className="mt-0.5 mr-2"
                  />
                  <div className="flex-1">
                    <div className="text-sm font-medium text-zinc-900">
                      {rule.label}
                    </div>
                    <div className="text-xs text-zinc-500 mt-0.5">
                      {rule.description}
                    </div>
                  </div>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* 预览信息 */}
        {previewInfo.unassignedCount > 0 && (
          <div>
            <label className="block text-sm font-medium text-zinc-700 mb-2">
              预览
            </label>
            <div className="p-3 bg-blue-50 rounded border border-blue-200">
              <div className="text-xs text-blue-900 mb-2">
                <strong>预计创建：</strong>{previewInfo.estimatedLots} 个检验批
              </div>
              <div className="text-xs text-blue-700 mb-2">
                未分配构件总数：{previewInfo.unassignedCount} 个
              </div>
              {previewInfo.groups.length > 0 && previewInfo.groups.length <= 10 && (
                <div className="mt-2 space-y-1">
                  <div className="text-xs font-medium text-blue-900">分组预览：</div>
                  {previewInfo.groups.map((group) => (
                    <div key={group.key} className="text-xs text-blue-700 pl-2">
                      · {group.label}: {group.count} 个构件
                    </div>
                  ))}
                </div>
              )}
              {previewInfo.groups.length > 10 && (
                <div className="text-xs text-blue-600 mt-2">
                  将创建 {previewInfo.groups.length} 个检验批（分组过多，未完全显示）
                </div>
              )}
            </div>
          </div>
        )}

        {/* 说明文字 */}
        <div className="p-3 bg-zinc-50 rounded border border-zinc-200">
          <p className="text-xs text-zinc-600">
            <strong>说明：</strong>
            系统将根据所选规则，自动为未分配的构件创建检验批。
            已分配到其他检验批的构件不会被重复分配。
          </p>
        </div>

        {/* 创建结果 */}
        {createLotsMutation.isSuccess && createLotsMutation.data && (
          <div className="p-3 bg-emerald-50 rounded border border-emerald-200">
            <div className="text-sm font-medium text-emerald-900 mb-1">
              创建成功
            </div>
            <div className="text-xs text-emerald-700">
              共创建 {createLotsMutation.data.total_lots} 个检验批，
              分配了 {createLotsMutation.data.elements_assigned} 个构件
            </div>
          </div>
        )}

        {/* 错误信息 */}
        {createLotsMutation.isError && (
          <div className="p-3 bg-red-50 rounded border border-red-200">
            <div className="text-sm font-medium text-red-900 mb-1">
              创建失败
            </div>
            <div className="text-xs text-red-700">
              {createLotsMutation.error instanceof Error
                ? createLotsMutation.error.message
                : '未知错误'}
            </div>
          </div>
        )}
      </div>

      {/* 底部操作按钮 */}
      <div className="p-4 border-t border-zinc-200">
        <button
          onClick={handleCreate}
          disabled={createLotsMutation.isPending}
          className={cn(
            'w-full px-4 py-2 text-sm font-medium rounded transition-colors',
            'bg-zinc-900 text-white hover:bg-zinc-800',
            'disabled:bg-zinc-400 disabled:cursor-not-allowed'
          )}
        >
          {createLotsMutation.isPending ? '创建中...' : '执行创建'}
        </button>
      </div>
    </div>
  );
}

