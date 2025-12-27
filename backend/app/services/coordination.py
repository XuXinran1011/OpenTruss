"""管线综合排布服务

实现3D管线综合排布功能，包括碰撞检测、避障优先级管理、路径调整等
"""

import logging
import json
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum

from app.utils.memgraph import MemgraphClient
from app.core.validators import SpatialValidator
from app.core.mep_routing_config import get_mep_routing_config
from app.models.speckle.base import Geometry

logger = logging.getLogger(__name__)


class AdjustmentType(str, Enum):
    """调整类型"""
    HORIZONTAL_TRANSLATION = "horizontal_translation"  # 水平平移
    VERTICAL_TRANSLATION = "vertical_translation"  # 垂直平移
    ADD_BEND = "add_bend"  # 增加翻弯


class CollisionPriority(str, Enum):
    """碰撞优先级"""
    BEAM_COLUMN = "beam_column"  # 梁、柱碰撞（最高优先级）
    STRUCTURE = "structure"  # 其他结构碰撞
    MEP = "mep"  # MEP元素之间的碰撞


class CoordinationService:
    """管线综合排布服务"""
    
    def __init__(self, client: Optional[MemgraphClient] = None):
        """初始化服务
        
        Args:
            client: Memgraph 客户端实例（如果为 None，将创建新实例）
        """
        self.client = client or MemgraphClient()
        self.collision_validator = SpatialValidator(self.client)
        self.config_loader = get_mep_routing_config()
        config_data = self.config_loader._config or {}
        
        # 从配置中获取竖向管线判定阈值
        vertical_pipe_config = config_data.get("vertical_pipe_detection", {})
        self.z_change_threshold = vertical_pipe_config.get("z_change_threshold", 1.0)  # 默认1米
    
    def detect_collisions(
        self,
        level_id: str,
        element_ids: Optional[List[str]] = None,
        include_structures: bool = True
    ) -> Dict[str, Any]:
        """检测碰撞
        
        Args:
            level_id: 楼层ID
            element_ids: 要检测的元素ID列表（如果为None，检测该楼层所有MEP元素）
            include_structures: 是否包含建筑结构（梁、柱、墙、楼板）
            
        Returns:
            {
                "collisions": List[Dict],  # 碰撞列表
                "collision_count": int,  # 碰撞数量
                "beam_column_collisions": List[Dict],  # 梁、柱碰撞（最高优先级）
                "structure_collisions": List[Dict],  # 其他结构碰撞
                "mep_collisions": List[Dict],  # MEP元素之间的碰撞
            }
        """
        # 获取要检测的元素ID列表
        if element_ids is None:
            query = """
            MATCH (e:Element)-[:LOCATED_AT]->(l:Level {id: $level_id})
            WHERE e.speckle_type IN ['Pipe', 'Duct', 'CableTray', 'Conduit', 'Wire']
            RETURN e.id as id
            """
            result = self.client.execute_query(query, {"level_id": level_id})
            element_ids = [row["id"] for row in result if row.get("id")]
        
        if not element_ids:
            return {
                "collisions": [],
                "collision_count": 0,
                "beam_column_collisions": [],
                "structure_collisions": [],
                "mep_collisions": []
            }
        
        # 检测MEP元素之间的碰撞
        mep_collisions = []
        collision_result = self.collision_validator.validate_collisions(element_ids)
        for collision in collision_result.get("collisions", []):
            elem1_id = collision.get("element_id_1")
            elem2_id = collision.get("element_id_2")
            
            # 检查元素类型，区分MEP和结构
            elem1_type = self._get_element_type(elem1_id)
            elem2_type = self._get_element_type(elem2_id)
            
            if self._is_structure(elem1_type) or self._is_structure(elem2_type):
                # 结构碰撞
                if self._is_beam_or_column(elem1_type) or self._is_beam_or_column(elem2_type):
                    mep_collisions.append({
                        "element_id_1": elem1_id,
                        "element_id_2": elem2_id,
                        "priority": CollisionPriority.BEAM_COLUMN.value,
                        "type": "beam_column"
                    })
                else:
                    mep_collisions.append({
                        "element_id_1": elem1_id,
                        "element_id_2": elem2_id,
                        "priority": CollisionPriority.STRUCTURE.value,
                        "type": "structure"
                    })
            else:
                # MEP元素之间的碰撞
                mep_collisions.append({
                    "element_id_1": elem1_id,
                    "element_id_2": elem2_id,
                    "priority": CollisionPriority.MEP.value,
                    "type": "mep"
                })
        
        # 如果包含结构，检测MEP与结构的碰撞
        structure_collisions = []
        beam_column_collisions = []
        if include_structures:
            # 获取楼层内的结构元素（梁、柱、墙、楼板）
            structure_query = """
            MATCH (s:Element)-[:LOCATED_AT]->(l:Level {id: $level_id})
            WHERE s.speckle_type IN ['Beam', 'Column', 'Wall', 'Slab']
            RETURN s.id as id, s.speckle_type as type
            """
            structure_result = self.client.execute_query(structure_query, {"level_id": level_id})
            structure_ids = [row["id"] for row in structure_result if row.get("id")]
            
            if structure_ids:
                # 检测MEP与结构的碰撞
                all_ids = element_ids + structure_ids
                structure_collision_result = self.collision_validator.validate_collisions(all_ids)
                
                for collision in structure_collision_result.get("collisions", []):
                    elem1_id = collision.get("element_id_1")
                    elem2_id = collision.get("element_id_2")
                    
                    # 检查是否是MEP与结构的碰撞
                    elem1_type = self._get_element_type(elem1_id)
                    elem2_type = self._get_element_type(elem2_id)
                    
                    is_beam_col = (
                        self._is_beam_or_column(elem1_type) or
                        self._is_beam_or_column(elem2_type)
                    )
                    is_structure = (
                        (self._is_structure(elem1_type) and elem1_id in structure_ids) or
                        (self._is_structure(elem2_type) and elem2_id in structure_ids)
                    )
                    is_mep = (
                        (elem1_id in element_ids and not self._is_structure(elem1_type)) or
                        (elem2_id in element_ids and not self._is_structure(elem2_type))
                    )
                    
                    if is_mep and is_structure:
                        if is_beam_col:
                            beam_column_collisions.append({
                                "element_id_1": elem1_id,
                                "element_id_2": elem2_id,
                                "priority": CollisionPriority.BEAM_COLUMN.value,
                                "type": "beam_column"
                            })
                        else:
                            structure_collisions.append({
                                "element_id_1": elem1_id,
                                "element_id_2": elem2_id,
                                "priority": CollisionPriority.STRUCTURE.value,
                                "type": "structure"
                            })
        
        # 合并所有碰撞，按优先级排序
        all_collisions = beam_column_collisions + structure_collisions + mep_collisions
        
        return {
            "collisions": all_collisions,
            "collision_count": len(all_collisions),
            "beam_column_collisions": beam_column_collisions,
            "structure_collisions": structure_collisions,
            "mep_collisions": mep_collisions
        }
    
    def get_system_priority(self, element_id: str) -> int:
        """获取元素的系统优先级
        
        Args:
            element_id: 元素ID
            
        Returns:
            优先级值（1-5，1为最高优先级）
        """
        # 查询元素的系统类型
        query = """
        MATCH (e:Element {id: $element_id})
        RETURN e.system_type as system_type, e.speckle_type as speckle_type
        """
        result = self.client.execute_query(query, {"element_id": element_id})
        
        if not result:
            return 5  # 默认最低优先级
        
        row = result[0]
        system_type = row.get("system_type")
        element_type = row.get("speckle_type")
        
        # 从配置中获取优先级
        config_data = self.config_loader._config or {}
        priority_config = config_data.get("system_priority", {}).get("default_priority_levels", [])
        
        for priority_level in priority_config:
            level = priority_level.get("level")
            systems = priority_level.get("systems", [])
            
            if system_type in systems:
                return level
        
        # 如果找不到匹配的系统类型，根据元素类型返回默认优先级
        if element_type == "Pipe":
            return 3  # 默认有压管道优先级
        elif element_type == "Duct":
            return 2  # 默认风管优先级
        elif element_type == "CableTray":
            return 4  # 默认桥架优先级
        else:
            return 5  # 默认最低优先级
    
    def coordinate_layout(
        self,
        level_id: str,
        element_ids: Optional[List[str]] = None,
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """进行管线综合排布
        
        Args:
            level_id: 楼层ID
            element_ids: 要排布的元素ID列表（如果为None，排布该楼层所有MEP元素）
            constraints: 约束条件
                {
                    "priorities": Dict[str, int],  # 自定义优先级（元素ID -> 优先级值）
                    "avoid_collisions": bool,  # 是否避开碰撞
                    "minimize_bends": bool,  # 是否最小化翻弯
                    "close_to_ceiling": bool,  # 是否贴近顶板
                }
                
        Returns:
            {
                "adjusted_elements": List[Dict],  # 调整后的元素列表
                "collisions_resolved": int,  # 解决的碰撞数量
                "warnings": List[str],  # 警告信息
                "errors": List[str],  # 错误信息
            }
        """
        constraints = constraints or {}
        avoid_collisions = constraints.get("avoid_collisions", True)
        minimize_bends = constraints.get("minimize_bends", True)
        close_to_ceiling = constraints.get("close_to_ceiling", True)
        custom_priorities = constraints.get("priorities", {})
        
        # 检测碰撞
        collision_result = self.detect_collisions(level_id, element_ids, include_structures=True)
        all_collisions = collision_result["collisions"]
        
        if not all_collisions:
            return {
                "adjusted_elements": [],
                "collisions_resolved": 0,
                "warnings": [],
                "errors": []
            }
        
        # 按优先级处理碰撞
        adjusted_elements = []
        resolved_count = 0
        warnings = []
        errors = []
        
        # 先处理梁、柱碰撞（最高优先级）
        beam_column_collisions = collision_result["beam_column_collisions"]
        for collision in beam_column_collisions:
            adjustment = self._resolve_collision(
                collision,
                level_id,
                custom_priorities,
                minimize_bends,
                close_to_ceiling
            )
            if adjustment:
                adjusted_elements.append(adjustment)
                resolved_count += 1
        
        # 再处理其他结构碰撞
        structure_collisions = collision_result["structure_collisions"]
        for collision in structure_collisions:
            adjustment = self._resolve_collision(
                collision,
                level_id,
                custom_priorities,
                minimize_bends,
                close_to_ceiling
            )
            if adjustment:
                adjusted_elements.append(adjustment)
                resolved_count += 1
        
        # 最后处理MEP元素之间的碰撞
        mep_collisions = collision_result["mep_collisions"]
        for collision in mep_collisions:
            adjustment = self._resolve_collision(
                collision,
                level_id,
                custom_priorities,
                minimize_bends,
                close_to_ceiling
            )
            if adjustment:
                adjusted_elements.append(adjustment)
                resolved_count += 1
        
        # 在管线综合排布完成后，自动生成支吊架
        hanger_warnings = []
        hanger_errors = []
        try:
            # 获取所有参与排布的元素ID（只包括Pipe、Duct、CableTray，不包括Wire和Conduit）
            all_element_ids = set()
            if element_ids:
                all_element_ids.update(element_ids)
            else:
                # 查询该楼层所有MEP元素
                query = """
                MATCH (e:Element)-[:LOCATED_AT]->(l:Level {id: $level_id})
                WHERE e.speckle_type IN ['Pipe', 'Duct', 'CableTray']
                RETURN e.id as id
                """
                result = self.client.execute_query(query, {"level_id": level_id})
                all_element_ids.update([row["id"] for row in result if row.get("id")])
            
            if all_element_ids:
                from app.services.hanger import HangerPlacementService
                
                hanger_service = HangerPlacementService(self.client)
                
                # 按Space分组元素，检查是否需要使用综合支吊架
                space_elements: Dict[str, List[str]] = {}
                standalone_elements: List[str] = []
                
                for elem_id in all_element_ids:
                    # 查询元素所在的Space（通过zone_id关联）
                    space_query = """
                    MATCH (e:Element {id: $element_id})
                    OPTIONAL MATCH (e)-[:LOCATED_AT]->(space:Element)
                    WHERE space.speckle_type = 'Space'
                    RETURN space.id as space_id, space.use_integrated_hanger as use_integrated_hanger
                    LIMIT 1
                    """
                    space_result = self.client.execute_query(space_query, {"element_id": elem_id})
                    
                    if space_result and space_result[0].get("space_id"):
                        space_id = space_result[0]["space_id"]
                        use_integrated = space_result[0].get("use_integrated_hanger", False)
                        
                        if use_integrated:
                            # 使用综合支吊架
                            if space_id not in space_elements:
                                space_elements[space_id] = []
                            space_elements[space_id].append(elem_id)
                        else:
                            # 单独支吊架
                            standalone_elements.append(elem_id)
                    else:
                        # 没有关联Space，使用单独支吊架
                        standalone_elements.append(elem_id)
                
                # 为每个Space生成综合支吊架
                for space_id, elem_ids in space_elements.items():
                    if len(elem_ids) >= 2:  # 至少需要2根管线
                        try:
                            hanger_service.generate_integrated_hangers(
                                space_id=space_id,
                                element_ids=elem_ids,
                                seismic_grade=None,  # 可以从配置中获取
                                create_nodes=True
                            )
                            logger.info(f"Generated integrated hangers for space {space_id} with {len(elem_ids)} elements")
                        except Exception as e:
                            error_msg = f"Failed to generate integrated hangers for space {space_id}: {str(e)}"
                            logger.warning(error_msg)
                            hanger_warnings.append(error_msg)
                
                # 为每个单独元素生成支吊架
                for elem_id in standalone_elements:
                    try:
                        # 检查元素类型是否支持支吊架
                        elem_type_query = """
                        MATCH (e:Element {id: $element_id})
                        RETURN e.speckle_type as type
                        """
                        type_result = self.client.execute_query(elem_type_query, {"element_id": elem_id})
                        
                        if type_result and type_result[0].get("type") in ["Pipe", "Duct", "CableTray"]:
                            hanger_service.generate_hangers(
                                element_id=elem_id,
                                seismic_grade=None,  # 可以从配置中获取
                                create_nodes=True
                            )
                            logger.info(f"Generated hangers for element {elem_id}")
                    except Exception as e:
                        error_msg = f"Failed to generate hangers for element {elem_id}: {str(e)}"
                        logger.warning(error_msg)
                        hanger_warnings.append(error_msg)
        
        except Exception as e:
            # 支吊架生成失败不应该阻止coordination完成
            error_msg = f"Failed to auto-generate hangers after coordination: {str(e)}"
            logger.warning(error_msg, exc_info=True)
            hanger_warnings.append(error_msg)
        
        # 合并警告和错误
        warnings.extend(hanger_warnings)
        errors.extend(hanger_errors)
        
        return {
            "adjusted_elements": adjusted_elements,
            "collisions_resolved": resolved_count,
            "warnings": warnings,
            "errors": errors
        }
    
    def _resolve_collision(
        self,
        collision: Dict[str, Any],
        level_id: str,
        custom_priorities: Dict[str, int],
        minimize_bends: bool,
        close_to_ceiling: bool
    ) -> Optional[Dict[str, Any]]:
        """解决单个碰撞
        
        Args:
            collision: 碰撞信息
            level_id: 楼层ID
            custom_priorities: 自定义优先级
            minimize_bends: 是否最小化翻弯
            close_to_ceiling: 是否贴近顶板
            
        Returns:
            调整方案，如果无法解决则返回None
        """
        elem1_id = collision.get("element_id_1")
        elem2_id = collision.get("element_id_2")
        
        # 获取优先级
        priority1 = custom_priorities.get(elem1_id) or self.get_system_priority(elem1_id)
        priority2 = custom_priorities.get(elem2_id) or self.get_system_priority(elem2_id)
        
        # 确定哪个元素需要避让（优先级高的保持不变，优先级低的避让）
        if priority1 < priority2:
            # elem1优先级更高，elem2需要避让
            element_to_adjust = elem2_id
            obstacle_element = elem1_id
        elif priority2 < priority1:
            # elem2优先级更高，elem1需要避让
            element_to_adjust = elem1_id
            obstacle_element = elem2_id
        else:
            # 优先级相同，使用冲突处理规则
            element_to_adjust, obstacle_element = self._resolve_same_priority_collision(
                elem1_id,
                elem2_id,
                minimize_bends
            )
        
        # 生成调整方案
        adjustment = self._generate_adjustment(
            element_to_adjust,
            obstacle_element,
            level_id,
            minimize_bends,
            close_to_ceiling
        )
        
        return adjustment
    
    def _resolve_same_priority_collision(
        self,
        elem1_id: str,
        elem2_id: str,
        minimize_bends: bool
    ) -> Tuple[str, str]:
        """解决相同优先级的碰撞冲突
        
        规则：少翻弯 > 较小管径/截面积避让较大管径/截面积 > 贴近顶板
        
        Args:
            elem1_id: 元素1 ID
            elem2_id: 元素2 ID
            minimize_bends: 是否最小化翻弯
            
        Returns:
            (需要调整的元素ID, 障碍物元素ID)
        """
        # 获取元素尺寸信息
        elem1_size = self._get_element_size(elem1_id)
        elem2_size = self._get_element_size(elem2_id)
        
        # 规则：较小管径/截面积避让较大管径/截面积
        if elem1_size < elem2_size:
            return elem1_id, elem2_id
        elif elem2_size < elem1_size:
            return elem2_id, elem1_id
        else:
            # 尺寸相同，默认elem1避让
            return elem1_id, elem2_id
    
    def _generate_adjustment(
        self,
        element_id: str,
        obstacle_id: str,
        level_id: str,
        minimize_bends: bool,
        close_to_ceiling: bool
    ) -> Optional[Dict[str, Any]]:
        """生成调整方案
        
        Args:
            element_id: 需要调整的元素ID
            obstacle_id: 障碍物元素ID
            level_id: 楼层ID
            minimize_bends: 是否最小化翻弯
            close_to_ceiling: 是否贴近顶板
            
        Returns:
            调整方案
        """
        # 获取元素路径信息
        query = """
        MATCH (e:Element {id: $element_id})
        RETURN e.geometry as geometry, e.height as height, e.base_offset as base_offset
        """
        result = self.client.execute_query(query, {"element_id": element_id})
        
        if not result:
            return None
        
        row = result[0]
        geometry_data = row.get("geometry")
        height = row.get("height") or 0.0
        base_offset = row.get("base_offset") or 0.0
        
        # 解析几何数据
        if isinstance(geometry_data, str):
            try:
                geometry_dict = json.loads(geometry_data)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse geometry for element {element_id}")
                return None
        else:
            geometry_dict = geometry_data
        
        coordinates = geometry_dict.get("coordinates", [])
        if not coordinates:
            return None
        
        # 根据障碍物类型和位置，生成调整方案
        # 优先使用垂直平移避开碰撞
        adjustment_type = AdjustmentType.VERTICAL_TRANSLATION.value
        
        # 保存原始路径（3D 坐标）
        original_path = []
        for coord in coordinates:
            if len(coord) >= 3:
                original_path.append([coord[0], coord[1], coord[2]])
            elif len(coord) >= 2:
                original_path.append([coord[0], coord[1], base_offset])
            else:
                continue
        
        # 计算新的路径（简化处理：向下平移0.2米）
        # 保持 3D 坐标，只调整 Z 值
        adjusted_path = []
        for coord in coordinates:
            if len(coord) >= 3:
                # 已有 Z 坐标，向下平移 0.2 米
                adjusted_path.append([coord[0], coord[1], coord[2] - 0.2])
            elif len(coord) >= 2:
                # 只有 X, Y，使用 base_offset - 0.2 作为 Z
                adjusted_path.append([coord[0], coord[1], base_offset - 0.2])
            else:
                # 无效坐标，跳过
                continue
        adjustment_reason = "避开碰撞"
        
        if close_to_ceiling:
            # 如果贴近顶板，可以向上平移（但需要确保不与顶板碰撞）
            # 这里简化处理，实际应该计算顶板高度
            pass
        
        return {
            "element_id": element_id,
            "original_path": original_path,
            "adjusted_path": adjusted_path,
            "adjustment_type": adjustment_type,
            "adjustment_reason": adjustment_reason
        }
    
    def _get_element_type(self, element_id: str) -> Optional[str]:
        """获取元素类型"""
        query = """
        MATCH (e:Element {id: $element_id})
        RETURN e.speckle_type as type
        """
        result = self.client.execute_query(query, {"element_id": element_id})
        if result:
            return result[0].get("type")
        return None
    
    def _is_structure(self, element_type: Optional[str]) -> bool:
        """判断是否为结构元素"""
        if not element_type:
            return False
        return element_type in ["Beam", "Column", "Wall", "Slab"]
    
    def _is_beam_or_column(self, element_type: Optional[str]) -> bool:
        """判断是否为梁或柱"""
        if not element_type:
            return False
        return element_type in ["Beam", "Column"]
    
    def _get_element_size(self, element_id: str) -> float:
        """获取元素尺寸（用于优先级冲突处理）
        
        Returns:
            尺寸值（管道的直径、风管的截面积等）
        """
        query = """
        MATCH (e:Element {id: $element_id})
        RETURN e.diameter as diameter, e.width as width, e.height as height, e.speckle_type as type
        """
        result = self.client.execute_query(query, {"element_id": element_id})
        
        if not result:
            return 0.0
        
        row = result[0]
        element_type = row.get("type")
        
        if element_type == "Pipe":
            # 管道：使用直径
            diameter = row.get("diameter") or 0.0
            return float(diameter)
        elif element_type == "Duct":
            # 风管：使用截面积（宽×高）
            width = row.get("width") or 0.0
            height = row.get("height") or 0.0
            return float(width * height)
        elif element_type == "CableTray":
            # 桥架：使用宽度
            width = row.get("width") or 0.0
            return float(width)
        else:
            return 0.0
    
    def is_vertical_pipe(self, element_id: str) -> bool:
        """判定是否为竖向管线
        
        判定标准：Z方向变化>阈值（默认1米）
        
        Args:
            element_id: 元素ID
            
        Returns:
            是否为竖向管线
        """
        # 获取元素的几何信息
        query = """
        MATCH (e:Element {id: $element_id})
        RETURN e.geometry as geometry, e.height as height, e.base_offset as base_offset
        """
        result = self.client.execute_query(query, {"element_id": element_id})
        
        if not result:
            return False
        
        row = result[0]
        height = row.get("height") or 0.0
        base_offset = row.get("base_offset") or 0.0
        
        # 计算Z方向变化
        z_change = abs(float(height))
        
        # 如果Z方向变化超过阈值，判定为竖向管线
        return z_change > self.z_change_threshold
    
    def get_vertical_pipe_elements(
        self,
        level_id: str,
        element_ids: Optional[List[str]] = None
    ) -> List[str]:
        """获取楼层内的竖向管线元素列表
        
        Args:
            level_id: 楼层ID
            element_ids: 要检查的元素ID列表（如果为None，检查该楼层所有MEP元素）
            
        Returns:
            竖向管线元素ID列表
        """
        # 获取要检查的元素ID列表
        if element_ids is None:
            query = """
            MATCH (e:Element)-[:LOCATED_AT]->(l:Level {id: $level_id})
            WHERE e.speckle_type IN ['Pipe', 'Duct', 'CableTray', 'Conduit', 'Wire']
            RETURN e.id as id
            """
            result = self.client.execute_query(query, {"level_id": level_id})
            element_ids = [row["id"] for row in result if row.get("id")]
        
        if not element_ids:
            return []
        
        # 判定每个元素是否为竖向管线
        vertical_pipes = []
        for element_id in element_ids:
            if self.is_vertical_pipe(element_id):
                vertical_pipes.append(element_id)
        
        return vertical_pipes

