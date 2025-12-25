#!/usr/bin/env python3
"""加载示例数据到 OpenTruss 数据库

此脚本将示例项目、层级结构和构件数据加载到 Memgraph 数据库。

使用方法:
    python scripts/load_example_data.py [--clear] [--project-file examples/sample_project.json] [--elements-file examples/sample_elements.json]

选项:
    --clear: 清除现有数据（可选）
    --project-file: 项目数据文件路径（默认: examples/sample_project.json）
    --elements-file: 构件数据文件路径（默认: examples/sample_elements.json）
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.utils.memgraph import MemgraphClient


def load_json_file(file_path: Path) -> dict:
    """加载 JSON 文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"错误: 文件 {file_path} 不存在")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"错误: JSON 文件格式错误: {e}")
        sys.exit(1)


def clear_database(client: MemgraphClient):
    """清除数据库中的所有数据"""
    print("⚠️  清除数据库中的所有数据...")
    
    queries = [
        "MATCH (n) DETACH DELETE n",
        "DROP INDEX ON :Project(id) IF EXISTS",
        "DROP INDEX ON :Building(id) IF EXISTS",
        "DROP INDEX ON :Division(id) IF EXISTS",
        "DROP INDEX ON :SubDivision(id) IF EXISTS",
        "DROP INDEX ON :Item(id) IF EXISTS",
        "DROP INDEX ON :InspectionLot(id) IF EXISTS",
        "DROP INDEX ON :Element(id) IF EXISTS",
        "DROP INDEX ON :Level(id) IF EXISTS",
    ]
    
    for query in queries:
        try:
            client.execute_query(query)
        except Exception as e:
            print(f"  警告: {query} 执行失败: {e}")
    
    print("✅ 数据库已清除")


def create_project_hierarchy(client: MemgraphClient, project_data: dict):
    """创建项目层级结构"""
    print("📁 创建项目层级结构...")
    
    # 创建项目
    project = project_data["project"]
    query = """
    CREATE (p:Project {
        id: $id,
        name: $name,
        description: $description,
        created_at: datetime(),
        updated_at: datetime()
    })
    CREATE INDEX ON :Project(id) IF NOT EXISTS
    """
    client.execute_query(query, {
        "id": project["id"],
        "name": project["name"],
        "description": project.get("description", "")
    })
    print(f"  ✅ 创建项目: {project['name']}")
    
    # 创建单体
    for building in project_data.get("buildings", []):
        query = """
        MATCH (p:Project {id: $project_id})
        CREATE (b:Building {
            id: $id,
            name: $name,
            created_at: datetime(),
            updated_at: datetime()
        })
        CREATE (p)-[:CONTAINS]->(b)
        CREATE INDEX ON :Building(id) IF NOT EXISTS
        """
        client.execute_query(query, {
            "id": building["id"],
            "name": building["name"],
            "project_id": building["project_id"]
        })
        print(f"  ✅ 创建单体: {building['name']}")
    
    # 创建楼层
    for level in project_data.get("levels", []):
        query = """
        MATCH (b:Building {id: $building_id})
        CREATE (l:Level {
            id: $id,
            name: $name,
            elevation: $elevation,
            created_at: datetime(),
            updated_at: datetime()
        })
        CREATE (b)-[:CONTAINS]->(l)
        CREATE INDEX ON :Level(id) IF NOT EXISTS
        """
        client.execute_query(query, {
            "id": level["id"],
            "name": level["name"],
            "elevation": level.get("elevation", 0.0),
            "building_id": level["building_id"]
        })
        print(f"  ✅ 创建楼层: {level['name']}")
    
    # 创建分部
    for division in project_data.get("divisions", []):
        query = """
        MATCH (b:Building {id: $building_id})
        CREATE (d:Division {
            id: $id,
            name: $name,
            description: $description,
            created_at: datetime(),
            updated_at: datetime()
        })
        CREATE (b)-[:CONTAINS]->(d)
        CREATE INDEX ON :Division(id) IF NOT EXISTS
        """
        client.execute_query(query, {
            "id": division["id"],
            "name": division["name"],
            "description": division.get("description", ""),
            "building_id": division["building_id"]
        })
        print(f"  ✅ 创建分部: {division['name']}")
    
    # 创建子分部
    for subdivision in project_data.get("subdivisions", []):
        query = """
        MATCH (d:Division {id: $division_id})
        CREATE (sd:SubDivision {
            id: $id,
            name: $name,
            description: $description,
            created_at: datetime(),
            updated_at: datetime()
        })
        CREATE (d)-[:CONTAINS]->(sd)
        CREATE INDEX ON :SubDivision(id) IF NOT EXISTS
        """
        client.execute_query(query, {
            "id": subdivision["id"],
            "name": subdivision["name"],
            "description": subdivision.get("description", ""),
            "division_id": subdivision["division_id"]
        })
        print(f"  ✅ 创建子分部: {subdivision['name']}")
    
    # 创建分项
    for item in project_data.get("items", []):
        query = """
        MATCH (sd:SubDivision {id: $subdivision_id})
        CREATE (i:Item {
            id: $id,
            name: $name,
            description: $description,
            created_at: datetime(),
            updated_at: datetime()
        })
        CREATE (sd)-[:CONTAINS]->(i)
        CREATE INDEX ON :Item(id) IF NOT EXISTS
        """
        client.execute_query(query, {
            "id": item["id"],
            "name": item["name"],
            "description": item.get("description", ""),
            "subdivision_id": item["subdivision_id"]
        })
        print(f"  ✅ 创建分项: {item['name']}")
    
    # 创建检验批
    for lot in project_data.get("inspection_lots", []):
        query = """
        MATCH (i:Item {id: $item_id}), (l:Level {id: $level_id})
        CREATE (lot:InspectionLot {
            id: $id,
            name: $name,
            status: $status,
            description: $description,
            created_at: datetime(),
            updated_at: datetime()
        })
        CREATE (i)-[:HAS_LOT]->(lot)
        CREATE (lot)-[:LOCATED_AT]->(l)
        CREATE INDEX ON :InspectionLot(id) IF NOT EXISTS
        """
        client.execute_query(query, {
            "id": lot["id"],
            "name": lot["name"],
            "status": lot.get("status", "PLANNING"),
            "description": lot.get("description", ""),
            "item_id": lot["item_id"],
            "level_id": lot["level_id"]
        })
        print(f"  ✅ 创建检验批: {lot['name']}")


