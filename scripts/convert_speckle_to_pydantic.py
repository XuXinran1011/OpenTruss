#!/usr/bin/env python3
"""
脚本：将 Speckle C# 类转换为 OpenTruss Pydantic 模型

功能：
- 解析 C# 类定义
- 提取属性和类型信息
- 转换为 Pydantic BaseModel
- 适配 OpenTruss 特定的数据模型需求
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class PropertyInfo:
    """属性信息"""
    name: str
    csharp_type: str
    is_optional: bool
    docstring: Optional[str] = None


@dataclass
class ClassInfo:
    """类信息"""
    name: str
    base_classes: List[str]
    properties: List[PropertyInfo]
    file_path: Path


# C# 类型到 Python/Pydantic 类型映射
TYPE_MAPPING = {
    # 基本类型
    "double": "float",
    "double?": "Optional[float]",
    "int": "int",
    "int?": "Optional[int]",
    "string": "str",
    "string?": "Optional[str]",
    "bool": "bool",
    "bool?": "Optional[bool]",
    
    # Speckle 特定类型 - 需要转换为 OpenTruss 类型
    "ICurve": "Geometry2D",  # 转换为 OpenTruss 的 Geometry2D
    "Level": "Optional[str]",  # 转换为 level_id (字符串)
    "Level?": "Optional[str]",
    
    # 集合类型
    "List<Base>": "List[Dict[str, Any]]",  # elements 字段
    "List<Base>?": "Optional[List[Dict[str, Any]]]",
    "IReadOnlyList<Base>": "List[Dict[str, Any]]",  # displayValue
    "List<ICurve>": "List[Geometry2D]",  # voids
    "List<ICurve>?": "Optional[List[Geometry2D]]",
    
    # Point 类型
    "Point": "List[float]",  # 转换为 [x, y, z] 列表
    "Point?": "Optional[List[float]]",
    
    # 其他类型（需要进一步处理）
    "Mesh": "Dict[str, Any]",
    "IReadOnlyList<Mesh>": "List[Dict[str, Any]]",
    "IReadOnlyList<Mesh>?": "Optional[List[Dict[str, Any]]]",
}


def parse_csharp_file(file_path: Path) -> Optional[ClassInfo]:
    """解析 C# 文件，提取类信息"""
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"✗ 读取文件失败 {file_path.name}: {e}")
        return None
    
    # 提取类名
    class_match = re.search(r'public\s+class\s+(\w+)\s*:', content)
    if not class_match:
        return None
    
    class_name = class_match.group(1)
    
    # 提取基类
    base_classes_match = re.search(r'public\s+class\s+\w+\s*:\s*([^{]+)', content)
    base_classes = []
    if base_classes_match:
        base_part = base_classes_match.group(1).strip()
        # 分割基类（可能有多个，用逗号分隔）
        base_classes = [b.strip().split('<')[0] for b in base_part.split(',')]
    
    # 提取属性
    properties = []
    
    # 匹配属性模式：public Type PropertyName { get; set; }
    property_pattern = r'public\s+([\w<>?,\s]+?)\s+(\w+)\s*\{\s*get;\s*set;\s*\}'
    for match in re.finditer(property_pattern, content):
        csharp_type = match.group(1).strip()
        prop_name = match.group(2).strip()
        
        # 处理可选类型（包含 ?）
        is_optional = '?' in csharp_type
        csharp_type = csharp_type.replace('?', '').strip()
        
        # 处理泛型
        if '<' in csharp_type:
            # 提取泛型类型
            generic_match = re.match(r'(\w+)<(.+)>', csharp_type)
            if generic_match:
                generic_base = generic_match.group(1)
                generic_param = generic_match.group(2).strip()
                
                # 构建完整的泛型类型名
                full_type = f"{generic_base}<{generic_param}>"
                csharp_type = full_type
        
        properties.append(PropertyInfo(
            name=prop_name,
            csharp_type=csharp_type,
            is_optional=is_optional
        ))
    
    return ClassInfo(
        name=class_name,
        base_classes=base_classes,
        properties=properties,
        file_path=file_path
    )


