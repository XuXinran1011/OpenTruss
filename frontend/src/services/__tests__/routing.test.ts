/**
 * routing Service 测试
 */

import {
  calculateMEPRoute,
  validateMEPRoute,
  batchPlanRoutes,
  completeRoutingPlanning,
  revertRoutingPlanning,
  coordinateLayout,
} from '../routing'
import { apiPost } from '../api'
import { ApiError } from '../api'

// Mock api
jest.mock('../api', () => ({
  apiPost: jest.fn(),
  ApiError: class ApiError extends Error {
    constructor(message: string, public statusCode: number) {
      super(message)
      this.name = 'ApiError'
    }
  },
}))

const mockApiPost = apiPost as jest.MockedFunction<typeof apiPost>

describe('routing Service', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('calculateMEPRoute', () => {
    it('应该成功计算MEP路径', async () => {
      const mockResponse = {
        status: 'success',
        data: {
          path_points: [[0, 0], [10, 0], [20, 0]],
          constraints: {
            bend_radius: 100,
            min_width: 50,
          },
          warnings: [],
          errors: [],
        },
      }

      mockApiPost.mockResolvedValue(mockResponse)

      const result = await calculateMEPRoute(
        { x: 0, y: 0 },
        { x: 20, y: 0 },
        {
          elementType: 'Pipe',
          properties: { diameter: 100 },
        }
      )

      expect(mockApiPost).toHaveBeenCalledWith(
        '/routing/calculate',
        expect.objectContaining({
          start: [0, 0],
          end: [20, 0],
          element_type: 'Pipe',
        })
      )
      expect(result.path_points).toHaveLength(3)
      expect(result.path_points[0]).toEqual({ x: 0, y: 0 })
    })

    it('应该在计算失败时抛出错误', async () => {
      const mockResponse = {
        status: 'error',
        data: {},
      }

      mockApiPost.mockResolvedValue(mockResponse)

      await expect(
        calculateMEPRoute(
          { x: 0, y: 0 },
          { x: 20, y: 0 },
          { elementType: 'Pipe', properties: {} }
        )
      ).rejects.toThrow('路径计算失败')
    })
  })

  describe('validateMEPRoute', () => {
    it('应该成功验证MEP路径', async () => {
      const mockResponse = {
        status: 'success',
        data: {
          valid: true,
          semantic_valid: true,
          constraint_valid: true,
          errors: [],
          warnings: [],
          semantic_errors: [],
          constraint_errors: [],
        },
      }

      mockApiPost.mockResolvedValue(mockResponse)

      const result = await validateMEPRoute(
        [{ x: 0, y: 0 }, { x: 20, y: 0 }],
        { elementType: 'Pipe', properties: {} }
      )

      expect(result.valid).toBe(true)
    })
  })

  describe('batchPlanRoutes', () => {
    it('应该成功批量规划路由', async () => {
      const mockResponse = {
        status: 'success',
        data: {
          results: [
            {
              path_points: [[0, 0], [10, 0]],
              constraints: {},
              warnings: [],
              errors: [],
            },
          ],
          total: 1,
          success_count: 1,
          failure_count: 0,
        },
      }

      mockApiPost.mockResolvedValue(mockResponse)

      const result = await batchPlanRoutes([
        {
          start: { x: 0, y: 0 },
          end: { x: 10, y: 0 },
          constraints: { elementType: 'Pipe', properties: {} },
        },
      ])

      expect(result.success_count).toBe(1)
      expect(result.results).toHaveLength(1)
    })
  })

  describe('completeRoutingPlanning', () => {
    it('应该成功完成路由规划', async () => {
      const mockResponse = {
        status: 'success',
        data: {
          updated_count: 2,
          total_count: 2,
          element_ids: ['element-1', 'element-2'],
        },
      }

      mockApiPost.mockResolvedValue(mockResponse)

      const result = await completeRoutingPlanning(['element-1', 'element-2'])

      expect(result.updated_count).toBe(2)
      expect(result.element_ids).toHaveLength(2)
    })
  })

  describe('revertRoutingPlanning', () => {
    it('应该成功退回路由规划', async () => {
      const mockResponse = {
        status: 'success',
        data: {
          updated_count: 1,
          total_count: 1,
          element_ids: ['element-1'],
        },
      }

      mockApiPost.mockResolvedValue(mockResponse)

      const result = await revertRoutingPlanning(['element-1'])

      expect(result.updated_count).toBe(1)
    })
  })

  describe('coordinateLayout', () => {
    it('应该成功进行管线综合排布', async () => {
      const mockResponse = {
        status: 'success',
        data: {
          adjusted_elements: [
            {
              element_id: 'element-1',
              original_path: [[0, 0], [10, 0]],
              adjusted_path: [[0, 0], [10, 0]],
              adjustment_type: 'horizontal_translation',
              adjustment_reason: '避免碰撞',
            },
          ],
          collisions_resolved: 1,
          warnings: [],
          errors: [],
        },
      }

      mockApiPost.mockResolvedValue(mockResponse)

      const result = await coordinateLayout('level-1', ['element-1'])

      expect(result.collisions_resolved).toBe(1)
      expect(result.adjusted_elements).toHaveLength(1)
    })
  })
})
