"""Schema 初始化服务

负责初始化 Memgraph 数据库 Schema，包括创建索引和默认节点
"""

import logging
from typing import Optional

from app.utils.memgraph import MemgraphClient
from app.models.gb50300.nodes import ItemNode
from app.models.gb50300.relationships import PHYSICALLY_CONTAINS, MANAGEMENT_CONTAINS
from app.services.user import UserService
from app.core.auth import UserRole

logger = logging.getLogger(__name__)

# Unassigned Item 的固定 ID
UNASSIGNED_ITEM_ID = "unassigned_item"


def initialize_schema(client: Optional[MemgraphClient] = None, create_default_users: bool = True) -> None:
    """初始化 Schema
    
    创建所有必要的索引和默认节点（如 Unassigned Item）
    
    Args:
        client: Memgraph 客户端实例（如果为 None，将创建新实例）
        create_default_users: 是否创建默认用户
    """
    if client is None:
        client = MemgraphClient()
    
    logger.info("Initializing OpenTruss schema...")
    
    try:
        # 创建索引
        _create_indexes(client)
        
        # 创建 Unassigned Item（如果不存在）
        _ensure_unassigned_item(client)
        
        # 创建默认用户（如果启用）
        if create_default_users:
            _create_default_users(client)
        
        logger.info("Schema initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Schema initialization failed: {e}")
        raise


def _create_indexes(client: MemgraphClient) -> None:
    """创建所有必要的索引
    
    参考 docs/SCHEMA.md 4.1 节
    """
    indexes = [
        # Project 索引
        ("Project", "id"),
        ("Project", "name"),
        
        # Building 索引
        ("Building", "id"),
        ("Building", "project_id"),
        
        # Division 索引
        ("Division", "id"),
        ("Division", "building_id"),
        
        # SubDivision 索引
        ("SubDivision", "id"),
        ("SubDivision", "division_id"),
        
        # Item 索引
        ("Item", "id"),
        ("Item", "sub_division_id"),
        
        # InspectionLot 索引
        ("InspectionLot", "id"),
        ("InspectionLot", "item_id"),
        ("InspectionLot", "status"),
        
        # Element 索引
        ("Element", "id"),
        ("Element", "speckle_type"),
        ("Element", "level_id"),
        ("Element", "inspection_lot_id"),
        ("Element", "status"),
        # Element 复合索引（优化常用查询组合）
        # 注意：Memgraph可能不支持复合索引，这里先记录，实际使用时需要验证
        
        # Level 索引
        ("Level", "id"),
        ("Level", "building_id"),
        
        # Zone 索引
        ("Zone", "id"),
        ("Zone", "level_id"),
        
        # System 索引
        ("System", "id"),
        ("System", "building_id"),
        
        # SubSystem 索引
        ("SubSystem", "id"),
        ("SubSystem", "system_id"),
    ]
    
    for label, property_name in indexes:
        try:
            # 尝试创建索引（如果已存在会忽略）
            query = f"CREATE INDEX ON :{label}({property_name})"
            client.execute_write(query)
            logger.debug(f"Created index: :{label}({property_name})")
        except Exception as e:
            # 索引可能已存在，忽略错误
            logger.debug(f"Index :{label}({property_name}) may already exist: {e}")


def _ensure_unassigned_item(client: MemgraphClient) -> None:
    """确保 Unassigned Item 节点存在
    
    如果不存在，则创建它
    """
    # 检查是否存在
    query = "MATCH (i:Item {id: $id}) RETURN i.id as id"
    result = client.execute_query(query, {"id": UNASSIGNED_ITEM_ID})
    
    if not result:
        # 创建 Unassigned Item
        # 注意：Unassigned Item 需要关联到一个 SubDivision
        # 这里我们创建一个临时的 Unassigned SubDivision（如果不存在）
        _ensure_unassigned_subdivision(client)
        
        # 查询 Unassigned SubDivision ID
        subdiv_query = "MATCH (sd:SubDivision {id: 'unassigned_subdivision'}) RETURN sd.id as id"
        subdiv_result = client.execute_query(subdiv_query)
        
        if subdiv_result:
            subdiv_id = subdiv_result[0]["id"]
        else:
            # 如果还是没有，使用一个占位 ID（这不应该发生）
            logger.warning("Unassigned SubDivision not found, using placeholder")
            subdiv_id = "unassigned_subdivision"
        
        # 创建 Unassigned Item 节点
        item = ItemNode(
            id=UNASSIGNED_ITEM_ID,
            name="未分配构件",
            sub_division_id=subdiv_id
        )
        
        props = item.model_dump(exclude_none=True)
        client.create_node("Item", props)
        logger.info(f"Created Unassigned Item: {UNASSIGNED_ITEM_ID}")
    else:
        logger.debug(f"Unassigned Item already exists: {UNASSIGNED_ITEM_ID}")


