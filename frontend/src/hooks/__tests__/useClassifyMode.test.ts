/**
 * useClassifyMode Hook 测试
 */

import { renderHook, act, waitFor } from '@testing-library/react'
import { useClassifyMode } from '../useClassifyMode'
import { classifyElement } from '@/services/elements'
import { useWorkbenchStore } from '@/stores/workbench'
import { ApiError } from '@/services/api'
import { TestWrapper } from '../../test-utils'

// Mock dependencies
jest.mock('@/services/elements', () => ({
  classifyElement: jest.fn(),
}))

jest.mock('@/stores/workbench', () => ({
  useWorkbenchStore: jest.fn(),
}))

const mockClassifyElement = classifyElement as jest.MockedFunction<typeof classifyElement>
const mockUseWorkbenchStore = useWorkbenchStore as jest.MockedFunction<typeof useWorkbenchStore>

describe('useClassifyMode', () => {
  const mockSelectedElementIds = ['element-1', 'element-2']
  const mockSetSelectedElementIds = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    
    mockUseWorkbenchStore.mockReturnValue({
      selectedElementIds: mockSelectedElementIds,
      setSelectedElementIds: mockSetSelectedElementIds,
    } as any)
  })

  describe('classify', () => {
    it('应该成功归类构件', async () => {
      const mockResponse = {
        element_id: 'element-1',
        item_id: 'item-1',
      }
      
      mockClassifyElement.mockResolvedValue(mockResponse)
      
      const { result } = renderHook(() => useClassifyMode(), {
        wrapper: TestWrapper,
      })
      
      act(() => {
        result.current.classify('item-1', ['element-1'])
      })
      
      await waitFor(() => {
        expect(result.current.isClassifying).toBe(false)
      })
      
      expect(mockClassifyElement).toHaveBeenCalledWith('element-1', {
        item_id: 'item-1',
      })
      expect(result.current.error).toBeNull()
      expect(result.current.successCount).toBe(1)
      expect(result.current.failedCount).toBe(0)
    })

    it('应该在归类失败时增加失败计数', async () => {
      const mockError = new ApiError('Classify failed', 404)
      mockClassifyElement.mockRejectedValue(mockError)
      
      const { result } = renderHook(() => useClassifyMode(), {
        wrapper: TestWrapper,
      })
      
      act(() => {
        result.current.classify('item-1', ['element-1'])
      })
      
      await waitFor(() => {
        expect(result.current.failedCount).toBe(1)
      })
      
      expect(result.current.error?.message).toContain('Classify failed')
      expect(result.current.successCount).toBe(0)
    })

    it('应该在归类过程中设置classifying状态', async () => {
      let resolveClassify: (value: any) => void
      const classifyPromise = new Promise((resolve) => {
        resolveClassify = resolve
      })
      
      mockClassifyElement.mockReturnValue(classifyPromise as any)
      
      const { result } = renderHook(() => useClassifyMode(), {
        wrapper: TestWrapper,
      })
      
      await act(async () => {
        result.current.classify('item-1', ['element-1'])
        // 立即检查状态应该为true
        expect(result.current.isClassifying).toBe(true)
      })
      
      await act(async () => {
        resolveClassify!({ element_id: 'element-1', item_id: 'item-1' })
        await classifyPromise
      })
      
      await waitFor(() => {
        expect(result.current.isClassifying).toBe(false)
      })
    })

    it('应该正确统计成功和失败数量', async () => {
      mockClassifyElement
        .mockResolvedValueOnce({ element_id: 'element-1', item_id: 'item-1' })
        .mockRejectedValueOnce(new ApiError('Failed', 404))
        .mockResolvedValueOnce({ element_id: 'element-3', item_id: 'item-1' })
      
      const { result } = renderHook(() => useClassifyMode(), {
        wrapper: TestWrapper,
      })
      
      act(() => {
        result.current.classify('item-1', ['element-1', 'element-2', 'element-3'])
      })
      
      await waitFor(() => {
        expect(result.current.successCount).toBe(2)
        expect(result.current.failedCount).toBe(1)
      }, { timeout: 3000 })
    })
  })

  describe('clearError', () => {
    it('应该清除错误状态', async () => {
      mockClassifyElement.mockRejectedValue(new ApiError('Test error', 500))
      
      const { result } = renderHook(() => useClassifyMode(), {
        wrapper: TestWrapper,
      })
      
      await act(async () => {
        try {
          result.current.classify('item-1', ['element-1'])
        } catch (err) {
          // Expected to throw
        }
      })
      
      await waitFor(() => {
        expect(result.current.error).not.toBeNull()
      })
      
      act(() => {
        result.current.clearError()
      })
      
      expect(result.current.error).toBeNull()
    })

    it('应该清除错误并重置计数', async () => {
      mockClassifyElement.mockResolvedValue({ element_id: 'element-1', item_id: 'item-1' })
      
      const { result } = renderHook(() => useClassifyMode(), {
        wrapper: TestWrapper,
      })
      
      await act(async () => {
        result.current.classify('item-1', ['element-1'])
      })
      
      await waitFor(() => {
        expect(result.current.successCount).toBeGreaterThan(0)
      })
      
      act(() => {
        result.current.clearError()
      })
      
      expect(result.current.successCount).toBe(0)
      expect(result.current.failedCount).toBe(0)
      expect(result.current.error).toBeNull()
    })
  })
})

