/**
 * spatial Service 测试
 */

import {
  setSpaceIntegratedHanger,
  getSpaceIntegratedHanger,
} from '../spatial'
import { apiGet, apiPut } from '../api'
import { ApiError } from '../api'

// Mock api
jest.mock('../api', () => ({
  apiGet: jest.fn(),
  apiPut: jest.fn(),
  ApiError: class ApiError extends Error {
    constructor(message: string, public statusCode: number) {
      super(message)
      this.name = 'ApiError'
    }
  },
}))

const mockApiGet = apiGet as jest.MockedFunction<typeof apiGet>
const mockApiPut = apiPut as jest.MockedFunction<typeof apiPut>

describe('spatial Service', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('setSpaceIntegratedHanger', () => {
    it('应该成功设置空间综合支吊架', async () => {
      const mockResponse = {
        data: {
          space_id: 'space-1',
          use_integrated_hanger: true,
          updated_at: '2024-01-01T00:00:00Z',
        },
      }

      mockApiPut.mockResolvedValue(mockResponse)

      const result = await setSpaceIntegratedHanger('space-1', {
        use_integrated_hanger: true,
      })

      expect(mockApiPut).toHaveBeenCalledWith(
        '/api/v1/spaces/space-1/integrated-hanger',
        { use_integrated_hanger: true }
      )
      expect(result).toEqual(mockResponse.data)
      expect(result.use_integrated_hanger).toBe(true)
    })
  })

  describe('getSpaceIntegratedHanger', () => {
    it('应该成功获取空间综合支吊架配置', async () => {
      const mockResponse = {
        data: {
          space_id: 'space-1',
          use_integrated_hanger: false,
          updated_at: '2024-01-01T00:00:00Z',
        },
      }

      mockApiGet.mockResolvedValue(mockResponse)

      const result = await getSpaceIntegratedHanger('space-1')

      expect(mockApiGet).toHaveBeenCalledWith(
        '/api/v1/spaces/space-1/integrated-hanger'
      )
      expect(result).toEqual(mockResponse.data)
      expect(result.use_integrated_hanger).toBe(false)
    })
  })
})