def _ensure_unassigned_subdivision(client: MemgraphClient) -> None:
    """确保 Unassigned SubDivision 节点存在（用于 Unassigned Item）
    
    如果不存在，则创建它及其上级节点
    """
    # 检查是否存在
    query = "MATCH (sd:SubDivision {id: 'unassigned_subdivision'}) RETURN sd.id as id"
    result = client.execute_query(query)
    
    if not result:
        # 需要创建上级节点（Division, Building, Project）
        # 这里我们创建一个默认的"未分配"层级结构
        
        # 先确保 Project 存在
        project_query = "MATCH (p:Project {id: 'default_project'}) RETURN p.id as id"
        project_result = client.execute_query(project_query)
        
        if not project_result:
            from app.models.gb50300.nodes import ProjectNode
            project = ProjectNode(
                id="default_project",
                name="默认项目",
                description="用于未分配构件的默认项目"
            )
            client.create_node("Project", project.model_dump(exclude_none=True))
        
        # 确保 Building 存在
        building_query = "MATCH (b:Building {id: 'default_building'}) RETURN b.id as id"
        building_result = client.execute_query(building_query)
        
        if not building_result:
            from app.models.gb50300.nodes import BuildingNode
            building = BuildingNode(
                id="default_building",
                name="默认单体",
                project_id="default_project"
            )
            client.create_node("Building", building.model_dump(exclude_none=True))
            # 建立关系
            client.create_relationship(
                "Project", "default_project",
                "Building", "default_building",
                PHYSICALLY_CONTAINS
            )
        
        # 确保 Division 存在
        division_query = "MATCH (d:Division {id: 'default_division'}) RETURN d.id as id"
        division_result = client.execute_query(division_query)
        
        if not division_result:
            from app.models.gb50300.nodes import DivisionNode
            division = DivisionNode(
                id="default_division",
                name="默认分部",
                building_id="default_building"
            )
            client.create_node("Division", division.model_dump(exclude_none=True))
            # 建立关系
            client.create_relationship(
                "Building", "default_building",
                "Division", "default_division",
                MANAGEMENT_CONTAINS
            )
        
        # 创建 SubDivision
        from app.models.gb50300.nodes import SubDivisionNode
        subdivision = SubDivisionNode(
            id="unassigned_subdivision",
            name="未分配子分部",
            division_id="default_division"
        )
        client.create_node("SubDivision", subdivision.model_dump(exclude_none=True))
        # 建立关系
        client.create_relationship(
            "Division", "default_division",
            "SubDivision", "unassigned_subdivision",
            MANAGEMENT_CONTAINS
        )
        
        logger.info("Created default hierarchy for unassigned items")


def _create_default_users(client: MemgraphClient) -> None:
    """创建默认用户"""
    user_service = UserService(client=client)
    
    # 默认管理员用户
    default_users = [
        {
            "username": "admin",
            "password": "admin123",
            "role": UserRole.ADMIN,
            "email": "admin@opentruss.com",
            "name": "系统管理员"
        },
        {
            "username": "editor",
            "password": "editor123",
            "role": UserRole.EDITOR,
            "email": "editor@opentruss.com",
            "name": "数据清洗工程师"
        },
        {
            "username": "approver",
            "password": "approver123",
            "role": UserRole.APPROVER,
            "email": "approver@opentruss.com",
            "name": "专业负责人"
        },
        {
            "username": "pm",
            "password": "pm123",
            "role": UserRole.PM,
            "email": "pm@opentruss.com",
            "name": "项目经理"
        }
    ]
    
    for user_data in default_users:
        try:
            # 检查用户是否已存在
            existing = user_service.get_user_by_username(user_data["username"])
            if not existing:
                user_service.create_user(**user_data)
                logger.info(f"Created default user: {user_data['username']} (role: {user_data['role'].value})")
            else:
                logger.debug(f"Default user already exists: {user_data['username']}")
        except Exception as e:
            logger.warning(f"Failed to create default user {user_data['username']}: {e}")

