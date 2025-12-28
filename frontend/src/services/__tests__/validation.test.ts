/**
 * validation Service 测试
 */

import { validateSemanticConnection } from '../validation'
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

describe('validation Service', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('validateSemanticConnection', () => {
    it('应该成功验证语义连接', async () => {
      const mockResponse = {
        status: 'success',
        data: {
          valid: true,
          source_type: 'Pipe',
          target_type: 'Valve',
          relationship: 'feeds',
          allowed_relationships: ['feeds', 'connects'],
        },
      }

      mockApiPost.mockResolvedValue(mockResponse)

      const result = await validateSemanticConnection({
        source_type: 'Pipe',
        target_type: 'Valve',
        relationship: 'feeds',
      })

      expect(mockApiPost).toHaveBeenCalledWith(
        expect.stringContaining('/validation/semantic/validate-connection'),
        expect.objectContaining({
          source_type: 'Pipe',
          target_type: 'Valve',
          relationship: 'feeds',
        })
      )
      expect(result.valid).toBe(true)
      expect(result.allowed_relationships).toContain('feeds')
    })

    it('应该处理无效的语义连接', async () => {
      const mockResponse = {
        status: 'success',
        data: {
          valid: false,
          source_type: 'Pipe',
          target_type: 'Wall',
          relationship: 'feeds',
          allowed_relationships: [],
          error: 'Pipe不能连接到Wall',
          suggestion: '请使用Connects关系',
        },
      }

      mockApiPost.mockResolvedValue(mockResponse)

      const result = await validateSemanticConnection({
        source_type: 'Pipe',
        target_type: 'Wall',
        relationship: 'feeds',
      })

      expect(result.valid).toBe(false)
      expect(result.error).toBeDefined()
      expect(result.suggestion).toBeDefined()
    })

    it('应该使用默认的relationship值', async () => {
      const mockResponse = {
        status: 'success',
        data: {
          valid: true,
          source_type: 'Pipe',
          target_type: 'Valve',
          relationship: 'feeds',
          allowed_relationships: ['feeds'],
        },
      }

      mockApiPost.mockResolvedValue(mockResponse)

      await validateSemanticConnection({
        source_type: 'Pipe',
        target_type: 'Valve',
      })

      expect(mockApiPost).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          relationship: 'feeds',
        })
      )
    })

    it('应该在验证失败时抛出错误', async () => {
      const mockResponse = {
        status: 'error',
        data: {},
      }

      mockApiPost.mockResolvedValue(mockResponse)

      await expect(
        validateSemanticConnection({
          source_type: 'Pipe',
          target_type: 'Valve',
        })
      ).rejects.toThrow('语义连接验证失败')
    })
  })
})
