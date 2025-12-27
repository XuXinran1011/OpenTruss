# OpenTruss Frontend

HITL Workbench 前端应用

## 技术栈

- **Next.js 14** - React 框架（支持 SSR 和客户端渲染）
- **TypeScript** - 类型安全
- **Tailwind CSS** - 实用优先的 CSS 框架
- **D3.js** - 2D 拓扑可视化
- **Zustand** - 轻量级状态管理
- **React Query** - 数据获取和缓存

## 项目结构

```
frontend/
├── src/
│   ├── app/              # Next.js App Router
│   │   ├── page.tsx      # 首页
│   │   ├── workbench/    # 工作台页面
│   │   └── layout.tsx    # 根布局
│   ├── components/       # React 组件
│   │   ├── layout/       # 布局组件
│   │   ├── toolbar/      # 工具栏组件
│   │   ├── hierarchy/    # 层级树组件
│   │   ├── canvas/       # 画布组件
│   │   ├── panel/        # 面板组件
│   │   └── triage/       # 分诊队列组件
│   ├── stores/           # Zustand 状态管理
│   │   ├── workbench.ts  # 工作台状态
│   │   ├── hierarchy.ts  # 层级树状态
│   │   └── canvas.ts     # 画布状态
│   ├── services/         # API 服务
│   │   ├── api.ts        # API 基础封装
│   │   ├── hierarchy.ts  # 层级结构 API
│   │   └── elements.ts   # 构件 API
│   ├── hooks/            # 自定义 Hooks
│   │   ├── useTraceMode.ts
│   │   ├── useLiftMode.ts
│   │   └── useClassifyMode.ts
│   ├── utils/            # 工具函数
│   │   ├── utils.ts      # 通用工具
│   │   └── topology.ts   # 拓扑计算
│   ├── types/            # TypeScript 类型定义
│   └── lib/              # 库文件
│       ├── api/          # API 配置
│       └── utils.ts      # 工具函数
├── public/               # 静态资源
└── package.json          # 依赖配置
```

## 安装依赖

```bash
npm install
```

## 开发

```bash
npm run dev
```

应用将在 [http://localhost:3000](http://localhost:3000) 启动。

## 环境变量

创建 `.env.local` 文件：

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 构建

```bash
npm run build
npm start
```

## 核心功能

### 1. 工作台布局

IDE 式三栏布局：
- **左侧边栏**：层级树 + 分诊队列
- **中间画布**：2D 拓扑可视化
- **右侧面板**：参数修正面板
- **顶部工具栏**：模式切换、工具按钮

### 2. 三种工作模式

#### Trace Mode（拓扑修复）
- DWG 底图叠加显示
- 透明度控制
- X-Ray 模式
- 磁吸操作
- 拓扑关系更新

#### Lift Mode（Z 轴升维）
- Z-Missing 构件识别和高亮
- 批量设置 Z 轴参数
- 实时预览

#### Classify Mode（归类）
- 拖拽构件到层级树
- 批量归类
- 视觉反馈

### 3. 层级树

- 展示完整的 GB50300 层级结构
- 支持展开/折叠
- 支持搜索
- 点击节点定位到画布

### 4. 画布

- D3.js 驱动的 2D 拓扑可视化
- 缩放和平移（鼠标滚轮和拖拽）
- 构件选择和渲染
- Dot Grid 背景

### 5. 分诊队列

按优先级显示问题构件：
- 拓扑错误（红色）
- 缺失高度（紫色）
- 低置信度（黄色）

## API 集成

前端通过以下 API 服务与后端通信：

- `services/hierarchy.ts` - 层级结构查询
- `services/elements.ts` - 构件查询和操作

所有 API 调用都通过 React Query 进行缓存和状态管理。

## 状态管理

使用 Zustand 管理全局状态：

- `workbench.ts` - 工作台状态（模式、选中构件、Trace/Lift 特定状态）
- `hierarchy.ts` - 层级树状态（展开节点、选中节点、搜索关键词）
- `canvas.ts` - 画布状态（视图变换、尺寸、DWG 底图）

## 样式

使用 Tailwind CSS 实现 **Arch-Tech Precision** 设计风格：

- 主色调：Zinc（灰色系）
- 强调色：Orange 600
- 状态颜色：Red（错误）、Violet（Z-Missing）、Amber（警告）、Emerald（已验证）
- 字体：JetBrains Mono（代码/ID 显示）

## 已完成功能

1. **Canvas 渲染优化**：从 ElementDetail 获取 geometry_2d 进行实际渲染 ✓
2. **拖拽归类功能**：实现完整的拖拽交互 ✓
3. **DWG 底图加载**：实现底图上传和加载功能 ✓
4. **磁吸操作**：完善拓扑修复的磁吸逻辑（支持端点、中点、交点吸附）✓
5. **性能优化**：虚拟化、分页加载、空间索引优化 ✓
6. **Triage Queue**：问题构件分诊队列，支持按严重性排序和自动聚焦 ✓
7. **Lift Mode 3D 预览**：实时预览 3D 升维效果 ✓
8. **批量审批**：支持批量审批检验批 ✓

## 相关文档

- [UI 设计文档](../../docs/UI_DESIGN.md)
- [API 设计文档](../../docs/API.md)
- [架构文档](../../docs/ARCHITECTURE.md)

