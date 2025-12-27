/**
 * element-utils 工具函数测试
 */

import { batchGetElementDetails } from '../element-utils'
import { getElementDetail } from '@/services/elements'

// Mock console.error to suppress error logs in tests
const originalError = console.error
beforeAll(() => {
  console.error = jest.fn()
})

afterAll(() => {
  console.error = originalError
})

// Mock services
jest.mock('@/services/elements', () => ({
  getElementDetail: jest.fn(),
}))

const mockGetElementDetail = getElementDetail as jest.MockedFunction<typeof getElementDetail>

describe('element-utils工具函数', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('batchGetElementDetails', () => {
    it('应该成功批量获取构件详情', async () => {
      mockGetElementDetail
        .mockResolvedValueOnce({
          id: 'element-1',
          speckle_type: 'Wall',
        } as any)
        .mockResolvedValueOnce({
          id: 'element-2',
          speckle_type: 'Column',
        } as any)

      const result = await batchGetElementDetails(['element-1', 'element-2'])

      expect(result.size).toBe(2)
      expect(result.get('element-1')?.id).toBe('element-1')
      expect(result.get('element-2')?.id).toBe('element-2')
    })

    it('应该在部分获取失败时继续处理其他元素', async () => {
      mockGetElementDetail
        .mockResolvedValueOnce({
          id: 'element-1',
          speckle_type: 'Wall',
        } as any)
        .mockRejectedValueOnce(new Error('Not found'))
        .mockResolvedValueOnce({
          id: 'element-3',
          speckle_type: 'Beam',
        } as any)

      const result = await batchGetElementDetails(['element-1', 'element-2', 'element-3'])

      expect(result.size).toBe(2)
      expect(result.get('element-1')).toBeDefined()
      expect(result.get('element-3')).toBeDefined()
      expect(result.get('element-2')).toBeUndefined()
    })

    it('应该在所有获取失败时返回空Map', async () => {
      mockGetElementDetail.mockRejectedValue(new Error('Network error'))

      const result = await batchGetElementDetails(['element-1', 'element-2'])

      expect(result.size).toBe(0)
    })
  })
})

