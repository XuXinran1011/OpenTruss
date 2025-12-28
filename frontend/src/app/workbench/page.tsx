/** HITL Workbench 主页面 */

'use client';

import { useEffect, useRef, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { WorkbenchLayout } from '@/components/layout/WorkbenchLayout';
import { TopToolbar } from '@/components/toolbar/TopToolbar';
import { HierarchyTree } from '@/components/hierarchy/HierarchyTree';
import { TriageQueue } from '@/components/triage/TriageQueue';
import { KeyboardShortcutsPanel } from '@/components/workbench/KeyboardShortcutsPanel';
import { Canvas, CanvasHandle } from '@/components/canvas/Canvas';
import { RightPanel } from '@/components/panel/RightPanel';
import { ToastProvider } from '@/providers/ToastProvider';
import { CanvasProvider } from '@/contexts/CanvasContext';
import { DragProvider } from '@/contexts/DragContext';
import { AuthGuard } from '@/components/auth/AuthGuard';
import { getProjects } from '@/services/hierarchy';
import { useHierarchyStore } from '@/stores/hierarchy';
import { useWorkbenchStore } from '@/stores/workbench';

export default function WorkbenchPage() {
  const { mode } = useWorkbenchStore();
  const { currentProjectId, setCurrentProjectId } = useHierarchyStore();
  const canvasRef = useRef<CanvasHandle>(null);

  // 获取项目列表（用于选择项目）
  const { data: projectsData, isLoading: isLoadingProjects } = useQuery({
    queryKey: ['projects'],
    queryFn: () => getProjects(1, 20),
  });

  // 使用useMemo直接计算projectId，避免状态更新时序问题
  // 这样在render时就能立即得到正确的值，不需要等待状态更新
  const projectId = useMemo(() => {
    // 如果项目列表正在加载，返回null
    if (isLoadingProjects) {
      return null;
    }
    
    // 优先使用store中的currentProjectId（如果存在），这样可以保留用户的选择
    if (currentProjectId) {
      return currentProjectId;
    }
    
    // 如果store中没有currentProjectId，但项目列表已加载且有项目，使用第一个项目的ID
    if (projectsData?.items && projectsData.items.length > 0) {
      return projectsData.items[0].id;
    }
    
    // 否则，返回null
    return null;
  }, [projectsData, isLoadingProjects, currentProjectId]);

  // 当projectId计算出来后，更新store中的currentProjectId
  useEffect(() => {
    if (projectId && projectId !== currentProjectId) {
      setCurrentProjectId(projectId);
    }
  }, [projectId, currentProjectId, setCurrentProjectId]);

  // 如果项目列表正在加载，显示加载状态
  if (isLoadingProjects) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-white">
        <div className="text-center">
          <p className="text-zinc-500">加载项目列表...</p>
        </div>
      </div>
    );
  }

  // 如果没有项目，显示选择界面
  if (!projectId) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-white">
        <div className="text-center">
          <h1 className="text-2xl font-semibold text-zinc-900 mb-4">选择项目</h1>
          {projectsData && projectsData.items.length > 0 ? (
            <div className="space-y-2">
              {projectsData.items.map((project) => (
                <button
                  key={project.id}
                  onClick={() => {
                    // 直接更新store，useMemo会自动重新计算projectId
                    setCurrentProjectId(project.id);
                  }}
                  className="block w-full px-4 py-2 text-left text-zinc-700 bg-zinc-50 hover:bg-zinc-100 rounded transition-colors"
                >
                  {project.name}
                </button>
              ))}
            </div>
          ) : (
            <p className="text-zinc-500">暂无项目</p>
          )}
        </div>
      </div>
    );
  }

  return (
    <AuthGuard>
      <ToastProvider>
        <DragProvider>
        <CanvasProvider canvasRef={canvasRef}>
          <WorkbenchLayout
            toolbar={<TopToolbar />}
          leftSidebar={
            <div className="h-full flex flex-col">
              <TriageQueue />
              <div className="flex-1 overflow-hidden">
                <HierarchyTree projectId={projectId} />
              </div>
            </div>
          }
            canvas={<Canvas ref={canvasRef} />}
            rightPanel={<RightPanel />}
          />
        </CanvasProvider>
      </DragProvider>
      {/* 快捷键提示面板 */}
      <KeyboardShortcutsPanel mode={mode} />
    </ToastProvider>
    </AuthGuard>
  );
}

