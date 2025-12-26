/** 空间索引工具
 * 
 * 基于 RBush 实现的高效 2D 空间索引
 * 用于快速查询与给定区域重叠的元素
 */

import RBush from 'rbush';
import type { Rectangle } from './topology';
import { getGeometryBoundingBox } from './topology';
import { SpatialValidator, type BoundingBox3D } from '@/lib/rules/SpatialValidator';
import type { ElementDetail } from '@/services/elements';

/**
 * 空间索引项接口
 */
export interface SpatialIndexItem {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
  elementId: string;
}

/**
 * 空间索引类
 * 
 * 提供高效的 2D 空间查询功能，用于：
 * - 视口剔除：快速查找视口内的元素
 * - 磁吸点查询：快速查找附近的元素
 * - 碰撞检测：快速查找可能相交的元素
 */
export class SpatialIndex {
  private tree: RBush<SpatialIndexItem>;
  private elementMap: Map<string, SpatialIndexItem>;

  constructor() {
    this.tree = new RBush<SpatialIndexItem>();
    this.elementMap = new Map();
  }

  /**
   * 插入元素到空间索引
   * 
   * @param elementId - 元素ID
   * @param coordinates - 几何坐标数组
   */
  insert(elementId: string, coordinates: number[][]): void {
    // 先移除旧的数据（如果存在）
    this.remove(elementId);

    // 计算边界框
    const bbox = getGeometryBoundingBox(coordinates);
    if (!bbox) {
      return; // 无效的几何数据
    }

    // 创建索引项
    const item: SpatialIndexItem = {
      minX: bbox.x,
      minY: bbox.y,
      maxX: bbox.x + bbox.width,
      maxY: bbox.y + bbox.height,
      elementId,
    };

    // 插入到索引树和映射表
    this.tree.insert(item);
    this.elementMap.set(elementId, item);
  }

  /**
   * 从空间索引中移除元素
   * 
   * @param elementId - 元素ID
   */
  remove(elementId: string): void {
    const item = this.elementMap.get(elementId);
    if (item) {
      this.tree.remove(item, (a, b) => a.elementId === b.elementId);
      this.elementMap.delete(elementId);
    }
  }

  /**
   * 查询与给定矩形区域重叠的元素
   * 
   * @param bbox - 查询区域（边界框）
   * @returns 元素ID列表
   */
  search(bbox: Rectangle): string[] {
    const results = this.tree.search({
      minX: bbox.x,
      minY: bbox.y,
      maxX: bbox.x + bbox.width,
      maxY: bbox.y + bbox.height,
    });

    return results.map((item) => item.elementId);
  }

  /**
   * 查询与给定点附近区域重叠的元素（用于磁吸点查询）
   * 
   * @param point - 查询点
   * @param radius - 查询半径（世界坐标）
   * @returns 元素ID列表
   */
  searchNearby(point: { x: number; y: number }, radius: number): string[] {
    const bbox: Rectangle = {
      x: point.x - radius,
      y: point.y - radius,
      width: radius * 2,
      height: radius * 2,
    };

    return this.search(bbox);
  }

  /**
   * 清空索引
   */
  clear(): void {
    this.tree.clear();
    this.elementMap.clear();
  }

  /**
   * 批量插入元素
   * 
   * @param elements - 元素数据数组，每个元素包含 id 和 coordinates
   */
  load(elements: Array<{ id: string; coordinates: number[][] }>): void {
    const items: SpatialIndexItem[] = [];

    for (const element of elements) {
      const bbox = getGeometryBoundingBox(element.coordinates);
      if (bbox) {
        items.push({
          minX: bbox.x,
          minY: bbox.y,
          maxX: bbox.x + bbox.width,
          maxY: bbox.y + bbox.height,
          elementId: element.id,
        });
        this.elementMap.set(element.id, items[items.length - 1]);
      }
    }

    // 批量插入（RBush 支持批量插入，性能更好）
    if (items.length > 0) {
      this.tree.load(items);
    }
  }

  /**
   * 获取索引中的元素数量
   */
  size(): number {
    return this.elementMap.size;
  }

  /**
   * 检查元素是否在索引中
   */
  has(elementId: string): boolean {
    return this.elementMap.has(elementId);
  }

  /**
   * 检查 3D 碰撞（使用 2D 索引查询候选，然后用 Z 轴过滤）
   * 
   * @param element 待检查的构件
   * @param elementDetailsMap 构件详情映射表（用于获取 height 和 base_offset）
   * @returns 碰撞的构件ID列表
   */
  checkCollision3D(
    element: ElementDetail,
    elementDetailsMap: Map<string, ElementDetail>
  ): string[] {
    const spatialValidator = new SpatialValidator();
    const elementBox = spatialValidator.calculateBoundingBox(element);
    
    if (!elementBox) {
      return [];
    }
    
    // 使用 2D 索引快速查询候选（RBush 只支持 2D）
    const bbox2D: Rectangle = {
      x: elementBox.minX,
      y: elementBox.minY,
      width: elementBox.maxX - elementBox.minX,
      height: elementBox.maxY - elementBox.minY,
    };
    
    const candidateIds = this.search(bbox2D);
    
    // 使用 Z 轴过滤，找出真正碰撞的构件
    const collisions: string[] = [];
    
    for (const candidateId of candidateIds) {
      // 跳过自身
      if (candidateId === element.id) {
        continue;
      }
      
      const candidateElement = elementDetailsMap.get(candidateId);
      if (!candidateElement) {
        continue;
      }
      
      const candidateBox = spatialValidator.calculateBoundingBox(candidateElement);
      if (!candidateBox) {
        continue;
      }
      
      // 检查 3D 碰撞
      if (spatialValidator.boxesOverlap(elementBox, candidateBox)) {
        collisions.push(candidateId);
      }
    }
    
    return collisions;
  }
}

