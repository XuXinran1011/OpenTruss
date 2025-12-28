"""
演示数据生成脚本

用于在Agent AI读图之前创建完整的演示数据集，包括：
- 完整的GB50300层级结构（项目-单体-分部-子分部-分项-检验批）
- 构件（Element）并关联到检验批
- 完整的几何信息（geometry_2d, height, base_offset）

使用方法:
    python -m scripts.create_demo_data

详细使用说明请参考: scripts/README_DEMO_DATA.md
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
from datetime import datetime
from typing import List, Dict, Any

from app.utils.memgraph import MemgraphClient
from app.services.schema import initialize_schema
from app.models.gb50300.nodes import (
    ProjectNode, BuildingNode, DivisionNode, SubDivisionNode,
    ItemNode, InspectionLotNode, LevelNode
)
from app.models.gb50300.element import ElementNode
from app.models.gb50300.relationships import (
    PHYSICALLY_CONTAINS, MANAGEMENT_CONTAINS, HAS_LOT, LOCATED_AT
)
from app.models.speckle.base import Geometry2D

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DemoDataGenerator:
    """演示数据生成器"""
    
    def __init__(self, client: MemgraphClient = None):
        self.client = client or MemgraphClient()
    
    def create_demo_project(self) -> Dict[str, Any]:
        """创建完整的演示项目数据"""
        logger.info("开始创建演示数据...")
        
        # 1. 初始化Schema
        initialize_schema(self.client, create_default_users=True)
        
        # 2. 创建项目
        project_id = "demo_project"
        project = ProjectNode(
            id=project_id,
            name="演示项目",
            description="用于Agent AI读图演示的测试项目"
        )
        self._create_node_if_not_exists("Project", project.model_dump(exclude_none=True))
        logger.info(f"✓ 创建项目: {project_id}")
        
        # 3. 创建单体
        building_id = "demo_building_001"
        building = BuildingNode(
            id=building_id,
            name="1#楼",
            project_id=project_id
        )
        self._create_node_if_not_exists("Building", building.model_dump(exclude_none=True))
        self._create_relationship_if_not_exists(
            "Project", project_id,
            "Building", building_id,
            PHYSICALLY_CONTAINS
        )
        logger.info(f"✓ 创建单体: {building_id}")
        
        # 4. 创建楼层
        level_id = "demo_level_f1"
        level = LevelNode(
            id=level_id,
            name="F1",
            building_id=building_id,
            elevation=0.0
        )
        self._create_node_if_not_exists("Level", level.model_dump(exclude_none=True))
        self._create_relationship_if_not_exists(
            "Building", building_id,
            "Level", level_id,
            PHYSICALLY_CONTAINS
        )
        logger.info(f"✓ 创建楼层: {level_id}")
        
        # 5. 创建分部
        division_id = "demo_division_001"
        division = DivisionNode(
            id=division_id,
            name="主体结构",
            building_id=building_id,
            description="主体结构分部"
        )
        self._create_node_if_not_exists("Division", division.model_dump(exclude_none=True))
        self._create_relationship_if_not_exists(
            "Building", building_id,
            "Division", division_id,
            MANAGEMENT_CONTAINS
        )
        logger.info(f"✓ 创建分部: {division_id}")
        
        # 6. 创建子分部
        subdivision_id = "demo_subdivision_001"
        subdivision = SubDivisionNode(
            id=subdivision_id,
            name="砌体结构",
            division_id=division_id,
            description="砌体结构子分部"
        )
        self._create_node_if_not_exists("SubDivision", subdivision.model_dump(exclude_none=True))
        self._create_relationship_if_not_exists(
            "Division", division_id,
            "SubDivision", subdivision_id,
            MANAGEMENT_CONTAINS
        )
        logger.info(f"✓ 创建子分部: {subdivision_id}")
        
        # 7. 创建分项
        item_id = "demo_item_001"
        item = ItemNode(
            id=item_id,
            name="填充墙砌体",
            subdivision_id=subdivision_id,
            description="填充墙砌体分项"
        )
        self._create_node_if_not_exists("Item", item.model_dump(exclude_none=True))
        self._create_relationship_if_not_exists(
            "SubDivision", subdivision_id,
            "Item", item_id,
            MANAGEMENT_CONTAINS
        )
        logger.info(f"✓ 创建分项: {item_id}")
        
        # 8. 创建检验批
        lot_id = "demo_lot_001"
        lot = InspectionLotNode(
            id=lot_id,
            name="1#楼F1层填充墙砌体检验批",
            item_id=item_id,
            spatial_scope=f"Level:{level_id}",
            status="PLANNING"
        )
        self._create_node_if_not_exists("InspectionLot", lot.model_dump(exclude_none=True))
        self._create_relationship_if_not_exists(
            "Item", item_id,
            "InspectionLot", lot_id,
            HAS_LOT
        )
        logger.info(f"✓ 创建检验批: {lot_id}")
        
        # 9. 创建构件并关联到检验批
        elements = self._create_demo_elements(lot_id, level_id, count=5)
        logger.info(f"✓ 创建 {len(elements)} 个构件")
        
        return {
            "project_id": project_id,
            "building_id": building_id,
            "level_id": level_id,
            "division_id": division_id,
            "subdivision_id": subdivision_id,
            "item_id": item_id,
            "lot_id": lot_id,
            "element_ids": elements
        }
    
    def _create_demo_elements(self, lot_id: str, level_id: str, count: int = 5) -> List[str]:
        """创建演示构件"""
        element_ids = []
        
        # 创建几个不同类型的构件
        element_configs = [
            {"type": "Wall", "coords": [[0, 0], [10, 0], [10, 0.2], [0, 0.2], [0, 0]], "height": 3.0},
            {"type": "Wall", "coords": [[10, 0], [20, 0], [20, 0.2], [10, 0.2], [10, 0]], "height": 3.0},
            {"type": "Column", "coords": [[5, 5], [5.5, 5], [5.5, 5.5], [5, 5.5], [5, 5]], "height": 3.0},
            {"type": "Floor", "coords": [[0, 0], [20, 0], [20, 10], [0, 10], [0, 0]], "height": 0.2},
            {"type": "Wall", "coords": [[0, 10], [20, 10], [20, 10.2], [0, 10.2], [0, 10]], "height": 3.0},
        ]
        
        for i, config in enumerate(element_configs[:count]):
            element_id = f"demo_element_{i+1:03d}"
            element = ElementNode(
                id=element_id,
                speckle_type=config["type"],
                geometry_2d=Geometry2D(
                    type="Polyline",
                    coordinates=config["coords"],
                    closed=True
                ),
                height=config["height"],
                base_offset=0.0,
                material="concrete",
                level_id=level_id,
                inspection_lot_id=lot_id,
                status="Draft"
            )
            
            # 转换geometry_2d为字典
            element_dict = element.model_dump(exclude_none=True)
            if isinstance(element_dict["geometry_2d"], Geometry2D):
                element_dict["geometry_2d"] = element_dict["geometry_2d"].model_dump()
            
            self._create_node_if_not_exists("Element", element_dict)
            self._create_relationship_if_not_exists(
                "InspectionLot", lot_id,
                "Element", element_id,
                MANAGEMENT_CONTAINS
            )
            self._create_relationship_if_not_exists(
                "Element", element_id,
                "Level", level_id,
                LOCATED_AT
            )
            element_ids.append(element_id)
        
        return element_ids
    
    def _create_node_if_not_exists(self, label: str, properties: Dict[str, Any]) -> bool:
        """如果节点不存在则创建"""
        node_id = properties.get("id")
        if not node_id:
            return False
        
        # 检查节点是否存在
        query = f"MATCH (n:{label} {{id: $id}}) RETURN n.id as id"
        result = self.client.execute_query(query, {"id": node_id})
        
        if not result:
            self.client.create_node(label, properties)
            return True
        return False
    
    def _create_relationship_if_not_exists(
        self,
        start_label: str, start_id: str,
        end_label: str, end_id: str,
        rel_type: str
    ) -> bool:
        """如果关系不存在则创建"""
        # 确保 rel_type 是字符串值（如果是枚举，获取其值）
        if hasattr(rel_type, 'value'):
            rel_type_str = rel_type.value
        elif isinstance(rel_type, str):
            rel_type_str = rel_type
        else:
            rel_type_str = str(rel_type)
        
        # 检查关系是否存在
        # 注意：在MATCH中，关系类型不能使用表达式，必须直接使用字符串
        query = f"""
        MATCH (a:{start_label} {{id: $start_id}})
        MATCH (b:{end_label} {{id: $end_id}})
        MATCH (a)-[r:{rel_type_str}]->(b)
        RETURN r
        """
        result = self.client.execute_query(query, {"start_id": start_id, "end_id": end_id})
        
        if not result:
            self.client.create_relationship(
                start_label, start_id,
                end_label, end_id,
                rel_type_str
            )
            return True
        return False


def main():
    """主函数"""
    try:
        generator = DemoDataGenerator()
        result = generator.create_demo_project()
        
        logger.info("\n" + "="*60)
        logger.info("演示数据创建完成！")
        logger.info("="*60)
        logger.info(f"项目ID: {result['project_id']}")
        logger.info(f"单体ID: {result['building_id']}")
        logger.info(f"楼层ID: {result['level_id']}")
        logger.info(f"检验批ID: {result['lot_id']}")
        logger.info(f"构件数量: {len(result['element_ids'])}")
        logger.info(f"构件IDs: {', '.join(result['element_ids'])}")
        logger.info("="*60)
        logger.info("\n现在可以使用这些数据进行演示和测试了！")
        
    except Exception as e:
        logger.error(f"创建演示数据失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

