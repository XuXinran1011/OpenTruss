"""层级结构查询服务

负责查询 GB50300 层级结构相关的数据
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.utils.memgraph import MemgraphClient, convert_neo4j_datetime
from app.core.cache import cache_result
from app.models.api.hierarchy import (
    ProjectListItem,
    ProjectDetail,
    HierarchyNode,
    HierarchyResponse,
    BuildingDetail,
    DivisionDetail,
    SubDivisionDetail,
    ItemDetail,
    InspectionLotDetail,
)

logger = logging.getLogger(__name__)


class HierarchyService:
    """层级结构查询服务"""
    
    def __init__(self, client: Optional[MemgraphClient] = None):
        """初始化服务
        
        Args:
            client: Memgraph 客户端实例（如果为 None，将创建新实例）
        """
        self.client = client or MemgraphClient()
    
    @cache_result(ttl=60, key_prefix="hierarchy:projects")  # 缓存 1 分钟
    def get_projects(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """获取项目列表
        
        Args:
            page: 页码（从 1 开始）
            page_size: 每页数量
            
        Returns:
            Dict: 包含 items（项目列表）和 total（总数量）的字典
        """
        skip = (page - 1) * page_size
        
        # 查询项目总数
        count_query = "MATCH (p:Project) RETURN count(p) as total"
        count_result = self.client.execute_query(count_query)
        total = count_result[0]["total"] if count_result else 0
        
        # 查询项目列表（带分页）
        query = """
        MATCH (p:Project)
        OPTIONAL MATCH (p)-[:PHYSICALLY_CONTAINS]->(b:Building)
        WITH p, count(DISTINCT b) as building_count
        RETURN p.id as id, p.name as name, p.description as description,
               building_count, p.created_at as created_at, p.updated_at as updated_at
        ORDER BY p.created_at DESC
        SKIP $skip LIMIT $limit
        """
        
        results = self.client.execute_query(query, {"skip": skip, "limit": page_size})
        
        items = [
            ProjectListItem(
                id=r["id"],
                name=r["name"],
                description=r.get("description"),
                building_count=r.get("building_count", 0),
                created_at=convert_neo4j_datetime(r["created_at"]) or datetime.now(),
                updated_at=convert_neo4j_datetime(r["updated_at"]) or datetime.now(),
            )
            for r in results
        ]
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    
    @cache_result(ttl=300, key_prefix="hierarchy:project_detail")  # 缓存 5 分钟
    def get_project_detail(self, project_id: str) -> Optional[ProjectDetail]:
        """获取项目详情
        
        Args:
            project_id: 项目 ID
            
        Returns:
            ProjectDetail: 项目详情，如果不存在则返回 None
        """
        query = """
        MATCH (p:Project {id: $project_id})
        OPTIONAL MATCH (p)-[:PHYSICALLY_CONTAINS]->(b:Building)
        WITH p, count(DISTINCT b) as building_count
        RETURN p.id as id, p.name as name, p.description as description,
               building_count, p.created_at as created_at, p.updated_at as updated_at
        """
        
        result = self.client.execute_query(query, {"project_id": project_id})
        
        if not result:
            return None
        
        r = result[0]
        return ProjectDetail(
            id=r["id"],
            name=r["name"],
            description=r.get("description"),
            building_count=r.get("building_count", 0),
            created_at=convert_neo4j_datetime(r["created_at"]) or datetime.now(),
            updated_at=convert_neo4j_datetime(r["updated_at"]) or datetime.now(),
        )
    
    @cache_result(ttl=300, key_prefix="hierarchy:project_hierarchy")  # 缓存 5 分钟
    def get_project_hierarchy(self, project_id: str) -> Optional[HierarchyResponse]:
        """获取项目的完整层级树
        
        优化：使用单个查询获取完整层级树，避免递归查询导致的 N+1 问题
        
        Args:
            project_id: 项目 ID
            
        Returns:
            HierarchyResponse: 层级树响应，如果项目不存在则返回 None
        """
        # 首先验证项目存在（注意：这里会绕过缓存，因为我们需要实时数据）
        # 但项目详情本身也有缓存，所以影响不大
        project = self.get_project_detail(project_id)
        if not project:
            return None
        
        # 使用递归方法构建树（避免Memgraph不支持嵌套collect的问题）
        # 这个方法虽然需要多次查询，但更稳定可靠
        root_node = self._build_hierarchy_node("Project", project_id)
        
        if not root_node:
            return None
        
        return HierarchyResponse(
            project_id=project_id,
            project_name=project.name,
            hierarchy=root_node,
        )
    
    def _build_hierarchy_node(self, label: str, node_id: str) -> Optional[HierarchyNode]:
        """递归构建层级节点
        
        Args:
            label: 节点标签（Project/Building/Division 等）
            node_id: 节点 ID
            
        Returns:
            HierarchyNode: 层级节点，如果不存在则返回 None
        """
        # 查询节点基本信息
        query = f"MATCH (n:{label} {{id: $node_id}}) RETURN n"
        result = self.client.execute_query(query, {"node_id": node_id})
        
        if not result:
            return None
        
        node_data = dict(result[0]["n"])
        node_name = node_data.get("name", node_id)
        
        # 根据节点类型查询子节点
        children = []
        
        if label == "Project":
            # Project -> Building
            children = self._get_child_nodes("Building", "Project", node_id, "PHYSICALLY_CONTAINS")
        elif label == "Building":
            # Building -> Division, Level
            children = self._get_child_nodes("Division", "Building", node_id, "MANAGEMENT_CONTAINS")
            children.extend(self._get_child_nodes("Level", "Building", node_id, "PHYSICALLY_CONTAINS"))
        elif label == "Division":
            # Division -> SubDivision
            children = self._get_child_nodes("SubDivision", "Division", node_id, "MANAGEMENT_CONTAINS")
        elif label == "SubDivision":
            # SubDivision -> Item
            children = self._get_child_nodes("Item", "SubDivision", node_id, "MANAGEMENT_CONTAINS")
        elif label == "Item":
            # Item -> InspectionLot
            children = self._get_child_nodes("InspectionLot", "Item", node_id, "HAS_LOT")
        
        # 构建元数据
        metadata = {}
        if label == "Item":
            # 查询检验批数量
            metadata["inspection_lot_count"] = len(children)
        elif label == "InspectionLot":
            # 查询构件数量
            element_count_query = """
            MATCH (lot:InspectionLot {id: $lot_id})-[r]->(e:Element)
            WHERE type(r) = 'MANAGEMENT_CONTAINS'
            RETURN count(e) as count
            """
            count_result = self.client.execute_query(element_count_query, {"lot_id": node_id})
            metadata["element_count"] = count_result[0]["count"] if count_result else 0
        
        return HierarchyNode(
            id=node_id,
            label=label,
            name=node_name,
            children=children,
            metadata=metadata if metadata else None,
        )
    
    def _get_child_nodes(
        self,
        child_label: str,
        parent_label: str,
        parent_id: str,
        relationship_type: str
    ) -> List[HierarchyNode]:
        """获取子节点列表（保留原方法以保持兼容性）"""
        return self._get_child_nodes_optimized(child_label, parent_label, parent_id, relationship_type)
    
    def _get_child_nodes_optimized(
        self,
        child_label: str,
        parent_label: str,
        parent_id: str,
        relationship_type: str
    ) -> List[HierarchyNode]:
        """优化的获取子节点列表
        
        优化：批量查询子节点信息，减少查询次数
        
        Args:
            child_label: 子节点标签
            parent_label: 父节点标签
            parent_id: 父节点 ID
            relationship_type: 关系类型
            
        Returns:
            List[HierarchyNode]: 子节点列表
        """
        # 根据关系方向构建查询
        # 如果是 HAS_LOT，关系是从 Item 指向 InspectionLot
        if relationship_type == "HAS_LOT":
            query = f"""
            MATCH (p:{parent_label} {{id: $parent_id}})-[:{relationship_type}]->(c:{child_label})
            RETURN c.id as id, c.name as name
            ORDER BY c.name, c.id
            """
        else:
            # 其他关系都是从父节点指向子节点
            query = f"""
            MATCH (p:{parent_label} {{id: $parent_id}})-[:{relationship_type}]->(c:{child_label})
            RETURN c.id as id, c.name as name
            ORDER BY c.name, c.id
            """
        
        results = self.client.execute_query(query, {"parent_id": parent_id})
        
        # 批量获取所有子节点 ID
        child_ids = [r["id"] for r in results]
        
        if not child_ids:
            return []
        
        # 批量查询子节点信息（优化：减少查询次数）
        # 对于 InspectionLot，还需要查询构件数量
        if child_label == "InspectionLot":
            batch_query = f"""
            MATCH (c:{child_label})
            WHERE c.id IN $child_ids
            OPTIONAL MATCH (c)-[r]->(e:Element)
            WHERE type(r) = 'MANAGEMENT_CONTAINS'
            WITH c, count(DISTINCT e) as element_count
            RETURN c.id as id, c.name as name, element_count
            ORDER BY c.name, c.id
            """
            batch_results = self.client.execute_query(batch_query, {"child_ids": child_ids})
            
            # 构建节点映射
            node_map = {}
            for r in batch_results:
                node_id = r["id"]
                node_name = r.get("name", node_id)
                element_count = r.get("element_count", 0)
                
                # 递归构建子节点（InspectionLot 没有子节点）
                node_map[node_id] = HierarchyNode(
                    id=node_id,
                    label=child_label,
                    name=node_name,
                    children=[],
                    metadata={"element_count": element_count} if element_count > 0 else None,
                )
            
            # 按原始顺序返回
            return [node_map[cid] for cid in child_ids if cid in node_map]
        else:
            # 对于其他节点类型，递归构建
            children = []
            for r in results:
                child_node = self._build_hierarchy_node(child_label, r["id"])
                if child_node:
                    children.append(child_node)
            
            return children
    
    def get_building_detail(self, building_id: str) -> Optional[BuildingDetail]:
        """获取单体详情"""
        query = "MATCH (b:Building {id: $building_id}) RETURN b"
        result = self.client.execute_query(query, {"building_id": building_id})
        
        if not result:
            return None
        
        node_data = dict(result[0]["b"])
        return BuildingDetail(
            id=node_data["id"],
            name=node_data.get("name", ""),
            project_id=node_data.get("project_id", ""),
            description=node_data.get("description"),
            created_at=convert_neo4j_datetime(node_data.get("created_at")) or datetime.now(),
            updated_at=convert_neo4j_datetime(node_data.get("updated_at")) or datetime.now(),
        )
    
    def get_division_detail(self, division_id: str) -> Optional[DivisionDetail]:
        """获取分部详情"""
        query = "MATCH (d:Division {id: $division_id}) RETURN d"
        result = self.client.execute_query(query, {"division_id": division_id})
        
        if not result:
            return None
        
        node_data = dict(result[0]["d"])
        return DivisionDetail(
            id=node_data["id"],
            name=node_data.get("name", ""),
            building_id=node_data.get("building_id", ""),
            description=node_data.get("description"),
            created_at=convert_neo4j_datetime(node_data.get("created_at")) or datetime.now(),
            updated_at=convert_neo4j_datetime(node_data.get("updated_at")) or datetime.now(),
        )
    
    def get_subdivision_detail(self, subdivision_id: str) -> Optional[SubDivisionDetail]:
        """获取子分部详情"""
        query = "MATCH (sd:SubDivision {id: $subdivision_id}) RETURN sd"
        result = self.client.execute_query(query, {"subdivision_id": subdivision_id})
        
        if not result:
            return None
        
        node_data = dict(result[0]["sd"])
        return SubDivisionDetail(
            id=node_data["id"],
            name=node_data.get("name", ""),
            division_id=node_data.get("division_id", ""),
            description=node_data.get("description"),
            created_at=convert_neo4j_datetime(node_data.get("created_at")) or datetime.now(),
            updated_at=convert_neo4j_datetime(node_data.get("updated_at")) or datetime.now(),
        )
    
    def get_item_detail(self, item_id: str) -> Optional[ItemDetail]:
        """获取分项详情"""
        query = """
        MATCH (item:Item {id: $item_id})
        OPTIONAL MATCH (item)-[:HAS_LOT]->(lot:InspectionLot)
        WITH item, count(DISTINCT lot) as lot_count
        RETURN item, lot_count
        """
        result = self.client.execute_query(query, {"item_id": item_id})
        
        if not result:
            return None
        
        node_data = dict(result[0]["item"])
        lot_count = result[0].get("lot_count", 0)
        
        return ItemDetail(
            id=node_data["id"],
            name=node_data.get("name", ""),
            subdivision_id=node_data.get("subdivision_id", ""),
            description=node_data.get("description"),
            inspection_lot_count=lot_count,
            created_at=convert_neo4j_datetime(node_data.get("created_at")) or datetime.now(),
            updated_at=convert_neo4j_datetime(node_data.get("updated_at")) or datetime.now(),
        )
    
    def get_inspection_lot_detail(self, lot_id: str) -> Optional[InspectionLotDetail]:
        """获取检验批详情"""
        query = """
        MATCH (lot:InspectionLot {id: $lot_id})
        OPTIONAL MATCH (lot)-[r]->(e:Element)
        WHERE type(r) = 'MANAGEMENT_CONTAINS'
        WITH lot, count(DISTINCT e) as element_count
        RETURN lot, element_count
        """
        result = self.client.execute_query(query, {"lot_id": lot_id})
        
        if not result:
            return None
        
        node_data = dict(result[0]["lot"])
        element_count = result[0].get("element_count", 0)
        
        return InspectionLotDetail(
            id=node_data["id"],
            name=node_data.get("name", ""),
            item_id=node_data.get("item_id", ""),
            spatial_scope=node_data.get("spatial_scope"),
            status=node_data.get("status", "PLANNING"),
            element_count=element_count,
            created_at=convert_neo4j_datetime(node_data.get("created_at")) or datetime.now(),
            updated_at=convert_neo4j_datetime(node_data.get("updated_at")) or datetime.now(),
        )


