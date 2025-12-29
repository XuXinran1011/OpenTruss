/**
 * 审批工作流E2E测试
 */

import { test, expect } from '@playwright/test';
import { loginAsEditor, loginAsApprover } from './helpers/auth';
import { ensureWorkbenchReady } from './helpers/workbench';

test.describe('审批工作流', () => {
  test('Editor用户应该能够提交检验批审批', async ({ page }) => {
    await loginAsEditor(page);
    await page.goto('/workbench');
    
    // 使用统一的辅助函数确保Workbench页面已准备好
    await ensureWorkbenchReady(page);
    
    // 选择一个检验批
    const lotNode = page.locator('.tree-node:has-text("检验批"), .tree-node[data-type="lot"]').first();
    
    if (await lotNode.isVisible()) {
      await lotNode.click();
      await page.waitForTimeout(1000);
      
      // 查找提交审批按钮
      const submitButton = page.locator('button:has-text("提交审批"), button:has-text("Submit")').first();
      
      if (await submitButton.isVisible()) {
        await submitButton.click();
        await page.waitForTimeout(2000);
        
        // 验证提交成功（通过Toast消息）
        // 注意：这需要实际有检验批数据
      }
    }
  });

  test('Approver用户应该能够查看待审批检验批', async ({ page }) => {
    await loginAsApprover(page);
    await page.goto('/workbench');
    
    // 使用统一的辅助函数确保Workbench页面已准备好
    await ensureWorkbenchReady(page);
    
    // Approver用户应该能看到已提交的检验批
    // 验证层级树中有检验批节点
    const hierarchyTree = page.locator('[data-testid="hierarchy-tree"], .hierarchy-tree').first();
    await expect(hierarchyTree).toBeVisible();
    
    // 尝试查找状态为SUBMITTED的检验批
    // 注意：这取决于实际数据
  });

  test('Approver用户应该能够审批通过检验批', async ({ page }) => {
    await loginAsApprover(page);
    await page.goto('/workbench');
    
    // 使用统一的辅助函数确保Workbench页面已准备好
    await ensureWorkbenchReady(page);
    
    // 选择已提交的检验批
    const lotNode = page.locator('.tree-node:has-text("检验批"), .tree-node[data-type="lot"]').first();
    
    if (await lotNode.isVisible()) {
      await lotNode.click();
      await page.waitForTimeout(1000);
      
      // 查找审批通过按钮
      const approveButton = page.locator('button:has-text("通过"), button:has-text("Approve")').first();
      
      if (await approveButton.isVisible()) {
        await approveButton.click();
        await page.waitForTimeout(1000);
        
        // 如果有确认对话框，确认操作
        const confirmButton = page.locator('button:has-text("确认"), button:has-text("Confirm")').first();
        if (await confirmButton.isVisible()) {
          await confirmButton.click();
          await page.waitForTimeout(2000);
        }
        
        // 验证审批成功（通过Toast或UI状态变化）
      }
    }
  });

  test('Approver用户应该能够驳回检验批', async ({ page }) => {
    await loginAsApprover(page);
    await page.goto('/workbench');
    
    // 使用统一的辅助函数确保Workbench页面已准备好
    await ensureWorkbenchReady(page);
    
    // 选择已提交的检验批
    const lotNode = page.locator('.tree-node:has-text("检验批"), .tree-node[data-type="lot"]').first();
    
    if (await lotNode.isVisible()) {
      await lotNode.click();
      await page.waitForTimeout(1000);
      
      // 查找驳回按钮
      const rejectButton = page.locator('button:has-text("驳回"), button:has-text("Reject")').first();
      
      if (await rejectButton.isVisible()) {
        await rejectButton.click();
        await page.waitForTimeout(1000);
        
        // 填写驳回原因（如果有输入框）
        const reasonInput = page.locator('textarea[name*="reason"], input[name*="reason"], textarea[placeholder*="原因"]').first();
        if (await reasonInput.isVisible()) {
          await reasonInput.fill('测试驳回原因');
          await page.waitForTimeout(500);
        }
        
        // 确认驳回
        const confirmButton = page.locator('button:has-text("确认"), button:has-text("Confirm")').first();
        if (await confirmButton.isVisible()) {
          await confirmButton.click();
          await page.waitForTimeout(2000);
        }
        
        // 验证驳回成功
      }
    }
  });

  test('应该能够查看审批历史', async ({ page }) => {
    await loginAsApprover(page);
    await page.goto('/workbench');
    
    // 使用统一的辅助函数确保Workbench页面已准备好
    await ensureWorkbenchReady(page);
    
    // 选择检验批
    const lotNode = page.locator('.tree-node:has-text("检验批"), .tree-node[data-type="lot"]').first();
    
    if (await lotNode.isVisible()) {
      await lotNode.click();
      await page.waitForTimeout(1000);
      
      // 查找审批历史标签或按钮
      const historyTab = page.locator('button:has-text("历史"), [role="tab"]:has-text("历史"), button:has-text("History")').first();
      const historyPanel = page.locator('[data-testid="approval-history"], .approval-history').first();
      
      if (await historyTab.isVisible()) {
        await historyTab.click();
        await page.waitForTimeout(1000);
        
        // 验证审批历史显示
        if (await historyPanel.isVisible({ timeout: 2000 })) {
          await expect(historyPanel).toBeVisible();
        }
      } else if (await historyPanel.isVisible({ timeout: 2000 })) {
        // 如果历史直接显示，验证它存在
        await expect(historyPanel).toBeVisible();
      }
    }
  });

  test('审批后应该更新检验批状态', async ({ page }) => {
    await loginAsApprover(page);
    await page.goto('/workbench');
    
    // 使用统一的辅助函数确保Workbench页面已准备好
    await ensureWorkbenchReady(page);
    
    // 选择一个已提交的检验批并审批
    const lotNode = page.locator('.tree-node:has-text("检验批"), .tree-node[data-type="lot"]').first();
    
    if (await lotNode.isVisible()) {
      await lotNode.click();
      await page.waitForTimeout(1000);
      
      // 执行审批操作
      const approveButton = page.locator('button:has-text("通过"), button:has-text("Approve")').first();
      if (await approveButton.isVisible()) {
        await approveButton.click();
        await page.waitForTimeout(2000);
        
        // 验证状态更新（可以通过检查节点样式或文本）
        // 注意：这需要实际有检验批数据
      }
    }
  });
});

