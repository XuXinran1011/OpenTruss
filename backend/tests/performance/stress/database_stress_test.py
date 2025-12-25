"""
数据库压力测试

测试Memgraph在大量数据和查询下的性能
"""

import asyncio
import time
from typing import List
from app.utils.memgraph import MemgraphClient
import logging


logger = logging.getLogger(__name__)


class DatabaseStressTest:
    """数据库压力测试类"""
    
    def __init__(self, client: MemgraphClient):
        self.client = client
    
    def test_large_query_performance(self, iterations: int = 100):
        """测试大量查询的性能"""
        logger.info(f"开始执行 {iterations} 次查询性能测试...")
        
        query = """
        MATCH (e:Element)
        RETURN e.id as id, e.speckle_type as type
        LIMIT 100
        """
        
        start_time = time.time()
        total_time = 0
        
        for i in range(iterations):
            query_start = time.time()
            result = self.client.execute_query(query)
            query_time = time.time() - query_start
            total_time += query_time
            
            if (i + 1) % 10 == 0:
                logger.info(f"完成 {i + 1}/{iterations} 次查询，平均时间: {total_time / (i + 1) * 1000:.2f}ms")
        
        elapsed = time.time() - start_time
        avg_time = total_time / iterations * 1000
        
        logger.info(f"查询性能测试完成:")
        logger.info(f"  总耗时: {elapsed:.2f}秒")
        logger.info(f"  平均查询时间: {avg_time:.2f}ms")
        logger.info(f"  QPS: {iterations / elapsed:.2f}")
        
        return {
            "iterations": iterations,
            "total_time": elapsed,
            "avg_query_time_ms": avg_time,
            "qps": iterations / elapsed,
        }
    
    def test_complex_query_performance(self, iterations: int = 50):
        """测试复杂查询（带关系）的性能"""
        logger.info(f"开始执行 {iterations} 次复杂查询性能测试...")
        
        query = """
        MATCH (p:Project)-[:PHYSICALLY_CONTAINS]->(b:Building)
               -[:PHYSICALLY_CONTAINS]->(d:Division)
               -[:PHYSICALLY_CONTAINS]->(sd:SubDivision)
               -[:PHYSICALLY_CONTAINS]->(i:Item)
               <-[:BELONGS_TO]-(e:Element)
        WHERE p.id = $project_id
        RETURN i.id as item_id, count(e) as element_count
        ORDER BY element_count DESC
        LIMIT 20
        """
        
        start_time = time.time()
        total_time = 0
        
        # 获取一个项目ID
        project_result = self.client.execute_query("MATCH (p:Project) RETURN p.id as id LIMIT 1")
        if not project_result:
            logger.warning("没有找到项目，跳过复杂查询测试")
            return None
        
        project_id = project_result[0]["id"]
        
        for i in range(iterations):
            query_start = time.time()
            result = self.client.execute_query(query, {"project_id": project_id})
            query_time = time.time() - query_start
            total_time += query_time
            
            if (i + 1) % 10 == 0:
                logger.info(f"完成 {i + 1}/{iterations} 次复杂查询，平均时间: {total_time / (i + 1) * 1000:.2f}ms")
        
        elapsed = time.time() - start_time
        avg_time = total_time / iterations * 1000
        
        logger.info(f"复杂查询性能测试完成:")
        logger.info(f"  总耗时: {elapsed:.2f}秒")
        logger.info(f"  平均查询时间: {avg_time:.2f}ms")
        logger.info(f"  QPS: {iterations / elapsed:.2f}")
        
        return {
            "iterations": iterations,
            "total_time": elapsed,
            "avg_query_time_ms": avg_time,
            "qps": iterations / elapsed,
        }
    
    def test_concurrent_queries(self, concurrent_users: int = 50, queries_per_user: int = 10):
        """测试并发查询性能"""
        logger.info(f"开始执行并发查询测试: {concurrent_users} 个并发用户，每个 {queries_per_user} 次查询...")
        
        query = """
        MATCH (e:Element)
        WHERE e.speckle_type = $type
        RETURN count(e) as count
        """
        
        async def user_query(user_id: int):
            """单个用户的查询任务"""
            query_times = []
            for i in range(queries_per_user):
                start = time.time()
                result = self.client.execute_query(query, {"type": "Wall"})
                query_time = time.time() - start
                query_times.append(query_time)
                await asyncio.sleep(0.1)  # 模拟用户操作间隔
            return query_times
        
        async def run_concurrent_test():
            """运行并发测试"""
            start_time = time.time()
            tasks = [user_query(i) for i in range(concurrent_users)]
            results = await asyncio.gather(*tasks)
            elapsed = time.time() - start_time
            
            # 统计结果
            all_times = [t for user_times in results for t in user_times]
            avg_time = sum(all_times) / len(all_times) * 1000
            total_queries = concurrent_users * queries_per_user
            
            logger.info(f"并发查询测试完成:")
            logger.info(f"  并发用户数: {concurrent_users}")
            logger.info(f"  总查询数: {total_queries}")
            logger.info(f"  总耗时: {elapsed:.2f}秒")
            logger.info(f"  平均查询时间: {avg_time:.2f}ms")
            logger.info(f"  总QPS: {total_queries / elapsed:.2f}")
            
            return {
                "concurrent_users": concurrent_users,
                "queries_per_user": queries_per_user,
                "total_queries": total_queries,
                "total_time": elapsed,
                "avg_query_time_ms": avg_time,
                "total_qps": total_queries / elapsed,
            }
        
        # 注意：这个测试需要异步环境
        # 在实际使用中，可能需要调整以适应同步环境
        try:
            return asyncio.run(run_concurrent_test())
        except Exception as e:
            logger.error(f"并发查询测试失败: {e}")
            return None


def run_stress_tests():
    """运行所有压力测试"""
    client = MemgraphClient()
    
    logger.info("=== 开始数据库压力测试 ===")
    
    test = DatabaseStressTest(client)
    
    # 1. 简单查询性能
    logger.info("\n1. 简单查询性能测试")
    simple_result = test.test_large_query_performance(iterations=100)
    
    # 2. 复杂查询性能
    logger.info("\n2. 复杂查询性能测试")
    complex_result = test.test_complex_query_performance(iterations=50)
    
    # 3. 并发查询性能（如果需要）
    # logger.info("\n3. 并发查询性能测试")
    # concurrent_result = test.test_concurrent_queries(concurrent_users=50, queries_per_user=10)
    
    logger.info("\n=== 数据库压力测试完成 ===")
    
    return {
        "simple_query": simple_result,
        "complex_query": complex_result,
        # "concurrent_query": concurrent_result,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    results = run_stress_tests()
    print("\n测试结果汇总:")
    print(results)

