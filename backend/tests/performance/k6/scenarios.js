/**
 * k6场景化性能测试
 * 
 * 模拟真实用户工作流（Editor和Approver）
 * 
 * 使用方法：
 * k6 run --config k6.config.js scenarios.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { API_BASE_URL, API_VERSION } from './k6.config.js';

export const options = {
  scenarios: {
    // Editor用户场景
    editor_workflow: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '30s', target: 5 },
        { duration: '2m', target: 5 },
        { duration: '30s', target: 0 },
      ],
      exec: 'editorWorkflow',
    },
    
    // Approver用户场景
    approver_workflow: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '30s', target: 2 },
        { duration: '2m', target: 2 },
        { duration: '30s', target: 0 },
      ],
      exec: 'approverWorkflow',
    },
  },
  
  thresholds: {
    http_req_duration: ['p(95)<1000'],
    http_req_failed: ['rate<0.05'],
  },
};

// Editor工作流
export function editorWorkflow() {
  // 登录
  const loginResponse = http.post(
    `${API_BASE_URL}${API_VERSION}/auth/login`,
    JSON.stringify({
      username: 'editor',
      password: 'editor123',
    }),
    {
      headers: { 'Content-Type': 'application/json' },
      tags: { name: 'Editor Login' },
    }
  );
  
  if (loginResponse.status !== 200) {
    sleep(1);
    return;
  }
  
  const loginBody = JSON.parse(loginResponse.body);
  const token = loginBody.data.access_token;
  const headers = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  };
  
  sleep(1);
  
  // 1. 获取项目列表
  const projectsResponse = http.get(
    `${API_BASE_URL}${API_VERSION}/hierarchy/projects?page=1&page_size=20`,
    { headers, tags: { name: 'Editor: Get Projects' } }
  );
  
  check(projectsResponse, {
    'projects fetched': (r) => r.status === 200,
  });
  
  sleep(1);
  
  // 2. 查询构件
  const elementsResponse = http.get(
    `${API_BASE_URL}${API_VERSION}/elements?page=1&page_size=20`,
    { headers, tags: { name: 'Editor: Get Elements' } }
  );
  
  check(elementsResponse, {
    'elements fetched': (r) => r.status === 200,
  });
  
  sleep(2);
  
  // 3. 更新构件拓扑（随机执行）
  if (Math.random() > 0.5) {
    const elementId = `element_${Math.floor(Math.random() * 1000)}`;
    const updateResponse = http.patch(
      `${API_BASE_URL}${API_VERSION}/elements/${elementId}/topology`,
      JSON.stringify({
        geometry_2d: {
          type: 'Polyline',
          coordinates: [[0, 0], [10, 0], [10, 5], [0, 5]],
          closed: true,
        },
      }),
      { headers, tags: { name: 'Editor: Update Topology' } }
    );
    
    check(updateResponse, {
      'topology updated': (r) => r.status === 200 || r.status === 404, // 404表示元素不存在，可接受
    });
    
    sleep(1);
  }
}

// Approver工作流
export function approverWorkflow() {
  // 登录
  const loginResponse = http.post(
    `${API_BASE_URL}${API_VERSION}/auth/login`,
    JSON.stringify({
      username: 'approver',
      password: 'approver123',
    }),
    {
      headers: { 'Content-Type': 'application/json' },
      tags: { name: 'Approver Login' },
    }
  );
  
  if (loginResponse.status !== 200) {
    sleep(1);
    return;
  }
  
  const loginBody = JSON.parse(loginResponse.body);
  const token = loginBody.data.access_token;
  const headers = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  };
  
  sleep(1);
  
  // 1. 获取项目层级（查看检验批）
  const projectsResponse = http.get(
    `${API_BASE_URL}${API_VERSION}/hierarchy/projects?page=1&page_size=10`,
    { headers, tags: { name: 'Approver: Get Projects' } }
  );
  
  check(projectsResponse, {
    'projects fetched': (r) => r.status === 200,
  });
  
  sleep(2);
  
  // 2. 查看审批历史（随机执行）
  if (Math.random() > 0.5) {
    const lotId = `lot_${Math.floor(Math.random() * 100)}`;
    const historyResponse = http.get(
      `${API_BASE_URL}${API_VERSION}/inspection-lots/${lotId}/approval-history`,
      { headers, tags: { name: 'Approver: Get Approval History' } }
    );
    
    check(historyResponse, {
      'history fetched': (r) => r.status === 200 || r.status === 404,
    });
    
    sleep(1);
  }
  
  // 3. 审批检验批（随机执行）
  if (Math.random() > 0.7) {
    const lotId = `lot_${Math.floor(Math.random() * 100)}`;
    const approveResponse = http.post(
      `${API_BASE_URL}${API_VERSION}/inspection-lots/${lotId}/approve`,
      JSON.stringify({ comment: 'k6 performance test approval' }),
      { headers, tags: { name: 'Approver: Approve Lot' } }
    );
    
    check(approveResponse, {
      'lot approved': (r) => r.status === 200 || r.status === 404 || r.status === 400,
    });
    
    sleep(1);
  }
}

