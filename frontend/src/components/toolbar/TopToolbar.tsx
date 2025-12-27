/** 顶部工具栏组件 */

'use client';

import { useRef } from 'react';
import { useWorkbenchStore } from '@/stores/workbench';
import { useCanvasStore } from '@/stores/canvas';
import { WorkbenchMode } from '@/types';
import { cn } from '@/lib/utils';
import { useAuth } from '@/hooks/useAuth';

export function TopToolbar() {
  const { mode, setMode } = useWorkbenchStore();
  const { currentUser, logout } = useAuth();
  const { 
    showDwgBackground, 
    setShowDwgBackground, 
    dwgOpacity, 
    setDwgOpacity, 
    xrayMode, 
    setXrayMode,
    setDwgImage,
    setDwgImageUrl 
  } = useCanvasStore();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 处理 DWG 文件上传（使用后端API）
  const handleDwgUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // 检查文件类型
    if (!file.type.startsWith('image/')) {
      alert('请上传图片文件');
      return;
    }

    try {
      // 使用后端API上传
      const { uploadBackground, getBackgroundUrl } = await import('@/services/background');
      const backgroundInfo = await uploadBackground(file);
      
      // 使用后端URL加载图片
      const imageUrl = getBackgroundUrl(backgroundInfo.id);
      const img = new Image();
      img.onload = () => {
        setDwgImage(img);
        setDwgImageUrl(imageUrl);
        setShowDwgBackground(true);
      };
      img.onerror = () => {
        alert('图片加载失败');
      };
      img.src = imageUrl;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '上传失败';
      alert(`上传失败：${errorMessage}`);
    }
  };

  const modes: { id: WorkbenchMode; label: string }[] = [
    { id: 'trace', label: 'Trace' },
    { id: 'lift', label: 'Lift' },
    { id: 'classify', label: 'Classify' },
  ];

  return (
    <div className="h-full flex items-center justify-between px-4">
      {/* 左侧：模式切换 */}
      <div className="flex items-center gap-2">
        {modes.map((m) => (
          <button
            key={m.id}
            onClick={() => setMode(m.id)}
            className={cn(
              'px-4 py-1.5 text-sm font-medium rounded transition-colors',
              mode === m.id
                ? 'bg-zinc-900 text-white'
                : 'bg-zinc-100 text-zinc-700 hover:bg-zinc-200'
            )}
          >
            {m.label}
          </button>
        ))}
      </div>

      {/* 中间：Trace Mode 专用控件 */}
      {mode === 'trace' && (
        <div className="flex items-center gap-4">
          {/* DWG 底图上传 */}
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleDwgUpload}
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            className="px-3 py-1.5 text-xs font-medium rounded transition-colors bg-zinc-100 text-zinc-700 hover:bg-zinc-200"
          >
            上传 DWG 底图
          </button>

          {/* 底图显示/隐藏切换 */}
          <button
            onClick={() => setShowDwgBackground(!showDwgBackground)}
            className={cn(
              'px-3 py-1.5 text-xs font-medium rounded transition-colors',
              showDwgBackground
                ? 'bg-zinc-900 text-white'
                : 'bg-zinc-100 text-zinc-700 hover:bg-zinc-200'
            )}
            title={showDwgBackground ? '隐藏底图' : '显示底图'}
          >
            {showDwgBackground ? '隐藏底图' : '显示底图'}
          </button>

          {/* 底图控制面板（仅在显示时） */}
          {showDwgBackground && (
            <>
              {/* 底图透明度滑块 */}
              <div className="flex items-center gap-2">
                <label className="text-xs text-zinc-600 whitespace-nowrap">透明度</label>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={dwgOpacity * 100}
                  onChange={(e) => setDwgOpacity(Number(e.target.value) / 100)}
                  className="w-24 h-1.5 bg-zinc-200 rounded-lg appearance-none cursor-pointer accent-zinc-900"
                />
                <span className="text-xs text-zinc-600 w-10 text-right">
                  {Math.round(dwgOpacity * 100)}%
                </span>
              </div>

              {/* X-Ray 模式切换 */}
              <button
                onClick={() => setXrayMode(!xrayMode)}
                className={cn(
                  'px-3 py-1.5 text-xs font-medium rounded transition-colors',
                  xrayMode
                    ? 'bg-zinc-900 text-white'
                    : 'bg-zinc-100 text-zinc-700 hover:bg-zinc-200'
                )}
              >
                X-Ray
              </button>
            </>
          )}
        </div>
      )}

      {/* 右侧：工具按钮 */}
      <div className="flex items-center gap-2">
        <button
          className="px-3 py-1.5 text-sm text-zinc-700 hover:bg-zinc-100 rounded transition-colors"
          title="撤销 (Ctrl+Z)"
        >
          撤销
        </button>
        <button
          className="px-3 py-1.5 text-sm text-zinc-700 hover:bg-zinc-100 rounded transition-colors"
          title="重做 (Ctrl+Y)"
        >
          重做
        </button>
        <div className="w-px h-6 bg-zinc-300 mx-2" />
        <button
          className="px-3 py-1.5 text-sm text-zinc-700 hover:bg-zinc-100 rounded transition-colors"
          title="导出"
        >
          导出
        </button>
        <div className="w-px h-6 bg-zinc-300 mx-2" />
        {/* 用户信息和登出 */}
        {currentUser && (
          <div className="flex items-center gap-2 text-sm text-zinc-600">
            <span>{currentUser.name || currentUser.username}</span>
            <span className="text-zinc-400">|</span>
            <span className="text-zinc-500">{currentUser.role}</span>
          </div>
        )}
        <button
          onClick={logout}
          className="px-3 py-1 text-sm text-zinc-600 hover:text-zinc-900 hover:bg-zinc-100 rounded transition-colors"
        >
          登出
        </button>
      </div>
    </div>
  );
}

