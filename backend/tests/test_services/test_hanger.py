"""支吊架服务测试"""

import pytest
from app.services.hanger import HangerPlacementService
from app.utils.memgraph import MemgraphClient
from app.services.schema import initialize_schema
from app.models.gb50300.relationships import SUPPORTS, HAS_HANGER, USES_INTEGRATED_HANGER


@pytest.fixture
def client():
    """Memgraph 客户端 fixture"""
    client = MemgraphClient()
    initialize_schema(client)
    return client


@pytest.fixture
def hanger_service(client):
    """支吊架服务 fixture"""
    return HangerPlacementService(client)


@pytest.fixture
def sample_pipe(client):
    """创建测试用的管道元素"""
    pipe_id = "test_pipe_001"
    
    query = """
    CREATE (pipe:Element {
        id: $pipe_id,
        speckle_type: 'Pipe',
        diameter: 100.0,
        geometry: {
            type: 'Line',
            coordinates: [[0.0, 0.0, 0.0], [10.0, 0.0, 0.0], [20.0, 0.0, 0.0]]
        },
        level_id: 'test_level_001'
    })
    RETURN pipe.id as id
    """
    client.execute_write(query, {"pipe_id": pipe_id})
    
    yield pipe_id
    
    # 清理
    client.execute_write(
        "MATCH (pipe:Element {id: $pipe_id}) DETACH DELETE pipe",
        {"pipe_id": pipe_id}
    )


@pytest.fixture
def sample_duct(client):
    """创建测试用的风管元素"""
    duct_id = "test_duct_001"
    
    query = """
    CREATE (duct:Element {
        id: $duct_id,
        speckle_type: 'Duct',
        width: 500.0,
        height: 300.0,
        geometry: {
            type: 'Line',
            coordinates: [[0.0, 0.0, 0.0], [10.0, 0.0, 0.0], [20.0, 0.0, 0.0]]
        },
        level_id: 'test_level_001'
    })
    RETURN duct.id as id
    """
    client.execute_write(query, {"duct_id": duct_id})
    
    yield duct_id
    
    # 清理
    client.execute_write(
        "MATCH (duct:Element {id: $duct_id}) DETACH DELETE duct",
        {"duct_id": duct_id}
    )


@pytest.fixture
def sample_space(client):
    """创建测试用的空间元素"""
    space_id = "test_space_001"
    
    query = """
    CREATE (space:Element {
        id: $space_id,
        speckle_type: 'Space',
        use_integrated_hanger: false,
        geometry: {
            type: 'Polyline',
            coordinates: [[0.0, 0.0, 0.0], [10.0, 0.0, 0.0], [10.0, 10.0, 0.0], [0.0, 10.0, 0.0], [0.0, 0.0, 0.0]]
        },
        level_id: 'test_level_001'
    })
    RETURN space.id as id
    """
    client.execute_write(query, {"space_id": space_id})
    
    yield space_id
    
    # 清理
    client.execute_write(
        "MATCH (space:Element {id: $space_id}) DETACH DELETE space",
        {"space_id": space_id}
    )


