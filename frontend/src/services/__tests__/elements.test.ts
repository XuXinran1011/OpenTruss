/**
 * elements Service 测试
 */

import {
  getElements,
  getUnassignedElements,
  getElementDetail,
  updateElementTopology,
  updateElement,
  batchLiftElements,
  classifyElement,
  deleteElement,
} from '../elements'
import { apiGet, apiPatch, apiPost, apiDelete } from '../api'
import { ApiError } from '../api'

// Mock api
jest.mock('../api', () => ({
  apiGet: jest.fn(),
  apiPatch: jest.fn(),
  apiPost: jest.fn(),
  apiDelete: jest.fn(),
  ApiError: class ApiError extends Error {
    constructor(message: string, public statusCode: number) {
      super(message)
      this.name = 'ApiError'
    }
  },
}))

const mockApiGet = apiGet as jest.MockedFunction<typeof apiGet>
const mockApiPatch = apiPatch as jest.MockedFunction<typeof apiPatch>
const mockApiPost = apiPost as jest.MockedFunction<typeof apiPost>
const mockApiDelete = apiDelete as jest.MockedFunction<typeof apiDelete>

describe('elements Service', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('getElements', () => {
    it('应该成功获取构件列表', async () => {
      const mockResponse = {
        items: [
          { id: 'element-1', speckle_type: 'Wall' },
          { id: 'element-2', speckle_type: 'Column' },
        ],
        total: 2,
      }
      
      mockApiGet.mockResolvedValue(mockResponse)
      
      const result = await getElements({
        page: 1,
        page_size: 20,
      })
      
      expect(mockApiGet).toHaveBeenCalledWith('/api/v1/elements?page=1&page_size=20')
      expect(result).toEqual(mockResponse)
    })

    it('应该支持查询参数', async () => {
      mockApiGet.mockResolvedValue({ items: [], total: 0 })
      
      await getElements({
        page: 2,
        page_size: 10,
        speckle_type: 'Wall',
        level_id: 'level-1',
        status: 'Draft',
      })
      
      const callUrl = mockApiGet.mock.calls[0][0] as string
      expect(callUrl).toContain('page=2')
      expect(callUrl).toContain('page_size=10')
      expect(callUrl).toContain('speckle_type=Wall')
      expect(callUrl).toContain('level_id=level-1')
      expect(callUrl).toContain('status=Draft')
    })
  })

  describe('getUnassignedElements', () => {
    it('应该成功获取未分配构件列表', async () => {
      const mockResponse = {
        items: [{ id: 'element-1' }],
        total: 1,
      }
      
      mockApiGet.mockResolvedValue(mockResponse)
      
      const result = await getUnassignedElements(1, 20)
      
      expect(mockApiGet).toHaveBeenCalledWith('/api/v1/elements/unassigned?page=1&page_size=20')
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getElementDetail', () => {
    it('应该成功获取构件详情', async () => {
      const mockResponse = {
        id: 'element-1',
        speckle_type: 'Wall',
        geometry: { type: 'Polyline', coordinates: [] },
      }
      
      mockApiGet.mockResolvedValue(mockResponse)
      
      const result = await getElementDetail('element-1')
      
      expect(mockApiGet).toHaveBeenCalledWith('/api/v1/elements/element-1')
      expect(result).toEqual(mockResponse)
    })
  })

  describe('updateElementTopology', () => {
    it('应该成功更新构件拓扑', async () => {
      const mockResponse = { id: 'element-1', updated: true }
      const request = {
        geometry: {
          type: 'Polyline',
          coordinates: [[0, 0, 0], [10, 0, 0]], // 3D 坐标
        },
      }
      
      mockApiPatch.mockResolvedValue(mockResponse)
      
      const result = await updateElementTopology('element-1', request)
      
      expect(mockApiPatch).toHaveBeenCalledWith('/api/v1/elements/element-1/topology', request)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('updateElement', () => {
    it('应该成功更新构件', async () => {
      const mockResponse = { id: 'element-1', updated: true }
      const request = {
        height: 3.5,
        base_offset: 0.1,
      }
      
      mockApiPatch.mockResolvedValue(mockResponse)
      
      const result = await updateElement('element-1', request)
      
      expect(mockApiPatch).toHaveBeenCalledWith('/api/v1/elements/element-1', request)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('batchLiftElements', () => {
    it('应该成功批量更新Z轴参数', async () => {
      const mockResponse = {
        updated_count: 2,
        element_ids: ['element-1', 'element-2'],
      }
      const request = {
        element_ids: ['element-1', 'element-2'],
        height: 3.5,
      }
      
      mockApiPost.mockResolvedValue(mockResponse)
      
      const result = await batchLiftElements(request)
      
      expect(mockApiPost).toHaveBeenCalledWith('/api/v1/elements/batch-lift', request)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('classifyElement', () => {
    it('应该成功归类构件', async () => {
      const mockResponse = {
        element_id: 'element-1',
        item_id: 'item-1',
      }
      const request = {
        item_id: 'item-1',
      }
      
      mockApiPost.mockResolvedValue(mockResponse)
      
      const result = await classifyElement('element-1', request)
      
      expect(mockApiPost).toHaveBeenCalledWith('/api/v1/elements/element-1/classify', request)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('deleteElement', () => {
    it('应该成功删除构件', async () => {
      const mockResponse = {
        id: 'element-1',
        deleted: true,
      }
      
      mockApiDelete.mockResolvedValue(mockResponse)
      
      const result = await deleteElement('element-1')
      
      expect(mockApiDelete).toHaveBeenCalledWith('/api/v1/elements/element-1')
      expect(result).toEqual(mockResponse)
    })
  })

  describe('错误处理', () => {
    it('应该在API调用失败时抛出错误', async () => {
      const mockError = new ApiError('Not found', 404)
      mockApiGet.mockRejectedValue(mockError)
      
      await expect(getElementDetail('nonexistent')).rejects.toThrow('Not found')
    })
  })
})