def convert_camel_to_snake(name: str) -> str:
    """将 camelCase 转换为 snake_case"""
    import re
    # 处理连续大写字母（如 basePoint -> base_point, topLevel -> top_level）
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def map_csharp_type_to_python(csharp_type: str, is_optional: bool) -> str:
    """将 C# 类型映射到 Python/Pydantic 类型"""
    # 先检查是否有直接映射
    optional_type = f"{csharp_type}?"
    if optional_type in TYPE_MAPPING:
        return TYPE_MAPPING[optional_type]
    if csharp_type in TYPE_MAPPING:
        python_type = TYPE_MAPPING[csharp_type]
        if is_optional and not python_type.startswith("Optional"):
            return f"Optional[{python_type}]"
        return python_type
    
    # 默认处理：转换为字符串或 Any
    if is_optional:
        return "Optional[Any]"
    return "Any"


def generate_pydantic_model(class_info: ClassInfo, category: str) -> str:
    """生成 Pydantic 模型代码（不包含导入语句，导入会在文件级别统一添加）"""
    lines = []
    
    # 类文档字符串
    lines.append(f'class {class_info.name}(SpeckleBuiltElementBase):')
    lines.append(f'    """Speckle {class_info.name} element')
    lines.append("    ")
    lines.append(f"    原文件: {class_info.file_path.name}")
    lines.append('    """')
    lines.append("")
    
    # 属性定义（跳过一些不需要的字段）
    skip_props = {"displayValue", "elements"}  # 这些字段已在基类中处理或不需要
    
    relevant_props = [p for p in class_info.properties if p.name not in skip_props or p.name in ["voids"]]
    
    if not relevant_props:
        lines.append("    pass  # 无额外属性定义")
    else:
        for prop in relevant_props:
            python_type = map_csharp_type_to_python(prop.csharp_type, prop.is_optional)
            
            # 生成字段定义
            field_def = f"    {prop.name}: {python_type}"
            
            # 特殊字段处理
            if prop.name in ["baseLine", "baseCurve"] and prop.csharp_type == "ICurve":
                # baseLine 和 baseCurve 都转换为 geometry_2d（优先使用 baseCurve）
                alias = "baseCurve" if prop.name == "baseCurve" else "baseLine"
                field_def = f"    geometry_2d: Geometry2D = Field(..., alias='{alias}', description='2D geometry (converted from ICurve {alias})')"
            elif prop.name == "outline" and prop.csharp_type == "ICurve":
                field_def = f"    geometry_2d: Geometry2D = Field(..., alias='outline', description='2D geometry outline')"
            elif prop.name == "level" and ("Level" in prop.csharp_type or prop.csharp_type == "Level"):
                # 转换为 level_id
                field_def = f"    level_id: Optional[str] = Field(None, alias='level', description='Level ID (converted from Level object)')"
            elif prop.name == "topLevel" and ("Level" in prop.csharp_type or prop.csharp_type == "Level"):
                # 转换为 top_level_id
                field_def = f"    top_level: Optional[str] = Field(None, alias='topLevel', description='Top level ID (converted from Level object)')"
            elif prop.name == "basePoint" and prop.csharp_type == "Point":
                # Point 转换为坐标列表
                field_def = f"    base_point: Optional[List[float]] = Field(None, alias='basePoint', description='基准点坐标 [x, y, z]')"
            elif prop.name == "voids" and ("ICurve" in prop.csharp_type or "List<ICurve>" in prop.csharp_type):
                # voids 转换为 Geometry2D 列表
                field_def = f"    voids: Optional[List[Geometry2D]] = Field(None, default_factory=list, description='开洞轮廓列表')"
            elif prop.name == "displayValue":
                # displayValue 字段在 OpenTruss 中通常不需要，跳过
                continue
            elif prop.name == "elements":
                # elements 字段保留但设为可选
                field_def = f"    elements: Optional[List[Dict[str, Any]]] = Field(None, description='嵌套元素')"
            elif prop.name in ["zone", "revitZone"]:
                # Zone 对象转换为字符串或保持为 Dict
                field_def = f"    {prop.name}: {python_type} = Field(None, description='Zone information (converted to dict or string)')"
            else:
                # 默认字段 - 处理字段名转换（camelCase to snake_case）
                snake_case_name = convert_camel_to_snake(prop.name)
                if snake_case_name != prop.name:
                    # 使用别名保持向后兼容
                    field_def = f"    {snake_case_name}: {python_type} = Field(None, alias='{prop.name}', description='{prop.name}')" if prop.is_optional else f"    {snake_case_name}: {python_type} = Field(..., alias='{prop.name}', description='{prop.name}')"
                else:
                    field_def = f"    {prop.name}: {python_type}"
                    if prop.is_optional:
                        field_def += " = None"
            
            lines.append(field_def)
    
    lines.append("")
    return "\n".join(lines)


