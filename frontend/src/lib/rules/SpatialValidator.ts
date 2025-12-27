/**
 * 空间校验器（规则引擎 Phase 3）
 * 
 * 实现物理碰撞检测功能，使用 2.5D 包围盒（AABB）算法
 */

import type { ElementDetail } from '@/services/elements';

/**
 * 3D 包围盒接口
 */
export interface BoundingBox3D {
  minX: number;
  minY: number;
  minZ: number;
  maxX: number;
  maxY: number;
  maxZ: number;
}

/**
 * 空间校验器类
 * 
 * 提供 3D 碰撞检测功能，使用轴对齐包围盒（AABB）算法
 */
export class SpatialValidator {
  /**
   * 检查两个 3D 包围盒是否重叠
   * 
   * 两个 Box 重叠 ⟺ X轴重叠 && Y轴重叠 && Z轴重叠
   * 
   * @param box1 第一个包围盒
   * @param box2 第二个包围盒
   * @returns 是否重叠
   */
  boxesOverlap(box1: BoundingBox3D, box2: BoundingBox3D): boolean {
    // X 轴重叠
    const xOverlap = box1.maxX >= box2.minX && box1.minX <= box2.maxX;
    
    // Y 轴重叠
    const yOverlap = box1.maxY >= box2.minY && box1.minY <= box2.maxY;
    
    // Z 轴重叠
    const zOverlap = box1.maxZ >= box2.minZ && box1.minZ <= box2.maxZ;
    
    return xOverlap && yOverlap && zOverlap;
  }

  /**
   * 从构件数据计算 3D 包围盒
   * 
   * @param element 构件数据
   * @returns 3D 包围盒，如果无法计算则返回 null
   */
  calculateBoundingBox(element: ElementDetail): BoundingBox3D | null {
    const geometry = element.geometry;
    
    // 检查必要的几何数据
    if (!geometry || !geometry.coordinates || geometry.coordinates.length < 2) {
      return null;
    }
    
    const height = element.height ?? 0;
    const baseOffset = element.base_offset ?? 0;
    
    // 计算 2D 包围盒（使用 X, Y 坐标，忽略 Z）
    const coords = geometry.coordinates;
    let minX = Infinity;
    let minY = Infinity;
    let maxX = -Infinity;
    let maxY = -Infinity;
    
    for (const coord of coords) {
      const x = coord[0] ?? 0;
      const y = coord[1] ?? 0;
      
      minX = Math.min(minX, x);
      minY = Math.min(minY, y);
      maxX = Math.max(maxX, x);
      maxY = Math.max(maxY, y);
    }
    
    // 如果坐标无效，返回 null
    if (!isFinite(minX) || !isFinite(minY) || !isFinite(maxX) || !isFinite(maxY)) {
      return null;
    }
    
    // 转换为 3D 包围盒
    return {
      minX,
      minY,
      minZ: baseOffset,
      maxX,
      maxY,
      maxZ: baseOffset + height,
    };
  }

  /**
   * 检查构件是否与其他构件碰撞
   * 
   * @param element 待检查的构件
   * @param otherElements 其他构件列表
   * @returns 碰撞的构件列表
   */
  checkCollisions(
    element: ElementDetail,
    otherElements: ElementDetail[]
  ): ElementDetail[] {
    const elementBox = this.calculateBoundingBox(element);
    if (!elementBox) {
      return [];
    }
    
    const collisions: ElementDetail[] = [];
    
    for (const otherElement of otherElements) {
      // 跳过自身
      if (otherElement.id === element.id) {
        continue;
      }
      
      const otherBox = this.calculateBoundingBox(otherElement);
      if (!otherBox) {
        continue;
      }
      
      if (this.boxesOverlap(elementBox, otherBox)) {
        collisions.push(otherElement);
      }
    }
    
    return collisions;
  }
}

