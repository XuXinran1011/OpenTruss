"""
构件API性能测试（Locust）

测试构件查询、更新、批量操作API的性能
"""

from locust import HttpUser, task, between
import random


class ElementsUser(HttpUser):
    """构件API用户行为模拟"""
    
    wait_time = between(1, 2)
    
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
        else:
            self.token = None
    
    def _get_headers(self):
        """获取请求头"""
        if not self.token:
            return {"Content-Type": "application/json"}
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    @task(5)
    def get_elements(self):
        """查询构件列表性能测试"""
        page = random.randint(1, 10)
        page_size = random.choice([10, 20, 50])
        
        self.client.get(
            f"/api/v1/elements?page={page}&page_size={page_size}",
            headers=self._get_headers(),
            name="GET /api/v1/elements"
        )
    
    @task(3)
    def get_elements_with_filters(self):
        """带筛选条件的构件查询性能测试"""
        speckle_type = random.choice(["Wall", "Floor", "Column", None])
        level_id = f"level_{random.randint(1, 10)}"
        
        params = {
            "page": 1,
            "page_size": 20
        }
        if speckle_type:
            params["speckle_type"] = speckle_type
        if random.choice([True, False]):
            params["level_id"] = level_id
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        
        self.client.get(
            f"/api/v1/elements?{query_string}",
            headers=self._get_headers(),
            name="GET /api/v1/elements (filtered)"
        )
    
    @task(2)
    def get_element_detail(self):
        """获取构件详情性能测试"""
        # 使用一个假设的ID（实际测试中应该使用真实存在的ID）
        element_id = f"element_{random.randint(1, 1000)}"
        
        self.client.get(
            f"/api/v1/elements/{element_id}",
            headers=self._get_headers(),
            name="GET /api/v1/elements/{element_id}"
        )
    
    @task(2)
    def batch_get_element_details(self):
        """批量获取构件详情性能测试"""
        element_ids = [f"element_{random.randint(1, 1000)}" for _ in range(5)]
        
        self.client.post(
            "/api/v1/elements/batch-details",
            json={"element_ids": element_ids},
            headers=self._get_headers(),
            name="POST /api/v1/elements/batch-details"
        )
    
    @task(1)
    def update_element_topology(self):
        """更新构件拓扑性能测试"""
        element_id = f"element_{random.randint(1, 1000)}"
        
        self.client.patch(
            f"/api/v1/elements/{element_id}/topology",
            json={
                "geometry": {
                    "type": "Polyline",
                    "coordinates": [[0, 0, 0], [10, 0, 0], [10, 5, 0], [0, 5, 0]],
                    "closed": True
                }
            },
            headers=self._get_headers(),
            name="PATCH /api/v1/elements/{element_id}/topology"
        )
    
    @task(1)
    def batch_lift_elements(self):
        """批量设置Z轴参数性能测试"""
        element_ids = [f"element_{random.randint(1, 1000)}" for _ in range(3)]
        
        self.client.post(
            "/api/v1/elements/batch-lift",
            json={
                "element_ids": element_ids,
                "height": random.uniform(2.5, 4.0),
                "base_offset": random.uniform(-0.1, 0.1),
                "material": random.choice(["混凝土", "钢材", "木材"])
            },
            headers=self._get_headers(),
            name="POST /api/v1/elements/batch-lift"
        )

