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
  
  // 等待项目列表按钮加载（增加等待时间，确保界面完全加载）
  await page.waitForSelector('button', { timeout: 10000 }).catch(() => {});
  
  // 等待一小段时间，确保所有按钮都已渲染
  await page.waitForTimeout(500);
  
  // 选择第一个项目按钮（使用更精确的选择器：在"选择项目"标题下的按钮）
  // 优先选择包含项目名称的按钮（项目名称通常包含中文字符或特定格式）
  const projectSelectionContainer = page.locator('text=/选择项目/i').locator('..').first();
  const projectButtons = projectSelectionContainer.locator('button').filter({ 
    hasText: /.+/,
    hasNotText: /登录|登录|Login|提交|取消/i 
  });
  
  // 如果容器内没有找到按钮，尝试在整个页面中查找（fallback）
  let firstProjectButton = projectButtons.first();
  if (await firstProjectButton.count() === 0) {
    console.log('在项目选择容器中未找到按钮，尝试在整个页面中查找...');
    firstProjectButton = page.locator('button').filter({ 
      hasText: /.+/,
      hasNotText: /登录|登录|Login|提交|取消/i 
    }).first();
  }
  
  if (await firstProjectButton.count() > 0 && await firstProjectButton.isVisible({ timeout: 5000 }).catch(() => false)) {
    const buttonText = await firstProjectButton.textContent().catch(() => '');
    console.log(`点击第一个项目按钮: "${buttonText}"`);
    await firstProjectButton.click();
    
    // 等待项目选择后的页面更新
    await page.waitForLoadState('networkidle', { timeout: 15000 });
    
    // 等待"选择项目"界面消失，确认WorkbenchLayout开始渲染
    // 检查工具栏元素是否出现（这是WorkbenchLayout渲染的第一个可见元素）
    try {
      await page.waitForSelector('div.h-12.bg-white.border-b', { timeout: 10000 });
      console.log('✓ 项目已选择，WorkbenchLayout开始渲染');
      return true;
    } catch (e) {
      // 如果工具栏没有出现，检查是否仍然显示"选择项目"界面
      const stillShowingSelection = await projectSelectionTitle.isVisible({ timeout: 2000 }).catch(() => false);
      if (stillShowingSelection) {
        console.warn('警告：点击项目按钮后，"选择项目"界面仍然显示');
        return false;
      }
      // 如果"选择项目"界面已消失，即使工具栏还没出现，也认为选择成功
      console.log('✓ 项目已选择，"选择项目"界面已消失');
      return true;
    }
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
  // 首先等待工具栏元素出现（这是WorkbenchLayout渲染的第一个可见元素）
  // 工具栏会在WorkbenchLayout渲染时立即出现，比aside元素更早
  try {
    await page.waitForSelector('div.h-12.bg-white.border-b', { timeout: 15000 });
    console.log('✓ 工具栏已出现');
  } catch (e) {
    // 如果工具栏没有出现，检查是否仍然显示"选择项目"界面
    const projectSelectionTitle = page.locator('text=/选择项目/i').first();
    const isProjectSelectionVisible = await projectSelectionTitle.isVisible({ timeout: 2000 }).catch(() => false);
    
    if (isProjectSelectionVisible) {
      const pageContent = await page.content().catch(() => '无法获取页面内容');
      throw new Error(
        `WorkbenchLayout未渲染：页面仍然显示"选择项目"界面。` +
        `这可能是因为：1) 项目选择失败 2) React状态更新延迟 3) 前端代码错误。` +
        `页面内容预览: ${pageContent.substring(0, 500)}`
      );
    }
    
    // 如果工具栏超时且不是"选择项目"界面，继续尝试等待aside元素
    console.warn('警告：工具栏未在预期时间内出现，尝试等待aside元素...');
  }
  
  // 等待左侧边栏（aside）元素出现
  try {
    await page.waitForSelector('aside', { timeout: 15000 });
  } catch (e) {
    const pageContent = await page.content().catch(() => '无法获取页面内容');
    const hasProjectSelection = pageContent.includes('选择项目');
    const hasLoading = pageContent.includes('加载项目列表');
    const hasToolbar = pageContent.includes('h-12 bg-white border-b');
    
    throw new Error(
      `左侧边栏（aside）未渲染。` +
      (hasProjectSelection ? ' 页面显示"选择项目"界面。' : '') +
      (hasLoading ? ' 页面可能仍在加载。' : '') +
      (hasToolbar ? ' 工具栏已出现，但左侧边栏未出现。' : ' 工具栏也未出现。')
    );
  }
  
  // 确保左侧边栏已渲染且可见
  const asideElement = page.locator('aside').first();
  const isAsideVisible = await asideElement.isVisible({ timeout: 10000 }).catch(() => false);
  
  if (!isAsideVisible) {
    const pageContent = await page.content().catch(() => '无法获取页面内容');
    const hasProjectSelection = pageContent.includes('选择项目');
    const hasLoading = pageContent.includes('加载项目列表');
    
    throw new Error(
      `左侧边栏未渲染或不可见。` +
      (hasProjectSelection ? ' 页面显示"选择项目"界面。' : '') +
      (hasLoading ? ' 页面可能仍在加载。' : '') +
      ` 这可能是因为：1) 左侧边栏被折叠 2) CSS样式问题 3) 渲染时序问题`
    );
  }
  
  console.log('✓ WorkbenchLayout已渲染，左侧边栏已出现');
}

