"""数据摄入服务

负责将 Speckle 元素转换为 OpenTruss Element 并存储到 Memgraph
"""

import uuid
import logging
from typing import Optional
from datetime import datetime

from app.utils.memgraph import MemgraphClient
from app.models.speckle import SpeckleBuiltElement
from app.models.speckle.base import Geometry, normalize_coordinates
from app.models.gb50300.element import ElementNode
from app.models.gb50300.relationships import (
    PHYSICALLY_CONTAINS,
    MANAGEMENT_CONTAINS,
    LOCATED_AT,
)

logger = logging.getLogger(__name__)

# Unassigned Item 的固定 ID
UNASSIGNED_ITEM_ID = "unassigned_item"


class IngestionService:
    """数据摄入服务"""
    
    def __init__(self, client: Optional[MemgraphClient] = None):
        """初始化服务
        
        Args:
            client: Memgraph 客户端实例（如果为 None，将创建新实例）
        """
        self.client = client or MemgraphClient()
    
    def ingest_speckle_element(
        self,
        speckle_element: SpeckleBuiltElement,
        project_id: str
    ) -> ElementNode:
        """摄入 Speckle 元素
        
        将 Speckle 元素转换为 OpenTruss Element 并存储到 Memgraph
        
        Args:
            speckle_element: Speckle 元素（Pydantic 模型）
            project_id: 项目 ID
            
        Returns:
            ElementNode: 创建的 Element 节点
            
        Raises:
            ValueError: 如果数据无效
            Exception: 如果存储失败
        """
        # 1. 生成 Element ID
        element_id = self._generate_element_id()
        
        # 2. 提取 geometry（3D 原生）
        geometry = self._extract_geometry(speckle_element)
        
        # 3. 提取 level_id（确保存在）
        level_id = self._extract_level_id(speckle_element, project_id)
        
        # 4. 处理未分配情况
        inspection_lot_id = speckle_element.inspection_lot_id
        if not inspection_lot_id:
            # 关联到 Unassigned Item（通过 inspection_lot_id 字段，但不创建关系）
            # 实际关系会在后续建立
            inspection_lot_id = None
        
        # 5. 创建 ElementNode
        element = ElementNode(
            id=element_id,
            speckle_id=speckle_element.speckle_id,
            speckle_type=speckle_element.speckle_type,
            geometry=geometry,
            height=getattr(speckle_element, 'height', None),
            base_offset=getattr(speckle_element, 'base_offset', None),
            material=getattr(speckle_element, 'material', None),
            level_id=level_id,
            zone_id=speckle_element.zone_id,
            inspection_lot_id=inspection_lot_id,
            status=speckle_element.status or "Draft",
            confidence=speckle_element.confidence,
            locked=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        # 6. 存储到 Memgraph
        self._store_element(element)
        
        # 7. 建立关系
        self._create_relationships(element, project_id)
        
        # 8. 语义验证（软检查，仅记录警告）
        # 注意：Ingestion 阶段不创建 Element 之间的连接关系，连接关系在 workbench 中创建
        # 如果将来需要处理连接关系，可以在这里添加软检查
        
        logger.info(f"Ingested element: {element_id} (type: {element.speckle_type})")
        
        return element
    
    def _generate_element_id(self) -> str:
        """生成 Element ID
        
        Returns:
            str: 唯一的 Element ID
        """
        # 使用 UUID 生成唯一 ID
        unique_id = str(uuid.uuid4())[:8]  # 使用 UUID 的前 8 位
        timestamp = datetime.now().strftime("%Y%m%d")
        return f"element_{timestamp}_{unique_id}"
    
    def _extract_geometry(self, speckle_element: SpeckleBuiltElement) -> Geometry:
        """提取 geometry（3D 原生）
        
        从 Speckle 元素中提取几何数据，支持 2D 和 3D 输入
        - 2D 输入（只有 x, y）：自动补 z=0.0
        - 3D 输入（x, y, z）：无损保存
        - null z 值：默认转换为 0.0
        
        Args:
            speckle_element: Speckle 元素
            
        Returns:
            Geometry: 3D 原生几何数据（坐标已规范化）
            
        Raises:
            ValueError: 如果无法提取几何数据
        """
        # 检查是否有 geometry 字段（3D 原生）
        if hasattr(speckle_element, 'geometry') and speckle_element.geometry:
            geo = speckle_element.geometry
            # 确保坐标已规范化（2D→3D 转换）
            if geo.coordinates:
                normalized_coords = normalize_coordinates(geo.coordinates)
                # 如果坐标被规范化，创建新的 Geometry 对象
                if normalized_coords != geo.coordinates:
                    return Geometry(
                        type=geo.type,
                        coordinates=normalized_coords,
                        closed=geo.closed
                    )
            return geo
        
        # 如果都没有，报错
        element_type = getattr(speckle_element, 'speckle_type', 'Unknown')
        raise ValueError(
            f"无法从 Speckle 元素提取 geometry: {element_type}. "
            f"元素必须包含有效的几何数据（geometry 字段）。"
        )
    
    def _extract_level_id(
        self,
        speckle_element: SpeckleBuiltElement,
        project_id: str
    ) -> str:
        """提取或创建 level_id
        
        确保 level_id 存在，如果不存在则查找或创建默认 Level
        
        Args:
            speckle_element: Speckle 元素
            project_id: 项目 ID
            
        Returns:
            str: level_id
        """
        # 如果已有 level_id，直接返回
        if speckle_element.level_id:
            # 验证 Level 是否存在
            query = "MATCH (l:Level {id: $level_id}) RETURN l.id as id"
            result = self.client.execute_query(query, {"level_id": speckle_element.level_id})
            if result:
                return speckle_element.level_id
            else:
                logger.warning(f"Level not found: {speckle_element.level_id}, will create default level")
        
        # 如果没有 level_id，查找项目下的默认 Level 或创建
        default_level_id = f"level_default_{project_id}"
        
        # 检查是否存在
        query = "MATCH (l:Level {id: $level_id}) RETURN l.id as id"
        result = self.client.execute_query(query, {"level_id": default_level_id})
        
        if not result:
            # 需要创建默认 Level
            # 先查找项目下的 Building
            building_query = "MATCH (b:Building {project_id: $project_id}) RETURN b.id as id LIMIT 1"
            building_result = self.client.execute_query(building_query, {"project_id": project_id})
            
            if building_result:
                building_id = building_result[0]["id"]
            else:
                # 如果 Building 也不存在，创建默认 Building
                from app.models.gb50300.nodes import BuildingNode
                building_id = f"building_default_{project_id}"
                building = BuildingNode(
                    id=building_id,
                    name="默认单体",
                    project_id=project_id
                )
                self.client.create_node("Building", building.model_dump(exclude_none=True))
                # 建立关系
                self.client.create_relationship(
                    "Project", project_id,
                    "Building", building_id,
                    PHYSICALLY_CONTAINS
                )
            
            # 创建默认 Level
            from app.models.gb50300.nodes import LevelNode
            level = LevelNode(
                id=default_level_id,
                name="默认楼层",
                elevation=0.0,
                building_id=building_id
            )
            self.client.create_node("Level", level.model_dump(exclude_none=True))
            # 建立关系
            self.client.create_relationship(
                "Building", building_id,
                "Level", default_level_id,
                PHYSICALLY_CONTAINS
            )
            
            logger.info(f"Created default level: {default_level_id}")
        
        return default_level_id
    
    def _store_element(self, element: ElementNode) -> None:
        """存储 Element 到 Memgraph
        
        Args:
            element: Element 节点
        """
        # 转换为属性字典
        props = element.to_cypher_properties()
        
        # 序列化 geometry
        if isinstance(props.get("geometry"), dict):
            # 已经是字典，直接使用
            pass
        elif hasattr(props.get("geometry"), "model_dump"):
            props["geometry"] = props["geometry"].model_dump()
        
        # 创建节点
        self.client.create_node("Element", props)
    
    def _create_relationships(
        self,
        element: ElementNode,
        project_id: str
    ) -> None:
        """创建 Element 的关系
        
        Args:
            element: Element 节点
            project_id: 项目 ID
        """
        # 1. 建立物理从属关系：Level -> Element (PHYSICALLY_CONTAINS)
        self.client.create_relationship(
            "Level", element.level_id,
            "Element", element.id,
            PHYSICALLY_CONTAINS
        )
        
        # 2. 建立位置关系：Element -> Level (LOCATED_AT)
        self.client.create_relationship(
            "Element", element.id,
            "Level", element.level_id,
            LOCATED_AT
        )
        
        # 3. 如果有 inspection_lot_id，建立管理从属关系：InspectionLot -> Element (MANAGEMENT_CONTAINS)
        if element.inspection_lot_id:
            # 验证 InspectionLot 是否存在
            query = "MATCH (lot:InspectionLot {id: $lot_id}) RETURN lot.id as id"
            result = self.client.execute_query(query, {"lot_id": element.inspection_lot_id})
            
            if result:
                self.client.create_relationship(
                    "InspectionLot", element.inspection_lot_id,
                    "Element", element.id,
                    MANAGEMENT_CONTAINS
                )
                logger.debug(f"Created MANAGEMENT_CONTAINS relationship: {element.inspection_lot_id} -> {element.id}")
            else:
                logger.warning(
                    f"InspectionLot not found: {element.inspection_lot_id} for element {element.id}. "
                    f"Skipping MANAGEMENT_CONTAINS relationship. "
                    f"The element will be treated as unassigned."
                )
        else:
            # 如果没有 inspection_lot_id，关联到 Unassigned Item
            # 这里我们需要找到 Unassigned Item 对应的 InspectionLot（如果有）
            # 否则，Element 暂时不关联到任何 InspectionLot
            # 在实际使用中，Editor 可以在工作台中手动分配
            pass

