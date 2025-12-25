"""认证和授权模块

实现 JWT 认证和基于角色的访问控制（RBAC）
"""

import logging
from typing import Optional, List
from datetime import datetime, timedelta
from enum import Enum

import jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)

# JWT 安全方案
security = HTTPBearer()


class UserRole(str, Enum):
    """用户角色"""
    EDITOR = "EDITOR"  # 数据清洗工程师
    APPROVER = "APPROVER"  # 专业负责人/总工
    PM = "PM"  # 项目经理
    ADMIN = "ADMIN"  # 系统管理员


class User(BaseModel):
    """用户模型"""
    id: str
    username: str
    email: Optional[str] = None
    role: UserRole
    name: Optional[str] = None


class TokenData(BaseModel):
    """Token 数据"""
    user_id: str
    username: str
    role: UserRole


def create_access_token(
    user_id: str,
    username: str,
    role: UserRole,
    expires_delta: Optional[timedelta] = None
) -> str:
    """创建 JWT 访问令牌
    
    Args:
        user_id: 用户 ID
        username: 用户名
        role: 用户角色
        expires_delta: 过期时间增量（如果为 None，使用默认值）
        
    Returns:
        str: JWT token
    """
    if expires_delta is None:
        # 从配置获取过期时间，默认 30 分钟
        expire_minutes = settings.jwt_access_token_expire_minutes
        expires_delta = timedelta(minutes=expire_minutes)
    
    expire = datetime.utcnow() + expires_delta
    
    payload = {
        "sub": user_id,  # subject (用户 ID)
        "username": username,
        "role": role.value,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    
    # 使用配置中的密钥（如果没有，使用默认值）
    secret_key = getattr(settings, "jwt_secret_key", "your-secret-key-change-in-production")
    algorithm = getattr(settings, "jwt_algorithm", "HS256")
    
    token = jwt.encode(payload, secret_key, algorithm=algorithm)
    return token


def verify_token(token: str) -> Optional[TokenData]:
    """验证 JWT token
    
    Args:
        token: JWT token 字符串
        
    Returns:
        Optional[TokenData]: Token 数据，如果验证失败则返回 None
    """
    try:
        secret_key = getattr(settings, "jwt_secret_key", "your-secret-key-change-in-production")
        algorithm = getattr(settings, "jwt_algorithm", "HS256")
        
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        
        user_id = payload.get("sub")
        username = payload.get("username")
        role_str = payload.get("role")
        
        if not user_id or not username or not role_str:
            return None
        
        try:
            role = UserRole(role_str)
        except ValueError:
            return None
        
        return TokenData(
            user_id=user_id,
            username=username,
            role=role
        )
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """获取当前用户（依赖注入）
    
    Args:
        credentials: HTTP Bearer 凭证
        
    Returns:
        TokenData: 当前用户数据
        
    Raises:
        HTTPException: 如果认证失败
    """
    token = credentials.credentials
    token_data = verify_token(token)
    
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token_data


def require_role(allowed_roles: List[UserRole]):
    """角色权限检查装饰器（工厂函数）
    
    Args:
        allowed_roles: 允许的角色列表
        
    Returns:
        依赖注入函数
    """
    async def role_checker(current_user: TokenData = Depends(get_current_user)) -> TokenData:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[r.value for r in allowed_roles]}"
            )
        return current_user
    
    return role_checker


# 预定义的权限检查器
require_approver = require_role([UserRole.APPROVER, UserRole.PM, UserRole.ADMIN])
require_pm = require_role([UserRole.PM, UserRole.ADMIN])
require_admin = require_role([UserRole.ADMIN])


# Mock认证（用于开发环境，临时解决方案）
async def get_mock_user() -> TokenData:
    """Mock用户（用于开发环境，临时跳过认证）"""
    return TokenData(
        user_id="mock_user_id",
        username="mock_user",
        role=UserRole.APPROVER
    )


async def require_mock_approver() -> TokenData:
    """Mock审批者权限检查（用于开发环境）"""
    return await get_mock_user()


async def require_mock_pm() -> TokenData:
    """Mock PM权限检查（用于开发环境）"""
    mock_user = await get_mock_user()
    # 返回一个PM角色的mock用户
    return TokenData(
        user_id=mock_user.user_id,
        username=mock_user.username,
        role=UserRole.PM
    )
