/**
 * useCoordination Hook 测试
 */

import { renderHook, act, waitFor } from '@testing-library/react'
import { useCoordination } from '../useCoordination'
import { coordinateLayout } from '@/services/routing'
import { useToastContext } from '@/providers/ToastProvider'
import { TestWrapper } from '../../test-utils'

// Mock dependencies
jest.mock('@/services/routing', () => ({
  coordinateLayout: jest.fn(),
}))

const mockCoordinateLayout = coordinateLayout as jest.MockedFunction<typeof coordinateLayout>

describe('useCoordination', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('应该成功进行管线综合排布', async () => {
    const mockResponse = {
      adjusted_elements: [
        {
          element_id: 'element-1',
          original_path: [[0, 0], [10, 0]],
          adjusted_path: [[0, 0], [10, 0]],
          adjustment_type: 'horizontal_translation' as const,
          adjustment_reason: '避免碰撞',
        },
      ],
      collisions_resolved: 1,
      warnings: [],
      errors: [],
    }

    mockCoordinateLayout.mockResolvedValue(mockResponse)

    const { result } = renderHook(() => useCoordination(), {
      wrapper: TestWrapper,
    })

    await act(async () => {
      await result.current.coordinate('level-1', ['element-1'])
    })

    await waitFor(() => {
      expect(result.current.coordinationState.isLoading).toBe(false)
    })

    expect(result.current.coordinationState.result).toEqual(mockResponse)
  })

  it('应该处理错误情况', async () => {
    const mockError = new Error('排布失败')
    mockCoordinateLayout.mockRejectedValue(mockError)

    const { result } = renderHook(() => useCoordination(), {
      wrapper: TestWrapper,
    })

    await act(async () => {
      try {
        await result.current.coordinate('level-1')
      } catch (err) {
        // Expected to throw
      }
    })

    await waitFor(() => {
      expect(result.current.coordinationState.isLoading).toBe(false)
    })

    expect(result.current.coordinationState.error).toBe('排布失败')
  })

  it('应该清除结果', () => {
    const { result } = renderHook(() => useCoordination(), {
      wrapper: TestWrapper,
    })

    act(() => {
      result.current.clearResult()
    })

    expect(result.current.coordinationState.result).toBeNull()
    expect(result.current.coordinationState.error).toBeNull()
    expect(result.current.coordinationState.isLoading).toBe(false)
  })
})
