/** 3D 几何工具函数
 * 
 * 提供 2D 到 3D 坐标转换和等轴测投影功能
 */

import { Geometry } from '@/types';

/**
 * 3D 坐标点
 */
export interface Point3D {
  x: number;
  y: number;
  z: number;
}

/**
 * 等轴测投影后的 2D 坐标点
 */
export interface Point2DProjected {
  x: number;
  y: number;
}

/**
 * 将 2D 坐标转换为 3D 坐标
 * 
 * @param x 2D X 坐标
 * @param y 2D Y 坐标
 * @param baseOffset 基础偏移（Z 轴起点，单位：米）
 * @param height 高度（Z 轴高度，单位：米，可选）
 * @returns 3D 坐标点
 */
export function point2dTo3d(
  x: number,
  y: number,
  baseOffset: number = 0,
  height: number = 0
): Point3D {
  return {
    x,
    y,
    z: baseOffset,
  };
}

/**
 * 将几何图形转换为 3D 坐标数组
 * 
 * 支持 3D 原生坐标（如果坐标已有 Z 值，使用它；否则使用 baseOffset）
 * 
 * @param geometry 几何图形（3D 原生，支持 2D 输入）
 * @param baseOffset 基础偏移（Z 轴起点，单位：米，当坐标没有 Z 值时使用）
 * @param height 高度（Z 轴高度，单位：米，可选，用于计算终点 Z 值）
 * @returns 3D 坐标点数组
 */
export function geometryTo3d(
  geometry: Geometry,
  baseOffset: number = 0,
  height: number = 0
): Point3D[] {
  return geometry.coordinates.map((coord) => {
    if (coord.length >= 3) {
      // 已有 Z 坐标，使用它
      const z = coord[2] !== null && coord[2] !== undefined ? coord[2] : baseOffset;
      return { x: coord[0], y: coord[1], z };
    } else if (coord.length >= 2) {
      // 只有 X, Y，使用 baseOffset 作为 Z
      return { x: coord[0], y: coord[1], z: baseOffset };
    } else {
      throw new Error(`Invalid coordinate length: ${coord.length}, expected 2 or 3`);
    }
  });
}

/**
 * @deprecated 使用 geometryTo3d 代替（支持 3D 原生坐标）
 * 保留此函数以保持向后兼容
 */
export function geometry2dTo3d(
  geometry: Geometry,
  baseOffset: number = 0,
  height: number = 0
): Point3D[] {
  return geometryTo3d(geometry, baseOffset, height);
}

/**
 * 等轴测投影：将 3D 坐标投影到 2D 平面
 * 
 * 等轴测投影参数：
 * - X 轴：30° 旋转
 * - Y 轴：-30° 旋转
 * - Z 轴：垂直向上
 * 
 * @param point 3D 坐标点
 * @param scale 缩放比例（默认 1）
 * @returns 投影后的 2D 坐标点
 */
export function isometricProjection(
  point: Point3D,
  scale: number = 1
): Point2DProjected {
  // 等轴测投影矩阵
  // X' = (X - Y) * cos(30°)
  // Y' = (X + Y) * sin(30°) - Z
  
  const cos30 = Math.cos(Math.PI / 6); // cos(30°) ≈ 0.866
  const sin30 = Math.sin(Math.PI / 6); // sin(30°) = 0.5
  
  const x2d = (point.x - point.y) * cos30 * scale;
  const y2d = ((point.x + point.y) * sin30 - point.z) * scale;
  
  return { x: x2d, y: y2d };
}

/**
 * 计算 3D 几何图形的边界框
 * 
 * @param points 3D 坐标点数组
 * @returns 边界框 { minX, minY, minZ, maxX, maxY, maxZ }
 */
export function calculate3dBoundingBox(points: Point3D[]): {
  minX: number;
  minY: number;
  minZ: number;
  maxX: number;
  maxY: number;
  maxZ: number;
} {
  if (points.length === 0) {
    return { minX: 0, minY: 0, minZ: 0, maxX: 0, maxY: 0, maxZ: 0 };
  }

  let minX = points[0].x;
  let minY = points[0].y;
  let minZ = points[0].z;
  let maxX = points[0].x;
  let maxY = points[0].y;
  let maxZ = points[0].z;

  for (const point of points) {
    minX = Math.min(minX, point.x);
    minY = Math.min(minY, point.y);
    minZ = Math.min(minZ, point.z);
    maxX = Math.max(maxX, point.x);
    maxY = Math.max(maxY, point.y);
    maxZ = Math.max(maxZ, point.z);
  }

  return { minX, minY, minZ, maxX, maxY, maxZ };
}

/**
 * 计算等轴测投影后的边界框（用于确定视图范围）
 * 
 * @param points 3D 坐标点数组
 * @param scale 缩放比例
 * @returns 投影后的边界框 { minX, minY, maxX, maxY, width, height }
 */
export function calculateProjectedBoundingBox(
  points: Point3D[],
  scale: number = 1
): {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
  width: number;
  height: number;
} {
  if (points.length === 0) {
    return { minX: 0, minY: 0, maxX: 0, maxY: 0, width: 0, height: 0 };
  }

  const projected = points.map(p => isometricProjection(p, scale));
  
  let minX = projected[0].x;
  let minY = projected[0].y;
  let maxX = projected[0].x;
  let maxY = projected[0].y;

  for (const p of projected) {
    minX = Math.min(minX, p.x);
    minY = Math.min(minY, p.y);
    maxX = Math.max(maxX, p.x);
    maxY = Math.max(maxY, p.y);
  }

  return {
    minX,
    minY,
    maxX,
    maxY,
    width: maxX - minX,
    height: maxY - minY,
  };
}

