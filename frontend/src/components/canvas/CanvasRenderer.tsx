/** Canvas 渲染器组件 */

'use client';

import { useEffect, useRef, useMemo, useState, useCallback } from 'react';
import * as d3 from 'd3';
import { useQuery } from '@tanstack/react-query';
import { getElements, ElementListItem, ElementDetail, getElementDetail, batchGetElementDetails } from '@/services/elements';
import { WorkbenchMode, Geometry2D } from '@/types';
import { useCanvasStore } from '@/stores/canvas';
import { useWorkbenchStore } from '@/stores/workbench';
import { findNearestSnapPoint, getGeometryEndpoints, createRectangle, rectangleIntersectsGeometryPrecise, type SnapPointElement } from '@/utils/topology';
import { calculateViewportBounds, isGeometryInViewport, throttle } from '@/utils/performance';
import { useDrag } from '@/contexts/DragContext';

interface CanvasRendererProps {
  width: number;
  height: number;
  viewTransform: { x: number; y: number; scale: number };
  selectedElementIds: string[];
  mode: WorkbenchMode;
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
  const { setIsDraggingElement, setDraggedElementIds } = useDrag();
  
  // 存储磁吸辅助线的状态
  const [snapLine, setSnapLine] = useState<{ from: { x: number; y: number }; to: { x: number; y: number } } | null>(null);
  
  // 框选状态
  const [selectionBox, setSelectionBox] = useState<{ x: number; y: number; width: number; height: number } | null>(null);
  const [isSelecting, setIsSelecting] = useState(false);
  const selectionStartRef = useRef<{ x: number; y: number } | null>(null);
  const isDraggingElementRef = useRef(false);
  
  // 磁吸距离阈值（根据缩放动态调整，基准值为10像素）
  const SNAP_DISTANCE = Math.max(5, Math.min(20, 10 / (viewTransform.scale || 1)));

  // 获取构件列表（使用分页，避免一次性加载过多）
  const { data: elementsData } = useQuery({
    queryKey: ['elements', 'canvas'],
    queryFn: () => getElements({ page: 1, page_size: 500 }), // 减少初始加载数量
  });

  // 计算视口边界（用于视口剔除）
  const viewportBounds = useMemo(() => {
    return calculateViewportBounds(width, height, viewTransform);
  }, [width, height, viewTransform]);

  // 筛选视口内的构件（视口剔除）- 优化：优先加载视口附近的构件
  const visibleElementIds = useMemo(() => {
    if (!elementsData?.items || elementsData.items.length === 0) return [];
    
    // 如果构件数量较少，直接返回所有ID
    if (elementsData.items.length <= 500) {
      return elementsData.items.map((el) => el.id);
    }
    
    // 如果构件数量较多，优先返回前500个（后续会在视口过滤中进一步筛选）
    // 这样可以在保持性能的同时，确保视口内的构件能被正确加载
    return elementsData.items.slice(0, 500).map((el) => el.id);
  }, [elementsData]);
  
  // 使用去重后的ID列表（避免重复请求）
  const uniqueVisibleElementIds = useMemo(() => {
    return Array.from(new Set(visibleElementIds));
  }, [visibleElementIds]);

  const elementDetailsQueries = useQuery({
    queryKey: ['element-details', uniqueVisibleElementIds],
    queryFn: async () => {
      // 批量获取，但限制并发数量（优化：增加批次大小以提高效率）
      const BATCH_SIZE = 30; // 从20增加到30，提高批量获取效率
      const detailsMap = new Map<string, ElementDetail>();
      
      // 并行处理多个批次（但限制总并发数）
      const MAX_CONCURRENT_BATCHES = 3;
      const batches: string[][] = [];
      for (let i = 0; i < uniqueVisibleElementIds.length; i += BATCH_SIZE) {
        batches.push(uniqueVisibleElementIds.slice(i, i + BATCH_SIZE));
      }
      
      // 分批并行处理
      for (let i = 0; i < batches.length; i += MAX_CONCURRENT_BATCHES) {
        const concurrentBatches = batches.slice(i, i + MAX_CONCURRENT_BATCHES);
        const batchResults = await Promise.all(
          concurrentBatches.map(async (batch) => {
            const batchDetails = await Promise.all(
              batch.map((id) =>
                getElementDetail(id).catch((error) => {
                  console.error(`Failed to fetch element ${id}:`, error);
                  return null;
                })
              )
            );
            return batchDetails.filter((detail): detail is ElementDetail => detail !== null);
          })
        );
        
        // 合并结果
        batchResults.flat().forEach((detail) => {
          detailsMap.set(detail.id, detail);
        });
      }
      
      return detailsMap;
    },
    enabled: uniqueVisibleElementIds.length > 0,
    staleTime: 30000, // 30秒内使用缓存，避免频繁重新获取
  });

