"""桥架容量验证器测试"""

import pytest
from app.core.cable_capacity_validator import CableCapacityValidator
from app.utils.memgraph import MemgraphClient
from app.services.schema import initialize_schema


@pytest.fixture
def client():
    """Memgraph 客户端 fixture"""
    client = MemgraphClient()
    initialize_schema(client)
    return client


@pytest.fixture
def validator(client):
    """容量验证器 fixture"""
    return CableCapacityValidator(client)


@pytest.fixture
def sample_cable_tray(client):
    """创建测试用的桥架元素"""
    tray_id = "test_tray_001"
    
    # 创建桥架（宽度200mm，高度100mm，截面积=20000平方毫米）
    query = """
    CREATE (tray:Element {
        id: $tray_id,
        speckle_type: 'CableTray',
        width: 200.0,
        height: 100.0,
        geometry: {
            type: 'Line',
            coordinates: [[0.0, 0.0, 0.0], [10.0, 0.0, 0.0]]
        }
    })
    RETURN tray.id as id
    """
    client.execute_write(query, {"tray_id": tray_id})
    
    yield tray_id
    
    # 清理
    client.execute_write(
        "MATCH (tray:Element {id: $tray_id}) DETACH DELETE tray",
        {"tray_id": tray_id}
    )


@pytest.fixture
def sample_power_cables(client, sample_cable_tray):
    """创建测试用的电力电缆"""
    from app.models.gb50300.relationships import CONTAINED_IN
    
    cable_ids = []
    
    # 创建3根电力电缆（每根截面积5000平方毫米）
    for i in range(3):
        cable_id = f"test_power_cable_{i+1:03d}"
        cable_ids.append(cable_id)
        
        query = f"""
        MATCH (tray:Element {{id: $tray_id}})
        CREATE (cable:Element {{
            id: $cable_id,
            speckle_type: 'Wire',
            cross_section_area: 5000.0,
            cable_type: '电力电缆',
            geometry: {{
                type: 'Line',
                coordinates: [[0.0, 0.0, 0.0], [10.0, 0.0, 0.0]]
            }}
        }})
        CREATE (cable)-[:CONTAINED_IN]->(tray)
        RETURN cable.id as id
        """
        client.execute_write(
            query,
            {"cable_id": cable_id, "tray_id": sample_cable_tray}
        )
    
    yield cable_ids
    
    # 清理
    for cable_id in cable_ids:
        client.execute_write(
            "MATCH (cable:Element {id: $cable_id}) DETACH DELETE cable",
            {"cable_id": cable_id}
        )


@pytest.fixture
def sample_control_cables(client, sample_cable_tray):
    """创建测试用的控制电缆"""
    from app.models.gb50300.relationships import CONTAINED_IN
    
    cable_ids = []
    
    # 创建3根控制电缆（每根截面积4000平方毫米）
    for i in range(3):
        cable_id = f"test_control_cable_{i+1:03d}"
        cable_ids.append(cable_id)
        
        query = f"""
        MATCH (tray:Element {{id: $tray_id}})
        CREATE (cable:Element {{
            id: $cable_id,
            speckle_type: 'Wire',
            cross_section_area: 4000.0,
            cable_type: '控制电缆',
            geometry: {{
                type: 'Line',
                coordinates: [[0.0, 0.0, 0.0], [10.0, 0.0, 0.0]]
            }}
        }})
        CREATE (cable)-[:CONTAINED_IN]->(tray)
        RETURN cable.id as id
        """
        client.execute_write(
            query,
            {"cable_id": cable_id, "tray_id": sample_cable_tray}
        )
    
    yield cable_ids
    
    # 清理
    for cable_id in cable_ids:
        client.execute_write(
            "MATCH (cable:Element {id: $cable_id}) DETACH DELETE cable",
            {"cable_id": cable_id}
        )


