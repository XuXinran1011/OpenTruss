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
  const [showRejectConfirm, setShowRejectConfirm] = useState(false);

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

  const handleRejectClick = () => {
    if (!rejectReason.trim()) {
      return; // 如果原因为空，不显示确认对话框
    }
    setShowRejectConfirm(true);
  };

  const handleRejectConfirm = () => {
    if (!rejectMutation.isPending && rejectReason.trim()) {
      rejectMutation.mutate({
        lotId,
        request: {
          reason: rejectReason,
          reject_level: rejectLevel,
          // rejector_id 和 role 从 JWT token 中自动获取
        },
      }, {
        onSuccess: () => {
          setShowRejectConfirm(false);
          setRejectReason(''); // 清空原因
        },
        onError: () => {
          // 错误时不关闭对话框，让用户看到错误信息
        },
      });
    }
  };

  const handleRejectCancel = () => {
    setShowRejectConfirm(false);
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
                disabled={approveMutation.isPending}
              />
            </div>

            <button
              onClick={handleApprove}
              disabled={approveMutation.isPending}
              className="w-full px-4 py-2 bg-emerald-600 text-white text-sm font-medium rounded hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {approveMutation.isPending ? '审批中...' : '审批通过'}
            </button>

            {approveMutation.isError && (
              <div className="text-sm text-red-600 bg-red-50 p-3 rounded-md">
                审批失败: {approveMutation.error?.message || '未知错误，请稍后重试'}
              </div>
            )}

            {approveMutation.isSuccess && (
              <div className="text-sm text-emerald-600 bg-emerald-50 p-3 rounded-md">
                审批成功！检验批状态已更新为 APPROVED。
              </div>
            )}
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
              onClick={handleRejectClick}
              disabled={rejectMutation.isPending || !rejectReason.trim()}
              className="w-full px-4 py-2 bg-red-600 text-white text-sm font-medium rounded hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {rejectMutation.isPending ? '驳回中...' : '驳回'}
            </button>

            {rejectMutation.isError && (
              <div className="text-sm text-red-600 bg-red-50 p-3 rounded-md">
                驳回失败: {rejectMutation.error?.message || '未知错误，请稍后重试'}
              </div>
            )}

            {rejectMutation.isSuccess && (
              <div className="text-sm text-emerald-600 bg-emerald-50 p-3 rounded-md">
                驳回成功！检验批状态已更新为 {rejectLevel}。
              </div>
            )}
          </div>
        )}

        {/* 驳回确认对话框 */}
        {showRejectConfirm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
              <h3 className="text-lg font-semibold text-zinc-900 mb-2">确认驳回</h3>
              <p className="text-sm text-zinc-600 mb-4">
                您确定要驳回此检验批吗？驳回后状态将变更为 <strong>{rejectLevel === 'IN_PROGRESS' ? 'IN_PROGRESS（进行中）' : 'PLANNING（规划中）'}</strong>。
              </p>
              <div className="flex gap-3 justify-end">
                <button
                  onClick={handleRejectCancel}
                  disabled={rejectMutation.isPending}
                  className="px-4 py-2 text-sm font-medium text-zinc-700 bg-zinc-100 rounded hover:bg-zinc-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  取消
                </button>
                <button
                  onClick={handleRejectConfirm}
                  disabled={rejectMutation.isPending}
                  className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {rejectMutation.isPending ? '驳回中...' : '确认驳回'}
                </button>
              </div>
            </div>
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

