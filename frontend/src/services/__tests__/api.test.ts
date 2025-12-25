/**
 * API服务测试
 */

import { ApiError, apiFetch, apiGet, apiPost, apiPatch, apiDelete } from '../api'
import { getToken } from '@/lib/auth/token'

// Mock token
jest.mock('@/lib/auth/token', () => ({
  getToken: jest.fn(),
}))

const mockGetToken = getToken as jest.MockedFunction<typeof getToken>

// Mock global fetch
global.fetch = jest.fn()
const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>

describe('ApiError', () => {
  it('应该正确创建ApiError实例', () => {
    const error = new ApiError('Test error', 404)
    
    expect(error.message).toBe('Test error')
    expect(error.statusCode).toBe(404)
    expect(error).toBeInstanceOf(Error)
  })
})

describe('apiFetch', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockGetToken.mockReturnValue('test-token')
  })

  it('应该成功发送GET请求', async () => {
    const mockResponse = { data: 'test' }
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockResponse,
    } as Response)
    
    const result = await apiFetch('/api/test')
    
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/test'),
      expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({
          'Authorization': 'Bearer test-token',
        }),
      })
    )
    expect(result).toEqual(mockResponse)
  })

  it('应该在请求头中包含token', async () => {
    mockGetToken.mockReturnValue('my-token')
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({}),
    } as Response)
    
    await apiFetch('/api/test')
    
    expect(mockFetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({
          'Authorization': 'Bearer my-token',
        }),
      })
    )
  })

  it('应该在没有token时不包含Authorization头', async () => {
    mockGetToken.mockReturnValue(null)
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({}),
    } as Response)
    
    await apiFetch('/api/test')
    
    const callArgs = mockFetch.mock.calls[0][1] as RequestInit
    expect(callArgs.headers).not.toHaveProperty('Authorization')
  })

  it('应该支持POST请求和body', async () => {
    const requestBody = { name: 'test' }
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({}),
    } as Response)
    
    await apiFetch('/api/test', {
      method: 'POST',
      body: JSON.stringify(requestBody),
    })
    
    expect(mockFetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify(requestBody),
      })
    )
  })

  it('应该在401错误时抛出ApiError', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 401,
      statusText: 'Unauthorized',
      json: async () => ({ detail: 'Unauthorized' }),
    } as Response)
    
    await expect(apiFetch('/api/test')).rejects.toThrow(ApiError)
    await expect(apiFetch('/api/test')).rejects.toThrow('Unauthorized')
  })

  it('应该在404错误时抛出ApiError', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 404,
      statusText: 'Not Found',
      json: async () => ({ detail: 'Not Found' }),
    } as Response)
    
    await expect(apiFetch('/api/test')).rejects.toThrow(ApiError)
    
    try {
      await apiFetch('/api/test')
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError)
      expect((error as ApiError).statusCode).toBe(404)
    }
  })

  it('应该在500错误时抛出ApiError', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      json: async () => ({ detail: 'Internal Server Error' }),
    } as Response)
    
    await expect(apiFetch('/api/test')).rejects.toThrow(ApiError)
    
    try {
      await apiFetch('/api/test')
    } catch (error) {
      expect((error as ApiError).statusCode).toBe(500)
    }
  })

  it('应该在响应无法解析为JSON时使用状态文本', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      json: async () => {
        throw new Error('Invalid JSON')
      },
    } as Response)
    
    await expect(apiFetch('/api/test')).rejects.toThrow('Internal Server Error')
  })

  it('应该使用baseURL配置', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({}),
    } as Response)
    
    await apiFetch('/api/test')
    
    const callUrl = mockFetch.mock.calls[0][0] as string
    // 检查URL是否以/api/test开头或包含它（因为baseURL可能是相对路径）
    expect(callUrl).toContain('/api/test')
  })
})

describe('apiGet', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockGetToken.mockReturnValue('test-token')
  })

  it('应该发送GET请求', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ data: 'test' }),
    } as Response)
    
    await apiGet('/api/test')
    
    expect(mockFetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        method: 'GET',
      })
    )
  })
})

describe('apiPost', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockGetToken.mockReturnValue('test-token')
  })

  it('应该发送POST请求', async () => {
    const body = { name: 'test' }
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({}),
    } as Response)
    
    await apiPost('/api/test', body)
    
    expect(mockFetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify(body),
        headers: expect.objectContaining({
          'Content-Type': 'application/json',
        }),
      })
    )
  })
})

describe('apiPatch', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockGetToken.mockReturnValue('test-token')
  })

  it('应该发送PATCH请求', async () => {
    const body = { name: 'updated' }
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({}),
    } as Response)
    
    await apiPatch('/api/test', body)
    
    expect(mockFetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        method: 'PATCH',
        body: JSON.stringify(body),
      })
    )
  })
})

describe('apiDelete', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockGetToken.mockReturnValue('test-token')
  })

  it('应该发送DELETE请求', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({}),
    } as Response)
    
    await apiDelete('/api/test')
    
    expect(mockFetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        method: 'DELETE',
      })
    )
  })
})

