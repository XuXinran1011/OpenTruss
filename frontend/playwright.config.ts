import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2E测试配置
 * 
 * 参考文档: https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  // 全局设置文件
  globalSetup: require.resolve('./e2e/global-setup.ts'),
  
  // 测试目录
  testDir: './e2e',
  
  // 测试超时时间（60秒，确保有足够时间等待页面加载）
  timeout: 60000,
  
  // 每个测试的超时时间
  expect: {
    timeout: 5000,
  },
  
  // 测试失败时重试次数
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 2 : undefined,
  
  // 报告配置
  reporter: [
    ['html'],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/junit.xml' }],
  ],
  
  // 共享配置
  use: {
    // 基础URL
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000',
    
    // 截图配置
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',
    
    // 请求超时
    actionTimeout: 10000,
    navigationTimeout: 30000,
    
    // 复用登录状态（如果存在）
    storageState: process.env.CI ? undefined : 'playwright/.auth/user.json',
  },

  // 配置测试项目（CI环境只测试Chromium）
  projects: process.env.CI
    ? [
        {
          name: 'chromium',
          use: { ...devices['Desktop Chrome'] },
        },
      ]
    : [
        {
          name: 'chromium',
          use: { ...devices['Desktop Chrome'] },
        },
        {
          name: 'firefox',
          use: { ...devices['Desktop Firefox'] },
        },
        {
          name: 'webkit',
          use: { ...devices['Desktop Safari'] },
        },
      ],

  // Web服务器配置（可选，用于启动开发服务器）
  // webServer: {
  //   command: 'npm run dev',
  //   url: 'http://localhost:3000',
  //   reuseExistingServer: !process.env.CI,
  //   timeout: 120000,
  // },
});

