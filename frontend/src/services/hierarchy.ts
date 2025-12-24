/** 层级结构 API 服务 */

import { apiGet } from './api';
import { ApiResponse, PaginatedResponse } from './api';

/**
 * 项目列表项
 */
export interface ProjectListItem {
  id: string;
  name: string;
  description?: string;
  building_count?: number;
  created_at: string;
  updated_at: string;
}

/**
 * 项目详情
 */
export interface ProjectDetail {
  id: string;
  name: string;
  description?: string;
  building_count?: number;
  created_at: string;
  updated_at: string;
}

/**
 * 层级节点
 */
export interface HierarchyNode {
  id: string;
  label: string;
  name: string;
  children: HierarchyNode[];
  metadata?: Record<string, any>;
}

/**
 * 层级树响应
 */
export interface HierarchyResponse {
  project_id: string;
  project_name: string;
  hierarchy: HierarchyNode;
}

/**
 * 单体详情
 */
export interface BuildingDetail {
  id: string;
  name: string;
  project_id: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

/**
 * 分部详情
 */
export interface DivisionDetail {
  id: string;
  name: string;
  building_id: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

/**
 * 子分部详情
 */
export interface SubDivisionDetail {
  id: string;
  name: string;
  division_id: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

/**
 * 分项详情
 */
export interface ItemDetail {
  id: string;
  name: string;
  subdivision_id: string;
  description?: string;
  inspection_lot_count?: number;
  created_at: string;
  updated_at: string;
}

/**
 * 检验批详情
 */
export interface InspectionLotDetail {
  id: string;
  name: string;
  item_id: string;
  spatial_scope?: string;
  status: 'PLANNING' | 'IN_PROGRESS' | 'SUBMITTED' | 'APPROVED' | 'PUBLISHED';
  element_count?: number;
  created_at: string;
  updated_at: string;
}

/**
 * 获取项目列表
 */
export async function getProjects(
  page: number = 1,
  pageSize: number = 20
): Promise<PaginatedResponse<ProjectListItem>> {
  const response = await apiGet<ApiResponse<PaginatedResponse<ProjectListItem>>>(
    `/api/v1/hierarchy/projects?page=${page}&page_size=${pageSize}`
  );
  return response.data;
}

/**
 * 获取项目详情
 */
export async function getProjectDetail(projectId: string): Promise<ProjectDetail> {
  const response = await apiGet<ApiResponse<ProjectDetail>>(
    `/api/v1/hierarchy/projects/${projectId}`
  );
  return response.data;
}

/**
 * 获取项目层级树
 */
export async function getProjectHierarchy(projectId: string): Promise<HierarchyResponse> {
  const response = await apiGet<ApiResponse<HierarchyResponse>>(
    `/api/v1/hierarchy/projects/${projectId}/hierarchy`
  );
  return response.data;
}

/**
 * 获取单体详情
 */
export async function getBuildingDetail(buildingId: string): Promise<BuildingDetail> {
  const response = await apiGet<ApiResponse<BuildingDetail>>(
    `/api/v1/hierarchy/buildings/${buildingId}`
  );
  return response.data;
}

/**
 * 获取分部详情
 */
export async function getDivisionDetail(divisionId: string): Promise<DivisionDetail> {
  const response = await apiGet<ApiResponse<DivisionDetail>>(
    `/api/v1/hierarchy/divisions/${divisionId}`
  );
  return response.data;
}

/**
 * 获取子分部详情
 */
export async function getSubDivisionDetail(subdivisionId: string): Promise<SubDivisionDetail> {
  const response = await apiGet<ApiResponse<SubDivisionDetail>>(
    `/api/v1/hierarchy/subdivisions/${subdivisionId}`
  );
  return response.data;
}

/**
 * 获取分项详情
 */
export async function getItemDetail(itemId: string): Promise<ItemDetail> {
  const response = await apiGet<ApiResponse<ItemDetail>>(
    `/api/v1/hierarchy/items/${itemId}`
  );
  return response.data;
}

/**
 * 获取检验批详情
 */
export async function getInspectionLotDetail(lotId: string): Promise<InspectionLotDetail> {
  const response = await apiGet<ApiResponse<InspectionLotDetail>>(
    `/api/v1/hierarchy/inspection-lots/${lotId}`
  );
  return response.data;
}

