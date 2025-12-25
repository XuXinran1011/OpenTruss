"""认证 API 测试"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_login_success():
    """测试登录成功"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "admin",
            "password": "admin123"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "data" in data
    assert "access_token" in data["data"]
    assert "user" in data["data"]
    assert data["data"]["user"]["username"] == "admin"
    assert data["data"]["user"]["role"] == "ADMIN"


def test_login_wrong_password():
    """测试错误的密码"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "admin",
            "password": "wrong_password"
        }
    )
    
    assert response.status_code == 401


def test_login_user_not_found():
    """测试不存在的用户"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "nonexistent_user",
            "password": "password"
        }
    )
    
    assert response.status_code == 401


def test_login_missing_fields():
    """测试缺少字段"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "admin"
            # 缺少 password
        }
    )
    
    assert response.status_code == 422  # Validation error


def test_get_current_user():
    """测试获取当前用户信息"""
    # 先登录获取token
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "admin",
            "password": "admin123"
        }
    )
    
    assert login_response.status_code == 200
    token = login_response.json()["data"]["access_token"]
    
    # 使用token获取用户信息
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "data" in data
    assert data["data"]["username"] == "admin"
    assert data["data"]["role"] == "ADMIN"


def test_get_current_user_no_token():
    """测试未提供token"""
    response = client.get("/api/v1/auth/me")
    
    assert response.status_code == 401  # Unauthorized (FastAPI HTTPBearer 返回 401)


def test_get_current_user_invalid_token():
    """测试无效的token"""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_token_12345"}
    )
    
    assert response.status_code == 401  # Unauthorized


def test_logout():
    """测试登出"""
    # 先登录获取token
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "admin",
            "password": "admin123"
        }
    )
    
    assert login_response.status_code == 200
    token = login_response.json()["data"]["access_token"]
    
    # 登出
    response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # 登出通常返回200（即使没有实际的后端状态管理）
    assert response.status_code in [200, 204]

