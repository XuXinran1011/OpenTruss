/**
 * useApproval Hook 测试
 */

import { renderHook, act, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useApproveLot, useRejectLot, useApprovalHistory } from '../useApproval'
import { approveLot, rejectLot, getApprovalHistory } from '@/services/approval'

// Mock dependencies
jest.mock('@/services/approval', () => ({
  approveLot: jest.fn(),
  rejectLot: jest.fn(),
  getApprovalHistory: jest.fn(),
}))

const mockApproveLot = approveLot as jest.MockedFunction<typeof approveLot>
const mockRejectLot = rejectLot as jest.MockedFunction<typeof rejectLot>
const mockGetApprovalHistory = getApprovalHistory as jest.MockedFunction<typeof getApprovalHistory>

const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
      mutations: {
        retry: false,
      },
    },
  })
  
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

const createWrapper = () => TestWrapper

describe('useApproval', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('useApproveLot', () => {
    it('应该成功审批通过检验批', async () => {
      const mockResponse = {
        lot_id: 'lot-1',
        status: 'APPROVED',
      }
      
      mockApproveLot.mockResolvedValue(mockResponse)
      
      const { result } = renderHook(() => useApproveLot(), {
        wrapper: createWrapper(),
      })
      
      await act(async () => {
        await result.current.mutateAsync({
          lotId: 'lot-1',
          request: {
            comment: 'Approved',
          },
        })
      })
      
      expect(mockApproveLot).toHaveBeenCalledWith('lot-1', {
        comment: 'Approved',
      })
    })

    it('应该在审批失败时抛出错误', async () => {
      const mockError = new Error('Approval failed')
      mockApproveLot.mockRejectedValue(mockError)
      
      const { result } = renderHook(() => useApproveLot(), {
        wrapper: createWrapper(),
      })
      
      await act(async () => {
        try {
          await result.current.mutateAsync({
            lotId: 'lot-1',
            request: {
              comment: 'Approved',
            },
          })
        } catch (err) {
          expect(err).toBe(mockError)
        }
      })
    })
  })

  describe('useRejectLot', () => {
    it('应该成功驳回检验批', async () => {
      const mockResponse = {
        lot_id: 'lot-1',
        status: 'REJECTED',
      }
      
      mockRejectLot.mockResolvedValue(mockResponse)
      
      const { result } = renderHook(() => useRejectLot(), {
        wrapper: createWrapper(),
      })
      
      await act(async () => {
        await result.current.mutateAsync({
          lotId: 'lot-1',
          request: {
            comment: 'Rejected',
          },
        })
      })
      
      expect(mockRejectLot).toHaveBeenCalledWith('lot-1', {
        comment: 'Rejected',
      })
    })

    it('应该在驳回失败时抛出错误', async () => {
      const mockError = new Error('Rejection failed')
      mockRejectLot.mockRejectedValue(mockError)
      
      const { result } = renderHook(() => useRejectLot(), {
        wrapper: createWrapper(),
      })
      
      await act(async () => {
        try {
          await result.current.mutateAsync({
            lotId: 'lot-1',
            request: {
              comment: 'Rejected',
            },
          })
        } catch (err) {
          expect(err).toBe(mockError)
        }
      })
    })
  })

  describe('useApprovalHistory', () => {
    it('应该成功获取审批历史', async () => {
      const mockHistory = [
        {
          id: 'history-1',
          lot_id: 'lot-1',
          action: 'APPROVED',
          user_id: 'user-1',
          comment: 'Approved',
          created_at: '2024-01-01T00:00:00Z',
        },
      ]
      
      mockGetApprovalHistory.mockResolvedValue(mockHistory)
      
      const { result } = renderHook(() => useApprovalHistory('lot-1'), {
        wrapper: createWrapper(),
      })
      
      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })
      
      expect(mockGetApprovalHistory).toHaveBeenCalledWith('lot-1')
      expect(result.current.data).toEqual(mockHistory)
    })

    it('应该在lotId为null时不查询', () => {
      const { result } = renderHook(() => useApprovalHistory(null), {
        wrapper: createWrapper(),
      })
      
      expect(mockGetApprovalHistory).not.toHaveBeenCalled()
      expect(result.current.isFetching).toBe(false)
    })

    it('应该在查询失败时返回错误', async () => {
      const mockError = new Error('Failed to fetch history')
      mockGetApprovalHistory.mockRejectedValue(mockError)
      
      const { result } = renderHook(() => useApprovalHistory('lot-1'), {
        wrapper: createWrapper(),
      })
      
      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })
      
      expect(result.current.error).toBe(mockError)
    })
  })
})

