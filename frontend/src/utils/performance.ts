/** 性能优化工具函数 */

/**
 * 防抖函数
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;
  
  return function executedFunction(...args: Parameters<T>) {
    const later = () => {
      timeout = null;
      func(...args);
    };
    
    if (timeout) {
      clearTimeout(timeout);
    }
    timeout = setTimeout(later, wait);
  };
}

/**
 * 节流函数
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean;
  
  return function executedFunction(...args: Parameters<T>) {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}

/**
 * 视口边界框
 */
export interface ViewportBounds {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
}

/**
 * 计算视口边界框（考虑缩放和平移）
 */
export function calculateViewportBounds(
  width: number,
  height: number,
  viewTransform: { x: number; y: number; scale: number }
): ViewportBounds {
  // 将屏幕坐标转换为世界坐标
  const scale = viewTransform.scale;
  const tx = viewTransform.x;
  const ty = viewTransform.y;
  
  // 屏幕左上角对应的世界坐标
  const minX = (-tx) / scale;
  const minY = (-ty) / scale;
  
  // 屏幕右下角对应的世界坐标
  const maxX = (width - tx) / scale;
  const maxY = (height - ty) / scale;
  
  return { minX, minY, maxX, maxY };
}

/**
 * 检查点是否在视口内
 */
export function isPointInViewport(
  x: number,
  y: number,
  viewport: ViewportBounds,
  padding: number = 0
): boolean {
  return (
    x >= viewport.minX - padding &&
    x <= viewport.maxX + padding &&
    y >= viewport.minY - padding &&
    y <= viewport.maxY + padding
  );
}

/**
 * 检查几何图形是否与视口相交
 */
export function isGeometryInViewport(
  coordinates: number[][],
  viewport: ViewportBounds,
  padding: number = 100 // 额外的边距，确保边界附近的元素也被渲染
): boolean {
  if (coordinates.length === 0) return false;
  
  // 检查是否有任何点在视口内
  for (const coord of coordinates) {
    if (isPointInViewport(coord[0] || 0, coord[1] || 0, viewport, padding)) {
      return true;
    }
  }
  
  // 检查边界框是否与视口相交
  const minX = Math.min(...coordinates.map(c => c[0] || 0));
  const maxX = Math.max(...coordinates.map(c => c[0] || 0));
  const minY = Math.min(...coordinates.map(c => c[1] || 0));
  const maxY = Math.max(...coordinates.map(c => c[1] || 0));
  
  return !(
    maxX < viewport.minX - padding ||
    minX > viewport.maxX + padding ||
    maxY < viewport.minY - padding ||
    minY > viewport.maxY + padding
  );
}

