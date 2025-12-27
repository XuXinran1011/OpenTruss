/** 快捷键提示面板 */

'use client';

import { useState } from 'react';
import { cn } from '@/lib/utils';

interface Shortcut {
  key: string;
  description: string;
  mode?: 'trace' | 'lift' | 'classify' | 'all';
}

const SHORTCUTS: Shortcut[] = [
  { key: 'T', description: '切换到 Trace Mode（描图模式）', mode: 'all' },
  { key: 'L', description: '切换到 Lift Mode（升维模式）', mode: 'all' },
  { key: 'C', description: '切换到 Classify Mode（归类模式）', mode: 'all' },
  { key: 'Delete / Backspace', description: '删除选中构件', mode: 'all' },
  { key: 'Escape', description: '清空选择', mode: 'all' },
  { key: '[', description: '减少 DWG 底图透明度', mode: 'trace' },
  { key: ']', description: '增加 DWG 底图透明度', mode: 'trace' },
];

interface KeyboardShortcutsPanelProps {
  mode?: 'trace' | 'lift' | 'classify';
  className?: string;
}

export function KeyboardShortcutsPanel({ mode = 'all', className }: KeyboardShortcutsPanelProps) {
  const [isOpen, setIsOpen] = useState(false);

  // 过滤当前模式相关的快捷键
  const relevantShortcuts = SHORTCUTS.filter(
    (s) => !s.mode || s.mode === 'all' || s.mode === mode
  );

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className={cn(
          'fixed bottom-4 right-4 z-40 px-3 py-2 text-xs font-medium text-zinc-700 bg-white border border-zinc-300 rounded-md shadow-sm hover:bg-zinc-50 transition-colors',
          className
        )}
        title="显示快捷键"
      >
        ⌨️ 快捷键
      </button>
    );
  }

  return (
    <div
      className={cn(
        'fixed bottom-4 right-4 z-40 bg-white border border-zinc-300 rounded-lg shadow-lg p-4 max-w-xs',
        className
      )}
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-zinc-900">快捷键</h3>
        <button
          onClick={() => setIsOpen(false)}
          className="text-zinc-400 hover:text-zinc-600 text-lg leading-none"
          aria-label="关闭"
        >
          ×
        </button>
      </div>

      <div className="space-y-2">
        {relevantShortcuts.map((shortcut, index) => (
          <div key={index} className="flex items-start justify-between gap-4 text-xs">
            <span className="text-zinc-600 flex-1">{shortcut.description}</span>
            <kbd className="px-2 py-1 font-mono text-xs font-medium text-zinc-700 bg-zinc-100 border border-zinc-300 rounded">
              {shortcut.key}
            </kbd>
          </div>
        ))}
      </div>
    </div>
  );
}

