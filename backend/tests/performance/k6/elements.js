/**
 * k6构件API性能测试
 * 
 * 使用方法：
 * k6 run --config k6.config.js elements.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter } from 'k6/metrics';
import { API_BASE_URL, API_VERSION } from './k6.config.js';

// 自定义指标
const elementsFetched = new Counter('elements_fetched');

export const options = {
  thresholds: {
    http_req_duration: ['p(95)<1000', 'p(99)<2000'], // 构件查询可能较慢
    http_req_failed: ['rate<0.05'],                   // 允许5%错误率（数据可能不存在）
  },
};

// 初始化：登录获取token
export function setup() {
  const loginResponse = http.post(
    `${API_BASE_URL}${API_VERSION}/auth/login`,
    JSON.stringify({
      username: 'editor',
      password: 'editor123',
    }),
    {
      headers: { 'Content-Type': 'application/json' },
    }
  );
  
  if (loginResponse.status === 200) {
    const body = JSON.parse(loginResponse.body);
    return {
      baseUrl: API_BASE_URL,
      apiVersion: API_VERSION,
      token: body.data.access_token,
    };
  }
  
  return {
    baseUrl: API_BASE_URL,
    apiVersion: API_VERSION,
    token: null,
  };
}

export default function (data) {
  if (!data.token) {
    sleep(1);
    return;
  }
  
  const headers = {
    'Authorization': `Bearer ${data.token}`,
    'Content-Type': 'application/json',
  };
  
  // 1. 查询构件列表
  const page = Math.floor(Math.random() * 10) + 1;
  const pageSize = [10, 20, 50][Math.floor(Math.random() * 3)];
  
  const listResponse = http.get(
    `${data.baseUrl}${data.apiVersion}/elements?page=${page}&page_size=${pageSize}`,
    {
      headers,
      tags: { name: 'GET /elements' },
    }
  );
  
  const listSuccess = check(listResponse, {
    'list elements status is 200': (r) => r.status === 200,
    'list elements has items': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.data && Array.isArray(body.data.items);
      } catch {
        return false;
      }
    },
  });
  
  if (listSuccess) {
    try {
      const body = JSON.parse(listResponse.body);
      const count = body.data.items ? body.data.items.length : 0;
      elementsFetched.add(count);
    } catch {}
  }
  
  sleep(1);
  
  // 2. 带筛选条件查询（随机选择）
  if (Math.random() > 0.5) {
    const speckleType = ['Wall', 'Floor', 'Column'][Math.floor(Math.random() * 3)];
    const filterResponse = http.get(
      `${data.baseUrl}${data.apiVersion}/elements?speckle_type=${speckleType}&page=1&page_size=20`,
      {
        headers,
        tags: { name: 'GET /elements (filtered)' },
      }
    );
    
    check(filterResponse, {
      'filtered elements status is 200': (r) => r.status === 200,
    });
    
    sleep(1);
  }
  
  // 3. 批量获取构件详情（随机执行）
  if (Math.random() > 0.7) {
    const elementIds = Array.from({ length: 5 }, (_, i) => `element_${Math.floor(Math.random() * 1000)}`);
    const batchResponse = http.post(
      `${data.baseUrl}${data.apiVersion}/elements/batch-details`,
      JSON.stringify({ element_ids: elementIds }),
      {
        headers,
        tags: { name: 'POST /elements/batch-details' },
      }
    );
    
    check(batchResponse, {
      'batch details status is 200': (r) => r.status === 200,
    });
    
    sleep(1);
  }
  
  sleep(1);
}

