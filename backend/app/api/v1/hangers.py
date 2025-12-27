"""支吊架 API

提供支吊架自动生成和查询接口
"""

import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends

from app.services.hanger import HangerPlacementService
from app.core.exceptions import NotFoundError, ValidationError
from app.models.api.hangers import (
    GenerateHangersRequest,
    GenerateIntegratedHangersRequest,
    GenerateHangersResponse,
    GenerateIntegratedHangersResponse,
    ElementHangersResponse,
    HangerInfo,
    IntegratedHangerInfo,
)
from app.utils.memgraph import get_memgraph_client, MemgraphClient
from app.models.gb50300.relationships import SUPPORTS, USES_INTEGRATED_HANGER

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hangers", tags=["hangers"])


def get_hanger_service(
    client: MemgraphClient = Depends(get_memgraph_client)
) -> HangerPlacementService:
    """获取支吊架服务实例（依赖注入）"""
    return HangerPlacementService(client=client)


@router.post(
    "/generate",
    response_model=dict,
    summary="生成支吊架",
    description="根据标准图集自动计算并生成支吊架位置"
)
async def generate_hangers(
    request: GenerateHangersRequest,
    service: HangerPlacementService = Depends(get_hanger_service)
) -> Dict[str, Any]:
    """生成支吊架"""
    try:
        all_hangers = []
        
        for element_id in request.element_ids:
            hangers = service.generate_hangers(
                element_id=element_id,
                seismic_grade=request.seismic_grade,
                create_nodes=request.create_nodes
            )
            all_hangers.append({
                "element_id": element_id,
                "hanger_count": len(hangers),
                "hangers": [
                    HangerInfo(
                        id=h["id"],
                        position=h["position"],
                        hanger_type=h["hanger_type"],
                        standard_code=h["standard_code"],
                        detail_code=h["detail_code"],
                        support_interval=h.get("support_interval")
                    )
                    for h in hangers
                ]
            })
        
        return {
            "status": "success",
            "data": {
                "total_elements": len(request.element_ids),
                "results": all_hangers
            }
        }
    except (NotFoundError, ValidationError) as e:
        status_code = status.HTTP_404_NOT_FOUND if isinstance(e, NotFoundError) else status.HTTP_400_BAD_REQUEST
        logger.error(f"Error in generate hangers: {e.message}", exc_info=True)
        raise HTTPException(
            status_code=status_code,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error in generate hangers: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="生成支吊架时发生意外错误，请稍后重试或联系技术支持"
        )


@router.post(
    "/integrated/generate",
    response_model=dict,
    summary="生成综合支吊架",
    description="为空间内的成排管线生成共用综合支吊架"
)
async def generate_integrated_hangers(
    request: GenerateIntegratedHangersRequest,
    service: HangerPlacementService = Depends(get_hanger_service)
) -> Dict[str, Any]:
    """生成综合支吊架"""
    try:
        hangers = service.generate_integrated_hangers(
            space_id=request.space_id,
            element_ids=request.element_ids,
            seismic_grade=request.seismic_grade,
            create_nodes=request.create_nodes
        )
        
        return {
            "status": "success",
            "data": GenerateIntegratedHangersResponse(
                space_id=request.space_id,
                hanger_count=len(hangers),
                hangers=[
                    IntegratedHangerInfo(
                        id=h["id"],
                        position=h["position"],
                        hanger_type=h["hanger_type"],
                        standard_code=h["standard_code"],
                        detail_code=h["detail_code"],
                        supported_element_ids=h["supported_element_ids"],
                        space_id=h["space_id"]
                    )
                    for h in hangers
                ]
            ).model_dump()
        }
    except (NotFoundError, ValidationError) as e:
        status_code = status.HTTP_404_NOT_FOUND if isinstance(e, NotFoundError) else status.HTTP_400_BAD_REQUEST
        logger.error(f"Error in generate integrated hangers: {e.message}", exc_info=True)
        raise HTTPException(
            status_code=status_code,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error in generate integrated hangers: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="生成综合支吊架时发生意外错误，请稍后重试或联系技术支持"
        )


@router.get(
    "/{element_id}",
    response_model=dict,
    summary="查询元素的支吊架",
    description="查询指定元素的所有支吊架"
)
async def get_element_hangers(
    element_id: str,
    service: HangerPlacementService = Depends(get_hanger_service),
    client: MemgraphClient = Depends(get_memgraph_client)
) -> Dict[str, Any]:
    """查询元素的支吊架"""
    try:
        # 查询单独支吊架
        hanger_query = f"""
        MATCH (hanger:Element)-[:{SUPPORTS}]->(e:Element {{id: $element_id}})
        WHERE hanger.speckle_type = 'Hanger'
        RETURN hanger.id as id,
               hanger.geometry as geometry,
               hanger.hanger_type as hanger_type,
               hanger.standard_code as standard_code,
               hanger.detail_code as detail_code,
               hanger.support_interval as support_interval
        """
        hanger_results = client.execute_query(hanger_query, {"element_id": element_id})
        
        hangers = []
        for row in hanger_results:
            geometry_dict = row.get("geometry", {})
            position = geometry_dict.get("coordinates", [[0, 0, 0]])[0] if geometry_dict.get("coordinates") else [0, 0, 0]
            
            hangers.append(HangerInfo(
                id=row.get("id"),
                position=position,
                hanger_type=row.get("hanger_type", "吊架"),
                standard_code=row.get("standard_code", ""),
                detail_code=row.get("detail_code", ""),
                support_interval=row.get("support_interval")
            ))
        
        # 查询综合支吊架
        integrated_query = f"""
        MATCH (e:Element {{id: $element_id}})-[:USES_INTEGRATED_HANGER]->(hanger:Element)
        WHERE hanger.speckle_type = 'IntegratedHanger'
        RETURN hanger.id as id,
               hanger.geometry as geometry,
               hanger.hanger_type as hanger_type,
               hanger.standard_code as standard_code,
               hanger.detail_code as detail_code,
               hanger.supported_element_ids as supported_element_ids,
               hanger.space_id as space_id
        LIMIT 1
        """
        integrated_results = client.execute_query(integrated_query, {"element_id": element_id})
        
        integrated_hanger = None
        if integrated_results:
            row = integrated_results[0]
            geometry_dict = row.get("geometry", {})
            position = geometry_dict.get("coordinates", [[0, 0, 0]])[0] if geometry_dict.get("coordinates") else [0, 0, 0]
            
            integrated_hanger = IntegratedHangerInfo(
                id=row.get("id"),
                position=position,
                hanger_type=row.get("hanger_type", "吊架"),
                standard_code=row.get("standard_code", ""),
                detail_code=row.get("detail_code", ""),
                supported_element_ids=row.get("supported_element_ids", []),
                space_id=row.get("space_id", "")
            )
        
        return {
            "status": "success",
            "data": ElementHangersResponse(
                element_id=element_id,
                hangers=hangers,
                integrated_hanger=integrated_hanger
            ).model_dump()
        }
    except Exception as e:
        logger.error(f"Unexpected error in get element hangers: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="查询支吊架时发生意外错误，请稍后重试或联系技术支持"
        )
