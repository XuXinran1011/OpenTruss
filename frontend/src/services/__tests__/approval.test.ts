/**
 * approval Service 测试
 */

import {
  approveLot,
  rejectLot,
  getApprovalHistory,
} from '../approval'
import { apiPost, apiGet } from '../api'
import { ApiError } from '../api'

// Mock api
jest.mock('../api', () => ({
  apiPost: jest.fn(),
  apiGet: jest.fn(),
  ApiError: class ApiError extends Error {
    constructor(message: string, public statusCode: number) {
      super(message)
      this.name = 'ApiError'
    }
  },
}))

const mockApiPost = apiPost as jest.MockedFunction<typeof apiPost>
const mockApiGet = apiGet as jest.MockedFunction<typeof apiGet>

describe('approval Service', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('approveLot', () => {
    it('应该成功审批通过检验批', async () => {
      const mockResponseData = {
        lot_id: 'lot-1',
        status: 'APPROVED',
        approved_by: 'user-1',
        approved_at: '2024-01-01T00:00:00Z',
        comment: 'Approved',
      }
      
      // apiPost returns ApiResponse<T>, and approveLot returns response.data
      mockApiPost.mockResolvedValue({ data: mockResponseData } as any)
      
      const result = await approveLot('lot-1', {
        comment: 'Approved',
      })
      
      expect(mockApiPost).toHaveBeenCalledWith('/api/v1/lots/lot-1/approve', {
        comment: 'Approved',
      })
      expect(result).toEqual(mockResponseData)
    })
  })

  describe('rejectLot', () => {
    it('应该成功驳回检验批', async () => {
      const mockResponseData = {
        lot_id: 'lot-1',
        status: 'REJECTED',
        rejected_by: 'user-1',
        rejected_at: '2024-01-01T00:00:00Z',
        reason: 'Invalid data',
        reject_level: 'PLANNING',
      }
      
      // apiPost returns ApiResponse<T>, and rejectLot returns response.data
      mockApiPost.mockResolvedValue({ data: mockResponseData } as any)
      
      const result = await rejectLot('lot-1', {
        reason: 'Invalid data',
        reject_level: 'PLANNING',
      })
      
      expect(mockApiPost).toHaveBeenCalledWith('/api/v1/lots/lot-1/reject', {
        reason: 'Invalid data',
        reject_level: 'PLANNING',
      })
      expect(result).toEqual(mockResponseData)
    })
  })

  describe('getApprovalHistory', () => {
    it('应该成功获取审批历史', async () => {
      const mockResponseData = {
        lot_id: 'lot-1',
        history: [
          {
            action: 'APPROVE',
            user_id: 'user-1',
            comment: 'Approved',
            old_status: 'SUBMITTED',
            new_status: 'APPROVED',
            timestamp: '2024-01-01T00:00:00Z',
          },
        ],
      }
      
      // apiGet returns ApiResponse<T>, and getApprovalHistory returns response.data
      mockApiGet.mockResolvedValue({ data: mockResponseData } as any)
      
      const result = await getApprovalHistory('lot-1')
      
      expect(mockApiGet).toHaveBeenCalledWith('/api/v1/lots/lot-1/approval-history')
      expect(result).toEqual(mockResponseData)
    })
  })

  describe('错误处理', () => {
    it('应该在API调用失败时抛出错误', async () => {
      const mockError = new ApiError('Unauthorized', 401)
      mockApiPost.mockRejectedValue(mockError)
      
      await expect(
        approveLot('lot-1', {
          comment: 'Approved',
        })
      ).rejects.toThrow('Unauthorized')
    })
  })
})
