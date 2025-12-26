"""Memgraph 连接工具

封装 Memgraph 数据库连接和查询操作
"""

from typing import List, Dict, Any, Optional
import logging
from contextlib import contextmanager
from datetime import datetime

try:
    from neo4j import GraphDatabase
    from neo4j.exceptions import ServiceUnavailable, TransientError
    import neo4j.time
except ImportError:
    raise ImportError(
        "neo4j is required. Install it with: pip install neo4j"
    )

from app.core.config import settings
from app.core.metrics import record_memgraph_query
import time

logger = logging.getLogger(__name__)


def convert_neo4j_datetime(value: Any) -> Optional[datetime]:
    """将 neo4j DateTime 对象转换为 Python datetime 对象
    
    Args:
        value: neo4j DateTime 对象或 Python datetime 对象
        
    Returns:
        Optional[datetime]: Python datetime 对象，如果输入为 None 则返回 None
    """
    if value is None:
        return None
    
    # 如果已经是 Python datetime，直接返回
    if isinstance(value, datetime):
        return value
    
    # 如果是 neo4j DateTime 对象，转换为 Python datetime
    if hasattr(value, 'to_native'):
        return value.to_native()
    
    # 如果是 neo4j.time.DateTime，尝试转换为 Python datetime
    if isinstance(value, neo4j.time.DateTime):
        return datetime(
            year=value.year,
            month=value.month,
            day=value.day,
            hour=value.hour,
            minute=value.minute,
            second=value.second,
            microsecond=value.nanosecond // 1000 if hasattr(value, 'nanosecond') else 0
        )
    
    # 其他类型，尝试直接返回（可能已经是 datetime）
    return value


