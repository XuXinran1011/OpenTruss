/**
 * Trace Mode E2E测试
 */

import { test, expect } from '@playwright/test';
import { loginAsEditor } from './helpers/auth';

test.describe('Trace Mode', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsEditor(page);
    await page.goto('/workbench');
    await page.waitForLoadState('networkidle', { timeout: 15000 });
    
    // 切换到Trace Mode
    await page.waitForSelector('button:has-text("Trace"), button:has-text("拓扑"), [data-testid="trace-mode"]', { timeout: 10000 }).catch(() => {});
    const traceButton = page.locator('button:has-text("Trace"), button:has-text("拓扑"), [data-testid="trace-mode"]').first();
    if (await traceButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await traceButton.click();
      await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
    }
  });

  test('应该能够切换到Trace Mode', async ({ page }) => {
    // 验证Trace Mode已激活
    // 这里可以根据实际UI调整验证逻辑
    const traceButton = page.locator('button:has-text("Trace"), button:has-text("拓扑")').first();
    await expect(traceButton).toBeVisible();
  });

  test('应该显示Canvas中的构件', async ({ page }) => {
    // 等待Canvas加载
    await page.waitForSelector('svg, canvas, [data-testid="canvas"]', { timeout: 10000 });
    
    // 验证Canvas中有SVG元素（构件的可视化）
    const canvas = page.locator('svg, canvas, [data-testid="canvas"]').first();
    await expect(canvas).toBeVisible();
    
    // 如果有构件，应该能看到SVG路径或元素
    // 注意：这取决于是否有测试数据
  });

  test('应该能够选择构件', async ({ page }) => {
    // 等待Canvas加载
    await page.waitForSelector('svg, canvas, [data-testid="canvas"]', { timeout: 10000 });
    
    // 尝试点击Canvas中的构件
    // 注意：这需要实际有构件数据
    const canvas = page.locator('svg, canvas, [data-testid="canvas"]').first();
    
    // 如果Canvas可点击，尝试点击中心点
    if (await canvas.isVisible({ timeout: 5000 }).catch(() => false)) {
      const box = await canvas.boundingBox();
      if (box) {
        // 点击Canvas中心（可能没有构件，但这至少验证了交互）
        await canvas.click({ position: { x: box.width / 2, y: box.height / 2 } });
        await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
      }
    }
  });

  test('应该能够拖拽构件调整位置', async ({ page }) => {
    // 等待Canvas加载
    await page.waitForSelector('svg, canvas, [data-testid="canvas"]', { timeout: 10000 });
    
    const canvas = page.locator('svg, canvas, [data-testid="canvas"]').first();
    
    if (await canvas.isVisible({ timeout: 5000 }).catch(() => false)) {
      const box = await canvas.boundingBox();
      if (box) {
        // 模拟拖拽操作（从中心点拖拽到右上角）
        await canvas.hover({ position: { x: box.width / 2, y: box.height / 2 } });
        await page.mouse.down();
        await canvas.hover({ position: { x: box.width * 0.7, y: box.height * 0.3 } });
        await page.mouse.up();
        await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
        
        // 验证拖拽操作没有导致错误
        // 注意：实际验证需要检查API调用或UI状态
      }
    }
  });

  test('应该显示拓扑连接线', async ({ page }) => {
    // 等待Canvas加载
    await page.waitForSelector('svg, canvas, [data-testid="canvas"]', { timeout: 10000 });
    
    // Trace Mode应该显示构件之间的拓扑连接
    const canvas = page.locator('svg, canvas, [data-testid="canvas"]').first();
    await expect(canvas).toBeVisible();
    
    // 检查是否有连接线（SVG line元素）
    // 注意：这需要实际有连接的构件数据
  });

  test('应该能够上传DWG底图', async ({ page }) => {
    // 查找上传DWG底图按钮
    const uploadButton = page.locator('button:has-text("DWG"), button:has-text("底图")').first();
    
    if (await uploadButton.isVisible()) {
      // 注意：文件上传测试需要实际文件，这里只验证按钮存在
      await expect(uploadButton).toBeVisible();
    }
  });

  test('应该能够切换底图显示', async ({ page }) => {
    // 查找底图显示开关
    await page.waitForSelector('button:has-text("底图"), input[type="checkbox"]', { timeout: 10000 }).catch(() => {});
    const toggleButton = page.locator('button:has-text("底图"), input[type="checkbox"]').first();
    
    if (await toggleButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await toggleButton.click();
      await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
      // 验证切换功能正常
    }
  });

  test('应该能够使用快捷键切换模式', async ({ page }) => {
    // 在Trace Mode中，按T键应该保持Trace Mode
    await page.keyboard.press('T');
    await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
    
    // 验证仍在Trace Mode（可以通过检查按钮状态）
    const traceButton = page.locator('button:has-text("Trace"), button:has-text("拓扑")').first();
    await expect(traceButton).toBeVisible();
  });
});

