"""用户管理服务

提供用户CRUD操作和密码验证功能
"""

import logging
import bcrypt
from typing import Optional
from datetime import datetime

from app.utils.memgraph import MemgraphClient, convert_neo4j_datetime
from app.models.gb50300.nodes import UserNode
from app.core.auth import UserRole

logger = logging.getLogger(__name__)


class UserService:
    """用户管理服务"""
    
    def __init__(self, client: Optional[MemgraphClient] = None):
        """初始化服务
        
        Args:
            client: Memgraph 客户端实例（如果为 None，将创建新实例）
        """
        self.client = client or MemgraphClient()
    
    def hash_password(self, password: str) -> str:
        """对密码进行bcrypt哈希
        
        Args:
            password: 明文密码
            
        Returns:
            str: 哈希后的密码
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """验证密码
        
        Args:
            password: 明文密码
            password_hash: 哈希后的密码
            
        Returns:
            bool: 验证是否通过
        """
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception as e:
            logger.error(f"Password verification failed: {e}")
            return False
    
    def create_user(
        self,
        username: str,
        password: str,
        role: UserRole,
        email: Optional[str] = None,
        name: Optional[str] = None
    ) -> UserNode:
        """创建用户
        
        Args:
            username: 用户名
            password: 明文密码（将被哈希存储）
            role: 用户角色
            email: 邮箱（可选）
            name: 姓名（可选）
            
        Returns:
            UserNode: 创建的用户节点
            
        Raises:
            ValueError: 如果用户名已存在
        """
        # 检查用户名是否已存在
        existing = self.get_user_by_username(username)
        if existing:
            raise ValueError(f"Username already exists: {username}")
        
        # 生成用户ID
        user_id = f"user_{username.lower().replace(' ', '_')}"
        
        # 哈希密码
        password_hash = self.hash_password(password)
        
        # 创建用户节点
        user_node = UserNode(
            id=user_id,
            username=username,
            email=email,
            password_hash=password_hash,
            role=role,
            name=name,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # 保存到Memgraph
        query = """
        CREATE (u:User {
            id: $id,
            username: $username,
            email: $email,
            password_hash: $password_hash,
            role: $role,
            name: $name,
            created_at: datetime(),
            updated_at: datetime()
        })
        RETURN u.id as id, u.username as username, u.email as email,
               u.password_hash as password_hash, u.role as role,
               u.name as name, u.created_at as created_at, u.updated_at as updated_at
        """
        
        params = {
            "id": user_node.id,
            "username": user_node.username,
            "email": user_node.email,
            "password_hash": user_node.password_hash,
            "role": user_node.role.value,
            "name": user_node.name,
        }
        
        result = self.client.execute_write(query, params)
        
        if not result:
            raise ValueError(f"Failed to create user: {username}")
        
        logger.info(f"Created user: {username} (role: {role.value})")
        return user_node
    
    def get_user_by_username(self, username: str) -> Optional[UserNode]:
        """根据用户名获取用户
        
        Args:
            username: 用户名
            
        Returns:
            Optional[UserNode]: 用户节点，如果不存在则返回 None
        """
        query = """
        MATCH (u:User {username: $username})
        RETURN u.id as id, u.username as username, u.email as email,
               u.password_hash as password_hash, u.role as role,
               u.name as name, u.created_at as created_at, u.updated_at as updated_at
        LIMIT 1
        """
        
        result = self.client.execute_query(query, {"username": username})
        
        if not result:
            return None
        
        user_data = result[0]
        return UserNode(
            id=user_data["id"],
            username=user_data["username"],
            email=user_data.get("email"),
            password_hash=user_data["password_hash"],
            role=UserRole(user_data["role"]),
            name=user_data.get("name"),
            created_at=convert_neo4j_datetime(user_data.get("created_at")) or datetime.now(),
            updated_at=convert_neo4j_datetime(user_data.get("updated_at")) or datetime.now()
        )
    
    def get_user_by_id(self, user_id: str) -> Optional[UserNode]:
        """根据用户ID获取用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            Optional[UserNode]: 用户节点，如果不存在则返回 None
        """
        query = """
        MATCH (u:User {id: $user_id})
        RETURN u.id as id, u.username as username, u.email as email,
               u.password_hash as password_hash, u.role as role,
               u.name as name, u.created_at as created_at, u.updated_at as updated_at
        LIMIT 1
        """
        
        result = self.client.execute_query(query, {"user_id": user_id})
        
        if not result:
            return None
        
        user_data = result[0]
        return UserNode(
            id=user_data["id"],
            username=user_data["username"],
            email=user_data.get("email"),
            password_hash=user_data["password_hash"],
            role=UserRole(user_data["role"]),
            name=user_data.get("name"),
            created_at=convert_neo4j_datetime(user_data.get("created_at")) or datetime.now(),
            updated_at=convert_neo4j_datetime(user_data.get("updated_at")) or datetime.now()
        )
    
    def authenticate_user(self, username: str, password: str) -> Optional[UserNode]:
        """验证用户凭据
        
        Args:
            username: 用户名
            password: 明文密码
            
        Returns:
            Optional[UserNode]: 如果验证通过返回用户节点，否则返回 None
        """
        user = self.get_user_by_username(username)
        if not user:
            return None
        
        if not self.verify_password(password, user.password_hash):
            return None
        
        return user

