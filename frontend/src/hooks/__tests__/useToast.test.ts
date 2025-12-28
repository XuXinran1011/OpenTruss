/**
 * useToast Hook 测试
 */

import { renderHook, act } from '@testing-library/react'
import { useToast } from '../useToast'

describe('useToast', () => {
  beforeEach(() => {
    jest.useFakeTimers()
  })

  afterEach(() => {
    act(() => {
      jest.runOnlyPendingTimers()
    })
    jest.useRealTimers()
  })

  describe('showToast', () => {
    it('应该显示Toast', () => {
      const { result } = renderHook(() => useToast())
      
      act(() => {
        result.current.showToast('Test message')
      })
      
      expect(result.current.toasts).toHaveLength(1)
      expect(result.current.toasts[0].message).toBe('Test message')
      expect(result.current.toasts[0].type).toBe('info')
    })

    it('应该支持不同类型的Toast', () => {
      const { result } = renderHook(() => useToast())
      
      act(() => {
        result.current.showToast('Success', 'success')
        result.current.showToast('Error', 'error')
        result.current.showToast('Warning', 'warning')
      })
      
      expect(result.current.toasts).toHaveLength(3)
      expect(result.current.toasts[0].type).toBe('success')
      expect(result.current.toasts[1].type).toBe('error')
      expect(result.current.toasts[2].type).toBe('warning')
    })

    it('应该在指定时间后自动移除Toast', () => {
      const { result } = renderHook(() => useToast())
      
      act(() => {
        result.current.showToast('Test message', 'info', 3000)
      })
      
      expect(result.current.toasts).toHaveLength(1)
      
      act(() => {
        jest.advanceTimersByTime(3000)
      })
      
      expect(result.current.toasts).toHaveLength(0)
    })

    it('应该在duration为0时不自动移除', () => {
      const { result } = renderHook(() => useToast())
      
      act(() => {
        result.current.showToast('Test message', 'info', 0)
      })
      
      expect(result.current.toasts).toHaveLength(1)
      
      act(() => {
        jest.advanceTimersByTime(10000)
      })
      
      expect(result.current.toasts).toHaveLength(1)
    })

    it('应该返回Toast ID', () => {
      const { result } = renderHook(() => useToast())
      
      let toastId: string | undefined
      
      act(() => {
        toastId = result.current.showToast('Test message')
      })
      
      expect(toastId).toBeDefined()
      expect(result.current.toasts[0].id).toBe(toastId)
    })
  })

  describe('removeToast', () => {
    it('应该移除指定的Toast', () => {
      const { result } = renderHook(() => useToast())
      
      let toastId: string | undefined
      
      act(() => {
        toastId = result.current.showToast('Message 1')
        result.current.showToast('Message 2')
      })
      
      expect(result.current.toasts).toHaveLength(2)
      
      act(() => {
        result.current.removeToast(toastId!)
      })
      
      expect(result.current.toasts).toHaveLength(1)
      expect(result.current.toasts[0].message).toBe('Message 2')
    })

    it('应该在不存在的Toast ID时不报错', () => {
      const { result } = renderHook(() => useToast())
      
      act(() => {
        result.current.showToast('Message 1')
      })
      
      expect(result.current.toasts).toHaveLength(1)
      
      act(() => {
        result.current.removeToast('non-existent-id')
      })
      
      expect(result.current.toasts).toHaveLength(1)
    })
  })

  describe('clearAll', () => {
    it('应该清除所有Toast', () => {
      const { result } = renderHook(() => useToast())
      
      act(() => {
        result.current.showToast('Message 1')
        result.current.showToast('Message 2')
        result.current.showToast('Message 3')
      })
      
      expect(result.current.toasts).toHaveLength(3)
      
      act(() => {
        result.current.clearAll()
      })
      
      expect(result.current.toasts).toHaveLength(0)
    })
  })
})

