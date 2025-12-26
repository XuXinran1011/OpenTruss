"""测试规则管理API端点"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_rules():
    """测试获取规则列表API"""
    response = client.get("/api/v1/rules")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "rules" in data["data"]
    assert isinstance(data["data"]["rules"], list)
    assert len(data["data"]["rules"]) > 0
    
    # 验证规则结构
    rule = data["data"]["rules"][0]
    assert "rule_type" in rule
    assert "name" in rule
    assert "description" in rule


def test_preview_rule_nonexistent_item():
    """测试规则预览API - 不存在的Item"""
    response = client.post(
        "/api/v1/rules/preview",
        json={
            "rule_type": "BY_LEVEL",
            "item_id": "nonexistent_item_id"
        }
    )
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_preview_rule_invalid_request():
    """测试规则预览API - 无效请求"""
    response = client.post(
        "/api/v1/rules/preview",
        json={
            "rule_type": "INVALID_RULE_TYPE",
            "item_id": "item_001"
        }
    )
    # 应该返回422（验证错误）或400（请求错误）
    assert response.status_code in [400, 422]

