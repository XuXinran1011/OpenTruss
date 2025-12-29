/**
 * E2E测试 - Workbench页面辅助函数
 */

import { Page, expect } from '@playwright/test';

/**
 * 页面状态信息
 */
interface PageState {
  isLoading: boolean;
  isProjectSelection: boolean;
  isWorkbenchLayout: boolean;
  projectId: string | null;
  pageContent: string;
  pageUrl: string;
}

/**
 * 等待React完全渲染
 * 确保页面body元素存在且有内容，React已经完成hydration
 */
async function waitForReactRender(page: Page, timeout = 10000): Promise<void> {
  // 等待DOM加载完成
  await page.waitForLoadState('domcontentloaded', { timeout });
  
  // 等待body元素存在
  await page.waitForSelector('body', { timeout, state: 'attached' });
  
  // 等待body内有内容（不只是HTML骨架）
  // 通过检查body的innerHTML是否包含React渲染的内容来判断
  await page.waitForFunction(
    () => {
      const body = document.body;
      if (!body) return false;
      
      // 检查body是否有子元素（React根元素）
      if (body.children.length === 0) return false;
      
      // 检查是否有React根元素（Next.js通常使用#__next作为根元素）
      const root = body.querySelector('#__next') || body.children[0];
      if (!root) return false;
      
      // 检查根元素是否有内容（文本或子元素）
      return root.textContent?.trim().length > 0 || root.children.length > 0;
    },
    { timeout }
  ).catch(() => {
    // 如果等待失败，至少等待一小段时间确保React有时间渲染
    return page.waitForTimeout(500);
  });
  
  // 额外等待一小段时间，确保React状态更新完成
  await page.waitForTimeout(200);
}

/**
 * 获取页面当前状态
 * 用于诊断页面处于哪种状态（加载中、选择项目、WorkbenchLayout）
 */
async function getPageState(page: Page): Promise<PageState> {
  // 先等待React完全渲染
  await waitForReactRender(page, 5000).catch(() => {
    // 如果等待失败，记录警告但继续执行
    console.warn('警告：等待React渲染超时，继续检查页面状态');
  });
  const pageContent = await page.content().catch(() => '无法获取页面内容');
  const pageUrl = page.url();
  
  // 检查是否显示"加载项目列表..."
  const isLoadingText = page.locator('text=/加载项目列表/i').first();
  const isLoading = await isLoadingText.isVisible({ timeout: 2000 }).catch(() => false);
  
  // 检查是否显示"选择项目"界面
  const projectSelectionTitle = page.locator('text=/选择项目/i').first();
  const isProjectSelection = await projectSelectionTitle.isVisible({ timeout: 2000 }).catch(() => false);
  
  // 检查是否显示WorkbenchLayout（工具栏或aside是否存在）
  const toolbar = page.locator('div.h-12.bg-white.border-b, div.relative.z-50.h-12.bg-white.border-b').first();
  const aside = page.locator('aside').first();
  const hasToolbar = await toolbar.isVisible({ timeout: 1000 }).catch(() => false);
  const hasAside = await aside.isVisible({ timeout: 1000 }).catch(() => false);
  const isWorkbenchLayout = hasToolbar || hasAside;
  
  // 尝试从页面上下文获取projectId（如果可能）
  let projectId: string | null = null;
  try {
    projectId = await page.evaluate(() => {
      // 尝试从React DevTools或全局状态获取projectId
      // 如果无法获取，返回null
      try {
        // 检查是否有项目选择按钮被点击（通过检查按钮的状态）
        // 或者通过检查WorkbenchLayout是否渲染来判断projectId是否存在
        return null; // 暂时无法直接从页面获取projectId
      } catch (e) {
        return null;
      }
    });
  } catch (e) {
    // 如果无法获取projectId，保持为null
  }
  
  return {
    isLoading,
    isProjectSelection,
    isWorkbenchLayout,
    projectId,
    pageContent,
    pageUrl,
  };
}

/**
 * 选择第一个项目（如果需要）
 * 如果页面显示"选择项目"界面，自动选择第一个项目
 */
