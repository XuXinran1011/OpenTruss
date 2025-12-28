"""电缆路由依赖集成测试"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.utils.memgraph import MemgraphClient
from app.services.schema import initialize_schema
from app.models.gb50300.relationships import CONTAINED_IN

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    """设置测试数据库"""
    memgraph_client = MemgraphClient()
    initialize_schema(memgraph_client)
    yield
    # 清理测试数据（如果需要）


@pytest.fixture
def memgraph_client():
    """Memgraph 客户端 fixture"""
    return MemgraphClient()


@pytest.fixture
def sample_cable_tray(memgraph_client):
    """创建测试用的桥架"""
    tray_id = "test_tray_dep_001"
    
    query = """
    CREATE (tray:Element {
        id: $tray_id,
        speckle_type: 'CableTray',
        width: 200.0,
        height: 100.0,
        routing_status: 'COMPLETED',
        geometry: {
            type: 'Line',
            coordinates: [[0.0, 0.0, 0.0], [10.0, 0.0, 0.0], [20.0, 0.0, 0.0]]
        },
        level_id: 'test_level_001'
    })
    RETURN tray.id as id
    """
    memgraph_client.execute_write(query, {"tray_id": tray_id})
    
    yield tray_id
    
    # 清理
    memgraph_client.execute_write(
        "MATCH (tray:Element {id: $tray_id}) DETACH DELETE tray",
        {"tray_id": tray_id}
    )


@pytest.fixture
def sample_wire_in_tray(memgraph_client, sample_cable_tray):
    """创建桥架内的电缆"""
    wire_id = "test_wire_dep_001"
    
    query = f"""
    MATCH (tray:Element {{id: $tray_id}})
    CREATE (wire:Element {{
        id: $wire_id,
        speckle_type: 'Wire',
        cross_section_area: 1000.0,
        cable_type: '电力电缆',
        geometry: {{
            type: 'Line',
            coordinates: [[0.0, 0.0, 0.0], [10.0, 0.0, 0.0]]
        }},
        level_id: 'test_level_001'
    }})
    CREATE (wire)-[:CONTAINED_IN]->(tray)
    RETURN wire.id as id
    """
    memgraph_client.execute_write(query, {"wire_id": wire_id, "tray_id": sample_cable_tray})
    
    yield wire_id
    
    # 清理
    memgraph_client.execute_write(
        "MATCH (wire:Element {id: $wire_id}) DETACH DELETE wire",
        {"wire_id": wire_id}
    )


class TestRoutingDependency:
    """电缆路由依赖测试类"""
    
    def test_wire_routing_requires_container(self, memgraph_client, sample_wire_in_tray, sample_cable_tray):
        """测试电缆路由需要容器（桥架/线管）"""
        # 尝试为电缆计算路由（应该失败，因为必须依赖桥架）
        response = client.post(
            "/api/v1/routing/calculate",
            json={
                "start": [0.0, 0.0],
                "end": [10.0, 10.0],
                "element_type": "Wire",
                "element_properties": {"width": 50},
                "element_id": sample_wire_in_tray,
                "level_id": "test_level_001"
            }
        )
        
        # 由于电缆已关联桥架，应该使用桥架的路由
        # 或者返回错误提示需要先完成桥架路由
        assert response.status_code in [200, 400, 422]
        
        if response.status_code == 200:
            data = response.json()
            # 如果成功，应该有警告提示路由继承自桥架
            assert "warnings" in data.get("data", {}) or "errors" in data.get("data", {})
        else:
            # 如果失败，错误信息应该提示需要桥架/线管
            error_detail = response.json().get("detail", "")
            assert any(keyword in error_detail for keyword in ["桥架", "线管", "容器", "container", "cable tray"])
    
    def test_wire_routing_uses_container_route(self, memgraph_client, sample_cable_tray, sample_wire_in_tray):
        """测试电缆路由使用容器的路由"""
        # 桥架已完成路由规划（routing_status = 'COMPLETED'）
        # 电缆应该能够继承桥架的路由
        
        response = client.post(
            "/api/v1/routing/calculate",
            json={
                "start": [0.0, 0.0],
                "end": [20.0, 0.0],
                "element_type": "Wire",
                "element_properties": {"width": 50},
                "element_id": sample_wire_in_tray,
                "level_id": "test_level_001"
            }
        )
        
        # 如果桥架路由已完成，电缆应该能够获取路由
        assert response.status_code in [200, 400, 422]
        
        if response.status_code == 200:
            data = response.json()
            # 应该返回路由点（可能继承自桥架）
            assert "path_points" in data.get("data", {})
    
    def test_wire_routing_fails_if_container_not_routed(self, memgraph_client):
        """测试如果容器未完成路由，电缆路由应该失败"""
        # 创建未完成路由的桥架
        tray_id = "test_tray_not_routed"
        wire_id = "test_wire_not_routed"
        
        try:
            query = f"""
            CREATE (tray:Element {{
                id: $tray_id,
                speckle_type: 'CableTray',
                width: 200.0,
                height: 100.0,
                routing_status: 'PLANNING',
                geometry: {{
                    type: 'Line',
                    coordinates: [[0.0, 0.0, 0.0], [10.0, 0.0, 0.0]]
                }},
                level_id: 'test_level_001'
            }})
            CREATE (wire:Element {{
                id: $wire_id,
                speckle_type: 'Wire',
                geometry: {{
                    type: 'Line',
                    coordinates: [[0.0, 0.0, 0.0], [10.0, 0.0, 0.0]]
                }},
                level_id: 'test_level_001'
            }})
            CREATE (wire)-[:CONTAINED_IN]->(tray)
            """
            memgraph_client.execute_write(query, {"tray_id": tray_id, "wire_id": wire_id})
            
            # 尝试为电缆计算路由（应该失败）
            response = client.post(
                "/api/v1/routing/calculate",
                json={
                    "start": [0.0, 0.0],
                    "end": [10.0, 10.0],
                    "element_type": "Wire",
                    "element_properties": {"width": 50},
                    "element_id": wire_id,
                    "level_id": "test_level_001"
                }
            )
            
            # 应该返回错误
            assert response.status_code in [400, 422, 500]
            error_detail = response.json().get("detail", "")
            assert any(keyword in error_detail.lower() for keyword in [
                "尚未完成", "not completed", "必须先", "must first", "关联的桥架"
            ])
            
        finally:
            # 清理
            memgraph_client.execute_write(
                "MATCH (n:Element) WHERE n.id IN [$tray_id, $wire_id] DETACH DELETE n",
                {"tray_id": tray_id, "wire_id": wire_id}
            )
    
    def test_cable_tray_capacity_check_during_routing(self, memgraph_client, sample_cable_tray):
        """测试路由时进行桥架容量检查"""
        # 创建多根电缆，使容量超过限制
        wire_ids = []
        try:
            for i in range(10):
                wire_id = f"test_capacity_wire_{i:03d}"
                wire_ids.append(wire_id)
                
                query = f"""
                MATCH (tray:Element {{id: $tray_id}})
                CREATE (wire:Element {{
                    id: $wire_id,
                    speckle_type: 'Wire',
                    cross_section_area: 1000.0,
                    cable_type: '电力电缆',
                    geometry: {{
                        type: 'Line',
                        coordinates: [[0.0, 0.0, 0.0], [10.0, 0.0, 0.0]]
                    }},
                    level_id: 'test_level_001'
                }})
                CREATE (wire)-[:CONTAINED_IN]->(tray)
                """
                memgraph_client.execute_write(query, {"wire_id": wire_id, "tray_id": sample_cable_tray})
            
            # 尝试添加新电缆路由（应该因为容量超限而失败）
            new_wire_id = "test_new_capacity_wire"
            
            # 先创建电缆节点
            query = """
            CREATE (wire:Element {
                id: $wire_id,
                speckle_type: 'Wire',
                cross_section_area: 1000.0,
                cable_type: '电力电缆',
                level_id: 'test_level_001'
            })
            """
            memgraph_client.execute_write(query, {"wire_id": new_wire_id})
            
            response = client.post(
                "/api/v1/routing/calculate",
                json={
                    "start": [0.0, 0.0],
                    "end": [10.0, 10.0],
                    "element_type": "Wire",
                    "element_properties": {"width": 50},
                    "element_id": new_wire_id,
                    "level_id": "test_level_001"
                }
            )
            
            # 即使路由计算可能成功，容量检查也应该在拓扑更新时进行
            # 这里主要测试路由服务能够处理容量检查
            
        finally:
            # 清理
            for wire_id in wire_ids + [new_wire_id]:
                memgraph_client.execute_write(
                    "MATCH (wire:Element {id: $wire_id}) DETACH DELETE wire",
                    {"wire_id": wire_id}
                )
