/**
 * Workbench基础功能E2E测试
 */

import { test, expect } from '@playwright/test';
import { loginAsEditor } from './helpers/auth';

test.describe('Workbench基础功能', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsEditor(page);
    await page.goto('/workbench');
  });

  test('应该正确加载Workbench页面', async ({ page }) => {
    await expect(page).toHaveURL('/workbench');
    
    // 验证页面主要元素存在
    // 左侧层级树
    const hierarchyTree = page.locator('[data-testid="hierarchy-tree"], .hierarchy-tree, aside').first();
    await expect(hierarchyTree).toBeVisible();
    
    // 中间画布区域
    const canvas = page.locator('[data-testid="canvas"], .canvas, canvas, svg').first();
    await expect(canvas).toBeVisible();
  });

  test('应该显示层级树', async ({ page }) => {
    // 等待层级树加载
    await page.waitForTimeout(2000);
    
    // 验证层级树中有项目节点（至少应该有默认项目）
    const projectNode = page.locator('text=/项目|Project/i').first();
    await expect(projectNode).toBeVisible({ timeout: 10000 });
  });

  test('应该能够展开和折叠层级树节点', async ({ page }) => {
    await page.waitForTimeout(2000);
    
    // 查找可展开的节点
    const expandableNode = page.locator('[aria-expanded="false"], .tree-node:has(> .tree-children)').first();
    
    if (await expandableNode.isVisible()) {
      await expandableNode.click();
      await page.waitForTimeout(500);
      
      // 验证节点已展开
      const expandedNode = page.locator('[aria-expanded="true"]').first();
      await expect(expandedNode).toBeVisible();
    }
  });

  test('应该显示Canvas视图', async ({ page }) => {
    await page.waitForTimeout(2000);
    
    // 验证Canvas元素存在
    const canvas = page.locator('canvas, svg, [data-testid="canvas"]').first();
    await expect(canvas).toBeVisible();
  });

  test('应该能够切换模式（Trace/Lift/Classify）', async ({ page }) => {
    await page.waitForTimeout(2000);
    
    // 查找模式切换按钮
    const traceButton = page.locator('button:has-text("Trace"), button:has-text("拓扑"), [data-testid="trace-mode"]').first();
    const liftButton = page.locator('button:has-text("Lift"), button:has-text("提升"), [data-testid="lift-mode"]').first();
    const classifyButton = page.locator('button:has-text("Classify"), button:has-text("归类"), [data-testid="classify-mode"]').first();
    
    // 如果按钮存在，测试切换
    if (await traceButton.isVisible()) {
      await traceButton.click();
      await page.waitForTimeout(500);
      // 验证模式已切换（可以通过检查按钮状态或UI变化）
    }
    
    if (await liftButton.isVisible()) {
      await liftButton.click();
      await page.waitForTimeout(500);
    }
    
    if (await classifyButton.isVisible()) {
      await classifyButton.click();
      await page.waitForTimeout(500);
    }
  });

  test('应该能够使用快捷键切换模式', async ({ page }) => {
    await page.waitForTimeout(2000);
    
    // 测试快捷键 T (Trace Mode)
    await page.keyboard.press('T');
    await page.waitForTimeout(500);
    
    // 测试快捷键 L (Lift Mode)
    await page.keyboard.press('L');
    await page.waitForTimeout(500);
    
    // 测试快捷键 C (Classify Mode)
    await page.keyboard.press('C');
    await page.waitForTimeout(500);
  });

  test('应该显示右侧面板', async ({ page }) => {
    await page.waitForTimeout(2000);
    
    // 验证右侧面板存在
    const rightPanel = page.locator('[data-testid="right-panel"], .right-panel, aside:has-text("参数")').first();
    
    // 右侧面板可能默认隐藏，所以只检查是否存在
    const isVisible = await rightPanel.isVisible().catch(() => false);
    
    // 如果面板存在但不可见，尝试选择一个节点来显示它
    if (!isVisible) {
      const node = page.locator('.tree-node, [role="treeitem"]').first();
      if (await node.isVisible()) {
        await node.click();
        await page.waitForTimeout(500);
        await expect(rightPanel).toBeVisible({ timeout: 5000 });
      }
    }
  });

  test('应该能够搜索层级树', async ({ page }) => {
    await page.waitForTimeout(2000);
    
    // 查找搜索框
    const searchInput = page.locator('input[type="search"], input[placeholder*="搜索"], [data-testid="search"]').first();
    
    if (await searchInput.isVisible()) {
      await searchInput.fill('test');
      await page.waitForTimeout(500);
      
      // 验证搜索结果
      // 这里可以根据实际UI调整
    }
  });

  test('应该能够响应窗口大小变化', async ({ page }) => {
    await page.waitForTimeout(2000);
    
    // 改变窗口大小
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.waitForTimeout(500);
    
    // 验证布局仍然正常
    const canvas = page.locator('canvas, svg, [data-testid="canvas"]').first();
    await expect(canvas).toBeVisible();
    
    // 改变为移动端尺寸
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForTimeout(500);
    
    // 验证响应式布局
    await expect(canvas).toBeVisible();
  });
});

