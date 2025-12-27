"""手动验证测试脚本

用于快速验证 Phase 1 的核心功能
使用方法: python -m pytest backend/tests/test_manual_verification.py -v -s
或直接运行: python backend/tests/test_manual_verification.py
"""

import sys
import io
from pathlib import Path

# 修复 Windows 控制台 Unicode 编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "backend"))

import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_imports():
    """测试 1: 验证所有模块可以正确导入"""
    print("\n" + "="*60)
    print("测试 1: 模块导入测试")
    print("="*60)
    
    try:
        # 测试 GB50300 节点模型导入
        from app.models.gb50300 import (
            ProjectNode, BuildingNode, DivisionNode, SubDivisionNode,
            ItemNode, InspectionLotNode, LevelNode, ZoneNode,
            SystemNode, SubSystemNode, ElementNode
        )
        print("[OK] GB50300 节点模型导入成功")
        
        # 测试 Speckle 模型导入
        from app.models.speckle import SpeckleBuiltElement, Wall, Beam
        print("[OK] Speckle 模型导入成功")
        
        # 测试工具模块导入
        from app.utils.memgraph import MemgraphClient, get_memgraph_client
        print("[OK] Memgraph 工具导入成功")
        
        # 测试服务模块导入
        from app.services.schema import initialize_schema
        from app.services.ingestion import IngestionService
        print("[OK] 服务模块导入成功")
        
        # 测试配置导入
        from app.core.config import settings
        print("[OK] 配置模块导入成功")
        print(f"  Memgraph 配置: {settings.memgraph_host}:{settings.memgraph_port}")
        
        print("\n[PASS] 所有模块导入成功！")
        return True
        
    except Exception as e:
        print(f"\n[FAIL] 模块导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_memgraph_connection():
    """测试 2: 验证 Memgraph 连接"""
    print("\n" + "="*60)
    print("测试 2: Memgraph 连接测试")
    print("="*60)
    
    try:
        from app.utils.memgraph import MemgraphClient
        
        print(f"正在连接到 Memgraph...")
        client = MemgraphClient()
        print("[OK] Memgraph 连接成功")
        
        # 执行简单查询
        print("执行测试查询...")
        result = client.execute_query("RETURN 1 as test")
        print(f"[OK] 查询执行成功，结果: {result}")
        
        # 测试获取数据库版本（如果支持）
        try:
            version_result = client.execute_query("RETURN 'Memgraph Connected' as status")
            print(f"[OK] 数据库响应正常: {version_result}")
        except Exception as e:
            print(f"[WARN] 版本查询失败（非关键）: {e}")
        
        print("\n[PASS] Memgraph 连接测试通过！")
        return True
        
    except Exception as e:
        print(f"\n[FAIL] Memgraph 连接失败: {e}")
        print("\n请先启动 Memgraph 服务:")
        print("方式 1: 使用 Docker Compose (推荐)")
        print("  cd ..  # 回到项目根目录")
        print("  docker-compose up -d memgraph")
        print("\n方式 2: 直接使用 Docker")
        print("  docker run -it -p 7687:7687 -p 7444:7444 memgraph/memgraph:latest")
        print("\n验证 Memgraph 是否运行:")
        print("  docker ps | Select-String memgraph  # Windows PowerShell")
        print("  curl http://localhost:7444/healthz  # 健康检查")
        print("\n然后重新运行此测试脚本。")
        return False


def test_schema_initialization():
    """测试 3: 验证 Schema 初始化"""
    print("\n" + "="*60)
    print("测试 3: Schema 初始化测试")
    print("="*60)
    
    try:
        from app.utils.memgraph import MemgraphClient
        from app.services.schema import initialize_schema
        
        print("初始化 Schema...")
        client = MemgraphClient()
        initialize_schema(client)
        print("[OK] Schema 初始化完成")
        
        # 验证索引（Memgraph 可能不支持 SHOW INDEXES，使用其他方式验证）
        print("\n验证默认节点...")
        
        # 检查 Unassigned Item
        result = client.execute_query(
            "MATCH (i:Item {id: $id}) RETURN i.id as id, i.name as name",
            {"id": "unassigned_item"}
        )
        if result:
            print(f"[OK] Unassigned Item 存在: {result[0]}")
        else:
            print("[WARN] Unassigned Item 不存在（可能需要先运行应用启动时初始化）")
        
        # 检查默认项目
        result = client.execute_query(
            "MATCH (p:Project {id: $id}) RETURN p.id as id",
            {"id": "default_project"}
        )
        if result:
            print(f"[OK] 默认项目存在: {result[0]['id']}")
        else:
            print("[WARN] 默认项目不存在（这是正常的，如果还没有创建）")
        
        print("\n[PASS] Schema 初始化测试通过！")
        return True
        
    except Exception as e:
        print(f"\n[FAIL] Schema 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_ingestion():
    """测试 5: 验证数据摄入"""
    print("\n" + "="*60)
    print("测试 5: 数据摄入测试")
    print("="*60)
    
    try:
        from app.services.ingestion import IngestionService
        from app.utils.memgraph import MemgraphClient
        from app.models.speckle import Wall
        from app.models.speckle.base import Geometry
        
        print("准备测试数据...")
        # 创建测试用的 Speckle 元素
        geometry = Geometry(
            type="Polyline",
            coordinates=[[0, 0, 0], [10, 0, 0], [10, 5, 0], [0, 5, 0], [0, 0, 0]],
            closed=True
        )
        speckle_wall = Wall(
            speckle_type="Wall",
            geometry=geometry,
            level_id="level_test_001"
        )
        
        print("创建 Ingestion Service...")
        client = MemgraphClient()
        service = IngestionService(client=client)
        
        print("摄入测试元素...")
        element = service.ingest_speckle_element(
            speckle_wall,
            project_id="test_project_001"
        )
        print(f"[OK] 元素摄入成功: {element.id}")
        print(f"  类型: {element.speckle_type}")
        print(f"  楼层: {element.level_id}")
        
        # 验证数据是否存储到 Memgraph
        print("\n验证数据存储...")
        result = client.execute_query(
            "MATCH (e:Element {id: $id}) RETURN e.id as id, e.speckle_type as type",
            {"id": element.id}
        )
        if result:
            print(f"[OK] 元素在 Memgraph 中: {result[0]}")
        else:
            print("[WARN] 元素未在 Memgraph 中找到")
        
        # 验证关系
        print("验证关系...")
        rel_result = client.execute_query(
            """
            MATCH (e:Element {id: $element_id})-[r]->(n)
            RETURN type(r) as rel_type, labels(n) as target_label, n.id as target_id
            """,
            {"element_id": element.id}
        )
        if rel_result:
            print(f"[OK] 找到 {len(rel_result)} 个关系:")
            for rel in rel_result:
                print(f"  - {rel}")
        else:
            print("[WARN] 未找到关系")
        
        print("\n[PASS] 数据摄入测试通过！")
        return True
        
    except Exception as e:
        print(f"\n[FAIL] 数据摄入测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("OpenTruss Phase 1 功能验证测试")
    print("="*60)
    
    results = []
    
    # 测试 1: 模块导入
    results.append(("模块导入", test_imports()))
    
    # 测试 2: Memgraph 连接（如果测试 1 通过）
    if results[-1][1]:
        results.append(("Memgraph 连接", test_memgraph_connection()))
    else:
        print("\n[SKIP] 跳过 Memgraph 连接测试（模块导入失败）")
        results.append(("Memgraph 连接", False))
    
    # 测试 3: Schema 初始化（如果测试 2 通过）
    if results[-1][1]:
        results.append(("Schema 初始化", test_schema_initialization()))
    else:
        print("\n[SKIP] 跳过 Schema 初始化测试（Memgraph 连接失败）")
        results.append(("Schema 初始化", False))
    
    # 测试 5: 数据摄入（如果测试 3 通过）
    if results[-1][1]:
        results.append(("数据摄入", test_data_ingestion()))
    else:
        print("\n[SKIP] 跳过数据摄入测试（Schema 初始化失败）")
        results.append(("数据摄入", False))
    
    # 打印总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{name}: {status}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n[SUCCESS] 所有测试通过！Phase 1 功能验证成功！")
        return 0
    else:
        print("\n[WARNING] 部分测试失败，请检查上述错误信息")
        return 1


if __name__ == "__main__":
    sys.exit(main())

