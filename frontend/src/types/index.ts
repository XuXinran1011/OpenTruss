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
 * 3D 原生几何数据（OpenTruss 格式）
 * 
 * 底层数据模型是 3D 原生的，支持：
 * - AI 识别结果（2D 输入，自动补 z=0.0）
 * - Revit 导出数据（3D 输入，无损保存）
 * 
 * 坐标格式：[[x1, y1, z1], [x2, y2, z2], ...]
 */
export interface Geometry {
  type: GeometryType;
  coordinates: number[][]; // 3D 坐标：[[x, y, z], ...]，支持 2D 输入（自动补 z=0.0）
  closed?: boolean;
}

/**
 * @deprecated 使用 Geometry 代替（3D 原生）
 * 保留此类型以保持向后兼容
 */
export interface Geometry2D extends Geometry {}

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

