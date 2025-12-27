"""桥架电缆容量验证器

验证桥架内电缆容量是否符合规范要求：
- 电力电缆截面积之和 ≤ 桥架截面积的40%
- 控制电缆截面积之和 ≤ 桥架截面积的50%
"""

import logging
from typing import Dict, Any, Optional, List

from app.utils.memgraph import MemgraphClient

logger = logging.getLogger(__name__)


class CableCapacityValidator:
    """桥架电缆容量验证器"""
    
    # 容量限制常量
    POWER_CABLE_MAX_RATIO = 0.40  # 电力电缆最大截面积比例：40%
    CONTROL_CABLE_MAX_RATIO = 0.50  # 控制电缆最大截面积比例：50%
    
    def __init__(self, client: Optional[MemgraphClient] = None):
        """初始化验证器
        
        Args:
            client: Memgraph 客户端实例（如果为 None，将创建新实例）
        """
        self.client = client or MemgraphClient()
    
    def validate_cable_tray_capacity(
        self,
        cable_tray_id: str,
        new_cable_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """验证桥架内电缆容量是否超限
        
        Args:
            cable_tray_id: 桥架元素ID
            new_cable_id: 新增电缆ID（如果为None，只验证现有电缆）
        
        Returns:
            {
                "valid": bool,
                "errors": List[str],
                "warnings": List[str],
                "power_cable_area": float,  # 电力电缆总截面积
                "control_cable_area": float,  # 控制电缆总截面积
                "tray_cross_section": float,  # 桥架截面积
                "power_cable_ratio": float,  # 电力电缆占比
                "control_cable_ratio": float  # 控制电缆占比
            }
        """
        # 1. 查询桥架信息（宽度、高度）
        tray_info = self._get_cable_tray_info(cable_tray_id)
        if not tray_info:
            return {
                "valid": False,
                "errors": [f"桥架 {cable_tray_id} 不存在"],
                "warnings": [],
                "power_cable_area": 0.0,
                "control_cable_area": 0.0,
                "tray_cross_section": 0.0,
                "power_cable_ratio": 0.0,
                "control_cable_ratio": 0.0
            }
        
        width = tray_info.get("width", 0.0)
        height = tray_info.get("height", 0.0)
        
        if width <= 0 or height <= 0:
            return {
                "valid": False,
                "errors": [f"桥架 {cable_tray_id} 的宽度或高度无效"],
                "warnings": [],
                "power_cable_area": 0.0,
                "control_cable_area": 0.0,
                "tray_cross_section": 0.0,
                "power_cable_ratio": 0.0,
                "control_cable_ratio": 0.0
            }
        
        tray_cross_section = width * height  # 平方毫米
        
        # 2. 查询桥架内所有电缆
        cables = self._get_cables_in_tray(cable_tray_id)
        
        # 如果添加新电缆，需要包含它
        if new_cable_id:
            new_cable = self._get_cable_info(new_cable_id)
            if new_cable:
                cables.append(new_cable)
        
        # 3. 计算电力电缆和控制电缆的总截面积
        power_cable_area = 0.0
        control_cable_area = 0.0
        
        for cable in cables:
            area = cable.get("cross_section_area")
            if area is None or area <= 0:
                # 如果缺少截面积信息，跳过该电缆（或记录警告）
                continue
            
            cable_type = cable.get("cable_type")
            
            if cable_type == "电力电缆":
                power_cable_area += area
            elif cable_type == "控制电缆":
                control_cable_area += area
        
        # 4. 计算占比
        power_cable_ratio = power_cable_area / tray_cross_section if tray_cross_section > 0 else 0.0
        control_cable_ratio = control_cable_area / tray_cross_section if tray_cross_section > 0 else 0.0
        
        # 5. 验证是否超限
        errors = []
        warnings = []
        
        if power_cable_ratio > self.POWER_CABLE_MAX_RATIO:
            errors.append(
                f"电力电缆截面积占比 {power_cable_ratio*100:.1f}% 超过限制 {self.POWER_CABLE_MAX_RATIO*100}%"
            )
        
        if control_cable_ratio > self.CONTROL_CABLE_MAX_RATIO:
            errors.append(
                f"控制电缆截面积占比 {control_cable_ratio*100:.1f}% 超过限制 {self.CONTROL_CABLE_MAX_RATIO*100}%"
            )
        
        # 6. 如果接近限制，发出警告（90%以上但未超过限制）
        # 使用小的容差值来处理浮点数精度问题
        EPSILON = 1e-6
        warning_threshold_power = self.POWER_CABLE_MAX_RATIO * 0.9
        warning_threshold_control = self.CONTROL_CABLE_MAX_RATIO * 0.9
        
        if power_cable_ratio >= (warning_threshold_power - EPSILON) and power_cable_ratio <= (self.POWER_CABLE_MAX_RATIO + EPSILON):
            warnings.append(
                f"电力电缆截面积占比 {power_cable_ratio*100:.1f}% 接近限制 {self.POWER_CABLE_MAX_RATIO*100}%"
            )
        
        if control_cable_ratio >= (warning_threshold_control - EPSILON) and control_cable_ratio <= (self.CONTROL_CABLE_MAX_RATIO + EPSILON):
            warnings.append(
                f"控制电缆截面积占比 {control_cable_ratio*100:.1f}% 接近限制 {self.CONTROL_CABLE_MAX_RATIO*100}%"
            )
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "power_cable_area": power_cable_area,
            "control_cable_area": control_cable_area,
            "tray_cross_section": tray_cross_section,
            "power_cable_ratio": power_cable_ratio,
            "control_cable_ratio": control_cable_ratio
        }
    
    def _get_cable_tray_info(self, cable_tray_id: str) -> Optional[Dict[str, Any]]:
        """获取桥架信息
        
        Args:
            cable_tray_id: 桥架元素ID
        
        Returns:
            桥架信息字典，包含 width 和 height，如果不存在则返回 None
        """
        query = """
        MATCH (tray:Element {id: $cable_tray_id})
        WHERE tray.speckle_type = 'CableTray'
        RETURN tray.width as width, tray.height as height
        """
        try:
            result = self.client.execute_query(query, {"cable_tray_id": cable_tray_id})
            if result:
                return dict(result[0])
        except Exception as e:
            logger.error(f"Error getting cable tray info: {e}", exc_info=True)
        return None
    
    def _get_cables_in_tray(self, cable_tray_id: str) -> List[Dict[str, Any]]:
        """获取桥架内所有电缆
        
        Args:
            cable_tray_id: 桥架元素ID
        
        Returns:
            电缆信息列表，每个元素包含 id, cross_section_area, cable_type
        """
        query = """
        MATCH (cable:Element)-[:CONTAINED_IN]->(tray:Element {id: $cable_tray_id})
        WHERE cable.speckle_type = 'Wire'
        RETURN cable.id as id,
               cable.cross_section_area as cross_section_area,
               cable.cable_type as cable_type
        """
        try:
            result = self.client.execute_query(query, {"cable_tray_id": cable_tray_id})
            return [dict(row) for row in result]
        except Exception as e:
            logger.error(f"Error getting cables in tray: {e}", exc_info=True)
            return []
    
    def _get_cable_info(self, cable_id: str) -> Optional[Dict[str, Any]]:
        """获取电缆信息
        
        Args:
            cable_id: 电缆元素ID
        
        Returns:
            电缆信息字典，包含 id, cross_section_area, cable_type，如果不存在则返回 None
        """
        query = """
        MATCH (cable:Element {id: $cable_id})
        WHERE cable.speckle_type = 'Wire'
        RETURN cable.id as id,
               cable.cross_section_area as cross_section_area,
               cable.cable_type as cable_type
        """
        try:
            result = self.client.execute_query(query, {"cable_id": cable_id})
            if result:
                return dict(result[0])
        except Exception as e:
            logger.error(f"Error getting cable info: {e}", exc_info=True)
        return None
