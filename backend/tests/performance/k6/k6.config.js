/**
 * k6性能测试配置
 * 
 * 使用方法：
 * k6 run --config k6.config.js auth.js
 */

export const options = {
  // 场景配置
  scenarios: {
    // 默认场景
    default_scenario: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '30s', target: 10 },   // 30秒内增加到10个虚拟用户
        { duration: '1m', target: 10 },    // 保持10个用户1分钟
        { duration: '30s', target: 50 },   // 30秒内增加到50个用户
        { duration: '2m', target: 50 },    // 保持50个用户2分钟
        { duration: '30s', target: 0 },    // 30秒内减少到0个用户
      ],
      gracefulRampDown: '30s',
    },
  },

  // 阈值配置（性能指标）
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'], // 95%的请求在500ms内，99%在1000ms内
    http_req_failed: ['rate<0.01'],                  // 错误率小于1%
    http_reqs: ['rate>10'],                          // 每秒请求数大于10
  },

  // 测试主机（可以通过命令行覆盖：k6 run --env API_BASE_URL=http://localhost:8000 script.js）
  ext: {
    loadimpact: {
      name: 'OpenTruss API Performance Test',
    },
  },
};

// 全局配置
export const API_BASE_URL = __ENV.API_BASE_URL || 'http://localhost:8000';
export const API_VERSION = '/api/v1';

