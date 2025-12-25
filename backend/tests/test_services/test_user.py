"""UserService 测试"""

import pytest
from app.services.user import UserService
from app.utils.memgraph import MemgraphClient
from app.services.schema import initialize_schema


@pytest.fixture(scope="module")
def memgraph_client():
    """创建 Memgraph 客户端"""
    client = MemgraphClient()
    initialize_schema(client)
    return client


@pytest.fixture
def user_service(memgraph_client):
    """创建 UserService 实例"""
    return UserService(client=memgraph_client)


def test_verify_password(user_service):
    """测试密码验证"""
    # 测试正确的密码
    password = "test_password_123"
    hashed = user_service.hash_password(password)
    
    assert user_service.verify_password(password, hashed) is True
    
    # 测试错误的密码
    assert user_service.verify_password("wrong_password", hashed) is False


def test_hash_password(user_service):
    """测试密码哈希"""
    password = "test_password_123"
    hashed1 = user_service.hash_password(password)
    hashed2 = user_service.hash_password(password)
    
    # 两次哈希应该不同（因为使用了salt）
    assert hashed1 != hashed2
    
    # 但都能验证原始密码
    assert user_service.verify_password(password, hashed1) is True
    assert user_service.verify_password(password, hashed2) is True


def test_get_user_by_username(user_service):
    """测试通过用户名获取用户"""
    # 默认用户应该存在
    user = user_service.get_user_by_username("admin")
    
    assert user is not None
    assert user.username == "admin"
    assert user.role == "ADMIN"


def test_get_user_by_username_not_found(user_service):
    """测试获取不存在的用户"""
    user = user_service.get_user_by_username("nonexistent_user")
    
    assert user is None


def test_get_user_by_id(user_service):
    """测试通过ID获取用户"""
    # 先获取一个存在的用户
    user_by_username = user_service.get_user_by_username("admin")
    assert user_by_username is not None
    
    # 通过ID获取
    user_by_id = user_service.get_user_by_id(user_by_username.id)
    
    assert user_by_id is not None
    assert user_by_id.id == user_by_username.id
    assert user_by_id.username == user_by_username.username


def test_get_user_by_id_not_found(user_service):
    """测试获取不存在的用户ID"""
    user = user_service.get_user_by_id("nonexistent_id")
    
    assert user is None


def test_authenticate_user(user_service):
    """测试用户认证"""
    # 测试正确的用户名和密码
    user = user_service.authenticate_user("admin", "admin123")
    
    assert user is not None
    assert user.username == "admin"


def test_authenticate_user_wrong_password(user_service):
    """测试错误的密码认证"""
    user = user_service.authenticate_user("admin", "wrong_password")
    
    assert user is None


def test_authenticate_user_not_found(user_service):
    """测试不存在的用户认证"""
    user = user_service.authenticate_user("nonexistent_user", "password")
    
    assert user is None

