/**
 * spatial-index 工具函数测试
 */

import { SpatialIndex } from '../spatial-index'
import type { Rectangle } from '../topology'
import type { ElementDetail } from '@/services/elements'

// Mock dependencies
jest.mock('../topology', () => ({
  getGeometryBoundingBox: jest.fn((coords: number[][]) => {
    if (coords.length === 0) return null
    const xs = coords.map(c => c[0])
    const ys = coords.map(c => c[1] || 0)
    return {
      x: Math.min(...xs),
      y: Math.min(...ys),
      width: Math.max(...xs) - Math.min(...xs),
      height: Math.max(...ys) - Math.min(...ys),
    }
  }),
}))

jest.mock('@/lib/rules/SpatialValidator', () => ({
  SpatialValidator: jest.fn().mockImplementation(() => ({
    calculateBoundingBox: jest.fn((element: ElementDetail) => {
      if (!element.geometry || !element.geometry.coordinates) return null
      const coords = element.geometry.coordinates
      const xs = coords.map((c: number[]) => c[0])
      const ys = coords.map((c: number[]) => c[1] || 0)
      const zs = coords.map((c: number[]) => c[2] || 0)
      return {
        minX: Math.min(...xs),
        minY: Math.min(...ys),
        minZ: Math.min(...zs),
        maxX: Math.max(...xs),
        maxY: Math.max(...ys),
        maxZ: Math.max(...zs),
      }
    }),
    boxesOverlap: jest.fn((box1: any, box2: any) => {
      return (
        box1.minX < box2.maxX &&
        box1.maxX > box2.minX &&
        box1.minY < box2.maxY &&
        box1.maxY > box2.minY &&
        box1.minZ < box2.maxZ &&
        box1.maxZ > box2.minZ
      )
    }),
  })),
}))

describe('SpatialIndex', () => {
  let index: SpatialIndex

  beforeEach(() => {
    index = new SpatialIndex()
  })

  describe('insert', () => {
    it('应该插入元素到空间索引', () => {
      index.insert('element-1', [[0, 0], [10, 10]])

      expect(index.has('element-1')).toBe(true)
      expect(index.size()).toBe(1)
    })

    it('应该更新已存在的元素', () => {
      index.insert('element-1', [[0, 0], [10, 10]])
      index.insert('element-1', [[20, 20], [30, 30]])

      expect(index.size()).toBe(1)
    })
  })

  describe('remove', () => {
    it('应该从空间索引中移除元素', () => {
      index.insert('element-1', [[0, 0], [10, 10]])
      index.remove('element-1')

      expect(index.has('element-1')).toBe(false)
      expect(index.size()).toBe(0)
    })

    it('应该安全地移除不存在的元素', () => {
      expect(() => index.remove('non-existent')).not.toThrow()
    })
  })

  describe('search', () => {
    it('应该查询与给定矩形区域重叠的元素', () => {
      index.insert('element-1', [[0, 0], [10, 10]])
      index.insert('element-2', [[20, 20], [30, 30]])

      const bbox: Rectangle = { x: 5, y: 5, width: 10, height: 10 }
      const results = index.search(bbox)

      expect(results).toContain('element-1')
      expect(results).not.toContain('element-2')
    })

    it('应该返回空数组当没有重叠元素时', () => {
      index.insert('element-1', [[0, 0], [10, 10]])

      const bbox: Rectangle = { x: 100, y: 100, width: 10, height: 10 }
      const results = index.search(bbox)

      expect(results).toHaveLength(0)
    })
  })

  describe('searchNearby', () => {
    it('应该查询附近区域的元素', () => {
      index.insert('element-1', [[0, 0], [10, 10]])

      const results = index.searchNearby({ x: 5, y: 5 }, 20)

      expect(results).toContain('element-1')
    })
  })

  describe('clear', () => {
    it('应该清空索引', () => {
      index.insert('element-1', [[0, 0], [10, 10]])
      index.clear()

      expect(index.size()).toBe(0)
    })
  })

  describe('load', () => {
    it('应该批量插入元素', () => {
      const elements = [
        { id: 'element-1', coordinates: [[0, 0], [10, 10]] },
        { id: 'element-2', coordinates: [[20, 20], [30, 30]] },
      ]

      index.load(elements)

      expect(index.size()).toBe(2)
      expect(index.has('element-1')).toBe(true)
      expect(index.has('element-2')).toBe(true)
    })
  })

  describe('size', () => {
    it('应该返回索引中的元素数量', () => {
      expect(index.size()).toBe(0)

      index.insert('element-1', [[0, 0], [10, 10]])
      expect(index.size()).toBe(1)
    })
  })

  describe('has', () => {
    it('应该检查元素是否在索引中', () => {
      expect(index.has('element-1')).toBe(false)

      index.insert('element-1', [[0, 0], [10, 10]])
      expect(index.has('element-1')).toBe(true)
    })
  })
})