def categorize_class(class_name: str) -> str:
    """将类分类到对应的模块"""
    architectural = ["Wall", "Floor", "Ceiling", "Roof", "Column"]
    structural = ["Beam", "Brace", "Structure", "Rebar"]
    mep = ["Duct", "Pipe", "CableTray", "Conduit", "Wire"]
    spatial = ["Level", "Room", "Space", "Zone", "Area"]
    
    if class_name in architectural:
        return "architectural"
    elif class_name in structural:
        return "structural"
    elif class_name in mep:
        return "mep"
    elif class_name in spatial:
        return "spatial"
    else:
        return "other"


def main():
    """主函数"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # 输入目录（Speckle 文件）- 优先使用本地目录
    local_dir = project_root / "SpeckleBuiltElements"
    temp_dir = project_root / "temp" / "speckle_built_elements"
    
    # 优先使用本地目录，如果不存在则使用临时目录
    if local_dir.exists() and any(local_dir.glob("*.cs")):
        input_dir = local_dir
        print(f"使用本地目录: {input_dir}")
    elif temp_dir.exists():
        input_dir = temp_dir
        print(f"使用临时目录: {input_dir}")
    else:
        print(f"✗ 输入目录不存在:")
        print(f"  本地目录: {local_dir}")
        print(f"  临时目录: {temp_dir}")
        print("\n请选择以下方式之一:")
        print("1. 将 Speckle .cs 文件放在 ./SpeckleBuiltElements/ 目录中")
        print("2. 运行 fetch_speckle_built_elements.py 从 GitHub 下载")
        return
    
    # 输出目录（Pydantic 模型）
    output_dir = project_root / "backend" / "app" / "models" / "speckle"
    
    print(f"开始转换 Speckle 类为 Pydantic 模型...")
    print(f"输入目录: {input_dir}")
    print(f"输出目录: {output_dir}")
    print(f"{'='*60}\n")
    
    # 分类存储
    classes_by_category: Dict[str, List[ClassInfo]] = {
        "architectural": [],
        "structural": [],
        "mep": [],
        "spatial": [],
        "other": []
    }
    
    # 解析所有文件
    cs_files = list(input_dir.glob("*.cs"))
    for cs_file in cs_files:
        class_info = parse_csharp_file(cs_file)
        if class_info:
            category = categorize_class(class_info.name)
            classes_by_category[category].append(class_info)
            print(f"✓ 解析: {class_info.name} -> {category}")
    
    # 生成模型文件
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for category, classes in classes_by_category.items():
        if not classes:
            continue
        
        output_file = output_dir / f"{category}.py"
        with open(output_file, 'w', encoding='utf-8') as f:
            # 写入文件头和导入语句
            f.write(f'"""Speckle {category.title()} BuiltElements (自动生成)\n\n')
            f.write('本文件包含的类:\n')
            for cls in classes:
                f.write(f'  - {cls.name}\n')
            f.write('"""\n\n')
            f.write('from typing import Optional, List, Dict, Any, Literal\n')
            f.write('from pydantic import BaseModel, Field\n')
            f.write('from .base import SpeckleBuiltElementBase, Geometry2D\n')
            f.write('\n\n')
            
            # 写入每个类的模型
            for class_info in classes:
                model_code = generate_pydantic_model(class_info, category)
                f.write(model_code)
                f.write("\n\n")
        
        print(f"✓ 生成: {output_file.name} ({len(classes)} 个类)")
    
    print(f"\n{'='*60}")
    print(f"转换完成！")
    print(f"下一步: 创建 base.py 和 __init__.py 文件")


if __name__ == "__main__":
    main()

