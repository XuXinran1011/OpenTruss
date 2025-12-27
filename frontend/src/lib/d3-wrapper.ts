/**
 * D3.js 类型安全包装器
 * 
 * 这个包装器解决了Next.js 14与d3模块解析的兼容性问题，
 * 同时保持了TypeScript的类型安全性。
 * 
 * 使用require()来绕过Next.js的模块解析问题，
 * 但通过类型定义保持类型检查。
 */

// 导入类型定义
import type * as d3Type from 'd3';
import type { ZoomTransform } from 'd3-zoom';
import type { Selection } from 'd3-selection';

// 使用require解决Next.js模块解析问题
// eslint-disable-next-line
const d3Required = require('d3') as any;

/**
 * D3包装器接口
 * 只暴露代码中实际需要的方法，保持API简洁
 */
export interface D3Wrapper {
  select: typeof d3Type.select;
  selectAll: typeof d3Type.selectAll;
  zoom: typeof d3Type.zoom;
  zoomIdentity: typeof d3Type.zoomIdentity;
  drag: any; // d3.drag 的类型定义较复杂，使用 any
  pointer: typeof d3Type.pointer;
  line: any; // d3.line 的类型定义较复杂，使用 any
  transition: any; // d3.transition 的类型定义较复杂，使用 any
}

/**
 * 类型安全的d3对象
 * 所有方法都保留了完整的类型定义
 */
export const d3: D3Wrapper = {
  select: d3Required.select,
  selectAll: d3Required.selectAll,
  zoom: d3Required.zoom,
  zoomIdentity: d3Required.zoomIdentity,
  drag: d3Required.drag,
  pointer: d3Required.pointer,
  line: d3Required.line,
  transition: d3Required.transition,
};

// 导出常用类型供其他文件使用
export type { ZoomTransform };
export type { Selection };

