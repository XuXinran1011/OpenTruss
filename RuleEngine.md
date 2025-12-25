OpenTruss 规则引擎增量开发指南
文档版本: 1.0
适用阶段: Phase 2 - Phase 4
核心目标: 构建一个轻量、可扩展、前后端协同的校验体系，确保“垃圾进，精华出”。
0. 总体策略：前后端分工
我们不搞“一套规则，两处运行”，而是采用分层防御策略：
前端 (UX Layer): "软引导" (Soft Guidance)。
技术: TypeScript, Turf.js, RBush。
表现: 鼠标吸附、变色、悬浮提示。
目标: 让用户不容易犯错。
后端 (Data Layer): "硬阻断" (Hard Blocking)。
技术: Python, Memgraph (Cypher), Pydantic。
表现: 提交审批时报错、数据库一致性检查。
目标: 确保错误数据进不了生产库。
Phase 1: 语义“防呆” (MVP)
目标: 防止违反常识的连接（如：水管接柱子）。
1.1 规则定义 (Configuration)
在前端和后端共享一份 JSON 配置（或由后端 API 下发）。
文件: shared/rules/semantic_allowlist.json
逻辑: 白名单机制（Allowlist）。未定义的连接即为非法。
{
  "Objects.BuiltElements.Pipe": [
    "Objects.BuiltElements.Pipe",
    "Objects.BuiltElements.Valve",
    "Objects.BuiltElements.Pump",
    "Objects.BuiltElements.Tank"
  ],
  "Objects.BuiltElements.Wall": [
    "Objects.BuiltElements.Wall",
    "Objects.BuiltElements.Column"
  ]
}


1.2 前端实现 (交互反馈)
动作: 拖拽连线 (onDrag).
逻辑:
// frontend/src/lib/rules/SemanticValidator.ts
const canConnect = (sourceType: string, targetType: string): boolean => {
  const allowed = SemanticAllowlist[sourceType];
  return allowed && allowed.includes(targetType);
};


效果: 当用户拖动管线端点靠近柱子时，不显示磁吸光圈，强制释放会弹回。
1.3 后端实现 (提交阻断)
动作: 提交审批 (/submit).
逻辑: 遍历提交批次中的所有关系，检查类型对。
效果: 报错 "Error: Invalid Connection (Pipe -> Column)".
Phase 2: 构造“规范化” (Alpha)
目标: 解决 2D 到 3D 的转换合理性（如：角度吸附、管径匹配）。
2.1 规则定义 (Lookup Tables)
引入 MEP 行业的标准数据。
文件: shared/rules/fitting_standards.json
内容: 定义允许的角度容差。
{
  "angles": {
    "standard": [90, 45, 180],
    "tolerance": 5,  // +/- 5度以内自动吸附
    "allow_custom": false // 是否允许非标角度
  }
}


2.2 前端实现 (智能吸附)
动作: 拖拽结束 (onDrop)。
逻辑:
// frontend/src/lib/rules/ConstructabilityValidator.ts
const snapAngle = (currentAngle: number) => {
  for (const std of StandardAngles) {
    if (Math.abs(currentAngle - std) < Tolerance) return std;
  }
  return currentAngle; // 或者返回 false 拒绝连接
};


效果: 用户画了一个 88° 的线，松手后自动变成 90°。
2.3 后端实现 (Z轴完整性检查)
这是“逆向重构”特有的规则。
逻辑: 检查所有 Wall, Column 的 height 和 baseOffset 字段。
效果: 如果发现 height == null，拒绝将状态变更为 PENDING。
Phase 3: 空间“避障” (Beta)
目标: 简单的物理碰撞检测（无需重型 3D 引擎）。
3.1 核心算法：2.5D 包围盒
不使用 Mesh 碰撞，使用 AABB (Axis-Aligned Bounding Box) + Z-Range。
Box: [minX, minY, minZ, maxX, maxY, maxZ]
逻辑: 两个 Box 重叠 $\iff$ X轴重叠 && Y轴重叠 && Z轴重叠。
3.2 前端实现 (实时警告)
利用 RBush 库实现毫秒级查询。
数据结构: 将画布上所有构件插入 RBush 树。
动作: 拖拽过程中 (onDragMove)。
逻辑:
// 伪代码
const nearby = tree.search(currentDragBox);
const hits = nearby.filter(item => checkZOverlap(currentItem, item));
if (hits.length > 0) {
  showWarning("Clash Detected with " + hits[0].id);
}


效果: 拖动管道穿过柱子时，管道变红。
Phase 4: 拓扑“完整性” (RC / Production)
目标: 确保系统逻辑闭环（如：没有悬空的管道端点）。
4.1 规则定义 (Graph Logic)
这些规则运行在 Memgraph 图数据库中。
规则 1 (Open Ends): 管道端点必须连接到某个设备或另一根管道（除非标记为 Cap/堵头）。
规则 2 (Islands): 系统中不应存在孤立的子图（比如一根管子谁也不连）。
4.2 后端实现 (Cypher 校验)
这是最强大的防线。
// 查找所有悬空的管道端点 (Degree = 1)
MATCH (p:Pipe)-[r]-(target)
WITH p, count(r) as degree
WHERE degree < 2 
RETURN p.id, "Warning: Open pipe end detected"


