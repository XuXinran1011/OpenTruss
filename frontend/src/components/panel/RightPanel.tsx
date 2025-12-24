/**
 * 右侧面板（带标签页）
 * 
 * 包含参数面板和检验批管理面板
 */

'use client';

import { useState } from 'react';
import { ParameterPanel } from './ParameterPanel';
import { LotStrategyPanel } from '@/components/lots/LotStrategyPanel';
import { LotManagementPanel } from '@/components/lots/LotManagementPanel';
import { ApprovalPanel } from '@/components/approval/ApprovalPanel';
import { ExportPanel } from '@/components/export/ExportPanel';
import { useHierarchyStore } from '@/stores/hierarchy';
import { cn } from '@/lib/utils';
import { InspectionLotStatus } from '@/types';

type TabType = 'parameters' | 'lot-strategy' | 'lot-management' | 'approval' | 'export';

export function RightPanel() {
  const [activeTab, setActiveTab] = useState<TabType>('parameters');
  const { selectedNodeId } = useHierarchyStore();
  
  // 如果选中的节点是Item，显示检验批管理相关标签页
  // 从层级数据中查找节点类型
  const { hierarchyData } = useHierarchyStore();
  const findNode = (node: any, nodeId: string): any => {
    if (node.id === nodeId) return node;
    for (const child of node.children || []) {
      const found = findNode(child, nodeId);
      if (found) return found;
    }
    return null;
  };
  const selectedNode = selectedNodeId && hierarchyData ? findNode(hierarchyData, selectedNodeId) : null;
  const isItemSelected = selectedNode?.label === 'Item';
  const isInspectionLotSelected = selectedNode?.label === 'InspectionLot';
  const lotStatus = selectedNode?.metadata?.status as InspectionLotStatus | undefined;
  const lotName = selectedNode?.name || '';
  const lotId = selectedNode?.id || null;

  const tabs = [
    { id: 'parameters' as TabType, label: '参数', show: true },
    { id: 'lot-strategy' as TabType, label: '检验批策略', show: isItemSelected },
    { id: 'lot-management' as TabType, label: '检验批管理', show: isItemSelected },
    { id: 'approval' as TabType, label: '审批', show: isInspectionLotSelected && lotStatus === 'SUBMITTED' },
    { id: 'export' as TabType, label: '导出', show: isInspectionLotSelected && lotStatus === 'APPROVED' },
  ].filter(tab => tab.show);

  const renderPanel = () => {
    switch (activeTab) {
      case 'lot-strategy':
        return <LotStrategyPanel itemId={selectedNodeId || null} onCreated={() => setActiveTab('lot-management')} />;
      case 'lot-management':
        return <LotManagementPanel itemId={selectedNodeId || null} />;
      case 'approval':
        return lotId && lotStatus ? (
          <ApprovalPanel lotId={lotId} lotStatus={lotStatus} lotName={lotName} />
        ) : (
          <div className="p-4 text-sm text-zinc-500 text-center">请先选择一个检验批</div>
        );
      case 'export':
        return lotId && lotStatus ? (
          <ExportPanel lotId={lotId} lotStatus={lotStatus} lotName={lotName} />
        ) : (
          <div className="p-4 text-sm text-zinc-500 text-center">请先选择一个检验批</div>
        );
      case 'parameters':
      default:
        return <ParameterPanel />;
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* 标签页 */}
      {tabs.length > 1 && (
        <div className="flex border-b border-zinc-200 bg-white">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                'flex-1 px-4 py-2 text-xs font-medium transition-colors',
                'border-b-2',
                activeTab === tab.id
                  ? 'border-zinc-900 text-zinc-900 bg-zinc-50'
                  : 'border-transparent text-zinc-500 hover:text-zinc-700 hover:bg-zinc-50'
              )}
            >
              {tab.label}
            </button>
          ))}
        </div>
      )}

      {/* 面板内容 */}
      <div className="flex-1 overflow-hidden">
        {renderPanel()}
      </div>
    </div>
  );
}

