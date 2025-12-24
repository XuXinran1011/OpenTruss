"""数据摄入 API

接收上游 AI Agent 识别的 Speckle 对象，转换为 OpenTruss 元素格式
"""

from typing import List, Union, Any, Dict
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field, ValidationError

# 导入 Speckle 模型
from app.models.speckle import (
    SpeckleBuiltElement,
    Wall, Beam, Column, Floor, Ceiling, Roof, Brace,
    Duct, Pipe, CableTray, Conduit, Wire,
    Level, Room, Space, Zone, Area,
    Opening, Topography, GridLine, Profile, Network, View,
    Alignment, Baseline, Featureline, Station,
)

# 导入服务
from app.services.ingestion import IngestionService
from app.utils.memgraph import get_memgraph_client, MemgraphClient

router = APIRouter(prefix="/ingest", tags=["ingestion"])


def get_ingestion_service(
    client: MemgraphClient = Depends(get_memgraph_client)
) -> IngestionService:
    """获取 Ingestion Service 实例（依赖注入）
    
    Args:
        client: Memgraph 客户端
        
    Returns:
        IngestionService: Ingestion Service 实例
    """
    return IngestionService(client=client)


class IngestRequest(BaseModel):
    """数据摄入请求
    
    采用"宽进严出"策略：
    - 允许 height, material, inspection_lot_id 为空
    - 无法确定归属的构件会暂存到 Unassigned Item
    """
    project_id: str = Field(..., description="项目 ID")
    elements: List[Dict[str, Any]] = Field(..., description="Speckle 元素列表（支持多种类型）")


class IngestResult(BaseModel):
    """数据摄入结果"""
    ingested_count: int = Field(..., description="成功摄入的构件数量")
    unassigned_count: int = Field(..., description="未分配到检验批的构件数量")
    element_ids: List[str] = Field(..., description="创建的 Element ID 列表")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="错误信息列表")


class IngestResponse(BaseModel):
    """数据摄入响应"""
    status: str = "success"
    data: IngestResult


# Speckle 类型名称到模型类的映射
SPECKLE_TYPE_MAP: Dict[str, type] = {
    "Wall": Wall,
    "Beam": Beam,
    "Column": Column,
    "Floor": Floor,
    "Ceiling": Ceiling,
    "Roof": Roof,
    "Brace": Brace,
    "Duct": Duct,
    "Pipe": Pipe,
    "CableTray": CableTray,
    "Conduit": Conduit,
    "Wire": Wire,
    "Level": Level,
    "Room": Room,
    "Space": Space,
    "Zone": Zone,
    "Area": Area,
    "Opening": Opening,
    "Topography": Topography,
    "GridLine": GridLine,
    "Profile": Profile,
    "Network": Network,
    "View": View,
    "Alignment": Alignment,
    "Baseline": Baseline,
    "Featureline": Featureline,
    "Station": Station,
}


def parse_speckle_element(element_data: Dict[str, Any]) -> SpeckleBuiltElement:
    """解析 Speckle 元素数据为对应的 Pydantic 模型
    
    Args:
        element_data: Speckle 元素数据字典
        
    Returns:
        SpeckleBuiltElement: 解析后的 Pydantic 模型
        
    Raises:
        ValueError: 如果元素类型不支持或数据格式错误
    """
    # 获取元素类型
    speckle_type = element_data.get("speckle_type") or element_data.get("speckleType")
    if not speckle_type:
        raise ValueError("缺少 speckle_type 字段")
    
    # 查找对应的模型类
    model_class = SPECKLE_TYPE_MAP.get(speckle_type)
    if not model_class:
        raise ValueError(f"不支持的 Speckle 类型: {speckle_type}")
    
    # 处理字段别名兼容性
    # Speckle 可能使用 baseLine 或 baseCurve，统一转换为 baseCurve
    element_data_normalized = element_data.copy()
    if "baseLine" in element_data_normalized and "baseCurve" not in element_data_normalized:
        element_data_normalized["baseCurve"] = element_data_normalized.pop("baseLine")
    
    try:
        # 使用 Pydantic 解析（允许通过字段别名）
        return model_class(**element_data_normalized)
    except ValidationError as e:
        raise ValueError(f"元素数据验证失败: {e}")


@router.post(
    "",
    response_model=IngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="数据摄入",
    description="接收上游 AI Agent 的识别结果，采用'宽进严出'策略"
)
async def ingest_elements(
    request: IngestRequest,
    ingestion_service: IngestionService = Depends(get_ingestion_service)
) -> IngestResponse:
    """数据摄入端点
    
    接收 Speckle 格式的元素数据，转换为 OpenTruss 内部格式并存储到 Memgraph。
    
    - **宽进策略**: 允许 height, material, inspection_lot_id 为空
    - **暂存策略**: 无法确定归属的构件挂载到 Unassigned Item
    """
    ingested_count = 0
    unassigned_count = 0
    element_ids = []
    errors = []
    
    for idx, element_data in enumerate(request.elements):
        try:
            # 解析 Speckle 元素
            speckle_element = parse_speckle_element(element_data)
            
            # 转换为 OpenTruss Element 节点并存储到 Memgraph
            element = ingestion_service.ingest_speckle_element(
                speckle_element,
                request.project_id
            )
            
            element_ids.append(element.id)
            ingested_count += 1
            
            # 如果 inspection_lot_id 为空，计入未分配数量
            if not element.inspection_lot_id:
                unassigned_count += 1
                
        except ValueError as e:
            errors.append({
                "index": idx,
                "error": str(e),
                "element_data": element_data
            })
        except Exception as e:
            errors.append({
                "index": idx,
                "error": f"处理失败: {str(e)}",
                "element_data": element_data
            })
    
    result = IngestResult(
        ingested_count=ingested_count,
        unassigned_count=unassigned_count,
        element_ids=element_ids,
        errors=errors
    )
    
    return IngestResponse(status="success", data=result)

