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
 * 获取线段的中点
 */
export function getLineMidpoint(
  start: { x: number; y: number },
  end: { x: number; y: number }
): { x: number; y: number } {
  return {
    x: (start.x + end.x) / 2,
    y: (start.y + end.y) / 2,
  };
}

/**
 * 获取几何的所有中点（用于磁吸检测）
 * 对于线段，返回中点；对于多段线，返回每段的中点
 */
export function getGeometryMidpoints(coordinates: number[][]): { x: number; y: number }[] {
  if (coordinates.length < 2) return [];
  
  const midpoints: { x: number; y: number }[] = [];
  
  for (let i = 0; i < coordinates.length - 1; i++) {
    const start = { x: coordinates[i][0] || 0, y: coordinates[i][1] || 0 };
    const end = { x: coordinates[i + 1][0] || 0, y: coordinates[i + 1][1] || 0 };
    midpoints.push(getLineMidpoint(start, end));
  }
  
  return midpoints;
}

/**
 * 获取所有几何的交点（用于磁吸检测）
 * 计算当前几何与其他几何的交点
 * 
 * @param coordinates - 当前几何的坐标数组
 * @param otherGeometries - 其他几何的坐标数组
 * @param spatialIndex - 可选的空间索引，用于预过滤候选几何
 * @param searchBbox - 可选的搜索边界框，用于空间过滤
 * @returns 交点数组
 */
