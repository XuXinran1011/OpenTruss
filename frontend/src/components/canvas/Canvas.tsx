/** 画布组件 */

'use client';

import { useEffect, useRef, useCallback } from 'react';
import { useCanvasStore } from '@/stores/canvas';
import { useWorkbenchStore } from '@/stores/workbench';
import { useTraceMode } from '@/hooks/useTraceMode';
import { useToastContext } from '@/providers/ToastProvider';
import { Geometry2D } from '@/types';
import { CanvasRenderer } from './CanvasRenderer';

export function Canvas() {
  const containerRef = useRef<HTMLDivElement>(null);
  const {
    canvasSize,
    setCanvasSize,
    viewTransform,
    showGrid,
    showDwgBackground,
    dwgImageUrl,
    dwgImage,
    dwgOpacity,
    xrayMode,
  } = useCanvasStore();

  const { mode, selectedElementIds, addSelectedElementId, setSelectedElementIds } = useWorkbenchStore();
  const { updateTopology, isUpdating, error, clearError } = useTraceMode();
  const { showToast } = useToastContext();

  // 显示错误和成功提示
  useEffect(() => {
    if (error) {
      showToast(error.message, 'error');
      clearError();
    }
  }, [error, showToast, clearError]);

  // 显示拓扑更新成功提示
  useEffect(() => {
    if (!isUpdating && !error && mode === 'trace') {
      // 这里可以根据需要添加成功提示
      // 但由于拖拽操作频繁，我们不显示每次拖拽的成功提示，只在错误时提示
    }
  }, [isUpdating, error, mode, showToast]);

  // 处理构件拖拽开始
  const handleElementDragStart = useCallback((elementIds: string[]) => {
    // 可以在拖拽开始时添加视觉反馈
    console.log('Dragging elements:', elementIds);
  }, []);

  // 处理构件点击
  const handleElementClick = useCallback((elementId: string, event: MouseEvent) => {
    // 按住 Ctrl/Cmd 键可以多选
    if (event.ctrlKey || event.metaKey) {
      addSelectedElementId(elementId);
    } else {
      // 否则单选
      setSelectedElementIds([elementId]);
    }
  }, [addSelectedElementId, setSelectedElementIds]);

  // 处理构件拖拽（Trace Mode 下的拓扑更新）
  // 使用 useCallback 和节流优化性能
  const handleElementDrag = useCallback((elementId: string, newCoordinates: number[][]) => {
    // 实时更新时的处理（可选，用于视觉反馈）
    // 这里可以添加实时预览逻辑，但为了性能，我们不在拖拽过程中频繁更新
  }, []);

  
  // 处理构件拖拽结束（Trace Mode 下的拓扑更新）
  // 使用防抖确保在快速拖拽时不会触发过多API调用
  const handleElementDragEnd = useCallback((elementId: string, finalCoordinates: number[][], originalType?: string, originalClosed?: boolean) => {
    if (mode === 'trace') {
      // 使用原始几何类型，如果未提供则根据坐标数量推断
      const geomType = (originalType === 'Line' || originalType === 'Polyline') 
        ? originalType 
        : (finalCoordinates.length === 2 ? 'Line' : 'Polyline');
      
      const newGeometry2D: Geometry2D = {
        type: geomType as 'Line' | 'Polyline',
        coordinates: finalCoordinates.map((coord): [number, number] => [coord[0] || 0, coord[1] || 0]),
        closed: originalClosed || false,
      };

      // 调用拓扑更新 API（成功提示由 hook 的 onSuccess 处理）
      updateTopology(elementId, {
        geometry_2d: newGeometry2D,
      });
    }
  }, [mode, updateTopology]);

  // 更新画布尺寸
  useEffect(() => {
    const updateSize = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        setCanvasSize({ width: rect.width, height: rect.height });
      }
    };

    updateSize();
    window.addEventListener('resize', updateSize);
    return () => window.removeEventListener('resize', updateSize);
  }, [setCanvasSize]);

  return (
    <div
      ref={containerRef}
      className="relative w-full h-full overflow-hidden bg-white"
      style={{
        backgroundImage: showGrid ? 'radial-gradient(circle, #E4E4E7 1px, transparent 1px)' : 'none',
        backgroundSize: '20px 20px',
      }}
    >
      {/* DWG 底图（Trace Mode） */}
      {mode === 'trace' && showDwgBackground && dwgImage && (
        <img
          src={dwgImageUrl || undefined}
          alt="DWG 底图"
          className="absolute inset-0 object-contain pointer-events-none"
          style={{
            opacity: dwgOpacity,
            filter: xrayMode ? 'grayscale(100%)' : 'none',
          }}
        />
      )}

      {/* Canvas 渲染器 */}
      <CanvasRenderer
        width={canvasSize.width}
        height={canvasSize.height}
        viewTransform={viewTransform}
        selectedElementIds={selectedElementIds}
        mode={mode}
        onElementDragStart={handleElementDragStart}
        onElementClick={handleElementClick}
        onElementDrag={handleElementDrag}
        onElementDragEnd={handleElementDragEnd}
      />
    </div>
  );
}

