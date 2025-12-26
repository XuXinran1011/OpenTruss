/** Canvas 渲染器组件 */

'use client';

import { useEffect, useRef, useMemo, useState, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { d3, type ZoomTransform, type Selection } from '@/lib/d3-wrapper';
import { getElements, ElementListItem, ElementDetail, getElementDetail, batchGetElementDetails } from '@/services/elements';
import { WorkbenchMode, Geometry2D } from '@/types';
import { useCanvasStore } from '@/stores/canvas';
import { useWorkbenchStore } from '@/stores/workbench';
import { findNearestSnapPoint, getGeometryEndpoints, getGeometryMidpoints, getGeometryIntersections, createRectangle, rectangleIntersectsGeometryPrecise, getGeometryBoundingBox, type SnapPointElement, type Rectangle } from '@/utils/topology';
import { calculateViewportBounds, isGeometryInViewport, throttle } from '@/utils/performance';
import { useDrag } from '@/contexts/DragContext';
import { SpatialIndex } from '@/utils/spatial-index';

interface CanvasRendererProps {
  width: number;
  height: number;
  viewTransform: { x: number; y: number; scale: number };
  selectedElementIds: string[];
  mode: WorkbenchMode;
  routingPath?: { x: number; y: number }[] | null; // MEP路径规划路径点
  collidingElementIds?: string[]; // 碰撞的构件ID列表（用于视觉反馈）
  onElementDragStart?: (elementIds: string[]) => void;
  onElementClick?: (elementId: string, event: MouseEvent) => void;
  onElementDrag?: (elementId: string, newCoordinates: number[][]) => void;
  onElementDragEnd?: (elementId: string, finalCoordinates: number[][], originalType?: string, originalClosed?: boolean) => void;
  onSelectionChange?: (ids: string[]) => void;
  onSelectionAdd?: (ids: string[]) => void;
  onSelectionClear?: () => void;
}

export function CanvasRenderer({
  width,
  height,
  viewTransform,
  selectedElementIds,
  mode,
  routingPath,
  collidingElementIds = [],
  onElementDragStart,
  onElementClick,
  onElementDrag,
  onElementDragEnd,
  onSelectionChange,
  onSelectionAdd,
  onSelectionClear,
}: CanvasRendererProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const { setViewTransform } = useCanvasStore();
  const { liftMode } = useWorkbenchStore();
  const { setIsDraggingElement, setDraggedElementIds, setDragPosition } = useDrag();
  const { traceMode } = useWorkbenchStore();
  
  // 存储磁吸辅助线的状态
  const [snapLine, setSnapLine] = useState<{ from: { x: number; y: number }; to: { x: number; y: number } } | null>(null);
  
  // 框选状态
  const [selectionBox, setSelectionBox] = useState<{ x: number; y: number; width: number; height: number } | null>(null);
  const [isSelecting, setIsSelecting] = useState(false);
  const selectionStartRef = useRef<{ x: number; y: number } | null>(null);
  const isDraggingElementRef = useRef(false);
  
  // 磁吸距离阈值（根据缩放动态调整，基准值为10像素）
  // 在屏幕空间中保持固定的像素距离，在世界坐标中根据缩放调整
  // 公式：屏幕像素距离 / 缩放比例 = 世界坐标距离
  // 限制在合理范围内：最小5像素，最大20像素（屏幕空间）
  const BASE_SNAP_PIXELS = 10; // 基准像素距离（屏幕空间）
  const MIN_SNAP_PIXELS = 5;   // 最小像素距离（屏幕空间）
  const MAX_SNAP_PIXELS = 20;  // 最大像素距离（屏幕空间）
  const scale = viewTransform.scale || 1;
  // 确保屏幕空间距离在合理范围内，然后转换为世界坐标距离
  const screenSnapPixels = Math.max(MIN_SNAP_PIXELS, Math.min(MAX_SNAP_PIXELS, BASE_SNAP_PIXELS));
  const SNAP_DISTANCE = screenSnapPixels / scale; // 转换为世界坐标距离

  // 获取构件列表（使用分页，避免一次性加载过多）
  // 智能加载策略：根据视口大小和缩放级别动态调整加载数量
  const loadPageSize = useMemo(() => {
    // 根据缩放级别调整：缩放越大，需要加载的构件越多（因为视口覆盖的世界坐标范围更小）
    const scale = viewTransform.scale || 1;
    // 基础加载数量：500
    // 当缩放较大时（>2），增加加载数量以覆盖更多细节
    // 当缩放较小时（<0.5），减少加载数量以节省资源
    const baseSize = 500;
    const adjustedSize = Math.max(200, Math.min(1000, baseSize * scale));
    return Math.round(adjustedSize);
  }, [viewTransform.scale]);

  const { data: elementsData } = useQuery({
    queryKey: ['elements', 'canvas', loadPageSize],
    queryFn: () => getElements({ page: 1, page_size: loadPageSize }),
    staleTime: 10000, // 10秒内使用缓存
  });

  // 计算视口边界（用于视口剔除）
  const viewportBounds = useMemo(() => {
    return calculateViewportBounds(width, height, viewTransform);
  }, [width, height, viewTransform]);

  // 筛选视口内的构件（视口剔除）- 优化：优先加载视口附近的构件
  // 智能筛选策略：根据视口位置和缩放级别，优先加载视口内和附近的构件
  const visibleElementIds = useMemo(() => {
    if (!elementsData?.items || elementsData.items.length === 0) return [];
    
    // 如果构件数量较少，直接返回所有ID
    if (elementsData.items.length <= loadPageSize) {
      return elementsData.items.map((el) => el.id);
    }
    
    // 如果构件数量较多，优先返回前loadPageSize个
    // 后续会在视口过滤中进一步筛选，确保视口内的构件能被正确加载
    return elementsData.items.slice(0, loadPageSize).map((el) => el.id);
  }, [elementsData, loadPageSize]);
  
  // 使用去重后的ID列表（避免重复请求）
  const uniqueVisibleElementIds = useMemo(() => {
    return Array.from(new Set(visibleElementIds));
  }, [visibleElementIds]);

  // 为查询创建稳定的key（排序后的ID字符串）
  const elementDetailsQueryKey = useMemo(() => {
    return ['element-details', [...uniqueVisibleElementIds].sort().join(',')];
  }, [uniqueVisibleElementIds]);

  const elementDetailsQueries = useQuery({
    queryKey: elementDetailsQueryKey, // 使用稳定的key，确保缓存一致性
    queryFn: async () => {
      // 使用批量API，限制批次大小为100（API限制）
      const BATCH_SIZE = 100; // API支持最多100个ID
      const detailsMap = new Map<string, ElementDetail>();
      
      // 分批处理
      const batches: string[][] = [];
      for (let i = 0; i < uniqueVisibleElementIds.length; i += BATCH_SIZE) {
        batches.push(uniqueVisibleElementIds.slice(i, i + BATCH_SIZE));
      }
      
      // 并行处理所有批次（批量API已经处理了并发控制）
      const batchResults = await Promise.allSettled(
        batches.map(async (batch) => {
          try {
            const result = await batchGetElementDetails(batch);
            return result.items;
          } catch (error) {
            console.error(`Failed to fetch batch of ${batch.length} elements:`, error);
            // 如果批量获取失败，回退到逐个获取（仅对失败的批次）
            const fallbackResults = await Promise.allSettled(
              batch.map((id) =>
                getElementDetail(id).catch((err) => {
                  console.error(`Failed to fetch element ${id}:`, err);
                  return null;
                })
              )
            );
            return fallbackResults
              .map((result) => (result.status === 'fulfilled' ? result.value : null))
              .filter((detail): detail is ElementDetail => detail !== null);
          }
        })
      );
      
      // 合并所有成功的结果
      batchResults.forEach((result) => {
        if (result.status === 'fulfilled') {
          result.value.forEach((detail) => {
            detailsMap.set(detail.id, detail);
          });
        }
      });
      
      return detailsMap;
    },
    enabled: uniqueVisibleElementIds.length > 0,
    staleTime: 30000, // 30秒内使用缓存，避免频繁重新获取
    gcTime: 5 * 60 * 1000, // 5分钟后清理缓存（React Query v5）
  });

  const elementDetailsMap = elementDetailsQueries.data || new Map<string, ElementDetail>();

  // 创建空间索引（用于快速查询视口内的元素）
  const spatialIndex = useMemo(() => {
    const index = new SpatialIndex();
    
    if (elementDetailsMap && elementsData?.items) {
      // 批量加载元素到空间索引
      const elementsToIndex = elementsData.items
        .map((element) => {
          const detail = elementDetailsMap.get(element.id);
          if (detail?.geometry_2d?.coordinates) {
            return {
              id: element.id,
              coordinates: detail.geometry_2d.coordinates,
            };
          }
          return null;
        })
        .filter((item): item is { id: string; coordinates: number[][] } => item !== null);
      
      index.load(elementsToIndex);
    }
    
    return index;
  }, [elementDetailsMap, elementsData]);

  // 进一步筛选视口内的构件（基于实际几何数据）
  // 优化：使用空间索引快速查询，然后进行精确检测
  // 使用更大的缓冲区（200px），确保在视口边缘的构件也能被加载
  // 同时考虑缩放级别：缩放越大，缓冲区越小（因为世界坐标范围更小）
  const viewportFilteredElements = useMemo(() => {
    if (!elementsData?.items) return [];
    
    // 根据缩放级别调整缓冲区大小
    const scale = viewTransform.scale || 1;
    const bufferSize = Math.max(100, Math.min(300, 200 / scale)); // 缩放越大，缓冲区越小
    
    // 扩展视口边界（添加缓冲区）
    const expandedViewport: Rectangle = {
      x: viewportBounds.minX - bufferSize,
      y: viewportBounds.minY - bufferSize,
      width: (viewportBounds.maxX - viewportBounds.minX) + bufferSize * 2,
      height: (viewportBounds.maxY - viewportBounds.minY) + bufferSize * 2,
    };
    
    // 使用空间索引快速查询候选元素
    const candidateIds = spatialIndex.search(expandedViewport);
    const candidateSet = new Set(candidateIds);
    
    // 过滤出候选元素，并进行精确检测
    return elementsData.items.filter((element) => {
      const detail = elementDetailsMap.get(element.id);
      if (!detail?.geometry_2d?.coordinates) {
        // 如果没有几何数据，默认显示（占位渲染）
        return true;
      }
      
      // 如果不在空间索引的候选列表中，直接排除
      if (!candidateSet.has(element.id)) {
        return false;
      }
      
      // 进行精确检测（带缓冲区）
      return isGeometryInViewport(detail.geometry_2d.coordinates, viewportBounds, bufferSize);
    });
  }, [elementsData, elementDetailsMap, viewportBounds, viewTransform.scale, spatialIndex]);

  useEffect(() => {
    if (!svgRef.current || width === 0 || height === 0) {
      return;
    }

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    // 设置 SVG 尺寸
    svg.attr('width', width).attr('height', height);

    // 创建缩放和平移容器
    const g = svg.append('g');

    // 设置初始变换
    const initialTransform = d3.zoomIdentity
      .translate(viewTransform.x, viewTransform.y)
      .scale(viewTransform.scale);
    
    g.attr('transform', initialTransform.toString());

    // 缩放和平移行为（使用节流优化性能）
    const throttledZoomUpdate = throttle((transform: ZoomTransform) => {
      const { x, y, k } = transform;
      setViewTransform({ x, y, scale: k });
      g.attr('transform', transform.toString());
    }, 16); // 约60fps

    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 10])
      .on('zoom', (event: { transform: ZoomTransform }) => {
        throttledZoomUpdate(event.transform);
      });

    // 应用缩放行为
    // 使用类型断言：zoom的类型是正确的，但call方法的类型推断过于严格
    svg.call(zoom as any);
    svg.call((zoom as any).transform, initialTransform);

    // 框选逻辑（仅在 trace 或 lift 模式下启用）
    if ((mode === 'trace' || mode === 'lift') && onSelectionChange) {
      const handleMouseDown = (event: MouseEvent) => {
        // 检查拖拽状态，如果正在拖拽构件，不执行框选
        if (isDraggingElementRef?.current) {
          if (isDraggingElementRef) isDraggingElementRef.current = false;
          return;
        }

        // 检查是否点击在构件上
        const target = event.target as SVGElement;
        const elementGroup = target.closest('[data-element-id]');
        
        // 如果点击在构件上，不执行框选（让构件的点击/拖拽处理）
        if (elementGroup) {
          return;
        }

        // 否则在空白区域开始框选
        if (event.button === 0) { // 左键
          event.preventDefault(); // 防止默认行为
          const point = d3.pointer(event, svgRef.current);
          const transformedPoint = initialTransform.invert(point);
          
          selectionStartRef.current = { x: transformedPoint[0], y: transformedPoint[1] };
          setIsSelecting(true);
          if (isDraggingElementRef) isDraggingElementRef.current = false;
          
          // 如果未按住 Ctrl/Cmd 键，清空当前选择
          if (!event.ctrlKey && !event.metaKey) {
            if (onSelectionClear) {
              onSelectionClear();
            }
          }
        }
      };

      const handleMouseMove = (event: MouseEvent) => {
        // 如果正在拖拽构件，不执行框选
        if (isDraggingElementRef?.current) {
          return;
        }

        if (!isSelecting || !selectionStartRef.current) return;

        const point = d3.pointer(event, svgRef.current);
        const transformedPoint = initialTransform.invert(point);
        const startX = selectionStartRef.current.x;
        const startY = selectionStartRef.current.y;
        const endX = transformedPoint[0];
        const endY = transformedPoint[1];

        const rect = createRectangle(startX, startY, endX, endY);
        setSelectionBox(rect);

        // 实时检测选中的构件（为了视觉反馈，但不更新选中状态直到 mouseup）
      };

      const handleMouseUp = (event: MouseEvent) => {
        // 如果正在拖拽构件，只清理状态，不执行框选
        if (isDraggingElementRef?.current) {
          if (isDraggingElementRef) isDraggingElementRef.current = false;
          return;
        }

        if (!isSelecting || !selectionStartRef.current) {
          return;
        }

        const point = d3.pointer(event, svgRef.current);
        const transformedPoint = initialTransform.invert(point);
        const startX = selectionStartRef.current.x;
        const startY = selectionStartRef.current.y;
        const endX = transformedPoint[0];
        const endY = transformedPoint[1];

        // 计算最终选择框（至少要有一定大小才认为是框选，避免误触）
        const minSize = 5 / initialTransform.k; // 考虑缩放
        const width = Math.abs(endX - startX);
        const height = Math.abs(endY - startY);

        if (width > minSize || height > minSize) {
          const rect = createRectangle(startX, startY, endX, endY);
          
          // 检测选中的构件
          const selectedIds: string[] = [];
          if (elementsData?.items && elementDetailsMap) {
            elementsData.items.forEach((element) => {
              const detail = elementDetailsMap.get(element.id);
              if (detail?.geometry_2d?.coordinates) {
                if (rectangleIntersectsGeometryPrecise(rect, detail.geometry_2d.coordinates)) {
                  selectedIds.push(element.id);
                }
              }
            });
          }

          // 更新选中状态
          if (selectedIds.length > 0) {
            if (event.ctrlKey || event.metaKey) {
              // 按住 Ctrl/Cmd 键时，添加到现有选择
              if (onSelectionAdd) {
                onSelectionAdd(selectedIds);
              }
            } else {
              // 否则替换选择
              if (onSelectionChange) {
                onSelectionChange(selectedIds);
              }
            }
          } else if (!event.ctrlKey && !event.metaKey) {
            // 如果没有选中任何构件且没有按住 Ctrl/Cmd，清空选择
            if (onSelectionClear) {
              onSelectionClear();
            }
          }
        }

        // 清理状态
        setIsSelecting(false);
        setSelectionBox(null);
        selectionStartRef.current = null;
      };

      svg.on('mousedown', handleMouseDown);
      svg.on('mousemove', handleMouseMove);
      svg.on('mouseup', handleMouseUp);
      svg.on('mouseleave', handleMouseUp); // 鼠标离开 SVG 时也结束框选

      // 清理函数
      return () => {
        svg.on('mousedown', null);
        svg.on('mousemove', null);
        svg.on('mouseup', null);
        svg.on('mouseleave', null);
      };
    }

    // 渲染构件（只渲染视口内的）
    if (viewportFilteredElements.length > 0) {
      const elements = viewportFilteredElements;
      elements.forEach((element) => {
        const elementDetail = elementDetailsMap.get(element.id);
        const isSelected = selectedElementIds.includes(element.id);
        const isColliding = collidingElementIds.includes(element.id);
        if (elementDetail?.geometry_2d) {
          // 使用实际几何数据渲染
          renderElement(
            g,
            elementDetail,
            isSelected,
            isColliding,
            mode,
            liftMode,
            onElementDragStart,
            onElementClick,
            onElementDrag,
            onElementDragEnd,
            elementsData?.items || [],
            elementDetailsMap,
            setSnapLine,
            traceMode.snapEnabled ? SNAP_DISTANCE : 0, // 如果磁吸被禁用，设置距离为0
            viewTransform,
            setIsDraggingElement,
            setDraggedElementIds,
            isDraggingElementRef,
            setDragPosition
          );
        } else {
          // 如果还没有加载详情，使用占位渲染
          renderElementPlaceholder(g, element, isSelected, isColliding, mode, liftMode, onElementDragStart, onElementClick, setDraggedElementIds, setDragPosition);
        }
      });
      
      // 渲染MEP路径规划路径（如果存在）
      if (routingPath && routingPath.length >= 2) {
        const pathGroup = g.append('g').attr('class', 'routing-path-group');
        
        // 创建路径数据（转换为屏幕坐标）
        const pathData = routingPath.map((pt) => [
          pt.x * viewTransform.scale + viewTransform.x,
          pt.y * viewTransform.scale + viewTransform.y,
        ] as [number, number]);
        
        // 使用D3的line生成器创建路径
        const lineGenerator = d3.line()
          .x((d: [number, number]) => d[0])
          .y((d: [number, number]) => d[1]);
        
        // 渲染路径线
        pathGroup
          .append('path')
          .attr('d', lineGenerator(pathData))
          .attr('fill', 'none')
          .attr('stroke', '#3B82F6') // blue-500
          .attr('stroke-width', 2)
          .attr('stroke-dasharray', '5,5')
          .attr('pointer-events', 'none');
        
        // 渲染路径点（小圆点）
        pathGroup
          .selectAll('circle.routing-point')
          .data(pathData)
          .enter()
          .append('circle')
          .attr('class', 'routing-point')
          .attr('cx', (d: [number, number]) => d[0])
          .attr('cy', (d: [number, number]) => d[1])
          .attr('r', 3)
          .attr('fill', '#3B82F6') // blue-500
          .attr('stroke', '#FFFFFF')
          .attr('stroke-width', 1)
          .attr('pointer-events', 'none');
        
        // 标记起点和终点
        if (pathData.length > 0) {
          // 起点（绿色）
          pathGroup
            .append('circle')
            .attr('class', 'routing-start-point')
            .attr('cx', pathData[0][0])
            .attr('cy', pathData[0][1])
            .attr('r', 5)
            .attr('fill', '#10B981') // green-500
            .attr('stroke', '#FFFFFF')
            .attr('stroke-width', 2)
            .attr('pointer-events', 'none');
          
          // 终点（红色）
          const lastPoint = pathData[pathData.length - 1];
          pathGroup
            .append('circle')
            .attr('class', 'routing-end-point')
            .attr('cx', lastPoint[0])
            .attr('cy', lastPoint[1])
            .attr('r', 5)
            .attr('fill', '#EF4444') // red-500
            .attr('stroke', '#FFFFFF')
            .attr('stroke-width', 2)
            .attr('pointer-events', 'none');
        }
      }
      
      // 渲染磁吸辅助线和磁吸点（改进：更明显的视觉反馈）
      if (snapLine) {
        const snapLineGroup = g.append('g').attr('class', 'snap-line');
        
        // 磁吸辅助线（更粗、更明显）
        snapLineGroup
          .append('line')
          .attr('x1', snapLine.from.x)
          .attr('y1', snapLine.from.y)
          .attr('x2', snapLine.to.x)
          .attr('y2', snapLine.to.y)
          .attr('stroke', '#EA580C') // 橙色（与选中颜色一致）
          .attr('stroke-width', 2) // 增加线宽，从1改为2
          .attr('stroke-dasharray', '4,2') // 调整虚线样式
          .attr('opacity', 0.8) // 提高不透明度，从0.6改为0.8
          .attr('stroke-linecap', 'round');
        
        // 磁吸起点（小圆点）
        snapLineGroup
          .append('circle')
          .attr('cx', snapLine.from.x)
          .attr('cy', snapLine.from.y)
          .attr('r', 3)
          .attr('fill', '#EA580C')
          .attr('opacity', 0.8);
        
        // 磁吸终点（较大圆点，高亮显示）
        snapLineGroup
          .append('circle')
          .attr('cx', snapLine.to.x)
          .attr('cy', snapLine.to.y)
          .attr('r', 5) // 较大的圆点
          .attr('fill', '#EA580C')
          .attr('opacity', 1)
          .attr('stroke', '#FFFFFF') // 白色边框，提高对比度
          .attr('stroke-width', 1.5);
      }

      // 渲染选择框
      if (selectionBox) {
        const selectionGroup = g.append('g').attr('class', 'selection-box');
        selectionGroup
          .append('rect')
          .attr('x', selectionBox.x)
          .attr('y', selectionBox.y)
          .attr('width', selectionBox.width)
          .attr('height', selectionBox.height)
          .attr('fill', 'rgba(59, 130, 246, 0.1)') // blue-500 with opacity
          .attr('stroke', '#3B82F6') // blue-500
          .attr('stroke-width', 1)
          .attr('stroke-dasharray', '4,4')
          .attr('pointer-events', 'none');
      }
    }
  }, [svgRef, viewportFilteredElements, elementDetailsMap, width, height, viewTransform, selectedElementIds, mode, liftMode, setViewTransform, onElementDragStart, onElementClick, onElementDrag, onElementDragEnd, snapLine, selectionBox, isSelecting, elementsData, onSelectionChange, onSelectionAdd, onSelectionClear, SNAP_DISTANCE, routingPath]);

  return (
    <svg
      ref={svgRef}
      className="absolute inset-0 w-full h-full z-10"
      style={{ cursor: 'grab' }}
    />
  );
}

