/** 层级树状态管理 */

import { create } from 'zustand';
import { HierarchyNode } from '@/services/hierarchy';

interface HierarchyState {
  // 当前项目 ID
  currentProjectId: string | null;
  setCurrentProjectId: (projectId: string | null) => void;
  
  // 展开的节点 ID 集合
  expandedNodeIds: Set<string>;
  toggleNode: (nodeId: string) => void;
  expandNode: (nodeId: string) => void;
  collapseNode: (nodeId: string) => void;
  expandAll: () => void;
  collapseAll: () => void;
  
  // 选中的节点 ID（用于定位）
  selectedNodeId: string | null;
  setSelectedNodeId: (nodeId: string | null) => void;
  
  // 层级树数据
  hierarchyData: HierarchyNode | null;
  setHierarchyData: (data: HierarchyNode | null) => void;
  
  // 搜索关键词
  searchKeyword: string;
  setSearchKeyword: (keyword: string) => void;
}

export const useHierarchyStore = create<HierarchyState>((set, get) => ({
  currentProjectId: null,
  setCurrentProjectId: (projectId) => set({ currentProjectId: projectId }),
  
  expandedNodeIds: new Set<string>(),
  toggleNode: (nodeId) =>
    set((state) => {
      const newSet = new Set(state.expandedNodeIds);
      if (newSet.has(nodeId)) {
        newSet.delete(nodeId);
      } else {
        newSet.add(nodeId);
      }
      return { expandedNodeIds: newSet };
    }),
  expandNode: (nodeId) =>
    set((state) => {
      const newSet = new Set(state.expandedNodeIds);
      newSet.add(nodeId);
      return { expandedNodeIds: newSet };
    }),
  collapseNode: (nodeId) =>
    set((state) => {
      const newSet = new Set(state.expandedNodeIds);
      newSet.delete(nodeId);
      return { expandedNodeIds: newSet };
    }),
  expandAll: () => {
    // 展开所有节点（递归收集所有节点 ID）
    const collectNodeIds = (node: HierarchyNode): string[] => {
      return [node.id, ...node.children.flatMap(collectNodeIds)];
    };
    const hierarchy = get().hierarchyData;
    if (hierarchy) {
      const allIds = collectNodeIds(hierarchy);
      set({ expandedNodeIds: new Set(allIds) });
    }
  },
  collapseAll: () => set({ expandedNodeIds: new Set() }),
  
  selectedNodeId: null,
  setSelectedNodeId: (nodeId) => set({ selectedNodeId: nodeId }),
  
  hierarchyData: null,
  setHierarchyData: (data) => set({ hierarchyData: data }),
  
  searchKeyword: '',
  setSearchKeyword: (keyword) => set({ searchKeyword: keyword }),
}));

