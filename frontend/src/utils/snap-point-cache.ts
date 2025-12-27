/** 磁吸点缓存工具
 * 
 * 缓存磁吸点计算结果，避免重复计算
 */

import type { SnapPointElement } from './topology';

/**
 * 缓存键生成器
 * 
 * 基于元素ID列表和坐标生成缓存键
 * 使用简单的哈希算法，确保相同输入生成相同键
 */
export function generateCacheKey(
  elementIds: string[],
  coordinates?: number[][]
): string {
  // 对元素ID进行排序，确保顺序不影响缓存键
  const sortedIds = [...elementIds].sort().join(',');
  
  // 如果有坐标，计算坐标的简单哈希
  let coordHash = '';
  if (coordinates && coordinates.length > 0) {
    // 使用前几个点的坐标生成哈希（避免过长）
    const sampleSize = Math.min(3, coordinates.length);
    const sample = coordinates.slice(0, sampleSize);
    coordHash = sample
      .map((coord) => `${Math.round(coord[0] || 0)},${Math.round(coord[1] || 0)}`)
      .join('|');
  }
  
  return `snap:${sortedIds}:${coordHash}`;
}

/**
 * 磁吸点缓存类
 * 
 * 提供磁吸点计算结果的缓存功能
 */
export class SnapPointCache {
  private cache: Map<string, SnapPointElement[]>;
  private maxSize: number;

  constructor(maxSize: number = 100) {
    this.cache = new Map();
    this.maxSize = maxSize;
  }

  /**
   * 获取缓存的磁吸点
   * 
   * @param key - 缓存键
   * @returns 磁吸点数组，如果不存在则返回 null
   */
  get(key: string): SnapPointElement[] | null {
    return this.cache.get(key) || null;
  }

  /**
   * 设置缓存的磁吸点
   * 
   * @param key - 缓存键
   * @param value - 磁吸点数组
   */
  set(key: string, value: SnapPointElement[]): void {
    // 如果缓存已满，删除最旧的项（简单策略：删除第一个）
    if (this.cache.size >= this.maxSize && !this.cache.has(key)) {
      const firstKey = this.cache.keys().next().value;
      if (firstKey) {
        this.cache.delete(firstKey);
      }
    }

    this.cache.set(key, value);
  }

  /**
   * 使特定元素的缓存失效
   * 
   * @param elementId - 元素ID
   */
  invalidate(elementId: string): void {
    // 查找所有包含该元素ID的缓存键并删除
    const keysToDelete: string[] = [];
    for (const key of this.cache.keys()) {
      if (key.includes(elementId)) {
        keysToDelete.push(key);
      }
    }
    keysToDelete.forEach((key) => this.cache.delete(key));
  }

  /**
   * 清空所有缓存
   */
  clear(): void {
    this.cache.clear();
  }

  /**
   * 获取缓存大小
   */
  size(): number {
    return this.cache.size;
  }
}

/**
 * 全局磁吸点缓存实例
 * 
 * 在 CanvasRenderer 中共享使用
 */
export const globalSnapPointCache = new SnapPointCache(100);

