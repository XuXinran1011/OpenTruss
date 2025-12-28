/**
 * performance 工具函数测试
 */

import { act } from '@testing-library/react'
import { debounce, throttle, calculateViewportBounds, isPointInViewport, isGeometryInViewport } from '../performance'

// 使用fake timers
jest.useFakeTimers()

describe('performance工具函数', () => {
  beforeEach(() => {
    jest.clearAllTimers()
  })

  afterAll(() => {
    jest.useRealTimers()
  })

  describe('debounce', () => {
    it('应该在延迟后执行函数', () => {
      const fn = jest.fn()
      const debouncedFn = debounce(fn, 100)

      debouncedFn()
      expect(fn).not.toHaveBeenCalled()

      act(() => {
        jest.advanceTimersByTime(100)
      })
      expect(fn).toHaveBeenCalledTimes(1)
    })

    it('应该在延迟期间多次调用时只执行最后一次', () => {
      const fn = jest.fn()
      const debouncedFn = debounce(fn, 100)

      debouncedFn(1)
      debouncedFn(2)
      debouncedFn(3)

      act(() => {
        jest.advanceTimersByTime(100)
      })
      expect(fn).toHaveBeenCalledTimes(1)
      expect(fn).toHaveBeenCalledWith(3)
    })

    it('应该传递正确的参数', () => {
      const fn = jest.fn()
      const debouncedFn = debounce(fn, 100)

      debouncedFn('arg1', 'arg2')
      act(() => {
        jest.advanceTimersByTime(100)
      })

      expect(fn).toHaveBeenCalledWith('arg1', 'arg2')
    })
  })

  describe('throttle', () => {
    it('应该在时间间隔内只执行一次', () => {
      const fn = jest.fn()
      const throttledFn = throttle(fn, 100)

      throttledFn()
      throttledFn()
      throttledFn()

      expect(fn).toHaveBeenCalledTimes(1)

      act(() => {
        jest.advanceTimersByTime(100)
      })
      throttledFn()
      expect(fn).toHaveBeenCalledTimes(2)
    })

    it('应该在时间间隔后允许再次执行', () => {
      const fn = jest.fn()
      const throttledFn = throttle(fn, 100)

      throttledFn(1)
      act(() => {
        jest.advanceTimersByTime(50)
      })
      throttledFn(2) // 应该被忽略
      act(() => {
        jest.advanceTimersByTime(50)
      })
      throttledFn(3) // 应该执行

      expect(fn).toHaveBeenCalledTimes(2)
      expect(fn).toHaveBeenNthCalledWith(1, 1)
      expect(fn).toHaveBeenNthCalledWith(2, 3)
    })
  })

  describe('calculateViewportBounds', () => {
    it('应该正确计算视口边界框', () => {
      const bounds = calculateViewportBounds(800, 600, { x: 0, y: 0, scale: 1 })
      // 根据公式: minX = (-tx) / scale, maxX = (width - tx) / scale
      expect(bounds.minX).toBe(0)
      expect(bounds.minY).toBe(0)
      expect(bounds.maxX).toBe(800)
      expect(bounds.maxY).toBe(600)
    })

    it('应该正确处理平移和缩放', () => {
      const bounds = calculateViewportBounds(800, 600, { x: 100, y: 50, scale: 2 })
      expect(bounds.minX).toBe(-50)
      expect(bounds.minY).toBe(-25)
      expect(bounds.maxX).toBe(350)
      expect(bounds.maxY).toBe(275)
    })
  })

  describe('isPointInViewport', () => {
    it('应该正确判断点是否在视口内', () => {
      const viewport = { minX: 0, minY: 0, maxX: 100, maxY: 100 }
      expect(isPointInViewport(50, 50, viewport)).toBe(true)
      expect(isPointInViewport(150, 150, viewport)).toBe(false)
    })
  })

  describe('isGeometryInViewport', () => {
    it('应该正确判断几何图形是否在视口内', () => {
      const viewport = { minX: 0, minY: 0, maxX: 100, maxY: 100 }
      const coordinates = [[10, 10], [20, 20]]
      expect(isGeometryInViewport(coordinates, viewport, 0)).toBe(true)
      expect(isGeometryInViewport([[200, 200], [300, 300]], viewport, 0)).toBe(false)
    })

    it('应该考虑padding参数', () => {
      const viewport = { minX: 0, minY: 0, maxX: 100, maxY: 100 }
      const coordinates = [[105, 105], [110, 110]]
      // 在padding内，应该返回true
      expect(isGeometryInViewport(coordinates, viewport, 10)).toBe(true)
      // 没有padding，应该返回false
      expect(isGeometryInViewport(coordinates, viewport, 0)).toBe(false)
    })

    it('应该处理部分在视口内的几何图形', () => {
      const viewport = { minX: 0, minY: 0, maxX: 100, maxY: 100 }
      const coordinates = [[50, 50], [150, 150]]
      expect(isGeometryInViewport(coordinates, viewport, 0)).toBe(true)
    })

    it('应该处理空坐标数组', () => {
      const viewport = { minX: 0, minY: 0, maxX: 100, maxY: 100 }
      expect(isGeometryInViewport([], viewport, 0)).toBe(false)
    })
  })

  describe('isPointInViewport', () => {
    it('应该处理边界点', () => {
      const viewport = { minX: 0, minY: 0, maxX: 100, maxY: 100 }
      expect(isPointInViewport(0, 0, viewport)).toBe(true)
      expect(isPointInViewport(100, 100, viewport)).toBe(true)
      expect(isPointInViewport(50, 50, viewport)).toBe(true)
      expect(isPointInViewport(-1, 0, viewport)).toBe(false)
      expect(isPointInViewport(0, -1, viewport)).toBe(false)
      expect(isPointInViewport(101, 50, viewport)).toBe(false)
      expect(isPointInViewport(50, 101, viewport)).toBe(false)
    })
  })
})