class TestCableCapacityValidator:
    """桥架容量验证器测试类"""
    
    def test_validate_empty_tray(self, validator, sample_cable_tray):
        """测试空桥架的容量验证"""
        result = validator.validate_cable_tray_capacity(sample_cable_tray)
        
        assert result["valid"] is True
        assert len(result["errors"]) == 0
        assert result["power_cable_area"] == 0.0
        assert result["control_cable_area"] == 0.0
        assert result["tray_cross_section"] == 20000.0  # 200 * 100
        assert result["power_cable_ratio"] == 0.0
        assert result["control_cable_ratio"] == 0.0
    
    def test_validate_tray_not_found(self, validator):
        """测试不存在的桥架"""
        result = validator.validate_cable_tray_capacity("nonexistent_tray")
        
        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert "不存在" in result["errors"][0] or "not found" in result["errors"][0].lower()
    
    def test_validate_power_cables_within_limit(self, validator, sample_cable_tray, sample_power_cables):
        """测试电力电缆在限制内（40%以内）"""
        # 3根电缆，每根5000，总共15000平方毫米
        # 桥架截面积20000，占比15000/20000=75%，但单个类型限制是40%
        # 实际应该只计算电力电缆：15000/20000=75% > 40%，应该失败
        
        # 先删除现有的电缆，重新创建符合限制的
        from app.models.gb50300.relationships import CONTAINED_IN
        
        for cable_id in sample_power_cables:
            validator.client.execute_write(
                "MATCH (cable:Element {id: $cable_id}) DETACH DELETE cable",
                {"cable_id": cable_id}
            )
        
        # 创建2根电力电缆（每根4000平方毫米，总共8000，占比40%）
        for i in range(2):
            cable_id = f"test_power_cable_limit_{i+1:03d}"
            query = f"""
            MATCH (tray:Element {{id: $tray_id}})
            CREATE (cable:Element {{
                id: $cable_id,
                speckle_type: 'Wire',
                cross_section_area: 4000.0,
                cable_type: '电力电缆'
            }})
            CREATE (cable)-[:CONTAINED_IN]->(tray)
            """
            validator.client.execute_write(
                query,
                {"cable_id": cable_id, "tray_id": sample_cable_tray}
            )
        
        result = validator.validate_cable_tray_capacity(sample_cable_tray)
        
        assert result["valid"] is True
        assert len(result["errors"]) == 0
        assert result["power_cable_area"] == 8000.0
        assert abs(result["power_cable_ratio"] - 0.40) < 0.01  # 40%
    
    def test_validate_power_cables_exceed_limit(self, validator, sample_cable_tray, sample_power_cables):
        """测试电力电缆超过限制（超过40%）"""
        # 3根电缆，每根5000，总共15000平方毫米
        # 桥架截面积20000，占比15000/20000=75% > 40%，应该失败
        
        result = validator.validate_cable_tray_capacity(sample_cable_tray)
        
        assert result["valid"] is False
        assert len(result["errors"]) > 0
        # 检查错误消息包含关键信息（使用更灵活的匹配方式）
        error_found = any("电力电缆" in err and ("40" in err or "40.0" in err) for err in result["errors"])
        assert error_found, f"Expected error message about power cables and 40%, but got: {result['errors']}"
        assert result["power_cable_area"] == 15000.0
        assert result["power_cable_ratio"] > 0.40
    
    def test_validate_control_cables_within_limit(self, validator, sample_cable_tray):
        """测试控制电缆在限制内（50%以内）"""
        from app.models.gb50300.relationships import CONTAINED_IN
        
        # 创建2根控制电缆（每根5000平方毫米，总共10000，占比50%）
        for i in range(2):
            cable_id = f"test_control_cable_limit_{i+1:03d}"
            query = f"""
            MATCH (tray:Element {{id: $tray_id}})
            CREATE (cable:Element {{
                id: $cable_id,
                speckle_type: 'Wire',
                cross_section_area: 5000.0,
                cable_type: '控制电缆'
            }})
            CREATE (cable)-[:CONTAINED_IN]->(tray)
            """
            validator.client.execute_write(
                query,
                {"cable_id": cable_id, "tray_id": sample_cable_tray}
            )
        
        result = validator.validate_cable_tray_capacity(sample_cable_tray)
        
        assert result["valid"] is True
        assert len(result["errors"]) == 0
        assert result["control_cable_area"] == 10000.0
        assert abs(result["control_cable_ratio"] - 0.50) < 0.01  # 50%
    
    def test_validate_control_cables_exceed_limit(self, validator, sample_cable_tray, sample_control_cables):
        """测试控制电缆超过限制（超过50%）"""
        # 3根电缆，每根4000，总共12000平方毫米
        # 桥架截面积20000，占比12000/20000=60% > 50%，应该失败
        
        result = validator.validate_cable_tray_capacity(sample_cable_tray)
        
        assert result["valid"] is False
        assert len(result["errors"]) > 0
        # 检查错误消息包含关键信息（使用更灵活的匹配方式）
        error_found = any("控制电缆" in err and ("50" in err or "50.0" in err) for err in result["errors"])
        assert error_found, f"Expected error message about control cables and 50%, but got: {result['errors']}"
        assert result["control_cable_area"] == 12000.0
        assert result["control_cable_ratio"] > 0.50
    
    def test_validate_new_cable_addition(self, validator, sample_cable_tray):
        """测试添加新电缆时的容量验证"""
        from app.models.gb50300.relationships import CONTAINED_IN
        
        # 创建1根电力电缆（4000平方毫米，占比20%）
        cable_id_1 = "test_new_cable_001"
        query = f"""
        MATCH (tray:Element {{id: $tray_id}})
        CREATE (cable:Element {{
            id: $cable_id,
            speckle_type: 'Wire',
            cross_section_area: 4000.0,
            cable_type: '电力电缆'
        }})
        CREATE (cable)-[:CONTAINED_IN]->(tray)
        """
        validator.client.execute_write(
            query,
            {"cable_id": cable_id_1, "tray_id": sample_cable_tray}
        )
        
        # 验证添加新电缆（5000平方毫米）后的容量
        new_cable_id = "test_new_cable_002"
        result = validator.validate_cable_tray_capacity(
            sample_cable_tray,
            new_cable_id=new_cable_id
        )
        
        # 由于新电缆还没有cable_type，应该不会影响验证
        # 但我们需要先创建新电缆节点
        query2 = f"""
        CREATE (cable:Element {{
            id: $cable_id,
            speckle_type: 'Wire',
            cross_section_area: 5000.0,
            cable_type: '电力电缆'
        }})
        """
        validator.client.execute_write(query2, {"cable_id": new_cable_id})
        
        result = validator.validate_cable_tray_capacity(
            sample_cable_tray,
            new_cable_id=new_cable_id
        )
        
        # 总共9000平方毫米（4000+5000），占比45% > 40%，应该失败
        assert result["valid"] is False
        assert result["power_cable_area"] == 9000.0
        assert result["power_cable_ratio"] > 0.40
        
        # 清理
        validator.client.execute_write(
            "MATCH (cable:Element {id: $cable_id}) DETACH DELETE cable",
            {"cable_id": cable_id_1}
        )
        validator.client.execute_write(
            "MATCH (cable:Element {id: $cable_id}) DETACH DELETE cable",
            {"cable_id": new_cable_id}
        )
    
    def test_validate_warning_threshold(self, validator, sample_cable_tray):
        """测试接近限制时的警告（90%阈值）"""
        from app.models.gb50300.relationships import CONTAINED_IN
        
        # 创建电力电缆，占比约36%（接近40%限制的90%）
        cable_id = "test_warning_cable"
        query = f"""
        MATCH (tray:Element {{id: $tray_id}})
        CREATE (cable:Element {{
            id: $cable_id,
            speckle_type: 'Wire',
            cross_section_area: 7200.0,
            cable_type: '电力电缆'
        }})
        CREATE (cable)-[:CONTAINED_IN]->(tray)
        """
        validator.client.execute_write(
            query,
            {"cable_id": cable_id, "tray_id": sample_cable_tray}
        )
        
        result = validator.validate_cable_tray_capacity(sample_cable_tray)
        
        assert result["valid"] is True
        assert len(result["warnings"]) > 0
        assert any("接近限制" in warn or "接近" in warn for warn in result["warnings"])
        
        # 清理
        validator.client.execute_write(
            "MATCH (cable:Element {id: $cable_id}) DETACH DELETE cable",
            {"cable_id": cable_id}
        )
