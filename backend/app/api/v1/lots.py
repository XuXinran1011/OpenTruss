"""检验批管理 API

提供检验批创建、管理和操作接口
"""

from typing import List
from fastapi import APIRouter, HTTPException, status, Depends

from app.services.lot_strategy import LotStrategyService, RuleType
from app.services.hierarchy import HierarchyService
from app.models.api.lots import (
    CreateLotsByRuleRequest,
    CreateLotsResponse,
    CreatedLotInfo,
    AssignElementsRequest,
    AssignElementsResponse,
    RemoveElementsRequest,
    RemoveElementsResponse,
    UpdateLotStatusRequest,
    UpdateLotStatusResponse,
    LotElementsResponse,
    LotElementListItem,
)
from app.utils.memgraph import get_memgraph_client, MemgraphClient, convert_neo4j_datetime
from datetime import datetime

router = APIRouter(prefix="/lots", tags=["lots"])


def get_lot_strategy_service(
    client: MemgraphClient = Depends(get_memgraph_client)
) -> LotStrategyService:
    """获取 LotStrategyService 实例（依赖注入）"""
    return LotStrategyService(client=client)


def get_hierarchy_service(
    client: MemgraphClient = Depends(get_memgraph_client)
):
    """获取 HierarchyService 实例（依赖注入）"""
    from app.services.hierarchy import HierarchyService
    return HierarchyService(client=client)


@router.post(
    "/create-by-rule",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="根据规则批量创建检验批",
    description="根据指定的规则类型（按楼层/区域/组合）批量创建检验批并分配构件"
)
async def create_lots_by_rule(
    request: CreateLotsByRuleRequest,
    service: LotStrategyService = Depends(get_lot_strategy_service),
) -> dict:
    """根据规则批量创建检验批"""
    try:
        # 验证规则类型
        try:
            rule_type = RuleType(request.rule_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid rule_type: {request.rule_type}. Must be one of: BY_LEVEL, BY_ZONE, BY_LEVEL_AND_ZONE"
            )
        
        # 执行创建
        result = service.create_lots_by_rule(
            item_id=request.item_id,
            rule_type=rule_type
        )
        
        # 转换为响应格式
        lots_created = [
            CreatedLotInfo(
                id=lot["id"],
                name=lot["name"],
                spatial_scope=lot["spatial_scope"],
                element_count=lot["element_count"]
            )
            for lot in result["lots_created"]
        ]
        
        response = CreateLotsResponse(
            lots_created=lots_created,
            elements_assigned=result["elements_assigned"],
            total_lots=result["total_lots"]
        )
        
        return {
            "status": "success",
            "data": response.model_dump()
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create lots: {str(e)}"
        )


@router.post(
    "/{lot_id}/assign-elements",
    response_model=dict,
    summary="分配构件到检验批",
    description="手动将构件分配到指定的检验批"
)
async def assign_elements_to_lot(
    lot_id: str,
    request: AssignElementsRequest,
    service: LotStrategyService = Depends(get_lot_strategy_service),
) -> dict:
    """分配构件到检验批"""
    try:
        assigned_count = service.assign_elements_to_lot(
            lot_id=lot_id,
            element_ids=request.element_ids
        )
        
        response = AssignElementsResponse(
            lot_id=lot_id,
            assigned_count=assigned_count,
            total_requested=len(request.element_ids)
        )
        
        return {
            "status": "success",
            "data": response.model_dump()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign elements: {str(e)}"
        )


@router.post(
    "/{lot_id}/remove-elements",
    response_model=dict,
    summary="从检验批移除构件",
    description="从指定的检验批中移除构件"
)
async def remove_elements_from_lot(
    lot_id: str,
    request: RemoveElementsRequest,
    service: LotStrategyService = Depends(get_lot_strategy_service),
) -> dict:
    """从检验批移除构件"""
    try:
        removed_count = service.remove_elements_from_lot(
            lot_id=lot_id,
            element_ids=request.element_ids
        )
        
        response = RemoveElementsResponse(
            lot_id=lot_id,
            removed_count=removed_count,
            total_requested=len(request.element_ids)
        )
        
        return {
            "status": "success",
            "data": response.model_dump()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove elements: {str(e)}"
        )


