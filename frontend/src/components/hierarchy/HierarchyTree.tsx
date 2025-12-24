/** 层级树组件 */

'use client';

import { useEffect, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useHierarchyStore } from '@/stores/hierarchy';
import { getProjectHierarchy } from '@/services/hierarchy';
import { HierarchyTreeNode } from './HierarchyTreeNode';
import { useWorkbenchStore } from '@/stores/workbench';

interface HierarchyTreeProps {
  projectId: string;
}

export function HierarchyTree({ projectId }: HierarchyTreeProps) {
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

  const handleNodeSelect = (nodeId: string) => {
    setSelectedNodeId(nodeId);
    // TODO: 定位到画布中的相关构件
    // 这里可以调用 API 获取该节点下的构件，然后高亮显示
    setSelectedElementIds([]); // 暂时清空选中
  };

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

