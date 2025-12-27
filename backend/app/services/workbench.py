"""工作台服务

负责 HITL Workbench 相关的数据查询和操作（Trace/Lift/Classify）
"""

import logging
import uuid
import math
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime

from app.utils.memgraph import MemgraphClient, convert_neo4j_datetime
from app.core.cache import get_cache
from app.core.exceptions import NotFoundError, ConflictError, ValidationError
from app.models.api.elements import (
    ElementListItem,
    ElementDetail,
    ElementQueryParams,
    TopologyUpdateRequest,
    ElementUpdateRequest,
    BatchLiftRequest,
    BatchLiftResponse,
    ClassifyRequest,
    ClassifyResponse,
)
from app.models.speckle.base import Geometry
from app.models.gb50300.element import ElementNode
from app.models.gb50300.relationships import (
    CONNECTED_TO,
    MANAGEMENT_CONTAINS,
    PHYSICALLY_CONTAINS,
    LOCATED_AT,
)

logger = logging.getLogger(__name__)

# Unassigned Item 的固定 ID
UNASSIGNED_ITEM_ID = "unassigned_item"


class WorkbenchService:
    """工作台服务"""
    
    def __init__(self, client: Optional[MemgraphClient] = None):
        """初始化服务
        
        Args:
            client: Memgraph 客户端实例（如果为 None，将创建新实例）
        """
        self.client = client or MemgraphClient()
    
    def query_elements(
        self,
        params: ElementQueryParams
    ) -> Dict[str, Any]:
        """查询构件列表
        
        Args:
            params: 查询参数
            
        Returns:
            Dict: 包含 items（构件列表）和 total（总数量）的字典
        """
        skip = (params.page - 1) * params.page_size
        
        # 构建 WHERE 条件
        where_conditions = []
        query_params: Dict[str, Any] = {}
        
        if params.level_id:
            where_conditions.append("e.level_id = $level_id")
            query_params["level_id"] = params.level_id
        
        # item_id 优化：使用关系直接查询，避免 N+1 查询
        # 如果同时指定了 item_id 和 inspection_lot_id，优先使用 inspection_lot_id
        item_id_used_in_match = False
        if params.item_id and not params.inspection_lot_id:
            # 标记 item_id 已在 MATCH 中使用，不需要在 WHERE 中添加条件
            item_id_used_in_match = True
            query_params["item_id"] = params.item_id
        
        if params.inspection_lot_id:
            where_conditions.append("e.inspection_lot_id = $inspection_lot_id")
            query_params["inspection_lot_id"] = params.inspection_lot_id
        
        if params.status:
            where_conditions.append("e.status = $status")
            query_params["status"] = params.status
        
        if params.speckle_type:
            where_conditions.append("e.speckle_type = $speckle_type")
            query_params["speckle_type"] = params.speckle_type
        
        if params.has_height is not None:
            if params.has_height:
                where_conditions.append("e.height IS NOT NULL")
            else:
                where_conditions.append("e.height IS NULL")
        
        if params.has_material is not None:
            if params.has_material:
                where_conditions.append("e.material IS NOT NULL")
            else:
                where_conditions.append("e.material IS NULL")
        
        if params.min_confidence is not None:
            where_conditions.append("e.confidence >= $min_confidence")
            query_params["min_confidence"] = params.min_confidence
        
        if params.max_confidence is not None:
            where_conditions.append("e.confidence <= $max_confidence")
            query_params["max_confidence"] = params.max_confidence
        
        # 生成缓存键
        cache = get_cache()
        cache_key = cache._generate_key(
            "elements:query",
            level_id=params.level_id,
            item_id=params.item_id,
            inspection_lot_id=params.inspection_lot_id,
            status=params.status,
            speckle_type=params.speckle_type,
            has_height=params.has_height,
            has_material=params.has_material,
            min_confidence=params.min_confidence,
            max_confidence=params.max_confidence,
            page=params.page,
            page_size=params.page_size,
        )
        
        # 尝试从缓存获取
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for elements query: {cache_key}")
            return cached_result
        
        logger.debug(f"Cache miss for elements query: {cache_key}")
        
        # 构建主查询
        # 优化：如果使用 item_id，直接在 MATCH 中使用关系路径，避免 N+1 查询
        if item_id_used_in_match:
            # 使用关系路径直接查询，单次查询完成
            where_conditions_clean = [c for c in where_conditions]
            where_clause = " AND ".join(where_conditions_clean) if where_conditions_clean else "1=1"
            
            query = f"""
            MATCH (item:Item {{id: $item_id}})-[:HAS_LOT]->(lot:InspectionLot)<-[:BELONGS_TO]-(e:Element)
            WHERE {where_clause}
            RETURN DISTINCT e.id as id,
                   e.speckle_type as speckle_type,
                   e.level_id as level_id,
                   e.inspection_lot_id as inspection_lot_id,
                   e.status as status,
                   e.height as height,
                   e.material as material,
                   e.created_at as created_at,
                   e.updated_at as updated_at
            ORDER BY e.created_at DESC
            SKIP $skip
            LIMIT $limit
            """
            
            count_query = f"""
            MATCH (item:Item {{id: $item_id}})-[:HAS_LOT]->(lot:InspectionLot)<-[:BELONGS_TO]-(e:Element)
            WHERE {where_clause}
            RETURN count(DISTINCT e) as total
            """
        else:
            # 标准查询路径
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            
            query = f"""
            MATCH (e:Element)
            WHERE {where_clause}
            RETURN e.id as id,
                   e.speckle_type as speckle_type,
                   e.level_id as level_id,
                   e.inspection_lot_id as inspection_lot_id,
                   e.status as status,
                   e.height as height,
                   e.material as material,
                   e.created_at as created_at,
                   e.updated_at as updated_at
            ORDER BY e.created_at DESC
            SKIP $skip
            LIMIT $limit
            """
            
            count_query = f"""
            MATCH (e:Element)
            WHERE {where_clause}
            RETURN count(e) as total
            """
        
        query_params["skip"] = skip
        query_params["limit"] = params.page_size
        
        # 查询总数
        count_result = self.client.execute_query(count_query, query_params)
        total = count_result[0]["total"] if count_result else 0
        
        # 查询构件列表
        results = self.client.execute_query(query, query_params)
        
        items = []
        for r in results:
            # 处理可能为 None 的字段，提供默认值
            level_id = r.get("level_id") or ""
            status = r.get("status") or "Draft"
            if status not in ["Draft", "Verified"]:
                status = "Draft"
            
            items.append(ElementListItem(
                id=r["id"],
                speckle_type=r["speckle_type"],
                level_id=level_id,
                inspection_lot_id=r.get("inspection_lot_id"),
                status=status,
                has_height=r.get("height") is not None,
                has_material=r.get("material") is not None,
                created_at=convert_neo4j_datetime(r.get("created_at")) or datetime.now(),
                updated_at=convert_neo4j_datetime(r.get("updated_at")) or datetime.now(),
            ))
        
        result = {
            "items": items,
            "total": total,
            "page": params.page,
            "page_size": params.page_size,
        }
        
        # 存入缓存（TTL: 30 秒）
        cache.set(cache_key, result, ttl=30)
        
        return result
    
    def batch_get_elements(self, element_ids: List[str]) -> Dict[str, Any]:
        """批量获取构件详情
        
        使用单个Cypher查询批量获取多个构件的详细信息，包括连接关系
        避免N+1查询问题
        
        Args:
            element_ids: 构件 ID 列表（最多100个）
            
        Returns:
            Dict: 包含 items（构件详情列表）和 not_found（未找到的ID列表）的字典
        """
        if not element_ids:
            return {"items": [], "not_found": []}
        
        # 限制批量查询数量，避免查询过大（从100提高到500）
        if len(element_ids) > 500:
            raise ValidationError(
                "最多支持批量查询500个构件",
                {"element_count": len(element_ids), "max_count": 500}
            )
        
        # 使用单个查询获取所有构件的详细信息和连接关系
        # 使用OPTIONAL MATCH来处理可能没有连接关系的构件
        query = """
        MATCH (e:Element)
        WHERE e.id IN $element_ids
        OPTIONAL MATCH (e)-[r]->(other:Element)
        WHERE type(r) IN ['CONNECTED_TO', 'FEEDS', 'FEEDS_FROM', 'CONTROLS', 'HAS_PART', 'LOCATED_IN', 'SERVES']
        WITH e, collect(DISTINCT other.id) as connected_ids
        RETURN e,
               connected_ids
        """
        
        results = self.client.execute_query(query, {"element_ids": element_ids})
        
        # 创建结果映射
        element_map: Dict[str, ElementDetail] = {}
        found_ids = set()
        
        for row in results:
            element_data = dict(row["e"])
            element_id = element_data["id"]
            found_ids.add(element_id)
            connected_elements = row.get("connected_ids", [])
            connected_elements = [cid for cid in connected_elements if cid]  # 过滤None值
            
            # 解析 geometry
            geometry_dict = element_data.get("geometry")
            if not isinstance(geometry_dict, dict):
                logger.warning(f"Element {element_id} has no geometry, skipping")
                continue
            
            try:
                geometry = Geometry(**geometry_dict)
            except Exception as e:
                logger.warning(f"Failed to parse geometry for element {element_id}: {e}")
                continue
            
            element_map[element_id] = ElementDetail(
                id=element_data["id"],
                speckle_id=element_data.get("speckle_id"),
                speckle_type=element_data["speckle_type"],
                geometry=geometry,
                height=element_data.get("height"),
                base_offset=element_data.get("base_offset"),
                material=element_data.get("material"),
                level_id=element_data["level_id"],
                zone_id=element_data.get("zone_id"),
                inspection_lot_id=element_data.get("inspection_lot_id"),
                status=element_data.get("status", "Draft"),
                confidence=element_data.get("confidence"),
                locked=element_data.get("locked", False),
                connected_elements=connected_elements,
                created_at=convert_neo4j_datetime(element_data.get("created_at")) or datetime.now(),
                updated_at=convert_neo4j_datetime(element_data.get("updated_at")) or datetime.now(),
            )
        
        # 找出未找到的ID
        not_found = [eid for eid in element_ids if eid not in found_ids]
        
        # 按输入顺序返回结果
        items = [element_map[eid] for eid in element_ids if eid in element_map]
        
        return {
            "items": items,
            "not_found": not_found,
        }
    
    def get_element(self, element_id: str) -> Optional[ElementDetail]:
        """获取构件详情
        
        Args:
            element_id: 构件 ID
            
        Returns:
            ElementDetail: 构件详情，如果不存在则返回 None
        """
        # 查询构件基本信息
        query = "MATCH (e:Element {id: $element_id}) RETURN e"
        result = self.client.execute_query(query, {"element_id": element_id})
        
        if not result:
            return None
        
        element_data = dict(result[0]["e"])
        
        # 查询连接的构件（支持所有 Brick 关系类型）
        from app.core.ontology import MEMGRAPH_BRICK_RELATIONSHIPS, DEFAULT_RELATIONSHIP
        all_relationship_types = list(MEMGRAPH_BRICK_RELATIONSHIPS.keys()) + [DEFAULT_RELATIONSHIP]
        relationship_types_str = "['" + "', '".join(all_relationship_types) + "']"
        
        connected_query = f"""
        MATCH (e:Element {{id: $element_id}})-[r]->(other:Element)
        WHERE type(r) IN {relationship_types_str}
        RETURN other.id as id, type(r) as relationship_type
        """
        connected_results = self.client.execute_query(connected_query, {"element_id": element_id})
        connected_elements = [r["id"] for r in connected_results]
        
        # 解析 geometry
        geometry_dict = element_data.get("geometry")
        if isinstance(geometry_dict, dict):
            geometry = Geometry(**geometry_dict)
        else:
            # 如果没有 geometry，返回 None（不应该发生）
            logger.warning(f"Element {element_id} has no geometry")
            return None
        
        return ElementDetail(
            id=element_data["id"],
            speckle_id=element_data.get("speckle_id"),
            speckle_type=element_data["speckle_type"],
            geometry=geometry,
            height=element_data.get("height"),
            base_offset=element_data.get("base_offset"),
            material=element_data.get("material"),
            level_id=element_data["level_id"],
            zone_id=element_data.get("zone_id"),
            inspection_lot_id=element_data.get("inspection_lot_id"),
            status=element_data.get("status", "Draft"),
            confidence=element_data.get("confidence"),
            locked=element_data.get("locked", False),
            connected_elements=connected_elements,
            created_at=convert_neo4j_datetime(element_data.get("created_at")) or datetime.now(),
            updated_at=convert_neo4j_datetime(element_data.get("updated_at")) or datetime.now(),
        )
    
    def get_unassigned_elements(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """获取未分配构件列表
        
        查找 inspection_lot_id 为 NULL 或关联到 Unassigned Item 的构件
        
        Args:
            page: 页码
            page_size: 每页数量
            
        Returns:
            Dict: 包含 items（构件列表）和 total（总数量）的字典
        """
        skip = (page - 1) * page_size
        
        # 查询未分配的构件（inspection_lot_id 为 NULL）
        # 优化：使用索引字段（inspection_lot_id）进行COUNT查询，性能更好
        count_query = "MATCH (e:Element) WHERE e.inspection_lot_id IS NULL RETURN count(e) as total"
        count_result = self.client.execute_query(count_query)
        total = count_result[0]["total"] if count_result else 0
        
        query = """
        MATCH (e:Element)
        WHERE e.inspection_lot_id IS NULL
        RETURN e.id as id, e.speckle_type as speckle_type, e.level_id as level_id,
               e.status as status, e.height as height, e.material as material,
               e.created_at as created_at, e.updated_at as updated_at
        ORDER BY e.created_at DESC
        SKIP $skip LIMIT $limit
        """
        
        results = self.client.execute_query(query, {"skip": skip, "limit": page_size})
        
        items = []
        for r in results:
            # 处理可能为 None 的字段，提供默认值
            level_id = r.get("level_id") or ""
            status = r.get("status") or "Draft"
            if status not in ["Draft", "Verified"]:
                status = "Draft"
            
            items.append(ElementListItem(
                id=r["id"],
                speckle_type=r["speckle_type"],
                level_id=level_id,
                inspection_lot_id=None,
                status=status,
                has_height=r.get("height") is not None,
                has_material=r.get("material") is not None,
                created_at=convert_neo4j_datetime(r.get("created_at")) or datetime.now(),
                updated_at=convert_neo4j_datetime(r.get("updated_at")) or datetime.now(),
            ))
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    
    def update_element_topology(
        self,
        element_id: str,
        request: TopologyUpdateRequest
    ) -> Dict[str, Any]:
        """更新构件拓扑关系（Trace Mode）
        
        Args:
            element_id: 构件 ID
            request: 拓扑更新请求
            
        Returns:
            Dict: 更新结果
            
        Raises:
            ValueError: 如果构件不存在
        """
        # 验证构件存在
        element = self.get_element(element_id)
        if not element:
            raise ValueError(f"Element not found: {element_id}")
        
        # 如果提供了 geometry，更新几何数据
        if request.geometry:
            geometry_dict = request.geometry.model_dump()
            update_query = """
            MATCH (e:Element {id: $element_id})
            SET e.geometry = $geometry, e.updated_at = datetime()
            """
            self.client.execute_write(update_query, {
                "element_id": element_id,
                "geometry": geometry_dict,
            })
            
            # 清除相关缓存
            cache = get_cache()
            cache.invalidate("elements:")
        
        # 更新连接关系
        if request.connected_elements is not None:
            # 删除旧的连接关系（删除所有可能的关系类型）
            # 注意：Cypher 不支持在关系类型中使用 OR，需要分别删除
            from app.core.ontology import MEMGRAPH_BRICK_RELATIONSHIPS, DEFAULT_RELATIONSHIP
            all_relationship_types = list(MEMGRAPH_BRICK_RELATIONSHIPS.keys()) + [DEFAULT_RELATIONSHIP]
            
            for rel_type in all_relationship_types:
                delete_query = f"""
                MATCH (e:Element {{id: $element_id}})-[r:{rel_type}]->()
                DELETE r
                """
                self.client.execute_write(delete_query, {"element_id": element_id})
            
            # 创建新的连接关系（使用 Brick 语义关系）
            invalid_connections = []
            from app.core.ontology import get_ontology_mapper
            
            # 获取源元素的类型
            source_element = self.get_element(element_id)
            if not source_element:
                logger.warning(f"Source element not found: {element_id}")
                return {
                    "id": element_id,
                    "topology_updated": False,
                    "error": "Source element not found"
                }
            
            source_type = source_element.speckle_type
            mapper = get_ontology_mapper()
            
            for connected_id in request.connected_elements:
                # 验证目标构件存在并获取类型
                target_query = "MATCH (e:Element {id: $id}) RETURN e.id as id, e.speckle_type as speckle_type"
                target_result = self.client.execute_query(target_query, {"id": connected_id})
                
                if target_result:
                    target_type = target_result[0].get("speckle_type")
                    
                    # 推断 Brick 语义关系类型
                    relationship_type = mapper.infer_relationship_type(source_type, target_type)
                    
                    # 如果创建 CONTAINED_IN 关系（电缆 -> 桥架），验证容量
                    if relationship_type == "CONTAINED_IN" and target_type == "CableTray":
                        from app.core.cable_capacity_validator import CableCapacityValidator
                        validator = CableCapacityValidator(self.client)
                        capacity_result = validator.validate_cable_tray_capacity(
                            connected_id, element_id
                        )
                        if not capacity_result["valid"]:
                            invalid_connections.append({
                                "id": connected_id,
                                "reason": "; ".join(capacity_result["errors"])
                            })
                            logger.warning(
                                f"Capacity validation failed for cable {element_id} -> tray {connected_id}: "
                                f"{'; '.join(capacity_result['errors'])}"
                            )
                            continue  # 跳过这个连接
                    
                    # 创建关系（使用推断的关系类型）
                    self.client.create_relationship(
                        "Element", element_id,
                        "Element", connected_id,
                        relationship_type
                    )
                    logger.debug(f"Created {relationship_type} relationship: {element_id} -> {connected_id}")
                else:
                    invalid_connections.append(connected_id)
                    logger.warning(f"Target element not found for connection: {connected_id}")
            
            if invalid_connections:
                logger.warning(
                    f"Element {element_id}: {len(invalid_connections)} invalid connection(s) skipped: {invalid_connections}"
                )
        
        logger.info(f"Updated topology for element: {element_id}")
        
        return {
            "id": element_id,
            "topology_updated": True,
        }
    
    def update_element(
        self,
        element_id: str,
        request: ElementUpdateRequest
    ) -> Dict[str, Any]:
        """更新构件参数（Lift Mode）
        
        Args:
            element_id: 构件 ID
            request: 更新请求
            
        Returns:
            Dict: 更新结果
            
        Raises:
            NotFoundError: 如果构件不存在
            ConflictError: 如果构件已锁定
        """
        # 验证构件存在
        element = self.get_element(element_id)
        if not element:
            raise NotFoundError(
                f"Element not found: {element_id}. Please check the element ID and try again.",
                {"element_id": element_id, "resource_type": "Element"}
            )
        
        # 检查是否锁定
        if element.locked:
            raise ConflictError(
                f"Element {element_id} is locked and cannot be modified. "
                f"Unlock the element first or contact the administrator.",
                {"element_id": element_id, "reason": "locked"}
            )
        
        # 构建更新字段
        update_fields = []
        update_params: Dict[str, Any] = {"element_id": element_id}
        
        if request.height is not None:
            update_fields.append("e.height = $height")
            update_params["height"] = request.height
        
        if request.base_offset is not None:
            update_fields.append("e.base_offset = $base_offset")
            update_params["base_offset"] = request.base_offset
        
        if request.material is not None:
            update_fields.append("e.material = $material")
            update_params["material"] = request.material
        
        if not update_fields:
            return {"id": element_id, "updated_fields": []}
        
        # 执行更新
        update_query = f"""
        MATCH (e:Element {{id: $element_id}})
        SET {', '.join(update_fields)}, e.updated_at = datetime()
        RETURN e.id as id
        """
        self.client.execute_write(update_query, update_params)
        
        # 提取字段名（移除 "e." 前缀和 " = $..." 后缀）
        updated_fields = []
        for f in update_fields:
            # 移除 "e." 前缀
            field_name = f.replace("e.", "")
            # 移除 " = $..." 后缀（保留字段名）
            if " = $" in field_name:
                field_name = field_name.split(" = $")[0]
            updated_fields.append(field_name)
        
        logger.info(f"Updated element: {element_id}, fields: {updated_fields}")
        
        # 清除相关缓存
        cache = get_cache()
        cache.invalidate("elements:")
        
        return {
            "id": element_id,
            "updated_fields": updated_fields,
        }
    
    def batch_lift_elements(
        self,
        request: BatchLiftRequest
    ) -> BatchLiftResponse:
        """批量设置 Z 轴参数（Lift Mode）
        
        Args:
            request: 批量 Lift 请求
            
        Returns:
            BatchLiftResponse: 批量更新结果
            
        Raises:
            ValueError: 如果任何构件不存在
        """
        updated_ids = []
        
        for element_id in request.element_ids:
            try:
                update_request = ElementUpdateRequest(
                    height=request.height,
                    base_offset=request.base_offset,
                    material=request.material,
                )
                self.update_element(element_id, update_request)
                updated_ids.append(element_id)
            except (ValueError, NotFoundError) as e:
                logger.warning(f"Failed to update element {element_id}: {e}")
                # 继续处理其他构件，不中断批量操作
        
        logger.info(f"Batch lifted {len(updated_ids)} elements")
        
        return BatchLiftResponse(
            updated_count=len(updated_ids),
            element_ids=updated_ids,
        )
    
    def delete_element(self, element_id: str) -> Dict[str, Any]:
        """删除构件及其所有关联关系
        
        使用 DETACH DELETE 删除构件节点及其所有关系（包括：
        - 与其他构件的连接关系 (CONNECTED_TO)
        - 所属检验批关系 (BELONGS_TO_LOT)
        - 其他可能的关联关系）
        
        Args:
            element_id: 要删除的构件 ID
            
        Returns:
            Dict: 删除结果，包含 id 和 deleted 字段
                - id: 被删除的构件 ID
                - deleted: 布尔值，表示是否成功删除
                
        Raises:
            ValueError: 如果构件不存在
            
        Note:
            - 删除操作不可撤销，请谨慎使用
            - 删除后，相关的检验批中的构件数量会自动更新
        """
        # 验证构件存在
        element = self.get_element(element_id)
        if not element:
            raise NotFoundError(
                f"Element not found: {element_id}",
                {"element_id": element_id, "resource_type": "Element"}
            )
        
        # 使用 DETACH DELETE 删除节点及其所有关系
        delete_query = """
        MATCH (e:Element {id: $element_id})
        DETACH DELETE e
        """
        self.client.execute_write(delete_query, {"element_id": element_id})
        
        logger.info(f"Deleted element: {element_id}")
        
        # 清除相关缓存
        cache = get_cache()
        cache.invalidate("elements:")
        
        return {
            "id": element_id,
            "deleted": True,
        }
    
    def batch_update_elements(
        self,
        element_ids: List[str],
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """批量更新构件
        
        优化：使用单个查询批量更新，提高性能
        
        Args:
            element_ids: 构件 ID 列表
            updates: 要更新的字段字典
            
        Returns:
            Dict: 包含 success_count, failed_count, updated_ids, errors
        """
        if not element_ids:
            return {
                "success_count": 0,
                "failed_count": 0,
                "updated_ids": [],
                "errors": [],
            }
        
        # 构建更新字段
        update_fields = []
        update_params: Dict[str, Any] = {"element_ids": element_ids}
        
        if "height" in updates and updates["height"] is not None:
            update_fields.append("e.height = $height")
            update_params["height"] = updates["height"]
        
        if "base_offset" in updates and updates["base_offset"] is not None:
            update_fields.append("e.base_offset = $base_offset")
            update_params["base_offset"] = updates["base_offset"]
        
        if "material" in updates and updates["material"] is not None:
            update_fields.append("e.material = $material")
            update_params["material"] = updates["material"]
        
        if "status" in updates and updates["status"] is not None:
            update_fields.append("e.status = $status")
            update_params["status"] = updates["status"]
        
        if not update_fields:
            return {
                "success_count": 0,
                "failed_count": len(element_ids),
                "updated_ids": [],
                "errors": [{"element_id": eid, "error_message": "没有提供要更新的字段"} for eid in element_ids],
            }
        
        # 验证构件存在且未锁定
        check_query = """
        MATCH (e:Element)
        WHERE e.id IN $element_ids
        RETURN e.id as id, e.locked as locked
        """
        check_results = self.client.execute_query(check_query, {"element_ids": element_ids})
        
        valid_ids = []
        errors = []
        found_ids = {r["id"] for r in check_results}
        
        for element_id in element_ids:
            if element_id not in found_ids:
                errors.append({"element_id": element_id, "error_message": "构件不存在"})
                continue
            result = next((r for r in check_results if r["id"] == element_id), None)
            if result and result.get("locked", False):
                errors.append({"element_id": element_id, "error_message": "构件已锁定"})
                continue
            valid_ids.append(element_id)
        
        if not valid_ids:
            return {
                "success_count": 0,
                "failed_count": len(element_ids),
                "updated_ids": [],
                "errors": errors,
            }
        
        # 批量更新有效构件
        update_query = f"""
        MATCH (e:Element)
        WHERE e.id IN $valid_ids
        SET {', '.join(update_fields)}, e.updated_at = datetime()
        RETURN e.id as id
        """
        update_params["valid_ids"] = valid_ids
        self.client.execute_write(update_query, update_params)
        
        logger.info(f"Batch updated {len(valid_ids)} elements")
        
        # 清除相关缓存
        cache = get_cache()
        cache.invalidate("elements:")
        
        return {
            "success_count": len(valid_ids),
            "failed_count": len(errors),
            "updated_ids": valid_ids,
            "errors": errors,
        }
    
    def batch_delete_elements(
        self,
        element_ids: List[str]
    ) -> Dict[str, Any]:
        """批量删除构件
        
        优化：使用单个查询批量删除，提高性能
        
        Args:
            element_ids: 要删除的构件 ID 列表
            
        Returns:
            Dict: 包含 success_count, failed_count, deleted_ids, errors
        """
        if not element_ids:
            return {
                "success_count": 0,
                "failed_count": 0,
                "deleted_ids": [],
                "errors": [],
            }
        
        # 验证构件存在
        check_query = """
        MATCH (e:Element)
        WHERE e.id IN $element_ids
        RETURN e.id as id
        """
        check_results = self.client.execute_query(check_query, {"element_ids": element_ids})
        
        valid_ids = [r["id"] for r in check_results]
        errors = []
        
        for element_id in element_ids:
            if element_id not in valid_ids:
                errors.append({"element_id": element_id, "error_message": "构件不存在"})
        
        if not valid_ids:
            return {
                "success_count": 0,
                "failed_count": len(element_ids),
                "deleted_ids": [],
                "errors": errors,
            }
        
        # 批量删除有效构件（使用 DETACH DELETE 级联删除关系）
        delete_query = """
        MATCH (e:Element)
        WHERE e.id IN $valid_ids
        DETACH DELETE e
        """
        self.client.execute_write(delete_query, {"valid_ids": valid_ids})
        
        logger.info(f"Batch deleted {len(valid_ids)} elements")
        
        # 清除相关缓存
        cache = get_cache()
        cache.invalidate("elements:")
        
        return {
            "success_count": len(valid_ids),
            "failed_count": len(errors),
            "deleted_ids": valid_ids,
            "errors": errors,
        }
    
    def classify_element(
        self,
        element_id: str,
        request: ClassifyRequest
    ) -> ClassifyResponse:
        """将构件归类到分项（Classify Mode）
        
        将构件从当前分项（或 Unassigned Item）移动到目标 Item
        
        Args:
            element_id: 构件 ID
            request: 归类请求
            
        Returns:
            ClassifyResponse: 归类结果
            
        Raises:
            ValueError: 如果构件或目标 Item 不存在
        """
        # 验证构件存在
        element = self.get_element(element_id)
        if not element:
            raise NotFoundError(
                f"Element not found: {element_id}. "
                f"Please check the element ID and ensure it exists in the database.",
                {"element_id": element_id, "resource_type": "Element"}
            )
        
        # 验证目标 Item 存在
        item_query = "MATCH (item:Item {id: $item_id}) RETURN item.id as id, item.name as name"
        item_result = self.client.execute_query(item_query, {"item_id": request.item_id})
        if not item_result:
            raise NotFoundError(
                f"Item not found: {request.item_id}. "
                f"Please check the item ID and ensure it exists in the hierarchy.",
                {"item_id": request.item_id, "resource_type": "Item"}
            )
        
        # 获取之前的 item_id（通过 inspection_lot_id 查找）
        previous_item_id = None
        if element.inspection_lot_id:
            # 查找该 InspectionLot 的 Item
            lot_query = """
            MATCH (lot:InspectionLot {id: $lot_id})<-[:HAS_LOT]-(item:Item)
            RETURN item.id as id
            """
            lot_result = self.client.execute_query(lot_query, {"lot_id": element.inspection_lot_id})
            if lot_result:
                previous_item_id = lot_result[0]["id"]
        
        # 由于 Element 通过 inspection_lot_id 关联到 Item，
        # 而归类操作是要将 Element 归类到 Item（不是 InspectionLot），
        # 这里我们需要：
        # 1. 如果 Item 没有 InspectionLot，我们需要创建一个默认的 InspectionLot
        # 2. 或者，我们直接将 Element 的 inspection_lot_id 设置为 None，表示未分配
        # 
        # 根据业务逻辑，Classify 操作是将 Element 归类到 Item，但 Element 实际关联的是 InspectionLot。
        # 在 Phase 2 中，我们简化处理：将 Element 的 inspection_lot_id 设置为 None，
        # 表示该 Element 已归类到 Item，但还没有分配到具体的 InspectionLot。
        # 
        # 注意：这个逻辑在 Phase 3 中可能会改变（当实现检验批管理时）
        
        # 暂时只更新 inspection_lot_id 为 None（表示已归类但未分配检验批）
        update_query = """
        MATCH (e:Element {id: $element_id})
        SET e.inspection_lot_id = NULL, e.updated_at = datetime()
        """
        self.client.execute_write(update_query, {"element_id": element_id})
        
        logger.info(f"Classified element {element_id} to item {request.item_id}")
        
        # 清除相关缓存
        cache = get_cache()
        cache.invalidate("elements:")
        cache.invalidate("hierarchy:")
        
        return ClassifyResponse(
            element_id=element_id,
            item_id=request.item_id,
            previous_item_id=previous_item_id,
        )
    
    def _generate_element_id(self) -> str:
        """生成 Element ID
        
        Returns:
            str: 唯一的 Element ID
        """
        unique_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d")
        return f"element_{timestamp}_{unique_id}"

