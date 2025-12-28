/**
 * capacity Service 测试
 */

import { getCableTrayCapacity } from '../capacity'
import { apiGet } from '../api'
import { ApiError } from '../api'

// Mock api
jest.mock('../api', () => ({
  apiGet: jest.fn(),
  ApiError: class ApiError extends Error {
    constructor(message: string, public statusCode: number) {
      super(message)
      this.name = 'ApiError'
    }
  },
}))

const mockApiGet = apiGet as jest.MockedFunction<typeof apiGet>

describe('capacity Service', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('getCableTrayCapacity', () => {
    it('应该成功获取桥架容量', async () => {
      const mockResponse = {
        data: {
          valid: true,
          errors: [],
          warnings: [],
          power_cable_area: 1000,
          control_cable_area: 500,
          tray_cross_section: 5000,
          power_cable_ratio: 0.2,
          control_cable_ratio: 0.1,
        },
      }

      mockApiGet.mockResolvedValue(mockResponse)

      const result = await getCableTrayCapacity('tray-1')

      expect(mockApiGet).toHaveBeenCalledWith('/api/v1/routing/cable-tray/tray-1/capacity')
      expect(result).toEqual(mockResponse.data)
      expect(result.valid).toBe(true)
      expect(result.power_cable_ratio).toBe(0.2)
    })

    it('应该处理无效的桥架容量', async () => {
      const mockResponse = {
        data: {
          valid: false,
          errors: ['桥架容量超载'],
          warnings: ['建议增加桥架尺寸'],
          power_cable_area: 6000,
          control_cable_area: 3000,
          tray_cross_section: 5000,
          power_cable_ratio: 1.2,
          control_cable_ratio: 0.6,
        },
      }

      mockApiGet.mockResolvedValue(mockResponse)

      const result = await getCableTrayCapacity('tray-1')

      expect(result.valid).toBe(false)
      expect(result.errors).toContain('桥架容量超载')
    })
  })
})
