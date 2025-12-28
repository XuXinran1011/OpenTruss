/**
 * useLotStrategy Hook 测试
 */

import { renderHook, act, waitFor } from '@testing-library/react'
import {
  useCreateLotsByRule,
  useAssignElementsToLot,
  useRemoveElementsFromLot,
  useUpdateLotStatus,
  useLotElements,
  useItemDetailForLots,
} from '../useLotStrategy'
import {
  createLotsByRule,
  assignElementsToLot,
  removeElementsFromLot,
  updateLotStatus,
  getLotElements,
} from '@/services/lots'
import { getItemDetail } from '@/services/hierarchy'
import { TestWrapper } from '../../test-utils'

// Mock dependencies
jest.mock('@/services/lots', () => ({
  createLotsByRule: jest.fn(),
  assignElementsToLot: jest.fn(),
  removeElementsFromLot: jest.fn(),
  updateLotStatus: jest.fn(),
  getLotElements: jest.fn(),
}))

jest.mock('@/services/hierarchy', () => ({
  getItemDetail: jest.fn(),
}))

const mockCreateLotsByRule = createLotsByRule as jest.MockedFunction<typeof createLotsByRule>
const mockAssignElementsToLot = assignElementsToLot as jest.MockedFunction<typeof assignElementsToLot>
const mockRemoveElementsFromLot = removeElementsFromLot as jest.MockedFunction<typeof removeElementsFromLot>
const mockUpdateLotStatus = updateLotStatus as jest.MockedFunction<typeof updateLotStatus>
const mockGetLotElements = getLotElements as jest.MockedFunction<typeof getLotElements>
const mockGetItemDetail = getItemDetail as jest.MockedFunction<typeof getItemDetail>

describe('useLotStrategy hooks', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('useCreateLotsByRule', () => {
    it('应该成功创建检验批', async () => {
      const mockResponse = {
        lots: [{ id: 'lot-1', name: 'Lot 1' }],
        total: 1,
      }

      mockCreateLotsByRule.mockResolvedValue(mockResponse)

      const { result } = renderHook(() => useCreateLotsByRule(), {
        wrapper: TestWrapper,
      })

      await act(async () => {
        await result.current.mutateAsync({
          rule_type: 'BY_LEVEL',
          item_id: 'item-1',
        })
      })

      expect(mockCreateLotsByRule).toHaveBeenCalledWith({
        rule_type: 'BY_LEVEL',
        item_id: 'item-1',
      })
    })
  })

  describe('useAssignElementsToLot', () => {
    it('应该成功分配构件到检验批', async () => {
      const mockResponse = {
        assigned_count: 2,
        element_ids: ['element-1', 'element-2'],
      }

      mockAssignElementsToLot.mockResolvedValue(mockResponse)

      const { result } = renderHook(() => useAssignElementsToLot('lot-1'), {
        wrapper: TestWrapper,
      })

      await act(async () => {
        await result.current.mutateAsync({
          element_ids: ['element-1', 'element-2'],
        })
      })

      expect(mockAssignElementsToLot).toHaveBeenCalledWith('lot-1', {
        element_ids: ['element-1', 'element-2'],
      })
    })
  })

  describe('useRemoveElementsFromLot', () => {
    it('应该成功从检验批移除构件', async () => {
      const mockResponse = {
        removed_count: 1,
        element_ids: ['element-1'],
      }

      mockRemoveElementsFromLot.mockResolvedValue(mockResponse)

      const { result } = renderHook(() => useRemoveElementsFromLot('lot-1'), {
        wrapper: TestWrapper,
      })

      await act(async () => {
        await result.current.mutateAsync({
          element_ids: ['element-1'],
        })
      })

      expect(mockRemoveElementsFromLot).toHaveBeenCalledWith('lot-1', {
        element_ids: ['element-1'],
      })
    })
  })

  describe('useUpdateLotStatus', () => {
    it('应该成功更新检验批状态', async () => {
      const mockResponse = {
        lot_id: 'lot-1',
        status: 'InProgress',
      }

      mockUpdateLotStatus.mockResolvedValue(mockResponse)

      const { result } = renderHook(() => useUpdateLotStatus('lot-1'), {
        wrapper: TestWrapper,
      })

      await act(async () => {
        await result.current.mutateAsync({
          status: 'InProgress',
        })
      })

      expect(mockUpdateLotStatus).toHaveBeenCalledWith('lot-1', {
        status: 'InProgress',
      })
    })
  })

  describe('useLotElements', () => {
    it('应该成功获取检验批构件列表', async () => {
      const mockResponse = {
        items: [{ id: 'element-1' }, { id: 'element-2' }],
        total: 2,
      }

      mockGetLotElements.mockResolvedValue(mockResponse)

      const { result } = renderHook(() => useLotElements('lot-1'), {
        wrapper: TestWrapper,
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(mockGetLotElements).toHaveBeenCalledWith('lot-1')
      expect(result.current.data).toEqual(mockResponse)
    })
  })

  describe('useItemDetailForLots', () => {
    it('应该成功获取分项详情', async () => {
      const mockResponse = {
        id: 'item-1',
        name: 'Item 1',
        lots: [],
      }

      mockGetItemDetail.mockResolvedValue(mockResponse)

      const { result } = renderHook(() => useItemDetailForLots('item-1'), {
        wrapper: TestWrapper,
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(mockGetItemDetail).toHaveBeenCalledWith('item-1')
      expect(result.current.data).toEqual(mockResponse)
    })

    it('应该在itemId为null时不执行查询', () => {
      const { result } = renderHook(() => useItemDetailForLots(null), {
        wrapper: TestWrapper,
      })

      expect(result.current.isFetching).toBe(false)
      expect(mockGetItemDetail).not.toHaveBeenCalled()
    })
  })
})
