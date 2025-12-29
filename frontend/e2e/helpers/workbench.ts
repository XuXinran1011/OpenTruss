/**
 * E2E测试 - Workbench页面辅助函数
 */

import { Page, expect } from '@playwright/test';

/**
 * 选择第一个项目（如果需要）
 * 如果页面显示"选择项目"界面，自动选择第一个项目
 */
export async function selectProjectIfNeeded(page: Page): Promise<boolean> {
  // 检查是否显示项目选择界面
  const projectSelectionTitle = page.locator('text=/选择项目/i').first();
  const isProjectSelectionVisible = await projectSelectionTitle.isVisible({ timeout: 5000 }).catch(() => false);
  
  if (!isProjectSelectionVisible) {
    return false; // 不需要选择项目
  }
  
  console.log('检测到项目选择界面，准备选择项目...');
  
  // 等待项目列表按钮加载
  await page.waitForSelector('button', { timeout: 10000 }).catch(() => {});
  
  // 选择第一个项目按钮（排除可能的"登录"等其他按钮）
  const projectButtons = page.locator('button').filter({ 
    hasText: /.+/,
    hasNotText: /登录|登录|Login/i 
  });
  const firstProjectButton = projectButtons.first();
  
  if (await firstProjectButton.count() > 0 && await firstProjectButton.isVisible({ timeout: 5000 }).catch(() => false)) {
    console.log('点击第一个项目按钮...');
    await firstProjectButton.click();
    
    // 等待项目选择后的页面更新
    await page.waitForLoadState('networkidle', { timeout: 15000 });
    console.log('✓ 项目已选择');
    return true;
  } else {
    console.warn('警告：未找到可点击的项目按钮');
    return false;
  }
}

/**
 * 等待WorkbenchLayout完全渲染
 * 确保左侧边栏（aside）和工具栏都已渲染
 */
export async function waitForWorkbenchLayout(page: Page): Promise<void> {
  // 等待WorkbenchLayout渲染（通过检查aside元素或工具栏）
  await page.waitForSelector('aside, div.h-12.bg-white.border-b', { timeout: 15000 });
  
  // 确保左侧边栏已渲染
  const asideElement = page.locator('aside').first();
  const isAsideVisible = await asideElement.isVisible({ timeout: 10000 }).catch(() => false);
  
  if (!isAsideVisible) {
    const pageContent = await page.content().catch(() => '无法获取页面内容');
    const hasProjectSelection = pageContent.includes('选择项目');
    const hasLoading = pageContent.includes('加载项目列表');
    
    throw new Error(
      `左侧边栏未渲染。` +
      (hasProjectSelection ? ' 页面显示"选择项目"界面。' : '') +
      (hasLoading ? ' 页面可能仍在加载。' : '')
    );
  }
  
  console.log('✓ WorkbenchLayout已渲染，左侧边栏已出现');
}

/**
 * 确保Workbench页面已准备好
 * 包括：检查项目数据、选择项目（如果需要）、等待WorkbenchLayout渲染、等待层级树容器出现
 */
