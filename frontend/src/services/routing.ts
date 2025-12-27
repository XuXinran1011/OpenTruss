/** MEP 路径规划服务 */

import { apiPost } from './api';

export interface MEPRoutingConstraints {
  elementType: 'Pipe' | 'Duct' | 'CableTray' | 'Conduit' | 'Wire';
  systemType?: string; // 'gravity_drainage', 'pressure_water', etc.
  properties: {
    diameter?: number; // 毫米
    width?: number; // 毫米
    height?: number; // 毫米
    cable_bend_radius?: number; // 毫米（用于电缆桥架）
  };
}

// API 原始响应格式（path_points 是 number[][]）
interface RoutingResponseRaw {
  path_points: number[][];
  constraints: {
    bend_radius?: number;
    min_width?: number;
    pattern?: string;
  };
  warnings: string[];
  errors: string[];
}

// 转换后的响应格式（path_points 是 { x: number; y: number }[]）
export interface RoutingResponse {
  path_points: { x: number; y: number }[];
  constraints: {
    bend_radius?: number;
    min_width?: number;
    pattern?: string;
  };
  warnings: string[];
  errors: string[];
}

export interface ValidationResponse {
  valid: boolean;
  semantic_valid: boolean;
  constraint_valid: boolean;
  errors: string[];
  warnings: string[];
  semantic_errors: string[];
  constraint_errors: string[];
}

/**
 * 计算 MEP 路径
 */
export async function calculateMEPRoute(
  start: { x: number; y: number },
  end: { x: number; y: number },
  constraints: MEPRoutingConstraints,
  sourceElementType?: string,
  targetElementType?: string,
  elementId?: string,
  levelId?: string,
  validateRoomConstraints: boolean = true,
  validateSlope: boolean = true
): Promise<RoutingResponse> {
  const response = await apiPost<{ status: string; data: RoutingResponseRaw }>(
    '/routing/calculate',
    {
      start: [start.x, start.y],
      end: [end.x, end.y],
      element_type: constraints.elementType,
      element_properties: constraints.properties,
      system_type: constraints.systemType,
      source_element_type: sourceElementType,
      target_element_type: targetElementType,
      validate_semantic: true,
      element_id: elementId,
      level_id: levelId,
      validate_room_constraints: validateRoomConstraints,
      validate_slope: validateSlope,
    }
  );

  if (response.status !== 'success') {
    throw new Error('路径计算失败');
  }

  // 转换路径点格式：从 number[][] 转换为 { x: number; y: number }[]
  const pathPoints = response.data.path_points.map((pt: number[]) => ({
    x: pt[0],
    y: pt[1],
  }));

  return {
    ...response.data,
    path_points: pathPoints,
  };
}

/**
 * 验证 MEP 路径
 */
export async function validateMEPRoute(
  pathPoints: { x: number; y: number }[],
  constraints: MEPRoutingConstraints,
  sourceElementType?: string,
  targetElementType?: string
): Promise<ValidationResponse> {
  const response = await apiPost<{ status: string; data: ValidationResponse }>(
    '/routing/validate',
    {
      path_points: pathPoints.map((pt) => [pt.x, pt.y]),
      element_type: constraints.elementType,
      system_type: constraints.systemType,
      element_properties: constraints.properties,
      source_element_type: sourceElementType,
      target_element_type: targetElementType,
    }
  );

  if (response.status !== 'success') {
    throw new Error('路径验证失败');
  }

  return response.data;
}

/**
 * 批量路由规划
 */
export async function batchPlanRoutes(
  routes: Array<{
    start: { x: number; y: number };
    end: { x: number; y: number };
    constraints: MEPRoutingConstraints;
    sourceElementType?: string;
    targetElementType?: string;
  }>,
  levelId?: string,
  validateRoomConstraints: boolean = true
): Promise<{
  results: RoutingResponse[];
  total: number;
  success_count: number;
  failure_count: number;
}> {
  const response = await apiPost<{ status: string; data: any }>(
    '/routing/plan-batch',
    {
      routes: routes.map((route) => ({
        start: [route.start.x, route.start.y],
        end: [route.end.x, route.end.y],
        element_type: route.constraints.elementType,
        element_properties: route.constraints.properties,
        system_type: route.constraints.systemType,
        source_element_type: route.sourceElementType,
        target_element_type: route.targetElementType,
        validate_semantic: true,
      })),
      level_id: levelId,
      validate_room_constraints: validateRoomConstraints,
    }
  );

  if (response.status !== 'success') {
    throw new Error('批量路由规划失败');
  }

  // 转换路径点格式
  const results = response.data.results.map((result: any) => ({
    ...result,
    path_points: result.path_points.map((pt: number[]) => ({
      x: pt[0],
      y: pt[1],
    })),
  }));

  return {
    ...response.data,
    results,
  };
}

/**
 * 完成路由规划
 */
export async function completeRoutingPlanning(
  elementIds: string[],
  originalRouteRoomIds?: Record<string, string[]>
): Promise<{
  updated_count: number;
  total_count: number;
  element_ids: string[];
}> {
  const response = await apiPost<{ status: string; data: any }>(
    '/routing/complete-planning',
    {
      element_ids: elementIds,
      original_route_room_ids: originalRouteRoomIds,
    }
  );

  if (response.status !== 'success') {
    throw new Error('完成路由规划失败');
  }

  return response.data;
}

/**
 * 退回路由规划
 */
export async function revertRoutingPlanning(
  elementIds: string[]
): Promise<{
  updated_count: number;
  total_count: number;
  element_ids: string[];
}> {
  const response = await apiPost<{ status: string; data: any }>(
    '/routing/revert-planning',
    {
      element_ids: elementIds,
    }
  );

  if (response.status !== 'success') {
    throw new Error('退回路由规划失败');
  }

  return response.data;
}

/**
 * 管线综合排布
 */
export interface CoordinationConstraints {
  priorities?: Record<string, number>; // 元素ID -> 优先级值
  avoid_collisions?: boolean;
  minimize_bends?: boolean;
  close_to_ceiling?: boolean;
}

export interface AdjustedElement {
  element_id: string;
  original_path: number[][];
  adjusted_path: number[][];
  adjustment_type: 'horizontal_translation' | 'vertical_translation' | 'add_bend';
  adjustment_reason: string;
}

export interface CoordinationResponse {
  adjusted_elements: AdjustedElement[];
  collisions_resolved: number;
  warnings: string[];
  errors: string[];
}

export async function coordinateLayout(
  levelId: string,
  elementIds?: string[],
  constraints?: CoordinationConstraints
): Promise<CoordinationResponse> {
  const response = await apiPost<{ status: string; data: CoordinationResponse }>(
    '/routing/coordination',
    {
      level_id: levelId,
      element_ids: elementIds,
      constraints: constraints || {},
    }
  );

  if (response.status !== 'success') {
    throw new Error('管线综合排布失败');
  }

  return response.data;
}

