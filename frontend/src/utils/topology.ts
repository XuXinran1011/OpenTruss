/** 拓扑计算工具 */

/**
 * 计算两点之间的距离
 */
export function distance(
  x1: number,
  y1: number,
  x2: number,
  y2: number
): number {
  return Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
}

/**
 * 磁吸检测：检查点是否在吸附范围内
 */
export function snapToPoint(
  point: { x: number; y: number },
  target: { x: number; y: number },
  snapDistance: number = 5
): { x: number; y: number; snapped: boolean } | null {
  const dist = distance(point.x, point.y, target.x, target.y);
  
  if (dist <= snapDistance) {
    return { x: target.x, y: target.y, snapped: true };
  }
  
  return null;
}

/**
 * 磁吸到网格
 */
export function snapToGrid(
  point: { x: number; y: number },
  gridSize: number = 20
): { x: number; y: number } {
  return {
    x: Math.round(point.x / gridSize) * gridSize,
    y: Math.round(point.y / gridSize) * gridSize,
  };
}

/**
 * 检测线段是否相交
 */
export function lineIntersection(
  p1: { x: number; y: number },
  p2: { x: number; y: number },
  p3: { x: number; y: number },
  p4: { x: number; y: number }
): { x: number; y: number } | null {
  const denom = (p4.y - p3.y) * (p2.x - p1.x) - (p4.x - p3.x) * (p2.y - p1.y);
  
  if (denom === 0) {
    return null; // 平行线
  }
  
  const ua = ((p4.x - p3.x) * (p1.y - p3.y) - (p4.y - p3.y) * (p1.x - p3.x)) / denom;
  const ub = ((p2.x - p1.x) * (p1.y - p3.y) - (p2.y - p1.y) * (p1.x - p3.x)) / denom;
  
  if (ua >= 0 && ua <= 1 && ub >= 0 && ub <= 1) {
    return {
      x: p1.x + ua * (p2.x - p1.x),
      y: p1.y + ua * (p2.y - p1.y),
    };
  }
  
  return null;
}

/**
 * 检查点是否在多边形内（使用射线法）
 */
export function pointInPolygon(
  point: { x: number; y: number },
  polygon: { x: number; y: number }[]
): boolean {
  let inside = false;
  
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const xi = polygon[i].x;
    const yi = polygon[i].y;
    const xj = polygon[j].x;
    const yj = polygon[j].y;
    
    const intersect =
      yi > point.y !== yj > point.y &&
      point.x < ((xj - xi) * (point.y - yi)) / (yj - yi) + xi;
    
    if (intersect) {
      inside = !inside;
    }
  }
  
  return inside;
}

/**
 * 获取几何的所有端点（用于磁吸检测）
 */
export function getGeometryEndpoints(coordinates: number[][]): { x: number; y: number }[] {
  if (coordinates.length === 0) return [];
  if (coordinates.length === 1) {
    return [{ x: coordinates[0][0] || 0, y: coordinates[0][1] || 0 }];
  }
  // 返回第一个和最后一个点
  return [
    { x: coordinates[0][0] || 0, y: coordinates[0][1] || 0 },
    { x: coordinates[coordinates.length - 1][0] || 0, y: coordinates[coordinates.length - 1][1] || 0 },
  ];
}

/**
 * 查找最近的吸附点
 */
export function findNearestSnapPoint(
  point: { x: number; y: number },
  snapPoints: { x: number; y: number }[],
  snapDistance: number = 10
): { x: number; y: number } | null {
  let nearest: { x: number; y: number } | null = null;
  let minDistance = snapDistance;

  for (const snapPoint of snapPoints) {
    const dist = distance(point.x, point.y, snapPoint.x, snapPoint.y);
    if (dist < minDistance) {
      minDistance = dist;
      nearest = snapPoint;
    }
  }

  return nearest;
}

/**
 * 查找最近的吸附点（带元素信息）
 */
export function findNearestSnapPointWithElement(
  point: { x: number; y: number },
  snapPoints: Array<{ 
    x: number; 
    y: number; 
    elementId: string;
    element?: any;  // ElementDetail类型，避免循环依赖
  }>,
  snapDistance: number = 10
): { x: number; y: number; elementId: string; element?: any } | null {
  let nearest: { x: number; y: number; elementId: string; element?: any } | null = null;
  let minDistance = snapDistance;

  for (const snapPoint of snapPoints) {
    const dist = distance(point.x, point.y, snapPoint.x, snapPoint.y);
    if (dist < minDistance) {
      minDistance = dist;
      nearest = {
        x: snapPoint.x,
        y: snapPoint.y,
        elementId: snapPoint.elementId,
        element: snapPoint.element,
      };
    }
  }

  return nearest;
}

/**
 * 获取线段上距离点最近的位置
 */
export function nearestPointOnLine(
  point: { x: number; y: number },
  lineStart: { x: number; y: number },
  lineEnd: { x: number; y: number }
): { x: number; y: number; distance: number } {
  const A = point.x - lineStart.x;
  const B = point.y - lineStart.y;
  const C = lineEnd.x - lineStart.x;
  const D = lineEnd.y - lineStart.y;

  const dot = A * C + B * D;
  const lenSq = C * C + D * D;
  let param = -1;
  if (lenSq !== 0) {
    param = dot / lenSq;
  }

  let xx: number;
  let yy: number;

  if (param < 0) {
    xx = lineStart.x;
    yy = lineStart.y;
  } else if (param > 1) {
    xx = lineEnd.x;
    yy = lineEnd.y;
  } else {
    xx = lineStart.x + param * C;
    yy = lineStart.y + param * D;
  }

  const dx = point.x - xx;
  const dy = point.y - yy;
  const dist = Math.sqrt(dx * dx + dy * dy);

  return { x: xx, y: yy, distance: dist };
}

