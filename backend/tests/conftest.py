"""Pytest 配置文件

包含测试共享的 fixtures 和配置
"""

import pytest
from typing import Generator, Optional
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "backend"))


@pytest.fixture(scope="session")
def memgraph_client():
    """Memgraph 客户端 fixture
    
    注意: 这需要 Memgraph 正在运行
    """
    from app.utils.memgraph import MemgraphClient
    
    try:
        client = MemgraphClient()
        # 测试连接
        client.execute_query("RETURN 1 as test")
        yield client
    except Exception as e:
        pytest.skip(f"Memgraph 连接失败，跳过测试: {e}")


@pytest.fixture
def sample_wall_element():
    """示例 Wall 元素数据"""
    from app.models.speckle import Wall
    from app.models.speckle.base import Geometry
    
    return Wall(
        speckle_type="Wall",
        geometry=Geometry(
            type="Polyline",
            coordinates=[[0, 0, 0], [10, 0, 0], [10, 5, 0], [0, 5, 0], [0, 0, 0]],
            closed=True
        ),
        level_id="level_f1",
    )


@pytest.fixture
def sample_project_id():
    """示例项目 ID"""
    return "test_project_001"


@pytest.fixture
def ingestion_service(memgraph_client):
    """Ingestion Service fixture"""
    from app.services.ingestion import IngestionService
    return IngestionService(client=memgraph_client)
