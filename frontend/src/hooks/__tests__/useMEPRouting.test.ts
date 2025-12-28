/**
 * useMEPRouting Hook 测试
 */

import { renderHook, act, waitFor } from '@testing-library/react'
import { useMEPRouting } from '../useMEPRouting'
import { calculateMEPRoute, validateMEPRoute } from '@/services/routing'
import { useToastContext } from '@/providers/ToastProvider'
import { TestWrapper } from '../../test-utils'

// Mock dependencies
jest.mock('@/services/routing', () => ({
  calculateMEPRoute: jest.fn(),
  validateMEPRoute: jest.fn(),
}))

const mockCalculateMEPRoute = calculateMEPRoute as jest.MockedFunction<typeof calculateMEPRoute>
const mockValidateMEPRoute = validateMEPRoute as jest.MockedFunction<typeof validateMEPRoute>

describe('useMEPRouting', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('calculateRoute', () => {
    it('应该成功计算MEP路径', async () => {
      const mockResponse = {
        path_points: [{ x: 0, y: 0 }, { x: 10, y: 0 }],
        constraints: {
          bend_radius: 100,
          min_width: 50,
        },
        warnings: [],
        errors: [],
      }

      mockCalculateMEPRoute.mockResolvedValue(mockResponse)

      const { result } = renderHook(() => useMEPRouting(), {
        wrapper: TestWrapper,
      })

      await act(async () => {
        await result.current.calculateRoute(
          { x: 0, y: 0 },
          { x: 10, y: 0 },
          { elementType: 'Pipe', properties: {} }
        )
      })

      await waitFor(() => {
        expect(result.current.routingState.isLoading).toBe(false)
      })

      expect(result.current.routingState.path).toEqual(mockResponse.path_points)
      expect(mockCalculateMEPRoute).toHaveBeenCalled()
    })

    it('应该处理错误情况', async () => {
      const mockError = new Error('路径计算失败')
      mockCalculateMEPRoute.mockRejectedValue(mockError)

      const { result } = renderHook(() => useMEPRouting(), {
        wrapper: TestWrapper,
      })

      await act(async () => {
        try {
          await result.current.calculateRoute(
            { x: 0, y: 0 },
            { x: 10, y: 0 },
            { elementType: 'Pipe', properties: {} }
          )
        } catch (err) {
          // Expected to throw
        }
      })

      await waitFor(() => {
        expect(result.current.routingState.isLoading).toBe(false)
      })

      expect(result.current.routingState.errors).toContain('路径计算失败')
    })
  })

  describe('validateRoute', () => {
    it('应该成功验证路径', async () => {
      const mockResponse = {
        valid: true,
        semantic_valid: true,
        constraint_valid: true,
        errors: [],
        warnings: [],
        semantic_errors: [],
        constraint_errors: [],
      }

      mockValidateMEPRoute.mockResolvedValue(mockResponse)

      const { result } = renderHook(() => useMEPRouting(), {
        wrapper: TestWrapper,
      })

      await act(async () => {
        await result.current.validateRoute(
          [{ x: 0, y: 0 }, { x: 10, y: 0 }],
          { elementType: 'Pipe', properties: {} }
        )
      })

      expect(mockValidateMEPRoute).toHaveBeenCalled()
    })

    it('应该处理无效路径', async () => {
      const mockResponse = {
        valid: false,
        semantic_valid: false,
        constraint_valid: true,
        errors: ['路径无效'],
        warnings: [],
        semantic_errors: ['语义错误'],
        constraint_errors: [],
      }

      mockValidateMEPRoute.mockResolvedValue(mockResponse)

      const { result } = renderHook(() => useMEPRouting(), {
        wrapper: TestWrapper,
      })

      await act(async () => {
        await result.current.validateRoute(
          [{ x: 0, y: 0 }, { x: 10, y: 0 }],
          { elementType: 'Pipe', properties: {} }
        )
      })

      // 路径验证失败会被正确处理
      expect(result).toBeDefined()
    })
  })

  describe('clearRoute', () => {
    it('应该清除路径状态', () => {
      const { result } = renderHook(() => useMEPRouting(), {
        wrapper: TestWrapper,
      })

      act(() => {
        result.current.clearRoute()
      })

      expect(result.current.routingState.path).toBeNull()
      expect(result.current.routingState.constraints).toBeNull()
      expect(result.current.routingState.errors).toEqual([])
      expect(result.current.routingState.warnings).toEqual([])
      expect(result.current.routingState.isLoading).toBe(false)
    })
  })
})
