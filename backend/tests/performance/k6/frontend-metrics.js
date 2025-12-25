/**
 * k6前端性能指标收集
 * 
 * 注意：k6主要用于API性能测试，前端性能测试通常需要浏览器自动化工具
 * 这个脚本主要用于收集API相关的性能指标，这些指标会影响前端体验
 * 
 * 使用方法：
 * k6 run --config k6.config.js frontend-metrics.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend } from 'k6/metrics';
import { API_BASE_URL, API_VERSION } from './k6.config.js';

// 自定义指标：页面加载所需的关键API响应时间
const pageLoadTime = new Trend('page_load_time');
const apiResponseTime = new Trend('api_response_time');

export const options = {
  thresholds: {
    page_load_time: ['p(95)<2000'], // 页面加载时间应该在2秒内
    api_response_time: ['p(95)<500'],
  },
};

// 初始化
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
  
  // 模拟页面加载流程：并行请求多个关键API
  const startTime = Date.now();
  
  // 1. 获取项目列表
  const projectsResponse = http.get(
    `${data.baseUrl}${data.apiVersion}/hierarchy/projects?page=1&page_size=20`,
    { headers, tags: { name: 'Load: Projects' } }
  );
  
  // 2. 获取层级结构
  let projectId = null;
  if (projectsResponse.status === 200) {
    try {
      const projectsBody = JSON.parse(projectsResponse.body);
      if (projectsBody.data.items && projectsBody.data.items.length > 0) {
        projectId = projectsBody.data.items[0].id;
      }
    } catch {}
  }
  
  // 3. 并行请求（模拟前端同时发起多个请求）
  const requests = [
    http.get(
      `${data.baseUrl}${data.apiVersion}/elements?page=1&page_size=20`,
      { headers, tags: { name: 'Load: Elements' } }
    ),
  ];
  
  if (projectId) {
    requests.push(
      http.get(
        `${data.baseUrl}${data.apiVersion}/hierarchy/projects/${projectId}/hierarchy`,
        { headers, tags: { name: 'Load: Hierarchy' } }
      )
    );
  }
  
  // 等待所有请求完成
  const results = requests.map(r => {
    apiResponseTime.add(r.timings.duration);
    return check(r, {
      'API response successful': (resp) => resp.status === 200,
    });
  });
  
  // 计算总页面加载时间（从开始到最后一个请求完成）
  const loadTime = Date.now() - startTime;
  pageLoadTime.add(loadTime);
  
  check(null, {
    'all APIs loaded': () => results.every(r => r),
  });
  
  sleep(2);
}

