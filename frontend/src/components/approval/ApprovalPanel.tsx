/** 审批面板组件 */

'use client';

import { useState } from 'react';
import { useApproveLot, useRejectLot, useApprovalHistory } from '@/hooks/useApproval';
import { ApprovalHistory } from './ApprovalHistory';
import { InspectionLotStatus } from '@/types';

interface ApprovalPanelProps {
  lotId: string;
  lotStatus: InspectionLotStatus;
  lotName: string;
}

export function ApprovalPanel({ lotId, lotStatus, lotName }: ApprovalPanelProps) {
  const [approveComment, setApproveComment] = useState('');
  const [rejectReason, setRejectReason] = useState('');
  const [rejectLevel, setRejectLevel] = useState<'IN_PROGRESS' | 'PLANNING'>('IN_PROGRESS');
  const [role, setRole] = useState<'APPROVER' | 'PM'>('APPROVER');

  const approveMutation = useApproveLot();
  const rejectMutation = useRejectLot();
  const { data: historyData, isLoading: historyLoading } = useApprovalHistory(lotId);

  const canApprove = lotStatus === 'SUBMITTED';
  // canReject 权限检查由后端根据用户角色自动处理
  const canReject = lotStatus === 'SUBMITTED' || lotStatus === 'APPROVED';

  const handleApprove = () => {
    if (!approveMutation.isPending) {
      approveMutation.mutate({
        lotId,
        request: {
          comment: approveComment || undefined,
          // approver_id 从 JWT token 中自动获取
        },
      });
    }
  };

  const handleReject = () => {
    if (!rejectMutation.isPending && rejectReason.trim()) {
      rejectMutation.mutate({
        lotId,
        request: {
          reason: rejectReason,
          reject_level: rejectLevel,
          // rejector_id 和 role 从 JWT token 中自动获取
        },
      });
    }
  };

  return (
    <div className="flex flex-col h-full bg-white">
      <div className="p-4 border-b border-zinc-200">
        <h2 className="text-lg font-semibold text-zinc-900">审批检验批</h2>
        <p className="text-sm text-zinc-600 mt-1">{lotName}</p>
        <div className="mt-2">
          <span
            className={`inline-flex px-2 py-1 text-xs font-medium rounded ${
              lotStatus === 'SUBMITTED'
                ? 'bg-amber-100 text-amber-800'
                : lotStatus === 'APPROVED'
                ? 'bg-emerald-100 text-emerald-800'
                : 'bg-zinc-100 text-zinc-800'
            }`}
          >
            {lotStatus === 'SUBMITTED' ? '待审批' : lotStatus === 'APPROVED' ? '已验收' : lotStatus}
          </span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* 审批操作 */}
        {canApprove && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-zinc-900 mb-2">
                审批意见（可选）
              </label>
              <textarea
                value={approveComment}
                onChange={(e) => setApproveComment(e.target.value)}
                placeholder="输入审批意见..."
                className="w-full px-3 py-2 text-sm border border-zinc-300 rounded-md focus:outline-none focus:ring-2 focus:ring-zinc-900 focus:border-transparent"
                rows={3}
              />
            </div>

            <button
              onClick={handleApprove}
              disabled={approveMutation.isPending}
              className="w-full px-4 py-2 bg-emerald-600 text-white text-sm font-medium rounded hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {approveMutation.isPending ? '审批中...' : '审批通过'}
            </button>
          </div>
        )}

        {/* 驳回操作 */}
        {canReject && (
          <div className="space-y-4 border-t border-zinc-200 pt-6">
            <div>
              <label className="block text-sm font-medium text-zinc-900 mb-2">
                驳回原因 <span className="text-red-600">*</span>
              </label>
              <textarea
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                placeholder="输入驳回原因..."
                className="w-full px-3 py-2 text-sm border border-zinc-300 rounded-md focus:outline-none focus:ring-2 focus:ring-zinc-900 focus:border-transparent"
                rows={3}
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-zinc-900 mb-2">
                驳回级别
              </label>
              <select
                value={rejectLevel}
                onChange={(e) => setRejectLevel(e.target.value as 'IN_PROGRESS' | 'PLANNING')}
                className="w-full px-3 py-2 text-sm border border-zinc-300 rounded-md focus:outline-none focus:ring-2 focus:ring-zinc-900 focus:border-transparent"
              >
                <option value="IN_PROGRESS">返回到清洗中（IN_PROGRESS）</option>
                <option value="PLANNING">返回到规划中（PLANNING）</option>
              </select>
              <p className="text-xs text-zinc-500 mt-1">
                注意：只有 PM 角色可以驳回至 PLANNING，Approver 只能驳回至 IN_PROGRESS
              </p>
            </div>

            <button
              onClick={handleReject}
              disabled={rejectMutation.isPending || !rejectReason.trim()}
              className="w-full px-4 py-2 bg-red-600 text-white text-sm font-medium rounded hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {rejectMutation.isPending ? '驳回中...' : '驳回'}
            </button>
          </div>
        )}

        {/* 审批历史 */}
        <div className="border-t border-zinc-200 pt-6">
          <h3 className="text-sm font-semibold text-zinc-900 mb-3">审批历史</h3>
          {historyLoading ? (
            <p className="text-sm text-zinc-500">加载中...</p>
          ) : (
            <ApprovalHistory history={historyData?.history || []} />
          )}
        </div>
      </div>
    </div>
  );
}

