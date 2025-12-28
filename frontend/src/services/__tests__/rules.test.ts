/**
 * rules Service 测试
 */

import { getRules, previewRule } from '../rules'

// Mock global fetch
global.fetch = jest.fn()
const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>

describe('rules Service', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('getRules', () => {
    it('应该成功获取规则列表', async () => {
      const mockResponse = {
        data: {
          rules: [
            {
              rule_type: 'BY_LEVEL',
              name: '按楼层分组',
              description: '按楼层对构件进行分组',
            },
            {
              rule_type: 'BY_ZONE',
              name: '按区域分组',
              description: '按区域对构件进行分组',
            },
          ],
        },
      }

      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => mockResponse,
      } as Response)

      const result = await getRules()

      expect(mockFetch).toHaveBeenCalledWith('/api/v1/rules', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      expect(result).toEqual(mockResponse.data.rules)
      expect(result).toHaveLength(2)
    })

    it('应该在获取失败时抛出错误', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
      } as Response)

      await expect(getRules()).rejects.toThrow('Failed to get rules')
    })
  })

  describe('previewRule', () => {
    it('应该成功预览规则', async () => {
      const mockResponse = {
        data: {
          rule_type: 'BY_LEVEL',
          estimated_lots: 3,
          groups: [
            { key: 'level-1', count: 10, label: 'Level 1' },
            { key: 'level-2', count: 8, label: 'Level 2' },
            { key: 'level-3', count: 5, label: 'Level 3' },
          ],
        },
      }

      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => mockResponse,
      } as Response)

      const result = await previewRule({
        rule_type: 'BY_LEVEL',
        item_id: 'item-1',
      })

      expect(mockFetch).toHaveBeenCalledWith('/api/v1/rules/preview', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          rule_type: 'BY_LEVEL',
          item_id: 'item-1',
        }),
      })
      expect(result).toEqual(mockResponse.data)
      expect(result.estimated_lots).toBe(3)
    })

    it('应该在预览失败时抛出错误', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
      } as Response)

      await expect(
        previewRule({ rule_type: 'BY_LEVEL', item_id: 'item-1' })
      ).rejects.toThrow('Failed to preview rule')
    })
  })
})
