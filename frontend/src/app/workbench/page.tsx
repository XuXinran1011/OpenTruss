/** HITL Workbench 主页面 */

'use client';

import { useState, useEffect, useRef } from 'react';
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
  const [projectId, setProjectId] = useState<string | null>(null);
  const canvasRef = useRef<CanvasHandle>(null);

  // 获取项目列表（用于选择项目）
  const { data: projectsData, isLoading: isLoadingProjects } = useQuery({
    queryKey: ['projects'],
    queryFn: () => getProjects(1, 20),
  });

  // 设置默认项目
  // 确保在项目列表加载完成后立即设置默认项目，避免显示选择界面
  useEffect(() => {
    // 如果项目列表正在加载，不执行任何操作
    if (isLoadingProjects) {
      return;
    }
    
    // 如果项目列表已加载且有项目，且当前没有projectId，设置第一个项目
    if (projectsData?.items && projectsData.items.length > 0 && !projectId) {
      const firstProject = projectsData.items[0];
      setProjectId(firstProject.id);
      setCurrentProjectId(firstProject.id);
    } 
    // 如果项目列表已加载但为空，且当前没有projectId，但store中有currentProjectId，使用store中的值
    else if (currentProjectId && !projectId && !isLoadingProjects) {
      setProjectId(currentProjectId);
    }
  }, [projectsData, projectId, currentProjectId, setCurrentProjectId, isLoadingProjects]);

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
                    setProjectId(project.id);
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