/**
 * 渲染实际几何形状
 */
function renderElement(
  g: Selection<SVGGElement, unknown, null, undefined>,
  element: ElementDetail,
  isSelected: boolean,
  isColliding: boolean,
  mode: WorkbenchMode,
  liftMode: { showZMissing: boolean },
  onElementDragStart?: (elementIds: string[]) => void,
  onElementClick?: (elementId: string, event: MouseEvent) => void,
  onElementDrag?: (elementId: string, newCoordinates: number[][]) => void,
  onElementDragEnd?: (elementId: string, finalCoordinates: number[][], originalType?: string, originalClosed?: boolean) => void,
  allElements?: ElementListItem[],
  elementDetailsMap?: Map<string, ElementDetail>,
  setSnapLine?: (line: { from: { x: number; y: number }; to: { x: number; y: number } } | null) => void,
  snapDistance: number = 10,
  currentViewTransform?: { x: number; y: number; scale: number },
  setIsDraggingElement?: (isDragging: boolean) => void,
  setDraggedElementIds?: (ids: string[] | null) => void,
  isDraggingElementRef?: React.MutableRefObject<boolean>,
  setDragPosition?: (position: { x: number; y: number } | null) => void
) {
  const { geometry_2d } = element;
  if (!geometry_2d || !geometry_2d.coordinates || geometry_2d.coordinates.length < 2) {
    return;
  }

  // 确定颜色和样式（碰撞检测优先级最高）
  const color = isColliding
    ? '#DC2626' // Colliding: red-600
    : mode === 'lift' && liftMode.showZMissing && !element.height
    ? '#9333EA' // Z-Missing: violet-600
    : isSelected
    ? '#EA580C' // Selected: orange-600
    : element.status === 'Verified'
    ? '#059669' // Verified: emerald-600
    : '#3F3F46'; // Default: zinc-700

  const strokeWidth = isSelected ? 2 : 1;
  const strokeDasharray =
    mode === 'lift' && liftMode.showZMissing && !element.height ? '4,4' : undefined;

  // 创建路径数据（使用本地副本以便拖拽时修改）
  let coordinates = geometry_2d.coordinates.map((coord) => [coord[0] || 0, coord[1] || 0] as [number, number]);
  const originalCoordinates = [...coordinates];

  // 创建元素组
  const elementGroup = g.append('g')
    .attr('data-element-id', element.id)
    .style('cursor', (mode === 'trace' || mode === 'classify') && isSelected ? 'grab' : 'pointer');

  // 添加点击事件
  if (onElementClick) {
    elementGroup.on('click', function (this: SVGGElement, event: MouseEvent) {
      event.stopPropagation();
      onElementClick(element.id, event);
    });
  }

    // Trace Mode 下的拖拽和磁吸
    if (mode === 'trace' && isSelected && onElementDrag && onElementDragEnd) {
      // 在 mousedown 时标记正在拖拽，防止框选逻辑触发
      elementGroup.on('mousedown', function (this: SVGGElement, event: MouseEvent) {
        event.stopPropagation();
        setIsDraggingElement?.(true);
      });
    // 收集所有其他构件的端点用于磁吸检测（带元素信息）
    const getAllSnapPointsWithElement = (): SnapPointElement[] => {
      const snapPoints: SnapPointElement[] = [];
      if (allElements && elementDetailsMap) {
        allElements.forEach((el) => {
          if (el.id !== element.id) {
            const detail = elementDetailsMap.get(el.id);
            if (detail?.geometry_2d?.coordinates) {
              const endpoints = getGeometryEndpoints(detail.geometry_2d.coordinates);
              endpoints.forEach(endpoint => {
                snapPoints.push({
                  x: endpoint.x,
                  y: endpoint.y,
                  elementId: el.id,
                  element: detail ? {
                    ...detail, // 包含所有属性
                  } : undefined,
                });
              });
            }
          }
        });
      }
      return snapPoints;
    };
    
    // 收集所有其他构件的磁吸点（端点、中点、交点）
    const getAllSnapPoints = (): { x: number; y: number }[] => {
      const snapPointsWithElement = getAllSnapPointsWithElement();
      const endpointPoints = snapPointsWithElement.map(sp => ({ x: sp.x, y: sp.y }));
      
      // 添加中点（如果启用）
      const midpoints: { x: number; y: number }[] = [];
      if (allElements && elementDetailsMap) {
        allElements.forEach((el) => {
          if (el.id !== element.id) {
            const detail = elementDetailsMap.get(el.id);
            if (detail?.geometry_2d?.coordinates && detail.geometry_2d.coordinates.length >= 2) {
              const elementMidpoints = getGeometryMidpoints(detail.geometry_2d.coordinates);
              midpoints.push(...elementMidpoints);
            }
          }
        });
      }
      
      // 添加交点（如果启用，但为了性能，限制计算数量）
      const intersections: { x: number; y: number }[] = [];
      if (allElements && elementDetailsMap && coordinates.length >= 2) {
        // 只计算与当前几何的交点（限制其他几何数量以提高性能）
        const otherGeometries = allElements
          .filter(el => el.id !== element.id)
          .slice(0, 20) // 限制最多20个其他几何，避免性能问题
          .map(el => {
            const detail = elementDetailsMap.get(el.id);
            return detail?.geometry_2d?.coordinates ? { coordinates: detail.geometry_2d.coordinates } : null;
          })
          .filter((g): g is { coordinates: number[][] } => g !== null);
        
        if (otherGeometries.length > 0) {
          const elementIntersections = getGeometryIntersections(coordinates, otherGeometries);
          intersections.push(...elementIntersections);
        }
      }
      
      // 合并所有磁吸点（端点、中点、交点）
      return [...endpointPoints, ...midpoints, ...intersections];
    };

    // D3 拖拽行为
    const drag = (d3.drag as any)() as any;
    drag
      .on('start', function (this: SVGGElement) {
        d3.select(this).style('cursor', 'grabbing');
        coordinates = [...originalCoordinates]; // 重置为原始坐标
        if (isDraggingElementRef) isDraggingElementRef.current = true;
        setIsDraggingElement?.(true);
      })
      .on('end', function (this: SVGGElement) {
        setIsDraggingElement?.(false);
        if (isDraggingElementRef) isDraggingElementRef.current = false;
      })
      .on('drag', function (this: SVGGElement, event: { dx: number; dy: number }) {
        // 计算拖拽偏移量（需要考虑缩放）
        const scale = currentViewTransform?.scale || 1;
        const dx = event.dx / scale;
        const dy = event.dy / scale;

        // 移动所有坐标点
        const newCoordinates = coordinates.map((coord): [number, number] => [
          (coord[0] || 0) + dx,
          (coord[1] || 0) + dy,
        ]);

        // 磁吸检测：检测第一个和最后一个点（仅在启用磁吸时）
        // 磁吸开关通过snapDistance参数控制：如果snapDistance为0，则磁吸被禁用
        let adjustedCoordinates: [number, number][] = [...newCoordinates];
        let snapLineData: { from: { x: number; y: number }; to: { x: number; y: number } } | null = null;

        // 检查磁吸是否启用（通过snapDistance > 0判断）
        if (snapDistance > 0) {
          const snapPoints = getAllSnapPoints();
          const firstPoint = { x: newCoordinates[0][0] || 0, y: newCoordinates[0][1] || 0 };
          const lastPoint = {
            x: newCoordinates[newCoordinates.length - 1][0] || 0,
            y: newCoordinates[newCoordinates.length - 1][1] || 0,
          };

          // 检测第一个点的磁吸
          const snapToFirst = findNearestSnapPoint(firstPoint, snapPoints, snapDistance);
          if (snapToFirst) {
            adjustedCoordinates[0] = [snapToFirst.x, snapToFirst.y];
            snapLineData = { from: firstPoint, to: snapToFirst };
          }

          // 检测最后一个点的磁吸
          const snapToLast = findNearestSnapPoint(lastPoint, snapPoints, snapDistance);
          if (snapToLast) {
            adjustedCoordinates[adjustedCoordinates.length - 1] = [snapToLast.x, snapToLast.y];
            if (!snapLineData) {
              snapLineData = { from: lastPoint, to: snapToLast };
            }
          }
        }

        // 更新坐标
        coordinates = adjustedCoordinates;
        if (setSnapLine) {
          setSnapLine(snapLineData);
        }

        // 更新渲染（直接更新，D3 会优化渲染）
        updateElementVisual(elementGroup, adjustedCoordinates, geometry_2d.type, geometry_2d.closed, color, strokeWidth, strokeDasharray);

        // 通知拖拽事件（可选，用于实时反馈）
        // 注意：为了性能，这里不频繁调用，只在必要时调用
        // if (onElementDrag) {
        //   onElementDrag(element.id, adjustedCoordinates);
        // }
      })
      .on('end', function (this: SVGGElement) {
        d3.select(this).style('cursor', 'grab');
        if (setSnapLine) {
          setSnapLine(null);
        }
        
        // 通知拖拽结束事件（传递原始几何类型信息）
        if (onElementDragEnd) {
          onElementDragEnd(element.id, coordinates, geometry_2d.type, geometry_2d.closed);
        }
        
        // 重置坐标（实际更新应该在 onElementDragEnd 中处理）
        coordinates = [...originalCoordinates];
      });

    elementGroup.call(drag);
  }

  // 渲染元素的辅助函数
  function updateElementVisual(
    group: Selection<SVGGElement, unknown, null, undefined>,
    coords: [number, number][],
    geomType: string,
    closed: boolean | undefined,
    elemColor: string,
    elemStrokeWidth: number,
    elemStrokeDasharray: string | undefined
  ) {
    // 清除旧的几何元素
    group.selectAll('line, path').remove();

    if (geomType === 'Line' && coords.length === 2) {
      // 渲染直线
      group
        .append('line')
        .attr('x1', coords[0][0])
        .attr('y1', coords[0][1])
        .attr('x2', coords[1][0])
        .attr('y2', coords[1][1])
        .attr('stroke', elemColor)
        .attr('stroke-width', elemStrokeWidth)
        .attr('stroke-dasharray', elemStrokeDasharray || null);
    } else if (geomType === 'Polyline') {
      // 使用 D3 line 生成器创建路径
      const lineGenerator = (d3.line as any)()
        .x((d: [number, number]) => d[0])
        .y((d: [number, number]) => d[1]);

      // 如果是闭合的 Polyline，添加起始点
      const pathData = closed && coords.length > 0
        ? [...coords, coords[0]]
        : coords;

      group
        .append('path')
        .attr('d', lineGenerator(pathData) || '')
        .attr('fill', 'none')
        .attr('stroke', elemColor)
        .attr('stroke-width', elemStrokeWidth)
        .attr('stroke-dasharray', elemStrokeDasharray || null)
        .attr('stroke-linejoin', 'round')
        .attr('stroke-linecap', 'round');
    }
  }

  // 初始渲染
  updateElementVisual(elementGroup, coordinates, geometry_2d.type, geometry_2d.closed, color, strokeWidth, strokeDasharray);

  // 添加标题
  elementGroup.append('title').text(`${element.id} (${element.speckle_type})`);

  // 为 Classify 模式添加拖拽支持（使用鼠标事件，因为 SVG 不支持 HTML5 drag）
  if (mode === 'classify' && isSelected && onElementDragStart) {
    elementGroup
      .on('mousedown', function (this: SVGGElement, event: MouseEvent) {
        event.stopPropagation();
        onElementDragStart([element.id]);
        // 存储拖拽数据到Context（供 HierarchyTreeNode 使用）
        setDraggedElementIds?.([element.id]);
        // 设置拖拽起始位置
        setDragPosition?.({ x: event.clientX, y: event.clientY });
        // 添加拖拽视觉反馈：降低透明度和添加拖拽样式
        const group = d3.select(this);
        group.style('opacity', '0.6');
        group.style('cursor', 'grabbing');
        group.style('filter', 'drop-shadow(0 4px 6px rgba(0, 0, 0, 0.3))');
      })
      .on('mouseup', function (this: SVGGElement) {
        // 恢复透明度和样式
        const group = d3.select(this);
        group.style('opacity', '1');
        group.style('cursor', 'grab');
        group.style('filter', null);
        // 清除拖拽位置（延迟清除，让drop事件先处理）
        setTimeout(() => {
          setDragPosition?.(null);
        }, 100);
      });
  }
}

