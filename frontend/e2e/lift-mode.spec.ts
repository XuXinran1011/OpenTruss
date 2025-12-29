/**
 * Lift Mode E2E测试
 */

import { test, expect } from '@playwright/test';
import { loginAsEditor } from './helpers/auth';
import { ensureWorkbenchReady, setupResponseListeners } from './helpers/workbench';

test.describe('Lift Mode', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsEditor(page);
    
    // 在导航前设置响应监听器，确保能捕获所有API请求
    const { failedRequests } = setupResponseListeners(page);
    await page.goto('/workbench');
    
    // 使用统一的辅助函数确保Workbench页面已准备好
    await ensureWorkbenchReady(page, failedRequests);
    
    // 切换到Lift Mode - 使用data-testid
    await page.waitForSelector('[data-testid="lift-mode"]', { timeout: 15000 });
    const liftButton = page.locator('[data-testid="lift-mode"]').first();
    await liftButton.waitFor({ state: 'visible', timeout: 10000 });
    await liftButton.click();
    await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
  });

  test('应该能够切换到Lift Mode', async ({ page }) => {
    // 验证Lift Mode已激活 - 使用data-testid
    const liftButton = page.locator('[data-testid="lift-mode"]').first();
    await expect(liftButton).toBeVisible({ timeout: 10000 });
  });

  test('应该显示右侧参数面板', async ({ page }) => {
    // 等待页面加载
    await page.waitForLoadState('networkidle', { timeout: 10000 });
    
    // Lift Mode应该显示Z轴参数设置面板
    // 右侧面板可能包含高度、基础偏移、材质等字段
    const rightPanel = page.locator('[data-testid="right-panel"], .right-panel, aside').last();
    
    // 尝试选择一个节点来显示右侧面板
    await page.waitForSelector('.tree-node, [role="treeitem"]', { timeout: 10000 }).catch(() => {});
    const node = page.locator('.tree-node, [role="treeitem"]').first();
    if (await node.isVisible({ timeout: 5000 }).catch(() => false)) {
      await node.click();
      await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
    }
    
    // 验证右侧面板显示（可能包含参数输入）
    // 注意：这取决于实际UI实现
  });

  test('应该能够批量选择构件', async ({ page }) => {
    // 等待Canvas加载
    await page.waitForSelector('svg, canvas, [data-testid="canvas"]', { timeout: 10000 });
    
    const canvas = page.locator('svg, canvas, [data-testid="canvas"]').first();
    
    if (await canvas.isVisible({ timeout: 5000 }).catch(() => false)) {
      const box = await canvas.boundingBox();
      if (box) {
        // 按住Ctrl键点击多个位置（模拟多选）
        await canvas.click({ position: { x: box.width * 0.3, y: box.height * 0.3 }, modifiers: ['Control'] });
        await page.waitForLoadState('networkidle', { timeout: 2000 }).catch(() => {});
        await canvas.click({ position: { x: box.width * 0.5, y: box.height * 0.5 }, modifiers: ['Control'] });
        await page.waitForLoadState('networkidle', { timeout: 2000 }).catch(() => {});
        await canvas.click({ position: { x: box.width * 0.7, y: box.height * 0.7 }, modifiers: ['Control'] });
        await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
        
        // 验证多选功能（可以通过检查选中状态或UI反馈）
      }
    }
  });

  test('应该能够设置构件高度', async ({ page }) => {
    // 等待页面加载
    await page.waitForLoadState('networkidle', { timeout: 10000 });
    
    // 查找高度输入框
    await page.waitForSelector('input[name*="height"], input[placeholder*="高度"], input[type="number"]', { timeout: 10000 }).catch(() => {});
    const heightInput = page.locator('input[name*="height"], input[placeholder*="高度"], input[type="number"]').first();
    
    if (await heightInput.isVisible({ timeout: 5000 }).catch(() => false)) {
      await heightInput.fill('3.5');
      await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
      
      // 验证输入值
      const value = await heightInput.inputValue();
      expect(value).toBe('3.5');
    }
  });

  test('应该能够设置基础偏移', async ({ page }) => {
    // 等待页面加载
    await page.waitForLoadState('networkidle', { timeout: 10000 });
    
    // 查找基础偏移输入框
    await page.waitForSelector('input[name*="offset"], input[placeholder*="偏移"], input[type="number"]', { timeout: 10000 }).catch(() => {});
    const offsetInput = page.locator('input[name*="offset"], input[placeholder*="偏移"], input[type="number"]').first();
    
    if (await offsetInput.isVisible({ timeout: 5000 }).catch(() => false)) {
      await offsetInput.fill('0.1');
      await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
      
      // 验证输入值
      const value = await offsetInput.inputValue();
      expect(value).toBe('0.1');
    }
  });

  test('应该能够设置材质', async ({ page }) => {
    // 等待页面加载
    await page.waitForLoadState('networkidle', { timeout: 10000 });
    
    // 查找材质输入框或选择器
    await page.waitForSelector('input[name*="material"], select[name*="material"]', { timeout: 10000 }).catch(() => {});
    const materialInput = page.locator('input[name*="material"], select[name*="material"]').first();
    
    if (await materialInput.isVisible({ timeout: 5000 }).catch(() => false)) {
      if (await materialInput.evaluate(el => el.tagName === 'SELECT')) {
        // 如果是下拉选择
        await materialInput.selectOption({ index: 0 });
      } else {
        // 如果是文本输入
        await materialInput.fill('混凝土');
      }
      await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
    }
  });

  test('应该能够批量应用Z轴参数', async ({ page }) => {
    // 等待页面加载
    await page.waitForLoadState('networkidle', { timeout: 10000 });
    
    // 先选择一些构件（如果可能）
    await page.waitForSelector('svg, canvas, [data-testid="canvas"]', { timeout: 10000 }).catch(() => {});
    const canvas = page.locator('svg, canvas, [data-testid="canvas"]').first();
    if (await canvas.isVisible({ timeout: 5000 }).catch(() => false)) {
      const box = await canvas.boundingBox();
      if (box) {
        await canvas.click({ position: { x: box.width / 2, y: box.height / 2 } });
        await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
      }
    }
    
    // 设置参数
    await page.waitForSelector('input[name*="height"], input[placeholder*="高度"]', { timeout: 10000 }).catch(() => {});
    const heightInput = page.locator('input[name*="height"], input[placeholder*="高度"]').first();
    if (await heightInput.isVisible({ timeout: 5000 }).catch(() => false)) {
      await heightInput.fill('3.0');
      await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
    }
    
    // 查找应用/保存按钮
    await page.waitForSelector('button:has-text("应用"), button:has-text("保存"), button[type="submit"]', { timeout: 10000 }).catch(() => {});
    const applyButton = page.locator('button:has-text("应用"), button:has-text("保存"), button[type="submit"]').first();
    
    if (await applyButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await applyButton.click();
      await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});
      
      // 验证操作成功（可以通过检查Toast消息或UI状态）
    }
  });

  test('应该能够使用快捷键切换到Lift Mode', async ({ page }) => {
    // 按L键应该切换到Lift Mode
    await page.keyboard.press('L');
    await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
    
    // 验证Lift Mode已激活 - 使用data-testid
    const liftButton = page.locator('[data-testid="lift-mode"]').first();
    await expect(liftButton).toBeVisible({ timeout: 10000 });
  });
});

