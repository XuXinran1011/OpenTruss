/** 画布组件 */

'use client';

import { useEffect, useRef, useCallback, useImperativeHandle, forwardRef, useState, useMemo } from 'react';
import { useCanvasStore } from '@/stores/canvas';
import { useWorkbenchStore } from '@/stores/workbench';
import { useTraceMode } from '@/hooks/useTraceMode';
import { useToastContext } from '@/providers/ToastProvider';
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';
import { useDrag } from '@/contexts/DragContext';
import { Geometry2D } from '@/types';
import { CanvasRenderer } from './CanvasRenderer';
import { getElementDetail, getElements, type ElementDetail } from '@/services/elements';
import { getGeometryBoundingBox } from '@/utils/topology';
import { MEPRoutingPanel } from './MEPRoutingPanel';
import { useQuery } from '@tanstack/react-query';
import { SemanticValidator } from '@/lib/rules/SemanticValidator';
import { validateSemanticConnection } from '@/services/validation';
import { SpatialIndex } from '@/utils/spatial-index';
import { debounce } from '@/utils/performance';

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
    setViewTransform,
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
  const { draggedElementIds, isDraggingElement, setDragPosition, setDraggedElementIds } = useDrag();
  const [routingPath, setRoutingPath] = useState<{ x: number; y: number }[] | null>(null);
  const [collidingElementIds, setCollidingElementIds] = useState<Set<string>>(new Set());
  
  // 获取选中的元素详情（用于路径规划）
  const selectedElementsQuery = useQuery({
    queryKey: ['elements', 'details', selectedElementIds],
    queryFn: async () => {
      if (selectedElementIds.length === 0) return [];
      const details = await Promise.all(
        selectedElementIds.map((id) => getElementDetail(id))
      );
      return details.filter((d) => d !== null);
    },
    enabled: selectedElementIds.length > 0 && mode === 'trace',
  });
  
  const selectedElements = selectedElementsQuery.data || [];
  const sourceElement = selectedElements.length >= 1 ? selectedElements[0] : null;
  const targetElement = selectedElements.length >= 2 ? selectedElements[1] : null;
  const showRoutingPanel = mode === 'trace' && selectedElements.length >= 2;
  
  // 语义校验器实例（使用配置文件进行快速验证）
  const semanticValidator = useMemo(() => new SemanticValidator(), []);
  
  // 语义校验结果（当选择两个元素时）
  const [semanticValidationResult, setSemanticValidationResult] = useState<{
    valid: boolean;
    error?: string;
    suggestion?: string;
  } | null>(null);
  
  // 当选择两个元素时，进行语义校验
  useEffect(() => {
    if (mode === 'trace' && sourceElement && targetElement) {
      // 使用前端校验器进行快速验证（实时反馈）
      const result = semanticValidator.validateConnection(
        sourceElement.speckle_type,
        targetElement.speckle_type,
        'feeds'
      );
      
      setSemanticValidationResult({
        valid: result.valid,
        error: result.error,
        suggestion: result.suggestion,
      });
      
      // 如果连接无效，显示警告（但不阻止操作）
      if (!result.valid) {
        showToast(
          `语义校验警告: ${result.error}${result.suggestion ? ` (建议使用: ${result.suggestion})` : ''}`,
          'warning'
        );
      }
      
      // 可选：同时调用后端 API 进行更严格的验证（异步）
      validateSemanticConnection({
        source_type: sourceElement.speckle_type,
        target_type: targetElement.speckle_type,
        relationship: 'feeds',
      }).catch((error) => {
        // 后端验证失败不影响前端操作，只记录错误
        console.warn('后端语义校验失败:', error);
      });
    } else {
      setSemanticValidationResult(null);
    }
  }, [mode, sourceElement, targetElement, semanticValidator, showToast]);

  // 获取所有元素数据（用于碰撞检测）
  const allElementsQuery = useQuery({
    queryKey: ['elements', 'all'],
    queryFn: async () => {
      const response = await getElements({ page_size: 10000 }); // 获取所有元素
      return response.items || [];
    },
    enabled: mode === 'trace', // 只在 Trace Mode 下启用
    staleTime: 30000, // 30秒内使用缓存
  });

  const allElements = allElementsQuery.data || [];

  // 获取所有元素的详情（用于碰撞检测）
  const allElementDetailsQuery = useQuery({
    queryKey: ['elements', 'details', 'all', allElements.map(e => e.id).join(',')],
    queryFn: async () => {
      if (allElements.length === 0) return new Map<string, ElementDetail>();
      
      // 批量获取元素详情
      const elementIds = allElements.map(e => e.id);
      const BATCH_SIZE = 100;
      const detailsMap = new Map<string, ElementDetail>();
      
      for (let i = 0; i < elementIds.length; i += BATCH_SIZE) {
        const batch = elementIds.slice(i, i + BATCH_SIZE);
        const batchDetails = await Promise.all(
          batch.map(id => getElementDetail(id))
        );
        
        batchDetails.forEach(detail => {
          if (detail) {
            detailsMap.set(detail.id, detail);
          }
        });
      }
      
      return detailsMap;
    },
    enabled: allElements.length > 0 && mode === 'trace',
    staleTime: 30000,
  });

  const allElementDetailsMap = allElementDetailsQuery.data || new Map<string, ElementDetail>();

  // 创建空间索引（用于碰撞检测）
  const collisionSpatialIndex = useMemo(() => {
    const index = new SpatialIndex();
    
    if (allElementDetailsMap.size > 0) {
      const elementsToIndex = Array.from(allElementDetailsMap.values())
        .filter(detail => detail.geometry_2d?.coordinates)
        .map(detail => ({
          id: detail.id,
          coordinates: detail.geometry_2d!.coordinates,
        }));
      
      index.load(elementsToIndex);
    }
    
    return index;
  }, [allElementDetailsMap]);
  
  // 启用键盘快捷键
  useKeyboardShortcuts();
  
  // 处理拖拽过程中的鼠标移动（用于视觉反馈和ESC取消）
  useEffect(() => {
    if (mode !== 'classify') return;

    const handleMouseMove = (e: MouseEvent) => {
      // 如果有拖拽的元素，更新拖拽位置
      if (draggedElementIds && draggedElementIds.length > 0) {
        setDragPosition({ x: e.clientX, y: e.clientY });
      }
    };

    const handleMouseUp = () => {
      // 拖拽结束时清除位置和状态（如果还在拖拽）
      if (draggedElementIds && draggedElementIds.length > 0) {
        // 延迟清除，让drop事件先处理
        setTimeout(() => {
          setDragPosition(null);
        }, 100);
      }
    };

    const handleKeyDown = (e: KeyboardEvent) => {
      // ESC键取消拖拽
      if (e.key === 'Escape' && draggedElementIds && draggedElementIds.length > 0) {
        setDraggedElementIds(null);
        setDragPosition(null);
        showToast('拖拽已取消', 'info');
      }
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    window.addEventListener('keydown', handleKeyDown);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [mode, draggedElementIds, setDragPosition, setDraggedElementIds, showToast]);

  // 显示错误和成功提示
  useEffect(() => {
    if (error) {
      showToast(error.message, 'error');
      clearError();
    }
  }, [error, showToast, clearError]);
  
  // 当选择改变时，如果少于2个元素，清除路径
  useEffect(() => {
    if (selectedElementIds.length < 2) {
      setRoutingPath(null);
    }
  }, [selectedElementIds]);

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

  // 碰撞检测的防抖处理（避免每帧都检测）
  const checkCollisionDebounced = useMemo(
    () =>
      debounce((elementId: string, newCoordinates: number[][]) => {
        if (mode !== 'trace') return;
        
        const element = allElementDetailsMap.get(elementId);
        if (!element || !element.geometry_2d) return;
        
        // 创建临时元素（使用新的坐标）
        const tempElement: ElementDetail = {
          ...element,
          geometry_2d: {
            ...element.geometry_2d,
            coordinates: newCoordinates,
          },
        };
        
        // 检查碰撞
        const collisions = collisionSpatialIndex.checkCollision3D(
          tempElement,
          allElementDetailsMap
        );
        
        // 更新碰撞状态
        if (collisions.length > 0) {
          setCollidingElementIds(new Set([elementId, ...collisions]));
          // 显示警告（只显示一次，避免重复提示）
          if (collisions.length === 1) {
            showToast(`碰撞检测：与 ${collisions[0]} 发生重叠`, 'warning');
          } else {
            showToast(`碰撞检测：与 ${collisions.length} 个构件发生重叠`, 'warning');
          }
        } else {
          setCollidingElementIds(new Set());
        }
      }, 100), // 100ms 防抖
    [mode, allElementDetailsMap, collisionSpatialIndex, showToast]
  );

  // 处理构件拖拽（Trace Mode 下的拓扑更新和碰撞检测）
  const handleElementDrag = useCallback(
    (elementId: string, newCoordinates: number[][]) => {
      // 执行防抖的碰撞检测
      checkCollisionDebounced(elementId, newCoordinates);
    },
    [checkCollisionDebounced]
  );

  
  // 处理构件拖拽结束（Trace Mode 下的拓扑更新）
  // 使用防抖确保在快速拖拽时不会触发过多API调用
  const handleElementDragEnd = useCallback((elementId: string, finalCoordinates: number[][], originalType?: string, originalClosed?: boolean) => {
    if (mode === 'trace') {
      // 角度吸附（规则引擎 Phase 2）
      let adjustedCoordinates = finalCoordinates;
      
      // 如果路径有多个点，对每个转弯点进行角度吸附
      if (finalCoordinates.length >= 3) {
        try {
          // 动态导入 ConstructabilityValidator（避免循环依赖）
          import('@/lib/rules/ConstructabilityValidator').then(({ ConstructabilityValidator }) => {
            const validator = new ConstructabilityValidator();
            
            // 对每个中间点进行角度吸附
            const newCoords = [...finalCoordinates];
            let hasChanges = false;
            
            for (let i = 1; i < finalCoordinates.length - 1; i++) {
              const turnAngle = validator.calculateTurnAngle(finalCoordinates, i);
              const snappedAngle = validator.snapAngle(turnAngle);
              
              // 如果角度可以吸附，调整路径点
              // 注意：这里只是简化实现，实际的角度吸附需要更复杂的几何计算
              // 当前实现仅作为示例，完整的角度吸附需要根据具体需求调整路径点坐标
              if (snappedAngle !== null && Math.abs(turnAngle - snappedAngle) > validator['config'].angles.tolerance) {
                // 这里应该根据 snappedAngle 调整路径点，但需要更复杂的几何计算
                // 暂时跳过，保持原始坐标
                // TODO: 实现完整的角度吸附逻辑
              }
            }
            
            // 如果坐标有变化，使用调整后的坐标
            if (hasChanges) {
              adjustedCoordinates = newCoords;
            }
          }).catch((error) => {
            console.warn('Failed to load ConstructabilityValidator:', error);
          });
        } catch (error) {
          console.warn('Failed to apply angle snapping:', error);
        }
      }
      
      // 使用原始几何类型，如果未提供则根据坐标数量推断
      const geomType = (originalType === 'Line' || originalType === 'Polyline') 
        ? originalType 
        : (adjustedCoordinates.length === 2 ? 'Line' : 'Polyline');
      
      const newGeometry2D: Geometry2D = {
        type: geomType as 'Line' | 'Polyline',
        coordinates: adjustedCoordinates.map((coord): [number, number] => [coord[0] || 0, coord[1] || 0]),
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
        routingPath={routingPath}
        collidingElementIds={Array.from(collidingElementIds)}
        onElementDragStart={handleElementDragStart}
        onElementClick={handleElementClick}
        onElementDrag={handleElementDrag}
        onElementDragEnd={handleElementDragEnd}
        onSelectionChange={setSelectedElementIds}
        onSelectionAdd={addSelectedElementIds}
        onSelectionClear={clearSelection}
      />
      
      {/* MEP 路径规划面板（Trace Mode，选中2个元素时显示） */}
      {showRoutingPanel && (
        <div className="absolute top-4 right-4 z-50">
          <MEPRoutingPanel
            sourceElement={sourceElement}
            targetElement={targetElement}
            onRouteCalculated={setRoutingPath}
            onClose={() => {
              setRoutingPath(null);
              clearSelection();
            }}
          />
        </div>
      )}
    </div>
  );
});

Canvas.displayName = 'Canvas';