export function getGeometryIntersections(
  coordinates: number[][],
  otherGeometries: Array<{ coordinates: number[][] }>,
  spatialIndex?: { search: (bbox: Rectangle) => string[] },
  searchBbox?: Rectangle
): { x: number; y: number }[] {
  const intersections: { x: number; y: number }[] = [];
  
  if (coordinates.length < 2) return intersections;
  
  // 如果提供了空间索引和搜索边界框，先进行空间过滤
  let geometriesToCheck = otherGeometries;
  if (spatialIndex && searchBbox) {
    const candidateIds = spatialIndex.search(searchBbox);
    // 注意：这里假设 otherGeometries 中的元素有某种方式关联到ID
    // 由于当前接口不包含ID，我们暂时跳过这个优化
    // 在实际使用中，调用方已经通过空间索引过滤了 otherGeometries
  }
  
  // 遍历当前几何的每条线段
  for (let i = 0; i < coordinates.length - 1; i++) {
    const p1 = { x: coordinates[i][0] || 0, y: coordinates[i][1] || 0 };
    const p2 = { x: coordinates[i + 1][0] || 0, y: coordinates[i + 1][1] || 0 };
    
    // 与其他几何的每条线段计算交点
    for (const otherGeometry of geometriesToCheck) {
      if (otherGeometry.coordinates.length < 2) continue;
      
      for (let j = 0; j < otherGeometry.coordinates.length - 1; j++) {
        const p3 = { 
          x: otherGeometry.coordinates[j][0] || 0, 
          y: otherGeometry.coordinates[j][1] || 0 
        };
        const p4 = { 
          x: otherGeometry.coordinates[j + 1][0] || 0, 
          y: otherGeometry.coordinates[j + 1][1] || 0 
        };
        
        const intersection = lineIntersection(p1, p2, p3, p4);
        if (intersection) {
          intersections.push(intersection);
        }
      }
    }
  }
  
  return intersections;
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
 * 吸附点元素信息（避免循环依赖，使用基本类型而非ElementDetail）
 */
export interface SnapPointElement {
  x: number;
  y: number;
  elementId: string;
  element?: {
    id: string;
    speckle_type?: string;
    geometry?: {
      coordinates: number[][];  // 3D 坐标：[[x, y, z], ...]
      type?: string;
      closed?: boolean;
    };
    [key: string]: unknown; // 允许其他属性
  };
}

/**
 * 查找最近的吸附点（带元素信息）
 * 
 * 在给定的吸附点列表中查找距离指定点最近的吸附点。
 * 用于 Trace Mode 下的磁吸功能，帮助用户对齐构件端点。
 * 
 * @param point - 目标点坐标
 * @param snapPoints - 吸附点列表（包含元素信息）
 * @param snapDistance - 吸附距离阈值（默认: 10）
 * @returns 最近的吸附点，如果距离超过阈值则返回 null
 */
export function findNearestSnapPointWithElement(
  point: { x: number; y: number },
  snapPoints: SnapPointElement[],
  snapDistance: number = 10
): SnapPointElement | null {
  let nearest: SnapPointElement | null = null;
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

/**
 * 调整路径点以实现角度吸附
 * 
 * 给定路径点 P[i-1], P[i], P[i+1]，调整P[i]的位置使转弯角度等于目标角度。
 * 保持P[i-1]到P[i]的距离和P[i]到P[i+1]的距离不变。
 * 
 * **边界情况处理**：
 * - 如果路径点少于3个或索引无效，返回原路径
 * - 如果向量长度为0，返回原路径（避免除零错误）
 * 
 * @param path - 路径点数组 [[x1, y1], [x2, y2], ...]
 * @param pointIndex - 需要调整的转弯点索引（路径中的中间点，1 到 path.length-2）
 * @param targetAngle - 目标角度（度）
 * @returns 调整后的路径点数组
 */
export function adjustPathForAngleSnap(
  path: number[][],
  pointIndex: number,
  targetAngle: number
): number[][] {
  if (path.length < 3 || pointIndex < 1 || pointIndex >= path.length - 1) {
    return path; // 无法调整，返回原路径
  }

  const pPrev = path[pointIndex - 1];
  const pCurr = path[pointIndex];
  const pNext = path[pointIndex + 1];

  // 计算当前两个向量
  const v1 = {
    x: pCurr[0] - pPrev[0],
    y: pCurr[1] - pPrev[1]
  };
  const v2 = {
    x: pNext[0] - pCurr[0],
    y: pNext[1] - pCurr[1]
  };

  // 计算向量长度
  const len1 = Math.sqrt(v1.x * v1.x + v1.y * v1.y);
  const len2 = Math.sqrt(v2.x * v2.x + v2.y * v2.y);

  if (len1 === 0 || len2 === 0) {
    return path; // 向量长度为0，无法调整
  }

  // 归一化向量1
  const dir1 = {
    x: v1.x / len1,
    y: v1.y / len1
  };

  // 计算向量1的角度（弧度）
  const angle1 = Math.atan2(dir1.y, dir1.x);

  // 计算目标角度对应的向量2方向（弧度）
  // 目标角度是内角，所以向量2的方向 = 向量1的方向 + (180° - 目标角度)
  const targetAngleRad = (targetAngle * Math.PI) / 180;
  const angle2 = angle1 + (Math.PI - targetAngleRad);

  // 计算归一化的向量2方向
  const dir2 = {
    x: Math.cos(angle2),
    y: Math.sin(angle2)
  };

  // 计算新的P[i]位置
  // 方案1：保持P[i-1]到P[i]的距离不变，P[i]的新位置 = P[i-1] + len1 * dir1
  // 方案2：保持P[i]到P[i+1]的距离不变，P[i]的新位置 = P[i+1] - len2 * dir2
  // 我们采用方案1，然后调整P[i+1]使其到新P[i]的距离和方向满足要求
  
  const newPCurr = {
    x: pPrev[0] + len1 * dir1.x,
    y: pPrev[1] + len1 * dir1.y
  };

  // 计算新的P[i+1]位置（保持P[i]到P[i+1]的距离）
  const newPNext = {
    x: newPCurr.x + len2 * dir2.x,
    y: newPCurr.y + len2 * dir2.y
  };

  // 创建调整后的路径
  const adjustedPath = [...path];
  adjustedPath[pointIndex] = [newPCurr.x, newPCurr.y];
  adjustedPath[pointIndex + 1] = [newPNext.x, newPNext.y];

  return adjustedPath;
}

/**
 * 矩形定义（用于框选）
 */
export interface Rectangle {
  x: number;
  y: number;
  width: number;
  height: number;
}

/**
 * 创建矩形（从两个点）
 */
export function createRectangle(
  x1: number,
  y1: number,
  x2: number,
  y2: number
): Rectangle {
  const x = Math.min(x1, x2);
  const y = Math.min(y1, y2);
  const width = Math.abs(x2 - x1);
  const height = Math.abs(y2 - y1);
  return { x, y, width, height };
}

/**
 * 检查点是否在矩形内
 */
export function pointInRectangle(
  point: { x: number; y: number },
  rect: Rectangle
): boolean {
  return (
    point.x >= rect.x &&
    point.x <= rect.x + rect.width &&
    point.y >= rect.y &&
    point.y <= rect.y + rect.height
  );
}

/**
 * 获取几何的边界框（bounding box）
 */
export function getGeometryBoundingBox(coordinates: number[][]): Rectangle | null {
  if (coordinates.length === 0) return null;
  
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;

  for (const coord of coordinates) {
    const x = coord[0] || 0;
    const y = coord[1] || 0;
    minX = Math.min(minX, x);
    minY = Math.min(minY, y);
    maxX = Math.max(maxX, x);
    maxY = Math.max(maxY, y);
  }

  return {
    x: minX,
    y: minY,
    width: maxX - minX,
    height: maxY - minY,
  };
}

/**
 * 检查矩形是否与几何相交（使用边界框快速检测）
 */
export function rectangleIntersectsGeometry(
  rect: Rectangle,
  coordinates: number[][]
): boolean {
  // 快速检测：使用边界框
  const geomBBox = getGeometryBoundingBox(coordinates);
  if (!geomBBox) return false;

  // 检查两个边界框是否相交
  return !(
    rect.x + rect.width < geomBBox.x ||
    rect.x > geomBBox.x + geomBBox.width ||
    rect.y + rect.height < geomBBox.y ||
    rect.y > geomBBox.y + geomBBox.height
  );
}

/**
 * 检查矩形是否与几何相交（精确检测：检查是否有顶点在矩形内或线段与矩形相交）
 */
export function rectangleIntersectsGeometryPrecise(
  rect: Rectangle,
  coordinates: number[][]
): boolean {
  // 快速检测：如果边界框不相交，直接返回 false
  if (!rectangleIntersectsGeometry(rect, coordinates)) {
    return false;
  }

  // 检查是否有顶点在矩形内
  for (const coord of coordinates) {
    if (pointInRectangle({ x: coord[0] || 0, y: coord[1] || 0 }, rect)) {
      return true;
    }
  }

  // 检查是否有线段与矩形相交
  const rectCorners = [
    { x: rect.x, y: rect.y },
    { x: rect.x + rect.width, y: rect.y },
    { x: rect.x + rect.width, y: rect.y + rect.height },
    { x: rect.x, y: rect.y + rect.height },
  ];

  // 检查几何的每条线段是否与矩形的边相交
  for (let i = 0; i < coordinates.length - 1; i++) {
    const p1 = { x: coordinates[i][0] || 0, y: coordinates[i][1] || 0 };
    const p2 = { x: coordinates[i + 1][0] || 0, y: coordinates[i + 1][1] || 0 };

    // 检查与矩形的每条边是否相交
    for (let j = 0; j < rectCorners.length; j++) {
      const r1 = rectCorners[j];
      const r2 = rectCorners[(j + 1) % rectCorners.length];
      if (lineIntersection(p1, p2, r1, r2)) {
        return true;
      }
    }
  }

  return false;
}

