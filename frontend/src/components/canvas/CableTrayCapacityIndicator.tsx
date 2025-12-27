/** 桥架容量指示器组件 */

'use client';

import { useEffect, useState } from 'react';
import { getCableTrayCapacity, type CableTrayCapacity } from '@/services/capacity';
import { cn } from '@/lib/utils';

interface CableTrayCapacityIndicatorProps {
  trayId: string;
  className?: string;
}

export function CableTrayCapacityIndicator({
  trayId,
  className,
}: CableTrayCapacityIndicatorProps) {
  const [capacity, setCapacity] = useState<CableTrayCapacity | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchCapacity() {
      try {
        setLoading(true);
        setError(null);
        const data = await getCableTrayCapacity(trayId);
        if (!cancelled) {
          setCapacity(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : '获取容量信息失败');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchCapacity();

    return () => {
      cancelled = true;
    };
  }, [trayId]);

  if (loading) {
    return (
      <div className={cn('text-sm text-zinc-400', className)}>
        加载中...
      </div>
    );
  }

  if (error) {
    return (
      <div className={cn('text-sm text-red-500', className)}>
        {error}
      </div>
    );
  }

  if (!capacity) {
    return null;
  }

  const powerRatio = capacity.power_cable_ratio * 100;
  const controlRatio = capacity.control_cable_ratio * 100;
  const powerMax = 40; // 电力电缆最大占比 40%
  const controlMax = 50; // 控制电缆最大占比 50%

  // 获取进度条颜色
  const getPowerColor = () => {
    if (powerRatio > powerMax) return 'bg-red-500';
    if (powerRatio > powerMax * 0.9) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getControlColor = () => {
    if (controlRatio > controlMax) return 'bg-red-500';
    if (controlRatio > controlMax * 0.9) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  return (
    <div className={cn('space-y-2', className)}>
      <div className="text-xs font-medium text-zinc-700 dark:text-zinc-300">
        桥架容量使用情况
      </div>

      {/* 电力电缆容量 */}
      <div className="space-y-1">
        <div className="flex items-center justify-between text-xs">
          <span className="text-zinc-600 dark:text-zinc-400">电力电缆</span>
          <span
            className={cn(
              'font-medium',
              powerRatio > powerMax
                ? 'text-red-600 dark:text-red-400'
                : powerRatio > powerMax * 0.9
                ? 'text-yellow-600 dark:text-yellow-400'
                : 'text-green-600 dark:text-green-400'
            )}
          >
            {powerRatio.toFixed(1)}% / {powerMax}%
          </span>
        </div>
        <div className="h-2 w-full overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-700">
          <div
            className={cn('h-full transition-all duration-300', getPowerColor())}
            style={{ width: `${Math.min(powerRatio, 100)}%` }}
          />
        </div>
      </div>

      {/* 控制电缆容量 */}
      <div className="space-y-1">
        <div className="flex items-center justify-between text-xs">
          <span className="text-zinc-600 dark:text-zinc-400">控制电缆</span>
          <span
            className={cn(
              'font-medium',
              controlRatio > controlMax
                ? 'text-red-600 dark:text-red-400'
                : controlRatio > controlMax * 0.9
                ? 'text-yellow-600 dark:text-yellow-400'
                : 'text-green-600 dark:text-green-400'
            )}
          >
            {controlRatio.toFixed(1)}% / {controlMax}%
          </span>
        </div>
        <div className="h-2 w-full overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-700">
          <div
            className={cn('h-full transition-all duration-300', getControlColor())}
            style={{ width: `${Math.min(controlRatio, 100)}%` }}
          />
        </div>
      </div>

      {/* 错误和警告 */}
      {capacity.errors.length > 0 && (
        <div className="space-y-1">
          {capacity.errors.map((err, idx) => (
            <div key={idx} className="text-xs text-red-600 dark:text-red-400">
              ⚠ {err}
            </div>
          ))}
        </div>
      )}

      {capacity.warnings.length > 0 && (
        <div className="space-y-1">
          {capacity.warnings.map((warn, idx) => (
            <div key={idx} className="text-xs text-yellow-600 dark:text-yellow-400">
              ⚠ {warn}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
