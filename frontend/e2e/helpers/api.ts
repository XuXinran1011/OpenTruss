/**
 * E2E测试 - API调用辅助函数
 * 
 * 用于测试数据准备和清理
 */

import { APIResponse } from '@playwright/test';

const API_BASE_URL = process.env.PLAYWRIGHT_API_BASE_URL || 'http://localhost:8000/api/v1';

/**
 * 获取认证Token
 */
export async function getAuthToken(
  username: string,
  password: string
): Promise<string | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password }),
    });
    
    if (!response.ok) {
      return null;
    }
    
    const data = await response.json();
    return data.data?.access_token || null;
  } catch (error) {
    console.error('获取Token失败:', error);
    return null;
  }
}

/**
 * 创建测试项目
 */
export async function createTestProject(
  token: string,
  projectId: string,
  name: string
): Promise<boolean> {
  try {
    // 注意：如果项目创建API不存在，可能需要通过数据摄入API创建
    // 这里假设有项目创建API，实际可能需要调整
    const response = await fetch(`${API_BASE_URL}/hierarchy/projects`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ id: projectId, name }),
    });
    
    return response.ok;
  } catch (error) {
    console.error('创建项目失败:', error);
    return false;
  }
}

/**
 * 创建测试构件（通过数据摄入API）
 */
export async function createTestElement(
  token: string,
  projectId: string,
  elementData: any
): Promise<string | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/ingest`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        project_id: projectId,
        elements: [elementData],
      }),
    });
    
    if (!response.ok) {
      return null;
    }
    
    const data = await response.json();
    return data.data?.element_ids?.[0] || null;
  } catch (error) {
    console.error('创建构件失败:', error);
    return null;
  }
}

/**
 * 创建测试检验批
 */
export async function createTestLot(
  token: string,
  itemId: string,
  ruleType: 'BY_LEVEL' | 'BY_ZONE' | 'BY_LEVEL_AND_ZONE' = 'BY_LEVEL'
): Promise<string | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/inspection-lots/strategy`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        item_id: itemId,
        rule_type: ruleType,
      }),
    });
    
    if (!response.ok) {
      return null;
    }
    
    const data = await response.json();
    return data.data?.lots_created?.[0]?.id || null;
  } catch (error) {
    console.error('创建检验批失败:', error);
    return null;
  }
}

/**
 * 清理测试数据（删除测试项目）
 */
export async function cleanupTestData(
  token: string,
  projectId: string
): Promise<boolean> {
  try {
    // 注意：如果项目删除API不存在，可能需要手动清理
    // 这里假设有项目删除API，实际可能需要调整
    const response = await fetch(`${API_BASE_URL}/hierarchy/projects/${projectId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    
    return response.ok;
  } catch (error) {
    console.error('清理测试数据失败:', error);
    return false;
  }
}

/**
 * 等待API响应
 */
export async function waitForAPI(
  url: string,
  options: {
    token?: string;
    method?: string;
    body?: any;
    expectedStatus?: number;
    timeout?: number;
  } = {}
): Promise<APIResponse> {
  const { token, method = 'GET', body, expectedStatus = 200, timeout = 10000 } = options;
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const startTime = Date.now();
  
  while (Date.now() - startTime < timeout) {
    try {
      const response = await fetch(url, {
        method,
        headers,
        body: body ? JSON.stringify(body) : undefined,
      });
      
      if (response.status === expectedStatus) {
        return response as any;
      }
      
      await new Promise(resolve => setTimeout(resolve, 500));
    } catch (error) {
      await new Promise(resolve => setTimeout(resolve, 500));
    }
  }
  
  throw new Error(`API请求超时: ${url}`);
}

