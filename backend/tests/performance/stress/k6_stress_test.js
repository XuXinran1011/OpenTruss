/**
 * k6压力测试场景
 * 
 * 包括：
 * 1. 渐进式负载测试（逐步增加负载）
 * 2. Spike测试（突发流量）
 * 3. 长时间运行稳定性测试
 * 
 * 使用方法：
 * k6 run --config k6.config.js k6_stress_test.js
 * 
 * 渐进式负载：
 * k6 run --env STRESS_TYPE=ramp k6_stress_test.js
 * 
 * Spike测试：
 * k6 run --env STRESS_TYPE=spike k6_stress_test.js
 * 
 * 长时间运行：
 * k6 run --env STRESS_TYPE=endurance k6_stress_test.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';

const API_BASE_URL = __ENV.API_BASE_URL || 'http://localhost:8000';
const API_VERSION = '/api/v1';

const STRESS_TYPE = __ENV.STRESS_TYPE || 'ramp';

// 根据测试类型选择不同的配置
export const options = (() => {
  if (STRESS_TYPE === 'spike') {
    // Spike测试：突发流量
    return {
      scenarios: {
        spike: {
          executor: 'ramping-vus',
          startVUs: 0,
          stages: [
            { duration: '10s', target: 100 },   // 10秒内增加到100个用户
            { duration: '1m', target: 100 },    // 保持100个用户1分钟
            { duration: '10s', target: 200 },   // 10秒内增加到200个用户（峰值）
            { duration: '30s', target: 200 },   // 保持200个用户30秒
            { duration: '10s', target: 0 },     // 10秒内减少到0
          ],
        },
      },
      thresholds: {
        http_req_duration: ['p(95)<2000'], // Spike测试时允许更长的响应时间
        http_req_failed: ['rate<0.1'],      // 允许10%错误率
      },
    };
  } else if (STRESS_TYPE === 'endurance') {
    // 长时间运行稳定性测试
    return {
      scenarios: {
        endurance: {
          executor: 'constant-vus',
          vus: 50,
          duration: '30m', // 运行30分钟
        },
      },
      thresholds: {
        http_req_duration: ['p(95)<1000'],
        http_req_failed: ['rate<0.02'], // 长时间运行要求更低的错误率
      },
    };
  } else {
    // 默认：渐进式负载测试
    return {
      scenarios: {
        ramp: {
          executor: 'ramping-vus',
          startVUs: 0,
          stages: [
            { duration: '1m', target: 50 },
            { duration: '2m', target: 100 },
            { duration: '2m', target: 150 },
            { duration: '2m', target: 200 },
            { duration: '2m', target: 300 },
            { duration: '2m', target: 400 },
            { duration: '2m', target: 500 }, // 达到500个用户
            { duration: '5m', target: 500 }, // 保持500个用户5分钟
            { duration: '2m', target: 0 },   // 逐步减少
          ],
        },
      },
      thresholds: {
        http_req_duration: ['p(95)<2000', 'p(99)<5000'],
        http_req_failed: ['rate<0.05'],
      },
    };
  }
})();

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
    sleep(0.5);
    return;
  }
  
  const headers = {
    'Authorization': `Bearer ${data.token}`,
    'Content-Type': 'application/json',
  };
  
  // 执行各种API调用
  const requests = [
    // 查询构件
    http.get(
      `${data.baseUrl}${data.apiVersion}/elements?page=1&page_size=20`,
      { headers, tags: { name: 'Stress: GET /elements' } }
    ),
    // 查询项目
    http.get(
      `${data.baseUrl}${data.apiVersion}/hierarchy/projects?page=1&page_size=10`,
      { headers, tags: { name: 'Stress: GET /projects' } }
    ),
    // 获取用户信息
    http.get(
      `${data.baseUrl}${data.apiVersion}/auth/me`,
      { headers, tags: { name: 'Stress: GET /auth/me' } }
    ),
  ];
  
  // 检查所有请求
  requests.forEach(response => {
    check(response, {
      'status is 200': (r) => r.status === 200,
    });
  });
  
  sleep(0.5);
}

