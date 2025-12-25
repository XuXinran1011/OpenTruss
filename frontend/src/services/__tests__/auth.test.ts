/**
 * auth Service 测试
 */

import { login, logout, getCurrentUserInfo } from '../auth'
import { apiPost, apiGet } from '../api'
import { ApiError } from '../api'

// Mock api
jest.mock('../api', () => ({
  apiPost: jest.fn(),
  apiGet: jest.fn(),
  ApiError: class ApiError extends Error {
    constructor(message: string, public statusCode: number) {
      super(message)
      this.name = 'ApiError'
    }
  },
}))

const mockApiPost = apiPost as jest.MockedFunction<typeof apiPost>
const mockApiGet = apiGet as jest.MockedFunction<typeof apiGet>

describe('auth Service', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('login', () => {
    it('应该成功登录', async () => {
      const mockResponse = {
        status: 'success',
        data: {
          access_token: 'test-token',
          user: {
            id: 'user-1',
            username: 'testuser',
            role: 'EDITOR',
          },
        },
      }
      
      mockApiPost.mockResolvedValue(mockResponse)
      
      const result = await login({
        username: 'testuser',
        password: 'password123',
      })
      
      expect(mockApiPost).toHaveBeenCalledWith('/api/v1/auth/login', {
        username: 'testuser',
        password: 'password123',
      })
      expect(result).toEqual(mockResponse.data)
    })

    it('应该在登录失败时抛出错误', async () => {
      const mockError = new ApiError('Invalid credentials', 401)
      mockApiPost.mockRejectedValue(mockError)
      
      await expect(
        login({
          username: 'testuser',
          password: 'wrongpassword',
        })
      ).rejects.toThrow('Invalid credentials')
    })
  })

  describe('logout', () => {
    it('应该成功登出', async () => {
      mockApiPost.mockResolvedValue({})
      
      await logout()
      
      expect(mockApiPost).toHaveBeenCalledWith('/api/v1/auth/logout')
    })

    it('应该在登出失败时不抛出错误', async () => {
      const mockError = new ApiError('Logout failed', 500)
      mockApiPost.mockRejectedValue(mockError)
      
      // logout应该不抛出错误，即使API调用失败
      await expect(logout()).resolves.not.toThrow()
    })
  })

  describe('getCurrentUserInfo', () => {
    it('应该成功获取当前用户信息', async () => {
      const mockResponse = {
        status: 'success',
        data: {
          id: 'user-1',
          username: 'testuser',
          role: 'EDITOR',
        },
      }
      
      mockApiGet.mockResolvedValue(mockResponse)
      
      const result = await getCurrentUserInfo()
      
      expect(mockApiGet).toHaveBeenCalledWith('/api/v1/auth/me')
      expect(result).toEqual(mockResponse.data)
    })

    it('应该在获取失败时抛出错误', async () => {
      const mockError = new ApiError('Unauthorized', 401)
      mockApiGet.mockRejectedValue(mockError)
      
      await expect(getCurrentUserInfo()).rejects.toThrow('Unauthorized')
    })
  })
})

