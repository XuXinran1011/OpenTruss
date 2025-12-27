"""Ontology 映射层

整合 Speckle 和 Brick Schema，提供类型映射和关系语义支持。

架构原则：
- Speckle: 物理节点定义（Nouns）— 描述"是什么"
- Brick Schema: 逻辑和关系（Verbs）— 描述"如何连接"
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from app.core.brick_validator import get_brick_validator, BrickSemanticValidator

logger = logging.getLogger(__name__)

# Speckle 到 Brick 映射文件路径
MAPPING_FILE = Path(__file__).parent / "speckle_brick_mapping.json"

# Brick 关系类型常量
BRICK_RELATIONSHIPS = {
    "FEEDS": "brick:feeds",
    "FEEDS_FROM": "brick:feedsFrom",
    "CONTROLS": "brick:controls",
    "HAS_PART": "brick:hasPart",
    "LOCATED_IN": "brick:locatedIn",
    "SERVES": "brick:serves",
}

# Memgraph 关系类型（用于实际存储）
# 注意：Memgraph 不支持冒号，所以使用下划线
MEMGRAPH_BRICK_RELATIONSHIPS = {
    "FEEDS": "FEEDS",
    "FEEDS_FROM": "FEEDS_FROM",
    "CONTROLS": "CONTROLS",
    "HAS_PART": "HAS_PART",
    "LOCATED_IN": "LOCATED_IN",
    "SERVES": "SERVES",
}

# 默认关系（当无法推断 Brick 关系时使用）
DEFAULT_RELATIONSHIP = "CONNECTS_TO"


class OntologyMapper:
    """Ontology 映射器
    
    提供 Speckle 到 Brick 类型转换和关系推断功能
    """
    
    def __init__(self, brick_validator: Optional[BrickSemanticValidator] = None):
        """初始化映射器
        
        Args:
            brick_validator: Brick 验证器实例（如果为 None，将创建新实例）
        """
        self.brick_validator = brick_validator or get_brick_validator()
        self._mapping: Dict[str, Any] = {}
        self._load_mapping()
    
    def _load_mapping(self) -> None:
        """加载 Speckle 到 Brick 类型映射"""
        try:
            with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
                self._mapping = json.load(f)
            logger.debug(f"Loaded Speckle-Brick mapping from {MAPPING_FILE}")
        except FileNotFoundError:
            logger.warning(f"Mapping file not found: {MAPPING_FILE}")
            self._mapping = {}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse mapping file: {e}")
            self._mapping = {}
    
    def speckle_to_brick_type(self, speckle_type: str) -> Optional[str]:
        """将 Speckle 类型转换为 Brick 类型
        
        Args:
            speckle_type: Speckle 元素类型（如：Pipe, Duct, Pump）
        
        Returns:
            Brick 类型 URI（如：brick:Water_Supply_Pipe），如果未找到则返回 None
        """
        return self.brick_validator.speckle_to_brick_type(speckle_type)
    
    def brick_to_speckle_type(self, brick_type: str) -> Optional[str]:
        """将 Brick 类型转换为 Speckle 类型（反向映射）
        
        Args:
            brick_type: Brick 类型 URI（如：brick:Water_Supply_Pipe）
        
        Returns:
            Speckle 类型（如：Pipe），如果未找到则返回 None
        """
        mappings = self._mapping.get("mappings", {})
        for speckle_type, brick_uri in mappings.items():
            if brick_uri == brick_type or brick_uri.endswith(brick_type.split(":")[-1]):
                return speckle_type
        return None
    
    def infer_relationship_type(
        self,
        source_type: str,
        target_type: str
    ) -> str:
        """根据源和目标类型推断 Brick 关系类型
        
        优先使用 Brick 语义关系，如果无匹配则回退到通用关系。
        
        Args:
            source_type: 源元素类型（Speckle 类型）
            target_type: 目标元素类型（Speckle 类型）
        
        Returns:
            关系类型（如：FEEDS, CONNECTS_TO）
        """
        # 获取允许的关系列表
        allowed_relationships = self.brick_validator.get_allowed_relationships(
            source_type,
            target_type
        )
        
        if allowed_relationships:
            # 返回第一个允许的关系（按优先级）
            # 优先级：FEEDS > FEEDS_FROM > CONTROLS > HAS_PART > LOCATED_IN > SERVES
            priority_order = ["feeds", "feeds_from", "controls", "has_part", "located_in", "serves"]
            
            for rel in priority_order:
                if rel in allowed_relationships:
                    # 转换为大写（Memgraph 关系类型）
                    return rel.upper().replace("_", "_")
            
            # 如果允许的关系不在优先级列表中，返回第一个
            return allowed_relationships[0].upper().replace("_", "_")
        
        # 如果没有匹配的 Brick 关系，返回默认关系
        return DEFAULT_RELATIONSHIP
    
    def get_allowed_relationships(
        self,
        source_type: str,
        target_type: str
    ) -> list[str]:
        """获取允许的关系类型列表
        
        Args:
            source_type: 源元素类型
            target_type: 目标元素类型
        
        Returns:
            允许的关系类型列表（如：["FEEDS", "CONTROLS"]）
        """
        allowed = self.brick_validator.get_allowed_relationships(source_type, target_type)
        # 转换为大写（Memgraph 关系类型）
        return [rel.upper().replace("_", "_") for rel in allowed]


# 全局映射器实例（单例模式）
_mapper: Optional[OntologyMapper] = None


def get_ontology_mapper() -> OntologyMapper:
    """获取全局 Ontology 映射器实例
    
    Returns:
        OntologyMapper 实例
    """
    global _mapper
    if _mapper is None:
        _mapper = OntologyMapper()
    return _mapper


# 便捷函数
def speckle_to_brick_type(speckle_type: str) -> Optional[str]:
    """将 Speckle 类型转换为 Brick 类型（便捷函数）
    
    Args:
        speckle_type: Speckle 元素类型
    
    Returns:
        Brick 类型 URI，如果未找到则返回 None
    """
    mapper = get_ontology_mapper()
    return mapper.speckle_to_brick_type(speckle_type)


def brick_to_speckle_type(brick_type: str) -> Optional[str]:
    """将 Brick 类型转换为 Speckle 类型（便捷函数）
    
    Args:
        brick_type: Brick 类型 URI
    
    Returns:
        Speckle 类型，如果未找到则返回 None
    """
    mapper = get_ontology_mapper()
    return mapper.brick_to_speckle_type(brick_type)


def infer_relationship_type(source_type: str, target_type: str) -> str:
    """推断关系类型（便捷函数）
    
    Args:
        source_type: 源元素类型
        target_type: 目标元素类型
    
    Returns:
        关系类型
    """
    mapper = get_ontology_mapper()
    return mapper.infer_relationship_type(source_type, target_type)

