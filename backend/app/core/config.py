"""配置管理

使用 pydantic-settings 管理应用配置
"""

from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """应用配置"""
    
    # Memgraph 配置
    memgraph_host: str = Field(default="localhost", description="Memgraph 主机地址")
    memgraph_port: int = Field(default=7687, description="Memgraph 端口")
    memgraph_user: str = Field(default="", description="Memgraph 用户名")
    memgraph_password: str = Field(default="", description="Memgraph 密码")
    
    # FastAPI 配置
    api_host: str = Field(default="0.0.0.0", description="API 主机地址")
    api_port: int = Field(default=8000, description="API 端口")
    api_reload: bool = Field(default=True, description="是否开启热重载")
    
    # 安全配置
    jwt_secret_key: str = Field(default="your-secret-key-here-change-in-production", description="JWT 密钥")
    jwt_algorithm: str = Field(default="HS256", description="JWT 算法")
    jwt_access_token_expire_minutes: int = Field(default=30, description="JWT 访问令牌过期时间（分钟）")
    
    # 日志配置
    log_level: str = Field(default="INFO", description="日志级别")
    log_file: str = Field(default="logs/opentruss.log", description="日志文件路径")
    
    # CORS 配置（使用字符串，用逗号分隔，解析时转换为列表）
    cors_origins_str: str = Field(
        default="http://localhost:3000,http://localhost:3001",
        description="CORS 允许的源（逗号分隔）"
    )
    
    @property
    def cors_origins(self) -> List[str]:
        """CORS 允许的源列表"""
        return [origin.strip() for origin in self.cors_origins_str.split(",") if origin.strip()]
    
    # 其他配置
    debug: bool = Field(default=False, description="调试模式")
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",  # 忽略额外的环境变量
    }


# 全局配置实例
settings = Settings()

