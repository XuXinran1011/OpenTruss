/**
 * ElementSelector 组件测试
 */

import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ElementSelector } from '../ElementSelector'

// Mock hooks
jest.mock('@tanstack/react-query', () => ({
  ...jest.requireActual('@tanstack/react-query'),
  useQuery: jest.fn(),
}))

jest.mock('@/lib/utils', () => ({
  cn: jest.fn((...args) => args.filter(Boolean).join(' ')),
}))

const { useQuery } = require('@tanstack/react-query')

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

describe('ElementSelector', () => {
  const mockProps = {
    itemId: 'test_item_001',
    excludeLotId: null,
    selectedElementIds: [],
    onSelectionChange: jest.fn(),
    onConfirm: jest.fn(),
    onCancel: jest.fn(),
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('应该在加载时显示加载信息', () => {
    useQuery.mockReturnValue({
      data: null,
      isLoading: true,
    })

    render(<ElementSelector {...mockProps} />, { wrapper: createWrapper() })

    expect(screen.getByText('加载中...')).toBeInTheDocument()
  })

  it('应该显示没有可用构件的信息', () => {
    useQuery.mockReturnValue({
      data: { items: [] },
      isLoading: false,
    })

    render(<ElementSelector {...mockProps} />, { wrapper: createWrapper() })

    expect(screen.getByText('没有可用的构件')).toBeInTheDocument()
  })

  it('应该显示构件列表', () => {
    const mockElements = [
      {
        id: 'element_001',
        speckle_type: 'Wall',
        level_id: 'level_f1',
        zone_id: null,
        inspection_lot_id: null,
      },
      {
        id: 'element_002',
        speckle_type: 'Column',
        level_id: 'level_f1',
        zone_id: 'zone_a',
        inspection_lot_id: null,
      },
    ]

    useQuery.mockReturnValue({
      data: { items: mockElements },
      isLoading: false,
    })

    render(<ElementSelector {...mockProps} />, { wrapper: createWrapper() })

    expect(screen.getByText('element_001')).toBeInTheDocument()
    expect(screen.getByText('element_002')).toBeInTheDocument()
  })

  it('应该显示取消和确认按钮', () => {
    useQuery.mockReturnValue({
      data: { items: [] },
      isLoading: false,
    })

    render(<ElementSelector {...mockProps} />, { wrapper: createWrapper() })

    expect(screen.getByText('取消')).toBeInTheDocument()
    expect(screen.getByText('确认 (0)')).toBeInTheDocument()
  })
})

