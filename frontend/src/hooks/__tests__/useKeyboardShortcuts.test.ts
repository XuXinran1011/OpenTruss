/**
 * useKeyboardShortcuts Hook 测试
 */

import { renderHook } from '@testing-library/react'
import { useKeyboardShortcuts } from '../useKeyboardShortcuts'
import { useWorkbenchStore } from '@/stores/workbench'
import { useCanvasStore } from '@/stores/canvas'
import { deleteElement } from '@/services/elements'
import { useToastContext } from '@/providers/ToastProvider'
import { TestWrapper } from '../../test-utils'

// Mock dependencies
jest.mock('@/stores/workbench', () => ({
  useWorkbenchStore: jest.fn(),
}))

jest.mock('@/stores/canvas', () => ({
  useCanvasStore: jest.fn(),
}))

jest.mock('@/services/elements', () => ({
  deleteElement: jest.fn(),
}))

jest.mock('@/providers/ToastProvider', () => ({
  useToastContext: jest.fn(),
}))

const mockUseWorkbenchStore = useWorkbenchStore as jest.MockedFunction<typeof useWorkbenchStore>
const mockUseCanvasStore = useCanvasStore as jest.MockedFunction<typeof useCanvasStore>
const mockDeleteElement = deleteElement as jest.MockedFunction<typeof deleteElement>
const mockUseToastContext = useToastContext as jest.MockedFunction<typeof useToastContext>

describe('useKeyboardShortcuts', () => {
  const mockSetMode = jest.fn()
  const mockSetSelectedElementIds = jest.fn()
  const mockSetDwgOpacity = jest.fn()
  const mockShowToast = jest.fn()
  const mockInvalidateQueries = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    mockUseWorkbenchStore.mockReturnValue({
      mode: 'trace',
      setMode: mockSetMode,
      selectedElementIds: [],
      setSelectedElementIds: mockSetSelectedElementIds,
    } as any)
    mockUseCanvasStore.mockReturnValue({
      dwgOpacity: 0.5,
      setDwgOpacity: mockSetDwgOpacity,
    } as any)
    mockUseToastContext.mockReturnValue({
      showToast: mockShowToast,
    } as any)
  })

  it('应该注册键盘快捷键', () => {
    renderHook(() => useKeyboardShortcuts(), {
      wrapper: TestWrapper,
    })

    // Hook应该成功注册，没有错误
    expect(mockUseWorkbenchStore).toHaveBeenCalled()
  })

  it('应该在按下T键时切换到Trace Mode', () => {
    renderHook(() => useKeyboardShortcuts(), {
      wrapper: TestWrapper,
    })

    const event = new KeyboardEvent('keydown', { key: 't' })
    Object.defineProperty(event, 'target', {
      value: document.body,
      writable: false,
    })
    event.preventDefault = jest.fn()

    window.dispatchEvent(event)

    expect(mockSetMode).toHaveBeenCalledWith('trace')
  })

  it('应该在按下L键时切换到Lift Mode', () => {
    renderHook(() => useKeyboardShortcuts(), {
      wrapper: TestWrapper,
    })

    const event = new KeyboardEvent('keydown', { key: 'l' })
    Object.defineProperty(event, 'target', {
      value: document.body,
      writable: false,
    })
    event.preventDefault = jest.fn()

    window.dispatchEvent(event)

    expect(mockSetMode).toHaveBeenCalledWith('lift')
  })

  it('应该在输入框中不处理快捷键', () => {
    renderHook(() => useKeyboardShortcuts(), {
      wrapper: TestWrapper,
    })

    const input = document.createElement('input')
    document.body.appendChild(input)
    input.focus()

    const event = new KeyboardEvent('keydown', { key: 't' })
    Object.defineProperty(event, 'target', {
      value: input,
      writable: false,
    })

    window.dispatchEvent(event)

    expect(mockSetMode).not.toHaveBeenCalled()
    document.body.removeChild(input)
  })
})
