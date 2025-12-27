"""语义验证器

基于 Brick Schema 的语义验证，检查连接是否符合逻辑规则。
"""

import logging
from typing import Dict, Any, Optional

from app.core.brick_validator import get_brick_validator, BrickSemanticValidator
from app.models.gb50300.element import ElementNode

logger = logging.getLogger(__name__)


class ValidationResult:
    """验证结果"""
    
    def __init__(
        self,
        valid: bool,
        error: Optional[str] = None,
        suggestion: Optional[str] = None,
        allowed_relationships: Optional[list[str]] = None
    ):
        self.valid = valid
        self.error = error
        self.suggestion = suggestion
        self.allowed_relationships = allowed_relationships or []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "valid": self.valid,
            "error": self.error,
            "suggestion": self.suggestion,
            "allowed_relationships": self.allowed_relationships
        }


class SemanticValidator:
    """语义验证器
    
    基于 Brick Schema 验证连接是否符合逻辑规则
    """
    
    def __init__(self, brick_validator: Optional[BrickSemanticValidator] = None):
        """初始化验证器
        
        Args:
            brick_validator: Brick 验证器实例（如果为 None，将创建新实例）
        """
        self.brick_validator = brick_validator or get_brick_validator()
    
    def validate_connection(
        self,
        source_element: ElementNode,
        target_element: ElementNode,
        relationship: str
    ) -> ValidationResult:
        """验证连接是否符合 Brick Schema 逻辑
        
        Args:
            source_element: 源元素
            target_element: 目标元素
            relationship: 关系类型（如：FEEDS, CONNECTS_TO）
        
        Returns:
            ValidationResult: 验证结果
        """
        # 将关系类型转换为小写（Brick 验证器使用小写）
        relationship_lower = relationship.lower().replace("_", "_")
        
        # 使用 Brick 验证器验证连接
        result = self.brick_validator.validate_mep_connection(
            source_element.speckle_type,
            target_element.speckle_type,
            relationship_lower
        )
        
        return ValidationResult(
            valid=result["valid"],
            error=result.get("error"),
            suggestion=result.get("suggestion"),
            allowed_relationships=result.get("allowed_relationships", [])
        )
    
    def validate_batch_connections(
        self,
        connections: list[tuple[ElementNode, ElementNode, str]]
    ) -> Dict[str, Any]:
        """批量验证连接
        
        Args:
            connections: 连接列表，每个元素为 (source_element, target_element, relationship)
        
        Returns:
            验证结果字典，包含：
            - valid: 是否所有连接都有效
            - errors: 错误列表
            - warnings: 警告列表
        """
        errors = []
        warnings = []
        all_valid = True
        
        for source, target, relationship in connections:
            result = self.validate_connection(source, target, relationship)
            
            if not result.valid:
                all_valid = False
                error_msg = (
                    f"{source.speckle_type} ({source.id}) cannot {relationship} "
                    f"{target.speckle_type} ({target.id})"
                )
                if result.error:
                    error_msg += f": {result.error}"
                errors.append(error_msg)
                
                if result.suggestion:
                    warnings.append(
                        f"建议使用关系: {result.suggestion} "
                        f"for {source.speckle_type} -> {target.speckle_type}"
                    )
        
        return {
            "valid": all_valid,
            "errors": errors,
            "warnings": warnings
        }


# 全局验证器实例（单例模式）
_validator: Optional[SemanticValidator] = None


def get_semantic_validator() -> SemanticValidator:
    """获取全局语义验证器实例
    
    Returns:
        SemanticValidator 实例
    """
    global _validator
    if _validator is None:
        _validator = SemanticValidator()
    return _validator

