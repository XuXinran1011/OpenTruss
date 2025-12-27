/** 工作台布局组件 */

'use client';

import { useState, ReactNode } from 'react';
import { Preview3DPanel } from '@/components/canvas/Preview3DPanel';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';

interface WorkbenchLayoutProps {
  leftSidebar: ReactNode;
  canvas: ReactNode;
  rightPanel: ReactNode;
  toolbar: ReactNode;
}

export function WorkbenchLayout({
  leftSidebar,
  canvas,
  rightPanel,
  toolbar,
}: WorkbenchLayoutProps) {
  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const [rightCollapsed, setRightCollapsed] = useState(false);
  const [preview3DCollapsed, setPreview3DCollapsed] = useState(true); // 默认折叠

  return (
    <div className="h-screen w-screen flex flex-col bg-white overflow-hidden">
      {/* 顶部工具栏（悬浮） */}
      <div className="relative z-50 h-12 bg-white border-b border-zinc-200 shadow-sm">
        {toolbar}
      </div>

      {/* 主内容区 */}
      <div className="flex-1 flex overflow-hidden">
        {/* 左侧边栏 */}
        <aside
          className={`
            bg-zinc-50 border-r border-zinc-200 transition-all duration-200
            ${leftCollapsed ? 'w-0 overflow-hidden' : 'w-[280px]'}
          `}
        >
          <div className="h-full flex flex-col">
            {/* 折叠按钮 */}
            <button
              onClick={() => setLeftCollapsed(!leftCollapsed)}
              className="absolute left-0 top-1/2 -translate-y-1/2 z-10 w-4 h-12 bg-zinc-200 hover:bg-zinc-300 border-r border-zinc-300 flex items-center justify-center transition-colors"
              aria-label={leftCollapsed ? '展开左侧边栏' : '折叠左侧边栏'}
            >
              <svg
                className={`w-3 h-3 text-zinc-700 transition-transform ${
                  leftCollapsed ? 'rotate-180' : ''
                }`}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 19l-7-7 7-7"
                />
              </svg>
            </button>

            {/* 侧边栏内容 */}
            <div className="flex-1 overflow-auto">{leftSidebar}</div>
          </div>
        </aside>

        {/* 中间画布 */}
        <main className="flex-1 overflow-hidden relative bg-white">
          {canvas}
        </main>

        {/* 右侧面板 */}
        <aside
          className={`
            bg-zinc-50 border-l border-zinc-200 transition-all duration-200
            ${rightCollapsed ? 'w-0 overflow-hidden' : 'w-[320px]'}
          `}
        >
          <div className="h-full flex flex-col">
            {/* 折叠按钮 */}
            <button
              onClick={() => setRightCollapsed(!rightCollapsed)}
              className="absolute right-0 top-1/2 -translate-y-1/2 z-10 w-4 h-12 bg-zinc-200 hover:bg-zinc-300 border-l border-zinc-300 flex items-center justify-center transition-colors"
              aria-label={rightCollapsed ? '展开右侧面板' : '折叠右侧面板'}
            >
              <svg
                className={`w-3 h-3 text-zinc-700 transition-transform ${
                  rightCollapsed ? '' : 'rotate-180'
                }`}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 19l-7-7 7-7"
                />
              </svg>
            </button>

            {/* 面板内容 */}
            <div className="flex-1 overflow-auto">{rightPanel}</div>
          </div>
        </aside>
        
        {/* 3D 预览面板（可折叠） */}
        <Preview3DPanel
          collapsed={preview3DCollapsed}
          onToggle={() => setPreview3DCollapsed(!preview3DCollapsed)}
        />
      </div>
    </div>
  );
}

