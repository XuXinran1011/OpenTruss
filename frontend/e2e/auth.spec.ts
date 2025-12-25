/**
 * 认证流程E2E测试
 */

import { test, expect } from '@playwright/test';
import { loginAsEditor, loginAsApprover, loginAsPM, login, logout, TEST_USERS } from './helpers/auth';

test.describe('认证流程', () => {
  test.beforeEach(async ({ page }) => {
    // 每个测试前访问登录页
    await page.goto('/login');
  });

  test('应该显示登录页面', async ({ page }) => {
    await expect(page).toHaveURL('/login');
    // 检查登录表单元素
    await expect(page.locator('input[type="text"], input[name="username"]').first()).toBeVisible();
    await expect(page.locator('input[type="password"], input[name="password"]').first()).toBeVisible();
    await expect(page.locator('button[type="submit"], button:has-text("登录")').first()).toBeVisible();
  });

  test('Editor用户应该能够成功登录', async ({ page }) => {
    await loginAsEditor(page);
    
    // 验证已跳转到工作台
    await expect(page).toHaveURL('/workbench');
    
    // 验证用户信息显示（如果页面有显示）
    // 这里可以根据实际UI调整选择器
  });

  test('Approver用户应该能够成功登录', async ({ page }) => {
    await loginAsApprover(page);
    
    // 验证已跳转到工作台
    await expect(page).toHaveURL('/workbench');
  });

  test('PM用户应该能够成功登录', async ({ page }) => {
    await loginAsPM(page);
    
    // 验证已跳转到工作台
    await expect(page).toHaveURL('/workbench');
  });

  test('错误的用户名或密码应该显示错误信息', async ({ page }) => {
    await login(page, 'wrong_user', 'wrong_password');
    
    // 等待错误提示出现
    await page.waitForTimeout(2000);
    
    // 验证仍在登录页或显示错误信息
    const currentUrl = page.url();
    const hasError = await page.locator('text=/错误|失败|无效/i').isVisible().catch(() => false);
    
    expect(currentUrl.includes('/login') || hasError).toBeTruthy();
  });

  test('空用户名或密码应该显示验证错误', async ({ page }) => {
    // 尝试提交空表单
    await page.click('button[type="submit"], button:has-text("登录")');
    
    // 等待验证错误
    await page.waitForTimeout(1000);
    
    // 验证仍在登录页
    await expect(page).toHaveURL('/login');
  });

  test('登录后应该能够登出', async ({ page }) => {
    // 先登录
    await loginAsEditor(page);
    await expect(page).toHaveURL('/workbench');
    
    // 登出
    await logout(page);
    
    // 验证已返回登录页
    await expect(page).toHaveURL('/login');
  });

  test('未登录用户访问受保护页面应该重定向到登录页', async ({ page }) => {
    // 直接访问工作台
    await page.goto('/workbench');
    
    // 应该被重定向到登录页
    await expect(page).toHaveURL('/login');
  });

  test('登录后访问登录页应该重定向到工作台', async ({ page }) => {
    // 先登录
    await loginAsEditor(page);
    
    // 再次访问登录页
    await page.goto('/login');
    
    // 应该被重定向到工作台
    await expect(page).toHaveURL('/workbench');
  });
});

test.describe('权限控制', () => {
  test('Editor用户应该能够访问工作台', async ({ page }) => {
    await loginAsEditor(page);
    await expect(page).toHaveURL('/workbench');
  });

  test('Approver用户应该能够访问检验批管理页面', async ({ page }) => {
    await loginAsApprover(page);
    
    // 导航到检验批管理页面（如果存在）
    await page.goto('/lot-strategy');
    
    // 验证能够访问（不应该被重定向到登录页）
    const currentUrl = page.url();
    expect(currentUrl).not.toContain('/login');
  });
});

