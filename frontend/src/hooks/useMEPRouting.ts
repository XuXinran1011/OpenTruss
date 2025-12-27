/** MEP 路径规划 Hook */

// React
import { useState, useCallback } from 'react';

// 本地模块
import { useToastContext } from '@/providers/ToastProvider';
import { calculateMEPRoute, validateMEPRoute, type MEPRoutingConstraints, type RoutingResponse, type ValidationResponse } from '@/services/routing';

export interface RoutingState {
  path: { x: number; y: number }[] | null;
  constraints: {
    bend_radius?: number;
    min_width?: number;
    pattern?: string;
  } | null;
  warnings: string[];
  errors: string[];
  isLoading: boolean;
}

export function useMEPRouting() {
  const [routingState, setRoutingState] = useState<RoutingState>({
    path: null,
    constraints: null,
    warnings: [],
    errors: [],
    isLoading: false,
  });
  const { showToast } = useToastContext();

  const calculateRoute = useCallback(
    async (
      start: { x: number; y: number },
      end: { x: number; y: number },
      constraints: MEPRoutingConstraints,
      sourceElementType?: string,
      targetElementType?: string,
      elementId?: string,
      levelId?: string,
      validateRoomConstraints: boolean = true,
      validateSlope: boolean = true
    ) => {
      setRoutingState((prev) => ({ ...prev, isLoading: true, errors: [], warnings: [] }));

      try {
        const result = await calculateMEPRoute(
          start,
          end,
          constraints,
          sourceElementType,
          targetElementType,
          elementId,
          levelId,
          validateRoomConstraints,
          validateSlope
        );

        setRoutingState({
          path: result.path_points,
          constraints: result.constraints,
          warnings: result.warnings,
          errors: result.errors,
          isLoading: false,
        });

        if (result.errors.length > 0) {
          showToast(`路径计算错误: ${result.errors.join(', ')}`, 'error');
        } else if (result.warnings.length > 0) {
          showToast(`路径计算警告: ${result.warnings.join(', ')}`, 'warning');
        }

        return result;
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : '路径计算失败';
        setRoutingState((prev) => ({
          ...prev,
          errors: [errorMessage],
          isLoading: false,
        }));
        showToast(errorMessage, 'error');
        throw error;
      }
    },
    [showToast]
  );

  const validateRoute = useCallback(
    async (
      path: { x: number; y: number }[],
      constraints: MEPRoutingConstraints,
      sourceElementType?: string,
      targetElementType?: string
    ) => {
      try {
        const result = await validateMEPRoute(
          path,
          constraints,
          sourceElementType,
          targetElementType
        );

        if (!result.valid) {
          const allErrors = [...result.semantic_errors, ...result.constraint_errors, ...result.errors];
          if (allErrors.length > 0) {
            showToast(`路径验证失败: ${allErrors.join(', ')}`, 'error');
          }
        } else if (result.warnings.length > 0) {
          showToast(`路径验证警告: ${result.warnings.join(', ')}`, 'warning');
        }

        return result;
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : '路径验证失败';
        showToast(errorMessage, 'error');
        throw error;
      }
    },
    [showToast]
  );

  const clearRoute = useCallback(() => {
    setRoutingState({
      path: null,
      constraints: null,
      warnings: [],
      errors: [],
      isLoading: false,
    });
  }, []);

  return {
    routingState,
    calculateRoute,
    validateRoute,
    clearRoute,
  };
}

