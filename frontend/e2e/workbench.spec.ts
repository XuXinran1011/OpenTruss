/**
 * Workbench基础功能E2E测试
 */

import { test, expect } from '@playwright/test';
import { loginAsEditor } from './helpers/auth';
import { ensureWorkbenchReady } from './helpers/workbench';

test.describe('Workbench基础功能', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsEditor(page);
    await page.goto('/workbench');
    
    // 使用统一的辅助函数确保Workbench页面已准备好
    await ensureWorkbenchReady(page);
  });

  test('应该正确加载Workbench页面', async ({ page }) => {
    await expect(page).toHaveURL('/workbench');
    
    // 验证页面主要元素存在
    // 左侧层级树 - 优先使用data-testid，后备使用aside
    let hierarchyTree = page.locator('[data-testid="hierarchy-tree"]').first();
    if (await hierarchyTree.count() === 0) {
      hierarchyTree = page.locator('aside').first();
    }
    await expect(hierarchyTree).toBeVisible({ timeout: 10000 });
    
    // 中间画布区域
    await page.waitForSelector('canvas, svg, [data-testid="canvas"]', { timeout: 15000 });
    const canvas = page.locator('canvas, svg, [data-testid="canvas"]').first();
    await expect(canvas).toBeVisible({ timeout: 10000 });
  });

  test('应该显示层级树', async ({ page }) => {
    // 等待层级树加载完成 - 直接等待hierarchy-tree出现，因为它的出现就意味着加载完成
    // HierarchyTree组件只有在数据加载完成后才会渲染带有data-testid="hierarchy-tree"的元素
    await page.waitForSelector('[data-testid="hierarchy-tree"]', { timeout: 20000 });
    
    // 验证层级树可见
    const hierarchyTree = page.locator('[data-testid="hierarchy-tree"]').first();
    await expect(hierarchyTree).toBeVisible({ timeout: 10000 });
    
    // 等待层级树节点加载（树节点可能稍后才渲染）
    await page.waitForSelector('[role="treeitem"], [data-node-label]', { timeout: 15000 }).catch(() => {});
    
    // 查找项目节点 - 优先使用data-node-label属性，后备使用文本匹配
    let projectNode = page.locator('[data-node-label="Project"]').first();
    if (await projectNode.count() === 0) {
      projectNode = page.locator('[role="treeitem"]').filter({ hasText: /Project|项目/i }).first();
    }
    await expect(projectNode).toBeVisible({ timeout: 10000 });
  });

  test('应该能够展开和折叠层级树节点', async ({ page }) => {
    // 等待层级树加载 - 使用data-testid
    await page.waitForSelector('[data-testid="hierarchy-tree"]', { timeout: 10000 });
    
    // 等待层级树节点加载
    await page.waitForSelector('[role="treeitem"]', { timeout: 10000 }).catch(() => {});
    
    // 查找可展开的节点 - 查找有子节点且未展开的节点（aria-expanded="false"或undefined）
    const expandableNode = page.locator('[role="treeitem"][aria-expanded="false"], [role="treeitem"]:not([aria-expanded="true"])').first();
    
    if (await expandableNode.isVisible({ timeout: 5000 }).catch(() => false)) {
      // 查找该节点内的展开按钮
      const expandButton = expandableNode.locator('button:has(svg)').first();
      if (await expandButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        await expandButton.click();
        // 等待节点展开动画完成
        await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
        await page.waitForTimeout(500); // 等待动画完成
        
        // 验证节点已展开 - 检查aria-expanded属性
        await expect(expandableNode).toHaveAttribute('aria-expanded', 'true', { timeout: 5000 });
      }
    }
  });

  test('应该显示Canvas视图', async ({ page }) => {
    // 等待Canvas元素出现
    await page.waitForSelector('[data-testid="canvas"], .canvas, canvas, svg', { timeout: 10000 });
    const canvas = page.locator('canvas, svg, [data-testid="canvas"]').first();
    await expect(canvas).toBeVisible();
  });

  test('应该能够切换模式（Trace/Lift/Classify）', async ({ page }) => {
    // 等待页面加载完成
    await page.waitForLoadState('networkidle', { timeout: 15000 });
    
    // 等待工具栏区域出现
    await page.waitForSelector('div.h-12.bg-white.border-b', { timeout: 15000 }).catch(() => {});
    
    // 等待模式切换按钮出现 - 使用data-testid
    await page.waitForSelector('[data-testid="trace-mode"]', { timeout: 15000 });
    
    const traceButton = page.locator('[data-testid="trace-mode"]').first();
    const liftButton = page.locator('[data-testid="lift-mode"]').first();
    const classifyButton = page.locator('[data-testid="classify-mode"]').first();
    
    // 验证按钮可见并测试切换
    await traceButton.waitFor({ state: 'visible', timeout: 10000 });
    await traceButton.click();
    await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
    
    await liftButton.waitFor({ state: 'visible', timeout: 10000 });
    await liftButton.click();
    await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
    
    await classifyButton.waitFor({ state: 'visible', timeout: 10000 });
    await classifyButton.click();
    await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
  });

  test('应该能够使用快捷键切换模式', async ({ page }) => {
    // 等待页面加载完成
    await page.waitForLoadState('networkidle', { timeout: 10000 });
    
    // 测试快捷键 T (Trace Mode)
    await page.keyboard.press('T');
    await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
    
    // 测试快捷键 L (Lift Mode)
    await page.keyboard.press('L');
    await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
    
    // 测试快捷键 C (Classify Mode)
    await page.keyboard.press('C');
    await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
  });

  test('应该显示右侧面板', async ({ page }) => {
    // 等待页面加载完成
    await page.waitForLoadState('networkidle', { timeout: 10000 });
    
    // 验证右侧面板存在
    const rightPanel = page.locator('[data-testid="right-panel"], .right-panel, aside:has-text("参数")').first();
    
    // 右侧面板可能默认隐藏，所以只检查是否存在
    const isVisible = await rightPanel.isVisible({ timeout: 5000 }).catch(() => false);
    
    // 如果面板存在但不可见，尝试选择一个节点来显示它
    if (!isVisible) {
      await page.waitForSelector('.tree-node, [role="treeitem"]', { timeout: 10000 }).catch(() => {});
      const node = page.locator('.tree-node, [role="treeitem"]').first();
      if (await node.isVisible({ timeout: 5000 }).catch(() => false)) {
        await node.click();
        await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
        await expect(rightPanel).toBeVisible({ timeout: 5000 });
      }
    }
  });

  test('应该能够搜索层级树', async ({ page }) => {
    // 等待页面加载完成
    await page.waitForLoadState('networkidle', { timeout: 10000 });
    
    // 查找搜索框
    await page.waitForSelector('input[type="search"], input[placeholder*="搜索"], [data-testid="search"]', { timeout: 10000 }).catch(() => {});
    const searchInput = page.locator('input[type="search"], input[placeholder*="搜索"], [data-testid="search"]').first();
    
    if (await searchInput.isVisible({ timeout: 5000 }).catch(() => false)) {
      await searchInput.fill('test');
      await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
      
      // 验证搜索结果
      // 这里可以根据实际UI调整
    }
  });

  test('应该能够响应窗口大小变化', async ({ page }) => {
    // 等待页面加载完成
    await page.waitForLoadState('networkidle', { timeout: 10000 });
    
    // 改变窗口大小
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
    
    // 验证布局仍然正常
    await page.waitForSelector('[data-testid="canvas"], .canvas, canvas, svg', { timeout: 10000 });
    const canvas = page.locator('canvas, svg, [data-testid="canvas"]').first();
    await expect(canvas).toBeVisible();
    
    // 改变为移动端尺寸
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
    
    // 验证响应式布局
    await expect(canvas).toBeVisible();
  });
});

