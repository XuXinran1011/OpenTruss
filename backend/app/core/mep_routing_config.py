"""MEP 路径规划配置加载器

加载和解析 MEP 路径规划配置文件，提供配置查询接口
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)

# 配置文件路径
CONFIG_FILE = Path(__file__).parent.parent / "config" / "rules" / "mep_routing_config.json"


class MEPRoutingConfigLoader:
    """MEP 路径规划配置加载器"""
    
    def __init__(self, config_file: Optional[Path] = None):
        """初始化配置加载器
        
        Args:
            config_file: 配置文件路径，如果为 None 则使用默认路径
        """
        self.config_file = config_file or CONFIG_FILE
        self._config: Optional[Dict[str, Any]] = None
        self._load_config()
    
    def _load_config(self) -> None:
        """加载配置文件"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
            logger.info(f"Loaded MEP routing config from {self.config_file}")
        except FileNotFoundError:
            logger.error(f"MEP routing config file not found: {self.config_file}")
            self._config = {}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse MEP routing config: {e}")
            self._config = {}
    
    def get_constraints(
        self,
        element_type: str,
        system_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取路径约束
        
        Args:
            element_type: 元素类型（如：Pipe, Duct, CableTray）
            system_type: 系统类型（如：gravity_drainage, pressure_water），如果为 None 则使用 general
        
        Returns:
            约束字典，包含 allowed_angles, forbidden_angles 等
        """
        if not self._config:
            return {}
        
        routing_constraints = self._config.get("routing_constraints", {})
        element_constraints = routing_constraints.get(element_type, {})
        
        if system_type and system_type in element_constraints:
            return element_constraints[system_type]
        elif "general" in element_constraints:
            return element_constraints["general"]
        else:
            # 返回默认约束
            return {
                "allowed_angles": [45, 90, 180],
                "forbidden_angles": []
            }
    
    def get_bend_radius_ratio(
        self,
        element_type: str,
        diameter_or_size: float
    ) -> Optional[float]:
        """获取转弯半径比
        
        Args:
            element_type: 元素类型（如：Pipe, Duct）
            diameter_or_size: 直径或尺寸（毫米）
        
        Returns:
            转弯半径比，如果未找到则返回 None
        """
        if not self._config:
            return None
        
        routing_constraints = self._config.get("routing_constraints", {})
        element_constraints = routing_constraints.get(element_type, {})
        
        if element_type == "Pipe":
            ratios = element_constraints.get("bend_radius_ratio_by_diameter", {})
        elif element_type == "Duct":
            # Duct 使用 bend_radius_ratio_by_size，需要额外参数判断矩形/圆形
            # 这里先返回默认值，具体实现需要更多信息
            return None
        else:
            return None
        
        # 解析范围键（如 "0-50", "50-150"）
        for range_key, ratio in ratios.items():
            if range_key.endswith("+"):
                min_val = float(range_key[:-1])
                if diameter_or_size >= min_val:
                    return ratio
            else:
                parts = range_key.split("-")
                if len(parts) == 2:
                    min_val, max_val = float(parts[0]), float(parts[1])
                    if min_val <= diameter_or_size < max_val:
                        return ratio
        
        return None
    
    def get_min_width_ratio(
        self,
        cable_bend_radius: float
    ) -> Optional[float]:
        """获取电缆桥架最小宽度比
        
        Args:
            cable_bend_radius: 电缆转弯半径（毫米）
        
        Returns:
            最小宽度比，如果未找到则返回 None
        """
        if not self._config:
            return None
        
        routing_constraints = self._config.get("routing_constraints", {})
        cable_tray_constraints = routing_constraints.get("CableTray", {})
        width_ratios = cable_tray_constraints.get("min_width_by_cable_bend_radius", {})
        
        # 解析范围键
        for range_key, ratio in width_ratios.items():
            if range_key.endswith("+"):
                min_val = float(range_key[:-1])
                if cable_bend_radius >= min_val:
                    return ratio
            else:
                parts = range_key.split("-")
                if len(parts) == 2:
                    min_val, max_val = float(parts[0]), float(parts[1])
                    if min_val <= cable_bend_radius < max_val:
                        return ratio
        
        return None
    
    def requires_double_45(
        self,
        element_type: str,
        system_type: Optional[str]
    ) -> bool:
        """检查是否需要双45°弯头模式
        
        Args:
            element_type: 元素类型
            system_type: 系统类型
        
        Returns:
            是否需要双45°弯头模式
        """
        constraints = self.get_constraints(element_type, system_type)
        return constraints.get("requires_double_45", False)


# 全局配置加载器实例（单例模式）
_config_loader: Optional[MEPRoutingConfigLoader] = None


def get_mep_routing_config() -> MEPRoutingConfigLoader:
    """获取全局配置加载器实例
    
    Returns:
        MEPRoutingConfigLoader 实例
    """
    global _config_loader
    if _config_loader is None:
        _config_loader = MEPRoutingConfigLoader()
    return _config_loader

