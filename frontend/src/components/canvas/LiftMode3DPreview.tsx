/** Lift Mode 3D 预览组件
 * 
 * 使用 CSS 3D transforms 实现简单的 3D 预览功能
 */

'use client';

import { useMemo, useState, useEffect } from 'react';
import { ElementDetail } from '@/services/elements';
import { geometry2dTo3d, isometricProjection, calculateProjectedBoundingBox, Point3D } from '@/utils/geometry3d';
import { cn } from '@/lib/utils';

interface LiftMode3DPreviewProps {
  elements: ElementDetail[];
  height?: number;
  baseOffset?: number;
  onClose?: () => void;
}

export function LiftMode3DPreview({
  elements,
  height = 3.0, // 默认高度 3 米
  baseOffset = 0,
  onClose,
}: LiftMode3DPreviewProps) {
  const [rotationX, setRotationX] = useState(-30); // 初始旋转角度
  const [rotationY, setRotationY] = useState(30);
  const [scale, setScale] = useState(1);

  // 将所有元素的 2D 几何转换为 3D 坐标
  const elements3d = useMemo(() => {
    return elements.map((element) => {
      const points3d = geometry2dTo3d(
        element.geometry,
        element.base_offset ?? baseOffset,
        element.height ?? height
      );
      return {
        element,
        points3d,
      };
    });
  }, [elements, baseOffset, height]);

  // 计算所有元素的边界框（用于居中显示）
  const allPoints3d = useMemo(() => {
    return elements3d.flatMap(({ points3d }) => points3d);
  }, [elements3d]);

  const boundingBox = useMemo(() => {
    // 计算投影后的边界框（不使用 scale，因为 scale 会通过 CSS transform 应用）
    return calculateProjectedBoundingBox(allPoints3d, 1);
  }, [allPoints3d]);

  // 处理鼠标拖拽旋转
  const [isDragging, setIsDragging] = useState(false);
  const [lastMousePos, setLastMousePos] = useState<{ x: number; y: number } | null>(null);

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setLastMousePos({ x: e.clientX, y: e.clientY });
  };

  useEffect(() => {
    if (!isDragging) return;

    const handleMouseMove = (e: MouseEvent) => {
      if (!lastMousePos) return;

      const deltaX = e.clientX - lastMousePos.x;
      const deltaY = e.clientY - lastMousePos.y;

      setRotationY((prev) => prev + deltaX * 0.5);
      setRotationX((prev) => Math.max(-90, Math.min(90, prev - deltaY * 0.5)));

      setLastMousePos({ x: e.clientX, y: e.clientY });
    };

    const handleMouseUp = () => {
      setIsDragging(false);
      setLastMousePos(null);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, lastMousePos]);

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    setScale((prev) => Math.max(0.1, Math.min(5, prev * delta)));
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-[90vw] h-[90vh] max-w-6xl max-h-[800px] flex flex-col">
        {/* 头部 */}
        <div className="flex items-center justify-between p-4 border-b border-zinc-200">
          <div>
            <h3 className="text-lg font-semibold text-zinc-900">3D 预览</h3>
            <p className="text-xs text-zinc-500 mt-1">
              {elements.length} 个构件 · 高度: {height}m · 基础偏移: {baseOffset}m
            </p>
          </div>
          <div className="flex items-center gap-2">
            <div className="text-xs text-zinc-500">
              拖拽旋转 · 滚轮缩放
            </div>
            {onClose && (
              <button
                onClick={onClose}
                className="text-zinc-400 hover:text-zinc-600 text-2xl leading-none"
                aria-label="关闭"
              >
                ×
              </button>
            )}
          </div>
        </div>

        {/* 3D 预览区域 */}
        <div
          className="flex-1 relative overflow-hidden bg-zinc-100"
          onMouseDown={handleMouseDown}
          onWheel={handleWheel}
          style={{ cursor: isDragging ? 'grabbing' : 'grab' }}
        >
          <div
            style={{
              transform: `perspective(1000px) rotateX(${rotationX}deg) rotateY(${rotationY}deg) scale(${scale})`,
              transformStyle: 'preserve-3d',
              width: '100%',
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <svg
              width="100%"
              height="100%"
              viewBox={
                boundingBox.width > 0 && boundingBox.height > 0
                  ? `${boundingBox.minX - 50} ${boundingBox.minY - 50} ${boundingBox.width + 100} ${boundingBox.height + 100}`
                  : "0 0 100 100"
              }
              preserveAspectRatio="xMidYMid meet"
            >
            <g>
              {/* 渲染每个元素 */}
              {elements3d.map(({ element, points3d }, elementIndex) => {
                // 将 3D 点投影到 2D
                const projectedPoints = points3d.map((p) => isometricProjection(p, 1));
                const pathData = projectedPoints
                  .map((p, i) => (i === 0 ? `M ${p.x} ${p.y}` : `L ${p.x} ${p.y}`))
                  .join(' ');

                // 如果几何图形是闭合的，添加 Z
                const isClosed = element.geometry.closed;
                const finalPathData = isClosed ? `${pathData} Z` : pathData;

                return (
                  <path
                    key={element.id}
                    d={finalPathData}
                    fill="none"
                    stroke={element.status === 'Verified' ? '#10b981' : '#f59e0b'}
                    strokeWidth="2"
                    opacity="0.8"
                  />
                );
              })}

              {/* 渲染 Z 轴指示器（可选） */}
              <line
                x1={0}
                y1={0}
                x2={0}
                y2={-50}
                stroke="#ef4444"
                strokeWidth="2"
                strokeDasharray="5,5"
                opacity="0.5"
              />
            </g>
          </svg>
          </div>
        </div>

        {/* 底部控制栏 */}
        <div className="p-4 border-t border-zinc-200 bg-zinc-50 flex items-center justify-between">
          <div className="flex items-center gap-4 text-xs text-zinc-600">
            <div>
              <span className="font-medium">旋转:</span> X={rotationX.toFixed(0)}° Y={rotationY.toFixed(0)}°
            </div>
            <div>
              <span className="font-medium">缩放:</span> {(scale * 100).toFixed(0)}%
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                setRotationX(-30);
                setRotationY(30);
                setScale(1);
              }}
              className="px-3 py-1.5 text-xs font-medium text-zinc-700 bg-white border border-zinc-300 rounded hover:bg-zinc-50 transition-colors"
            >
              重置视图
            </button>
            {onClose && (
              <button
                onClick={onClose}
                className="px-3 py-1.5 text-xs font-medium text-white bg-zinc-900 rounded hover:bg-zinc-800 transition-colors"
              >
                关闭
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

