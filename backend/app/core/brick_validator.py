"""Brick Schema 语义验证器

使用 Brick Schema 本体验证 MEP 连接的语义正确性
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Set, Tuple

try:
    from brickschema import Graph
    from rdflib import Namespace, URIRef
    BRICK_AVAILABLE = True
    # Brick Schema 命名空间
    BRICK = Namespace("https://brickschema.org/schema/Brick#")
except ImportError:
    BRICK_AVAILABLE = False
    Namespace = None  # type: ignore
    URIRef = None  # type: ignore
    BRICK = None  # type: ignore
    logger = logging.getLogger(__name__)
    logger.warning("brickschema or rdflib not installed. Brick validation will be disabled.")

logger = logging.getLogger(__name__)

# Speckle 到 Brick 映射文件路径
MAPPING_FILE = Path(__file__).parent / "speckle_brick_mapping.json"


class BrickSemanticValidator:
    """Brick Schema 语义验证器"""
    
    def __init__(
        self,
        mapping_file: Optional[Path] = None,
        load_brick_schema: bool = True
    ):
        """初始化验证器
        
        Args:
            mapping_file: Speckle 到 Brick 映射文件路径
            load_brick_schema: 是否加载 Brick Schema 本体（可能需要网络连接）
        """
        if not BRICK_AVAILABLE:
            logger.warning("Brick Schema libraries not available. Validation will use mapping file only.")
            self._brick_graph = None
        else:
            self._brick_graph = None
            if load_brick_schema:
                try:
                    self._brick_graph = Graph()
                    # 尝试加载 Brick Schema（可能需要网络连接或本地文件）
                    # 这里使用在线版本，实际部署时可以下载到本地
                    self._brick_graph.load_file("https://brickschema.org/schema/Brick.ttl")
                    logger.info("Brick Schema loaded successfully")
                except Exception as e:
                    logger.warning(f"Failed to load Brick Schema: {e}. Using mapping file only.")
        
        self.mapping_file = mapping_file or MAPPING_FILE
        self._mapping: Dict[str, Any] = {}
        self._load_mapping()
    
    def _load_mapping(self) -> None:
        """加载 Speckle 到 Brick 类型映射"""
        try:
            with open(self.mapping_file, 'r', encoding='utf-8') as f:
                self._mapping = json.load(f)
            logger.info(f"Loaded Speckle-Brick mapping from {self.mapping_file}")
        except FileNotFoundError:
            logger.error(f"Mapping file not found: {self.mapping_file}")
            self._mapping = {}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse mapping file: {e}")
            self._mapping = {}
    
    def speckle_to_brick_type(self, speckle_type: str) -> Optional[str]:
        """将 Speckle 类型转换为 Brick 类型
        
        Args:
            speckle_type: Speckle 元素类型
        
        Returns:
            Brick 类型 URI，如果未找到则返回 None
        """
        mappings = self._mapping.get("mappings", {})
        return mappings.get(speckle_type)
    
    def can_connect(
        self,
        source_type: str,
        target_type: str,
        relationship: str = "feeds"
    ) -> bool:
        """验证两种类型是否可以连接
        
        Args:
            source_type: 源元素类型（Speckle 类型）
            target_type: 目标元素类型（Speckle 类型）
            relationship: 关系类型（feeds, feeds_from, controls 等）
        
        Returns:
            是否可以连接
        """
        # 1. 转换 Speckle 类型到 Brick 类型
        source_brick = self.speckle_to_brick_type(source_type)
        target_brick = self.speckle_to_brick_type(target_type)
        
        if not source_brick or not target_brick:
            # 如果类型未映射，使用映射文件中的示例关系进行验证
            return self._check_mapping_examples(source_type, target_type, relationship)
        
        # 2. 如果有 Brick Graph，使用 SPARQL 查询验证
        if self._brick_graph:
            return self._query_brick_schema(source_brick, target_brick, relationship)
        
        # 3. 否则使用映射文件中的关系示例验证
        return self._check_mapping_examples(source_type, target_type, relationship)
    
    def _check_mapping_examples(
        self,
        source_type: str,
        target_type: str,
        relationship: str
    ) -> bool:
        """使用映射文件中的关系示例进行验证
        
        Args:
            source_type: 源元素类型
            target_type: 目标元素类型
            relationship: 关系类型
        
        Returns:
            是否可以连接
        """
        relationships = self._mapping.get("relationships", {})
        relationship_config = relationships.get(relationship, {})
        examples = relationship_config.get("examples", [])
        
        # 检查示例中是否包含该类型对
        for example in examples:
            if len(example) == 2:
                if example[0] == source_type and example[1] == target_type:
                    return True
        
        # 如果没有找到精确匹配，返回 False（严格模式）
        # 也可以返回 True（宽松模式），这里使用严格模式
        return False
    
    def _query_brick_schema(
        self,
        source_brick: str,
        target_brick: str,
        relationship: str
    ) -> bool:
        """使用 SPARQL 查询 Brick Schema 本体
        
        Args:
            source_brick: 源 Brick 类型 URI
            target_brick: 目标 Brick 类型 URI
            relationship: 关系类型
        
        Returns:
            是否可以连接
        """
        if not self._brick_graph:
            return False
        
        try:
            # 构建 SPARQL 查询
            # 这里简化处理，实际应该查询 Brick Schema 中的关系定义
            relationship_uri = BRICK[relationship]
            
            query = f"""
            PREFIX brick: <https://brickschema.org/schema/Brick#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            ASK {{
                ?source rdfs:subClassOf* <{source_brick}> .
                ?target rdfs:subClassOf* <{target_brick}> .
                ?source <{relationship_uri}> ?target .
            }}
            """
            
            result = self._brick_graph.query(query)
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to query Brick Schema: {e}")
            # 出错时回退到映射文件验证
            return False
    
    def get_allowed_relationships(
        self,
        source_type: str,
        target_type: str
    ) -> List[str]:
        """获取允许的关系类型列表
        
        Args:
            source_type: 源元素类型
            target_type: 目标元素类型
        
        Returns:
            允许的关系类型列表
        """
        allowed = []
        relationships = self._mapping.get("relationships", {})
        
        for rel_name, rel_config in relationships.items():
            examples = rel_config.get("examples", [])
            for example in examples:
                if len(example) == 2:
                    if example[0] == source_type and example[1] == target_type:
                        allowed.append(rel_name)
        
        return allowed
    
    def validate_mep_connection(
        self,
        source_type: str,
        target_type: str,
        relationship: str = "feeds"
    ) -> Dict[str, Any]:
        """验证 MEP 连接
        
        Args:
            source_type: 源元素类型
            target_type: 目标元素类型
            relationship: 关系类型
        
        Returns:
            验证结果字典
        """
        can_connect = self.can_connect(source_type, target_type, relationship)
        allowed_relationships = self.get_allowed_relationships(source_type, target_type)
        
        return {
            "valid": can_connect,
            "source_type": source_type,
            "target_type": target_type,
            "relationship": relationship,
            "allowed_relationships": allowed_relationships,
            "error": None if can_connect else f"{source_type} cannot {relationship} {target_type}",
            "suggestion": allowed_relationships[0] if not can_connect and allowed_relationships else None
        }


# 全局验证器实例（单例模式）
_validator: Optional[BrickSemanticValidator] = None


def get_brick_validator() -> BrickSemanticValidator:
    """获取全局 Brick 验证器实例
    
    Returns:
        BrickSemanticValidator 实例
    """
    global _validator
    if _validator is None:
        _validator = BrickSemanticValidator()
    return _validator

