"""
层级结构API性能测试（Locust）

测试项目层级树查询、递归查询等API的性能
"""

from locust import HttpUser, task, between
import random


class HierarchyUser(HttpUser):
    """层级结构API用户行为模拟"""
    
    wait_time = between(1, 3)
    
    def on_start(self):
        """登录获取Token"""
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "username": "editor",
                "password": "editor123"
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("data", {}).get("access_token")
            # 获取项目列表，用于后续测试
            self._load_projects()
        else:
            self.token = None
            self.project_ids = []
    
    def _load_projects(self):
        """加载项目ID列表"""
        response = self.client.get(
            "/api/v1/hierarchy/projects",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            self.project_ids = [p.get("id") for p in data.get("data", {}).get("items", [])]
        else:
            self.project_ids = []
    
    def _get_headers(self):
        """获取请求头"""
        if not self.token:
            return {"Content-Type": "application/json"}
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    @task(5)
    def get_projects(self):
        """获取项目列表性能测试"""
        page = random.randint(1, 5)
        page_size = random.choice([10, 20])
        
        self.client.get(
            f"/api/v1/hierarchy/projects?page={page}&page_size={page_size}",
            headers=self._get_headers(),
            name="GET /api/v1/hierarchy/projects"
        )
    
    @task(3)
    def get_project_hierarchy(self):
        """获取项目层级树性能测试"""
        if not self.project_ids:
            return
        
        project_id = random.choice(self.project_ids)
        
        self.client.get(
            f"/api/v1/hierarchy/projects/{project_id}/hierarchy",
            headers=self._get_headers(),
            name="GET /api/v1/hierarchy/projects/{project_id}/hierarchy"
        )
    
    @task(2)
    def get_item_detail(self):
        """获取分项详情性能测试"""
        item_id = f"item_{random.randint(1, 100)}"
        
        self.client.get(
            f"/api/v1/hierarchy/items/{item_id}",
            headers=self._get_headers(),
            name="GET /api/v1/hierarchy/items/{item_id}"
        )
    
    @task(1)
    def get_division_detail(self):
        """获取分部详情性能测试"""
        division_id = f"division_{random.randint(1, 50)}"
        
        self.client.get(
            f"/api/v1/hierarchy/divisions/{division_id}",
            headers=self._get_headers(),
            name="GET /api/v1/hierarchy/divisions/{division_id}"
        )
    
    @task(1)
    def get_building_detail(self):
        """获取单体详情性能测试"""
        building_id = f"building_{random.randint(1, 20)}"
        
        self.client.get(
            f"/api/v1/hierarchy/buildings/{building_id}",
            headers=self._get_headers(),
            name="GET /api/v1/hierarchy/buildings/{building_id}"
        )

