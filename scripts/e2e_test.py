"""
端到端测试脚本
测试 OpenTruss 系统的完整工作流程
"""

import sys
import io
import requests
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime

# 设置 UTF-8 编码（Windows 兼容）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 配置
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"
FRONTEND_URL = "http://localhost:3000"

class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_success(message: str):
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")

def print_error(message: str):
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")

def print_info(message: str):
    print(f"{Colors.BLUE}ℹ {message}{Colors.RESET}")

def print_warning(message: str):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")

def test_backend_health() -> bool:
    """测试后端健康检查"""
    print_info("测试后端健康检查...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"后端健康检查通过: {data.get('status', 'unknown')}")
            return True
        else:
            print_error(f"后端健康检查失败: HTTP {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("无法连接到后端服务（请确保后端正在运行在 http://localhost:8000）")
        return False
    except Exception as e:
        print_error(f"后端健康检查出错: {str(e)}")
        return False

def test_memgraph_connection() -> bool:
    """测试 Memgraph 连接（通过后端）"""
    print_info("测试 Memgraph 连接...")
    try:
        # 通过查询项目列表来测试 Memgraph 连接（使用正确的路由路径）
        response = requests.get(f"{API_BASE}/hierarchy/projects", timeout=5)
        if response.status_code == 200:
            print_success("Memgraph 连接正常")
            return True
        else:
            print_error(f"Memgraph 连接测试失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Memgraph 连接测试出错: {str(e)}")
        return False

def test_data_ingestion() -> Optional[str]:
    """测试数据摄取"""
    print_info("测试数据摄取...")
    
    # 首先需要获取项目列表
    project_id = None
    try:
        response = requests.get(f"{API_BASE}/hierarchy/projects", timeout=5)
        if response.status_code == 200:
            projects = response.json()
            # 处理响应格式：可能是列表，也可能是包含 items 的字典
            if isinstance(projects, list):
                project_list = projects
            elif isinstance(projects, dict) and "items" in projects:
                project_list = projects["items"]
            else:
                project_list = []
            
            if project_list:
                project_id = project_list[0]["id"]
                print_info(f"使用现有项目: {project_id}")
            else:
                print_warning("没有现有项目，数据摄取将创建默认项目结构")
                # 如果没有项目，我们可以使用一个默认的 project_id
                # 根据系统设计，数据摄取应该会自动创建项目结构
                project_id = "default-project-id"  # 这将触发系统创建默认项目
        else:
            print_warning(f"无法获取项目列表: HTTP {response.status_code}")
            project_id = "default-project-id"
    except Exception as e:
        print_warning(f"获取项目列表失败: {str(e)}")
        project_id = "default-project-id"
    
    # 创建一个测试 Speckle 元素（Wall）
    test_element = {
        "speckle_id": f"test-wall-{int(time.time())}",
        "speckle_type": "Wall",
        "units": "meters",
        "geometry_2d": {
            "type": "Polyline",
            "coordinates": [[0, 0], [10, 0], [10, 5], [0, 5]],
            "closed": True
        },
        "height": 3.0,
        "material": {
            "name": "Concrete",
            "category": "Structural"
        }
    }
    
    try:
        # 数据摄取 API 需要 project_id 和 elements 数组
        ingest_request = {
            "project_id": project_id,
            "elements": [test_element]
        }
        
        response = requests.post(
            f"{API_BASE}/ingest",
            json=ingest_request,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        # 数据摄取可能返回 200 或 201
        if response.status_code in [200, 201]:
            data = response.json()
            # 处理响应格式：可能直接是结果，也可能在 data 字段中
            if "data" in data:
                result_data = data["data"]
            else:
                result_data = data
            
            element_ids = result_data.get("element_ids", [])
            ingested_count = result_data.get("ingested_count", 0)
            
            if element_ids:
                element_id = element_ids[0]
                print_success(f"数据摄取成功: element_id = {element_id}, ingested_count = {ingested_count}")
                return element_id
            elif ingested_count > 0:
                print_success(f"数据摄取成功: ingested_count = {ingested_count}（但未返回 element_ids）")
                return "success"
            else:
                print_warning("数据摄取成功，但没有返回 element_id")
                return None
        else:
            print_error(f"数据摄取失败: HTTP {response.status_code}")
            print_error(f"响应: {response.text[:500]}")
            return None
    except Exception as e:
        print_error(f"数据摄取出错: {str(e)}")
        return None

def test_hierarchy_api() -> bool:
    """测试层次结构 API"""
    print_info("测试层次结构 API...")
    
    try:
        # 测试获取项目列表（使用正确的路由路径）
        response = requests.get(f"{API_BASE}/hierarchy/projects", timeout=5)
        if response.status_code != 200:
            print_error(f"获取项目列表失败: HTTP {response.status_code}")
            return False
        
        projects_data = response.json()
        # 处理响应格式：可能是列表，也可能是包含 items 的字典
        if isinstance(projects_data, list):
            projects = projects_data
        elif isinstance(projects_data, dict) and "items" in projects_data:
            projects = projects_data["items"]
        else:
            projects = []
        
        print_success(f"获取项目列表成功: {len(projects)} 个项目")
        
        if projects:
            project_id = projects[0]["id"]
            print_info(f"测试项目详情: {project_id}")
            
            # 测试获取项目详情（使用正确的路由路径）
            try:
                response = requests.get(f"{API_BASE}/hierarchy/projects/{project_id}", timeout=5)
                if response.status_code == 200:
                    project_detail = response.json()
                    # 处理响应格式
                    if isinstance(project_detail, dict) and "data" in project_detail:
                        detail_data = project_detail["data"]
                    else:
                        detail_data = project_detail
                    print_success(f"获取项目详情成功: {detail_data.get('name', 'N/A')}")
                    
                    # 测试获取层次结构（使用正确的路由路径）
                    response = requests.get(f"{API_BASE}/hierarchy/projects/{project_id}/hierarchy", timeout=5)
                    if response.status_code == 200:
                        hierarchy = response.json()
                        print_success("获取层次结构成功")
                        return True
                    else:
                        print_error(f"获取层次结构失败: HTTP {response.status_code}")
                        return False
                else:
                    print_error(f"获取项目详情失败: HTTP {response.status_code}")
                    return False
            except Exception as e:
                print_error(f"获取项目详情出错: {str(e)}")
                return False
        else:
            print_warning("没有项目数据，跳过层次结构测试")
            return True  # 这不算错误，只是没有数据
            
    except Exception as e:
        print_error(f"层次结构 API 测试出错: {str(e)}")
        return False

def test_elements_api(element_id: Optional[str] = None) -> bool:
    """测试构件 API"""
    print_info("测试构件 API...")
    
    try:
        # 测试获取构件列表
        response = requests.get(f"{API_BASE}/elements?page=1&page_size=10", timeout=5)
        if response.status_code != 200:
            print_error(f"获取构件列表失败: HTTP {response.status_code}")
            return False
        
        data = response.json()
        # 处理响应格式：可能在 data 字段中，也可能直接是列表
        if isinstance(data, dict) and "data" in data:
            response_data = data["data"]
        else:
            response_data = data
        
        elements = response_data.get("items", []) if isinstance(response_data, dict) else []
        total = response_data.get("total", len(elements)) if isinstance(response_data, dict) else len(elements)
        print_success(f"获取构件列表成功: {len(elements)} 个构件（总计: {total}）")
        
        if elements:
            test_element_id = element_id or elements[0]["id"]
            print_info(f"测试构件详情: {test_element_id}")
            
            # 测试获取构件详情
            response = requests.get(f"{API_BASE}/elements/{test_element_id}", timeout=5)
            if response.status_code == 200:
                element_detail_data = response.json()
                # 处理响应格式
                if isinstance(element_detail_data, dict) and "data" in element_detail_data:
                    element_detail = element_detail_data["data"]
                else:
                    element_detail = element_detail_data
                
                print_success(f"获取构件详情成功: {element_detail.get('speckle_type', 'N/A')}")
                
                # 检查是否有 geometry_2d
                if element_detail.get("geometry_2d"):
                    print_success("构件包含 geometry_2d 数据")
                else:
                    print_warning("构件不包含 geometry_2d 数据")
                
                return True
            else:
                print_error(f"获取构件详情失败: HTTP {response.status_code}")
                return False
        else:
            print_warning("没有构件数据，跳过构件详情测试")
            return True  # 这不算错误，只是没有数据
            
    except Exception as e:
        print_error(f"构件 API 测试出错: {str(e)}")
        return False

def test_frontend_load() -> bool:
    """测试前端页面加载"""
    print_info("测试前端页面加载...")
    
    try:
        response = requests.get(FRONTEND_URL, timeout=5, allow_redirects=True)
        if response.status_code == 200:
            print_success("前端页面加载成功")
            return True
        else:
            print_warning(f"前端页面返回 HTTP {response.status_code}（可能正在构建）")
            return False
    except requests.exceptions.ConnectionError:
        print_warning("无法连接到前端服务（请确保前端正在运行在 http://localhost:3000）")
        return False
    except Exception as e:
        print_warning(f"前端页面加载测试出错: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("OpenTruss 端到端测试")
    print("=" * 60)
    print()
    
    results = {
        "backend_health": False,
        "memgraph_connection": False,
        "data_ingestion": False,
        "hierarchy_api": False,
        "elements_api": False,
        "frontend_load": False,
    }
    
    # 1. 后端健康检查
    results["backend_health"] = test_backend_health()
    if not results["backend_health"]:
        print_error("\n后端服务不可用，终止测试")
        sys.exit(1)
    print()
    
    # 2. Memgraph 连接测试
    results["memgraph_connection"] = test_memgraph_connection()
    print()
    
    # 3. 数据摄取测试
    element_id = test_data_ingestion()
    results["data_ingestion"] = element_id is not None
    print()
    
    # 等待数据同步
    if results["data_ingestion"]:
        print_info("等待数据同步...")
        time.sleep(1)
    
    # 4. 层次结构 API 测试
    results["hierarchy_api"] = test_hierarchy_api()
    print()
    
    # 5. 构件 API 测试
    results["elements_api"] = test_elements_api(element_id)
    print()
    
    # 6. 前端页面加载测试
    results["frontend_load"] = test_frontend_load()
    print()
    
    # 测试结果汇总
    print("=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    
    for test_name, passed in results.items():
        status = "✓ 通过" if passed else "✗ 失败"
        color = Colors.GREEN if passed else Colors.RED
        print(f"{color}{status}{Colors.RESET}: {test_name}")
    
    print()
    print(f"总计: {passed_tests}/{total_tests} 测试通过")
    
    if passed_tests == total_tests:
        print_success("所有测试通过！")
        sys.exit(0)
    else:
        print_error(f"{total_tests - passed_tests} 个测试失败")
        sys.exit(1)

if __name__ == "__main__":
    main()

