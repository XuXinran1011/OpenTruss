"""认证API

提供登录、登出和用户信息查询接口
"""

from fastapi import APIRouter, HTTPException, status, Depends
from datetime import timedelta

from app.services.user import UserService
from app.models.api.auth import LoginRequest, LoginResponse, UserResponse
from app.core.auth import create_access_token, get_current_user, TokenData, UserRole
from app.utils.memgraph import get_memgraph_client, MemgraphClient
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


def get_user_service(
    client: MemgraphClient = Depends(get_memgraph_client)
) -> UserService:
    """获取 UserService 实例（依赖注入）"""
    return UserService(client=client)


@router.post(
    "/login",
    response_model=dict,
    summary="用户登录",
    description="使用用户名和密码登录，获取JWT访问令牌"
)
async def login(
    request: LoginRequest,
    service: UserService = Depends(get_user_service),
) -> dict:
    """用户登录"""
    # 验证用户凭据
    user = service.authenticate_user(request.username, request.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 生成JWT token
    expires_in = settings.jwt_access_token_expire_minutes * 60  # 转换为秒
    access_token = create_access_token(
        user_id=user.id,
        username=user.username,
        role=user.role,
        expires_delta=timedelta(minutes=settings.jwt_access_token_expire_minutes)
    )
    
    # 构建响应
    response = LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
        user=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            name=user.name
        )
    )
    
    return {
        "status": "success",
        "data": response.model_dump()
    }


@router.get(
    "/me",
    response_model=dict,
    summary="获取当前用户信息",
    description="获取当前登录用户的信息"
)
async def get_current_user_info(
    current_user: TokenData = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> dict:
    """获取当前用户信息"""
    # 从数据库获取完整用户信息
    user = service.get_user_by_id(current_user.user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    response = UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        name=user.name
    )
    
    return {
        "status": "success",
        "data": response.model_dump()
    }


@router.post(
    "/logout",
    response_model=dict,
    summary="用户登出",
    description="登出当前用户（JWT无状态，此接口主要用于记录日志）"
)
async def logout(
    current_user: TokenData = Depends(get_current_user),
) -> dict:
    """用户登出"""
    # JWT是无状态的，服务端不需要存储session
    # 客户端只需删除本地存储的token即可
    # 此接口主要用于记录登出日志（未来可扩展）
    
    return {
        "status": "success",
        "message": "登出成功"
    }

