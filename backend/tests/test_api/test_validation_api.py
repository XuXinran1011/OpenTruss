"""测试校验API端点"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_validate_angle_valid():
    """测试角度验证API - 有效角度"""
    response = client.post(
        "/api/v1/validation/constructability/validate-angle",
        json={"angle": 90.0}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["valid"] is True
    assert data["data"]["snapped_angle"] == 90.0


def test_validate_angle_invalid():
    """测试角度验证API - 无效角度"""
    response = client.post(
        "/api/v1/validation/constructability/validate-angle",
        json={"angle": 100.0}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    # 100度不在标准角度范围内（45, 90, 180），应该无效
    assert data["data"]["valid"] is False


def test_validate_z_axis_complete():
    """测试Z轴完整性验证API - 完整"""
    response = client.post(
        "/api/v1/validation/constructability/validate-z-axis",
        json={
            "element": {
                "id": "wall_001",
                "speckle_type": "Wall",
                "height": 3.0,
                "base_offset": 0.0,
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["valid"] is True


def test_validate_z_axis_incomplete():
    """测试Z轴完整性验证API - 不完整"""
    response = client.post(
        "/api/v1/validation/constructability/validate-z-axis",
        json={
            "element": {
                "id": "wall_001",
                "speckle_type": "Wall",
                "height": 3.0,
                # 缺少 base_offset
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["valid"] is False
    assert len(data["data"]["errors"]) > 0


def test_calculate_path_angle():
    """测试路径角度计算API"""
    response = client.post(
        "/api/v1/validation/constructability/calculate-path-angle",
        json={
            "path": [[0, 0], [10, 0]]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "angle" in data["data"]
    assert isinstance(data["data"]["angle"], (int, float))


def test_validate_topology_nonexistent_lot():
    """测试拓扑验证API - 不存在的检验批"""
    response = client.post(
        "/api/v1/validation/topology/validate",
        json={"lot_id": "nonexistent_lot_id"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    # 不存在的检验批应该返回有效（因为没有元素需要验证）
    assert data["data"]["valid"] is True


def test_find_open_ends_empty():
    """测试查找悬空端点API - 空列表"""
    response = client.post(
        "/api/v1/validation/topology/find-open-ends",
        json={"element_ids": []}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["element_ids"] == []


def test_find_isolated_empty():
    """测试查找孤立元素API - 空列表"""
    response = client.post(
        "/api/v1/validation/topology/find-isolated",
        json={"element_ids": []}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["element_ids"] == []

