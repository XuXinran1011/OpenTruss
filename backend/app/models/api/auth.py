"""认证相关的API模型"""

from typing import Optional
from pydantic import BaseModel, Field, EmailStr, ConfigDict

from app.core.auth import UserRole


class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., description="用户名", min_length=1)
    password: str = Field(..., description="密码", min_length=1)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "admin",
                "password": "password123"
            }
        }
    )


class UserResponse(BaseModel):
    """用户信息响应"""
    id: str
    username: str
    email: Optional[str] = None
    role: UserRole
    name: Optional[str] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "user_001",
                "username": "admin",
                "email": "admin@example.com",
                "role": "ADMIN",
                "name": "管理员"
            }
        }
    )


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")
    user: UserResponse = Field(..., description="用户信息")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800,
                "user": {
                    "id": "user_001",
                    "username": "admin",
                    "email": "admin@example.com",
                    "role": "ADMIN",
                    "name": "管理员"
                }
            }
        }
    )