  const elementDetailsMap = elementDetailsQueries.data || new Map<string, ElementDetail>();

  // 进一步筛选视口内的构件（基于实际几何数据）
  const viewportFilteredElements = useMemo(() => {
    if (!elementsData?.items) return [];
    
    return elementsData.items.filter((element) => {
      const detail = elementDetailsMap.get(element.id);
      if (!detail?.geometry_2d?.coordinates) {
        // 如果没有几何数据，默认显示（占位渲染）
        return true;
      }
      // 检查几何是否在视口内
      return isGeometryInViewport(detail.geometry_2d.coordinates, viewportBounds, 200);
    });
  }, [elementsData, elementDetailsMap, viewportBounds]);

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
    const throttledZoomUpdate = throttle((transform: d3.ZoomTransform) => {
      const { x, y, k } = transform;
      setViewTransform({ x, y, scale: k });
      g.attr('transform', transform.toString());
    }, 16); // 约60fps

    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 10])
      .on('zoom', (event) => {
        throttledZoomUpdate(event.transform);
      });

    // D3 zoom 类型处理：使用类型断言确保类型安全
    // 注意：D3的类型定义在某些情况下需要类型断言
    (svg as unknown as d3.Selection<SVGSVGElement, unknown, null, undefined>).call(zoom);
    (svg as unknown as d3.Selection<SVGSVGElement, unknown, null, undefined>).call(zoom.transform, initialTransform);

    // 框选逻辑（仅在 trace 或 lift 模式下启用）
    if ((mode === 'trace' || mode === 'lift') && onSelectionChange) {
      const handleMouseDown = (event: MouseEvent) => {
        // 检查拖拽状态，如果正在拖拽构件，不执行框选
        if (isDraggingElementRef.current) {
          isDraggingElementRef.current = false;
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
          isDraggingElementRef.current = false;
          
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
        if (isDraggingElementRef.current) {
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
        if (isDraggingElementRef.current) {
          isDraggingElementRef.current = false;
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
        if (elementDetail?.geometry_2d) {
          // 使用实际几何数据渲染
          renderElement(
            g,
            elementDetail,
            isSelected,
            mode,
            liftMode,
            onElementDragStart,
            onElementClick,
            onElementDrag,
            onElementDragEnd,
            elementsData?.items || [],
            elementDetailsMap,
            setSnapLine,
            SNAP_DISTANCE,
            viewTransform
          );
        } else {
          // 如果还没有加载详情，使用占位渲染
          renderElementPlaceholder(g, element, isSelected, mode, liftMode, onElementDragStart, onElementClick);
        }
      });
      
      // 渲染磁吸辅助线
      if (snapLine) {
        const snapLineGroup = g.append('g').attr('class', 'snap-line');
        snapLineGroup
          .append('line')
          .attr('x1', snapLine.from.x)
          .attr('y1', snapLine.from.y)
          .attr('x2', snapLine.to.x)
          .attr('y2', snapLine.to.y)
          .attr('stroke', '#EA580C')
          .attr('stroke-width', 1)
          .attr('stroke-dasharray', '2,2')
          .attr('opacity', 0.6);
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
  }, [svgRef, viewportFilteredElements, elementDetailsMap, width, height, viewTransform, selectedElementIds, mode, liftMode, setViewTransform, onElementDragStart, onElementClick, onElementDrag, onElementDragEnd, snapLine, selectionBox, isSelecting, elementsData, onSelectionChange, onSelectionAdd, onSelectionClear, SNAP_DISTANCE]);

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
  g: d3.Selection<SVGGElement, unknown, null, undefined>,
  element: ElementDetail,
  isSelected: boolean,
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
  currentViewTransform?: { x: number; y: number; scale: number }
) {
  const { geometry_2d } = element;
  if (!geometry_2d || !geometry_2d.coordinates || geometry_2d.coordinates.length < 2) {
    return;
  }

  // 确定颜色和样式
  const color =
    mode === 'lift' && liftMode.showZMissing && !element.height
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
    elementGroup.on('click', function (event: MouseEvent) {
      event.stopPropagation();
      onElementClick(element.id, event);
    });
  }

    // Trace Mode 下的拖拽和磁吸
    if (mode === 'trace' && isSelected && onElementDrag && onElementDragEnd) {
      // 在 mousedown 时标记正在拖拽，防止框选逻辑触发
      elementGroup.on('mousedown', function (event: MouseEvent) {
        event.stopPropagation();
        setIsDraggingElement(true);
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
                    id: detail.id,
                    speckle_type: detail.speckle_type,
                    geometry_2d: detail.geometry_2d,
                    ...detail, // 包含其他属性
                  } : undefined,
                });
              });
            }
          }
        });
      }
      return snapPoints;
    };
    
    // 收集所有其他构件的端点用于磁吸检测（向后兼容）
    const getAllSnapPoints = (): { x: number; y: number }[] => {
      const snapPointsWithElement = getAllSnapPointsWithElement();
      return snapPointsWithElement.map(sp => ({ x: sp.x, y: sp.y }));
    };

    // D3 拖拽行为
    const drag = d3
      .drag<SVGGElement, unknown>()
      .on('start', function () {
        d3.select(this).style('cursor', 'grabbing');
        coordinates = [...originalCoordinates]; // 重置为原始坐标
        isDraggingElementRef.current = true;
        setIsDraggingElement(true);
      })
      .on('end', function () {
        setIsDraggingElement(false);
        isDraggingElementRef.current = false;
      })
      .on('drag', function (event) {
        // 计算拖拽偏移量（需要考虑缩放）
        const scale = currentViewTransform?.scale || 1;
        const dx = event.dx / scale;
        const dy = event.dy / scale;

        // 移动所有坐标点
        const newCoordinates = coordinates.map((coord): [number, number] => [
          (coord[0] || 0) + dx,
          (coord[1] || 0) + dy,
        ]);

        // 磁吸检测：检测第一个和最后一个点
        const snapPoints = getAllSnapPoints();
        const firstPoint = { x: newCoordinates[0][0] || 0, y: newCoordinates[0][1] || 0 };
        const lastPoint = {
          x: newCoordinates[newCoordinates.length - 1][0] || 0,
          y: newCoordinates[newCoordinates.length - 1][1] || 0,
        };

        let adjustedCoordinates: [number, number][] = [...newCoordinates];
        let snapLineData: { from: { x: number; y: number }; to: { x: number; y: number } } | null = null;

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
      .on('end', function () {
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
    group: d3.Selection<SVGGElement, unknown, null, undefined>,
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
      const lineGenerator = d3
        .line<[number, number]>()
        .x((d) => d[0])
        .y((d) => d[1]);

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
    let dragStartX = 0;
    let dragStartY = 0;
    elementGroup
      .on('mousedown', function (event: MouseEvent) {
        dragStartX = event.clientX;
        dragStartY = event.clientY;
        onElementDragStart([element.id]);
        // 存储拖拽数据到Context（供 HierarchyTreeNode 使用）
        setDraggedElementIds([element.id]);
      });
  }
}

/**
 * 占位渲染（当几何数据还未加载时）
 */
function renderElementPlaceholder(
  g: d3.Selection<SVGGElement, unknown, null, undefined>,
  element: ElementListItem,
  isSelected: boolean,
  mode: WorkbenchMode,
  liftMode: { showZMissing: boolean },
  onElementDragStart?: (elementIds: string[]) => void,
  onElementClick?: (elementId: string, event: MouseEvent) => void
) {
  // 占位渲染：简单的矩形
  // 使用 element.id 作为种子生成固定位置，避免每次渲染位置变化
  const seed = element.id.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
  const x = (seed % 400) + 50;
  const y = ((seed * 7) % 400) + 50;

  const color =
    mode === 'lift' && liftMode.showZMissing && !element.has_height
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
    elementGroup.on('click', function (event: MouseEvent) {
      event.stopPropagation();
      onElementClick(element.id, event);
    });
  }

  // 为 Classify 模式添加拖拽支持（使用鼠标事件）
  if (mode === 'classify' && isSelected && onElementDragStart) {
    elementGroup
      .on('mousedown', function (event: MouseEvent) {
        event.stopPropagation();
        onElementDragStart([element.id]);
        // 存储拖拽数据到Context（供 HierarchyTreeNode 使用）
        setDraggedElementIds([element.id]);
        // 添加拖拽视觉反馈：降低透明度
        d3.select(this).style('opacity', '0.6');
      })
      .on('mouseup', function () {
        // 恢复透明度
        d3.select(this).style('opacity', '1');
      })
      .on('mouseleave', function () {
        // 如果鼠标离开时还在拖拽，保持半透明
        // 透明度将在drop时恢复
      });
  }

  // 占位矩形（改进：添加加载指示）
  const placeholderRect = elementGroup.append('rect')
    .attr('x', x)
    .attr('y', y)
    .attr('width', 100)
    .attr('height', 50)
    .attr('fill', 'none')
    .attr('stroke', color)
    .attr('stroke-width', isSelected ? 2 : 1)
    .attr('stroke-dasharray', strokeDasharray || null)
    .attr('opacity', 0.5); // 降低占位元素的不透明度，表明这是占位符

  // 添加加载指示文本
  elementGroup.append('text')
    .attr('x', x + 50)
    .attr('y', y + 30)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', color)
    .attr('opacity', 0.6)
    .text('Loading...');

  // 添加标题提示
  elementGroup.append('title')
    .text(`${element.id} (${element.speckle_type}) - Loading geometry...`);
}

