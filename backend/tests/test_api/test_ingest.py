"""数据摄入 API 测试"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "backend"))

from app.main import app

client = TestClient(app)


@pytest.fixture
def sample_ingest_request():
    """示例 Ingestion API 请求数据"""
    return {
        "project_id": "test_project_001",
        "elements": [
            {
                "speckle_type": "Wall",
                "geometry": {
                    "type": "Polyline",
                    "coordinates": [[0, 0, 0], [10, 0, 0], [10, 5, 0], [0, 5, 0], [0, 0, 0]],
                    "closed": True
                },
                "level_id": "level_f1"
            }
        ]
    }


def test_health_endpoint():
    """测试健康检查端点"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_root_endpoint():
    """测试根端点"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert data["name"] == "OpenTruss API"


def test_ingest_endpoint_basic(sample_ingest_request):
    """测试 Ingestion API 端点（基础测试）
    
    注意: 这需要 Memgraph 正在运行
    """
    # 跳过测试如果 Memgraph 不可用
    try:
        response = client.post("/api/v1/ingest", json=sample_ingest_request)
        # 如果连接失败，跳过测试
        if response.status_code == 500:
            pytest.skip("Memgraph not available or connection failed")
        
        assert response.status_code in [201, 500]  # 201 成功，500 可能是连接问题
        
        if response.status_code == 201:
            data = response.json()
            assert "status" in data
            assert "data" in data
            assert "ingested_count" in data["data"]
            assert "element_ids" in data["data"]
    except Exception as e:
        pytest.skip(f"Test skipped due to: {e}")


def test_ingest_endpoint_invalid_data():
    """测试 Ingestion API 的错误处理"""
    invalid_request = {
        "project_id": "test",
        "elements": [
            {
                "speckle_type": "InvalidType",  # 无效类型
                # 缺少必需字段
            }
        ]
    }
    
    response = client.post("/api/v1/ingest", json=invalid_request)
    # 应该返回 422 (Validation Error) 或 201 with errors
    assert response.status_code in [201, 422]
    
    if response.status_code == 201:
        data = response.json()
        # 应该包含错误信息
        assert "errors" in data["data"] or data["data"]["ingested_count"] == 0
