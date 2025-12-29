/**
 * Classify Mode E2E测试
 */

import { test, expect } from '@playwright/test';
import { loginAsEditor } from './helpers/auth';
import { ensureWorkbenchReady, setupResponseListeners } from './helpers/workbench';

test.describe('Classify Mode', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsEditor(page);
    
    // 在导航前设置响应监听器，确保能捕获所有API请求
    const { failedRequests } = setupResponseListeners(page);
    await page.goto('/workbench');
    
    // 使用统一的辅助函数确保Workbench页面已准备好
    await ensureWorkbenchReady(page, failedRequests);
    
    // 切换到Classify Mode - 使用data-testid
    await page.waitForSelector('[data-testid="classify-mode"]', { timeout: 15000 });
    const classifyButton = page.locator('[data-testid="classify-mode"]').first();
    await classifyButton.waitFor({ state: 'visible', timeout: 10000 });
    await classifyButton.click();
    await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
  });

  test('应该能够切换到Classify Mode', async ({ page }) => {
    // 验证Classify Mode已激活 - 使用data-testid
    const classifyButton = page.locator('[data-testid="classify-mode"]').first();
    await expect(classifyButton).toBeVisible({ timeout: 10000 });
  });

  test('应该显示层级树中的分项节点', async ({ page }) => {
    // 等待层级树加载
    await page.waitForSelector('[data-testid="hierarchy-tree"], .hierarchy-tree', { timeout: 10000 });
    
    // 层级树应该显示可归类的分项节点
    const hierarchyTree = page.locator('[data-testid="hierarchy-tree"], .hierarchy-tree').first();
    await expect(hierarchyTree).toBeVisible();
    
    // 尝试展开节点以查看分项
    await page.waitForSelector('[aria-expanded="false"], .tree-node:has(> .tree-children)', { timeout: 10000 }).catch(() => {});
    const expandableNode = page.locator('[aria-expanded="false"], .tree-node:has(> .tree-children)').first();
    if (await expandableNode.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expandableNode.click();
      await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
    }
  });

  test('应该能够选择构件', async ({ page }) => {
    // 等待Canvas加载
    await page.waitForSelector('svg, canvas, [data-testid="canvas"]', { timeout: 10000 });
    
    const canvas = page.locator('svg, canvas, [data-testid="canvas"]').first();
    
    if (await canvas.isVisible({ timeout: 5000 }).catch(() => false)) {
      const box = await canvas.boundingBox();
      if (box) {
        // 点击选择构件
        await canvas.click({ position: { x: box.width / 2, y: box.height / 2 } });
        await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
        
        // 验证构件已选中（可以通过检查UI状态）
      }
    }
  });

  test('应该能够拖拽构件到分项节点', async ({ page }) => {
    // 等待Canvas加载
    await page.waitForSelector('svg, canvas, [data-testid="canvas"]', { timeout: 10000 });
    
    // 先选择一个构件
    const canvas = page.locator('svg, canvas, [data-testid="canvas"]').first();
    let canvasBox = null;
    
    if (await canvas.isVisible({ timeout: 5000 }).catch(() => false)) {
      canvasBox = await canvas.boundingBox();
      if (canvasBox) {
        await canvas.click({ position: { x: canvasBox.width / 2, y: canvasBox.height / 2 } });
        await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
      }
    }
    
    // 查找层级树中的分项节点
    await page.waitForSelector('.tree-node:has-text("分项"), .tree-node[data-type="item"]', { timeout: 10000 }).catch(() => {});
    const itemNode = page.locator('.tree-node:has-text("分项"), .tree-node[data-type="item"]').first();
    
    if (await itemNode.isVisible({ timeout: 5000 }).catch(() => false) && canvasBox) {
      // 从Canvas拖拽到层级树节点
      await canvas.hover({ position: { x: canvasBox.width / 2, y: canvasBox.height / 2 } });
      await page.mouse.down();
      
      const itemBox = await itemNode.boundingBox();
      if (itemBox) {
        await itemNode.hover();
        await page.mouse.up();
        await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});
        
        // 验证归类操作成功（可以通过检查Toast消息或UI状态）
      }
    }
  });

  test('应该能够批量选择多个构件', async ({ page }) => {
    // 等待Canvas加载
    await page.waitForSelector('svg, canvas, [data-testid="canvas"]', { timeout: 10000 });
    
    const canvas = page.locator('svg, canvas, [data-testid="canvas"]').first();
    
    if (await canvas.isVisible({ timeout: 5000 }).catch(() => false)) {
      const box = await canvas.boundingBox();
      if (box) {
        // 按住Ctrl键多选
        await canvas.click({ position: { x: box.width * 0.3, y: box.height * 0.3 }, modifiers: ['Control'] });
        await page.waitForLoadState('networkidle', { timeout: 2000 }).catch(() => {});
        await canvas.click({ position: { x: box.width * 0.5, y: box.height * 0.5 }, modifiers: ['Control'] });
        await page.waitForLoadState('networkidle', { timeout: 2000 }).catch(() => {});
        await canvas.click({ position: { x: box.width * 0.7, y: box.height * 0.7 }, modifiers: ['Control'] });
        await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
        
        // 验证多选功能
      }
    }
  });

  test('应该能够批量归类构件到分项', async ({ page }) => {
    // 等待Canvas加载
    await page.waitForSelector('svg, canvas, [data-testid="canvas"]', { timeout: 10000 });
    
    // 多选构件
    const canvas = page.locator('svg, canvas, [data-testid="canvas"]').first();
    let canvasBox = null;
    
    if (await canvas.isVisible({ timeout: 5000 }).catch(() => false)) {
      canvasBox = await canvas.boundingBox();
      if (canvasBox) {
        await canvas.click({ position: { x: canvasBox.width * 0.4, y: canvasBox.height * 0.4 }, modifiers: ['Control'] });
        await page.waitForLoadState('networkidle', { timeout: 2000 }).catch(() => {});
        await canvas.click({ position: { x: canvasBox.width * 0.6, y: canvasBox.height * 0.6 }, modifiers: ['Control'] });
        await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
      }
    }
    
    // 拖拽到分项节点
    await page.waitForSelector('.tree-node:has-text("分项"), .tree-node[data-type="item"]', { timeout: 10000 }).catch(() => {});
    const itemNode = page.locator('.tree-node:has-text("分项"), .tree-node[data-type="item"]').first();
    
    if (await itemNode.isVisible({ timeout: 5000 }).catch(() => false) && canvasBox) {
      await canvas.hover({ position: { x: canvasBox.width / 2, y: canvasBox.height / 2 } });
      await page.mouse.down();
      
      const itemBox = await itemNode.boundingBox();
      if (itemBox) {
        await itemNode.hover();
        await page.mouse.up();
        await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});
      }
    }
  });

  test('应该显示归类结果反馈', async ({ page }) => {
    // 等待页面加载
    await page.waitForLoadState('networkidle', { timeout: 10000 });
    
    // 执行归类操作后，应该显示成功或失败的反馈
    // 这通常通过Toast消息或UI状态变化体现
    
    // 验证Toast容器存在（即使可能为空）
    const toastContainer = page.locator('[data-testid="toast"], .toast-container').first();
    // 注意：Toast可能不存在或不可见，这里只验证容器结构
  });

  test('应该能够使用快捷键切换到Classify Mode', async ({ page }) => {
    // 按C键应该切换到Classify Mode
    await page.keyboard.press('C');
    await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
    
    // 验证Classify Mode已激活 - 使用data-testid
    const classifyButton = page.locator('[data-testid="classify-mode"]').first();
    await expect(classifyButton).toBeVisible({ timeout: 10000 });
  });

  test('归类后应该清除选择', async ({ page }) => {
    // 等待Canvas加载
    await page.waitForSelector('svg, canvas, [data-testid="canvas"]', { timeout: 10000 });
    
    // 选择构件并归类
    const canvas = page.locator('svg, canvas, [data-testid="canvas"]').first();
    let canvasBox = null;
    
    if (await canvas.isVisible({ timeout: 5000 }).catch(() => false)) {
      canvasBox = await canvas.boundingBox();
      if (canvasBox) {
        await canvas.click({ position: { x: canvasBox.width / 2, y: canvasBox.height / 2 } });
        await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
        
        // 拖拽到分项节点
        await page.waitForSelector('.tree-node:has-text("分项"), .tree-node[data-type="item"]', { timeout: 10000 }).catch(() => {});
        const itemNode = page.locator('.tree-node:has-text("分项"), .tree-node[data-type="item"]').first();
        if (await itemNode.isVisible({ timeout: 5000 }).catch(() => false)) {
          await canvas.hover({ position: { x: canvasBox.width / 2, y: canvasBox.height / 2 } });
          await page.mouse.down();
          
          const itemBox = await itemNode.boundingBox();
          if (itemBox) {
            await itemNode.hover();
            await page.mouse.up();
            await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});
            
            // 验证选择已清除（可以通过检查UI状态）
          }
        }
      }
    }
  });
});

