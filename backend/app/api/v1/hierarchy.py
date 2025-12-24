"""层级结构 API

提供 GB50300 层级结构的查询接口
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, status, Query, Depends

from app.services.hierarchy import HierarchyService
from app.models.api.hierarchy import (
    ProjectListItem,
    ProjectDetail,
    HierarchyResponse,
    BuildingDetail,
    DivisionDetail,
    SubDivisionDetail,
    ItemDetail,
    InspectionLotDetail,
)
from app.utils.memgraph import get_memgraph_client, MemgraphClient


router = APIRouter(prefix="/hierarchy", tags=["hierarchy"])


def get_hierarchy_service(
    client: MemgraphClient = Depends(get_memgraph_client)
) -> HierarchyService:
    """获取 Hierarchy Service 实例（依赖注入）"""
    return HierarchyService(client=client)


@router.get(
    "/projects",
    response_model=dict,
    summary="获取项目列表",
    description="获取所有项目的列表，支持分页"
)
async def get_projects(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    service: HierarchyService = Depends(get_hierarchy_service),
) -> dict:
    """获取项目列表"""
    result = service.get_projects(page=page, page_size=page_size)
    return {
        "status": "success",
        "data": result,
    }


@router.get(
    "/projects/{project_id}",
    response_model=dict,
    summary="获取项目详情",
    description="根据项目 ID 获取项目详细信息"
)
async def get_project(
    project_id: str,
    service: HierarchyService = Depends(get_hierarchy_service),
) -> dict:
    """获取项目详情"""
    project = service.get_project_detail(project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {project_id}",
        )
    
    return {
        "status": "success",
        "data": project.model_dump(),
    }


@router.get(
    "/projects/{project_id}/hierarchy",
    response_model=dict,
    summary="获取项目层级树",
    description="获取项目的完整层级结构树"
)
async def get_project_hierarchy(
    project_id: str,
    service: HierarchyService = Depends(get_hierarchy_service),
) -> dict:
    """获取项目层级树"""
    hierarchy = service.get_project_hierarchy(project_id)
    
    if not hierarchy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {project_id}",
        )
    
    return {
        "status": "success",
        "data": hierarchy.model_dump(),
    }


@router.get(
    "/buildings/{building_id}",
    response_model=dict,
    summary="获取单体详情",
    description="根据单体 ID 获取单体详细信息"
)
async def get_building(
    building_id: str,
    service: HierarchyService = Depends(get_hierarchy_service),
) -> dict:
    """获取单体详情"""
    building = service.get_building_detail(building_id)
    
    if not building:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Building not found: {building_id}",
        )
    
    return {
        "status": "success",
        "data": building.model_dump(),
    }


@router.get(
    "/divisions/{division_id}",
    response_model=dict,
    summary="获取分部详情",
    description="根据分部 ID 获取分部详细信息"
)
async def get_division(
    division_id: str,
    service: HierarchyService = Depends(get_hierarchy_service),
) -> dict:
    """获取分部详情"""
    division = service.get_division_detail(division_id)
    
    if not division:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Division not found: {division_id}",
        )
    
    return {
        "status": "success",
        "data": division.model_dump(),
    }


@router.get(
    "/subdivisions/{subdivision_id}",
    response_model=dict,
    summary="获取子分部详情",
    description="根据子分部 ID 获取子分部详细信息"
)
async def get_subdivision(
    subdivision_id: str,
    service: HierarchyService = Depends(get_hierarchy_service),
) -> dict:
    """获取子分部详情"""
    subdivision = service.get_subdivision_detail(subdivision_id)
    
    if not subdivision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SubDivision not found: {subdivision_id}",
        )
    
    return {
        "status": "success",
        "data": subdivision.model_dump(),
    }


@router.get(
    "/items/{item_id}",
    response_model=dict,
    summary="获取分项详情",
    description="根据分项 ID 获取分项详细信息（包含检验批列表）"
)
async def get_item(
    item_id: str,
    service: HierarchyService = Depends(get_hierarchy_service),
) -> dict:
    """获取分项详情"""
    item = service.get_item_detail(item_id)
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item not found: {item_id}",
        )
    
    return {
        "status": "success",
        "data": item.model_dump(),
    }


@router.get(
    "/inspection-lots/{lot_id}",
    response_model=dict,
    summary="获取检验批详情",
    description="根据检验批 ID 获取检验批详细信息（包含构件列表）"
)
async def get_inspection_lot(
    lot_id: str,
    service: HierarchyService = Depends(get_hierarchy_service),
) -> dict:
    """获取检验批详情"""
    lot = service.get_inspection_lot_detail(lot_id)
    
    if not lot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"InspectionLot not found: {lot_id}",
        )
    
    return {
        "status": "success",
        "data": lot.model_dump(),
    }


