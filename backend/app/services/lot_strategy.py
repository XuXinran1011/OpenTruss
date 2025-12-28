"""检验批策略服务

负责根据规则批量创建检验批并分配构件
"""

import logging
import uuid
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
from enum import Enum

from app.utils.memgraph import MemgraphClient, convert_neo4j_datetime
from app.core.exceptions import NotFoundError, ValidationError
from app.models.gb50300.nodes import InspectionLotNode
from app.models.gb50300.relationships import HAS_LOT, MANAGEMENT_CONTAINS

logger = logging.getLogger(__name__)

# 规则类型
class RuleType(str, Enum):
    """检验批划分规则类型"""
    BY_LEVEL = "BY_LEVEL"  # 按楼层划分
    BY_ZONE = "BY_ZONE"  # 按区域划分
    BY_LEVEL_AND_ZONE = "BY_LEVEL_AND_ZONE"  # 按楼层和区域组合划分


class LotStrategyService:
    """检验批策略服务"""
    
    def __init__(self, client: Optional[MemgraphClient] = None):
        """初始化服务
        
        Args:
            client: Memgraph 客户端实例（如果为 None，将创建新实例）
        """
        self.client = client or MemgraphClient()
    
    def create_lots_by_rule(
        self,
        item_id: str,
        rule_type: RuleType
    ) -> Dict[str, Any]:
        """根据规则批量创建检验批并分配构件
        
        Args:
            item_id: 分项 ID
            rule_type: 规则类型
            
        Returns:
            Dict: 包含创建的检验批列表和分配的构件数量
            
        Raises:
            ValueError: 如果 Item 不存在或规则无效
        """
        # 1. 验证 Item 是否存在
        item_query = "MATCH (item:Item {id: $item_id}) RETURN item"
        item_result = self.client.execute_query(item_query, {"item_id": item_id})
        if not item_result:
            raise NotFoundError(
                f"Item not found: {item_id}",
                {"item_id": item_id, "resource_type": "Item"}
            )
        
        item_data = dict(item_result[0]["item"])
        item_name = item_data.get("name", item_id)
        
        # 2. 获取 Building 信息（用于生成检验批名称）
        building_info = self._get_building_for_item(item_id)
        building_name = building_info.get("name", "") if building_info else ""
        
        # 3. 查询未分配的构件（inspection_lot_id IS NULL 或为空字符串）
        # 排除已经属于该 Item 下任何检验批的构件
        unassigned_elements_query = """
        MATCH (e:Element)
        WHERE (e.inspection_lot_id IS NULL OR e.inspection_lot_id = "")
        OPTIONAL MATCH (item:Item {id: $item_id})-[:HAS_LOT]->(existing_lot:InspectionLot)-[r]->(e)
        WHERE type(r) = 'MANAGEMENT_CONTAINS'
        WITH e
        WHERE existing_lot IS NULL
        RETURN e.id as element_id, e.level_id as level_id, e.zone_id as zone_id, e.speckle_type as speckle_type
        """
        
        elements = self.client.execute_query(unassigned_elements_query, {"item_id": item_id})
        
        if not elements:
            logger.info(f"No unassigned elements found for item: {item_id}")
            return {
                "lots_created": [],
                "elements_assigned": 0,
                "total_lots": 0
            }
        
        # 4. 根据规则类型分组构件
        grouped_elements = self._group_elements_by_rule(elements, rule_type)
        
        # 5. 为每个分组创建检验批
        created_lots = []
        total_elements_assigned = 0
        
        for group_key, element_ids in grouped_elements.items():
            if not element_ids:
                continue
            
            # 生成检验批信息
            lot_info = self._parse_group_key(group_key, rule_type)
            lot_name = self._generate_lot_name(
                building_name,
                lot_info,
                item_name
            )
            spatial_scope = self._generate_spatial_scope(lot_info, rule_type)
            lot_id = self._generate_lot_id(item_id, group_key)
            
            # 创建检验批节点
            lot_node = InspectionLotNode(
                id=lot_id,
                name=lot_name,
                item_id=item_id,
                spatial_scope=spatial_scope,
                status="PLANNING",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # 存储到数据库
            self._create_lot_node(lot_node)
            
            # 建立 Item -> InspectionLot 关系
            self.client.create_relationship(
                "Item", item_id,
                "InspectionLot", lot_id,
                HAS_LOT
            )
            
            # 分配构件到检验批
            assigned_count = self._assign_elements_to_lot(lot_id, element_ids)
            total_elements_assigned += assigned_count
            
            created_lots.append({
                "id": lot_id,
                "name": lot_name,
                "spatial_scope": spatial_scope,
                "element_count": assigned_count
            })
            
            logger.info(f"Created lot {lot_id} with {assigned_count} elements")
        
        return {
            "lots_created": created_lots,
            "elements_assigned": total_elements_assigned,
            "total_lots": len(created_lots)
        }
    
    def _get_building_for_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """获取 Item 所属的 Building 信息
        
        Args:
            item_id: 分项 ID
            
        Returns:
            Optional[Dict]: Building 信息，如果不存在则返回 None
        """
        query = """
        MATCH path = (item:Item {id: $item_id})-[:MANAGEMENT_CONTAINS*]->(div:Division)-[:MANAGEMENT_CONTAINS]->(bld:Building)
        WHERE ALL(r in relationships(path) WHERE type(r) = 'MANAGEMENT_CONTAINS')
        RETURN bld.id as id, bld.name as name
        LIMIT 1
        """
        result = self.client.execute_query(query, {"item_id": item_id})
        if result:
            return {"id": result[0]["id"], "name": result[0].get("name", "")}
        return None
    
    def _group_elements_by_rule(
        self,
        elements: List[Dict[str, Any]],
        rule_type: RuleType
    ) -> Dict[str, List[str]]:
        """根据规则类型分组构件
        
        Args:
            elements: 构件列表
            rule_type: 规则类型
            
        Returns:
            Dict: 分组键 -> 构件ID列表的映射
        """
        grouped = {}
        
        for elem in elements:
            element_id = elem["element_id"]
            level_id = elem.get("level_id") or ""
            zone_id = elem.get("zone_id") or ""
            
            if rule_type == RuleType.BY_LEVEL:
                group_key = f"level:{level_id}" if level_id else "level:unknown"
            elif rule_type == RuleType.BY_ZONE:
                group_key = f"zone:{zone_id}" if zone_id else "zone:unknown"
            elif rule_type == RuleType.BY_LEVEL_AND_ZONE:
                group_key = f"level:{level_id}_zone:{zone_id}" if (level_id and zone_id) else "unknown"
            else:
                group_key = "default"
            
            if group_key not in grouped:
                grouped[group_key] = []
            grouped[group_key].append(element_id)
        
        return grouped
    
    def _parse_group_key(self, group_key: str, rule_type: RuleType) -> Dict[str, str]:
        """解析分组键，提取空间信息
        
        Args:
            group_key: 分组键
            rule_type: 规则类型
            
        Returns:
            Dict: 包含 level_id, level_name, zone_id, zone_name 等信息
        """
        info = {
            "level_id": "",
            "level_name": "",
            "zone_id": "",
            "zone_name": ""
        }
        
        if rule_type == RuleType.BY_LEVEL:
            if group_key.startswith("level:"):
                level_id = group_key.replace("level:", "")
                if level_id and level_id != "unknown":
                    info["level_id"] = level_id
                    level_data = self._get_level_info(level_id)
                    if level_data:
                        info["level_name"] = level_data.get("name", level_id)
        
        elif rule_type == RuleType.BY_ZONE:
            if group_key.startswith("zone:"):
                zone_id = group_key.replace("zone:", "")
                if zone_id and zone_id != "unknown":
                    info["zone_id"] = zone_id
                    zone_data = self._get_zone_info(zone_id)
                    if zone_data:
                        info["zone_name"] = zone_data.get("name", zone_id)
                        info["level_id"] = zone_data.get("level_id", "")
        
        elif rule_type == RuleType.BY_LEVEL_AND_ZONE:
            # 解析 "level:xxx_zone:yyy" 格式
            parts = group_key.split("_zone:")
            if len(parts) == 2:
                level_id = parts[0].replace("level:", "")
                zone_id = parts[1]
                if level_id and level_id != "unknown":
                    info["level_id"] = level_id
                    level_data = self._get_level_info(level_id)
                    if level_data:
                        info["level_name"] = level_data.get("name", level_id)
                if zone_id and zone_id != "unknown":
                    info["zone_id"] = zone_id
                    zone_data = self._get_zone_info(zone_id)
                    if zone_data:
                        info["zone_name"] = zone_data.get("name", zone_id)
        
        return info
    
    def _get_level_info(self, level_id: str) -> Optional[Dict[str, Any]]:
        """获取 Level 节点信息
        
        Args:
            level_id: 楼层 ID
            
        Returns:
            Optional[Dict]: Level 信息
        """
        query = "MATCH (l:Level {id: $level_id}) RETURN l.id as id, l.name as name"
        result = self.client.execute_query(query, {"level_id": level_id})
        if result:
            return {"id": result[0]["id"], "name": result[0].get("name", level_id)}
        return None
    
    def _get_zone_info(self, zone_id: str) -> Optional[Dict[str, Any]]:
        """获取 Zone 节点信息
        
        Args:
            zone_id: 区域 ID
            
        Returns:
            Optional[Dict]: Zone 信息（包含 level_id）
        """
        query = "MATCH (z:Zone {id: $zone_id}) RETURN z.id as id, z.name as name, z.level_id as level_id"
        result = self.client.execute_query(query, {"zone_id": zone_id})
        if result:
            return {
                "id": result[0]["id"],
                "name": result[0].get("name", zone_id),
                "level_id": result[0].get("level_id", "")
            }
        return None
    
    def _generate_lot_name(
        self,
        building_name: str,
        lot_info: Dict[str, str],
        item_name: str
    ) -> str:
        """生成检验批名称
        
        格式: "{Building名称}{Level/Zone名称}{Item名称}检验批"
        例如: "1#楼F1层填充墙砌体检验批"
        
        Args:
            building_name: Building 名称
            lot_info: 空间信息（level_name, zone_name 等）
            item_name: Item 名称
            
        Returns:
            str: 检验批名称
        """
        parts = []
        
        if building_name:
            parts.append(building_name)
        
        if lot_info.get("level_name"):
            parts.append(lot_info["level_name"] + "层")
        elif lot_info.get("zone_name"):
            parts.append(lot_info["zone_name"])
            # 如果有 level_name，也应该包含
            if lot_info.get("level_name"):
                parts.insert(-1, lot_info["level_name"] + "层")
        
        if item_name:
            parts.append(item_name)
        
        parts.append("检验批")
        
        return "".join(parts)
    
    def _generate_spatial_scope(
        self,
        lot_info: Dict[str, str],
        rule_type: RuleType
    ) -> str:
        """生成空间范围描述
        
        Args:
            lot_info: 空间信息
            rule_type: 规则类型
            
        Returns:
            str: 空间范围描述（如："Level:F1" 或 "Level:F1,Zone:A区"）
        """
        parts = []
        
        if lot_info.get("level_id"):
            level_name = lot_info.get("level_name", lot_info["level_id"])
            parts.append(f"Level:{level_name}")
        
        if lot_info.get("zone_id"):
            zone_name = lot_info.get("zone_name", lot_info["zone_id"])
            parts.append(f"Zone:{zone_name}")
        
        return ",".join(parts) if parts else "Unknown"
    
    def _generate_lot_id(self, item_id: str, group_key: str) -> str:
        """生成检验批 ID
        
        Args:
            item_id: Item ID
            group_key: 分组键
            
        Returns:
            str: 检验批 ID
        """
        # 使用 item_id 和 group_key 生成唯一 ID
        # 格式: lot_{item_id}_{hash}
        import hashlib
        hash_obj = hashlib.md5(group_key.encode())
        hash_str = hash_obj.hexdigest()[:8]
        return f"lot_{item_id}_{hash_str}"
    
    def _create_lot_node(self, lot_node: InspectionLotNode) -> None:
        """创建检验批节点
        
        Args:
            lot_node: 检验批节点模型
        """
        props = lot_node.model_dump()
        # 转换 datetime 为字符串（Cypher 兼容格式）
        if "created_at" in props and isinstance(props["created_at"], datetime):
            props["created_at"] = props["created_at"].isoformat()
        if "updated_at" in props and isinstance(props["updated_at"], datetime):
            props["updated_at"] = props["updated_at"].isoformat()
        
        self.client.create_node("InspectionLot", props, return_id=False)
    
    def _assign_elements_to_lot(
        self,
        lot_id: str,
        element_ids: List[str]
    ) -> int:
        """将构件分配到检验批
        
        Args:
            lot_id: 检验批 ID
            element_ids: 构件 ID 列表
            
        Returns:
            int: 成功分配的构件数量
        """
        if not element_ids:
            return 0
        
        assigned_count = 0
        
        for element_id in element_ids:
            try:
                # 更新 Element 的 inspection_lot_id 属性
                update_query = """
                MATCH (e:Element {id: $element_id})
                SET e.inspection_lot_id = $lot_id, e.updated_at = datetime()
                RETURN e.id as id
                """
                result = self.client.execute_query(update_query, {
                    "element_id": element_id,
                    "lot_id": lot_id
                })
                
                if result:
                    # 建立关系
                    self.client.create_relationship(
                        "InspectionLot", lot_id,
                        "Element", element_id,
                        MANAGEMENT_CONTAINS
                    )
                    assigned_count += 1
            except Exception as e:
                logger.warning(f"Failed to assign element {element_id} to lot {lot_id}: {e}")
        
        return assigned_count
    
    def assign_elements_to_lot(
        self,
        lot_id: str,
        element_ids: List[str]
    ) -> int:
        """手动分配构件到检验批（公共方法）
        
        Args:
            lot_id: 检验批 ID
            element_ids: 构件 ID 列表
            
        Returns:
            int: 成功分配的构件数量
        """
        return self._assign_elements_to_lot(lot_id, element_ids)
    
    def remove_elements_from_lot(
        self,
        lot_id: str,
        element_ids: List[str]
    ) -> int:
        """从检验批移除构件
        
        Args:
            lot_id: 检验批 ID
            element_ids: 构件 ID 列表
            
        Returns:
            int: 成功移除的构件数量
        """
        if not element_ids:
            return 0
        
        removed_count = 0
        
        for element_id in element_ids:
            try:
                # 删除关系
                delete_rel_query = """
                MATCH (lot:InspectionLot {id: $lot_id})-[r]->(e:Element {id: $element_id})
                WHERE type(r) = 'MANAGEMENT_CONTAINS'
                DELETE r
                RETURN e.id as id
                """
                result = self.client.execute_query(delete_rel_query, {
                    "lot_id": lot_id,
                    "element_id": element_id
                })
                
                if result:
                    # 清空 Element 的 inspection_lot_id
                    update_query = """
                    MATCH (e:Element {id: $element_id})
                    SET e.inspection_lot_id = NULL, e.updated_at = datetime()
                    RETURN e.id as id
                    """
                    self.client.execute_query(update_query, {"element_id": element_id})
                    removed_count += 1
            except Exception as e:
                logger.warning(f"Failed to remove element {element_id} from lot {lot_id}: {e}")
        
        return removed_count

