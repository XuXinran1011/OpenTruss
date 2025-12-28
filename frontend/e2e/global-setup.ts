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
