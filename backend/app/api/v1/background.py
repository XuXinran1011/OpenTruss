"""底图管理 API

提供DWG底图上传、管理和操作接口
"""

import os
import uuid
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.utils.memgraph import get_memgraph_client, MemgraphClient
from datetime import datetime
from app.core.config import settings

router = APIRouter(prefix="/background", tags=["background"])

# 底图存储目录
BACKGROUND_DIR = Path(settings.data_dir) / "backgrounds"
BACKGROUND_DIR.mkdir(parents=True, exist_ok=True)

# 允许的图片格式
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


class BackgroundInfo(BaseModel):
    """底图信息"""
    id: str
    filename: str
    url: str
    size: int
    content_type: str
    created_at: str


class BackgroundListResponse(BaseModel):
    """底图列表响应"""
    items: List[BackgroundInfo]
    total: int


@router.post(
    "/upload",
    response_model=BackgroundInfo,
    summary="上传底图",
    description="上传DWG底图文件（支持图片格式）"
)
async def upload_background(
    file: UploadFile = File(..., description="底图文件"),
    client: MemgraphClient = Depends(get_memgraph_client)
):
    """上传底图文件
    
    Args:
        file: 上传的文件
        client: Memgraph客户端
        
    Returns:
        BackgroundInfo: 底图信息
        
    Raises:
        HTTPException: 如果文件格式不支持或文件过大
    """
    # 检查文件扩展名
    file_ext = Path(file.filename or "").suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件格式。支持的格式：{', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # 读取文件内容
    content = await file.read()
    file_size = len(content)
    
    # 检查文件大小
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件过大。最大允许大小：{MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
    # 生成唯一ID和文件名
    file_id = str(uuid.uuid4())
    safe_filename = f"{file_id}{file_ext}"
    file_path = BACKGROUND_DIR / safe_filename
    
    # 保存文件
    try:
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件保存失败：{str(e)}"
        )
    
    # 返回文件信息
    return BackgroundInfo(
        id=file_id,
        filename=file.filename or safe_filename,
        url=f"/api/v1/background/{file_id}",
        size=file_size,
        content_type=file.content_type or "image/jpeg",
        created_at=datetime.now().isoformat()
    )


@router.get(
    "/{background_id}",
    response_class=FileResponse,
    summary="获取底图",
    description="根据ID获取底图文件"
)
async def get_background(
    background_id: str,
    client: MemgraphClient = Depends(get_memgraph_client)
):
    """获取底图文件
    
    Args:
        background_id: 底图ID
        
    Returns:
        FileResponse: 底图文件
        
    Raises:
        HTTPException: 如果底图不存在
    """
    # 查找文件（通过ID前缀匹配）
    for file_path in BACKGROUND_DIR.glob(f"{background_id}.*"):
        if file_path.is_file():
            # 确定媒体类型
            ext = file_path.suffix.lower()
            media_type_map = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".gif": "image/gif",
                ".webp": "image/webp",
                ".bmp": "image/bmp",
            }
            media_type = media_type_map.get(ext, "image/jpeg")
            
            return FileResponse(
                path=file_path,
                media_type=media_type,
                filename=file_path.name
            )
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="底图不存在"
    )


@router.get(
    "",
    response_model=BackgroundListResponse,
    summary="获取底图列表",
    description="获取所有已上传的底图列表"
)
async def list_backgrounds(
    client: MemgraphClient = Depends(get_memgraph_client)
):
    """获取底图列表
    
    Returns:
        BackgroundListResponse: 底图列表
    """
    items = []
    
    for file_path in BACKGROUND_DIR.glob("*.*"):
        if file_path.is_file():
            ext = file_path.suffix.lower()
            if ext in ALLOWED_EXTENSIONS:
                file_id = file_path.stem
                file_size = file_path.stat().st_size
                
                media_type_map = {
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".png": "image/png",
                    ".gif": "image/gif",
                    ".webp": "image/webp",
                    ".bmp": "image/bmp",
                }
                content_type = media_type_map.get(ext, "image/jpeg")
                
                items.append(BackgroundInfo(
                    id=file_id,
                    filename=file_path.name,
                    url=f"/api/v1/background/{file_id}",
                    size=file_size,
                    content_type=content_type,
                    created_at=datetime.now().isoformat()
                ))
    
    return BackgroundListResponse(
        items=items,
        total=len(items)
    )


@router.delete(
    "/{background_id}",
    summary="删除底图",
    description="根据ID删除底图文件"
)
async def delete_background(
    background_id: str,
    client: MemgraphClient = Depends(get_memgraph_client)
):
    """删除底图文件
    
    Args:
        background_id: 底图ID
        
    Returns:
        dict: 删除结果
        
    Raises:
        HTTPException: 如果底图不存在
    """
    # 查找文件
    for file_path in BACKGROUND_DIR.glob(f"{background_id}.*"):
        if file_path.is_file():
            try:
                file_path.unlink()
                return {"id": background_id, "deleted": True}
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"文件删除失败：{str(e)}"
                )
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="底图不存在"
    )

