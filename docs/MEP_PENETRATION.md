# 穿墙/穿楼板节点生成文档

## 概述

本文档说明MEP管线穿过墙体、楼板时所需生成的节点类型和生成规则。这些节点在完成管线综合排布确认通过审批时生成。

## 生成时机

**生成时机**：完成管线综合排布，MEP专业负责人点击"确认完成管线综合排布"，系统通过审批后，自动生成所有穿墙/穿楼板节点。

**生成原则**：
- 在路径最终确定后再生成节点，避免重复生成
- 确保所有碰撞已解决，路径不再变更
- 节点生成是审批流程的一部分

## 节点类型

### 1. 防火封堵节点

#### 适用场景

- **有防火要求的楼板**：MEP管线穿过有防火等级的楼板
- **有防火要求的内墙**：MEP管线穿过有防火等级的内墙

#### 生成规则

- **防火等级匹配**：节点防火等级必须与楼板/内墙的防火等级相同
- **节点类型**：根据MEP系统类型和规格选择合适的防火封堵材料
- **节点位置**：在管线与楼板/墙体的相交位置生成节点

#### 数据结构

```python
class FireSealNode:
    id: str
    element_id: str  # 关联的MEP元素ID
    wall_or_floor_id: str  # 穿过的墙体或楼板ID
    fire_rating: str  # 防火等级（如：A级、B级）
    position: List[float]  # 节点位置 [x, y, z]
    material_type: str  # 封堵材料类型
```

### 2. 防水套管节点

#### 适用场景

- **有防水要求的楼板**：MEP管线穿过有防水要求的楼板
- **有防水要求的墙体**：MEP管线穿过有防水要求的墙体

#### 生成规则

根据MEP系统类型，使用不同的默认套管类型：

- **重力流管道**：默认刚性防水套管（用户可手动改为柔性）
- **有压管道**：默认刚性防水套管（用户可手动改为柔性）
- **风管**：穿楼板时设置挡水台（见下文）
- **电缆桥架**：穿楼板时设置挡水台（见下文）

#### 刚性 vs 柔性防水套管

- **刚性防水套管**：
  - 适用于一般情况
  - 成本较低
  - 施工简单

- **柔性防水套管**：
  - 适用于有振动或温度变化的情况
  - 成本较高
  - 施工较复杂
  - 用户可在审批前手动修改

#### 数据结构

```python
class WaterproofSleeveNode:
    id: str
    element_id: str  # 关联的MEP元素ID
    wall_or_floor_id: str  # 穿过的墙体或楼板ID
    sleeve_type: Literal["rigid", "flexible"]  # 刚性或柔性
    position: List[float]  # 节点位置 [x, y, z]
    diameter_or_size: Dict[str, float]  # 套管尺寸
```

### 3. 挡水台节点

#### 适用场景

- **风管穿楼板**：风管穿过有防水要求的楼板时
- **电缆桥架穿楼板**：电缆桥架穿过有防水要求的楼板时

#### 生成规则

- **高度要求**：挡水台高度根据防水等级确定（通常100-200mm）
- **位置**：在楼板表面，围绕管线开口设置
- **材料**：通常使用与楼板相同的材料（混凝土等）

#### 数据结构

```python
class WaterBarrierNode:
    id: str
    element_id: str  # 关联的MEP元素ID
    floor_id: str  # 穿过的楼板ID
    height: float  # 挡水台高度（米）
    position: List[float]  # 节点位置 [x, y, z]
    shape: Geometry2D  # 挡水台轮廓（通常是圆形或矩形）
```

### 4. 一般穿墙套管节点

#### 适用场景

- **无防火/防水要求的墙**：MEP管线穿过无防火和防水要求的墙体

#### 生成规则

- **套管类型**：使用一般穿墙套管（非防水、非防火）
- **套管尺寸**：根据管线外径（包括保温层等）确定
- **预留空间**：套管内径应大于管线外径，预留安装和维护空间

#### 数据结构

```python
class GeneralWallSleeveNode:
    id: str
    element_id: str  # 关联的MEP元素ID
    wall_id: str  # 穿过的墙体ID
    position: List[float]  # 节点位置 [x, y, z]
    inner_diameter: float  # 套管内径（米）
    outer_diameter: float  # 套管外径（米）
    material: str  # 套管材料（如：钢套管、塑料套管）
```

