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
      expect(bounds).toEqual({
        minX: 0,
        minY: 0,
        maxX: 800,
        maxY: 600,
      })
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
      expect(isGeometryInViewport(coordinates, viewport)).toBe(true)
      expect(isGeometryInViewport([[200, 200], [300, 300]], viewport)).toBe(false)
    })
  })
})