class MemgraphClient:
    """Memgraph 客户端
    
    封装 Memgraph 数据库连接和查询操作
    """
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """初始化 Memgraph 客户端
        
        Args:
            host: Memgraph 主机地址（默认从配置读取）
            port: Memgraph 端口（默认从配置读取）
            user: Memgraph 用户名（默认从配置读取）
            password: Memgraph 密码（默认从配置读取）
        """
        self.host = host or settings.memgraph_host
        self.port = port or settings.memgraph_port
        self.user = user or settings.memgraph_user
        self.password = password or settings.memgraph_password
        
        # 创建 Memgraph 连接（使用 Neo4j 驱动，因为 Memgraph 兼容 Neo4j Bolt 协议）
        self._driver: Optional[GraphDatabase.driver] = None
        self._connect()
    
    def _connect(self):
        """建立 Memgraph 连接"""
        try:
            # 构建连接 URI
            uri = f"bolt://{self.host}:{self.port}"
            
            # 创建驱动（使用 Neo4j 驱动连接 Memgraph）
            # 优化：配置连接池参数，提高连接复用效率
            driver_config = {
                "max_connection_lifetime": self._max_connection_lifetime,
                "max_connection_pool_size": self._max_connection_pool_size,
                "connection_acquisition_timeout": self._connection_acquisition_timeout,
            }
            
            if self.user and self.password:
                self._driver = GraphDatabase.driver(
                    uri,
                    auth=(self.user, self.password),
                    **driver_config
                )
            else:
                # 无认证连接（Memgraph 默认无认证）
                self._driver = GraphDatabase.driver(uri, **driver_config)
            
            # 测试连接
            with self._driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
            
            logger.info(f"Connected to Memgraph at {self.host}:{self.port}")
            
        except ServiceUnavailable as e:
            logger.error(f"Failed to connect to Memgraph: {e}")
            raise ConnectionError(f"Cannot connect to Memgraph at {self.host}:{self.port}") from e
        except Exception as e:
            logger.error(f"Unexpected error connecting to Memgraph: {e}")
            raise
    
    def _extract_query_type(self, query: str) -> str:
        """从查询语句中提取查询类型
        
        Args:
            query: Cypher 查询语句
            
        Returns:
            str: 查询类型（如 'MATCH', 'CREATE', 'UPDATE' 等）
        """
        query_upper = query.strip().upper()
        if query_upper.startswith('MATCH'):
            return 'MATCH'
        elif query_upper.startswith('CREATE'):
            return 'CREATE'
        elif query_upper.startswith('MERGE'):
            return 'MERGE'
        elif query_upper.startswith('SET') or query_upper.startswith('UPDATE'):
            return 'UPDATE'
        elif query_upper.startswith('DELETE') or query_upper.startswith('DETACH DELETE'):
            return 'DELETE'
        elif query_upper.startswith('RETURN'):
            return 'RETURN'
        else:
            return 'OTHER'
    
    def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """执行查询操作（只读）
        
        Args:
            query: Cypher 查询语句
            parameters: 查询参数
            
        Returns:
            List[Dict]: 查询结果列表
            
        Raises:
            ConnectionError: 连接失败
            Exception: 查询执行失败
        """
        if not self._driver:
            self._connect()
        
        query_type = self._extract_query_type(query)
        start_time = time.time()
        success = True
        
        try:
            with self._driver.session() as session:
                if parameters:
                    result = session.run(query, parameters)
                else:
                    result = session.run(query)
                
                # 转换为字典列表
                results = [dict(record) for record in result]
                
                duration = time.time() - start_time
                record_memgraph_query(query_type, duration, success=True)
                
                return results
            
        except (ServiceUnavailable, TransientError) as e:
            success = False
            duration = time.time() - start_time
            record_memgraph_query(query_type, duration, success=False)
            logger.error(f"Memgraph connection error: {e}")
            # 尝试重连
            self._connect()
            raise ConnectionError(f"Memgraph connection lost: {e}") from e
        except Exception as e:
            success = False
            duration = time.time() - start_time
            record_memgraph_query(query_type, duration, success=False)
            logger.error(f"Query execution failed: {e}\nQuery: {query}\nParameters: {parameters}")
            raise
    
    def execute_write(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行写入操作（CREATE, UPDATE, DELETE）
        
        Args:
            query: Cypher 写入语句
            parameters: 查询参数
            
        Returns:
            Dict: 执行结果（通常包含统计信息）
            
        Raises:
            ConnectionError: 连接失败
            Exception: 写入执行失败
        """
        if not self._driver:
            self._connect()
        
        query_type = self._extract_query_type(query)
        start_time = time.time()
        success = True
        
        try:
            with self._driver.session() as session:
                if parameters:
                    result = session.run(query, parameters)
                else:
                    result = session.run(query)
                
                # 消费结果（写入操作需要消费结果才能提交）
                result.consume()
            
            duration = time.time() - start_time
            record_memgraph_query(query_type, duration, success=True)
            
            # 返回统计信息
            return {"status": "success"}
            
        except (ServiceUnavailable, TransientError) as e:
            success = False
            duration = time.time() - start_time
            record_memgraph_query(query_type, duration, success=False)
            logger.error(f"Memgraph connection error: {e}")
            self._connect()
            raise ConnectionError(f"Memgraph connection lost: {e}") from e
        except Exception as e:
            success = False
            duration = time.time() - start_time
            record_memgraph_query(query_type, duration, success=False)
            logger.error(f"Write execution failed: {e}\nQuery: {query}\nParameters: {parameters}")
            raise
    
    @contextmanager
    def transaction(self):
        """事务上下文管理器
        
        使用示例:
            with client.transaction() as tx:
                tx.execute_write("CREATE (n:Node {id: $id})", {"id": "123"})
                tx.execute_write("CREATE (m:Node {id: $id})", {"id": "456"})
        """
        # Memgraph 的 pymemgraph 库可能不支持显式事务
        # 如果需要事务支持，可能需要使用 neo4j 驱动
        # 这里提供一个占位实现
        yield self
    
    def create_node(
        self,
        label: str,
        properties: Dict[str, Any],
        return_id: bool = True
    ) -> Optional[str]:
        """创建节点
        
        Args:
            label: 节点标签（如 "Project", "Building"）
            properties: 节点属性
            return_id: 是否返回节点 ID
            
        Returns:
            Optional[str]: 节点 ID（如果 return_id=True）
        """
        # 构建属性字符串
        props_str = ", ".join([f"{k}: ${k}" for k in properties.keys()])
        
        # 如果 return_id 且 properties 中有 id，直接返回
        if return_id and "id" in properties:
            # 使用 execute_query 执行带返回的 CREATE
            query = f"CREATE (n:{label} {{{props_str}}}) RETURN n.id as id"
            result = self.execute_query(query, properties)
            if result:
                return result[0].get("id")
            return properties.get("id")
        
        # 否则只执行创建，不返回
        query = f"CREATE (n:{label} {{{props_str}}})"
        self.execute_write(query, properties)
        
        # 如果有 id 属性，直接返回
        if return_id and "id" in properties:
            return properties["id"]
        
        return None
    
    def create_relationship(
        self,
        start_label: str,
        start_id: str,
        end_label: str,
        end_id: str,
        rel_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> None:
        """创建关系
        
        Args:
            start_label: 起始节点标签
            start_id: 起始节点 ID
            end_label: 结束节点标签
            end_id: 结束节点 ID
            rel_type: 关系类型（字符串或 RelationshipType 枚举）
            properties: 关系属性（可选）
        """
        # 处理 RelationshipType 枚举
        if hasattr(rel_type, "value"):
            rel_type_str = rel_type.value
        else:
            rel_type_str = str(rel_type)
        
        rel_props = ""
        params = {"start_id": start_id, "end_id": end_id}
        
        if properties:
            rel_props = " {" + ", ".join([f"{k}: ${k}" for k in properties.keys()]) + "}"
            params.update(properties)
        
        query = (
            f"MATCH (a:{start_label} {{id: $start_id}}), "
            f"(b:{end_label} {{id: $end_id}}) "
            f"CREATE (a)-[:{rel_type_str}{rel_props}]->(b)"
        )
        
        self.execute_write(query, params)
    
    def close(self):
        """关闭连接"""
        if self._driver:
            self._driver.close()
            self._driver = None
            logger.info("Memgraph connection closed")


# 全局客户端实例（可选，用于依赖注入）
_memgraph_client: Optional[MemgraphClient] = None


def get_memgraph_client() -> MemgraphClient:
    """获取 Memgraph 客户端实例（单例模式）
    
    Returns:
        MemgraphClient: Memgraph 客户端实例
    """
    global _memgraph_client
    if _memgraph_client is None:
        _memgraph_client = MemgraphClient()
    return _memgraph_client

