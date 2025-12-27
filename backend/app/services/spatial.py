"""Space和Room查询服务

负责查询楼层内的Room和Space元素，验证路径是否穿过有效的空间
"""

"""Space和Room查询服务

负责查询楼层内的Room和Space元素，验证路径是否穿过有效的空间
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from app.core.cache import generate_cache_key, get_cache
from app.core.exceptions import SpatialServiceError
from app.models.speckle.base import Geometry
from app.models.speckle.spatial import Room, Space
from app.utils.memgraph import MemgraphClient
from app.core.exceptions import NotFoundError
from app.utils.spatial_filter import (
    bbox_intersects,
    calculate_geometry_bbox,
    filter_obstacles_by_bbox,
)

logger = logging.getLogger(__name__)


class SpatialService:
    """空间查询服务"""
    
    def __init__(self, client: Optional[MemgraphClient] = None):
        """初始化服务
        
        Args:
            client: Memgraph 客户端实例（如果为 None，将创建新实例）
        """
        self.client = client or MemgraphClient()
    
    def get_rooms_by_level(self, level_id: str) -> List[Room]:
        """查询楼层内的所有Room元素
        
        Args:
            level_id: 楼层ID
            
        Returns:
            Room元素列表
        """
        query = """
        MATCH (room:Element {speckle_type: 'Room'})-[:LOCATED_AT]->(level:Level {id: $level_id})
        RETURN room.id as id,
               room.speckle_id as speckle_id,
               room.speckle_type as speckle_type,
               room.geometry as geometry,
               room.level_id as level_id
        """
        
        results = self.client.execute_query(query, {"level_id": level_id})
        
        rooms = []
        for row in results:
            try:
                # 解析geometry
                geometry = None
                if row.get("geometry"):
                    if isinstance(row["geometry"], str):
                        geometry_data = json.loads(row["geometry"])
                    else:
                        geometry_data = row["geometry"]
                    geometry = Geometry(**geometry_data)
                
                # 注意：Room作为Element存储时，可能没有所有Room模型的字段
                # 我们只需要基本的id和geometry即可用于约束验证
                room = Room(
                    id=row["id"],
                    speckle_id=row.get("speckle_id"),
                    speckle_type="Room",
                    geometry=geometry,
                    level_id=row.get("level_id", level_id)
                )
                rooms.append(room)
            except Exception as e:
                logger.warning(f"Failed to parse Room {row.get('id')}: {e}")
                continue
        
        return rooms
    
    def get_spaces_by_level(self, level_id: str) -> List[Space]:
        """查询楼层内的所有Space元素
        
        Args:
            level_id: 楼层ID
            
        Returns:
            Space元素列表
        """
        query = """
        MATCH (space:Element {speckle_type: 'Space'})-[:LOCATED_AT]->(level:Level {id: $level_id})
        RETURN space.id as id,
               space.speckle_id as speckle_id,
               space.speckle_type as speckle_type,
               space.geometry as geometry,
               space.level_id as level_id,
               space.room_id as room_id,
               space.forbid_horizontal_mep as forbid_horizontal_mep,
               space.forbid_vertical_mep as forbid_vertical_mep
        """
        
        results = self.client.execute_query(query, {"level_id": level_id})
        
        spaces = []
        for row in results:
            try:
                # 解析geometry
                geometry = None
                if row.get("geometry"):
                    if isinstance(row["geometry"], str):
                        geometry_data = json.loads(row["geometry"])
                    else:
                        geometry_data = row["geometry"]
                    geometry = Geometry(**geometry_data)
                
                # 注意：Space作为Element存储时，可能没有所有Space模型的字段
                # 我们只需要用于约束验证的字段：id, geometry, room_id, forbid_horizontal_mep, forbid_vertical_mep
                space = Space(
                    id=row["id"],
                    speckle_id=row.get("speckle_id"),
                    speckle_type="Space",
                    geometry=geometry,
                    room_id=row.get("room_id"),
                    forbid_horizontal_mep=row.get("forbid_horizontal_mep", False),
                    forbid_vertical_mep=row.get("forbid_vertical_mep", False),
                    level_id=row.get("level_id", level_id)
                )
                spaces.append(space)
            except Exception as e:
                logger.warning(f"Failed to parse Space {row.get('id')}: {e}")
                continue
        
        return spaces
    
    def get_original_route_rooms(self, element_id: str) -> List[str]:
        """获取原始路由经过的Room ID列表
        
        从Element节点的original_route_room_ids属性中读取Room ID列表
        
        Args:
            element_id: 元素ID
            
        Returns:
            Room ID列表（不是Space ID）
        """
        query = """
        MATCH (e:Element {id: $element_id})
        RETURN e.original_route_room_ids as original_route_room_ids
        """
        
        results = self.client.execute_query(query, {"element_id": element_id})
        
        if not results or not results[0].get("original_route_room_ids"):
            return []
        
        room_ids = results[0]["original_route_room_ids"]
        if isinstance(room_ids, str):
            # 如果是字符串，尝试解析为JSON列表
            try:
                room_ids = json.loads(room_ids)
            except json.JSONDecodeError:
                # 如果解析失败，尝试按逗号分割
                room_ids = [r.strip() for r in room_ids.split(",") if r.strip()]
        
        if not isinstance(room_ids, list):
            return []
        
        return [str(rid) for rid in room_ids if rid]
    
    def validate_path_through_rooms_and_spaces(
        self,
        path_points: List[Tuple[float, float]],
        original_route_room_ids: List[str],
        level_id: str,
        forbid_horizontal: bool = False
    ) -> Dict[str, Any]:
        """验证路径是否符合Room和Space约束
        
        约束逻辑：
        1. 查询路径经过的所有Space
        2. 对于每个Space：
           - 如果Space.room_id存在且不在original_route_room_ids中 → 违反约束
           - 如果Space.room_id为None → 允许通过（不受原始路由约束限制）
           - 检查Space.forbid_horizontal_mep设置
        
        Args:
            path_points: 路径点列表 [(x, y), ...]
            original_route_room_ids: 原始路由经过的Room ID列表
            level_id: 楼层ID
            forbid_horizontal: 是否检查水平MEP限制（默认False）
            
        Returns:
            {
                "valid": bool,  # 是否通过验证
                "errors": List[str],  # 错误信息列表
                "warnings": List[str],  # 警告信息列表
                "passed_spaces": List[str],  # 通过的Space ID列表
                "blocked_spaces": List[str],  # 被阻止的Space ID列表
                "violated_rooms": List[str]  # 违反约束的Room ID列表
            }
        """
        errors = []
        warnings = []
        passed_spaces = []
        blocked_spaces = []
        violated_rooms = []
        
        if not path_points or len(path_points) < 2:
            return {
                "valid": True,
                "errors": [],
                "warnings": ["路径点数量不足，跳过验证"],
                "passed_spaces": [],
                "blocked_spaces": [],
                "violated_rooms": []
            }
        
        # 查询楼层内所有Space
        spaces = self.get_spaces_by_level(level_id)
        
        if not spaces:
            warnings.append(f"楼层 {level_id} 中没有找到Space元素")
            return {
                "valid": True,
                "errors": [],
                "warnings": warnings,
                "passed_spaces": [],
                "blocked_spaces": [],
                "violated_rooms": []
            }
        
        # 检查路径是否穿过每个Space
        original_route_room_set = set(original_route_room_ids) if original_route_room_ids else set()
        
        for space in spaces:
            if not space.geometry:
                continue
            
            # 检查路径是否穿过此Space
            if not self._path_intersects_space(path_points, space):
                continue
            
            # 检查Space限制设置
            if forbid_horizontal and space.forbid_horizontal_mep:
                blocked_spaces.append(space.id)
                errors.append(f"路径穿过了禁止水平MEP通过的空间 {space.name or space.id}")
                continue
            
            # 检查Room约束（仅当Space关联到Room时）
            if space.room_id:
                # 如果Space关联到Room，检查该Room是否在原始路由经过的Room列表中
                if space.room_id not in original_route_room_set:
                    violated_rooms.append(space.room_id)
                    blocked_spaces.append(space.id)
                    errors.append(
                        f"路径穿过了原始路由未经过的房间 {space.room_id} "
                        f"(Space: {space.name or space.id})"
                    )
                    continue
            
            # 通过所有检查，允许通过
            passed_spaces.append(space.id)
        
        valid = len(errors) == 0
        
        return {
            "valid": valid,
            "errors": errors,
            "warnings": warnings,
            "passed_spaces": passed_spaces,
            "blocked_spaces": blocked_spaces,
            "violated_rooms": violated_rooms
        }
    
    def _path_intersects_space(
        self,
        path_points: List[Tuple[float, float]],
        space: Space
    ) -> bool:
        """检查路径是否与Space相交
        
        使用简化的边界框检查。如果需要精确的交集判断，可以使用Shapely库。
        
        Args:
            path_points: 路径点列表
            space: Space元素
            
        Returns:
            是否相交
        """
        if not space.geometry or not space.geometry.coordinates:
            return False
        
        # 计算Space的边界框
        space_coords = space.geometry.coordinates
        space_min_x = min(coord[0] for coord in space_coords)
        space_max_x = max(coord[0] for coord in space_coords)
        space_min_y = min(coord[1] for coord in space_coords)
        space_max_y = max(coord[1] for coord in space_coords)
        
        # 检查路径的任何点是否在Space边界框内
        for point in path_points:
            x, y = point[0], point[1]
            if space_min_x <= x <= space_max_x and space_min_y <= y <= space_max_y:
                return True
        
        # 检查路径线段是否与Space边界框相交（简化：只检查路径的包围盒）
        path_min_x = min(point[0] for point in path_points)
        path_max_x = max(point[0] for point in path_points)
        path_min_y = min(point[1] for point in path_points)
        path_max_y = max(point[1] for point in path_points)
        
        # 检查包围盒是否相交
        if path_max_x < space_min_x or path_min_x > space_max_x:
            return False
        if path_max_y < space_min_y or path_min_y > space_max_y:
            return False
        
        return True
    
    def set_space_mep_restrictions(
        self,
        space_id: str,
        forbid_horizontal_mep: bool,
        forbid_vertical_mep: bool
    ) -> Dict[str, Any]:
        """设置空间MEP限制
        
        Args:
            space_id: 空间ID
            forbid_horizontal_mep: 是否禁止水平MEP穿过
            forbid_vertical_mep: 是否禁止竖向MEP穿过
            
        Returns:
            {
                "space_id": str,
                "forbid_horizontal_mep": bool,
                "forbid_vertical_mep": bool,
                "updated_at": str
            }
        """
        # 更新Space节点的属性
        query = """
        MATCH (space:Element {id: $space_id, speckle_type: 'Space'})
        SET space.forbid_horizontal_mep = $forbid_horizontal_mep,
            space.forbid_vertical_mep = $forbid_vertical_mep,
            space.updated_at = datetime()
        RETURN space.id as id,
               space.forbid_horizontal_mep as forbid_horizontal_mep,
               space.forbid_vertical_mep as forbid_vertical_mep,
               space.updated_at as updated_at
        """
        
        result = self.client.execute_query(
            query,
            {
                "space_id": space_id,
                "forbid_horizontal_mep": forbid_horizontal_mep,
                "forbid_vertical_mep": forbid_vertical_mep
            }
        )
        
        if not result:
            raise NotFoundError(
                f"Space {space_id} not found",
                {"space_id": space_id, "resource_type": "Space"}
            )
        
        row = result[0]
        updated_at = row.get("updated_at")
        if updated_at:
            # 将datetime对象转换为ISO格式字符串
            if hasattr(updated_at, 'isoformat'):
                updated_at_str = updated_at.isoformat()
            else:
                updated_at_str = str(updated_at)
        else:
            from datetime import datetime
            updated_at_str = datetime.utcnow().isoformat()
        
        return {
            "space_id": row["id"],
            "forbid_horizontal_mep": row["forbid_horizontal_mep"],
            "forbid_vertical_mep": row["forbid_vertical_mep"],
            "updated_at": updated_at_str
        }
    
    def set_space_integrated_hanger(
        self,
        space_id: str,
        use_integrated_hanger: bool
    ) -> Dict[str, Any]:
        """设置空间综合支吊架配置
        
        Args:
            space_id: 空间ID
            use_integrated_hanger: 是否使用综合支吊架
            
        Returns:
            {
                "space_id": str,
                "use_integrated_hanger": bool,
                "updated_at": str
            }
        """
        # 更新Space节点的属性
        query = """
        MATCH (space:Element {id: $space_id, speckle_type: 'Space'})
        SET space.use_integrated_hanger = $use_integrated_hanger,
            space.updated_at = datetime()
        RETURN space.id as id,
               space.use_integrated_hanger as use_integrated_hanger,
               space.updated_at as updated_at
        """
        
        result = self.client.execute_query(
            query,
            {
                "space_id": space_id,
                "use_integrated_hanger": use_integrated_hanger
            }
        )
        
        if not result:
            raise NotFoundError(
                f"Space {space_id} not found",
                {"space_id": space_id, "resource_type": "Space"}
            )
        
        row = result[0]
        updated_at = row.get("updated_at")
        if updated_at:
            # 将datetime对象转换为ISO格式字符串
            if hasattr(updated_at, 'isoformat'):
                updated_at_str = updated_at.isoformat()
            else:
                updated_at_str = str(updated_at)
        else:
            from datetime import datetime
            updated_at_str = datetime.utcnow().isoformat()
        
        return {
            "space_id": row["id"],
            "use_integrated_hanger": row.get("use_integrated_hanger", False),
            "updated_at": updated_at_str
        }
    
    def get_space_integrated_hanger(self, space_id: str) -> Dict[str, Any]:
        """获取空间综合支吊架配置
        
        Args:
            space_id: 空间ID
            
        Returns:
            {
                "space_id": str,
                "use_integrated_hanger": bool
            }
        """
        query = """
        MATCH (space:Element {id: $space_id, speckle_type: 'Space'})
        RETURN space.id as id,
               space.use_integrated_hanger as use_integrated_hanger
        """
        
        result = self.client.execute_query(query, {"space_id": space_id})
        
        if not result:
            raise NotFoundError(
                f"Space {space_id} not found",
                {"space_id": space_id, "resource_type": "Space"}
            )
        
        row = result[0]
        return {
            "space_id": row["id"],
            "use_integrated_hanger": row.get("use_integrated_hanger", False)
        }
    
    def get_space_mep_restrictions(self, space_id: str) -> Dict[str, Any]:
        """获取空间MEP限制
        
        Args:
            space_id: 空间ID
            
        Returns:
            {
                "space_id": str,
                "forbid_horizontal_mep": bool,
                "forbid_vertical_mep": bool
            }
        """
        query = """
        MATCH (space:Element {id: $space_id, speckle_type: 'Space'})
        RETURN space.id as id,
               space.forbid_horizontal_mep as forbid_horizontal_mep,
               space.forbid_vertical_mep as forbid_vertical_mep
        """
        
        result = self.client.execute_query(query, {"space_id": space_id})
        
        if not result:
            raise NotFoundError(
                f"Space {space_id} not found",
                {"space_id": space_id, "resource_type": "Space"}
            )
        
        row = result[0]
        return {
            "space_id": row["id"],
            "forbid_horizontal_mep": row.get("forbid_horizontal_mep", False),
            "forbid_vertical_mep": row.get("forbid_vertical_mep", False)
        }
    
    def _parse_geometry(
        self,
        element_id: str,
        geometry_data: Any
    ) -> Optional[Geometry]:
        """解析几何数据并转换为Geometry对象（3D 原生）
        
        这是一个辅助方法，用于统一处理几何数据的解析逻辑。
        
        Args:
            element_id: 元素ID（用于日志记录）
            geometry_data: 几何数据（可能是字符串或字典）
            
        Returns:
            Optional[Geometry]: Geometry对象（3D 原生），如果解析失败则返回None
        """
        if not geometry_data:
            return None
        
        # 解析几何数据
        if isinstance(geometry_data, str):
            try:
                geometry_dict = json.loads(geometry_data)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse geometry JSON for element {element_id}: {e}")
                return None
        else:
            geometry_dict = geometry_data
        
        # 转换为Geometry对象（支持2D和3D输入，自动规范化）
        try:
            obstacle_geometry = Geometry(
                type=geometry_dict.get("type", "Polyline"),
                coordinates=geometry_dict.get("coordinates", []),
                closed=geometry_dict.get("closed", False)
            )
            return obstacle_geometry
        except Exception as e:
            logger.warning(f"Failed to create Geometry for element {element_id}: {e}")
            return None
    
    def get_obstacles(
        self,
        level_id: str,
        bbox: Optional[List[float]] = None,  # [min_x, min_y, max_x, max_y]
        obstacle_types: Optional[List[str]] = None  # ["Beam", "Column", "Wall", "Slab", "Space"]
    ) -> Dict[str, Any]:
        """查询障碍物
        
        Args:
            level_id: 楼层ID
            bbox: 边界框 [min_x, min_y, max_x, max_y]（可选，不提供则查询整个楼层）
            obstacle_types: 障碍物类型列表（可选，默认查询所有类型）
            
        Returns:
            {
                "obstacles": List[Dict],  # 障碍物列表
                "total": int  # 障碍物总数
            }
            
        Raises:
            SpatialServiceError: 如果参数无效或查询失败
        """
        # 参数验证
        if not level_id:
            raise SpatialServiceError("level_id 不能为空")
        
        # 尝试从缓存获取
        cache = get_cache()
        cache_key = generate_cache_key(
            "obstacles",
            {
                "level_id": level_id,
                "bbox": bbox,
                "obstacle_types": sorted(obstacle_types) if obstacle_types else None
            }
        )
        
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for obstacles query: level_id={level_id}, bbox={bbox}")
            return cached_result
        
        logger.info(f"Querying obstacles: level_id={level_id}, bbox={bbox}, types={obstacle_types}")
        
        obstacles = []
        
        # 默认障碍物类型：结构元素和禁止MEP穿过的Space
        if obstacle_types is None:
            obstacle_types = ["Beam", "Column", "Wall", "Slab", "Space"]
        
        # 构建查询条件
        params = {"level_id": level_id}
        type_conditions = []
        
        # 分离结构类型和Space类型
        structure_types = [t for t in obstacle_types if t != "Space"]
        has_space = "Space" in obstacle_types
        
        # 构建结构类型条件
        if structure_types:
            for i, obs_type in enumerate(structure_types):
                param_name = f"type_{i}"
                type_conditions.append(f"obs.speckle_type = ${param_name}")
                params[param_name] = obs_type
        
        # 构建Space条件（只查询禁止MEP穿过的Space）
        if has_space:
            type_conditions.append("(obs.speckle_type = 'Space' AND (obs.forbid_horizontal_mep = true OR obs.forbid_vertical_mep = true))")
        
        # 构建WHERE子句
        if type_conditions:
            where_clause = "(" + " OR ".join(type_conditions) + ")"
        else:
            where_clause = "1=1"
        
        # 构建查询
        query = f"""
        MATCH (obs:Element)-[:LOCATED_AT]->(l:Level {{id: $level_id}})
        WHERE {where_clause}
        RETURN obs.id as id,
               obs.speckle_type as type,
               obs.geometry as geometry,
               obs.height as height,
               obs.base_offset as base_offset,
               obs.forbid_horizontal_mep as forbid_horizontal_mep,
               obs.forbid_vertical_mep as forbid_vertical_mep
        """
        
        result = self.client.execute_query(query, params)
        
        for row in result:
            obstacle_id = row.get("id")
            obstacle_type = row.get("type")
            geometry_data = row.get("geometry")
            height = row.get("height")
            base_offset = row.get("base_offset")
            forbid_horizontal_mep = row.get("forbid_horizontal_mep", False)
            forbid_vertical_mep = row.get("forbid_vertical_mep", False)
            
            if not geometry_data:
                continue
            
            # 解析几何数据并转换为Geometry对象（3D 原生）
            obstacle_geometry = self._parse_geometry(obstacle_id, geometry_data)
            if obstacle_geometry is None:
                continue
            
            obstacle_info = {
                "id": obstacle_id,
                "type": obstacle_type,
                "geometry": obstacle_geometry,
                "height": height,
                "base_offset": base_offset
            }
            
            # 如果是Space，添加MEP限制信息
            if obstacle_type == "Space":
                obstacle_info["forbid_horizontal_mep"] = forbid_horizontal_mep
                obstacle_info["forbid_vertical_mep"] = forbid_vertical_mep
            
            obstacles.append(obstacle_info)
        
        # 如果提供了bbox，过滤障碍物
        if bbox is not None:
            if len(bbox) != 4:
                raise SpatialServiceError(
                    "bbox 必须包含4个值: [min_x, min_y, max_x, max_y]",
                    {"bbox": bbox}
                )
            
            min_x, min_y, max_x, max_y = bbox
            
            # 验证bbox范围
            if min_x >= max_x or min_y >= max_y:
                raise SpatialServiceError(
                    "bbox 范围无效: min_x < max_x 且 min_y < max_y",
                    {"bbox": bbox}
                )
            
            query_bbox = (min_x, min_y, max_x, max_y)
            obstacles = filter_obstacles_by_bbox(obstacles, query_bbox)
            logger.debug(f"Filtered {len(obstacles)} obstacles by bbox {bbox}")
        
        result = {
            "obstacles": obstacles,
            "total": len(obstacles)
        }
        
        # 将结果存入缓存（TTL: 5分钟）
        cache.set(cache_key, result, ttl=300)
        logger.debug(f"Cached obstacles query result: {cache_key}")
        
        return result

