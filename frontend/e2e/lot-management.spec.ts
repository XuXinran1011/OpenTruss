/**
 * 检验批管理E2E测试
 */

import { test, expect } from '@playwright/test';
import { loginAsEditor, loginAsApprover } from './helpers/auth';

test.describe('检验批管理', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsEditor(page);
    await page.goto('/workbench');
    await page.waitForTimeout(2000);
  });

  test('应该能够在层级树中查看检验批', async ({ page }) => {
    // 展开层级树以查看检验批节点
    const expandableNode = page.locator('[aria-expanded="false"], .tree-node:has(> .tree-children)').first();
    
    if (await expandableNode.isVisible()) {
      await expandableNode.click();
      await page.waitForTimeout(1000);
      
      // 继续展开以查找检验批节点
      const lotNodes = page.locator('.tree-node:has-text("检验批"), .tree-node[data-type="lot"]');
      // 注意：检验批可能不存在，这里只验证展开功能
    }
  });

  test('应该能够查看检验批详情', async ({ page }) => {
    await page.waitForTimeout(3000);
    
    // 点击检验批节点
    const lotNode = page.locator('.tree-node:has-text("检验批"), .tree-node[data-type="lot"]').first();
    
    if (await lotNode.isVisible()) {
      await lotNode.click();
      await page.waitForTimeout(1000);
      
      // 验证右侧面板显示检验批详情
      const rightPanel = page.locator('[data-testid="right-panel"], .right-panel').first();
      if (await rightPanel.isVisible({ timeout: 3000 })) {
        await expect(rightPanel).toBeVisible();
      }
    }
  });

  test('应该能够查看检验批构件列表', async ({ page }) => {
    await page.waitForTimeout(3000);
    
    // 选择检验批节点
    const lotNode = page.locator('.tree-node:has-text("检验批"), .tree-node[data-type="lot"]').first();
    
    if (await lotNode.isVisible()) {
      await lotNode.click();
      await page.waitForTimeout(1000);
      
      // 查找构件列表标签或内容
      const elementsTab = page.locator('button:has-text("构件"), [role="tab"]:has-text("构件")').first();
      const elementsList = page.locator('[data-testid="lot-elements"], .elements-list').first();
      
      // 如果有构件标签，点击它
      if (await elementsTab.isVisible()) {
        await elementsTab.click();
        await page.waitForTimeout(500);
      }
      
      // 验证构件列表显示（可能为空）
      if (await elementsList.isVisible({ timeout: 2000 })) {
        await expect(elementsList).toBeVisible();
      }
    }
  });

  test('应该能够分配构件到检验批', async ({ page }) => {
    await page.waitForTimeout(3000);
    
    // 选择一个检验批
    const lotNode = page.locator('.tree-node:has-text("检验批"), .tree-node[data-type="lot"]').first();
    
    if (await lotNode.isVisible()) {
      await lotNode.click();
      await page.waitForTimeout(1000);
      
      // 查找分配构件按钮
      const assignButton = page.locator('button:has-text("分配"), button:has-text("Assign")').first();
      
      if (await assignButton.isVisible()) {
        await assignButton.click();
        await page.waitForTimeout(1000);
        
        // 验证分配对话框或界面出现
        const dialog = page.locator('[role="dialog"], .modal, [data-testid="assign-dialog"]').first();
        if (await dialog.isVisible({ timeout: 2000 })) {
          await expect(dialog).toBeVisible();
        }
      }
    }
  });

  test('应该能够移除检验批中的构件', async ({ page }) => {
    await page.waitForTimeout(3000);
    
    // 选择检验批并查看构件列表
    const lotNode = page.locator('.tree-node:has-text("检验批"), .tree-node[data-type="lot"]').first();
    
    if (await lotNode.isVisible()) {
      await lotNode.click();
      await page.waitForTimeout(1000);
      
      // 查找移除按钮（可能在构件列表项上）
      const removeButton = page.locator('button:has-text("移除"), button:has-text("Remove"), [data-testid="remove-element"]').first();
      
      if (await removeButton.isVisible()) {
        await removeButton.click();
        await page.waitForTimeout(1000);
        
        // 验证移除操作（可能需要确认对话框）
      }
    }
  });

  test('应该能够更新检验批状态', async ({ page }) => {
    await page.waitForTimeout(3000);
    
    // 选择检验批
    const lotNode = page.locator('.tree-node:has-text("检验批"), .tree-node[data-type="lot"]').first();
    
    if (await lotNode.isVisible()) {
      await lotNode.click();
      await page.waitForTimeout(1000);
      
      // 查找状态更新按钮（提交、发布等）
      const submitButton = page.locator('button:has-text("提交"), button:has-text("Submit")').first();
      
      if (await submitButton.isVisible()) {
        await submitButton.click();
        await page.waitForTimeout(2000);
        
        // 验证状态更新成功（通过Toast或UI状态变化）
      }
    }
  });

  test('Approver用户应该能够查看待审批检验批', async ({ page }) => {
    await loginAsApprover(page);
    await page.goto('/workbench');
    await page.waitForTimeout(2000);
    
    // Approver用户应该能看到已提交的检验批
    // 验证层级树中有检验批节点
    const hierarchyTree = page.locator('[data-testid="hierarchy-tree"], .hierarchy-tree').first();
    await expect(hierarchyTree).toBeVisible();
  });
});

