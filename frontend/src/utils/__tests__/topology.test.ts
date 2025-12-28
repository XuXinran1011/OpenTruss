/**
 * topology 工具函数测试
 */

import {
  distance,
  snapToPoint,
  snapToGrid,
  lineIntersection,
  pointInPolygon,
  getGeometryEndpoints,
  findNearestSnapPoint,
  nearestPointOnLine,
  createRectangle,
  pointInRectangle,
  getGeometryBoundingBox,
} from '../topology'

describe('topology工具函数', () => {
  describe('distance', () => {
    it('应该正确计算两点之间的距离', () => {
      expect(distance(0, 0, 3, 4)).toBe(5) // 3-4-5 triangle
      expect(distance(0, 0, 0, 0)).toBe(0)
      expect(distance(1, 1, 4, 5)).toBeCloseTo(5, 5)
    })
  })

  describe('snapToPoint', () => {
    it('应该在距离内时吸附到目标点', () => {
      const result = snapToPoint({ x: 1, y: 1 }, { x: 2, y: 2 }, 5)
      expect(result).toEqual({ x: 2, y: 2, snapped: true })
    })

    it('应该在距离外时不吸附', () => {
      const result = snapToPoint({ x: 0, y: 0 }, { x: 100, y: 100 }, 5)
      expect(result).toBeNull()
    })
  })

  describe('snapToGrid', () => {
    it('应该将点吸附到网格', () => {
      const result = snapToGrid({ x: 23, y: 47 }, 20)
      expect(result).toEqual({ x: 20, y: 40 })
    })

    it('应该正确处理负坐标', () => {
      const result = snapToGrid({ x: -23, y: -47 }, 20)
      expect(result).toEqual({ x: -20, y: -40 })
    })
  })

  describe('lineIntersection', () => {
    it('应该正确计算两条线段的交点', () => {
      const result = lineIntersection(
        { x: 0, y: 0 },
        { x: 2, y: 2 },
        { x: 0, y: 2 },
        { x: 2, y: 0 }
      )
      expect(result).toEqual({ x: 1, y: 1 })
    })

    it('应该在平行线时返回null', () => {
      const result = lineIntersection(
        { x: 0, y: 0 },
        { x: 2, y: 0 },
        { x: 0, y: 2 },
        { x: 2, y: 2 }
      )
      expect(result).toBeNull()
    })
  })

  describe('pointInPolygon', () => {
    it('应该正确判断点在多边形内', () => {
      const polygon = [
        [0, 0],
        [10, 0],
        [10, 10],
        [0, 10],
      ]
      expect(pointInPolygon({ x: 5, y: 5 }, polygon)).toBe(true)
      expect(pointInPolygon({ x: 15, y: 15 }, polygon)).toBe(false)
    })
  })

  describe('getGeometryEndpoints', () => {
    it('应该正确获取几何体的端点', () => {
      const coordinates = [
        [0, 0],
        [10, 0],
        [10, 10],
        [0, 10],
      ]
      const endpoints = getGeometryEndpoints(coordinates)
      expect(endpoints).toHaveLength(2)
      expect(endpoints[0]).toEqual({ x: 0, y: 0 })
      expect(endpoints[1]).toEqual({ x: 0, y: 10 })
    })
  })

  describe('findNearestSnapPoint', () => {
    it('应该找到最近的吸附点', () => {
      const snapPoints = [
        { x: 10, y: 10 },
        { x: 100, y: 100 },
      ]
      const result = findNearestSnapPoint({ x: 5, y: 5 }, snapPoints, 20)
      expect(result).not.toBeNull()
      expect(result?.x).toBe(10)
      expect(result?.y).toBe(10)
    })

    it('应该在距离外时返回null', () => {
      const snapPoints = [
        { x: 100, y: 100 },
      ]
      const result = findNearestSnapPoint({ x: 0, y: 0 }, snapPoints, 20)
      expect(result).toBeNull()
    })

    it('应该处理空数组', () => {
      const result = findNearestSnapPoint({ x: 0, y: 0 }, [], 20)
      expect(result).toBeNull()
    })

    it('应该选择距离最近的点', () => {
      const snapPoints = [
        { x: 50, y: 50 },
        { x: 10, y: 10 },
        { x: 30, y: 30 },
      ]
      const result = findNearestSnapPoint({ x: 5, y: 5 }, snapPoints, 100)
      expect(result).not.toBeNull()
      expect(result?.x).toBe(10)
      expect(result?.y).toBe(10)
    })
  })

  describe('nearestPointOnLine', () => {
    it('应该找到线段上最近的点', () => {
      const result = nearestPointOnLine(
        { x: 5, y: 5 },
        { x: 0, y: 0 },
        { x: 10, y: 0 }
      )
      expect(result).toEqual({ x: 5, y: 0, distance: 5 })
    })
  })

  describe('createRectangle', () => {
    it('应该正确创建矩形', () => {
      const rect = createRectangle(0, 0, 10, 10)
      expect(rect).toEqual({
        x: 0,
        y: 0,
        width: 10,
        height: 10,
      })
    })

    it('应该处理反向坐标', () => {
      const rect = createRectangle(10, 10, 0, 0)
      expect(rect).toEqual({
        x: 0,
        y: 0,
        width: 10,
        height: 10,
      })
    })
  })

  describe('pointInRectangle', () => {
    it('应该正确判断点在矩形内', () => {
      const rect = { x: 0, y: 0, width: 10, height: 10 }
      expect(pointInRectangle({ x: 5, y: 5 }, rect)).toBe(true)
      expect(pointInRectangle({ x: 15, y: 15 }, rect)).toBe(false)
    })
  })

  describe('findNearestSnapPointWithElement', () => {
    it('应该找到最近的吸附点并包含元素信息', () => {
      const snapPoints = [
        { x: 10, y: 10, elementId: 'elem1', element: { id: 'elem1' } },
        { x: 100, y: 100, elementId: 'elem2', element: { id: 'elem2' } },
      ]
      const result = findNearestSnapPointWithElement({ x: 5, y: 5 }, snapPoints, 20)
      expect(result).not.toBeNull()
      expect(result?.x).toBe(10)
      expect(result?.y).toBe(10)
      expect(result?.elementId).toBe('elem1')
      expect(result?.element?.id).toBe('elem1')
    })

    it('应该在距离外时返回null', () => {
      const snapPoints = [
        { x: 100, y: 100, elementId: 'elem1', element: { id: 'elem1' } },
      ]
      const result = findNearestSnapPointWithElement({ x: 0, y: 0 }, snapPoints, 20)
      expect(result).toBeNull()
    })

    it('应该处理空数组', () => {
      const result = findNearestSnapPointWithElement({ x: 0, y: 0 }, [], 20)
      expect(result).toBeNull()
    })
  })

  describe('getGeometryBoundingBox', () => {
    it('应该正确计算几何体的边界框', () => {
      const coordinates = [
        [5, 10],
        [15, 5],
        [20, 20],
        [0, 15],
      ]
      const bbox = getGeometryBoundingBox(coordinates)
      expect(bbox).toEqual({
        x: 0,
        y: 5,
        width: 20,
        height: 15,
      })
    })

    it('应该在坐标为空时返回null', () => {
      const bbox = getGeometryBoundingBox([])
      expect(bbox).toBeNull()
    })
  })
})

