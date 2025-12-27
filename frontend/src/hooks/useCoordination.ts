/** 管线综合排布 Hook */

import { useState, useCallback } from 'react';
import { coordinateLayout, type CoordinationConstraints, type CoordinationResponse } from '@/services/routing';
import { useToastContext } from '@/providers/ToastProvider';

export interface CoordinationState {
  result: CoordinationResponse | null;
  isLoading: boolean;
  error: string | null;
}

export function useCoordination() {
  const [coordinationState, setCoordinationState] = useState<CoordinationState>({
    result: null,
    isLoading: false,
    error: null,
  });
  const { showToast } = useToastContext();

  const coordinate = useCallback(
    async (
      levelId: string,
      elementIds?: string[],
      constraints?: CoordinationConstraints
    ) => {
      setCoordinationState({
        result: null,
        isLoading: true,
        error: null,
      });

      try {
        const result = await coordinateLayout(levelId, elementIds, constraints);

        setCoordinationState({
          result,
          isLoading: false,
          error: null,
        });

        if (result.errors.length > 0) {
          showToast(`管线综合排布错误: ${result.errors.join(', ')}`, 'error');
        } else if (result.warnings.length > 0) {
          showToast(`管线综合排布警告: ${result.warnings.join(', ')}`, 'warning');
        } else {
          showToast(
            `管线综合排布完成，解决了 ${result.collisions_resolved} 个碰撞`,
            'success'
          );
        }

        return result;
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : '管线综合排布失败';
        setCoordinationState({
          result: null,
          isLoading: false,
          error: errorMessage,
        });
        showToast(errorMessage, 'error');
        throw error;
      }
    },
    [showToast]
  );

  const clearResult = useCallback(() => {
    setCoordinationState({
      result: null,
      isLoading: false,
      error: null,
    });
  }, []);

  return {
    coordinationState,
    coordinate,
    clearResult,
  };
}

