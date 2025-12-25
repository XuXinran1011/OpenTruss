/**
 * LotManagementPanel 组件测试
 */

import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { LotManagementPanel } from '../LotManagementPanel'

// Mock hooks and stores
jest.mock('@/hooks/useLotStrategy', () => ({
  useItemDetailForLots: jest.fn(),
  useLotElements: jest.fn(),
  useUpdateLotStatus: jest.fn(),
  useRemoveElementsFromLot: jest.fn(),
  useAssignElementsToLot: jest.fn(),
}))

jest.mock('@/stores/hierarchy', () => ({
  useHierarchyStore: jest.fn(),
}))

jest.mock('@/lib/utils', () => ({
  cn: jest.fn((...args) => args.filter(Boolean).join(' ')),
}))

const { useItemDetailForLots, useLotElements, useUpdateLotStatus, useRemoveElementsFromLot, useAssignElementsToLot } = require('@/hooks/useLotStrategy')
const { useHierarchyStore } = require('@/stores/hierarchy')

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })
  
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

describe('LotManagementPanel', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    
    useHierarchyStore.mockReturnValue({
      hierarchyData: {
        id: 'test_root',
        name: 'Test Project',
        label: 'Project',
        children: [
          {
            id: 'test_item_001',
            name: 'Test Item',
            label: 'Item',
            children: [
              {
                id: 'lot_001',
                name: 'Test Lot',
                label: 'InspectionLot',
                metadata: {
                  status: 'PLANNING',
                  element_count: 5,
                },
              },
            ],
          },
        ],
      },
    })
  })

  it('应该在没有itemId时显示提示信息', () => {
    useItemDetailForLots.mockReturnValue({
      data: null,
      isLoading: false,
    })
    useLotElements.mockReturnValue({
      data: { items: [], total: 0 },
      isLoading: false,
    })
    useUpdateLotStatus.mockReturnValue({
      mutateAsync: jest.fn(),
      isPending: false,
    })
    useRemoveElementsFromLot.mockReturnValue({
      mutateAsync: jest.fn(),
      isPending: false,
    })
    useAssignElementsToLot.mockReturnValue({
      mutateAsync: jest.fn(),
      isPending: false,
    })

    render(<LotManagementPanel itemId={null} />, { wrapper: createWrapper() })

    expect(screen.getByText('请先选择一个分项（Item）')).toBeInTheDocument()
  })

  it('应该在加载时显示加载信息', () => {
    useItemDetailForLots.mockReturnValue({
      data: null,
      isLoading: true,
    })
    useLotElements.mockReturnValue({
      data: { items: [], total: 0 },
      isLoading: false,
    })
    useUpdateLotStatus.mockReturnValue({
      mutateAsync: jest.fn(),
      isPending: false,
    })
    useRemoveElementsFromLot.mockReturnValue({
      mutateAsync: jest.fn(),
      isPending: false,
    })
    useAssignElementsToLot.mockReturnValue({
      mutateAsync: jest.fn(),
      isPending: false,
    })

    render(<LotManagementPanel itemId="test_item_001" />, { wrapper: createWrapper() })

    expect(screen.getByText('加载中...')).toBeInTheDocument()
  })

  it('应该显示检验批列表', () => {
    useItemDetailForLots.mockReturnValue({
      data: { name: 'Test Item' },
      isLoading: false,
    })
    useLotElements.mockReturnValue({
      data: { items: [], total: 0 },
      isLoading: false,
    })
    useUpdateLotStatus.mockReturnValue({
      mutateAsync: jest.fn(),
      isPending: false,
    })
    useRemoveElementsFromLot.mockReturnValue({
      mutateAsync: jest.fn(),
      isPending: false,
    })
    useAssignElementsToLot.mockReturnValue({
      mutateAsync: jest.fn(),
      isPending: false,
    })

    render(<LotManagementPanel itemId="test_item_001" />, { wrapper: createWrapper() })

    expect(screen.getByText('Test Lot')).toBeInTheDocument()
  })

  it('应该在没有任何检验批时显示提示', () => {
    useItemDetailForLots.mockReturnValue({
      data: { name: 'Test Item' },
      isLoading: false,
    })
    useLotElements.mockReturnValue({
      data: { items: [], total: 0 },
      isLoading: false,
    })
    useUpdateLotStatus.mockReturnValue({
      mutateAsync: jest.fn(),
      isPending: false,
    })
    useRemoveElementsFromLot.mockReturnValue({
      mutateAsync: jest.fn(),
      isPending: false,
    })
    useAssignElementsToLot.mockReturnValue({
      mutateAsync: jest.fn(),
      isPending: false,
    })
    useHierarchyStore.mockReturnValue({
      hierarchyData: {
        id: 'test_root',
        name: 'Test Project',
        label: 'Project',
        children: [
          {
            id: 'test_item_001',
            name: 'Test Item',
            label: 'Item',
            children: [],
          },
        ],
      },
    })

    render(<LotManagementPanel itemId="test_item_001" />, { wrapper: createWrapper() })

    expect(screen.getByText('暂无检验批')).toBeInTheDocument()
  })
})

