/**
 * hierarchy Service 测试
 */

import {
  getProjects,
  getProjectDetail,
  getProjectHierarchy,
  getBuildingDetail,
  getDivisionDetail,
  getSubDivisionDetail,
  getItemDetail,
  getInspectionLotDetail,
} from '../hierarchy'
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

describe('hierarchy Service', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('getProjects', () => {
    it('应该成功获取项目列表', async () => {
      const mockResponseData = {
        items: [{ id: 'project-1', name: 'Project 1' }],
        total: 1,
      }
      
      // apiGet returns ApiResponse<T>, and getProjects returns response.data
      mockApiGet.mockResolvedValue({ data: mockResponseData } as any)
      
      const result = await getProjects(1, 20)
      
      expect(mockApiGet).toHaveBeenCalledWith('/api/v1/hierarchy/projects?page=1&page_size=20')
      expect(result).toEqual(mockResponseData)
    })
  })

  describe('getProjectDetail', () => {
    it('应该成功获取项目详情', async () => {
      const mockResponseData = {
        id: 'project-1',
        name: 'Project 1',
      }
      
      // apiGet returns ApiResponse<T>, and getProjectDetail returns response.data
      mockApiGet.mockResolvedValue({ data: mockResponseData } as any)
      
      const result = await getProjectDetail('project-1')
      
      expect(mockApiGet).toHaveBeenCalledWith('/api/v1/hierarchy/projects/project-1')
      expect(result).toEqual(mockResponseData)
    })
  })

  describe('getProjectHierarchy', () => {
    it('应该成功获取项目层级结构', async () => {
      const mockResponseData = {
        project_id: 'project-1',
        project_name: 'Project 1',
        hierarchy: {
          id: 'project-1',
          label: 'Project',
          name: 'Project 1',
          children: [],
        },
      }
      
      // apiGet returns ApiResponse<T>, and getProjectHierarchy returns response.data
      mockApiGet.mockResolvedValue({ data: mockResponseData } as any)
      
      const result = await getProjectHierarchy('project-1')
      
      expect(mockApiGet).toHaveBeenCalledWith('/api/v1/hierarchy/projects/project-1/hierarchy')
      expect(result).toEqual(mockResponseData)
    })
  })

  describe('getBuildingDetail', () => {
    it('应该成功获取单体详情', async () => {
      const mockResponseData = {
        id: 'building-1',
        name: 'Building 1',
      }
      
      // apiGet returns ApiResponse<T>, and getBuildingDetail returns response.data
      mockApiGet.mockResolvedValue({ data: mockResponseData } as any)
      
      const result = await getBuildingDetail('building-1')
      
      expect(mockApiGet).toHaveBeenCalledWith('/api/v1/hierarchy/buildings/building-1')
      expect(result).toEqual(mockResponseData)
    })
  })

  describe('getDivisionDetail', () => {
    it('应该成功获取分部详情', async () => {
      const mockResponseData = {
        id: 'division-1',
        name: 'Division 1',
      }
      
      // apiGet returns ApiResponse<T>, and getDivisionDetail returns response.data
      mockApiGet.mockResolvedValue({ data: mockResponseData } as any)
      
      const result = await getDivisionDetail('division-1')
      
      expect(mockApiGet).toHaveBeenCalledWith('/api/v1/hierarchy/divisions/division-1')
      expect(result).toEqual(mockResponseData)
    })
  })

  describe('getSubDivisionDetail', () => {
    it('应该成功获取子分部详情', async () => {
      const mockResponseData = {
        id: 'subdivision-1',
        name: 'SubDivision 1',
      }
      
      // apiGet returns ApiResponse<T>, and getSubDivisionDetail returns response.data
      mockApiGet.mockResolvedValue({ data: mockResponseData } as any)
      
      const result = await getSubDivisionDetail('subdivision-1')
      
      expect(mockApiGet).toHaveBeenCalledWith('/api/v1/hierarchy/subdivisions/subdivision-1')
      expect(result).toEqual(mockResponseData)
    })
  })

  describe('getItemDetail', () => {
    it('应该成功获取分项详情', async () => {
      const mockResponseData = {
        id: 'item-1',
        name: 'Item 1',
        inspection_lot_count: 5,
      }
      
      // apiGet returns ApiResponse<T>, and getItemDetail returns response.data
      mockApiGet.mockResolvedValue({ data: mockResponseData } as any)
      
      const result = await getItemDetail('item-1')
      
      expect(mockApiGet).toHaveBeenCalledWith('/api/v1/hierarchy/items/item-1')
      expect(result).toEqual(mockResponseData)
    })
  })

  describe('getInspectionLotDetail', () => {
    it('应该成功获取检验批详情', async () => {
      const mockResponseData = {
        id: 'lot-1',
        name: 'Lot 1',
        status: 'PLANNING',
        element_count: 10,
      }
      
      // apiGet returns ApiResponse<T>, and getInspectionLotDetail returns response.data
      mockApiGet.mockResolvedValue({ data: mockResponseData } as any)
      
      const result = await getInspectionLotDetail('lot-1')
      
      expect(mockApiGet).toHaveBeenCalledWith('/api/v1/hierarchy/inspection-lots/lot-1')
      expect(result).toEqual(mockResponseData)
    })
  })

  describe('错误处理', () => {
    it('应该在API调用失败时抛出错误', async () => {
      const mockError = new ApiError('Not found', 404)
      mockApiGet.mockRejectedValue(mockError)
      
      await expect(getProjectDetail('nonexistent')).rejects.toThrow('Not found')
    })
  })
})
