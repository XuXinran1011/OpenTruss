"""查询结果缓存模块

实现基于内存的 LRU 缓存，用于缓存查询结果
"""

import time
from typing import Dict, Any, Optional, Callable
from collections import OrderedDict
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


class LRUCache:
    """LRU（最近最少使用）缓存实现
    
    使用 OrderedDict 实现 LRU 缓存，自动淘汰最久未使用的项
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """初始化 LRU 缓存
        
        Args:
            max_size: 最大缓存项数量（默认 1000）
            default_ttl: 默认 TTL（Time To Live）秒数（默认 300 秒，即 5 分钟）
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """生成缓存键
        
        Args:
            prefix: 缓存键前缀
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            str: 缓存键
        """
        # 将参数序列化为 JSON 字符串
        key_data = {
            "args": args,
            "kwargs": sorted(kwargs.items()) if kwargs else [],
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        # 使用 MD5 哈希生成固定长度的键
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            Optional[Any]: 缓存值，如果不存在或已过期则返回 None
        """
        if key not in self.cache:
            return None
        
        item = self.cache[key]
        
        # 检查是否过期
        if time.time() > item["expires_at"]:
            del self.cache[key]
            return None
        
        # 移动到末尾（标记为最近使用）
        self.cache.move_to_end(key)
        
        return item["value"]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: TTL（秒），如果为 None 则使用默认 TTL
        """
        if ttl is None:
            ttl = self.default_ttl
        
        expires_at = time.time() + ttl
        
        # 如果键已存在，更新值并移动到末尾
        if key in self.cache:
            self.cache[key] = {
                "value": value,
                "expires_at": expires_at,
            }
            self.cache.move_to_end(key)
            return
        
        # 如果缓存已满，删除最久未使用的项（第一个）
        if len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)
        
        # 添加新项
        self.cache[key] = {
            "value": value,
            "expires_at": expires_at,
        }
    
    def delete(self, key: str) -> None:
        """删除缓存项
        
        Args:
            key: 缓存键
        """
        if key in self.cache:
            del self.cache[key]
    
    def clear(self, prefix: Optional[str] = None) -> None:
        """清空缓存
        
        Args:
            prefix: 如果提供，只清空以该前缀开头的缓存项
        """
        if prefix is None:
            self.cache.clear()
        else:
            keys_to_delete = [key for key in self.cache.keys() if key.startswith(prefix)]
            for key in keys_to_delete:
                del self.cache[key]
    
    def invalidate(self, pattern: str) -> None:
        """使匹配模式的缓存项失效
        
        Args:
            pattern: 缓存键模式（支持前缀匹配）
        """
        keys_to_delete = [key for key in self.cache.keys() if key.startswith(pattern)]
        for key in keys_to_delete:
            del self.cache[key]
    
    def size(self) -> int:
        """获取当前缓存项数量"""
        return len(self.cache)


# 全局缓存实例
_cache: Optional[LRUCache] = None


def get_cache() -> LRUCache:
    """获取全局缓存实例（单例模式）
    
    Returns:
        LRUCache: 缓存实例
    """
    global _cache
    if _cache is None:
        _cache = LRUCache(max_size=1000, default_ttl=300)
    return _cache


def cache_result(ttl: int = 300, key_prefix: str = "cache"):
    """缓存装饰器
    
    用于缓存函数调用结果
    
    Args:
        ttl: TTL（秒），默认 300 秒（5 分钟）
        key_prefix: 缓存键前缀，默认 "cache"
    
    Usage:
        @cache_result(ttl=600, key_prefix="hierarchy")
        def get_project_hierarchy(project_id: str):
            ...
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            cache = get_cache()
            cache_key = cache._generate_key(key_prefix, *args, **kwargs)
            
            # 尝试从缓存获取
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_value
            
            # 缓存未命中，执行函数
            logger.debug(f"Cache miss: {cache_key}")
            result = func(*args, **kwargs)
            
            # 将结果存入缓存
            cache.set(cache_key, result, ttl=ttl)
            
            return result
        
        return wrapper
    return decorator


def generate_cache_key(endpoint: str, params: Dict[str, Any]) -> str:
    """生成缓存键（用于 API 端点）
    
    Args:
        endpoint: API 端点路径
        params: 查询参数字典
        
    Returns:
        str: 缓存键
    """
    cache = get_cache()
    return cache._generate_key(endpoint, **params)

