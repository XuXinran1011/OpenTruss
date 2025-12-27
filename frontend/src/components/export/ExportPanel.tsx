/** IFC 导出面板组件 */

'use client';

import { useState } from 'react';
import { useExportLotToIFC, useBatchExportLotsToIFC } from '@/hooks/useExport';
import { InspectionLotStatus } from '@/types';

interface ExportPanelProps {
  lotId?: string;
  lotStatus?: InspectionLotStatus;
  lotName?: string;
  approvedLotIds?: string[]; // 用于批量导出
}

export function ExportPanel({
  lotId,
  lotStatus,
  lotName,
  approvedLotIds = [],
}: ExportPanelProps) {
  const [selectedLotIds, setSelectedLotIds] = useState<string[]>([]);

  const exportLotMutation = useExportLotToIFC();
  const batchExportMutation = useBatchExportLotsToIFC();

  const canExport = lotStatus === 'APPROVED';

  const handleExportSingle = () => {
    if (lotId && !exportLotMutation.isPending) {
      exportLotMutation.mutate({
        lotId,
        filename: lotName ? `${lotName}.ifc` : undefined,
      });
    }
  };

  const handleBatchExport = () => {
    const idsToExport = selectedLotIds.length > 0 ? selectedLotIds : approvedLotIds;
    if (idsToExport.length > 0 && !batchExportMutation.isPending) {
      batchExportMutation.mutate({
        lotIds: idsToExport,
      });
    }
  };

  return (
    <div className="flex flex-col h-full bg-white">
      <div className="p-4 border-b border-zinc-200">
        <h2 className="text-lg font-semibold text-zinc-900">导出 IFC</h2>
        {lotName && <p className="text-sm text-zinc-600 mt-1">{lotName}</p>}
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* 单个检验批导出 */}
        {lotId && (
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-semibold text-zinc-900 mb-2">导出当前检验批</h3>
              {!canExport && (
                <p className="text-xs text-amber-600 mb-2">
                  检验批状态必须为 APPROVED 才能导出
                </p>
              )}
            </div>

            <button
              onClick={handleExportSingle}
              disabled={!canExport || exportLotMutation.isPending}
              className="w-full px-4 py-2 bg-zinc-900 text-white text-sm font-medium rounded hover:bg-zinc-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {exportLotMutation.isPending ? '导出中...' : '导出为 IFC'}
            </button>

            {exportLotMutation.isError && (
              <div className="text-sm text-red-600 bg-red-50 p-3 rounded-md">
                导出失败: {exportLotMutation.error?.message || '未知错误，请稍后重试'}
              </div>
            )}

            {exportLotMutation.isSuccess && (
              <div className="text-sm text-emerald-600 bg-emerald-50 p-3 rounded-md">
                导出成功！文件已开始下载。
              </div>
            )}
          </div>
        )}

        {/* 批量导出 */}
        {approvedLotIds.length > 0 && (
          <div className="space-y-4 border-t border-zinc-200 pt-6">
            <div>
              <h3 className="text-sm font-semibold text-zinc-900 mb-2">批量导出</h3>
              <p className="text-xs text-zinc-500 mb-3">
                选择要导出的检验批（已选择 {selectedLotIds.length} 个）
              </p>
            </div>

            <div className="max-h-60 overflow-y-auto space-y-2">
              {approvedLotIds.map((id) => (
                <label
                  key={id}
                  className="flex items-center p-2 hover:bg-zinc-50 rounded cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={selectedLotIds.includes(id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedLotIds([...selectedLotIds, id]);
                      } else {
                        setSelectedLotIds(selectedLotIds.filter((lid) => lid !== id));
                      }
                    }}
                    className="mr-2"
                  />
                  <span className="text-sm text-zinc-700">{id}</span>
                </label>
              ))}
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => setSelectedLotIds(approvedLotIds)}
                className="flex-1 px-3 py-1.5 text-xs font-medium text-zinc-700 bg-zinc-100 rounded hover:bg-zinc-200 transition-colors"
              >
                全选
              </button>
              <button
                onClick={() => setSelectedLotIds([])}
                className="flex-1 px-3 py-1.5 text-xs font-medium text-zinc-700 bg-zinc-100 rounded hover:bg-zinc-200 transition-colors"
              >
                清空
              </button>
            </div>

            <button
              onClick={handleBatchExport}
              disabled={batchExportMutation.isPending || approvedLotIds.length === 0}
              className="w-full px-4 py-2 bg-zinc-900 text-white text-sm font-medium rounded hover:bg-zinc-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {batchExportMutation.isPending
                ? '导出中...'
                : `批量导出 (${selectedLotIds.length > 0 ? selectedLotIds.length : approvedLotIds.length} 个)`}
            </button>

            {batchExportMutation.isError && (
              <div className="text-sm text-red-600">
                批量导出失败: {batchExportMutation.error?.message || '未知错误'}
              </div>
            )}

            {batchExportMutation.isSuccess && (
              <div className="text-sm text-emerald-600">
                批量导出成功！文件已开始下载。
              </div>
            )}
          </div>
        )}

        {!lotId && approvedLotIds.length === 0 && (
          <div className="text-sm text-zinc-500 text-center py-8">
            没有可导出的检验批
          </div>
        )}
      </div>
    </div>
  );
}

