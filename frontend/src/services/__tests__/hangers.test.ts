/**
 * hangers Service 测试
 */

import {
  generateHangers,
  generateIntegratedHangers,
  getElementHangers,
} from '../hangers'
import { apiGet, apiPost } from '../api'
import { ApiError } from '../api'

// Mock api
jest.mock('../api', () => ({
  apiGet: jest.fn(),
  apiPost: jest.fn(),
  ApiError: class ApiError extends Error {
    constructor(message: string, public statusCode: number) {
      super(message)
      this.name = 'ApiError'
    }
  },
}))

const mockApiGet = apiGet as jest.MockedFunction<typeof apiGet>
const mockApiPost = apiPost as jest.MockedFunction<typeof apiPost>

describe('hangers Service', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('generateHangers', () => {
    it('应该成功生成支吊架', async () => {
      const mockResponse = {
        data: {
          generated_hangers: [
            {
              id: 'hanger-1',
              position: [0, 0, 3],
              hanger_type: '吊架',
              standard_code: 'GB/T 17116.1',
              detail_code: 'H-001',
              support_interval: 3000,
            },
          ],
          warnings: [],
          errors: [],
        },
      }

      mockApiPost.mockResolvedValue(mockResponse)

      const result = await generateHangers({
        element_ids: ['element-1'],
        seismic_grade: '7度',
      })

      expect(mockApiPost).toHaveBeenCalledWith(
        '/api/v1/hangers/generate',
        expect.objectContaining({
          element_ids: ['element-1'],
          seismic_grade: '7度',
        })
      )
      expect(result).toEqual(mockResponse.data)
      expect(result.generated_hangers).toHaveLength(1)
    })
  })

  describe('generateIntegratedHangers', () => {
    it('应该成功生成综合支吊架', async () => {
      const mockResponse = {
        data: {
          generated_integrated_hangers: [
            {
              id: 'integrated-hanger-1',
              position: [0, 0, 3],
              hanger_type: '吊架',
              standard_code: 'GB/T 17116.1',
              detail_code: 'IH-001',
              supported_element_ids: ['element-1', 'element-2'],
              space_id: 'space-1',
            },
          ],
          warnings: [],
          errors: [],
        },
      }

      mockApiPost.mockResolvedValue(mockResponse)

      const result = await generateIntegratedHangers({
        space_id: 'space-1',
        element_ids: ['element-1', 'element-2'],
        seismic_grade: '7度',
      })

      expect(mockApiPost).toHaveBeenCalledWith(
        '/api/v1/hangers/generate-integrated',
        expect.objectContaining({
          space_id: 'space-1',
          element_ids: ['element-1', 'element-2'],
        })
      )
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('getElementHangers', () => {
    it('应该成功查询元素的支吊架', async () => {
      const mockResponse = {
        data: {
          hangers: [
            {
              id: 'hanger-1',
              position: [0, 0, 3],
              hanger_type: '吊架',
              standard_code: 'GB/T 17116.1',
              detail_code: 'H-001',
            },
          ],
          integrated_hangers: [],
        },
      }

      mockApiGet.mockResolvedValue(mockResponse)

      const result = await getElementHangers('element-1')

      expect(mockApiGet).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/hangers/query')
      )
      expect(result).toEqual(mockResponse.data)
    })

    it('应该支持通过spaceId查询', async () => {
      const mockResponse = {
        data: {
          hangers: [],
          integrated_hangers: [
            {
              id: 'integrated-hanger-1',
              position: [0, 0, 3],
              hanger_type: '吊架',
              standard_code: 'GB/T 17116.1',
              detail_code: 'IH-001',
              supported_element_ids: ['element-1'],
              space_id: 'space-1',
            },
          ],
        },
      }

      mockApiGet.mockResolvedValue(mockResponse)

      const result = await getElementHangers(undefined, 'space-1')

      expect(mockApiGet).toHaveBeenCalledWith(
        expect.stringContaining('space_id=space-1')
      )
      expect(result.integrated_hangers).toHaveLength(1)
    })
  })
})
