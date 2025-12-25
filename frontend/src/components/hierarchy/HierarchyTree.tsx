/** 层级树组件 */

'use client';

import { useEffect, useMemo, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useHierarchyStore } from '@/stores/hierarchy';
import { getProjectHierarchy } from '@/services/hierarchy';
import { getElements } from '@/services/elements';
import { HierarchyTreeNode } from './HierarchyTreeNode';
import { useWorkbenchStore } from '@/stores/workbench';
import { useCanvas } from '@/contexts/CanvasContext';

interface HierarchyTreeProps {
  projectId: string;
}

function HierarchyTreeComponent({ projectId }: HierarchyTreeProps) {
  const {
    currentProjectId,
    setCurrentProjectId,
    hierarchyData,
    setHierarchyData,
    searchKeyword,
    setSearchKeyword,
    setSelectedNodeId,
  } = useHierarchyStore();

  const { setSelectedElementIds } = useWorkbenchStore();
  const { canvasRef } = useCanvas();

  // 设置当前项目 ID
  useEffect(() => {
    setCurrentProjectId(projectId);
  }, [projectId, setCurrentProjectId]);

  // 获取层级树数据
  const { data, isLoading, error } = useQuery({
    queryKey: ['hierarchy', projectId],
    queryFn: () => getProjectHierarchy(projectId),
    enabled: !!projectId,
  });

  // 更新层级树数据到 store
  useEffect(() => {
    if (data?.hierarchy) {
      setHierarchyData(data.hierarchy);
    }
  }, [data, setHierarchyData]);

  // 搜索过滤
  const filteredHierarchy = useMemo(() => {
    if (!hierarchyData || !searchKeyword.trim()) {
      return hierarchyData;
    }

    const filterNode = (node: typeof hierarchyData): typeof hierarchyData | null => {
      const matchesSearch = node.name.toLowerCase().includes(searchKeyword.toLowerCase());
      
      const filteredChildren = node.children
        .map(filterNode)
        .filter((child): child is typeof hierarchyData => child !== null);

      if (matchesSearch || filteredChildren.length > 0) {
        return {
          ...node,
          children: filteredChildren,
        };
      }

      return null;
    };

    return filterNode(hierarchyData);
  }, [hierarchyData, searchKeyword]);

  const handleNodeSelect = useCallback(async (nodeId: string) => {
    setSelectedNodeId(nodeId);
    
    // 尝试定位到该节点下的构件
    // 注意：这里我们需要知道节点类型来判断使用哪个查询参数
    // 由于层级树节点可能包含 metadata，我们可以通过查询来获取构件
    try {
      // 尝试按 inspection_lot_id 查询（如果是 InspectionLot 节点）
      const lotResult = await getElements({ inspection_lot_id: nodeId, page: 1, page_size: 100 });
      if (lotResult.items && lotResult.items.length > 0) {
        const elementIds = lotResult.items.map((el) => el.id);
        setSelectedElementIds(elementIds);
        if (canvasRef?.current && elementIds.length > 0) {
          canvasRef.current.focusOnElements(elementIds);
        }
        return;
      }

      // 尝试按 item_id 查询（如果是 Item 节点）
      const itemResult = await getElements({ item_id: nodeId, page: 1, page_size: 100 });
      if (itemResult.items && itemResult.items.length > 0) {
        const elementIds = itemResult.items.map((el) => el.id);
        setSelectedElementIds(elementIds);
        if (canvasRef?.current && elementIds.length > 0) {
          canvasRef.current.focusOnElements(elementIds);
        }
        return;
      }

      // 如果没有找到构件，清空选择
      setSelectedElementIds([]);
    } catch (error) {
      console.error('Failed to get elements for node:', error);
      setSelectedElementIds([]);
    }
  }, [setSelectedNodeId, setSelectedElementIds, canvasRef]);

  if (isLoading) {
    return (
      <div className="p-4 text-sm text-zinc-500 text-center">加载中...</div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-sm text-red-600 text-center">
        加载失败: {error instanceof Error ? error.message : '未知错误'}
      </div>
    );
  }

  if (!filteredHierarchy) {
    return (
      <div className="p-4 text-sm text-zinc-500 text-center">暂无数据</div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* 搜索框 */}
      <div className="p-2 border-b border-zinc-200">
        <input
          type="text"
          placeholder="搜索节点..."
          value={searchKeyword}
          onChange={(e) => setSearchKeyword(e.target.value)}
          className="w-full px-3 py-1.5 text-sm border border-zinc-300 rounded focus:outline-none focus:ring-2 focus:ring-zinc-900 focus:border-transparent"
        />
      </div>

      {/* 层级树内容 */}
      <div className="flex-1 overflow-auto">
        <HierarchyTreeNode node={filteredHierarchy} onSelect={handleNodeSelect} />
      </div>
    </div>
  );
}

export { HierarchyTreeComponent as HierarchyTree };

