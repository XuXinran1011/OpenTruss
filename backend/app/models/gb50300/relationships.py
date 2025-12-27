"""关系类型定义

定义 OpenTruss 图数据库中的关系类型
"""

from enum import Enum
from typing import Literal


class RelationshipType(str, Enum):
    """关系类型枚举"""
    
    # 物理从属关系（Project -> Building -> Level/Zone -> Element）
    PHYSICALLY_CONTAINS = "PHYSICALLY_CONTAINS"
    
    # 管理从属关系（Project -> Building -> Division -> SubDivision -> Item -> InspectionLot -> Element）
    MANAGEMENT_CONTAINS = "MANAGEMENT_CONTAINS"
    
    # MEP 专业系统从属关系（Building -> System -> SubSystem -> Element）
    SYSTEM_CONTAINS = "SYSTEM_CONTAINS"
    
    # 位置关系（Element -> Level/Zone）
    LOCATED_AT = "LOCATED_AT"
    
    # 拓扑连接关系（Element -> Element）
    CONNECTED_TO = "CONNECTED_TO"
    
    # 检验批关系（Item -> InspectionLot）
    HAS_LOT = "HAS_LOT"
    
    # 审批历史关系（InspectionLot -> ApprovalHistory）
    HAS_APPROVAL_HISTORY = "HAS_APPROVAL_HISTORY"
    
    # 支吊架关系（Element -> Element）
    SUPPORTS = "SUPPORTS"  # 支吊架支撑MEP元素（Hanger -> Element）
    HAS_HANGER = "HAS_HANGER"  # MEP元素有支吊架（Element -> Hanger，反向关系）
    
    # 容器关系（Element -> Element）
    CONTAINED_IN = "CONTAINED_IN"  # 电缆/电线包含在桥架/线管中（Wire/Cable -> CableTray/Conduit）
    
    # 综合支吊架关系（Element -> Element）
    USES_INTEGRATED_HANGER = "USES_INTEGRATED_HANGER"  # 元素使用综合支吊架（Element -> IntegratedHanger）


# 关系类型常量（方便使用）
PHYSICALLY_CONTAINS = RelationshipType.PHYSICALLY_CONTAINS
MANAGEMENT_CONTAINS = RelationshipType.MANAGEMENT_CONTAINS
SYSTEM_CONTAINS = RelationshipType.SYSTEM_CONTAINS
LOCATED_AT = RelationshipType.LOCATED_AT
CONNECTED_TO = RelationshipType.CONNECTED_TO
HAS_LOT = RelationshipType.HAS_LOT
HAS_APPROVAL_HISTORY = RelationshipType.HAS_APPROVAL_HISTORY
SUPPORTS = RelationshipType.SUPPORTS
HAS_HANGER = RelationshipType.HAS_HANGER
CONTAINED_IN = RelationshipType.CONTAINED_IN
USES_INTEGRATED_HANGER = RelationshipType.USES_INTEGRATED_HANGER

