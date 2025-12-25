/** 工作台状态管理 */

import { create } from 'zustand';
import { WorkbenchMode } from '@/types';

interface WorkbenchState {
  // 当前模式
  mode: WorkbenchMode;
  setMode: (mode: WorkbenchMode) => void;
  
  // 选中的构件 ID 列表
  selectedElementIds: string[];
  setSelectedElementIds: (ids: string[]) => void;
  addSelectedElementId: (id: string) => void;
  addSelectedElementIds: (ids: string[]) => void;
  removeSelectedElementId: (id: string) => void;
  clearSelection: () => void;
  
  // Trace Mode 特定状态
  traceMode: {
    dwgOpacity: number; // DWG 底图透明度 (0-100)
    xRayMode: boolean; // X-Ray 模式
  };
  setDwgOpacity: (opacity: number) => void;
  setXRayMode: (enabled: boolean) => void;
  
  // Lift Mode 特定状态
  liftMode: {
    showZMissing: boolean; // 是否高亮显示 Z-Missing 构件
  };
  setShowZMissing: (show: boolean) => void;
}

export const useWorkbenchStore = create<WorkbenchState>((set) => ({
  // 默认模式为 trace
  mode: 'trace',
  setMode: (mode) => set({ mode }),
  
  // 选中状态
  selectedElementIds: [],
  setSelectedElementIds: (ids) => set({ selectedElementIds: ids }),
  addSelectedElementId: (id) =>
    set((state) => ({
      selectedElementIds: state.selectedElementIds.includes(id)
        ? state.selectedElementIds
        : [...state.selectedElementIds, id],
    })),
  addSelectedElementIds: (ids) =>
    set((state) => {
      const newIds = ids.filter((id) => !state.selectedElementIds.includes(id));
      return {
        selectedElementIds: [...state.selectedElementIds, ...newIds],
      };
    }),
  removeSelectedElementId: (id) =>
    set((state) => ({
      selectedElementIds: state.selectedElementIds.filter((eid) => eid !== id),
    })),
  clearSelection: () => set({ selectedElementIds: [] }),
  
  // Trace Mode 状态
  traceMode: {
    dwgOpacity: 30, // 默认 30%
    xRayMode: false,
  },
  setDwgOpacity: (opacity) =>
    set((state) => ({
      traceMode: { ...state.traceMode, dwgOpacity: Math.max(0, Math.min(100, opacity)) },
    })),
  setXRayMode: (enabled) =>
    set((state) => ({
      traceMode: { ...state.traceMode, xRayMode: enabled },
    })),
  
  // Lift Mode 状态
  liftMode: {
    showZMissing: true, // 默认显示 Z-Missing
  },
  setShowZMissing: (show) =>
    set((state) => ({
      liftMode: { ...state.liftMode, showZMissing: show },
    })),
}));

