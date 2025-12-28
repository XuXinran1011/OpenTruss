/**
 * Playwright全局设置
 * 在所有测试运行前执行一次，用于准备测试环境（如登录、保存状态等）
 */

import { chromium, FullConfig } from '@playwright/test';
import * as path from 'path';
import * as fs from 'fs';
import { TEST_USERS } from './helpers/auth';

async function globalSetup(config: FullConfig) {
  const { baseURL } = config.projects[0].use;
  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    // 导航到登录页面
    await page.goto(`${baseURL}/login`);

    // 使用Editor用户登录
    await page.fill('[name="username"], input[type="text"]', TEST_USERS.editor.username);
    await page.fill('[name="password"], input[type="password"]', TEST_USERS.editor.password);
    await page.click('button[type="submit"], button:has-text("登录")');

    // 等待登录成功
    await page.waitForURL(`${baseURL}/workbench`, { timeout: 10000 });
    await page.waitForLoadState('networkidle', { timeout: 15000 });

    // 确保目录存在
    const authDir = path.join(process.cwd(), 'playwright', '.auth');
    if (!fs.existsSync(authDir)) {
      fs.mkdirSync(authDir, { recursive: true });
    }

    // 保存登录状态
    await page.context().storageState({ path: path.join(authDir, 'user.json') });

    console.log('登录状态已保存到 playwright/.auth/user.json');
    
    // 验证项目数据是否存在（可选验证，不阻止测试运行）
    // 注意：在CI环境中，后端服务器可能在global-setup之后启动，所以这个验证可能会失败
    // 这是可接受的，因为数据已经在CI步骤中准备了
    try {
      const apiBaseUrl = process.env.PLAYWRIGHT_API_BASE_URL || baseURL?.replace(':3000', ':8000') || 'http://localhost:8000';
      const response = await page.request.get(`${apiBaseUrl}/api/v1/hierarchy/projects?page=1&page_size=1`);
      
      if (response.ok()) {
        const data = await response.json().catch(() => null);
        if (data?.data?.items && data.data.items.length > 0) {
          console.log(`✓ 测试数据验证通过：找到 ${data.data.items.length} 个项目`);
        } else {
          console.warn('⚠ 警告：测试环境没有项目数据，某些测试可能失败');
          console.warn('  请确保在测试开始前运行：python -m scripts.create_demo_data');
        }
      } else {
        console.warn(`⚠ 无法验证测试数据：API响应状态 ${response.status()}`);
      }
    } catch (error) {
      // 如果API不可用（例如后端未启动），只记录警告，不阻止测试
      console.warn('⚠ 无法验证测试数据（API可能未启动或数据未准备）：', error instanceof Error ? error.message : error);
      console.warn('  在CI环境中，这是正常的，因为数据会在测试开始前准备');
    }
  } catch (error) {
    console.error('全局设置失败:', error);
    // 如果登录失败，仍然创建目录（测试可能会失败，但至少结构是正确的）
    const authDir = path.join(process.cwd(), 'playwright', '.auth');
    if (!fs.existsSync(authDir)) {
      fs.mkdirSync(authDir, { recursive: true });
    }
    throw error;
  } finally {
    await browser.close();
  }
}

export default globalSetup;
