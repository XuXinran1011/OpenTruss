/**
 * snap-point-cache 工具函数测试
 */

import { generateCacheKey, SnapPointCache, globalSnapPointCache } from '../snap-point-cache'
import type { SnapPointElement } from '../topology'

describe('snap-point-cache utils', () => {
  describe('generateCacheKey', () => {
    it('应该基于元素ID生成缓存键', () => {
      const key = generateCacheKey(['element-1', 'element-2'])
      expect(key).toContain('element-1')
      expect(key).toContain('element-2')
    })

    it('应该对元素ID进行排序', () => {
      const key1 = generateCacheKey(['element-2', 'element-1'])
      const key2 = generateCacheKey(['element-1', 'element-2'])
      expect(key1).toBe(key2)
    })

    it('应该包含坐标哈希', () => {
      const coordinates = [[0, 0], [10, 0], [10, 10]]
      const key = generateCacheKey(['element-1'], coordinates)
      expect(key).toContain('snap:')
    })
  })

  describe('SnapPointCache', () => {
    let cache: SnapPointCache

    beforeEach(() => {
      cache = new SnapPointCache(10)
    })

    it('应该设置和获取缓存', () => {
      const key = 'test-key'
      const value: SnapPointElement[] = [
        {
          elementId: 'element-1',
          point: { x: 0, y: 0 },
          type: 'endpoint',
        },
      ]

      cache.set(key, value)
      const result = cache.get(key)

      expect(result).toEqual(value)
    })

    it('应该在缓存不存在时返回null', () => {
      const result = cache.get('non-existent-key')
      expect(result).toBeNull()
    })

    it('应该在缓存满时删除最旧的项', () => {
      const maxSize = 3
      const smallCache = new SnapPointCache(maxSize)

      // 填满缓存
      for (let i = 0; i < maxSize; i++) {
        smallCache.set(`key-${i}`, [])
      }

      // 添加新项，应该删除最旧的
      smallCache.set('new-key', [])

      expect(smallCache.size()).toBe(maxSize)
      expect(smallCache.get('key-0')).toBeNull()
      expect(smallCache.get('new-key')).not.toBeNull()
    })

    it('应该使特定元素的缓存失效', () => {
      cache.set('snap:element-1,element-2:', [])
      cache.set('snap:element-1,element-3:', [])
      cache.set('snap:element-4,element-5:', [])

      cache.invalidate('element-1')

      expect(cache.get('snap:element-1,element-2:')).toBeNull()
      expect(cache.get('snap:element-1,element-3:')).toBeNull()
      expect(cache.get('snap:element-4,element-5:')).not.toBeNull()
    })

    it('应该清空所有缓存', () => {
      cache.set('key-1', [])
      cache.set('key-2', [])

      cache.clear()

      expect(cache.size()).toBe(0)
      expect(cache.get('key-1')).toBeNull()
      expect(cache.get('key-2')).toBeNull()
    })

    it('应该返回缓存大小', () => {
      expect(cache.size()).toBe(0)

      cache.set('key-1', [])
      expect(cache.size()).toBe(1)

      cache.set('key-2', [])
      expect(cache.size()).toBe(2)
    })
  })

  describe('globalSnapPointCache', () => {
    it('应该存在全局缓存实例', () => {
      expect(globalSnapPointCache).toBeInstanceOf(SnapPointCache)
    })
  })
})
