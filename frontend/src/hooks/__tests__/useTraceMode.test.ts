/**
 * useTraceMode Hook 测试
 */

import { renderHook, act, waitFor } from '@testing-library/react'
import { useTraceMode } from '../useTraceMode'
import { updateElementTopology } from '@/services/elements'
import { useWorkbenchStore } from '@/stores/workbench'
import { ApiError } from '@/services/api'
import { TestWrapper } from '../../test-utils'

// Mock dependencies
jest.mock('@/services/elements', () => ({
  updateElementTopology: jest.fn(),
}))

jest.mock('@/stores/workbench', () => ({
  useWorkbenchStore: jest.fn(),
}))

const mockUpdateElementTopology = updateElementTopology as jest.MockedFunction<typeof updateElementTopology>
const mockUseWorkbenchStore = useWorkbenchStore as jest.MockedFunction<typeof useWorkbenchStore>

describe('useTraceMode', () => {
  const mockSelectedElementIds = ['element-1', 'element-2']
  const mockSetSelectedElementIds = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    
    mockUseWorkbenchStore.mockReturnValue({
      selectedElementIds: mockSelectedElementIds,
      setSelectedElementIds: mockSetSelectedElementIds,
    } as any)
  })

  describe('updateTopology', () => {
    it('应该成功更新拓扑关系', async () => {
      const mockResponse = {
        id: 'element-1',
        updated: true,
      }
      
      mockUpdateElementTopology.mockResolvedValue(mockResponse)
      
      const { result } = renderHook(() => useTraceMode(), {
        wrapper: TestWrapper,
      })
      
      act(() => {
        result.current.updateTopology('element-1', {
          geometry: {
            type: 'Polyline',
            coordinates: [[0, 0], [10, 0]],
          },
        })
      })
      
      await waitFor(() => {
        expect(result.current.isUpdating).toBe(false)
      })
      
      expect(mockUpdateElementTopology).toHaveBeenCalledWith('element-1', {
        geometry: {
          type: 'Polyline',
          coordinates: [[0, 0, 0], [10, 0, 0]], // 3D 坐标
        },
      })
      expect(result.current.error).toBeNull()
    })

    it('应该在更新失败时设置错误', async () => {
      const mockError = new ApiError('Update failed', 500)
      mockUpdateElementTopology.mockRejectedValue(mockError)
      
      const { result } = renderHook(() => useTraceMode(), {
        wrapper: TestWrapper,
      })
      
      await act(async () => {
        try {
          await result.current.updateTopology('element-1', {
            geometry: {
              type: 'Polyline',
              coordinates: [[0, 0], [10, 0]],
            },
          })
        } catch (err) {
          // Expected to throw
        }
      })
      
      await waitFor(() => {
        expect(result.current.error).not.toBeNull()
      })
      
      expect(result.current.error?.message).toContain('Update failed')
      expect(result.current.error?.elementId).toBe('element-1')
    })

    it('应该在更新过程中设置tracing状态', async () => {
      let resolveUpdate: (value: any) => void
      const updatePromise = new Promise((resolve) => {
        resolveUpdate = resolve
      })
      
      mockUpdateElementTopology.mockReturnValue(updatePromise as any)
      
      const { result } = renderHook(() => useTraceMode(), {
        wrapper: TestWrapper,
      })
      
      await act(async () => {
        result.current.updateTopology('element-1', {
          geometry: {
            type: 'Polyline',
            coordinates: [[0, 0], [10, 0]],
          },
        })
        // 立即检查状态应该为true
        expect(result.current.isUpdating).toBe(true)
      })
      
      await act(async () => {
        resolveUpdate!({ id: 'element-1', updated: true })
        await updatePromise
      })
      
      await waitFor(() => {
        expect(result.current.isUpdating).toBe(false)
      })
    })
  })

  describe('clearError', () => {
    it('应该清除错误状态', async () => {
      mockUpdateElementTopology.mockRejectedValue(new ApiError('Test error', 500))
      
      const { result } = renderHook(() => useTraceMode(), {
        wrapper: TestWrapper,
      })
      
      act(() => {
        result.current.updateTopology('element-1', {
          geometry: {
            type: 'Polyline',
            coordinates: [[0, 0], [10, 0]],
          },
        })
      })
      
      await waitFor(() => {
        expect(result.current.error).not.toBeNull()
      }, { timeout: 3000 })
      
      act(() => {
        result.current.clearError()
      })
      
      await waitFor(() => {
        expect(result.current.error).toBeNull()
      })
    })
  })
})

