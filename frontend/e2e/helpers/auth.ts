/**
 * E2E测试 - 认证辅助函数
 */

import { Page, expect } from '@playwright/test';

/**
 * 测试用户凭据
 */
export const TEST_USERS = {
  editor: {
    username: 'editor',
    password: 'editor123',
    role: 'EDITOR',
  },
  approver: {
    username: 'approver',
    password: 'approver123',
    role: 'APPROVER',
  },
  pm: {
    username: 'pm',
    password: 'pm123',
    role: 'PM',
  },
  admin: {
    username: 'admin',
    password: 'admin123',
    role: 'ADMIN',
  },
} as const;

/**
 * 以Editor角色登录
 */
export async function loginAsEditor(page: Page): Promise<void> {
  await page.goto('/login');
  await page.fill('[name="username"], input[type="text"]', TEST_USERS.editor.username);
  await page.fill('[name="password"], input[type="password"]', TEST_USERS.editor.password);
  await page.click('button[type="submit"], button:has-text("登录")');
  
  // 等待跳转到工作台
  await page.waitForURL('/workbench', { timeout: 10000 });
  
  // 验证登录成功
  await expect(page).toHaveURL('/workbench');
}

/**
 * 以Approver角色登录
 */
export async function loginAsApprover(page: Page): Promise<void> {
  await page.goto('/login');
  await page.fill('[name="username"], input[type="text"]', TEST_USERS.approver.username);
  await page.fill('[name="password"], input[type="password"]', TEST_USERS.approver.password);
  await page.click('button[type="submit"], button:has-text("登录")');
  
  // 等待跳转到工作台
  await page.waitForURL('/workbench', { timeout: 10000 });
  
  // 验证登录成功
  await expect(page).toHaveURL('/workbench');
}

/**
 * 以PM角色登录
 */
export async function loginAsPM(page: Page): Promise<void> {
  await page.goto('/login');
  await page.fill('[name="username"], input[type="text"]', TEST_USERS.pm.username);
  await page.fill('[name="password"], input[type="password"]', TEST_USERS.pm.password);
  await page.click('button[type="submit"], button:has-text("登录")');
  
  // 等待跳转到工作台
  await page.waitForURL('/workbench', { timeout: 10000 });
  
  // 验证登录成功
  await expect(page).toHaveURL('/workbench');
}

/**
 * 以Admin角色登录
 */
export async function loginAsAdmin(page: Page): Promise<void> {
  await page.goto('/login');
  await page.fill('[name="username"], input[type="text"]', TEST_USERS.admin.username);
  await page.fill('[name="password"], input[type="password"]', TEST_USERS.admin.password);
  await page.click('button[type="submit"], button:has-text("登录")');
  
  // 等待跳转到工作台
  await page.waitForURL('/workbench', { timeout: 10000 });
  
  // 验证登录成功
  await expect(page).toHaveURL('/workbench');
}

/**
 * 通用登录函数
 */
export async function login(
  page: Page,
  username: string,
  password: string
): Promise<void> {
  await page.goto('/login');
  await page.fill('[name="username"], input[type="text"]', username);
  await page.fill('[name="password"], input[type="password"]', password);
  await page.click('button[type="submit"], button:has-text("登录")');
  
  // 等待跳转或错误提示
  await page.waitForTimeout(2000);
}

/**
 * 登出
 */
export async function logout(page: Page): Promise<void> {
  // 查找登出按钮（可能在顶部工具栏或用户菜单中）
  const logoutButton = page.locator('button:has-text("登出"), button:has-text("退出"), [data-testid="logout"]').first();
  
  if (await logoutButton.isVisible()) {
    await logoutButton.click();
    await page.waitForURL('/login', { timeout: 10000 });
  } else {
    // 如果没有找到登出按钮，直接导航到登录页
    await page.goto('/login');
  }
  
  // 验证已登出
  await expect(page).toHaveURL('/login');
}

/**
 * 检查是否已登录
 */
export async function isLoggedIn(page: Page): Promise<boolean> {
  const currentUrl = page.url();
  return !currentUrl.includes('/login');
}

/**
 * 获取当前用户信息（从localStorage或页面元素）
 */
export async function getCurrentUser(page: Page): Promise<{ username?: string; role?: string } | null> {
  // 尝试从localStorage获取
  const userInfo = await page.evaluate(() => {
    const userStr = localStorage.getItem('opentruss_user');
    if (userStr) {
      try {
        return JSON.parse(userStr);
      } catch {
        return null;
      }
    }
    return null;
  });
  
  return userInfo;
}

