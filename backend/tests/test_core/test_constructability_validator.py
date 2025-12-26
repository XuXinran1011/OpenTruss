"""测试构造校验器（规则引擎 Phase 2）"""

import pytest
from pathlib import Path
from app.core.validators import ConstructabilityValidator


def test_snap_angle_standard():
    """测试角度吸附到标准角度"""
    validator = ConstructabilityValidator()
    
    # 应该吸附到90度（容差5度内）
    assert validator.snap_angle(88.0) == 90.0
    assert validator.snap_angle(92.0) == 90.0
    assert validator.snap_angle(90.0) == 90.0
    
    # 应该吸附到45度
    assert validator.snap_angle(46.0) == 45.0
    assert validator.snap_angle(44.0) == 45.0
    
    # 应该吸附到180度
    assert validator.snap_angle(178.0) == 180.0


def test_snap_angle_out_of_tolerance():
    """测试超出容差的角度"""
    validator = ConstructabilityValidator()
    
    # 超出容差的角度应该返回None
    assert validator.snap_angle(100.0) is None  # 100度不在标准角度±5度范围内
    assert validator.snap_angle(30.0) is None  # 30度不在标准角度±5度范围内


def test_validate_angle_valid():
    """测试角度验证 - 有效角度"""
    validator = ConstructabilityValidator()
    
    result = validator.validate_angle(90.0)
    assert result["valid"] is True
    assert result["snapped_angle"] == 90.0
    assert result["error"] is None


def test_validate_angle_invalid():
    """测试角度验证 - 无效角度（不允许自定义）"""
    validator = ConstructabilityValidator()
    
    result = validator.validate_angle(100.0)
    assert result["valid"] is False
    assert result["snapped_angle"] is None
    assert result["error"] is not None


def test_validate_z_axis_completeness_wall_complete():
    """测试Z轴完整性验证 - Wall完整"""
    validator = ConstructabilityValidator()
    
    element = {
        "id": "wall_001",
        "speckle_type": "Wall",
        "height": 3.0,
        "base_offset": 0.0,
    }
    
    result = validator.validate_z_axis_completeness(element)
    assert result["valid"] is True
    assert len(result["errors"]) == 0


def test_validate_z_axis_completeness_wall_missing_height():
    """测试Z轴完整性验证 - Wall缺少height"""
    validator = ConstructabilityValidator()
    
    element = {
        "id": "wall_001",
        "speckle_type": "Wall",
        "base_offset": 0.0,
    }
    
    result = validator.validate_z_axis_completeness(element)
    assert result["valid"] is False
    assert len(result["errors"]) > 0
    assert "height" in result["errors"][0].lower()


def test_validate_z_axis_completeness_wall_missing_base_offset():
    """测试Z轴完整性验证 - Wall缺少base_offset"""
    validator = ConstructabilityValidator()
    
    element = {
        "id": "wall_001",
        "speckle_type": "Wall",
        "height": 3.0,
    }
    
    result = validator.validate_z_axis_completeness(element)
    assert result["valid"] is False
    assert len(result["errors"]) > 0
    assert "base_offset" in result["errors"][0].lower()


def test_validate_z_axis_completeness_non_required_type():
    """测试Z轴完整性验证 - 不需要Z轴的元素类型"""
    validator = ConstructabilityValidator()
    
    element = {
        "id": "pipe_001",
        "speckle_type": "Pipe",
    }
    
    result = validator.validate_z_axis_completeness(element)
    assert result["valid"] is True  # Pipe不在要求Z轴完整性的类型列表中


def test_calculate_path_angle():
    """测试路径角度计算"""
    validator = ConstructabilityValidator()
    
    # 水平路径（0度）
    path = [[0, 0], [10, 0]]
    angle = validator.calculate_path_angle(path)
    assert abs(angle - 0.0) < 0.1
    
    # 垂直路径（90度）
    path = [[0, 0], [0, 10]]
    angle = validator.calculate_path_angle(path)
    assert abs(angle - 90.0) < 0.1
    
    # 45度路径
    path = [[0, 0], [10, 10]]
    angle = validator.calculate_path_angle(path)
    assert abs(angle - 45.0) < 0.1

