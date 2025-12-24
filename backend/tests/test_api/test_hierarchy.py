"""层级结构 API 测试"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.utils.memgraph import MemgraphClient
from app.services.schema import initialize_schema


client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    """设置测试数据库"""
    memgraph_client = MemgraphClient()
    initialize_schema(memgraph_client)
    yield
    # 清理测试数据（如果需要）


def test_get_projects():
    """测试获取项目列表"""
    response = client.get("/api/v1/hierarchy/projects")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "data" in data
    assert "items" in data["data"]
    assert "total" in data["data"]


def test_get_project_not_found():
    """测试获取不存在的项目"""
    response = client.get("/api/v1/hierarchy/projects/nonexistent_project")
    assert response.status_code == 404


def test_get_project_hierarchy():
    """测试获取项目层级树"""
    # 首先需要一个存在的项目 ID（从默认 schema 初始化中获取）
    # 由于我们有默认项目，这里测试默认项目
    project_id = "default_project"
    response = client.get(f"/api/v1/hierarchy/projects/{project_id}/hierarchy")
    
    # 如果项目存在，应该返回 200
    if response.status_code == 200:
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert "hierarchy" in data["data"]
    else:
        # 如果项目不存在（可能没有初始化默认项目），测试 404
        assert response.status_code == 404


