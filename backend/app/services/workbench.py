"""工作台服务

负责 HITL Workbench 相关的数据查询和操作（Trace/Lift/Classify）
"""

import logging
import uuid
import math
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime

from app.utils.memgraph import MemgraphClient, convert_neo4j_datetime
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
from app.models.speckle.base import Geometry2D
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
        
        # item_id 需要单独处理，因为它需要关联 InspectionLot
        item_lot_ids = None
        if params.item_id:
            # 先查找该 Item 的所有 InspectionLot IDs
            lot_query = """
            MATCH (item:Item {id: $item_id})-[:HAS_LOT]->(lot:InspectionLot)
            RETURN collect(lot.id) as lot_ids
            """
            lot_result = self.client.execute_query(lot_query, {"item_id": params.item_id})
            item_lot_ids = lot_result[0]["lot_ids"] if lot_result and lot_result[0].get("lot_ids") else []
        
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
        
        # 处理 item_id 筛选（需要关联 InspectionLot）
        if item_lot_ids is not None:
            if item_lot_ids:
                # Item 有 InspectionLot，查找这些 InspectionLot 的构件或未分配的构件
                where_conditions.append("(e.inspection_lot_id IN $item_lot_ids OR e.inspection_lot_id IS NULL)")
                query_params["item_lot_ids"] = item_lot_ids
            else:
                # Item 没有 InspectionLot，只查找未分配的构件
                where_conditions.append("e.inspection_lot_id IS NULL")
        
        # 构建 WHERE 子句
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # 查询总数
        count_query = f"MATCH (e:Element) WHERE {where_clause} RETURN count(e) as total"
        count_result = self.client.execute_query(count_query, query_params)
        total = count_result[0]["total"] if count_result else 0
        
        # 查询构件列表
        query = f"""
        MATCH (e:Element)
        WHERE {where_clause}
        RETURN e.id as id, e.speckle_type as speckle_type, e.level_id as level_id,
               e.inspection_lot_id as inspection_lot_id, e.status as status,
               e.height as height, e.material as material,
               e.created_at as created_at, e.updated_at as updated_at
        ORDER BY e.created_at DESC
        SKIP $skip LIMIT $limit
        """
        query_params["skip"] = skip
        query_params["limit"] = params.page_size
        
        results = self.client.execute_query(query, query_params)
        
        items = []
        for r in results:
            items.append(ElementListItem(
                id=r["id"],
                speckle_type=r["speckle_type"],
                level_id=r["level_id"],
                inspection_lot_id=r.get("inspection_lot_id"),
                status=r.get("status", "Draft"),
                has_height=r.get("height") is not None,
                has_material=r.get("material") is not None,
                created_at=convert_neo4j_datetime(r.get("created_at")) or datetime.now(),
                updated_at=convert_neo4j_datetime(r.get("updated_at")) or datetime.now(),
            ))
        
        return {
            "items": items,
            "total": total,
            "page": params.page,
            "page_size": params.page_size,
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
        
        # 查询连接的构件
        connected_query = """
        MATCH (e:Element {id: $element_id})-[r:CONNECTED_TO]->(other:Element)
        RETURN other.id as id
        """
        connected_results = self.client.execute_query(connected_query, {"element_id": element_id})
        connected_elements = [r["id"] for r in connected_results]
        
        # 解析 geometry_2d
        geometry_2d_dict = element_data.get("geometry_2d")
        if isinstance(geometry_2d_dict, dict):
            geometry_2d = Geometry2D(**geometry_2d_dict)
        else:
            # 如果没有 geometry_2d，返回 None（不应该发生）
            logger.warning(f"Element {element_id} has no geometry_2d")
            return None
        
        return ElementDetail(
            id=element_data["id"],
            speckle_id=element_data.get("speckle_id"),
            speckle_type=element_data["speckle_type"],
            geometry_2d=geometry_2d,
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
            items.append(ElementListItem(
                id=r["id"],
                speckle_type=r["speckle_type"],
                level_id=r["level_id"],
                inspection_lot_id=None,
                status=r.get("status", "Draft"),
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
        
        # 如果提供了 geometry_2d，更新几何数据
        if request.geometry_2d:
            geometry_dict = request.geometry_2d.model_dump()
            update_query = """
            MATCH (e:Element {id: $element_id})
            SET e.geometry_2d = $geometry_2d, e.updated_at = datetime()
            """
            self.client.execute_write(update_query, {
                "element_id": element_id,
                "geometry_2d": geometry_dict,
            })
        
        # 更新连接关系
        if request.connected_elements is not None:
            # 删除旧的连接关系
            delete_query = """
            MATCH (e:Element {id: $element_id})-[r:CONNECTED_TO]->()
            DELETE r
            """
            self.client.execute_write(delete_query, {"element_id": element_id})
            
            # 创建新的连接关系
            invalid_connections = []
            for connected_id in request.connected_elements:
                # 验证目标构件存在
                target = self.client.execute_query(
                    "MATCH (e:Element {id: $id}) RETURN e.id as id",
                    {"id": connected_id}
                )
                if target:
                    self.client.create_relationship(
                        "Element", element_id,
                        "Element", connected_id,
                        CONNECTED_TO
                    )
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
            ValueError: 如果构件不存在或已锁定
        """
        # 验证构件存在
        element = self.get_element(element_id)
        if not element:
            raise ValueError(f"Element not found: {element_id}. Please check the element ID and try again.")
        
        # 检查是否锁定
        if element.locked:
            raise ValueError(
                f"Element {element_id} is locked and cannot be modified. "
                f"Unlock the element first or contact the administrator."
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
            except ValueError as e:
                logger.warning(f"Failed to update element {element_id}: {e}")
                # 继续处理其他构件，不中断批量操作
        
        logger.info(f"Batch lifted {len(updated_ids)} elements")
        
        return BatchLiftResponse(
            updated_count=len(updated_ids),
            element_ids=updated_ids,
        )
    
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
            raise ValueError(
                f"Element not found: {element_id}. "
                f"Please check the element ID and ensure it exists in the database."
            )
        
        # 验证目标 Item 存在
        item_query = "MATCH (item:Item {id: $item_id}) RETURN item.id as id, item.name as name"
        item_result = self.client.execute_query(item_query, {"item_id": request.item_id})
        if not item_result:
            raise ValueError(
                f"Item not found: {request.item_id}. "
                f"Please check the item ID and ensure it exists in the hierarchy."
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

