/**
 * k6认证API性能测试
 * 
 * 使用方法：
 * k6 run --config k6.config.js auth.js
 * k6 run --env API_BASE_URL=http://localhost:8000 auth.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';
import { API_BASE_URL, API_VERSION } from './k6.config.js';

// 自定义指标
const loginSuccessRate = new Rate('login_success_rate');

// 测试配置
export const options = {
  thresholds: {
    login_success_rate: ['rate>0.95'], // 95%的登录请求应该成功
    http_req_duration: ['p(95)<500'],  // 95%的请求在500ms内
  },
};

// 测试数据
const TEST_USERS = [
  { username: 'editor', password: 'editor123' },
  { username: 'approver', password: 'approver123' },
  { username: 'pm', password: 'pm123' },
  { username: 'admin', password: 'admin123' },
];

// 初始化函数（每个虚拟用户运行一次）
export function setup() {
  return {
    baseUrl: API_BASE_URL,
    apiVersion: API_VERSION,
  };
}

// 默认函数（每个虚拟用户每次迭代运行）
export default function (data) {
  const baseUrl = data.baseUrl;
  const apiVersion = data.apiVersion;
  
  // 随机选择一个测试用户
  const user = TEST_USERS[Math.floor(Math.random() * TEST_USERS.length)];
  
  // 1. 登录
  const loginResponse = http.post(
    `${baseUrl}${apiVersion}/auth/login`,
    JSON.stringify({
      username: user.username,
      password: user.password,
    }),
    {
      headers: {
        'Content-Type': 'application/json',
      },
      tags: { name: 'POST /auth/login' },
    }
  );
  
  const loginSuccess = check(loginResponse, {
    'login status is 200': (r) => r.status === 200,
    'login response has token': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.data && body.data.access_token;
      } catch {
        return false;
      }
    },
  });
  
  loginSuccessRate.add(loginSuccess);
  
  if (!loginSuccess) {
    sleep(1);
    return;
  }
  
  // 解析token
  const loginBody = JSON.parse(loginResponse.body);
  const token = loginBody.data.access_token;
  
  // 2. 获取当前用户信息
  const meResponse = http.get(
    `${baseUrl}${apiVersion}/auth/me`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      tags: { name: 'GET /auth/me' },
    }
  );
  
  check(meResponse, {
    'get current user status is 200': (r) => r.status === 200,
    'get current user response has user data': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.data && body.data.username;
      } catch {
        return false;
      }
    },
  });
  
  sleep(1);
  
  // 3. 登出（可选）
  if (Math.random() > 0.5) {
    const logoutResponse = http.post(
      `${baseUrl}${apiVersion}/auth/logout`,
      null,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        tags: { name: 'POST /auth/logout' },
      }
    );
    
    check(logoutResponse, {
      'logout status is 200': (r) => r.status === 200,
    });
  }
  
  sleep(1);
}

