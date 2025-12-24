"""测试数据生成器

包含测试用的示例数据
"""

from typing import Dict, Any, List


def get_sample_wall_element() -> Dict[str, Any]:
    """获取示例 Wall 元素数据"""
    return {
        "speckle_type": "Wall",
        "geometry_2d": {
            "type": "Polyline",
            "coordinates": [[0, 0], [10, 0], [10, 5], [0, 5], [0, 0]],
            "closed": True
        },
        "level_id": "level_f1",
        "speckle_id": "speckle_wall_test_001",
    }


def get_sample_beam_element() -> Dict[str, Any]:
    """获取示例 Beam 元素数据"""
    return {
        "speckle_type": "Beam",
        "geometry_2d": {
            "type": "Line",
            "coordinates": [[0, 0], [10, 0]],
        },
        "level_id": "level_f1",
        "height": 0.5,
        "material": "concrete",
    }


def get_sample_column_element() -> Dict[str, Any]:
    """获取示例 Column 元素数据"""
    return {
        "speckle_type": "Column",
        "geometry_2d": {
            "type": "Polyline",
            "coordinates": [[0, 0], [0.5, 0], [0.5, 0.5], [0, 0.5], [0, 0]],
            "closed": True
        },
        "level_id": "level_f1",
        "height": 3.0,
        "base_offset": 0.0,
    }


def get_sample_ingest_request() -> Dict[str, Any]:
    """获取示例 Ingestion API 请求数据"""
    return {
        "project_id": "test_project_001",
        "elements": [
            get_sample_wall_element(),
            get_sample_beam_element(),
            get_sample_column_element(),
        ]
    }


def get_sample_unassigned_element() -> Dict[str, Any]:
    """获取未分配的构件（无 inspection_lot_id）"""
    return {
        "speckle_type": "Wall",
        "geometry_2d": {
            "type": "Polyline",
            "coordinates": [[0, 0], [5, 0], [5, 3], [0, 3], [0, 0]],
            "closed": True
        },
        "level_id": "level_f1",
        # 没有 inspection_lot_id，应该关联到 Unassigned Item
    }


def get_sample_invalid_element() -> Dict[str, Any]:
    """获取无效的元素数据（用于错误处理测试）"""
    return {
        "speckle_type": "InvalidType",  # 无效的类型
        # 缺少必需字段
    }


def sample_inspection_lot(
    lot_id: str = "test_lot_001",
    name: str = "测试检验批",
    status: str = "SUBMITTED",
    item_id: str = "test_item_001"
) -> Dict[str, Any]:
    """创建测试用的检验批数据"""
    from datetime import datetime
    return {
        "id": lot_id,
        "name": name,
        "status": status,
        "item_id": item_id,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }


def sample_approval_request(comment: str = "验收通过") -> Dict[str, Any]:
    """创建审批请求数据"""
    return {
        "comment": comment
    }


def sample_reject_request(
    reason: str = "需要补充资料",
    reject_level: str = "IN_PROGRESS"
) -> Dict[str, Any]:
    """创建驳回请求数据"""
    return {
        "reason": reason,
        "reject_level": reject_level
    }


def sample_element_with_geometry(
    element_id: str = "test_element_001",
    speckle_type: str = "Wall",
    height: float = 3.0,
    base_offset: float = 0.0
) -> Dict[str, Any]:
    """创建带几何数据的构件数据"""
    from datetime import datetime
    from app.models.speckle.base import Geometry2D
    
    geometry_2d = Geometry2D(
        type="Polyline",
        coordinates=[[0.0, 0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0], [0.0, 0.0]],
        closed=True
    )
    
    return {
        "id": element_id,
        "speckle_id": f"speckle_{element_id}",
        "speckle_type": speckle_type,
        "geometry_2d": geometry_2d,
        "height": height,
        "base_offset": base_offset,
        "status": "APPROVED",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

