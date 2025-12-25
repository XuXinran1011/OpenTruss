/**
 * LotStrategyPanel 组件测试
 */

import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { LotStrategyPanel } from '../LotStrategyPanel'

// Mock hooks
jest.mock('@/hooks/useLotStrategy', () => ({
  useCreateLotsByRule: jest.fn(),
  useItemDetailForLots: jest.fn(),
}))

jest.mock('@/lib/utils', () => ({
  cn: jest.fn((...args) => args.filter(Boolean).join(' ')),
}))

const { useCreateLotsByRule, useItemDetailForLots } = require('@/hooks/useLotStrategy')

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

describe('LotStrategyPanel', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('应该在没有itemId时显示提示信息', () => {
    useItemDetailForLots.mockReturnValue({
      data: null,
      isLoading: false,
    })
    useCreateLotsByRule.mockReturnValue({
      mutateAsync: jest.fn(),
      isPending: false,
      isSuccess: false,
      isError: false,
    })

    render(<LotStrategyPanel itemId={null} />, { wrapper: createWrapper() })

    expect(screen.getByText('请先选择一个分项（Item）')).toBeInTheDocument()
  })

  it('应该在加载时显示加载信息', () => {
    useItemDetailForLots.mockReturnValue({
      data: null,
      isLoading: true,
    })
    useCreateLotsByRule.mockReturnValue({
      mutateAsync: jest.fn(),
      isPending: false,
      isSuccess: false,
      isError: false,
    })

    render(<LotStrategyPanel itemId="test_item_001" />, { wrapper: createWrapper() })

    expect(screen.getByText('加载中...')).toBeInTheDocument()
  })

  it('应该显示规则类型选择', () => {
    useItemDetailForLots.mockReturnValue({
      data: { name: 'Test Item' },
      isLoading: false,
    })
    useCreateLotsByRule.mockReturnValue({
      mutateAsync: jest.fn(),
      isPending: false,
      isSuccess: false,
      isError: false,
    })

    render(<LotStrategyPanel itemId="test_item_001" />, { wrapper: createWrapper() })

    expect(screen.getByText('按楼层划分')).toBeInTheDocument()
    expect(screen.getByText('按区域划分')).toBeInTheDocument()
    expect(screen.getByText('按楼层+区域划分')).toBeInTheDocument()
  })

  it('应该显示创建按钮', () => {
    useItemDetailForLots.mockReturnValue({
      data: { name: 'Test Item' },
      isLoading: false,
    })
    useCreateLotsByRule.mockReturnValue({
      mutateAsync: jest.fn(),
      isPending: false,
      isSuccess: false,
      isError: false,
    })

    render(<LotStrategyPanel itemId="test_item_001" />, { wrapper: createWrapper() })

    expect(screen.getByText('执行创建')).toBeInTheDocument()
  })
})

