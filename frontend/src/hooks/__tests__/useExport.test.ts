/**
 * useExport Hook 测试
 */

import { renderHook, act, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import {
  useExportLotToIFC,
  useExportProjectToIFC,
  useBatchExportLotsToIFC,
} from '../useExport'
import {
  exportLotToIFC,
  exportProjectToIFC,
  batchExportLotsToIFC,
  downloadBlob,
} from '@/services/export'

// Mock dependencies
jest.mock('@/services/export', () => ({
  exportLotToIFC: jest.fn(),
  exportProjectToIFC: jest.fn(),
  batchExportLotsToIFC: jest.fn(),
  downloadBlob: jest.fn(),
}))

const mockExportLotToIFC = exportLotToIFC as jest.MockedFunction<typeof exportLotToIFC>
const mockExportProjectToIFC = exportProjectToIFC as jest.MockedFunction<typeof exportProjectToIFC>
const mockBatchExportLotsToIFC = batchExportLotsToIFC as jest.MockedFunction<typeof batchExportLotsToIFC>
const mockDownloadBlob = downloadBlob as jest.MockedFunction<typeof downloadBlob>

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

describe('useExport', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('useExportLotToIFC', () => {
    it('应该成功导出检验批为IFC', async () => {
      const mockBlob = new Blob(['test content'], { type: 'application/octet-stream' })
      mockExportLotToIFC.mockResolvedValue(mockBlob)
      
      const { result } = renderHook(() => useExportLotToIFC(), {
        wrapper: createWrapper(),
      })
      
      await act(async () => {
        await result.current.mutateAsync({
          lotId: 'lot-1',
          filename: 'test.ifc',
        })
      })
      
      expect(mockExportLotToIFC).toHaveBeenCalledWith('lot-1')
      expect(mockDownloadBlob).toHaveBeenCalledWith(mockBlob, 'test.ifc')
    })

    it('应该使用默认文件名', async () => {
      const mockBlob = new Blob(['test content'])
      mockExportLotToIFC.mockResolvedValue(mockBlob)
      
      const { result } = renderHook(() => useExportLotToIFC(), {
        wrapper: createWrapper(),
      })
      
      await act(async () => {
        await result.current.mutateAsync({
          lotId: 'lot-1',
        })
      })
      
      expect(mockDownloadBlob).toHaveBeenCalledWith(mockBlob, 'lot_lot-1.ifc')
    })

    it('应该在导出失败时抛出错误', async () => {
      const mockError = new Error('Export failed')
      mockExportLotToIFC.mockRejectedValue(mockError)
      
      const { result } = renderHook(() => useExportLotToIFC(), {
        wrapper: createWrapper(),
      })
      
      await act(async () => {
        try {
          await result.current.mutateAsync({
            lotId: 'lot-1',
          })
        } catch (err) {
          expect(err).toBe(mockError)
        }
      })
      
      expect(mockDownloadBlob).not.toHaveBeenCalled()
    })
  })

  describe('useExportProjectToIFC', () => {
    it('应该成功导出项目为IFC', async () => {
      const mockBlob = new Blob(['test content'])
      mockExportProjectToIFC.mockResolvedValue(mockBlob)
      
      const { result } = renderHook(() => useExportProjectToIFC(), {
        wrapper: createWrapper(),
      })
      
      await act(async () => {
        await result.current.mutateAsync({
          projectId: 'project-1',
          filename: 'project.ifc',
        })
      })
      
      expect(mockExportProjectToIFC).toHaveBeenCalledWith('project-1')
      expect(mockDownloadBlob).toHaveBeenCalledWith(mockBlob, 'project.ifc')
    })

    it('应该使用默认文件名', async () => {
      const mockBlob = new Blob(['test content'])
      mockExportProjectToIFC.mockResolvedValue(mockBlob)
      
      const { result } = renderHook(() => useExportProjectToIFC(), {
        wrapper: createWrapper(),
      })
      
      await act(async () => {
        await result.current.mutateAsync({
          projectId: 'project-1',
        })
      })
      
      expect(mockDownloadBlob).toHaveBeenCalledWith(mockBlob, 'project_project-1.ifc')
    })
  })

  describe('useBatchExportLotsToIFC', () => {
    it('应该成功批量导出检验批为IFC', async () => {
      const mockBlob = new Blob(['test content'])
      mockBatchExportLotsToIFC.mockResolvedValue(mockBlob)
      
      const { result } = renderHook(() => useBatchExportLotsToIFC(), {
        wrapper: createWrapper(),
      })
      
      await act(async () => {
        await result.current.mutateAsync({
          lotIds: ['lot-1', 'lot-2'],
          filename: 'batch.ifc',
        })
      })
      
      expect(mockBatchExportLotsToIFC).toHaveBeenCalledWith(['lot-1', 'lot-2'])
      expect(mockDownloadBlob).toHaveBeenCalledWith(mockBlob, 'batch.ifc')
    })

    it('应该使用默认文件名（基于数量）', async () => {
      const mockBlob = new Blob(['test content'])
      mockBatchExportLotsToIFC.mockResolvedValue(mockBlob)
      
      const { result } = renderHook(() => useBatchExportLotsToIFC(), {
        wrapper: createWrapper(),
      })
      
      await act(async () => {
        await result.current.mutateAsync({
          lotIds: ['lot-1', 'lot-2', 'lot-3'],
        })
      })
      
      expect(mockDownloadBlob).toHaveBeenCalledWith(mockBlob, 'batch_3_lots.ifc')
    })
  })
})

