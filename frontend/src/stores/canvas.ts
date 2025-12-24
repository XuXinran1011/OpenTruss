/** 画布状态管理 */

import { create } from 'zustand';

interface CanvasState {
  // 视图变换
  viewTransform: {
    x: number; // 平移 X
    y: number; // 平移 Y
    scale: number; // 缩放比例
  };
  setViewTransform: (transform: Partial<CanvasState['viewTransform']>) => void;
  resetView: () => void;
  
  // 画布尺寸
  canvasSize: {
    width: number;
    height: number;
  };
  setCanvasSize: (size: { width: number; height: number }) => void;
  
  // 是否显示网格
  showGrid: boolean;
  setShowGrid: (show: boolean) => void;
  
  // 是否显示 DWG 底图
  showDwgBackground: boolean;
  setShowDwgBackground: (show: boolean) => void;
  dwgImageUrl: string | null;
  setDwgImageUrl: (url: string | null) => void;
  dwgImage: HTMLImageElement | null;
  setDwgImage: (image: HTMLImageElement | null) => void;
  dwgOpacity: number;
  setDwgOpacity: (opacity: number) => void;
  xrayMode: boolean;
  setXrayMode: (enabled: boolean) => void;
}

const INITIAL_TRANSFORM = {
  x: 0,
  y: 0,
  scale: 1,
};

export const useCanvasStore = create<CanvasState>((set) => ({
  viewTransform: INITIAL_TRANSFORM,
  setViewTransform: (transform) =>
    set((state) => ({
      viewTransform: { ...state.viewTransform, ...transform },
    })),
  resetView: () => set({ viewTransform: INITIAL_TRANSFORM }),
  
  canvasSize: { width: 0, height: 0 },
  setCanvasSize: (size) => set({ canvasSize: size }),
  
  showGrid: true,
  setShowGrid: (show) => set({ showGrid: show }),
  
  showDwgBackground: false,
  setShowDwgBackground: (show) => set({ showDwgBackground: show }),
  dwgImageUrl: null,
  setDwgImageUrl: (url) => set({ dwgImageUrl: url }),
  dwgImage: null,
  setDwgImage: (image) => set({ dwgImage: image }),
  dwgOpacity: 0.5,
  setDwgOpacity: (opacity) => set({ dwgOpacity: opacity }),
  xrayMode: false,
  setXrayMode: (enabled) => set({ xrayMode: enabled }),
}));

