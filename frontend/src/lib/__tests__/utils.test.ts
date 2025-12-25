/**
 * lib/utils 工具函数测试
 */

import { cn, formatNumber } from '../utils'

describe('lib/utils工具函数', () => {
  describe('cn', () => {
    it('应该合并className字符串', () => {
      expect(cn('class1', 'class2')).toContain('class1')
      expect(cn('class1', 'class2')).toContain('class2')
    })

    it('应该过滤falsy值', () => {
      const result = cn('class1', null, 'class2', undefined, 'class3')
      expect(result).toContain('class1')
      expect(result).toContain('class2')
      expect(result).toContain('class3')
    })

    it('应该处理条件类名', () => {
      const result = cn('class1', true && 'class2', false && 'class3')
      expect(result).toContain('class1')
      expect(result).toContain('class2')
      expect(result).not.toContain('class3')
    })

    it('应该处理空参数', () => {
      expect(cn()).toBe('')
    })
  })

  describe('formatNumber', () => {
    it('应该正确格式化数字', () => {
      expect(formatNumber(3.14159, 2)).toBe('3.14')
      expect(formatNumber(100, 0)).toBe('100')
      expect(formatNumber(10.5)).toBe('10.50')
    })
  })
})