/**
 * 设置响应监听器（用于在导航前注册，确保能捕获所有API请求）
 * 必须在page.goto()之前调用
 * 
 * @returns 包含failedRequests数组的对象，用于传递给ensureWorkbenchReady
 */
export function setupResponseListeners(page: Page): { failedRequests: string[] } {
  const failedRequests: string[] = [];
  page.on('response', (response) => {
    if (!response.ok() && response.url().includes('/api/v1/hierarchy/')) {
      failedRequests.push(`${response.url()}: ${response.status()} ${response.statusText()}`);
    }
  });
  return { failedRequests };
}

/**
 * 确保Workbench页面已准备好
 * 包括：检查项目数据、选择项目（如果需要）、等待WorkbenchLayout渲染、等待层级树容器出现
 * 
 * 注意：如果需要在导航前捕获API请求，请先调用setupResponseListeners(page)并在page.goto()之前，
 * 然后将返回的failedRequests传入此函数
 * 
 * @param page Playwright Page对象
 * @param failedRequests 可选的失败请求数组（如果已在导航前通过setupResponseListeners设置监听器）
 */
export async function ensureWorkbenchReady(
  page: Page,
  failedRequests?: string[]
): Promise<void> {
  // 如果没有传入failedRequests，创建一个新的数组并注册监听器
  const failedRequestsArray = failedRequests || [];
  if (!failedRequests) {
    page.on('response', (response) => {
      if (!response.ok() && response.url().includes('/api/v1/hierarchy/')) {
        failedRequestsArray.push(`${response.url()}: ${response.status()} ${response.statusText()}`);
      }
    });
  }
  
  // 等待项目列表API请求完成并检查响应
  // 注意：如果页面已经在workbench且API请求已完成，waitForResponse可能会超时
  // 因此我们需要同时检查是否已经有响应数据
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
    // 如果waitForResponse超时，可能是API请求在监听器注册之前就已完成
    // 尝试直接从页面上下文中获取项目数据
    console.warn('警告：无法通过waitForResponse获取项目列表API响应，尝试直接从页面获取数据...');
    
    try {
      const projectsData = await page.evaluate(async () => {
        try {
          const response = await fetch('/api/v1/hierarchy/projects?page=1&page_size=10');
          if (response.ok) {
            return await response.json();
          }
          return null;
        } catch (e) {
          return null;
        }
      });
      
      if (projectsData?.data?.items) {
        projectsCount = projectsData.data.items.length;
        if (projectsCount > 0) {
          console.log(`✓ 通过直接请求获取项目列表，找到 ${projectsCount} 个项目`);
        }
      }
    } catch (e) {
      console.warn('无法直接从页面获取项目数据:', e);
    }
  }
  
  // 等待页面加载完成
  await page.waitForLoadState('networkidle', { timeout: 15000 });
  
  // 选择项目（如果需要）
  const projectSelected = await selectProjectIfNeeded(page);
  
  // 如果尝试选择了项目，等待"选择项目"界面消失
  if (projectSelected) {
    console.log('等待"选择项目"界面消失...');
    try {
      const projectSelectionTitle = page.locator('text=/选择项目/i').first();
      await projectSelectionTitle.waitFor({ state: 'hidden', timeout: 10000 });
      console.log('✓ "选择项目"界面已消失');
    } catch (e) {
      // 如果"选择项目"界面仍然显示，记录警告但继续执行
      const stillVisible = await page.locator('text=/选择项目/i').first().isVisible({ timeout: 2000 }).catch(() => false);
      if (stillVisible) {
        console.warn('警告："选择项目"界面仍然显示，但继续尝试等待WorkbenchLayout渲染');
      }
    }
  }
  
  // 在等待WorkbenchLayout之前，先检查是否仍然显示"选择项目"界面
  // 如果显示，说明项目选择失败或React状态更新延迟
  const projectSelectionTitle = page.locator('text=/选择项目/i').first();
  const isProjectSelectionVisible = await projectSelectionTitle.isVisible({ timeout: 2000 }).catch(() => false);
  
  if (isProjectSelectionVisible && projectsCount > 0) {
    // 如果有项目数据但仍在显示"选择项目"界面，尝试再次选择
    console.log('检测到"选择项目"界面仍然显示，尝试再次选择项目...');
    const retrySelected = await selectProjectIfNeeded(page);
    if (!retrySelected) {
      console.warn('警告：重试选择项目失败，但继续尝试等待WorkbenchLayout渲染');
    }
  }
  
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
      const apiErrors = failedRequestsArray.length > 0 ? failedRequestsArray.join(', ') : '无';
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
    if (failedRequestsArray.length > 0) {
      console.error('失败的API请求:', failedRequestsArray);
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
      (failedRequestsArray.length > 0 ? `失败的API请求: ${failedRequestsArray.join(', ')}。` : '') +
      `请检查：1) API是否正常响应 2) 测试环境是否有项目数据 3) 网络请求是否完成 4) projectId是否正确设置`
    );
  }
}
