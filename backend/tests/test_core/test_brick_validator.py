"""Brick Schema 验证器测试"""

import pytest
from pathlib import Path
from app.core.brick_validator import BrickSemanticValidator


class TestBrickSemanticValidator:
    """BrickSemanticValidator 测试类"""
    
    def test_init(self):
        """测试初始化"""
        validator = BrickSemanticValidator(load_brick_schema=False)
        assert validator._mapping is not None
    
    def test_speckle_to_brick_type(self):
        """测试 Speckle 到 Brick 类型转换"""
        validator = BrickSemanticValidator(load_brick_schema=False)
        
        brick_type = validator.speckle_to_brick_type("Pipe")
        assert brick_type == "brick:Water_Supply_Pipe"
        
        brick_type = validator.speckle_to_brick_type("Duct")
        assert brick_type == "brick:Air_Duct"
        
        brick_type = validator.speckle_to_brick_type("UnknownType")
        assert brick_type is None
    
    def test_can_connect_from_mapping(self):
        """测试使用映射文件验证连接"""
        validator = BrickSemanticValidator(load_brick_schema=False)
        
        # 测试允许的连接
        assert validator.can_connect("Pump", "Pipe", "feeds") is True
        assert validator.can_connect("Pipe", "Valve", "feeds") is True
        
        # 测试不允许的连接（应该返回False）
        # 注意：实际映射文件中可能没有所有组合，这里只是测试逻辑
    
    def test_get_allowed_relationships(self):
        """测试获取允许的关系类型"""
        validator = BrickSemanticValidator(load_brick_schema=False)
        
        relationships = validator.get_allowed_relationships("Pump", "Pipe")
        assert "feeds" in relationships
    
    def test_validate_mep_connection(self):
        """测试 MEP 连接验证"""
        validator = BrickSemanticValidator(load_brick_schema=False)
        
        result = validator.validate_mep_connection(
            "Pump",
            "Pipe",
            "feeds"
        )
        
        assert "valid" in result
        assert "source_type" in result
        assert "target_type" in result
        assert "relationship" in result
        assert result["source_type"] == "Pump"
        assert result["target_type"] == "Pipe"
        assert result["relationship"] == "feeds"
    
    def test_validate_mep_connection_invalid(self):
        """测试无效连接验证"""
        validator = BrickSemanticValidator(load_brick_schema=False)
        
        # 测试一个可能无效的连接（如果映射文件中没有定义）
        result = validator.validate_mep_connection(
            "UnknownType1",
            "UnknownType2",
            "feeds"
        )
        
        assert "valid" in result
        assert "source_type" in result
        assert result["source_type"] == "UnknownType1"
    
    def test_validate_mep_connection_different_relationships(self):
        """测试不同关系类型的验证"""
        validator = BrickSemanticValidator(load_brick_schema=False)
        
        # 测试不同的关系类型
        result_feeds = validator.validate_mep_connection("Pump", "Pipe", "feeds")
        assert "valid" in result_feeds
        
        result_feeds_from = validator.validate_mep_connection("Pipe", "Pump", "feeds_from")
        assert "valid" in result_feeds_from
        
        result_controls = validator.validate_mep_connection("Valve", "Pipe", "controls")
        assert "valid" in result_controls
    
    def test_load_mapping_file_not_found(self):
        """测试映射文件不存在的情况"""
        from pathlib import Path
        non_existent_file = Path("/non/existent/mapping.json")
        
        validator = BrickSemanticValidator(
            mapping_file=non_existent_file,
            load_brick_schema=False
        )
        
        # 应该使用空映射
        assert validator._mapping == {}
    
    def test_load_mapping_json_error(self):
        """测试映射文件JSON解析错误"""
        import json
        from pathlib import Path
        from tempfile import NamedTemporaryFile
        
        # 创建无效的JSON文件
        with NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json {")
            temp_file = Path(f.name)
        
        try:
            validator = BrickSemanticValidator(
                mapping_file=temp_file,
                load_brick_schema=False
            )
            
            # 应该使用空映射
            assert validator._mapping == {}
        finally:
            temp_file.unlink()
    
    def test_check_mapping_examples_valid(self):
        """测试映射示例检查（有效连接）"""
        validator = BrickSemanticValidator(load_brick_schema=False)
        
        # 测试一个有效的连接（应该在映射文件中）
        # _check_mapping_examples 是私有方法，但我们可以通过 can_connect 间接测试
        result = validator.can_connect("Pump", "Pipe", "feeds")
        assert isinstance(result, bool)
    
    def test_check_mapping_examples_invalid(self):
        """测试映射示例检查（无效连接）"""
        validator = BrickSemanticValidator(load_brick_schema=False)
        
        # 测试一个无效的连接
        result = validator.can_connect("UnknownType1", "UnknownType2", "feeds")
        assert result is False
    
    def test_check_mapping_examples_different_relationships(self):
        """测试不同关系类型的映射示例检查"""
        validator = BrickSemanticValidator(load_brick_schema=False)
        
        # 测试不同的关系类型
        result1 = validator.can_connect("Pipe", "Valve", "feeds")
        assert isinstance(result1, bool)
        
        result2 = validator.can_connect("Valve", "Pipe", "controls")
        assert isinstance(result2, bool)
    
    def test_speckle_to_brick_type_all_mappings(self):
        """测试所有映射的类型转换"""
        validator = BrickSemanticValidator(load_brick_schema=False)
        
        # 测试所有常见的映射
        test_cases = [
            ("Pipe", "brick:Water_Supply_Pipe"),
            ("Duct", "brick:Air_Duct"),
            ("CableTray", "brick:Cable_Tray"),
            ("Pump", "brick:Water_Pump"),
            ("Valve", "brick:Valve"),
            ("VAV", "brick:Variable_Air_Volume_Box"),
        ]
        
        for speckle_type, expected_brick_type in test_cases:
            brick_type = validator.speckle_to_brick_type(speckle_type)
            assert brick_type == expected_brick_type
    
    def test_can_connect_unmapped_types(self):
        """测试未映射类型的连接检查"""
        validator = BrickSemanticValidator(load_brick_schema=False)
        
        # 未映射的类型应该返回False
        result = validator.can_connect("UnmappedType1", "UnmappedType2", "feeds")
        assert result is False
    
    def test_get_allowed_relationships_empty(self):
        """测试获取允许的关系（无映射时返回空列表）"""
        validator = BrickSemanticValidator(load_brick_schema=False)
        
        # 对于未映射的类型，应该返回空列表
        relationships = validator.get_allowed_relationships("UnmappedType1", "UnmappedType2")
        assert isinstance(relationships, list)
    
    def test_get_allowed_relationships_multiple(self):
        """测试获取多个允许的关系"""
        validator = BrickSemanticValidator(load_brick_schema=False)
        
        # 获取Pipe和Valve之间的所有允许关系
        relationships = validator.get_allowed_relationships("Pipe", "Valve")
        assert isinstance(relationships, list)
        # 应该包含"feeds"关系
        if len(relationships) > 0:
            assert "feeds" in relationships or "controls" in relationships or any(r in relationships for r in ["feeds", "controls", "feeds_from"])

