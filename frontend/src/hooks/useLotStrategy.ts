/**
 * 检验批策略管理 Hook
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  createLotsByRule,
  assignElementsToLot,
  removeElementsFromLot,
  updateLotStatus,
  getLotElements,
  CreateLotsByRuleRequest,
  AssignElementsRequest,
  RemoveElementsRequest,
  UpdateLotStatusRequest,
} from '@/services/lots';
import { getItemDetail } from '@/services/hierarchy';

/**
 * 使用检验批策略创建
 */
export function useCreateLotsByRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: CreateLotsByRuleRequest) => createLotsByRule(request),
    onSuccess: (data, variables) => {
      // 使相关查询失效，触发重新获取
      queryClient.invalidateQueries({ queryKey: ['hierarchy', 'items', variables.item_id] });
      queryClient.invalidateQueries({ queryKey: ['hierarchy'] });
    },
  });
}

/**
 * 使用检验批分配构件
 */
export function useAssignElementsToLot(lotId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: AssignElementsRequest) => assignElementsToLot(lotId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lots', lotId, 'elements'] });
      queryClient.invalidateQueries({ queryKey: ['elements'] });
      queryClient.invalidateQueries({ queryKey: ['hierarchy'] });
    },
  });
}

/**
 * 使用检验批移除构件
 */
export function useRemoveElementsFromLot(lotId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: RemoveElementsRequest) => removeElementsFromLot(lotId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lots', lotId, 'elements'] });
      queryClient.invalidateQueries({ queryKey: ['elements'] });
      queryClient.invalidateQueries({ queryKey: ['hierarchy'] });
    },
  });
}

/**
 * 使用检验批状态更新
 */
export function useUpdateLotStatus(lotId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: UpdateLotStatusRequest) => updateLotStatus(lotId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lots', lotId] });
      queryClient.invalidateQueries({ queryKey: ['hierarchy'] });
    },
  });
}

/**
 * 使用检验批构件列表
 */
export function useLotElements(lotId: string) {
  return useQuery({
    queryKey: ['lots', lotId, 'elements'],
    queryFn: () => getLotElements(lotId),
    enabled: !!lotId,
  });
}

/**
 * 使用分项详情（用于检验批管理）
 */
export function useItemDetailForLots(itemId: string | null) {
  return useQuery({
    queryKey: ['hierarchy', 'items', itemId],
    queryFn: () => getItemDetail(itemId!),
    enabled: !!itemId,
  });
}