def create_elements(client: MemgraphClient, elements_data: dict):
    """创建构件和连接关系"""
    print("🧱 创建构件...")
    
    for element in elements_data.get("elements", []):
        geometry = element["geometry_2d"]
        
        query = """
        MATCH (l:Level {id: $level_id})
        CREATE (e:Element {
            id: $id,
            speckle_id: $speckle_id,
            speckle_type: $speckle_type,
            geometry_2d: $geometry_2d,
            height: $height,
            base_offset: $base_offset,
            material: $material,
            level_id: $level_id,
            inspection_lot_id: $inspection_lot_id,
            status: $status,
            confidence: $confidence,
            locked: false,
            created_at: datetime(),
            updated_at: datetime()
        })
        CREATE (e)-[:LOCATED_AT]->(l)
        CREATE INDEX ON :Element(id) IF NOT EXISTS
        """
        
        params = {
            "id": element["id"],
            "speckle_id": element.get("speckle_id"),
            "speckle_type": element["speckle_type"],
            "geometry_2d": json.dumps(geometry),
            "height": element.get("height"),
            "base_offset": element.get("base_offset", 0.0),
            "material": element.get("material"),
            "level_id": element["level_id"],
            "inspection_lot_id": element.get("inspection_lot_id"),
            "status": element.get("status", "Draft"),
            "confidence": element.get("confidence")
        }
        
        client.execute_query(query, params)
        
        # 如果有关联的检验批，创建关系
        if element.get("inspection_lot_id"):
            query = """
            MATCH (e:Element {id: $element_id}), (lot:InspectionLot {id: $lot_id})
            CREATE (lot)-[:CONTAINS]->(e)
            """
            client.execute_query(query, {
                "element_id": element["id"],
                "lot_id": element["inspection_lot_id"]
            })
        
        print(f"  ✅ 创建构件: {element['id']} ({element['speckle_type']})")
    
    # 创建构件连接关系
    print("🔗 创建构件连接关系...")
    for conn in elements_data.get("connections", []):
        query = """
        MATCH (e1:Element {id: $id1}), (e2:Element {id: $id2})
        CREATE (e1)-[:CONNECTED_TO]->(e2)
        CREATE (e2)-[:CONNECTED_TO]->(e1)
        """
        client.execute_query(query, {
            "id1": conn["element_id_1"],
            "id2": conn["element_id_2"]
        })
        print(f"  ✅ 创建连接: {conn['element_id_1']} <-> {conn['element_id_2']}")


def main():
    parser = argparse.ArgumentParser(description="加载示例数据到 OpenTruss 数据库")
    parser.add_argument("--clear", action="store_true", help="清除现有数据")
    parser.add_argument(
        "--project-file",
        type=Path,
        default=project_root / "examples" / "sample_project.json",
        help="项目数据文件路径"
    )
    parser.add_argument(
        "--elements-file",
        type=Path,
        default=project_root / "examples" / "sample_elements.json",
        help="构件数据文件路径"
    )
    
    args = parser.parse_args()
    
    print("🚀 开始加载示例数据...")
    print(f"   项目文件: {args.project_file}")
    print(f"   构件文件: {args.elements_file}")
    print()
    
    # 连接数据库
    try:
        client = MemgraphClient()
        print("✅ 数据库连接成功")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        print("   请确保 Memgraph 正在运行: docker-compose up -d memgraph")
        sys.exit(1)
    
    # 清除数据（如果指定）
    if args.clear:
        clear_database(client)
        print()
    
    # 加载项目数据
    project_data = load_json_file(args.project_file)
    create_project_hierarchy(client, project_data)
    print()
    
    # 加载构件数据
    elements_data = load_json_file(args.elements_file)
    create_elements(client, elements_data)
    print()
    
    print("✅ 示例数据加载完成！")
    print()
    print("📊 验证数据:")
    print("   curl http://localhost:8000/api/v1/projects")
    print("   curl http://localhost:8000/api/v1/elements")


if __name__ == "__main__":
    main()

