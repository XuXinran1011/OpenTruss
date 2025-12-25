/**
 * lots Service 测试
 */

import {
  createLotsByRule,
  assignElementsToLot,
  removeElementsFromLot,
  updateLotStatus,
  getLotElements,
} from '../lots'
import { apiPost, apiPatch, apiGet } from '../api'
import { ApiError } from '../api'

// Mock api
jest.mock('../api', () => ({
  apiPost: jest.fn(),
  apiPatch: jest.fn(),
  apiGet: jest.fn(),
  ApiError: class ApiError extends Error {
    constructor(message: string, public statusCode: number) {
      super(message)
      this.name = 'ApiError'
    }
  },
}))

const mockApiPost = apiPost as jest.MockedFunction<typeof apiPost>
const mockApiPatch = apiPatch as jest.MockedFunction<typeof apiPatch>
const mockApiGet = apiGet as jest.MockedFunction<typeof apiGet>

describe('lots Service', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('createLotsByRule', () => {
    it('应该成功根据规则创建检验批', async () => {
      const mockResponse = {
        lots_created: [
          { id: 'lot-1', name: 'Lot 1', spatial_scope: 'Level 1', element_count: 10 },
        ],
        elements_assigned: 10,
        total_lots: 1,
      }
      
      mockApiPost.mockResolvedValue(mockResponse)
      
      const result = await createLotsByRule({
        item_id: 'item-1',
        rule_type: 'BY_LEVEL',
      })
      
      expect(mockApiPost).toHaveBeenCalledWith('/api/v1/lots/create-by-rule', {
        item_id: 'item-1',
        rule_type: 'BY_LEVEL',
      })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('assignElementsToLot', () => {
    it('应该成功分配构件到检验批', async () => {
      const mockResponse = {
        lot_id: 'lot-1',
        assigned_count: 2,
        total_requested: 2,
      }
      
      mockApiPost.mockResolvedValue(mockResponse)
      
      const result = await assignElementsToLot('lot-1', {
        element_ids: ['element-1', 'element-2'],
      })
      
      expect(mockApiPost).toHaveBeenCalledWith('/api/v1/lots/lot-1/assign-elements', {
        element_ids: ['element-1', 'element-2'],
      })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('removeElementsFromLot', () => {
    it('应该成功从检验批移除构件', async () => {
      const mockResponse = {
        lot_id: 'lot-1',
        removed_count: 1,
        total_requested: 1,
      }
      
      mockApiPost.mockResolvedValue(mockResponse)
      
      const result = await removeElementsFromLot('lot-1', {
        element_ids: ['element-1'],
      })
      
      expect(mockApiPost).toHaveBeenCalledWith('/api/v1/lots/lot-1/remove-elements', {
        element_ids: ['element-1'],
      })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('updateLotStatus', () => {
    it('应该成功更新检验批状态', async () => {
      const mockResponse = {
        lot_id: 'lot-1',
        old_status: 'PLANNING',
        new_status: 'IN_PROGRESS',
        updated_at: '2024-01-01T00:00:00Z',
      }
      
      mockApiPatch.mockResolvedValue(mockResponse)
      
      const result = await updateLotStatus('lot-1', {
        status: 'IN_PROGRESS',
      })
      
      expect(mockApiPatch).toHaveBeenCalledWith('/api/v1/lots/lot-1/status', {
        status: 'IN_PROGRESS',
      })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getLotElements', () => {
    it('应该成功获取检验批下的构件列表', async () => {
      const mockResponse = {
        lot_id: 'lot-1',
        items: [
          { id: 'element-1', speckle_type: 'Wall', level_id: 'level-1', status: 'Draft' },
        ],
        total: 1,
      }
      
      mockApiGet.mockResolvedValue(mockResponse)
      
      const result = await getLotElements('lot-1')
      
      expect(mockApiGet).toHaveBeenCalledWith('/api/v1/lots/lot-1/elements')
      expect(result).toEqual(mockResponse)
    })
  })

  describe('错误处理', () => {
    it('应该在API调用失败时抛出错误', async () => {
      const mockError = new ApiError('Not found', 404)
      mockApiPost.mockRejectedValue(mockError)
      
      await expect(
        createLotsByRule({
          item_id: 'nonexistent',
          rule_type: 'BY_LEVEL',
        })
      ).rejects.toThrow('Not found')
    })
  })
})

