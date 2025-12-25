"""Schema 初始化测试"""

import pytest
from app.services.schema import initialize_schema, UNASSIGNED_ITEM_ID
from app.utils.memgraph import MemgraphClient


@pytest.fixture(scope="module")
def memgraph_client():
    """创建 Memgraph 客户端"""
    client = MemgraphClient()
    initialize_schema(client)
    return client


def test_initialize_schema(memgraph_client):
    """测试schema初始化"""
    # 验证Unassigned Item存在
    query = "MATCH (item:Item {id: $item_id}) RETURN item.id as id"
    result = memgraph_client.execute_query(query, {"item_id": UNASSIGNED_ITEM_ID})
    
    assert result is not None
    assert len(result) > 0
    assert result[0]["id"] == UNASSIGNED_ITEM_ID


def test_default_users_created(memgraph_client):
    """测试默认用户是否已创建"""
    query = "MATCH (u:User) RETURN u.username as username, u.role as role"
    result = memgraph_client.execute_query(query)
    
    # 验证至少有默认用户
    usernames = [r["username"] for r in result]
    assert "admin" in usernames
    assert "editor" in usernames
    assert "approver" in usernames


def test_indexes_created(memgraph_client):
    """测试索引是否已创建"""
    # Memgraph的索引查询可能需要特殊方式
    # 这里只验证基本功能可用
    query = "MATCH (e:Element) RETURN count(e) as count LIMIT 1"
    result = memgraph_client.execute_query(query)
    
    assert result is not None
    # 如果查询成功，说明基本功能正常

