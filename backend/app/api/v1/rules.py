"""规则管理 API

提供规则查询和预览接口
"""

import logging
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Dict, Any, Optional

from app.models.api.rules import (
    RulePreviewRequest,
    RulePreviewResponse,
    RuleListResponse,
    RuleInfo,
)
from app.services.lot_strategy import LotStrategyService, RuleType
from app.utils.memgraph import get_memgraph_client, MemgraphClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rules", tags=["rules"])


def get_lot_strategy_service(
    client: MemgraphClient = Depends(get_memgraph_client)
) -> LotStrategyService:
    """获取 LotStrategyService 实例（依赖注入）"""
    return LotStrategyService(client=client)


@router.get(
    "",
    response_model=Dict[str, Any],
    summary="获取规则列表",
    description="获取可用的检验批划分规则列表"
)
async def get_rules() -> Dict[str, Any]:
    """获取规则列表"""
    try:
        rules = [
            RuleInfo(
                rule_type="BY_LEVEL",
                name="按楼层划分",
                description="根据构件的楼层（Level）自动分组创建检验批"
            ),
            RuleInfo(
                rule_type="BY_ZONE",
                name="按区域划分",
                description="根据构件的区域（Zone）自动分组创建检验批"
            ),
            RuleInfo(
                rule_type="BY_LEVEL_AND_ZONE",
                name="按楼层+区域划分",
                description="根据楼层和区域的组合自动分组创建检验批"
            ),
        ]
        
        return {
            "status": "success",
            "data": RuleListResponse(rules=rules).model_dump()
        }
    except Exception as e:
        logger.error(f"Failed to get rules: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取规则列表失败: {str(e)}"
        )


@router.post(
    "/preview",
    response_model=Dict[str, Any],
    summary="预览规则",
    description="预览规则应用后的效果（预估创建的检验批数量和分组信息）"
)
async def preview_rule(
    request: RulePreviewRequest,
    service: LotStrategyService = Depends(get_lot_strategy_service),
) -> Dict[str, Any]:
    """预览规则"""
    try:
        # 验证 Item 存在
        item_query = "MATCH (item:Item {id: $item_id}) RETURN item.id as id"
        item_result = service.client.execute_query(item_query, {"item_id": request.item_id})
        if not item_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item not found: {request.item_id}"
            )
        
        # 获取未分配的构件
        unassigned_elements_query = """
        MATCH (e:Element)
        WHERE (e.inspection_lot_id IS NULL OR e.inspection_lot_id = "")
        OPTIONAL MATCH (item:Item {id: $item_id})-[:HAS_LOT]->(existing_lot:InspectionLot)-[:MANAGEMENT_CONTAINS]->(e)
        WITH e
        WHERE existing_lot IS NULL
        RETURN e.id as element_id, e.level_id as level_id, e.zone_id as zone_id, e.speckle_type as speckle_type
        """
        
        elements = service.client.execute_query(unassigned_elements_query, {"item_id": request.item_id})
        
        if not elements:
            return {
                "status": "success",
                "data": RulePreviewResponse(
                    rule_type=request.rule_type,
                    estimated_lots=0,
                    groups=[]
                ).model_dump()
            }
        
        # 根据规则类型分组（使用服务的内部方法，注意：这里假设这些方法是公共的或我们可以访问）
        # 由于 _group_elements_by_rule 和 _parse_group_key 是私有方法，我们需要直接调用服务的公共方法
        # 或者使用临时解决方案：创建一个临时服务实例并直接调用私有方法（不推荐，但为了功能完整性暂时这样做）
        rule_type = RuleType(request.rule_type)
        
        # 重构：我们应该让这些方法成为公共方法，或者使用服务的公共API
        # 临时方案：直接使用服务的内部方法（通过Python的访问控制）
        grouped_elements = service._group_elements_by_rule(elements, rule_type)
        
        # 构建预览响应
        groups = []
        for group_key, element_ids in grouped_elements.items():
            lot_info = service._parse_group_key(group_key, rule_type)
            groups.append({
                "key": group_key,
                "count": len(element_ids),
                "label": lot_info.get("name", group_key)
            })
        
        return {
            "status": "success",
            "data": RulePreviewResponse(
                rule_type=request.rule_type,
                estimated_lots=len(groups),
                groups=groups
            ).model_dump()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to preview rule: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"规则预览失败: {str(e)}"
        )

