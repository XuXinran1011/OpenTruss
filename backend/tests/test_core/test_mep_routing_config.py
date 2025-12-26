"""MEP 路径规划配置加载器测试"""

import json
import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile
from app.core.mep_routing_config import MEPRoutingConfigLoader, get_mep_routing_config


class TestMEPRoutingConfigLoader:
    """MEPRoutingConfigLoader 测试类"""
    
    def test_init_with_default_config(self):
        """测试使用默认配置文件初始化"""
        loader = MEPRoutingConfigLoader()
        assert loader.config_file is not None
        assert loader._config is not None
        assert "routing_constraints" in loader._config
    
    def test_init_with_custom_config(self):
        """测试使用自定义配置文件初始化"""
        # 创建临时配置文件
        test_config = {
            "version": "2.0",
            "routing_constraints": {
                "Pipe": {
                    "gravity_drainage": {
                        "allowed_angles": [45, 180],
                        "forbidden_angles": [90],
                        "requires_double_45": True
                    }
                }
            }
        }
        
        with NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_config, f)
            temp_file = Path(f.name)
        
        try:
            loader = MEPRoutingConfigLoader(config_file=temp_file)
            assert loader.config_file == temp_file
            assert loader._config == test_config
        finally:
            temp_file.unlink()
    
    def test_load_config_file_not_found(self):
        """测试配置文件不存在的情况"""
        non_existent_file = Path("/non/existent/config.json")
        loader = MEPRoutingConfigLoader(config_file=non_existent_file)
        assert loader._config == {}
    
    def test_load_config_json_error(self):
        """测试JSON解析错误的情况"""
        # 创建无效的JSON文件
        with NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json {")
            temp_file = Path(f.name)
        
        try:
            loader = MEPRoutingConfigLoader(config_file=temp_file)
            assert loader._config == {}
        finally:
            temp_file.unlink()
    
    def test_get_constraints_with_system_type(self):
        """测试获取特定系统类型的约束"""
        loader = MEPRoutingConfigLoader()
        
        constraints = loader.get_constraints("Pipe", "gravity_drainage")
        
        assert "allowed_angles" in constraints
        assert "forbidden_angles" in constraints
        assert 90 in constraints["forbidden_angles"]
        assert constraints["requires_double_45"] is True
    
    def test_get_constraints_without_system_type(self):
        """测试获取默认约束（无系统类型）"""
        loader = MEPRoutingConfigLoader()
        
        constraints = loader.get_constraints("Pipe", None)
        
        assert "allowed_angles" in constraints
        assert isinstance(constraints["allowed_angles"], list)
    
    def test_get_constraints_nonexistent_element_type(self):
        """测试获取不存在的元素类型约束"""
        loader = MEPRoutingConfigLoader()
        
        constraints = loader.get_constraints("NonExistentType", None)
        
        # 应该返回默认约束
        assert "allowed_angles" in constraints
        assert constraints["allowed_angles"] == [45, 90, 180]
        assert constraints["forbidden_angles"] == []
    
    def test_get_constraints_nonexistent_system_type(self):
        """测试获取不存在的系统类型约束"""
        loader = MEPRoutingConfigLoader()
        
        constraints = loader.get_constraints("Pipe", "nonexistent_system")
        
        # 应该返回默认约束
        assert "allowed_angles" in constraints
    
    def test_get_bend_radius_ratio_pipe(self):
        """测试获取管道转弯半径比"""
        loader = MEPRoutingConfigLoader()
        
        # 测试不同直径范围（根据配置文件）
        # 0-50: 1.0
        ratio_30 = loader.get_bend_radius_ratio("Pipe", 30)
        assert ratio_30 == 1.0
        
        # 50-150: 1.5
        ratio_100 = loader.get_bend_radius_ratio("Pipe", 100)
        assert ratio_100 == 1.5
        
        # 150-300: 2.0
        ratio_200 = loader.get_bend_radius_ratio("Pipe", 200)
        assert ratio_200 == 2.0
        
        # 300-500: 2.5
        ratio_400 = loader.get_bend_radius_ratio("Pipe", 400)
        assert ratio_400 == 2.5
        
        # 500+: 3.0
        ratio_600 = loader.get_bend_radius_ratio("Pipe", 600)
        assert ratio_600 == 3.0
    
    def test_get_bend_radius_ratio_boundary_values(self):
        """测试边界值"""
        loader = MEPRoutingConfigLoader()
        
        # 测试边界值（0, 50, 150, 300, 500）
        ratio_0 = loader.get_bend_radius_ratio("Pipe", 0)
        assert ratio_0 == 1.0
        
        ratio_50 = loader.get_bend_radius_ratio("Pipe", 50)
        assert ratio_50 == 1.5  # 50应该落在50-150范围
        
        ratio_150 = loader.get_bend_radius_ratio("Pipe", 150)
        assert ratio_150 == 2.0  # 150应该落在150-300范围
        
        ratio_300 = loader.get_bend_radius_ratio("Pipe", 300)
        assert ratio_300 == 2.5  # 300应该落在300-500范围
        
        ratio_500 = loader.get_bend_radius_ratio("Pipe", 500)
        assert ratio_500 == 3.0  # 500应该落在500+范围
    
    def test_get_bend_radius_ratio_plus_suffix(self):
        """测试带+后缀的范围（如500+）"""
        loader = MEPRoutingConfigLoader()
        
        # 测试大于500的值
        ratio_1000 = loader.get_bend_radius_ratio("Pipe", 1000)
        assert ratio_1000 == 3.0
    
    def test_get_bend_radius_ratio_not_found(self):
        """测试未找到转弯半径比的情况"""
        loader = MEPRoutingConfigLoader()
        
        # Duct 暂时返回None（未完全实现）
        ratio = loader.get_bend_radius_ratio("Duct", 100)
        assert ratio is None
        
        # 不存在的元素类型
        ratio = loader.get_bend_radius_ratio("NonExistent", 100)
        assert ratio is None
    
    def test_get_min_width_ratio(self):
        """测试获取电缆桥架最小宽度比"""
        loader = MEPRoutingConfigLoader()
        
        # 测试不同电缆转弯半径（根据配置文件）
        # 0-50: 2.0
        ratio_30 = loader.get_min_width_ratio(30)
        assert ratio_30 == 2.0
        
        # 50-150: 3.0
        ratio_100 = loader.get_min_width_ratio(100)
        assert ratio_100 == 3.0
        
        # 150-300: 4.0
        ratio_200 = loader.get_min_width_ratio(200)
        assert ratio_200 == 4.0
        
        # 300+: 5.0
        ratio_400 = loader.get_min_width_ratio(400)
        assert ratio_400 == 5.0
    
    def test_get_min_width_ratio_boundary_values(self):
        """测试边界值"""
        loader = MEPRoutingConfigLoader()
        
        ratio_0 = loader.get_min_width_ratio(0)
        assert ratio_0 == 2.0
        
        ratio_50 = loader.get_min_width_ratio(50)
        assert ratio_50 == 3.0  # 50应该落在50-150范围
        
        ratio_150 = loader.get_min_width_ratio(150)
        assert ratio_150 == 4.0  # 150应该落在150-300范围
        
        ratio_300 = loader.get_min_width_ratio(300)
        assert ratio_300 == 5.0  # 300应该落在300+范围
    
    def test_get_min_width_ratio_plus_suffix(self):
        """测试带+后缀的范围"""
        loader = MEPRoutingConfigLoader()
        
        ratio_1000 = loader.get_min_width_ratio(1000)
        assert ratio_1000 == 5.0
    
    def test_get_min_width_ratio_not_found(self):
        """测试配置为空时返回None"""
        # 创建空配置
        empty_config = {}
        with NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(empty_config, f)
            temp_file = Path(f.name)
        
        try:
            loader = MEPRoutingConfigLoader(config_file=temp_file)
            ratio = loader.get_min_width_ratio(100)
            assert ratio is None
        finally:
            temp_file.unlink()
    
    def test_requires_double_45_gravity_drainage(self):
        """测试重力排水系统需要双45°"""
        loader = MEPRoutingConfigLoader()
        
        assert loader.requires_double_45("Pipe", "gravity_drainage") is True
        assert loader.requires_double_45("Pipe", "pressure_water") is False
        assert loader.requires_double_45("Pipe", None) is False
    
    def test_requires_double_45_other_types(self):
        """测试其他元素类型不需要双45°"""
        loader = MEPRoutingConfigLoader()
        
        assert loader.requires_double_45("Duct", "any_system") is False
        assert loader.requires_double_45("CableTray", "any_system") is False
        assert loader.requires_double_45("NonExistent", "any_system") is False


class TestGetMEPRoutingConfig:
    """get_mep_routing_config 单例函数测试"""
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        loader1 = get_mep_routing_config()
        loader2 = get_mep_routing_config()
        
        # 应该是同一个实例
        assert loader1 is loader2

