/**
 * useAuth Hook 测试
 */

import { renderHook, act, waitFor } from '@testing-library/react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../useAuth'
import { login as loginService, logout as logoutService } from '@/services/auth'
import { useAuthStore } from '@/stores/auth'
import { ApiError } from '@/services/api'

// Mock dependencies
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}))

jest.mock('@/services/auth', () => ({
  login: jest.fn(),
  logout: jest.fn(),
}))

jest.mock('@/stores/auth', () => ({
  useAuthStore: jest.fn(),
}))

const mockUseRouter = useRouter as jest.MockedFunction<typeof useRouter>
const mockLoginService = loginService as jest.MockedFunction<typeof loginService>
const mockLogoutService = logoutService as jest.MockedFunction<typeof logoutService>
const mockUseAuthStore = useAuthStore as jest.MockedFunction<typeof useAuthStore>

describe('useAuth', () => {
  const mockPush = jest.fn()
  const mockSetAuth = jest.fn()
  const mockClearAuth = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    
    mockUseRouter.mockReturnValue({
      push: mockPush,
    } as any)
    
    mockUseAuthStore.mockReturnValue({
      setAuth: mockSetAuth,
      clearAuth: mockClearAuth,
      isAuthenticated: false,
      currentUser: null,
    } as any)
  })

  describe('login', () => {
    it('应该成功登录并跳转到工作台', async () => {
      const mockTokenInfo = {
        access_token: 'test-token',
        user: {
          id: 'user-1',
          username: 'testuser',
          role: 'EDITOR',
        },
      }
      
      mockLoginService.mockResolvedValue(mockTokenInfo)
      
      const { result } = renderHook(() => useAuth())
      
      await act(async () => {
        await result.current.login({
          username: 'testuser',
          password: 'password123',
        })
      })
      
      expect(mockLoginService).toHaveBeenCalledWith({
        username: 'testuser',
        password: 'password123',
      })
      expect(mockSetAuth).toHaveBeenCalledWith(mockTokenInfo)
      expect(mockPush).toHaveBeenCalledWith('/workbench')
      expect(result.current.error).toBeNull()
    })

    it('应该在登录失败时设置错误', async () => {
      const mockError = new ApiError('Invalid credentials', 401)
      mockLoginService.mockRejectedValue(mockError)
      
      const { result } = renderHook(() => useAuth())
      
      await act(async () => {
        try {
          await result.current.login({
            username: 'testuser',
            password: 'wrongpassword',
          })
        } catch (err) {
          // Expected to throw
        }
      })
      
      await waitFor(() => {
        expect(result.current.error).not.toBeNull()
      })
      
      expect(result.current.error?.message).toContain('Invalid credentials')
      expect(mockSetAuth).not.toHaveBeenCalled()
      expect(mockPush).not.toHaveBeenCalled()
    })

    it('应该在登录过程中设置loading状态', async () => {
      let resolveLogin: (value: any) => void
      const loginPromise = new Promise((resolve) => {
        resolveLogin = resolve
      })
      
      mockLoginService.mockReturnValue(loginPromise as any)
      
      const { result } = renderHook(() => useAuth())
      
      act(() => {
        result.current.login({
          username: 'testuser',
          password: 'password123',
        })
      })
      
      expect(result.current.isLoading).toBe(true)
      
      await act(async () => {
        resolveLogin!({
          access_token: 'test-token',
          user: { id: 'user-1', username: 'testuser', role: 'EDITOR' },
        })
        await loginPromise
      })
      
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })
    })
  })

  describe('logout', () => {
    it('应该成功登出并跳转到登录页', async () => {
      mockLogoutService.mockResolvedValue(undefined)
      
      const { result } = renderHook(() => useAuth())
      
      await act(async () => {
        await result.current.logout()
      })
      
      expect(mockClearAuth).toHaveBeenCalled()
      expect(mockPush).toHaveBeenCalledWith('/login')
    })

    it('应该在登出API失败时仍清除本地状态', async () => {
      mockLogoutService.mockRejectedValue(new Error('Network error'))
      
      const { result } = renderHook(() => useAuth())
      
      await act(async () => {
        await result.current.logout()
      })
      
      expect(mockClearAuth).toHaveBeenCalled()
      expect(mockPush).toHaveBeenCalledWith('/login')
    })
  })

  describe('clearError', () => {
    it('应该清除错误状态', async () => {
      mockLoginService.mockRejectedValue(new ApiError('Test error', 500))
      
      const { result } = renderHook(() => useAuth())
      
      await act(async () => {
        try {
          await result.current.login({
            username: 'testuser',
            password: 'password123',
          })
        } catch (err) {
          // Expected to throw
        }
      })
      
      await waitFor(() => {
        expect(result.current.error).not.toBeNull()
      })
      
      act(() => {
        result.current.clearError()
      })
      
      expect(result.current.error).toBeNull()
    })
  })

  describe('状态管理', () => {
    it('应该返回认证状态和用户信息', () => {
      mockUseAuthStore.mockReturnValue({
        setAuth: mockSetAuth,
        clearAuth: mockClearAuth,
        isAuthenticated: true,
        currentUser: {
          id: 'user-1',
          username: 'testuser',
          role: 'EDITOR',
        },
      } as any)
      
      const { result } = renderHook(() => useAuth())
      
      expect(result.current.isAuthenticated).toBe(true)
      expect(result.current.currentUser).toEqual({
        id: 'user-1',
        username: 'testuser',
        role: 'EDITOR',
      })
    })
  })
})

