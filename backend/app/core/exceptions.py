"""自定义异常定义模块

定义统一的异常类，用于服务层错误处理
"""


class OpenTrussError(Exception):
    """OpenTruss 基础异常类
    
    所有自定义异常的基类。提供统一的错误处理机制，支持错误消息和详细信息。
    """
    
    def __init__(self, message: str, details: dict = None):
        """初始化异常
        
        Args:
            message: 错误消息（用户友好的描述）
            details: 错误详情字典（可选，用于记录技术细节）
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}


class SpatialServiceError(OpenTrussError):
    """空间服务异常
    
    用于空间查询相关的错误，如查询Room/Space失败、bbox参数无效等。
    
    示例：
        ```python
        raise SpatialServiceError(
            "bbox 参数无效，必须包含4个值",
            {"bbox": invalid_bbox}
        )
        ```
    """
    pass


class RoutingServiceError(OpenTrussError):
    """路由服务异常
    
    用于路由规划相关的错误，如路径计算失败、参数验证失败等。
    
    示例：
        ```python
        raise RoutingServiceError(
            "起点和终点不能相同",
            {"start": start, "end": end}
        )
        ```
    """
    pass


class ValidationError(OpenTrussError):
    """验证异常
    
    用于数据验证相关的错误，如输入数据不符合规范等。
    
    示例：
        ```python
        raise ValidationError(
            "元素ID格式不正确",
            {"element_id": invalid_id}
        )
        ```
    """
    pass


class NotFoundError(OpenTrussError):
    """资源未找到异常
    
    用于资源不存在的情况，如元素、检验批、项目等不存在。
    
    示例：
        ```python
        raise NotFoundError(
            f"Element with id {element_id} not found",
            {"element_id": element_id, "resource_type": "Element"}
        )
        ```
    """
    pass


class ConflictError(OpenTrussError):
    """冲突异常
    
    用于资源冲突的情况，如元素已锁定、状态不允许操作等。
    
    示例：
        ```python
        raise ConflictError(
            f"Element {element_id} is locked and cannot be modified",
            {"element_id": element_id, "reason": "locked"}
        )
        ```
    """
    pass


class ConfigurationError(OpenTrussError):
    """配置异常
    
    用于配置相关的错误，如配置文件缺失、配置项无效等。
    
    示例：
        ```python
        raise ConfigurationError(
            "MEP路由配置文件未找到",
            {"config_path": config_path}
        )
        ```
    """
    pass