export async function selectProjectIfNeeded(page: Page): Promise<boolean> {
  // 先等待"加载项目列表..."消失
  const loadingText = page.locator('text=/加载项目列表/i').first();
  const isLoading = await loadingText.isVisible({ timeout: 5000 }).catch(() => false);
  
  if (isLoading) {
    console.log('检测到"加载项目列表..."状态，等待加载完成...');
    try {
      await loadingText.waitFor({ state: 'hidden', timeout: 15000 });
      console.log('✓ "加载项目列表..."状态已消失');
    } catch (e) {
      console.warn('警告："加载项目列表..."状态超时，继续尝试检查项目选择界面');
    }
  }
  
  // 检查是否显示项目选择界面
  const projectSelectionTitle = page.locator('text=/选择项目/i').first();
  const isProjectSelectionVisible = await projectSelectionTitle.isVisible({ timeout: 5000 }).catch(() => false);
  
  if (!isProjectSelectionVisible) {
    // 如果不在显示"选择项目"界面，检查是否已经显示WorkbenchLayout
    const toolbar = page.locator('div.h-12.bg-white.border-b, div.relative.z-50.h-12.bg-white.border-b').first();
    const hasToolbar = await toolbar.isVisible({ timeout: 2000 }).catch(() => false);
    if (hasToolbar) {
      console.log('✓ WorkbenchLayout已渲染，不需要选择项目');
      return false; // 不需要选择项目
    }
    // 如果既没有显示"选择项目"界面，也没有显示WorkbenchLayout，返回false
    return false;
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
    
    // 等待React状态更新：检查"选择项目"界面是否消失
    try {
      await projectSelectionTitle.waitFor({ state: 'hidden', timeout: 10000 });
      console.log('✓ "选择项目"界面已消失，React状态已更新');
    } catch (e) {
      console.warn('警告："选择项目"界面未在预期时间内消失');
    }
    
    // 等待WorkbenchLayout开始渲染：检查工具栏元素是否出现
    try {
      await page.waitForSelector('div.h-12.bg-white.border-b, div.relative.z-50.h-12.bg-white.border-b', { timeout: 10000 });
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
  // 使用多个备选选择器以提高匹配成功率
  const toolbarSelectors = [
    'div.relative.z-50.h-12.bg-white.border-b', // 精确选择器（包含所有类名）
    'div.h-12.bg-white.border-b', // 简化选择器（部分类名）
  ];
  
  let toolbarFound = false;
  for (const selector of toolbarSelectors) {
    try {
      await page.waitForSelector(selector, { timeout: 15000 });
      console.log(`✓ 工具栏已出现（使用选择器: ${selector}）`);
      toolbarFound = true;
      break;
    } catch (e) {
      // 尝试下一个选择器
      continue;
    }
  }
  
  if (!toolbarFound) {
    // 如果工具栏没有出现，获取页面状态用于诊断
    const pageState = await getPageState(page);
    
    if (pageState.isProjectSelection) {
      throw new Error(
        `WorkbenchLayout未渲染：页面仍然显示"选择项目"界面。` +
        `这可能是因为：1) 项目选择失败 2) React状态更新延迟 3) 前端代码错误。` +
        `页面URL: ${pageState.pageUrl}。` +
        `页面内容预览: ${pageState.pageContent.substring(0, 500)}`
      );
    }
    
    if (pageState.isLoading) {
      throw new Error(
        `WorkbenchLayout未渲染：页面仍然显示"加载项目列表..."状态。` +
        `这可能是因为：1) API请求超时 2) 网络问题 3) 前端代码错误。` +
        `页面URL: ${pageState.pageUrl}。`
      );
    }
    
    // 如果工具栏超时且不是"选择项目"界面或"加载中"状态，继续尝试等待aside元素
    console.warn('警告：工具栏未在预期时间内出现，尝试等待aside元素...');
    console.warn(`页面状态: isLoading=${pageState.isLoading}, isProjectSelection=${pageState.isProjectSelection}, isWorkbenchLayout=${pageState.isWorkbenchLayout}`);
    console.warn(`页面URL: ${pageState.pageUrl}`);
  }
  
  // 等待左侧边栏（aside）元素出现
  try {
    await page.waitForSelector('aside', { timeout: 15000 });
  } catch (e) {
    // 如果aside超时，获取详细的页面状态用于诊断
    const pageState = await getPageState(page);
    
    const errorParts: string[] = ['左侧边栏（aside）未渲染。'];
    
    if (pageState.isProjectSelection) {
      errorParts.push('页面显示"选择项目"界面。');
    }
    if (pageState.isLoading) {
      errorParts.push('页面可能仍在加载。');
    }
    if (toolbarFound) {
      errorParts.push('工具栏已出现，但左侧边栏未出现。');
    } else {
      errorParts.push('工具栏也未出现。');
    }
    
    errorParts.push(`页面URL: ${pageState.pageUrl}。`);
    errorParts.push(`页面内容预览: ${pageState.pageContent.substring(0, 300)}。`);
    
    throw new Error(errorParts.join(' '));
  }
  
  // 确保左侧边栏已渲染且可见
  const asideElement = page.locator('aside').first();
  const isAsideVisible = await asideElement.isVisible({ timeout: 10000 }).catch(() => false);
  
  if (!isAsideVisible) {
    const pageState = await getPageState(page);
    
    const errorParts: string[] = ['左侧边栏未渲染或不可见。'];
    
    if (pageState.isProjectSelection) {
      errorParts.push('页面显示"选择项目"界面。');
    }
    if (pageState.isLoading) {
      errorParts.push('页面可能仍在加载。');
    }
    
    errorParts.push('这可能是因为：1) 左侧边栏被折叠 2) CSS样式问题 3) 渲染时序问题。');
    errorParts.push(`页面URL: ${pageState.pageUrl}。`);
    
    throw new Error(errorParts.join(' '));
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
  
  // 等待React完全渲染
  await waitForReactRender(page, 10000).catch(() => {
    console.warn('警告：等待React渲染超时，继续执行');
  });
  
  // 先等待"加载项目列表..."状态消失
  const loadingText = page.locator('text=/加载项目列表/i').first();
  const isLoading = await loadingText.isVisible({ timeout: 5000 }).catch(() => false);
  if (isLoading) {
    console.log('检测到"加载项目列表..."状态，等待加载完成...');
    try {
      await loadingText.waitFor({ state: 'hidden', timeout: 15000 });
      console.log('✓ "加载项目列表..."状态已消失');
      // 等待React状态更新
      await waitForReactRender(page, 5000).catch(() => {});
    } catch (e) {
      console.warn('警告："加载项目列表..."状态超时，继续执行');
    }
  }
  
  // 获取页面状态
  let pageState = await getPageState(page);
  console.log(`页面状态: isLoading=${pageState.isLoading}, isProjectSelection=${pageState.isProjectSelection}, isWorkbenchLayout=${pageState.isWorkbenchLayout}`);
  
  // 选择项目（如果需要）
  const projectSelected = await selectProjectIfNeeded(page);
  
  // 如果selectProjectIfNeeded返回false，检查是否已经渲染了WorkbenchLayout
  if (!projectSelected) {
    pageState = await getPageState(page);
    if (pageState.isWorkbenchLayout) {
      console.log('✓ WorkbenchLayout已渲染，跳过项目选择步骤');
    } else if (pageState.isProjectSelection && projectsCount > 0) {
      // 如果仍然显示"选择项目"界面，尝试再次选择
      console.log('检测到"选择项目"界面仍然显示，尝试再次选择项目...');
      const retrySelected = await selectProjectIfNeeded(page);
      if (!retrySelected) {
        console.warn('警告：重试选择项目失败，但继续尝试等待WorkbenchLayout渲染');
      }
    } else if (!pageState.isProjectSelection && !pageState.isWorkbenchLayout) {
      // 如果既不是"选择项目"界面，也不是WorkbenchLayout，记录诊断信息
      console.warn('警告：页面状态未知，既不是"选择项目"界面，也不是WorkbenchLayout');
      console.warn(`页面URL: ${pageState.pageUrl}`);
      console.warn(`页面内容预览: ${pageState.pageContent.substring(0, 300)}`);
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
