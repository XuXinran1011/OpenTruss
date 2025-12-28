/**
 * useLiftMode Hook 测试
 */

import { renderHook, act, waitFor } from '@testing-library/react'
import { useLiftMode } from '../useLiftMode'
import { batchLiftElements } from '@/services/elements'
import { useWorkbenchStore } from '@/stores/workbench'
import { ApiError } from '@/services/api'
import { TestWrapper } from '@/test-utils'

// Mock dependencies
jest.mock('@/services/elements', () => ({
  batchLiftElements: jest.fn(),
}))

jest.mock('@/stores/workbench', () => ({
  useWorkbenchStore: jest.fn(),
}))

const mockBatchLiftElements = batchLiftElements as jest.MockedFunction<typeof batchLiftElements>
const mockUseWorkbenchStore = useWorkbenchStore as jest.MockedFunction<typeof useWorkbenchStore>

describe('useLiftMode', () => {
  const mockSelectedElementIds = ['element-1', 'element-2']
  const mockSetSelectedElementIds = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    
    mockUseWorkbenchStore.mockReturnValue({
      selectedElementIds: mockSelectedElementIds,
      setSelectedElementIds: mockSetSelectedElementIds,
    } as any)
  })

  describe('batchLift', () => {
    it('应该成功批量更新Z轴参数', async () => {
      const mockResponse = {
        updated_count: 2,
        element_ids: ['element-1', 'element-2'],
      }
      
      mockBatchLiftElements.mockResolvedValue(mockResponse)
      
      const { result } = renderHook(() => useLiftMode(), { wrapper: TestWrapper })
      
      await act(async () => {
        result.current.batchLift(3.5, 0.1)
      })
      
      expect(mockBatchLiftElements).toHaveBeenCalledWith({
        element_ids: ['element-1', 'element-2'],
        height: 3.5,
        base_offset: 0.1,
      })
      expect(result.current.error).toBeNull()
    })

    it('应该在部分更新失败时设置警告错误', async () => {
      const mockResponse = {
        updated_count: 1,
        element_ids: ['element-1'], // 只有1个成功，2个失败
      }
      
      mockBatchLiftElements.mockResolvedValue(mockResponse)
      
      const { result } = renderHook(() => useLiftMode(), { wrapper: TestWrapper })
      
      await act(async () => {
        result.current.batchLift(3.5)
      })
      
      await waitFor(() => {
        expect(result.current.error).not.toBeNull()
      })
      
      expect(result.current.error?.message).toContain('成功更新 1 个构件')
      expect(result.current.error?.elementIds).toEqual(['element-2'])
    })

    it('应该在全部更新失败时设置错误', async () => {
      const mockError = new ApiError('Batch update failed', 500)
      mockBatchLiftElements.mockRejectedValue(mockError)
      
      const { result } = renderHook(() => useLiftMode(), { wrapper: TestWrapper })
      
      await act(async () => {
        try {
          result.current.batchLift(3.5)
        } catch (err) {
          // Expected to throw
        }
      })
      
      await waitFor(() => {
        expect(result.current.error).not.toBeNull()
      })
      
      expect(result.current.error?.message).toContain('Batch update failed')
    })

    it('应该在更新过程中设置lifting状态', async () => {
      let resolveLift: (value: any) => void
      const liftPromise = new Promise((resolve) => {
        resolveLift = resolve
      })
      
      mockBatchLiftElements.mockReturnValue(liftPromise as any)
      
      const { result } = renderHook(() => useLiftMode(), { wrapper: TestWrapper })
      
      await act(async () => {
        result.current.batchLift(3.5)
        // 立即检查状态应该为true
        expect(result.current.isLifting).toBe(true)
      })
      
      await act(async () => {
        resolveLift!({ updated_count: 1, element_ids: ['element-1'] })
        await liftPromise
      })
      
      await waitFor(() => {
        expect(result.current.isLifting).toBe(false)
      })
    })
  })

  describe('clearError', () => {
    it('应该清除错误状态', async () => {
      mockBatchLiftElements.mockRejectedValue(new ApiError('Test error', 500))
      
      const { result } = renderHook(() => useLiftMode(), { wrapper: TestWrapper })
      
      await act(async () => {
        try {
          result.current.batchLift(3.5)
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
  })
})

