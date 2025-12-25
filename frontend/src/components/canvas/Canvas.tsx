/** 画布组件 */

'use client';

import { useEffect, useRef, useCallback, useImperativeHandle, forwardRef } from 'react';
import { useCanvasStore } from '@/stores/canvas';
import { useWorkbenchStore } from '@/stores/workbench';
import { useTraceMode } from '@/hooks/useTraceMode';
import { useToastContext } from '@/providers/ToastProvider';
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';
import { Geometry2D } from '@/types';
import { CanvasRenderer } from './CanvasRenderer';
import { getElementDetail } from '@/services/elements';
import { getGeometryBoundingBox } from '@/utils/topology';

export interface CanvasHandle {
  focusOnElement: (elementId: string) => Promise<void>;
  focusOnElements: (elementIds: string[]) => Promise<void>;
}

export const Canvas = forwardRef<CanvasHandle>((props, ref) => {
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

  const { mode, selectedElementIds, addSelectedElementId, setSelectedElementIds, addSelectedElementIds, clearSelection } = useWorkbenchStore();
  const { updateTopology, isUpdating, error, clearError } = useTraceMode();
  const { showToast } = useToastContext();
  
  // 启用键盘快捷键
  useKeyboardShortcuts();

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
    // 拖拽已通过DragContext和视觉反馈处理
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

  // 定位到构件的方法
  const focusOnElement = useCallback(async (elementId: string) => {
    try {
      const elementDetail = await getElementDetail(elementId);
      if (!elementDetail?.geometry_2d?.coordinates || elementDetail.geometry_2d.coordinates.length === 0) {
        return;
      }

      // 计算构件的边界框
      const bbox = getGeometryBoundingBox(elementDetail.geometry_2d.coordinates);
      if (!bbox) return;

      // 计算中心点
      const centerX = bbox.x + bbox.width / 2;
      const centerY = bbox.y + bbox.height / 2;

      // 获取画布中心
      const canvasCenterX = canvasSize.width / 2;
      const canvasCenterY = canvasSize.height / 2;

      // 计算需要平移的距离（考虑当前缩放）
      const scale = viewTransform.scale;
      const targetX = canvasCenterX - centerX * scale;
      const targetY = canvasCenterY - centerY * scale;

      // 平滑过渡到目标位置
      const duration = 500; // 动画时长（毫秒）
      const startX = viewTransform.x;
      const startY = viewTransform.y;
      const startTime = Date.now();

      const animate = () => {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // 使用 easing 函数（ease-out）
        const eased = 1 - Math.pow(1 - progress, 3);

        const currentX = startX + (targetX - startX) * eased;
        const currentY = startY + (targetY - startY) * eased;

        setViewTransform({
          x: currentX,
          y: currentY,
          scale: viewTransform.scale,
        });

        if (progress < 1) {
          requestAnimationFrame(animate);
        }
      };

      animate();

      // 选中该构件
      setSelectedElementIds([elementId]);
    } catch (error) {
      console.error('Failed to focus on element:', error);
    }
  }, [canvasSize, viewTransform, setViewTransform, setSelectedElementIds]);

  // 定位到多个构件（显示所有构件的边界）
  const focusOnElements = useCallback(async (elementIds: string[]) => {
    if (elementIds.length === 0) return;
    if (elementIds.length === 1) {
      return focusOnElement(elementIds[0]);
    }

    try {
      // 获取所有构件的详情
      const elementDetails = await Promise.all(
        elementIds.map(id => getElementDetail(id).catch(() => null))
      );

      // 计算所有构件的联合边界框
      let minX = Infinity;
      let minY = Infinity;
      let maxX = -Infinity;
      let maxY = -Infinity;

      for (const detail of elementDetails) {
        if (!detail?.geometry_2d?.coordinates) continue;
        const bbox = getGeometryBoundingBox(detail.geometry_2d.coordinates);
        if (!bbox) continue;

        minX = Math.min(minX, bbox.x);
        minY = Math.min(minY, bbox.y);
        maxX = Math.max(maxX, bbox.x + bbox.width);
        maxY = Math.max(maxY, bbox.y + bbox.height);
      }

      if (minX === Infinity) return;

      // 计算中心点和尺寸
      const centerX = (minX + maxX) / 2;
      const centerY = (minY + maxY) / 2;
      const width = maxX - minX;
      const height = maxY - minY;

      // 获取画布尺寸
      const canvasWidth = canvasSize.width;
      const canvasHeight = canvasSize.height;

      // 计算合适的缩放比例（留一些边距）
      const padding = 50;
      const scaleX = (canvasWidth - padding * 2) / width;
      const scaleY = (canvasHeight - padding * 2) / height;
      const targetScale = Math.min(scaleX, scaleY, viewTransform.scale); // 不放大，只缩小

      // 计算需要平移的距离
      const canvasCenterX = canvasWidth / 2;
      const canvasCenterY = canvasHeight / 2;
      const targetX = canvasCenterX - centerX * targetScale;
      const targetY = canvasCenterY - centerY * targetScale;

      // 平滑过渡
      const duration = 500;
      const startX = viewTransform.x;
      const startY = viewTransform.y;
      const startScale = viewTransform.scale;
      const startTime = Date.now();

      const animate = () => {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);

        const currentX = startX + (targetX - startX) * eased;
        const currentY = startY + (targetY - startY) * eased;
        const currentScale = startScale + (targetScale - startScale) * eased;

        setViewTransform({
          x: currentX,
          y: currentY,
          scale: currentScale,
        });

        if (progress < 1) {
          requestAnimationFrame(animate);
        }
      };

      animate();

      // 选中这些构件
      setSelectedElementIds(elementIds);
    } catch (error) {
      console.error('Failed to focus on elements:', error);
    }
  }, [canvasSize, viewTransform, setViewTransform, setSelectedElementIds, focusOnElement]);

  // 暴露方法给父组件
  useImperativeHandle(ref, () => ({
    focusOnElement,
    focusOnElements,
  }));

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
      {/* DWG 底图（Trace Mode）- 在SVG下方作为背景层 */}
      {mode === 'trace' && showDwgBackground && dwgImage && (
        <img
          src={dwgImageUrl || undefined}
          alt="DWG 底图"
          className="absolute inset-0 object-contain pointer-events-none z-0"
          style={{
            opacity: dwgOpacity,
            filter: xrayMode ? 'grayscale(100%) brightness(1.2)' : 'none',
            mixBlendMode: xrayMode ? 'multiply' : 'normal',
          }}
          onError={(e) => {
            console.error('Failed to load DWG background image');
            (e.target as HTMLImageElement).style.display = 'none';
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
        onSelectionChange={setSelectedElementIds}
        onSelectionAdd={addSelectedElementIds}
        onSelectionClear={clearSelection}
      />
    </div>
  );
});

Canvas.displayName = 'Canvas';