/**
 * 占位渲染（当几何数据还未加载时）
 */
function renderElementPlaceholder(
  g: Selection<SVGGElement, unknown, null, undefined>,
  element: ElementListItem,
  isSelected: boolean,
  mode: WorkbenchMode,
  liftMode: { showZMissing: boolean },
  onElementDragStart?: (elementIds: string[]) => void,
  onElementClick?: (elementId: string, event: MouseEvent) => void,
  setDraggedElementIds?: (ids: string[] | null) => void,
  setDragPosition?: (position: { x: number; y: number } | null) => void
) {
  // 占位渲染：简单的矩形
  // 使用 element.id 作为种子生成固定位置，避免每次渲染位置变化
  const seed = element.id.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
  const x = (seed % 400) + 50;
  const y = ((seed * 7) % 400) + 50;

  const color = isColliding
    ? '#DC2626' // Colliding: red-600
    : mode === 'lift' && liftMode.showZMissing && !element.has_height
    ? '#9333EA' // Z-Missing: violet-600
    : isSelected
    ? '#EA580C' // Selected: orange-600
    : element.status === 'Verified'
    ? '#059669' // Verified: emerald-600
    : '#3F3F46'; // Default: zinc-700

  const strokeDasharray =
    mode === 'lift' && liftMode.showZMissing && !element.has_height ? '4,4' : undefined;

  // 创建元素组
  const elementGroup = g.append('g')
    .attr('data-element-id', element.id)
    .style('cursor', mode === 'classify' && isSelected ? 'grab' : 'pointer');

  // 添加点击事件
  if (onElementClick) {
    elementGroup.on('click', function (this: SVGGElement, event: MouseEvent) {
      event.stopPropagation();
      onElementClick(element.id, event);
    });
  }

  // 为 Classify 模式添加拖拽支持（使用鼠标事件）
  if (mode === 'classify' && isSelected && onElementDragStart) {
    elementGroup
      .on('mousedown', function (this: SVGGElement, event: MouseEvent) {
        event.stopPropagation();
        onElementDragStart([element.id]);
        // 存储拖拽数据到Context（供 HierarchyTreeNode 使用）
        setDraggedElementIds?.([element.id]);
        // 设置拖拽起始位置
        setDragPosition?.({ x: event.clientX, y: event.clientY });
        // 添加拖拽视觉反馈：降低透明度和添加拖拽样式
        const group = d3.select(this);
        group.style('opacity', '0.6');
        group.style('cursor', 'grabbing');
        group.style('filter', 'drop-shadow(0 4px 6px rgba(0, 0, 0, 0.3))');
      })
      .on('mouseup', function (this: SVGGElement) {
        // 恢复透明度和样式
        const group = d3.select(this);
        group.style('opacity', '1');
        group.style('cursor', 'grab');
        group.style('filter', null);
        // 清除拖拽位置
        setDragPosition?.(null);
      })
      .on('mouseleave', function (this: SVGGElement) {
        // 如果鼠标离开时还在拖拽，保持半透明
        // 透明度将在drop或mouseup时恢复
      });
  }

  // 占位矩形（改进：添加加载指示和动画效果）
  const placeholderRect = elementGroup.append('rect')
    .attr('x', x)
    .attr('y', y)
    .attr('width', 100)
    .attr('height', 50)
    .attr('fill', 'none')
    .attr('stroke', color)
    .attr('stroke-width', isSelected ? 2 : 1)
    .attr('stroke-dasharray', strokeDasharray || '5,5')
    .attr('opacity', 0.4) // 降低占位元素的不透明度，表明这是占位符
    .attr('rx', 4) // 圆角，更现代的外观
    .attr('ry', 4);

  // 添加加载指示动画（脉动效果）
  const loadingIndicator = elementGroup.append('circle')
    .attr('cx', x + 50)
    .attr('cy', y + 25)
    .attr('r', 4)
    .attr('fill', color)
    .attr('opacity', 0.6);

  // 简单的脉动动画
  const animateLoading = () => {
    (loadingIndicator as any)
      .transition()
      .duration(800)
      .attr('r', 6)
      .attr('opacity', 0.3)
      .transition()
      .duration(800)
      .attr('r', 4)
      .attr('opacity', 0.6)
      .on('end', animateLoading);
  };
  animateLoading();

  // 添加加载指示文本（可选，减少视觉噪音）
  // elementGroup.append('text')
  //   .attr('x', x + 50)
  //   .attr('y', y + 40)
  //   .attr('text-anchor', 'middle')
  //   .attr('font-size', '9px')
  //   .attr('fill', color)
  //   .attr('opacity', 0.5)
  //   .text('Loading...');

  // 添加标题提示
  elementGroup.append('title')
    .text(`${element.id} (${element.speckle_type}) - Loading geometry...`);
}

