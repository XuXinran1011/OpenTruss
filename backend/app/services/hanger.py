"""支吊架自动布置服务

根据标准图集自动计算和生成支吊架位置
"""

import logging
import math
import json
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from app.utils.memgraph import MemgraphClient
from app.core.exceptions import NotFoundError, ValidationError
from app.models.gb50300.element import ElementNode
from app.models.speckle.base import Geometry
from app.models.speckle.mep import Hanger, IntegratedHanger
from app.models.gb50300.relationships import SUPPORTS, HAS_HANGER, USES_INTEGRATED_HANGER

logger = logging.getLogger(__name__)

# 配置文件路径
HANGER_CONFIG_FILE = Path(__file__).parent.parent / "config" / "rules" / "hanger_config.json"


class HangerPlacementService:
    """支吊架自动布置服务"""
    
    def __init__(self, client: Optional[MemgraphClient] = None):
        """初始化服务
        
        Args:
            client: Memgraph 客户端实例（如果为 None，将创建新实例）
        """
        self.client = client or MemgraphClient()
        self._config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """加载支吊架配置"""
        try:
            with open(HANGER_CONFIG_FILE, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
            logger.info(f"Loaded hanger config from {HANGER_CONFIG_FILE}")
        except FileNotFoundError:
            logger.error(f"Hanger config file not found: {HANGER_CONFIG_FILE}")
            self._config = {}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse hanger config: {e}")
            self._config = {}
    
    def calculate_hanger_positions(
        self,
        element_id: str,
        seismic_grade: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """计算支吊架布置位置
        
        Args:
            element_id: MEP元素ID（Pipe, Duct, CableTray）
            seismic_grade: 抗震等级（6度、7度、8度、9度）
        
        Returns:
            支吊架位置列表，每个元素包含：
            - position: [x, y, z] 位置坐标
            - hanger_type: "支架" 或 "吊架"
            - standard_code: 标准图集编号
            - detail_code: 详图编号
            - support_interval: 支撑间距
        """
        # 1. 查询元素信息
        element = self._get_element(element_id)
        if not element:
            raise ValueError(f"Element not found: {element_id}")
        
        # 2. 确定适用的标准图集
        standard_code = self._determine_standard(element.speckle_type)
        if not standard_code:
            raise ValidationError(
                f"No standard found for element type: {element.speckle_type}",
                {"element_type": element.speckle_type, "element_id": element_id}
            )
        
        # 3. 计算最大间距
        max_spacing = self._calculate_max_spacing(
            element, standard_code, seismic_grade
        )
        
        # 4. 沿路径计算支吊架位置
        positions = self._calculate_positions_along_path(
            element, max_spacing, standard_code
        )
        
        # 5. 根据放置规则调整位置
        positions = self._adjust_positions_by_rules(
            element, positions, standard_code
        )
        
        # 6. 确定每个位置的支吊架类型和详图编号
        hangers = []
        for pos in positions:
            hanger_type = self._determine_hanger_type(element, pos)
            detail_code = self._select_detail_code(
                standard_code, hanger_type, element, seismic_grade
            )
            
            hangers.append({
                "position": pos,
                "hanger_type": hanger_type,
                "standard_code": standard_code,
                "detail_code": detail_code,
                "support_interval": max_spacing
            })
        
        return hangers
    
    def _get_element(self, element_id: str) -> Optional[ElementNode]:
        """获取元素信息"""
        query = "MATCH (e:Element {id: $element_id}) RETURN e"
        try:
            result = self.client.execute_query(query, {"element_id": element_id})
            if result:
                element_data = dict(result[0]["e"])
                return ElementNode(**element_data)
        except Exception as e:
            logger.error(f"Error getting element: {e}", exc_info=True)
        return None
    
    def _determine_standard(self, element_type: str) -> Optional[str]:
        """根据元素类型确定标准图集"""
        standards = self._config.get("standards", {})
        for code, config in standards.items():
            if element_type in config.get("element_types", []):
                return code
        return None
    
    def _calculate_max_spacing(
        self,
        element: ElementNode,
        standard_code: str,
        seismic_grade: Optional[str]
    ) -> float:
        """计算最大支撑间距"""
        standard_config = self._config.get("standards", {}).get(standard_code, {})
        spacing_rules = standard_config.get("spacing_rules", {})
        
        max_spacing = 3.0  # 默认间距（米）
        
        # 根据元素类型和参数选择间距规则
        if element.speckle_type == "Pipe":
            # 需要从element属性获取diameter
            element_dict = element.model_dump() if hasattr(element, 'model_dump') else element.dict()
            diameter = element_dict.get('diameter', 0)
            if diameter <= 0:
                # 尝试从geometry推断
                return max_spacing
            
            spacing_config = spacing_rules.get("horizontal", {})
            if diameter <= 25:
                max_spacing = spacing_config.get("DN15-DN25", {}).get("max_spacing", 2.5)
            elif diameter <= 40:
                max_spacing = spacing_config.get("DN32-DN40", {}).get("max_spacing", 3.0)
            elif diameter <= 80:
                max_spacing = spacing_config.get("DN50-DN80", {}).get("max_spacing", 4.0)
            elif diameter <= 150:
                max_spacing = spacing_config.get("DN100-DN150", {}).get("max_spacing", 5.0)
            else:
                max_spacing = spacing_config.get("DN200+", {}).get("max_spacing", 6.0)
        
        elif element.speckle_type == "Duct":
            element_dict = element.model_dump() if hasattr(element, 'model_dump') else element.dict()
            width = element_dict.get('width', 0)
            if width <= 0:
                return max_spacing
            
            spacing_config = spacing_rules.get("horizontal", {})
            if width <= 400:
                max_spacing = spacing_config.get("矩形_小截面", {}).get("max_spacing", 3.0)
            elif width <= 1250:
                max_spacing = spacing_config.get("矩形_中截面", {}).get("max_spacing", 3.75)
            elif width <= 2000:
                max_spacing = spacing_config.get("矩形_大截面", {}).get("max_spacing", 4.5)
            else:
                max_spacing = spacing_config.get("矩形_大截面", {}).get("max_spacing", 4.5)
        
        elif element.speckle_type == "CableTray":
            element_dict = element.model_dump() if hasattr(element, 'model_dump') else element.dict()
            width = element_dict.get('width', 0)
            if width <= 0:
                return max_spacing
            
            spacing_config = spacing_rules.get("horizontal", {})
            if width <= 100:
                max_spacing = spacing_config.get("宽度_50-100", {}).get("max_spacing", 1.5)
            elif width <= 200:
                max_spacing = spacing_config.get("宽度_100-200", {}).get("max_spacing", 2.0)
            elif width <= 400:
                max_spacing = spacing_config.get("宽度_200-400", {}).get("max_spacing", 2.5)
            else:
                max_spacing = spacing_config.get("宽度_400+", {}).get("max_spacing", 3.0)
        
        # 考虑抗震要求，减小间距
        if seismic_grade and seismic_grade != "6度":
            seismic_config = self._config.get("seismic_requirements", {}).get(
                "GB50981-2014", {}
            ).get("requirements", {}).get(seismic_grade, {})
            
            reduction = seismic_config.get("additional_spacing_reduction", 0.0)
            max_spacing = max_spacing * (1 - reduction)
        
        return max_spacing
    
    def _calculate_positions_along_path(
        self,
        element: ElementNode,
        max_spacing: float,
        standard_code: str
    ) -> List[List[float]]:
        """沿路径计算支吊架位置"""
        coordinates = element.geometry.coordinates
        if len(coordinates) < 2:
            return []
        
        positions = []
        total_length = 0.0
        segment_lengths = []
        
        # 计算总长度和各段长度
        for i in range(len(coordinates) - 1):
            p1 = coordinates[i]
            p2 = coordinates[i + 1]
            seg_len = math.sqrt(
                (p2[0] - p1[0])**2 + 
                (p2[1] - p1[1])**2 + 
                (p2[2] - p1[2])**2
            )
            segment_lengths.append(seg_len)
            total_length += seg_len
        
        # 沿路径等间距布置
        current_distance = 0.0
        while current_distance < total_length:
            pos = self._interpolate_position(
                coordinates, segment_lengths, current_distance
            )
            positions.append(pos)
            current_distance += max_spacing
        
        # 确保起点和终点有支吊架
        if positions and len(positions) > 0:
            start_pos = coordinates[0]
            end_pos = coordinates[-1]
            
            # 检查起点是否需要添加
            if self._distance(start_pos, positions[0]) > 0.5:
                positions.insert(0, start_pos)
            
            # 检查终点是否需要添加
            if self._distance(end_pos, positions[-1]) > 0.5:
                positions.append(end_pos)
        else:
            # 如果没有计算到位置，至少添加起点和终点
            positions = [coordinates[0], coordinates[-1]]
        
        return positions
    
    def _interpolate_position(
        self,
        coordinates: List[List[float]],
        segment_lengths: List[float],
        distance: float
    ) -> List[float]:
        """在路径上插值位置"""
        current_distance = 0.0
        for i, seg_len in enumerate(segment_lengths):
            if current_distance + seg_len >= distance:
                # 在这个段内
                t = (distance - current_distance) / seg_len if seg_len > 0 else 0.0
                p1 = coordinates[i]
                p2 = coordinates[i + 1]
                return [
                    p1[0] + t * (p2[0] - p1[0]),
                    p1[1] + t * (p2[1] - p1[1]),
                    p1[2] + t * (p2[2] - p1[2])
                ]
            current_distance += seg_len
        
        # 如果超出范围，返回最后一个点
        return coordinates[-1] if coordinates else [0.0, 0.0, 0.0]
    
    def _distance(self, p1: List[float], p2: List[float]) -> float:
        """计算两点间距离"""
        return math.sqrt(
            (p2[0] - p1[0])**2 + 
            (p2[1] - p1[1])**2 + 
            (p2[2] - p1[2])**2
        )
    
    def _adjust_positions_by_rules(
        self,
        element: ElementNode,
        positions: List[List[float]],
        standard_code: str
    ) -> List[List[float]]:
        """根据放置规则调整位置
        
        Args:
            element: MEP元素节点
            positions: 初步计算的支吊架位置列表
            standard_code: 标准图集代码
            
        Returns:
            调整后的支吊架位置列表
        """
        if not positions or len(element.geometry.coordinates) < 3:
            return positions
        
        coordinates = element.geometry.coordinates
        
        # 1. 检测接头位置（弯头、三通等）
        joint_positions = self._detect_joints(coordinates)
        
        # 2. 移除接头处的支吊架（接头前后0.3米范围内）
        adjusted_positions = []
        avoid_distance = 0.3  # 接头避让范围（米）
        
        for pos in positions:
            is_near_joint = False
            for joint_pos in joint_positions:
                if self._distance(pos, joint_pos) < avoid_distance:
                    is_near_joint = True
                    break
            if not is_near_joint:
                adjusted_positions.append(pos)
        
        # 3. 在接头附近（0.5米范围内）强制添加支吊架
        add_distance = 0.5  # 接头附近强制添加范围（米）
        
        for joint_pos in joint_positions:
            # 检查是否已有支吊架在附近
            has_nearby_hanger = False
            for pos in adjusted_positions:
                if self._distance(pos, joint_pos) < add_distance:
                    has_nearby_hanger = True
                    break
            
            if not has_nearby_hanger:
                # 在接头前后添加支吊架
                # 计算接头位置在路径上的参数t
                t, segment_index = self._find_position_on_path(coordinates, joint_pos)
                
                if segment_index is not None and segment_index < len(coordinates) - 1:
                    # 在接头前后0.5米处添加支吊架
                    p1 = coordinates[segment_index]
                    p2 = coordinates[segment_index + 1]
                    segment_length = self._distance(p1, p2)
                    
                    if segment_length > 0:
                        # 计算方向向量
                        direction = [
                            (p2[0] - p1[0]) / segment_length,
                            (p2[1] - p1[1]) / segment_length,
                            (p2[2] - p1[2]) / segment_length
                        ]
                        
                        # 接头前方0.5米
                        front_offset = min(0.5, segment_length * (1 - t))
                        front_pos = [
                            joint_pos[0] + direction[0] * front_offset,
                            joint_pos[1] + direction[1] * front_offset,
                            joint_pos[2] + direction[2] * front_offset
                        ]
                        adjusted_positions.append(front_pos)
                        
                        # 接头后方0.5米（如果还有空间）
                        if t * segment_length > 0.5:
                            back_offset = min(0.5, segment_length * t)
                            back_pos = [
                                joint_pos[0] - direction[0] * back_offset,
                                joint_pos[1] - direction[1] * back_offset,
                                joint_pos[2] - direction[2] * back_offset
                            ]
                            adjusted_positions.append(back_pos)
        
        # 4. 按路径顺序排序
        adjusted_positions = self._sort_positions_along_path(coordinates, adjusted_positions)
        
        return adjusted_positions
    
    def _detect_joints(self, coordinates: List[List[float]]) -> List[List[float]]:
        """检测路径中的接头位置（弯头、三通等）
        
        Args:
            coordinates: 路径坐标点列表
            
        Returns:
            接头位置列表
        """
        joints = []
        angle_threshold = math.radians(30)  # 30度角度阈值
        
        for i in range(1, len(coordinates) - 1):
            p1 = coordinates[i - 1]
            p2 = coordinates[i]
            p3 = coordinates[i + 1]
            
            # 计算角度
            angle = self._calculate_angle(p1, p2, p3)
            
            # 如果角度变化超过阈值，认为是接头
            if angle < (math.pi - angle_threshold):
                joints.append(p2)
        
        return joints
    
    def _calculate_angle(self, p1: List[float], p2: List[float], p3: List[float]) -> float:
        """计算三点形成的角度（以p2为顶点）
        
        Args:
            p1: 第一个点
            p2: 顶点
            p3: 第三个点
            
        Returns:
            角度（弧度），范围 [0, π]
        """
        # 计算向量
        v1 = [p1[0] - p2[0], p1[1] - p2[1], p1[2] - p2[2]]
        v2 = [p3[0] - p2[0], p3[1] - p2[1], p3[2] - p2[2]]
        
        # 计算向量长度
        len1 = math.sqrt(v1[0]**2 + v1[1]**2 + v1[2]**2)
        len2 = math.sqrt(v2[0]**2 + v2[1]**2 + v2[2]**2)
        
        if len1 == 0 or len2 == 0:
            return math.pi
        
        # 计算点积
        dot_product = v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2]
        
        # 计算夹角
        cos_angle = dot_product / (len1 * len2)
        cos_angle = max(-1.0, min(1.0, cos_angle))  # 限制在 [-1, 1] 范围内
        
        return math.acos(cos_angle)
    
    def _find_position_on_path(
        self,
        coordinates: List[List[float]],
        target_pos: List[float]
    ) -> Tuple[float, Optional[int]]:
        """查找目标位置在路径上的参数和段索引
        
        Args:
            coordinates: 路径坐标点列表
            target_pos: 目标位置
            
        Returns:
            (t, segment_index) 元组，t为在该段上的参数（0-1），segment_index为段索引
        """
        min_distance = float('inf')
        best_t = 0.0
        best_segment = None
        
        for i in range(len(coordinates) - 1):
            p1 = coordinates[i]
            p2 = coordinates[i + 1]
            
            # 计算点到线段的最近距离和参数t
            t, distance = self._point_to_segment_distance(target_pos, p1, p2)
            
            if distance < min_distance:
                min_distance = distance
                best_t = t
                best_segment = i
        
        return best_t, best_segment
    
    def _point_to_segment_distance(
        self,
        point: List[float],
        seg_start: List[float],
        seg_end: List[float]
    ) -> Tuple[float, float]:
        """计算点到线段的距离和参数t
        
        Args:
            point: 点坐标
            seg_start: 线段起点
            seg_end: 线段终点
            
        Returns:
            (t, distance) 元组，t为在线段上的参数（0-1），distance为距离
        """
        # 线段向量
        seg_vec = [seg_end[0] - seg_start[0], seg_end[1] - seg_start[1], seg_end[2] - seg_start[2]]
        
        # 点到起点的向量
        point_vec = [point[0] - seg_start[0], point[1] - seg_start[1], point[2] - seg_start[2]]
        
        # 线段长度的平方
        seg_len_sq = seg_vec[0]**2 + seg_vec[1]**2 + seg_vec[2]**2
        
        if seg_len_sq == 0:
            # 线段长度为0，返回起点
            return 0.0, self._distance(point, seg_start)
        
        # 计算投影参数t
        t = (point_vec[0] * seg_vec[0] + point_vec[1] * seg_vec[1] + point_vec[2] * seg_vec[2]) / seg_len_sq
        
        # 限制t在 [0, 1] 范围内
        t = max(0.0, min(1.0, t))
        
        # 计算投影点
        proj_point = [
            seg_start[0] + t * seg_vec[0],
            seg_start[1] + t * seg_vec[1],
            seg_start[2] + t * seg_vec[2]
        ]
        
        # 计算距离
        distance = self._distance(point, proj_point)
        
        return t, distance
    
    def _sort_positions_along_path(
        self,
        coordinates: List[List[float]],
        positions: List[List[float]]
    ) -> List[List[float]]:
        """按路径顺序对位置进行排序
        
        Args:
            coordinates: 路径坐标点列表
            positions: 需要排序的位置列表
            
        Returns:
            排序后的位置列表
        """
        if not positions:
            return []
        
        # 计算每个位置在路径上的累计距离
        position_distances = []
        for pos in positions:
            t, segment_index = self._find_position_on_path(coordinates, pos)
            
            # 计算累计距离
            cumulative_distance = 0.0
            for i in range(segment_index):
                cumulative_distance += self._distance(coordinates[i], coordinates[i + 1])
            
            # 加上在当前段上的距离
            if segment_index is not None and segment_index < len(coordinates) - 1:
                segment_start = coordinates[segment_index]
                segment_end = coordinates[segment_index + 1]
                segment_pos = [
                    segment_start[0] + t * (segment_end[0] - segment_start[0]),
                    segment_start[1] + t * (segment_end[1] - segment_start[1]),
                    segment_start[2] + t * (segment_end[2] - segment_start[2])
                ]
                cumulative_distance += self._distance(segment_start, segment_pos)
            
            position_distances.append((cumulative_distance, pos))
        
        # 按距离排序
        position_distances.sort(key=lambda x: x[0])
        
        return [pos for _, pos in position_distances]
    
    def _determine_hanger_type(
        self,
        element: ElementNode,
        position: List[float]
    ) -> str:
        """确定支吊架类型（支架或吊架）
        
        根据位置和周围结构判断：
        - 如果上方有结构（梁、板），使用吊架
        - 如果下方有结构（墙、柱），使用支架
        
        Args:
            element: MEP元素节点
            position: 支吊架位置 [x, y, z]
            
        Returns:
            "吊架" 或 "支架"
        """
        if not element.level_id:
            # 如果没有楼层信息，默认使用吊架
            return "吊架"
        
        try:
            # 获取元素的Z坐标（支吊架所在高度）
            z_position = position[2] if len(position) >= 3 else (element.base_offset or 0.0)
            
            # 查询该楼层内的结构元素（梁、板、墙、柱）
            query = """
            MATCH (s:Element)-[:LOCATED_AT]->(l:Level {id: $level_id})
            WHERE s.speckle_type IN ['Beam', 'Slab', 'Wall', 'Column']
                  AND s.height IS NOT NULL
                  AND s.base_offset IS NOT NULL
            RETURN s.id as id,
                   s.speckle_type as type,
                   s.base_offset as base_offset,
                   s.height as height
            """
            result = self.client.execute_query(query, {"level_id": element.level_id})
            
            # 判断上方和下方是否有结构
            has_structure_above = False  # 梁、板在上方 -> 使用吊架
            has_structure_below = False  # 墙、柱在下方 -> 使用支架
            
            for row in result:
                struct_type = row.get("type")
                struct_base = row.get("base_offset", 0.0) or 0.0
                struct_height = row.get("height", 0.0) or 0.0
                struct_top = struct_base + struct_height
                
                # 判断结构元素是否在支吊架位置附近（Z轴方向）
                # 简化判断：检查结构元素的Z范围是否与支吊架位置相交或接近
                # 如果结构的顶部在支吊架上方，认为是上方结构
                if struct_type in ['Beam', 'Slab']:
                    if struct_top > z_position:
                        # 梁或板的底部在支吊架上方或接近（允许0.5米容差）
                        if struct_base <= z_position + 0.5:
                            has_structure_above = True
                
                # 如果结构的底部在支吊架下方，认为是下方结构
                elif struct_type in ['Wall', 'Column']:
                    if struct_base < z_position:
                        # 墙或柱的顶部接近支吊架位置（允许0.5米容差）
                        if struct_top >= z_position - 0.5:
                            has_structure_below = True
            
            # 优先判断：如果上方有结构，使用吊架；如果下方有结构，使用支架
            if has_structure_above:
                return "吊架"
            elif has_structure_below:
                return "支架"
            else:
                # 如果都没有检测到，默认使用吊架（更常见的情况）
                return "吊架"
                
        except Exception as e:
            logger.warning(f"Error determining hanger type for element {element.id}: {e}")
            # 出错时默认使用吊架
            return "吊架"
    
    def _select_detail_code(
        self,
        standard_code: str,
        hanger_type: str,
        element: ElementNode,
        seismic_grade: Optional[str]
    ) -> str:
        """选择详图编号"""
        standard_config = self._config.get("standards", {}).get(standard_code, {})
        detail_codes = standard_config.get("detail_codes", {}).get(hanger_type, [])
        
        # 如果是抗震支吊架，选择抗震详图
        if seismic_grade and seismic_grade != "6度":
            seismic_config = self._config.get("seismic_requirements", {}).get(
                "GB50981-2014", {}
            ).get("requirements", {}).get(seismic_grade, {})
            
            seismic_codes = seismic_config.get("seismic_detail_codes", {})
            if standard_code in seismic_codes:
                return seismic_codes[standard_code]
        
        # 默认返回第一个详图编号
        return detail_codes[0] if detail_codes else f"{standard_code}-1"
    
    def generate_hangers(
        self,
        element_id: str,
        seismic_grade: Optional[str] = None,
        create_nodes: bool = True
    ) -> List[Dict[str, Any]]:
        """生成支吊架节点
        
        Args:
            element_id: MEP元素ID
            seismic_grade: 抗震等级
            create_nodes: 是否在数据库中创建节点
        
        Returns:
            生成的支吊架节点列表
        """
        # 1. 计算支吊架位置
        hanger_positions = self.calculate_hanger_positions(element_id, seismic_grade)
        
        # 2. 查询元素信息
        element = self._get_element(element_id)
        if not element:
            raise ValueError(f"Element not found: {element_id}")
        
        # 3. 创建支吊架节点
        hangers = []
        for idx, hanger_data in enumerate(hanger_positions):
            hanger_id = f"{element_id}_hanger_{idx + 1}"
            
            # 创建支吊架Element节点
            # 支吊架是点状元素，使用 Line 类型需要至少 2 个点，这里使用相同的起点和终点
            position = hanger_data["position"]
            hanger_element = ElementNode(
                id=hanger_id,
                speckle_type="Hanger",
                geometry=Geometry(
                    type="Line",
                    coordinates=[position, position],  # Line 需要至少 2 个点，使用相同点表示点状元素
                    closed=False
                ),
                level_id=element.level_id,
                material=hanger_data.get("material"),
            )
            
            # 添加支吊架特定属性
            hanger_props = hanger_element.to_cypher_properties()
            hanger_props.update({
                "hanger_type": hanger_data["hanger_type"],
                "standard_code": hanger_data["standard_code"],
                "detail_code": hanger_data["detail_code"],
                "supported_element_id": element_id,
                "supported_element_type": element.speckle_type,
                "support_interval": hanger_data["support_interval"],
                "seismic_grade": seismic_grade
            })
            
            if create_nodes:
                # 存储到数据库
                self._store_hanger(hanger_id, hanger_props, element_id)
            
            hangers.append({
                "id": hanger_id,
                **hanger_data
            })
        
        return hangers
    
    def _store_hanger(
        self,
        hanger_id: str,
        hanger_props: Dict[str, Any],
        supported_element_id: str
    ) -> None:
        """存储支吊架节点并创建关系"""
        # 1. 存储支吊架节点
        self.client.create_node("Element", hanger_props)
        
        # 2. 创建支吊架关系：Hanger SUPPORTS Element
        self.client.create_relationship(
            "Element", hanger_id,
            "Element", supported_element_id,
            SUPPORTS
        )
        
        # 3. 创建反向关系：Element HAS_HANGER Hanger
        self.client.create_relationship(
            "Element", supported_element_id,
            "Element", hanger_id,
            HAS_HANGER
        )
    
    def generate_integrated_hangers(
        self,
        space_id: str,
        element_ids: List[str],
        seismic_grade: Optional[str] = None,
        create_nodes: bool = True
    ) -> List[Dict[str, Any]]:
        """为空间内的成排管线生成综合支吊架
        
        Args:
            space_id: 空间ID
            element_ids: 要生成综合支吊架的元素ID列表
            seismic_grade: 抗震等级
            create_nodes: 是否在数据库中创建节点
        
        Returns:
            生成的综合支吊架节点列表
        """
        if len(element_ids) < 2:
            raise ValidationError(
                "综合支吊架至少需要2根管线",
                {"element_count": len(element_ids), "min_count": 2}
            )
        
        # 1. 获取所有元素
        elements = []
        for element_id in element_ids:
            element = self._get_element(element_id)
            if element:
                elements.append(element)
        
        if len(elements) < 2:
            raise ValidationError(
                "至少需要2个有效元素才能生成综合支吊架",
                {"valid_element_count": len(valid_elements), "min_count": 2}
            )
        
        # 2. 根据空间位置对元素分组（简化：所有元素为一组）
        grouped_elements = self._group_elements_by_spatial_proximity(elements)
        
        # 3. 为每组计算综合支吊架位置
        integrated_hangers = []
        for group in grouped_elements:
            positions = self._calculate_integrated_hanger_positions(group)
            
            for pos in positions:
                hanger_type = self._determine_hanger_type(group[0], pos)
                
                # 确定标准图集（使用第一个元素的类型）
                standard_code = self._determine_standard(group[0].speckle_type)
                if not standard_code:
                    continue
                
                detail_code = self._select_detail_code(
                    standard_code, hanger_type, group[0], seismic_grade
                )
                
                integrated_hangers.append({
                    "position": pos,
                    "hanger_type": hanger_type,
                    "standard_code": standard_code,
                    "detail_code": detail_code,
                    "supported_element_ids": [e.id for e in group],
                    "space_id": space_id
                })
        
        # 4. 创建综合支吊架节点
        created_hangers = []
        for idx, hanger_data in enumerate(integrated_hangers):
            hanger_id = f"{space_id}_integrated_hanger_{idx + 1}"
            
            # 创建综合支吊架Element节点
            # 综合支吊架是点状元素，使用 Line 类型需要至少 2 个点，这里使用相同的起点和终点
            position = hanger_data["position"]
            hanger_element = ElementNode(
                id=hanger_id,
                speckle_type="IntegratedHanger",
                geometry=Geometry(
                    type="Line",
                    coordinates=[position, position],  # Line 需要至少 2 个点，使用相同点表示点状元素
                    closed=False
                ),
                level_id=elements[0].level_id,
            )
            
            # 添加综合支吊架特定属性
            hanger_props = hanger_element.to_cypher_properties()
            hanger_props.update({
                "hanger_type": hanger_data["hanger_type"],
                "standard_code": hanger_data["standard_code"],
                "detail_code": hanger_data["detail_code"],
                "supported_element_ids": hanger_data["supported_element_ids"],
                "space_id": space_id,
                "seismic_grade": seismic_grade
            })
            
            if create_nodes:
                # 存储到数据库
                self._store_integrated_hanger(hanger_id, hanger_props, hanger_data["supported_element_ids"])
            
            created_hangers.append({
                "id": hanger_id,
                **hanger_data
            })
        
        return created_hangers
    
    def _group_elements_by_spatial_proximity(
        self,
        elements: List[ElementNode]
    ) -> List[List[ElementNode]]:
        """根据空间位置对元素分组
        
        Args:
            elements: 待分组的元素列表
            
        Returns:
            分组后的元素列表（每个子列表为一组）
        """
        if len(elements) < 2:
            return [elements] if elements else []
        
        # 读取配置中的空间接近度阈值
        # 对于综合支吊架，通常可以支撑距离2-3米的平行管线
        proximity_threshold = 2.0  # 默认值（米），比配置文件中的值更宽松
        try:
            integrated_config = self._config.get("integrated_hanger", {})
            configured_threshold = integrated_config.get("spatial_proximity_threshold", 0.5)
            if isinstance(configured_threshold, (int, float)):
                # 如果配置的值太小（< 1.5米），使用更宽松的默认值
                # 因为综合支吊架通常可以支撑距离更远的管线
                if float(configured_threshold) < 1.5:
                    proximity_threshold = 2.0
                else:
                    proximity_threshold = float(configured_threshold)
        except Exception as e:
            logger.warning(f"Failed to read spatial_proximity_threshold from config: {e}")
        
        # Z坐标容差（高度差异）
        z_tolerance = 0.5  # 米
        
        # 提取每根管线的关键点（起点、中点、终点）用于距离计算
        element_key_points = []
        for element in elements:
            coords = element.geometry.coordinates
            if len(coords) < 2:
                continue
            
            # 起点
            start_point = coords[0]
            # 终点
            end_point = coords[-1]
            # 中点（如果有多个点，取中间点）
            if len(coords) > 2:
                mid_index = len(coords) // 2
                mid_point = coords[mid_index]
            else:
                # 计算中点，处理Z坐标
                z1 = start_point[2] if len(start_point) > 2 else 0.0
                z2 = end_point[2] if len(end_point) > 2 else 0.0
                mid_point = [
                    (start_point[0] + end_point[0]) / 2,
                    (start_point[1] + end_point[1]) / 2,
                    (z1 + z2) / 2
                ]
            
            element_key_points.append({
                'element': element,
                'start': start_point,
                'mid': mid_point,
                'end': end_point,
                'base_offset': element.base_offset or 0.0
            })
        
        if len(element_key_points) < 2:
            return [elements]
        
        # 使用简单的聚类算法进行分组（贪心算法）
        groups: List[List[ElementNode]] = []
        used_indices = set()
        
        for i, elem_data1 in enumerate(element_key_points):
            if i in used_indices:
                continue
            
            # 创建新组
            current_group = [elem_data1['element']]
            used_indices.add(i)
            
            # 查找所有接近的元素
            changed = True
            while changed:
                changed = False
                for j, elem_data2 in enumerate(element_key_points):
                    if j in used_indices or j == i:
                        continue
                    
                    # 检查Z坐标差异
                    z_diff = abs(elem_data1['base_offset'] - elem_data2['base_offset'])
                    if z_diff > z_tolerance:
                        continue
                    
                    # 计算关键点之间的最小距离
                    # 对于平行管线，使用平均距离更合理
                    distances = []
                    for p1 in [elem_data1['start'], elem_data1['mid'], elem_data1['end']]:
                        for p2 in [elem_data2['start'], elem_data2['mid'], elem_data2['end']]:
                            dist = self._distance(p1, p2)
                            distances.append(dist)
                    
                    # 使用最小距离来判断是否接近（更宽松的判断）
                    min_distance = min(distances) if distances else float('inf')
                    
                    # 如果距离小于阈值，加入当前组
                    if min_distance <= proximity_threshold:
                        current_group.append(elem_data2['element'])
                        used_indices.add(j)
                        # 更新组的参考元素（使用新加入的元素）
                        elem_data1 = elem_data2
                        changed = True
            
            groups.append(current_group)
        
        return groups if groups else [elements]
    
    def _calculate_integrated_hanger_positions(
        self,
        elements: List[ElementNode]
    ) -> List[List[float]]:
        """计算综合支吊架位置（对齐多根管线）
        
        Args:
            elements: 需要对齐的多根管线元素列表
            
        Returns:
            综合支吊架位置列表（每个位置为 [x, y, z]）
        """
        if not elements:
            return []
        
        if len(elements) == 1:
            # 只有一根管线，使用该管线的位置
            standard_code = self._determine_standard(elements[0].speckle_type) or "03s402"
            return self._calculate_positions_along_path(elements[0], 3.0, standard_code)
        
        # 1. 找到所有管线的公共路径段
        common_segments = self._find_common_path_segments(elements)
        
        if not common_segments:
            # 如果没有公共路径，使用第一根管线的位置（降级处理）
            standard_code = self._determine_standard(elements[0].speckle_type) or "03s402"
            return self._calculate_positions_along_path(elements[0], 3.0, standard_code)
        
        # 2. 在公共路径上计算支吊架位置
        positions = []
        
        # 计算最大间距（使用所有管线的最大间距的最小值）
        max_spacing = 3.0  # 默认值
        for element in elements:
            standard_code = self._determine_standard(element.speckle_type)
            if standard_code:
                spacing = self._calculate_max_spacing(element, standard_code, None)
                max_spacing = min(max_spacing, spacing)
        
        # 在公共路径段上等间距布置支吊架
        for segment in common_segments:
            segment_length = self._distance(segment['start'], segment['end'])
            num_hangers = max(1, int(segment_length / max_spacing) + 1)
            
            for i in range(num_hangers):
                t = i / (num_hangers - 1) if num_hangers > 1 else 0.0
                pos = [
                    segment['start'][0] + t * (segment['end'][0] - segment['start'][0]),
                    segment['start'][1] + t * (segment['end'][1] - segment['start'][1]),
                    segment['z_max']  # 使用最高Z坐标
                ]
                positions.append(pos)
        
        # 去重（如果两个位置太接近）
        unique_positions = []
        for pos in positions:
            is_duplicate = False
            for existing_pos in unique_positions:
                if self._distance(pos, existing_pos) < 0.5:  # 0.5米去重阈值
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_positions.append(pos)
        
        return unique_positions if unique_positions else [self._get_center_position(elements)]
    
    def _find_common_path_segments(
        self,
        elements: List[ElementNode]
    ) -> List[Dict[str, Any]]:
        """找到多根管线的公共路径段
        
        Args:
            elements: 管线元素列表
            
        Returns:
            公共路径段列表，每个段包含 'start', 'end', 'z_max'
        """
        if len(elements) < 2:
            return []
        
        # 提取所有管线的路径段
        all_segments = []
        for element in elements:
            coords = element.geometry.coordinates
            base_offset = element.base_offset or 0.0
            
            for i in range(len(coords) - 1):
                start = coords[i]
                end = coords[i + 1]
                # 使用较高的Z坐标
                z_max = max(start[2] if len(start) > 2 else base_offset,
                           end[2] if len(end) > 2 else base_offset,
                           base_offset)
                all_segments.append({
                    'element': element,
                    'start': start,
                    'end': end,
                    'z_max': z_max
                })
        
        if not all_segments:
            return []
        
        # 使用第一根管线的第一个段作为参考
        reference_element = elements[0]
        reference_coords = reference_element.geometry.coordinates
        reference_base_offset = reference_element.base_offset or 0.0
        
        common_segments = []
        
        # 检查参考路径的每个段
        for i in range(len(reference_coords) - 1):
            ref_start = reference_coords[i]
            ref_end = reference_coords[i + 1]
            ref_z_max = max(ref_start[2] if len(ref_start) > 2 else reference_base_offset,
                           ref_end[2] if len(ref_end) > 2 else reference_base_offset,
                           reference_base_offset)
            
            # 检查其他管线是否有相似的段（允许一定的容差）
            tolerance = 0.5  # 0.5米容差
            overlapping_count = 0
            
            for other_element in elements[1:]:
                other_coords = other_element.geometry.coordinates
                other_base_offset = other_element.base_offset or 0.0
                
                has_overlap = False
                for j in range(len(other_coords) - 1):
                    other_start = other_coords[j]
                    other_end = other_coords[j + 1]
                    
                    # 检查线段是否重叠（简化的2D投影检查）
                    # 计算线段的中点距离
                    ref_mid = [
                        (ref_start[0] + ref_end[0]) / 2,
                        (ref_start[1] + ref_end[1]) / 2
                    ]
                    other_mid = [
                        (other_start[0] + other_end[0]) / 2,
                        (other_start[1] + other_end[1]) / 2
                    ]
                    
                    mid_distance_2d = math.sqrt(
                        (ref_mid[0] - other_mid[0])**2 +
                        (ref_mid[1] - other_mid[1])**2
                    )
                    
                    if mid_distance_2d < tolerance:
                        has_overlap = True
                        # 更新z_max为所有重叠段的最高值
                        other_z = max(other_start[2] if len(other_start) > 2 else other_base_offset,
                                     other_end[2] if len(other_end) > 2 else other_base_offset,
                                     other_base_offset)
                        ref_z_max = max(ref_z_max, other_z)
                        break
                
                if has_overlap:
                    overlapping_count += 1
            
            # 如果至少有一半的其他管线有重叠，认为是公共段
            if overlapping_count >= (len(elements) - 1) / 2:
                common_segments.append({
                    'start': ref_start,
                    'end': ref_end,
                    'z_max': ref_z_max
                })
        
        return common_segments
    
    def _get_center_position(self, elements: List[ElementNode]) -> List[float]:
        """计算所有管线元素的中心位置
        
        Args:
            elements: 管线元素列表
            
        Returns:
            中心位置 [x, y, z]
        """
        if not elements:
            return [0.0, 0.0, 0.0]
        
        total_x = 0.0
        total_y = 0.0
        total_z = 0.0
        count = 0
        
        for element in elements:
            coords = element.geometry.coordinates
            base_offset = element.base_offset or 0.0
            
            for coord in coords:
                total_x += coord[0] if len(coord) > 0 else 0.0
                total_y += coord[1] if len(coord) > 1 else 0.0
                z = coord[2] if len(coord) > 2 else base_offset
                total_z += z
                count += 1
        
        if count == 0:
            return [0.0, 0.0, 0.0]
        
        return [total_x / count, total_y / count, total_z / count]
    
    def _store_integrated_hanger(
        self,
        hanger_id: str,
        hanger_props: Dict[str, Any],
        supported_element_ids: List[str]
    ) -> None:
        """存储综合支吊架节点并创建关系"""
        # 1. 存储综合支吊架节点
        self.client.create_node("Element", hanger_props)
        
        # 2. 为每个被支撑元素创建关系
        for element_id in supported_element_ids:
            # Element USES_INTEGRATED_HANGER IntegratedHanger
            self.client.create_relationship(
                "Element", element_id,
                "Element", hanger_id,
                USES_INTEGRATED_HANGER
            )
