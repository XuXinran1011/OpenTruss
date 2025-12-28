/**
 * geometry3d 工具函数测试
 */

import {
  point2dTo3d,
  geometryTo3d,
  geometry2dTo3d,
  isometricProjection,
  calculate3dBoundingBox,
  calculateProjectedBoundingBox,
} from '../geometry3d'
import { Geometry } from '@/types'

describe('geometry3d utils', () => {
  describe('point2dTo3d', () => {
    it('应该将2D坐标转换为3D坐标', () => {
      const result = point2dTo3d(10, 20, 5, 3)
      expect(result).toEqual({ x: 10, y: 20, z: 5 })
    })

    it('应该使用默认值', () => {
      const result = point2dTo3d(10, 20)
      expect(result).toEqual({ x: 10, y: 20, z: 0 })
    })
  })

  describe('geometryTo3d', () => {
    it('应该将2D几何图形转换为3D坐标数组', () => {
      const geometry: Geometry = {
        type: 'Polyline',
        coordinates: [[0, 0], [10, 0], [10, 10]],
      }

      const result = geometryTo3d(geometry, 5)

      expect(result).toHaveLength(3)
      expect(result[0]).toEqual({ x: 0, y: 0, z: 5 })
      expect(result[1]).toEqual({ x: 10, y: 0, z: 5 })
      expect(result[2]).toEqual({ x: 10, y: 10, z: 5 })
    })

    it('应该处理已有Z坐标的3D几何图形', () => {
      const geometry: Geometry = {
        type: 'Polyline',
        coordinates: [[0, 0, 5], [10, 0, 10], [10, 10, 15]],
      }

      const result = geometryTo3d(geometry, 0)

      expect(result[0]).toEqual({ x: 0, y: 0, z: 5 })
      expect(result[1]).toEqual({ x: 10, y: 0, z: 10 })
      expect(result[2]).toEqual({ x: 10, y: 10, z: 15 })
    })

    it('应该在坐标长度无效时抛出错误', () => {
      const geometry: Geometry = {
        type: 'Polyline',
        coordinates: [[0] as any],
      }

      expect(() => geometryTo3d(geometry)).toThrow('Invalid coordinate length')
    })
  })

  describe('geometry2dTo3d', () => {
    it('应该调用geometryTo3d', () => {
      const geometry: Geometry = {
        type: 'Polyline',
        coordinates: [[0, 0], [10, 0]],
      }

      const result = geometry2dTo3d(geometry, 5)
      expect(result).toHaveLength(2)
      expect(result[0].z).toBe(5)
    })
  })

  describe('isometricProjection', () => {
    it('应该正确进行等轴测投影', () => {
      const point = { x: 10, y: 10, z: 5 }
      const result = isometricProjection(point)

      expect(result).toHaveProperty('x')
      expect(result).toHaveProperty('y')
      expect(typeof result.x).toBe('number')
      expect(typeof result.y).toBe('number')
    })

    it('应该支持缩放', () => {
      const point = { x: 10, y: 10, z: 5 }
      const result = isometricProjection(point, 2)

      expect(result.x).toBeCloseTo(isometricProjection(point, 1).x * 2, 5)
      expect(result.y).toBeCloseTo(isometricProjection(point, 1).y * 2, 5)
    })
  })

  describe('calculate3dBoundingBox', () => {
    it('应该计算3D边界框', () => {
      const points = [
        { x: 0, y: 0, z: 0 },
        { x: 10, y: 20, z: 5 },
        { x: 5, y: 10, z: 10 },
      ]

      const result = calculate3dBoundingBox(points)

      expect(result.minX).toBe(0)
      expect(result.minY).toBe(0)
      expect(result.minZ).toBe(0)
      expect(result.maxX).toBe(10)
      expect(result.maxY).toBe(20)
      expect(result.maxZ).toBe(10)
    })

    it('应该处理空数组', () => {
      const result = calculate3dBoundingBox([])

      expect(result.minX).toBe(0)
      expect(result.minY).toBe(0)
      expect(result.minZ).toBe(0)
      expect(result.maxX).toBe(0)
      expect(result.maxY).toBe(0)
      expect(result.maxZ).toBe(0)
    })
  })

  describe('calculateProjectedBoundingBox', () => {
    it('应该计算投影后的边界框', () => {
      const points = [
        { x: 0, y: 0, z: 0 },
        { x: 10, y: 10, z: 5 },
      ]

      const result = calculateProjectedBoundingBox(points)

      expect(result).toHaveProperty('minX')
      expect(result).toHaveProperty('minY')
      expect(result).toHaveProperty('maxX')
      expect(result).toHaveProperty('maxY')
      expect(result).toHaveProperty('width')
      expect(result).toHaveProperty('height')
      expect(result.width).toBeGreaterThanOrEqual(0)
      expect(result.height).toBeGreaterThanOrEqual(0)
    })

    it('应该处理空数组', () => {
      const result = calculateProjectedBoundingBox([])

      expect(result.minX).toBe(0)
      expect(result.minY).toBe(0)
      expect(result.maxX).toBe(0)
      expect(result.maxY).toBe(0)
      expect(result.width).toBe(0)
      expect(result.height).toBe(0)
    })
  })
})
