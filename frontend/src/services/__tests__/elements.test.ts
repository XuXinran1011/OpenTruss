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
      const mockResponseData = {
        items: [
          { id: 'element-1', speckle_type: 'Wall' },
          { id: 'element-2', speckle_type: 'Column' },
        ],
        total: 2,
      }
      
      // apiGet returns ApiResponse<T>, and getElements returns response.data
      mockApiGet.mockResolvedValue({ data: mockResponseData } as any)
      
      const result = await getElements({
        page: 1,
        page_size: 20,
      })
      
      expect(mockApiGet).toHaveBeenCalledWith('/api/v1/elements?page=1&page_size=20')
      expect(result).toEqual(mockResponseData)
    })

    it('应该支持查询参数', async () => {
      mockApiGet.mockResolvedValue({ data: { items: [], total: 0 } } as any)
      
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
      const mockResponseData = {
        items: [{ id: 'element-1' }],
        total: 1,
      }
      
      // apiGet returns ApiResponse<T>, and getUnassignedElements returns response.data
      mockApiGet.mockResolvedValue({ data: mockResponseData } as any)
      
      const result = await getUnassignedElements(1, 20)
      
      expect(mockApiGet).toHaveBeenCalledWith('/api/v1/elements/unassigned?page=1&page_size=20')
      expect(result).toEqual(mockResponseData)
    })
  })

  describe('getElementDetail', () => {
    it('应该成功获取构件详情', async () => {
      const mockResponseData = {
        id: 'element-1',
        speckle_type: 'Wall',
        geometry: { type: 'Polyline', coordinates: [] },
      }
      
      // apiGet returns ApiResponse<T>, and getElementDetail returns response.data
      mockApiGet.mockResolvedValue({ data: mockResponseData } as any)
      
      const result = await getElementDetail('element-1')
      
      expect(mockApiGet).toHaveBeenCalledWith('/api/v1/elements/element-1')
      expect(result).toEqual(mockResponseData)
    })
  })

  describe('updateElementTopology', () => {
    it('应该成功更新构件拓扑', async () => {
      const mockResponseData = { id: 'element-1', topology_updated: true }
      const request = {
        geometry: {
          type: 'Polyline',
          coordinates: [[0, 0, 0], [10, 0, 0]], // 3D 坐标
        },
      }
      
      // apiPatch returns ApiResponse<T>, and updateElementTopology returns response.data
      mockApiPatch.mockResolvedValue({ data: mockResponseData } as any)
      
      const result = await updateElementTopology('element-1', request)
      
      expect(mockApiPatch).toHaveBeenCalledWith('/api/v1/elements/element-1/topology', request)
      expect(result).toEqual(mockResponseData)
    })
  })

  describe('updateElement', () => {
    it('应该成功更新构件', async () => {
      const mockResponseData = { id: 'element-1', updated_fields: ['height', 'base_offset'] }
      const request = {
        height: 3.5,
        base_offset: 0.1,
      }
      
      // apiPatch returns ApiResponse<T>, and updateElement returns response.data
      mockApiPatch.mockResolvedValue({ data: mockResponseData } as any)
      
      const result = await updateElement('element-1', request)
      
      expect(mockApiPatch).toHaveBeenCalledWith('/api/v1/elements/element-1', request)
      expect(result).toEqual(mockResponseData)
    })
  })

  describe('batchLiftElements', () => {
    it('应该成功批量更新Z轴参数', async () => {
      const mockResponseData = {
        updated_count: 2,
        element_ids: ['element-1', 'element-2'],
      }
      const request = {
        element_ids: ['element-1', 'element-2'],
        height: 3.5,
      }
      
      // apiPost returns ApiResponse<T>, and batchLiftElements returns response.data
      mockApiPost.mockResolvedValue({ data: mockResponseData } as any)
      
      const result = await batchLiftElements(request)
      
      expect(mockApiPost).toHaveBeenCalledWith('/api/v1/elements/batch-lift', request)
      expect(result).toEqual(mockResponseData)
    })
  })

  describe('classifyElement', () => {
    it('应该成功归类构件', async () => {
      const mockResponseData = {
        element_id: 'element-1',
        item_id: 'item-1',
      }
      const request = {
        item_id: 'item-1',
      }
      
      // apiPost returns ApiResponse<T>, and classifyElement returns response.data
      mockApiPost.mockResolvedValue({ data: mockResponseData } as any)
      
      const result = await classifyElement('element-1', request)
      
      expect(mockApiPost).toHaveBeenCalledWith('/api/v1/elements/element-1/classify', request)
      expect(result).toEqual(mockResponseData)
    })
  })

  describe('deleteElement', () => {
    it('应该成功删除构件', async () => {
      const mockResponseData = {
        id: 'element-1',
        deleted: true,
      }
      
      // apiDelete returns ApiResponse<T>, and deleteElement returns response.data
      mockApiDelete.mockResolvedValue({ data: mockResponseData } as any)
      
      const result = await deleteElement('element-1')
      
      expect(mockApiDelete).toHaveBeenCalledWith('/api/v1/elements/element-1')
      expect(result).toEqual(mockResponseData)
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
