/** MEP 路径规划面板 */

'use client';

import { useState } from 'react';
import { useMEPRouting } from '@/hooks/useMEPRouting';
import { ElementDetail } from '@/services/elements';
import { completeRoutingPlanning } from '@/services/routing';
import { useToastContext } from '@/providers/ToastProvider';
import { CableTrayCapacityIndicator } from './CableTrayCapacityIndicator';

interface MEPRoutingPanelProps {
  sourceElement: ElementDetail | null;
  targetElement: ElementDetail | null;
  onRouteCalculated?: (path: { x: number; y: number }[], isPreview: boolean) => void;
  onClose?: () => void;
}

export function MEPRoutingPanel({
  sourceElement,
  targetElement,
  onRouteCalculated,
  onClose,
}: MEPRoutingPanelProps) {
  const { routingState, calculateRoute, clearRoute } = useMEPRouting();
  const { showToast } = useToastContext();
  const [elementType, setElementType] = useState<'Pipe' | 'Duct' | 'CableTray' | 'Conduit' | 'Wire'>('Pipe');
  const [systemType, setSystemType] = useState<string>('');
  const [diameter, setDiameter] = useState<number>(100);
  const [width, setWidth] = useState<number>(200);
  const [height, setHeight] = useState<number>(200);
  const [previewPath, setPreviewPath] = useState<{ x: number; y: number }[] | null>(null);
  const [confirmedPath, setConfirmedPath] = useState<{ x: number; y: number }[] | null>(null);
  const [isCompleting, setIsCompleting] = useState(false);
  const [containerTrayId, setContainerTrayId] = useState<string | null>(null);

  const handleCalculate = async () => {
    if (!sourceElement || !targetElement) {
      return;
    }

    // 获取起点和终点（使用几何的中心点或端点）
    const sourceGeometry = sourceElement.geometry;
    const targetGeometry = targetElement.geometry;

    if (!sourceGeometry?.coordinates || !targetGeometry?.coordinates) {
      return;
    }

    // 使用第一个和最后一个点作为起点和终点（简化处理）
    const startPoint = {
      x: sourceGeometry.coordinates[0]?.[0] || 0,
      y: sourceGeometry.coordinates[0]?.[1] || 0,
    };
    
    const lastSourceIndex = sourceGeometry.coordinates.length - 1;
    const endPoint = {
      x: targetGeometry.coordinates[0]?.[0] || 0,
      y: targetGeometry.coordinates[0]?.[1] || 0,
    };

    const constraints = {
      elementType,
      systemType: systemType || undefined,
      properties: elementType === 'CableTray' || elementType === 'Wire'
        ? { width, cable_bend_radius: width }
        : elementType === 'Duct'
        ? { width, height }
        : { diameter },
    };

    try {
      // 获取level_id（从sourceElement或targetElement）
      const levelId = sourceElement?.level_id || targetElement?.level_id;
      // 使用sourceElement的ID作为element_id（如果存在）
      const elementId = sourceElement?.id;

      const result = await calculateRoute(
        startPoint,
        endPoint,
        constraints,
        sourceElement.speckle_type,
        targetElement.speckle_type,
        elementId,
        levelId,
        true, // validate_room_constraints
        true  // validate_slope
      );

      if (result.path_points) {
        // 设置为预览路径（虚线显示）
        setPreviewPath(result.path_points);
        setConfirmedPath(null);
        if (onRouteCalculated) {
          onRouteCalculated(result.path_points, true); // true表示预览
        }
      }

      // 如果是桥架，检查容量（用于容量指示器）
      if (elementType === 'CableTray' && sourceElement?.id) {
        setContainerTrayId(sourceElement.id);
      }
    } catch (error) {
      // 错误已在hook中处理
    }
  };

  const handleConfirm = () => {
    if (previewPath) {
      // 确认预览路径
      setConfirmedPath(previewPath);
      setPreviewPath(null);
      if (onRouteCalculated) {
        onRouteCalculated(previewPath, false); // false表示已确认
      }
      showToast('路径已确认', 'success');
    }
  };

  const handleCancel = () => {
    // 取消预览，保留原始路径
    setPreviewPath(null);
    if (onRouteCalculated && confirmedPath) {
      onRouteCalculated(confirmedPath, false);
    } else if (onRouteCalculated) {
      onRouteCalculated([], false);
    }
  };

  const handleClear = () => {
    clearRoute();
    setPreviewPath(null);
    setConfirmedPath(null);
    if (onRouteCalculated) {
      onRouteCalculated([], false);
    }
  };

  const handleCompleteRoutingPlanning = async () => {
    if (!sourceElement?.id) {
      showToast('无法完成路由规划：缺少元素ID', 'error');
      return;
    }

    setIsCompleting(true);
    try {
      await completeRoutingPlanning([sourceElement.id]);
      showToast('路由规划已完成', 'success');
      // 可以在这里关闭面板或刷新状态
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '完成路由规划失败';
      showToast(errorMessage, 'error');
    } finally {
      setIsCompleting(false);
    }
  };

  if (!sourceElement || !targetElement) {
    return null;
  }

  return (
    <div className="bg-white border border-zinc-200 rounded-lg shadow-lg p-4 min-w-[300px]">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-zinc-900">MEP 路径规划</h3>
        {onClose && (
          <button
            onClick={onClose}
            className="text-zinc-400 hover:text-zinc-600"
            aria-label="关闭"
          >
            ×
          </button>
        )}
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-zinc-700 mb-1">
            元素类型
          </label>
          <select
            value={elementType}
            onChange={(e) => setElementType(e.target.value as typeof elementType)}
            className="w-full px-3 py-2 border border-zinc-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="Pipe">管道 (Pipe)</option>
            <option value="Duct">风管 (Duct)</option>
            <option value="CableTray">电缆桥架 (CableTray)</option>
            <option value="Conduit">导管 (Conduit)</option>
            <option value="Wire">线缆 (Wire)</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-zinc-700 mb-1">
            系统类型（可选）
          </label>
          <input
            type="text"
            value={systemType}
            onChange={(e) => setSystemType(e.target.value)}
            placeholder="如: gravity_drainage, pressure_water"
            className="w-full px-3 py-2 border border-zinc-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {elementType === 'Pipe' || elementType === 'Conduit' ? (
          <div>
            <label className="block text-sm font-medium text-zinc-700 mb-1">
              直径 (mm)
            </label>
            <input
              type="number"
              value={diameter}
              onChange={(e) => setDiameter(Number(e.target.value))}
              min="1"
              className="w-full px-3 py-2 border border-zinc-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        ) : elementType === 'Duct' ? (
          <>
            <div>
              <label className="block text-sm font-medium text-zinc-700 mb-1">
                宽度 (mm)
              </label>
              <input
                type="number"
                value={width}
                onChange={(e) => setWidth(Number(e.target.value))}
                min="1"
                className="w-full px-3 py-2 border border-zinc-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-zinc-700 mb-1">
                高度 (mm)
              </label>
              <input
                type="number"
                value={height}
                onChange={(e) => setHeight(Number(e.target.value))}
                min="1"
                className="w-full px-3 py-2 border border-zinc-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </>
        ) : (
          <div>
            <label className="block text-sm font-medium text-zinc-700 mb-1">
              宽度 (mm)
            </label>
            <input
              type="number"
              value={width}
              onChange={(e) => setWidth(Number(e.target.value))}
              min="1"
              className="w-full px-3 py-2 border border-zinc-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        )}

        {/* 电缆/电线路由依赖提示 */}
        {elementType === 'Wire' && (
          <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
            <p className="text-sm font-medium text-blue-800 mb-1">
              电缆/电线路由说明
            </p>
            <p className="text-xs text-blue-700">
              电缆/电线必须首先指定关联的桥架/线管，路由将继承桥架/线管的路径。
            </p>
            {!containerTrayId && (
              <p className="text-xs text-yellow-700 mt-1">
                ⚠ 当前未检测到关联的桥架/线管，请先建立 CONTAINED_IN 关系。
              </p>
            )}
          </div>
        )}

        {/* 桥架容量指示器 */}
        {elementType === 'CableTray' && containerTrayId && (
          <div className="border border-zinc-200 rounded-md p-3">
            <CableTrayCapacityIndicator trayId={containerTrayId} />
          </div>
        )}

        {routingState.errors.length > 0 && (
          <div className="bg-red-50 border border-red-200 rounded-md p-3">
            <p className="text-sm font-medium text-red-800">错误:</p>
            <ul className="mt-1 text-sm text-red-700 list-disc list-inside">
              {routingState.errors.map((error, index) => (
                <li key={index}>{error}</li>
              ))}
            </ul>
          </div>
        )}

        {routingState.warnings.length > 0 && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3">
            <p className="text-sm font-medium text-yellow-800">警告:</p>
            <ul className="mt-1 text-sm text-yellow-700 list-disc list-inside">
              {routingState.warnings.map((warning, index) => (
                <li key={index}>{warning}</li>
              ))}
            </ul>
          </div>
        )}

        {/* 预览路径提示 */}
        {previewPath && (
          <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
            <p className="text-sm font-medium text-blue-800">
              新路由已计算（虚线显示），请确认或取消
            </p>
          </div>
        )}

        <div className="flex space-x-2">
          <button
            onClick={handleCalculate}
            disabled={routingState.isLoading || isCompleting}
            className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:bg-zinc-400 disabled:cursor-not-allowed flex items-center justify-center"
          >
            {routingState.isLoading ? (
              <span className="flex items-center">
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                计算中...
              </span>
            ) : (
              '计算路径'
            )}
          </button>
          {routingState.path && (
            <button
              onClick={handleClear}
              className="px-4 py-2 border border-zinc-300 text-zinc-700 rounded-md hover:bg-zinc-50"
            >
              清除
            </button>
          )}
        </div>

        {/* 预览确认按钮 */}
        {previewPath && (
          <div className="flex space-x-2 pt-2 border-t border-zinc-200">
            <button
              onClick={handleConfirm}
              disabled={routingState.isLoading || isCompleting}
              className="flex-1 bg-emerald-600 text-white px-4 py-2 rounded-md hover:bg-emerald-700 disabled:bg-zinc-400 disabled:cursor-not-allowed"
            >
              确认路径
            </button>
            <button
              onClick={handleCancel}
              disabled={routingState.isLoading || isCompleting}
              className="flex-1 bg-zinc-200 text-zinc-700 px-4 py-2 rounded-md hover:bg-zinc-300 disabled:bg-zinc-300 disabled:cursor-not-allowed"
            >
              取消
            </button>
          </div>
        )}

        {/* 完成路由规划按钮 */}
        {confirmedPath && (
          <div className="pt-2 border-t border-zinc-200">
            <button
              onClick={handleCompleteRoutingPlanning}
              disabled={isCompleting}
              className="w-full bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 disabled:bg-zinc-400 disabled:cursor-not-allowed"
            >
              {isCompleting ? '完成中...' : '完成路由规划'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