### 5. 一般穿楼板套管节点

#### 适用场景

- **无防火/防水要求的楼板**：MEP管线穿过无防火和防水要求的楼板

#### 生成规则

- **套管类型**：使用一般穿楼板套管（非防水、非防火）
- **套管尺寸**：根据管线外径（包括保温层等）确定
- **预留空间**：套管内径应大于管线外径，预留安装和维护空间

#### 数据结构

```python
class GeneralFloorSleeveNode:
    id: str
    element_id: str  # 关联的MEP元素ID
    floor_id: str  # 穿过的楼板ID
    position: List[float]  # 节点位置 [x, y, z]
    inner_diameter: float  # 套管内径（米）
    outer_diameter: float  # 套管外径（米）
    material: str  # 套管材料（如：钢套管、塑料套管）
```

## 节点生成流程

### 1. 检测穿墙/穿楼板位置

在完成管线综合排布后，系统检测所有MEP管线与墙体、楼板的相交位置：

1. **几何计算**：计算管线3D路径与墙体/楼板3D几何的相交点
2. **记录位置**：记录所有相交位置和相关信息
   - MEP元素ID
   - 墙体/楼板ID
   - 相交点坐标
   - 墙体/楼板的属性（防火等级、防水要求等）

### 2. 确定节点类型

根据墙体/楼板的属性确定节点类型：

1. **有防火要求** → 生成防火封堵节点
2. **有防水要求**：
   - 管道 → 生成防水套管节点（刚性/柔性）
   - 风管/桥架 → 生成挡水台节点
3. **无防火/防水要求**：
   - 穿墙 → 生成一般穿墙套管节点
   - 穿楼板 → 生成一般穿楼板套管节点

### 3. 计算节点参数

根据MEP元素和墙体/楼板的属性计算节点参数：

- **套管尺寸**：根据管线外径（包括保温层等）和预留空间计算
- **防火等级**：与墙体/楼板的防火等级匹配
- **位置**：精确的相交点坐标

### 4. 生成节点

在数据库中创建节点记录：

- 创建节点节点（PenetrationNode或类似的节点类型）
- 建立MEP元素与节点的关系
- 建立墙体/楼板与节点的关系
- 存储节点参数

### 5. 审批流程

节点生成后，进入审批流程：
- MEP专业负责人确认节点参数
- 如需修改（如刚性改为柔性），可以手动调整
- 审批通过后，节点正式生效

## 节点数据模型

### 通用节点基类

```python
class PenetrationNode(BaseModel):
    """穿墙/穿楼板节点基类"""
    id: str
    element_id: str  # 关联的MEP元素ID
    wall_or_floor_id: str  # 穿过的墙体或楼板ID
    position: List[float]  # 节点位置 [x, y, z]
    node_type: Literal[
        "fire_seal",
        "waterproof_sleeve",
        "water_barrier",
        "general_wall_sleeve",
        "general_floor_sleeve"
    ]
    created_at: datetime
    updated_at: datetime
```

### 节点关系

在图数据库中，节点关系如下：

```
(Element) -[:HAS_PENETRATION]-> (PenetrationNode)
(Wall) -[:HAS_PENETRATION]-> (PenetrationNode)
(Floor) -[:HAS_PENETRATION]-> (PenetrationNode)
```

## 配置参数

### 套管尺寸计算

- **预留空间**：套管内径 = 管线外径 + 预留空间（通常10-20mm）
- **套管壁厚**：根据规范和材料确定
- **套管长度**：根据墙体/楼板厚度确定

### 挡水台尺寸

- **高度**：根据防水等级确定（通常100-200mm）
- **轮廓**：根据管线截面形状确定（圆形或矩形）
- **宽度**：根据管线尺寸和规范确定

配置可在 `backend/app/config/rules/mep_routing_config.json` 中定义。

## 相关文档

- [MEP_ROUTING_DETAILED.md](./MEP_ROUTING_DETAILED.md) - MEP路由规划详细规格
- [MEP_COORDINATION.md](./MEP_COORDINATION.md) - 管线综合排布规格
- [API.md](./API.md) - API接口文档（节点生成API）
- [RULE_ENGINE.md](./RULE_ENGINE.md) - 规则引擎文档

