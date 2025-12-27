"""空间过滤工具模块

提供高效的几何边界框检查功能，用于空间查询优化
"""

from typing import List, Optional, Tuple
from app.models.speckle.base import Geometry


def calculate_bbox_from_points(points: List[List[float]]) -> Optional[Tuple[float, float, float, float]]:
    """从点列表计算边界框
    
    Args:
        points: 点列表 [[x1, y1], [x2, y2], ...]
        
    Returns:
        Optional[Tuple[float, float, float, float]]: 边界框 (min_x, min_y, max_x, max_y)，如果点列表为空则返回 None
    """
    if not points:
        return None
    
    min_x = min(p[0] for p in points if len(p) >= 2)
    min_y = min(p[1] for p in points if len(p) >= 2)
    max_x = max(p[0] for p in points if len(p) >= 2)
    max_y = max(p[1] for p in points if len(p) >= 2)
    
    return (min_x, min_y, max_x, max_y)


def calculate_geometry_bbox(geometry: Geometry) -> Optional[Tuple[float, float, float, float]]:
    """计算几何对象的边界框（3D 原生，使用 X/Y 坐标）
    
    Args:
        geometry: Geometry 对象（3D 坐标）
        
    Returns:
        Optional[Tuple[float, float, float, float]]: 边界框 (min_x, min_y, max_x, max_y)，如果几何无效则返回 None
    """
    if not geometry or not geometry.coordinates:
        return None
    
    # 提取 X, Y 坐标用于 2D 边界框计算（忽略 Z 坐标）
    xy_coords = [[coord[0], coord[1]] for coord in geometry.coordinates if len(coord) >= 2]
    return calculate_bbox_from_points(xy_coords)


def bbox_intersects(
    bbox1: Tuple[float, float, float, float],
    bbox2: Tuple[float, float, float, float]
) -> bool:
    """检查两个边界框是否相交
    
    Args:
        bbox1: 边界框1 (min_x, min_y, max_x, max_y)
        bbox2: 边界框2 (min_x, min_y, max_x, max_y)
        
    Returns:
        bool: 如果相交则返回 True
    """
    min_x1, min_y1, max_x1, max_y1 = bbox1
    min_x2, min_y2, max_x2, max_y2 = bbox2
    
    # 检查是否不相交（一个在另一个的左侧、右侧、上方或下方）
    if max_x1 < min_x2 or max_x2 < min_x1:
        return False
    if max_y1 < min_y2 or max_y2 < min_y1:
        return False
    
    return True


def bbox_contains_point(
    bbox: Tuple[float, float, float, float],
    point: Tuple[float, float]
) -> bool:
    """检查点是否在边界框内
    
    Args:
        bbox: 边界框 (min_x, min_y, max_x, max_y)
        point: 点坐标 (x, y)
        
    Returns:
        bool: 如果点在边界框内则返回 True
    """
    min_x, min_y, max_x, max_y = bbox
    x, y = point
    
    return min_x <= x <= max_x and min_y <= y <= max_y


def expand_bbox(
    bbox: Tuple[float, float, float, float],
    buffer: float
) -> Tuple[float, float, float, float]:
    """扩展边界框（添加缓冲区）
    
    Args:
        bbox: 原始边界框 (min_x, min_y, max_x, max_y)
        buffer: 缓冲区大小（单位：米）
        
    Returns:
        Tuple[float, float, float, float]: 扩展后的边界框
    """
    min_x, min_y, max_x, max_y = bbox
    return (min_x - buffer, min_y - buffer, max_x + buffer, max_y + buffer)


def calculate_route_bbox(
    start: Tuple[float, float],
    end: Tuple[float, float],
    buffer_ratio: float = 0.1
) -> Tuple[float, float, float, float]:
    """根据起点和终点计算路由边界框（带缓冲区）
    
    Args:
        start: 起点坐标 (x, y)
        end: 终点坐标 (x, y)
        buffer_ratio: 缓冲区比例（相对于边界框尺寸），默认 0.1 (10%)
        
    Returns:
        Tuple[float, float, float, float]: 边界框 (min_x, min_y, max_x, max_y)
    """
    min_x = min(start[0], end[0])
    min_y = min(start[1], end[1])
    max_x = max(start[0], end[0])
    max_y = max(start[1], end[1])
    
    # 计算边界框尺寸
    width = max_x - min_x
    height = max_y - min_y
    
    # 计算缓冲区大小（至少1米）
    buffer = max(width * buffer_ratio, height * buffer_ratio, 1.0)
    
    return expand_bbox((min_x, min_y, max_x, max_y), buffer)


def filter_obstacles_by_bbox(
    obstacles: List[dict],
    bbox: Tuple[float, float, float, float]
) -> List[dict]:
    """根据边界框过滤障碍物列表
    
    Args:
        obstacles: 障碍物列表，每个障碍物包含 'geometry' 字段（3D 原生）
        bbox: 边界框 (min_x, min_y, max_x, max_y)
        
    Returns:
        List[dict]: 过滤后的障碍物列表
    """
    filtered = []
    
    for obstacle in obstacles:
        geometry = obstacle.get("geometry")
        if not geometry:
            continue
        
        # 如果 geometry 是字典，转换为 Geometry 对象
        if isinstance(geometry, dict):
            from app.models.speckle.base import Geometry
            try:
                geometry = Geometry(**geometry)
            except Exception:
                continue
        
        # 计算障碍物的边界框
        obstacle_bbox = calculate_geometry_bbox(geometry)
        if obstacle_bbox is None:
            continue
        
        # 检查是否与查询边界框相交
        if bbox_intersects(bbox, obstacle_bbox):
            filtered.append(obstacle)
    
    return filtered

