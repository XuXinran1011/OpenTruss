/**
 * background Service 测试
 */

import {
  uploadBackground,
  listBackgrounds,
  getBackgroundUrl,
  deleteBackground,
} from '../background'
import { apiGet, apiDelete } from '../api'
import { ApiError } from '../api'

// Mock api
jest.mock('../api', () => ({
  apiGet: jest.fn(),
  apiDelete: jest.fn(),
  ApiError: class ApiError extends Error {
    constructor(message: string, public statusCode: number) {
      super(message)
      this.name = 'ApiError'
    }
  },
}))

// Mock global fetch
global.fetch = jest.fn()
const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
}
Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
})

const mockApiGet = apiGet as jest.MockedFunction<typeof apiGet>
const mockApiDelete = apiDelete as jest.MockedFunction<typeof apiDelete>

describe('background Service', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockLocalStorage.getItem.mockReturnValue('test-token')
  })

  describe('uploadBackground', () => {
    it('应该成功上传底图文件', async () => {
      const mockFile = new File(['test'], 'test.jpg', { type: 'image/jpeg' })
      const mockResponse = {
        id: 'bg-1',
        filename: 'test.jpg',
        url: '/api/v1/background/bg-1',
        size: 1024,
        content_type: 'image/jpeg',
        created_at: '2024-01-01T00:00:00Z',
      }

      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => mockResponse,
      } as Response)

      const result = await uploadBackground(mockFile)

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/background/upload'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            Authorization: 'Bearer test-token',
          }),
        })
      )
      expect(result).toEqual(mockResponse)
    })

    it('应该在上传失败时抛出错误', async () => {
      const mockFile = new File(['test'], 'test.jpg', { type: 'image/jpeg' })

      mockFetch.mockResolvedValue({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
        json: async () => ({ detail: '上传失败' }),
      } as Response)

      await expect(uploadBackground(mockFile)).rejects.toThrow('上传失败')
    })
  })

  describe('listBackgrounds', () => {
    it('应该成功获取底图列表', async () => {
      const mockResponse = {
        data: {
          items: [
            {
              id: 'bg-1',
              filename: 'test.jpg',
              url: '/api/v1/background/bg-1',
              size: 1024,
              content_type: 'image/jpeg',
              created_at: '2024-01-01T00:00:00Z',
            },
          ],
          total: 1,
        },
      }

      mockApiGet.mockResolvedValue(mockResponse)

      const result = await listBackgrounds()

      expect(mockApiGet).toHaveBeenCalledWith('/api/v1/background')
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('getBackgroundUrl', () => {
    it('应该返回正确的底图URL', () => {
      const url = getBackgroundUrl('bg-1')
      expect(url).toContain('/api/v1/background/bg-1')
    })
  })

  describe('deleteBackground', () => {
    it('应该成功删除底图', async () => {
      const mockResponse = {
        data: {
          id: 'bg-1',
          deleted: true,
        },
      }

      mockApiDelete.mockResolvedValue(mockResponse)

      const result = await deleteBackground('bg-1')

      expect(mockApiDelete).toHaveBeenCalledWith('/api/v1/background/bg-1')
      expect(result).toEqual(mockResponse.data)
    })
  })
})
