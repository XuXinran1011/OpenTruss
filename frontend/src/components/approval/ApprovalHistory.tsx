/** 审批历史组件 */

'use client';

import { ApprovalHistoryItem } from '@/services/approval';

interface ApprovalHistoryProps {
  history: ApprovalHistoryItem[];
}

export function ApprovalHistory({ history }: ApprovalHistoryProps) {
  if (history.length === 0) {
    return (
      <div className="text-sm text-zinc-500 py-4 text-center">暂无审批历史</div>
    );
  }

  return (
    <div className="space-y-3">
      {history.map((item, index) => (
        <div
          key={index}
          className="p-3 bg-zinc-50 rounded-md border border-zinc-200"
        >
          <div className="flex items-start justify-between mb-2">
            <div className="flex items-center gap-2">
              <span
                className={`px-2 py-0.5 text-xs font-medium rounded ${
                  item.action === 'APPROVE'
                    ? 'bg-emerald-100 text-emerald-800'
                    : 'bg-red-100 text-red-800'
                }`}
              >
                {item.action === 'APPROVE' ? '审批通过' : '驳回'}
              </span>
              <span className="text-xs text-zinc-500">
                {new Date(item.timestamp).toLocaleString('zh-CN')}
              </span>
            </div>
            <span className="text-xs text-zinc-500">{item.user_id}</span>
          </div>

          <div className="text-xs text-zinc-600 mb-1">
            状态变更: {item.old_status} → {item.new_status}
          </div>

          {item.comment && (
            <div className="text-sm text-zinc-700 mt-2 pt-2 border-t border-zinc-200">
              {item.comment}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

