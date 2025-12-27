# 构建问题说明

## 前端 Docker 镜像构建失败

### 错误信息

```
Failed to compile: 'BatchedMesh' is not exported from 'three' (imported as 'THREE').
Import trace for requested module:
./node_modules/three-mesh-bvh/src/utils/ExtensionUtilities.js
```

### 原因分析

1. **版本不兼容问题**：
   - `three-mesh-bvh` 包需要从 `three` 导入 `BatchedMesh`
   - 当前项目使用的 `three` 版本是 `^0.158.0`
   - `BatchedMesh` 是 `three.js r159+` 版本引入的新功能
   - 因此当前版本不支持 `BatchedMesh` 导出

2. **依赖链**：
   - `Preview3D.tsx` → `@react-three/drei` → `three-mesh-bvh` → `three` (需要 BatchedMesh)

### 解决方案

#### 方案 1：升级 three.js（推荐）

```bash
cd frontend
npm install three@^0.159.0
npm install
npm run build
```

#### 方案 2：检查依赖兼容性

确认以下包的版本兼容性：
- `three`: `^0.159.0` 或更高
- `@react-three/drei`: 确保支持 three r159+
- `@react-three/fiber`: 确保支持 three r159+

#### 方案 3：移除或替换 three-mesh-bvh（如果不需要）

如果 `Preview3D` 组件不是必需的，可以考虑：
- 临时移除 `Preview3D` 组件
- 或者在开发环境中跳过构建该组件

### 当前状态

- **后端镜像**：构建成功 ✅
- **前端镜像**：构建失败 ❌（需要修复依赖版本）

### 修复步骤

1. 更新 `frontend/package.json` 中的 `three` 版本
2. 运行 `npm install` 更新依赖
3. 运行 `npm run build` 验证构建
4. 重新构建 Docker 镜像