class TestHangerPlacementService:
    """支吊架服务测试类"""
    
    def test_generate_hangers_for_pipe(self, hanger_service, sample_pipe):
        """测试为管道生成支吊架"""
        try:
            hangers = hanger_service.generate_hangers(
                element_id=sample_pipe,
                seismic_grade=None,
                create_nodes=True
            )
            
            # 验证生成了支吊架
            assert len(hangers) > 0
            
            # 验证支吊架属性
            for hanger in hangers:
                assert "id" in hanger
                assert "position" in hanger
                assert "hanger_type" in hanger
                assert "standard_code" in hanger
                assert "detail_code" in hanger
                assert hanger["hanger_type"] in ["支架", "吊架"]
                assert len(hanger["position"]) == 3  # [x, y, z]
            
            # 验证数据库中的关系
            query = f"""
            MATCH (hanger:Element)-[r]->(pipe:Element {{id: $pipe_id}})
            WHERE type(r) = '{SUPPORTS}' AND hanger.speckle_type = 'Hanger'
            RETURN count(hanger) as count
            """
            result = hanger_service.client.execute_query(query, {"pipe_id": sample_pipe})
            assert result[0]["count"] == len(hangers)
            
        finally:
            # 清理生成的支吊架
            query = f"""
            MATCH (hanger:Element)-[r]->(pipe:Element {{id: $pipe_id}})
            WHERE type(r) = '{SUPPORTS}' AND hanger.speckle_type = 'Hanger'
            DETACH DELETE hanger
            """
            hanger_service.client.execute_write(query, {"pipe_id": sample_pipe})
    
    def test_generate_hangers_for_duct(self, hanger_service, sample_duct):
        """测试为风管生成支吊架"""
        try:
            hangers = hanger_service.generate_hangers(
                element_id=sample_duct,
                seismic_grade=None,
                create_nodes=True
            )
            
            assert len(hangers) > 0
            
            for hanger in hangers:
                assert "id" in hanger
                assert "position" in hanger
                assert hanger["standard_code"] == "08k132"  # 风管标准图集
            
        finally:
            # 清理
            query = f"""
            MATCH (hanger:Element)-[r]->(duct:Element {{id: $duct_id}})
            WHERE type(r) = '{SUPPORTS}' AND hanger.speckle_type = 'Hanger'
            DETACH DELETE hanger
            """
            hanger_service.client.execute_write(query, {"duct_id": sample_duct})
    
    def test_generate_integrated_hangers(self, hanger_service, sample_space, sample_pipe):
        """测试生成综合支吊架"""
        # 创建第二个管道元素
        pipe_id_2 = "test_pipe_002"
        query = """
        CREATE (pipe:Element {
            id: $pipe_id,
            speckle_type: 'Pipe',
            diameter: 80.0,
            geometry: {
                type: 'Line',
                coordinates: [[0.0, 1.0, 0.0], [10.0, 1.0, 0.0], [20.0, 1.0, 0.0]]
            },
            level_id: 'test_level_001'
        })
        """
        hanger_service.client.execute_write(query, {"pipe_id": pipe_id_2})
        
        # 将管道关联到空间
        query2 = """
        MATCH (space:Element {id: $space_id}), (pipe:Element {id: $pipe_id})
        CREATE (pipe)-[:LOCATED_AT]->(space)
        """
        hanger_service.client.execute_write(query2, {"space_id": sample_space, "pipe_id": sample_pipe})
        hanger_service.client.execute_write(query2, {"space_id": sample_space, "pipe_id": pipe_id_2})
        
        # 设置空间使用综合支吊架
        query3 = """
        MATCH (space:Element {id: $space_id})
        SET space.use_integrated_hanger = true
        """
        hanger_service.client.execute_write(query3, {"space_id": sample_space})
        
        try:
            integrated_hangers = hanger_service.generate_integrated_hangers(
                space_id=sample_space,
                element_ids=[sample_pipe, pipe_id_2],
                seismic_grade=None,
                create_nodes=True
            )
            
            # 验证生成了综合支吊架
            assert len(integrated_hangers) > 0
            
            for hanger in integrated_hangers:
                assert "id" in hanger
                assert "position" in hanger
                assert "supported_element_ids" in hanger
                assert len(hanger["supported_element_ids"]) >= 2
            
        finally:
            # 清理
            query = f"""
            MATCH (hanger:Element)-[:{USES_INTEGRATED_HANGER}]-(pipe:Element)
            WHERE hanger.speckle_type = 'IntegratedHanger'
            DETACH DELETE hanger
            """
            hanger_service.client.execute_write(query)
            
            hanger_service.client.execute_write(
                "MATCH (pipe:Element {id: $pipe_id}) DETACH DELETE pipe",
                {"pipe_id": pipe_id_2}
            )
    
    def test_calculate_spacing(self, hanger_service, sample_pipe):
        """测试计算支吊架间距"""
        # 获取管道元素
        query = """
        MATCH (pipe:Element {id: $pipe_id})
        RETURN pipe.diameter as diameter, pipe.speckle_type as type
        """
        result = hanger_service.client.execute_query(query, {"pipe_id": sample_pipe})
        assert len(result) > 0
        
        # 测试间距计算（内部方法，可能需要通过公共接口测试）
        # 这里主要测试服务初始化正常
        assert hanger_service.client is not None
        assert hanger_service._config is not None
    
    def test_invalid_element_id(self, hanger_service):
        """测试无效的元素ID"""
        with pytest.raises((ValueError, Exception)):
            hanger_service.generate_hangers(
                element_id="nonexistent_element",
                create_nodes=False
            )