export async function ensureWorkbenchReady(page: Page): Promise<void> {
  // 收集失败的API请求
  const failedRequests: string[] = [];
  page.on('response', (response) => {
    if (!response.ok() && response.url().includes('/api/v1/hierarchy/')) {
      failedRequests.push(`${response.url()}: ${response.status()} ${response.statusText()}`);
    }
  });
  
  // 等待项目列表API请求完成并检查响应
  const projectsResponse = await page.waitForResponse(
    (response) => response.url().includes('/api/v1/hierarchy/projects') && 
                 (response.url().endsWith('/projects') || response.url().includes('/projects?')),
    { timeout: 15000 }
  ).catch(() => null);
  
  // 检查项目列表响应
  let projectsCount = 0;
  if (projectsResponse) {
    const projectsData = await projectsResponse.json().catch(() => null);
    projectsCount = projectsData?.data?.items?.length || 0;
    
    if (projectsCount === 0) {
      const errorMessage = '错误：项目列表为空，层级树无法加载。请确保测试环境已准备测试数据（运行 python -m scripts.create_demo_data）';
      console.error(errorMessage);
      // 在CI环境中，这应该是一个失败条件
      if (process.env.CI) {
        throw new Error(errorMessage);
      } else {
        console.warn(errorMessage);
      }
    } else {
      console.log(`✓ 项目列表API响应成功，找到 ${projectsCount} 个项目`);
    }
  } else {
    console.warn('警告：无法获取项目列表API响应');
  }
  
  // 等待页面加载完成
  await page.waitForLoadState('networkidle', { timeout: 15000 });
  
  // 选择项目（如果需要）
  await selectProjectIfNeeded(page);
  
  // 等待WorkbenchLayout渲染
  await waitForWorkbenchLayout(page);
  
  // 等待层级树容器出现
  try {
    await page.waitForSelector('[data-testid="hierarchy-tree"]', { timeout: 20000 });
    console.log('✓ 层级树容器已出现');
    
    // 检查层级树是否处于错误状态
    const hierarchyTree = page.locator('[data-testid="hierarchy-tree"]').first();
    const treeContent = await hierarchyTree.textContent({ timeout: 5000 }).catch(() => '');
    
    if (treeContent?.includes('加载失败') || treeContent?.includes('暂无数据')) {
      // 记录诊断信息
      const errorText = treeContent;
      const apiErrors = failedRequests.length > 0 ? failedRequests.join(', ') : '无';
      console.error(`层级树状态异常: ${errorText}, API错误: ${apiErrors}`);
      
      // 不抛出错误，让测试继续执行，测试用例本身会验证层级树是否可见
    }
  } catch (error) {
    // 如果层级树容器都没有出现，提供详细诊断
    const pageTitle = await page.title().catch(() => '未知');
    const domDump = await page.content().catch(() => '无法获取DOM内容');
    const asideContent = await page.locator('aside').first().textContent().catch(() => null);
    const hasProjectSelection = domDump.includes('选择项目');
    const hasLoading = domDump.includes('加载项目列表');
    
    // 检查项目选择界面
    const projectSelectionVisible = await page.locator('text=/选择项目/i').first().isVisible({ timeout: 2000 }).catch(() => false);
    
    console.error('层级树容器未出现的诊断信息:');
    console.error('页面标题:', pageTitle);
    console.error('项目数量:', projectsCount);
    console.error('是否显示项目选择界面:', projectSelectionVisible);
    console.error('页面内容包含"选择项目":', hasProjectSelection);
    console.error('页面内容包含"加载项目列表":', hasLoading);
    console.error('左侧边栏内容:', asideContent?.substring(0, 200) || '未找到左侧边栏');
    if (failedRequests.length > 0) {
      console.error('失败的API请求:', failedRequests);
    }
    
    // 尝试获取项目列表API的响应
    try {
      const projectsApiResponse = await page.evaluate(() => {
        return fetch('/api/v1/hierarchy/projects?page=1&page_size=10')
          .then(r => r.json())
          .catch(() => null);
      });
      console.error('当前项目列表API响应:', projectsApiResponse ? JSON.stringify(projectsApiResponse).substring(0, 300) : '无法获取');
    } catch (e) {
      console.error('无法获取项目列表API响应:', e);
    }
    
    throw new Error(
      `层级树容器未加载（超时）。页面标题: ${pageTitle}。` +
      `项目数量: ${projectsCount}。` +
      (projectSelectionVisible ? ' 页面显示"选择项目"界面。' : '') +
      (hasLoading ? ' 页面可能仍在加载。' : '') +
      (failedRequests.length > 0 ? `失败的API请求: ${failedRequests.join(', ')}。` : '') +
      `请检查：1) API是否正常响应 2) 测试环境是否有项目数据 3) 网络请求是否完成 4) projectId是否正确设置`
    );
  }
}
