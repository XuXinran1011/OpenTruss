/** 审批工作流 Hook */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  approveLot,
  rejectLot,
  getApprovalHistory,
  batchApproveLots,
  ApproveRequest,
  RejectRequest,
  BatchApproveRequest,
} from '@/services/approval';

/**
 * 审批通过检验批
 */
export function useApproveLot() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ lotId, request }: { lotId: string; request: ApproveRequest }) =>
      approveLot(lotId, request),
    onSuccess: (_, variables) => {
      // 使相关查询失效，触发重新获取
      queryClient.invalidateQueries({ queryKey: ['lot', variables.lotId] });
      queryClient.invalidateQueries({ queryKey: ['approvalHistory', variables.lotId] });
      queryClient.invalidateQueries({ queryKey: ['lots'] });
      queryClient.invalidateQueries({ queryKey: ['hierarchy'] });
    },
  });
}

/**
 * 驳回检验批
 */
export function useRejectLot() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ lotId, request }: { lotId: string; request: RejectRequest }) =>
      rejectLot(lotId, request),
    onSuccess: (_, variables) => {
      // 使相关查询失效，触发重新获取
      queryClient.invalidateQueries({ queryKey: ['lot', variables.lotId] });
      queryClient.invalidateQueries({ queryKey: ['approvalHistory', variables.lotId] });
      queryClient.invalidateQueries({ queryKey: ['lots'] });
      queryClient.invalidateQueries({ queryKey: ['hierarchy'] });
    },
  });
}

/**
 * 获取审批历史
 */
export function useApprovalHistory(lotId: string | null) {
  return useQuery({
    queryKey: ['approvalHistory', lotId],
    queryFn: () => getApprovalHistory(lotId!),
    enabled: !!lotId,
  });
}

/**
 * 批量审批通过检验批
 */
export function useBatchApproveLots() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: BatchApproveRequest) => batchApproveLots(request),
    onSuccess: () => {
      // 使相关查询失效，触发重新获取
      queryClient.invalidateQueries({ queryKey: ['lots'] });
      queryClient.invalidateQueries({ queryKey: ['hierarchy'] });
      queryClient.invalidateQueries({ queryKey: ['approvalHistory'] });
    },
  });
}