@router.patch(
    "/{lot_id}/status",
    response_model=dict,
    summary="更新检验批状态",
    description=(
        "更新检验批的状态。"
        "允许的转换：PLANNING -> IN_PROGRESS -> SUBMITTED -> PUBLISHED。"
        "注意：SUBMITTED -> APPROVED 必须通过审批端点（/lots/{lot_id}/approve）完成。"
    )
)
async def update_lot_status(
    lot_id: str,
    request: UpdateLotStatusRequest,
    service: LotStrategyService = Depends(get_lot_strategy_service),
    hierarchy_service = Depends(get_hierarchy_service),
) -> dict:
    """更新检验批状态"""
    try:
        # 验证检验批存在
        lot_detail = hierarchy_service.get_inspection_lot_detail(lot_id)
        if not lot_detail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"InspectionLot not found: {lot_id}"
            )
        
        old_status = lot_detail.status
        new_status = request.status
        
        # 验证状态转换
        # 注意：SUBMITTED -> APPROVED 只能通过审批端点（/lots/{lot_id}/approve）完成
        # 此端点不允许该转换，以确保审批流程的完整性
        valid_transitions = {
            "PLANNING": ["IN_PROGRESS"],
            "IN_PROGRESS": ["SUBMITTED"],
            # SUBMITTED -> APPROVED 必须通过审批端点，不能直接转换
            "APPROVED": ["PUBLISHED"],
            "PUBLISHED": []  # 最终状态
        }
        
        if new_status not in valid_transitions.get(old_status, []):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status transition from {old_status} to {new_status}"
            )
        
        # 如果转换为 SUBMITTED，需要验证所有构件都有完整几何信息
        if new_status == "SUBMITTED":
            # 获取检验批下的所有构件
            elements_query = """
            MATCH (lot:InspectionLot {id: $lot_id})-[:MANAGEMENT_CONTAINS]->(e:Element)
            RETURN e.id as id, e.height as height, e.material as material, e.geometry_2d as geometry_2d
            """
            elements = service.client.execute_query(elements_query, {"lot_id": lot_id})
            
            incomplete_elements = []
            for elem in elements:
                if not elem.get("height") or not elem.get("material") or not elem.get("geometry_2d"):
                    incomplete_elements.append(elem.get("id"))
            
            if incomplete_elements:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot submit lot: {len(incomplete_elements)} elements are missing required data (height, material, or geometry_2d)"
                )
        
        # 更新状态
        update_query = """
        MATCH (lot:InspectionLot {id: $lot_id})
        SET lot.status = $new_status, lot.updated_at = datetime()
        RETURN lot.id as id, lot.status as status
        """
        result = service.client.execute_query(update_query, {
            "lot_id": lot_id,
            "new_status": new_status
        })
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update lot status"
            )
        
        # 获取更新时间
        updated_at_query = """
        MATCH (lot:InspectionLot {id: $lot_id})
        RETURN lot.updated_at as updated_at
        """
        updated_result = service.client.execute_query(updated_at_query, {"lot_id": lot_id})
        updated_at = convert_neo4j_datetime(updated_result[0]["updated_at"]) if updated_result else datetime.now()
        
        response = UpdateLotStatusResponse(
            lot_id=lot_id,
            old_status=old_status,
            new_status=new_status,
            updated_at=updated_at
        )
        
        return {
            "status": "success",
            "data": response.model_dump()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update lot status: {str(e)}"
        )


@router.get(
    "/{lot_id}/elements",
    response_model=dict,
    summary="获取检验批下的构件列表",
    description="获取指定检验批下的所有构件"
)
async def get_lot_elements(
    lot_id: str,
    service: LotStrategyService = Depends(get_lot_strategy_service),
    hierarchy_service = Depends(get_hierarchy_service),
) -> dict:
    """获取检验批下的构件列表"""
    try:
        # 验证检验批存在
        lot_detail = hierarchy_service.get_inspection_lot_detail(lot_id)
        if not lot_detail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"InspectionLot not found: {lot_id}"
            )
        
        # 查询构件列表
        query = """
        MATCH (lot:InspectionLot {id: $lot_id})-[:MANAGEMENT_CONTAINS]->(e:Element)
        RETURN e.id as id, e.speckle_type as speckle_type, e.level_id as level_id,
               e.zone_id as zone_id, e.status as status, e.height as height, e.material as material
        ORDER BY e.id
        """
        elements = service.client.execute_query(query, {"lot_id": lot_id})
        
        items = [
            LotElementListItem(
                id=elem["id"],
                speckle_type=elem["speckle_type"],
                level_id=elem.get("level_id"),
                zone_id=elem.get("zone_id"),
                status=elem.get("status", "Draft"),
                has_height=elem.get("height") is not None,
                has_material=elem.get("material") is not None
            )
            for elem in elements
        ]
        
        response = LotElementsResponse(
            lot_id=lot_id,
            items=items,
            total=len(items)
        )
        
        return {
            "status": "success",
            "data": response.model_dump()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get lot elements: {str(e)}"
        )

