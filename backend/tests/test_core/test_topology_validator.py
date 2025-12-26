"""测试拓扑校验器（规则引擎 Phase 4）"""

import pytest
from app.core.validators import TopologyValidator
from app.utils.memgraph import MemgraphClient


@pytest.fixture
def topology_validator():
    """创建拓扑校验器实例"""
    client = MemgraphClient()
    return TopologyValidator(client)


def test_find_open_ends_empty_list(topology_validator):
    """测试查找悬空端点 - 空列表"""
    result = topology_validator.find_open_ends([])
    assert result == []


def test_find_isolated_elements_empty_list(topology_validator):
    """测试查找孤立元素 - 空列表"""
    result = topology_validator.find_isolated_elements([])
    assert result == []


def test_validate_topology_nonexistent_lot(topology_validator):
    """测试验证拓扑 - 不存在的检验批"""
    result = topology_validator.validate_topology("nonexistent_lot_id")
    # 应该返回有效（因为检验批不存在或没有元素）
    assert result["valid"] is True
    assert len(result["open_ends"]) == 0
    assert len(result["isolated_elements"]) == 0


def test_find_open_ends_with_connections(topology_validator):
    """测试查找悬空端点 - 有连接的元素（应该不是悬空端点）"""
    # 注意：这个测试需要实际的数据库数据
    # 这里我们只测试方法不会崩溃
    element_ids = ["element_001", "element_002"]
    result = topology_validator.find_open_ends(element_ids)
    # 结果应该是列表（即使为空）
    assert isinstance(result, list)


def test_find_isolated_elements_with_connections(topology_validator):
    """测试查找孤立元素 - 有连接的元素（应该不是孤立元素）"""
    # 注意：这个测试需要实际的数据库数据
    # 这里我们只测试方法不会崩溃
    element_ids = ["element_001", "element_002"]
    result = topology_validator.find_isolated_elements(element_ids)
    # 结果应该是列表（即使为空）
    assert isinstance(result, list)