4.3 前端展示 (Triage Queue)
逻辑: 调用后端校验 API。
效果: 在左侧“分诊列表”中，列出 "Topology Warnings"。点击列表项，画布自动聚焦到悬空的端点，并闪烁提示。
5. 开发排期建议
迭代版本
重点模块
交付物
备注
v0.1
Phase 1 (语义)
SemanticValidator.ts
必须阻止水管接墙/柱
v0.2
Phase 2 (Z轴)
ZMissingCheck (后端)
确保 Ingestion 数据能被补全
v0.3
Phase 2 (角度)
AngleSnapper (前端)
提升绘图手感
v0.4
Phase 4 (拓扑)
Cypher 校验脚本
辅助 HITL 查漏补缺
v1.0
Phase 3 (空间)
RBush 集成
属于高级特性，可延后

6. 开发者注意事项
Rule as Code: 将规则配置（JSON）视为代码的一部分，进行版本管理。
Performance: 前端校验必须在 <16ms (一帧) 内完成。复杂的几何计算请使用 Web Worker 或简化为包围盒计算。
Override: 永远给用户留一个“强制执行”的后门（例如按住 Alt 键忽略吸附），因为现实世界的改造项目总有非标情况。

OpenTruss 规则引擎参考资源清单
为了避免“造轮子”，OpenTruss 的校验逻辑（Validator）应基于成熟的行业本体和开源算法构建。
1. 语义约束 (Semantic Constraints)
解决问题：防止“水管接柱子”、“风管接水泵”等逻辑错误。
核心参考：Brick Schema (强烈推荐)
简介：Brick 是目前全球最主流的建筑元数据本体（Ontology），专门用于定义物理、逻辑和虚拟资产之间的关系。
为什么适合 OpenTruss：
它定义了标准的关系，如 feeds (供给), feeds_from (被供给), controls (控制)。
它定义了设备类型层级，明确了 HVAC_Zone 和 VAV_Box 的关系。
如何使用：
不要自己写 if (type == 'Pipe')。
而是导入 Brick 的 .ttl 文件到 Memgraph。
查询时检查：ASK { ?a brick:feeds ?b }。如果 Brick 定义里没有这种连接可能性，则报错。
资源地址：Brick Schema GitHub | 官方文档
辅助参考：RealEstateCore (REC)
简介：微软 Azure Digital Twins 背后的本体标准。
参考点：它的 Space 和 BuildingComponent 之间的拓扑定义非常严谨（如 isPartOf, isLocatedIn），适合用来校验构件的空间归属。
资源地址：RealEstateCore GitHub
2. 构造约束 (Constructability Constraints)
解决问题：防止“27°怪异弯头”、“不存在的管径”等制造错误。
核心参考：Revit Lookup Tables (查表法)
工业标准：Revit MEP 处理弯头时，不是靠算，是靠查表 (CSV Lookup)。
逻辑：
厂商会提供 .csv 文件，列出所有生产出的弯头规格（如：45°, 90°）。
算法逻辑：if (current_angle NOT IN lookup_table) -> Error/Snap。
OpenTruss 实现：
在后端维护一个简单的 JSON 配置文件 standard_fittings.json。
前端拖拽时，计算角度，寻找 standard_fittings 中最近的值进行吸附。
参考数据源：搜索 "ASHRAE Duct Fitting Database" 或国内的《通风与空调工程施工质量验收规范》(GB 50243)。
算法参考：Manhattan Routing (正交路由)
简介：电路板设计（EDA）和 MEP 管道设计共用的算法，强制路径走“曼哈顿距离”（直角转弯）。
开源库：
NetworkX (Python): 用于后端计算复杂的图路径。
Obstacle-avoidance routing: 搜索相关的 GitHub 仓库，很多基于 A* 算法变体的实现。
WebCola (JS): 前端用于生成正交连线的布局算法。
3. 物理/空间约束 (Spatial Constraints)
解决问题：防止“管道穿过天井”、“构件重叠”。
核心参考：TopologicPy
简介：专为建筑空间拓扑设计的 Python 库。
强项：它引入了 Cell (房间/空间) 和 Complex (复合体) 的概念。
场景：
用它来定义“天井”是一个 Void Cell。
当管道路径（Line）穿过 Void Cell 时，Topologic 能直接检测出 Topology.Intersects 并返回真。
资源地址：TopologicPy GitHub
基础算法：R-Tree (空间索引)
简介：处理数万个构件碰撞检测的基础设施。
库推荐：
RBush (TypeScript): 前端极其高效的 2D 矩形索引。用户拖动管道时，用 RBush 瞬间找出周围 50mm 内所有的墙和柱子，进行吸附或报错。
rtree (Python): 后端对应的库。
4. 实战：如何组合使用？(The Validator Architecture)
建议在 frontend/src/lib/logic/ 下建立一个 RuleEngine。
// 伪代码：组合规则引擎

import { RBush } from 'rbush'; // 空间索引
import { StandardAngles } from '@/config/mep_standards'; // 构造约束
import { BrickRelationships } from '@/config/brick_schema'; // 语义约束

export const validateDragAction = (source: Element, target: Element, path: Line) => {

  // 1. 语义检查 (Brick Schema)
  if (!BrickRelationships.canConnect(source.type, target.type)) {
    return { valid: false, reason: "SEMANTIC_ERROR: Invalid System Connection" };
  }

  // 2. 构造检查 (Lookup Table)
  const angle = calculateAngle(path);
  if (!StandardAngles.includes(angle)) {
     // 尝试软吸附
     const snapped = findClosestAngle(angle);
     return { valid: true, warning: "Non-standard angle", suggestSnap: snapped };
  }

  // 3. 空间检查 (RBush)
  const nearbyHazards = spatialIndex.search(path.boundingBox);
  for (const hazard of nearbyHazards) {
    if (hazard.type === 'VOID') {
       return { valid: true, warning: "SPATIAL_WARNING: Crossing Void without support" };
    }
  }

  return { valid: true };
}


