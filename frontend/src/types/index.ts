/** 通用类型定义 */

/**
 * 工作台模式
 */
export type WorkbenchMode = 'trace' | 'lift' | 'classify';

/**
 * 构件状态
 */
export type ElementStatus = 'Draft' | 'Verified';

/**
 * 检验批状态
 */
export type InspectionLotStatus = 'PLANNING' | 'IN_PROGRESS' | 'SUBMITTED' | 'APPROVED' | 'PUBLISHED';

/**
 * 几何类型
 */
export type GeometryType = 'Line' | 'Polyline';

/**
 * 2D 几何数据
 */
export interface Geometry2D {
  type: GeometryType;
  coordinates: number[][];
  closed?: boolean;
}

/**
 * 层级节点类型
 */
export type HierarchyNodeLabel = 'Project' | 'Building' | 'Division' | 'SubDivision' | 'Item' | 'InspectionLot';

/**
 * 问题构件类型
 */
export type IssueType = 'topology_error' | 'z_missing' | 'low_confidence';

/**
 * 问题构件
 */
export interface IssueElement {
  element_id: string;
  issue_type: IssueType;
  severity: 'high' | 'medium' | 'low';
}

