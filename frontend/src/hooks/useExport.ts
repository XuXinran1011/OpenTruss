/** IFC 导出 Hook */

import { useMutation } from '@tanstack/react-query';
import {
  exportLotToIFC,
  exportProjectToIFC,
  batchExportLotsToIFC,
  downloadBlob,
} from '@/services/export';

/**
 * 导出检验批为 IFC
 */
export function useExportLotToIFC() {
  return useMutation({
    mutationFn: async ({ lotId, filename }: { lotId: string; filename?: string }) => {
      const blob = await exportLotToIFC(lotId);
      const finalFilename = filename || `lot_${lotId}.ifc`;
      downloadBlob(blob, finalFilename);
      return { lotId, filename: finalFilename };
    },
  });
}

/**
 * 导出项目为 IFC
 */
export function useExportProjectToIFC() {
  return useMutation({
    mutationFn: async ({ projectId, filename }: { projectId: string; filename?: string }) => {
      const blob = await exportProjectToIFC(projectId);
      const finalFilename = filename || `project_${projectId}.ifc`;
      downloadBlob(blob, finalFilename);
      return { projectId, filename: finalFilename };
    },
  });
}

/**
 * 批量导出检验批为 IFC
 */
export function useBatchExportLotsToIFC() {
  return useMutation({
    mutationFn: async ({ lotIds, filename }: { lotIds: string[]; filename?: string }) => {
      const blob = await batchExportLotsToIFC(lotIds);
      const finalFilename = filename || `batch_${lotIds.length}_lots.ifc`;
      downloadBlob(blob, finalFilename);
      return { lotIds, filename: finalFilename };
    },
  });
}

