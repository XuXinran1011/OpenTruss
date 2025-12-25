"""
测试数据生成器

用于生成性能测试所需的测试数据（项目、构件、检验批等）
"""

import uuid
import random
import logging
from typing import List, Dict, Any
from datetime import datetime

from app.utils.memgraph import MemgraphClient
from app.services.schema import initialize_schema
from app.services.ingestion import IngestionService
from app.models.speckle.architectural import Wall, Floor, Column
from app.models.speckle.base import Geometry2D, Point2D

logger = logging.getLogger(__name__)


class TestDataGenerator:
    """测试数据生成器"""
    
    def __init__(self, client: MemgraphClient = None):
        self.client = client or MemgraphClient()
        self.ingestion_service = IngestionService(client=self.client)
    
    def generate_project(self, project_id: str = None, name: str = None) -> Dict[str, Any]:
        """生成测试项目"""
        return {
            "id": project_id or f"test_project_{uuid.uuid4().hex[:8]}",
            "name": name or f"测试项目 {datetime.now().strftime('%Y%m%d_%H%M%S')}",
        }
    
    def generate_element(self, speckle_type: str = "Wall", level_id: str = None) -> Dict[str, Any]:
        """生成测试构件数据"""
        element_id = f"test_element_{uuid.uuid4().hex[:8]}"
        
        # 生成随机2D几何
        base_x = random.uniform(0, 100)
        base_y = random.uniform(0, 100)
        width = random.uniform(5, 20)
        height = random.uniform(5, 20)
        
        coordinates = [
            [base_x, base_y],
            [base_x + width, base_y],
            [base_x + width, base_y + height],
            [base_x, base_y + height],
        ]
        
        element_data = {
            "speckle_id": f"speckle_{element_id}",
            "speckle_type": speckle_type,
            "geometry_2d": {
                "type": "Polyline",
                "coordinates": coordinates,
                "closed": True,
            },
            "height": random.uniform(2.5, 4.0),
            "level_id": level_id or f"level_{random.randint(1, 10)}",
        }
        
        return element_data
    
    def generate_batch_elements(self, count: int, speckle_type: str = "Wall", level_id: str = None) -> List[Dict[str, Any]]:
        """批量生成测试构件"""
        return [self.generate_element(speckle_type, level_id) for _ in range(count)]
    
    def create_test_project_with_elements(
        self,
        project_id: str = None,
        element_count: int = 100,
        levels: int = 5
    ) -> Dict[str, Any]:
        """创建测试项目并批量生成构件"""
        project = self.generate_project(project_id)
        
        # 确保Schema已初始化
        initialize_schema(self.client, create_default_users=False)
        
        # 生成不同楼层的构件
        elements = []
        elements_per_level = element_count // levels
        
        for level_idx in range(levels):
            level_id = f"level_{level_idx + 1}"
            level_elements = self.generate_batch_elements(
                elements_per_level,
                speckle_type=random.choice(["Wall", "Floor", "Column"]),
                level_id=level_id
            )
            elements.extend(level_elements)
        
        # 创建项目节点（简化版，实际需要完整的层级结构）
        # 这里只返回数据，实际的创建需要调用相应的服务
        
        return {
            "project": project,
            "elements": elements,
            "total_count": len(elements),
        }
    
    def generate_large_dataset(
        self,
        project_id: str,
        total_elements: int = 10000,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """生成大数据集（用于压力测试）"""
        logger.info(f"开始生成大数据集: {total_elements} 个构件...")
        
        elements = []
        batches = (total_elements + batch_size - 1) // batch_size
        
        for batch_idx in range(batches):
            batch_start = batch_idx * batch_size
            batch_end = min(batch_start + batch_size, total_elements)
            batch_count = batch_end - batch_start
            
            batch_elements = self.generate_batch_elements(
                batch_count,
                speckle_type=random.choice(["Wall", "Floor", "Column", "Ceiling"]),
            )
            elements.extend(batch_elements)
            
            if (batch_idx + 1) % 10 == 0:
                logger.info(f"已生成 {batch_end}/{total_elements} 个构件...")
        
        logger.info(f"大数据集生成完成: {len(elements)} 个构件")
        
        return {
            "project_id": project_id,
            "elements": elements,
            "total_count": len(elements),
        }


# 使用示例
if __name__ == "__main__":
    import logging
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    generator = TestDataGenerator()
    
    # 生成小型测试数据集
    logger.info("生成小型测试数据集...")
    small_dataset = generator.create_test_project_with_elements(
        element_count=100,
        levels=5
    )
    logger.info(f"生成完成: {small_dataset['total_count']} 个构件")
    
    # 生成大型测试数据集
    logger.info("\n生成大型测试数据集...")
    large_dataset = generator.generate_large_dataset(
        project_id="stress_test_project",
        total_elements=1000,  # 测试时可以使用10000+
        batch_size=100
    )
    logger.info(f"生成完成: {large_dataset['total_count']} 个构件")

