"""
检验批API性能测试（Locust）

测试检验批创建、查询、批量操作API的性能
"""

from locust import HttpUser, task, between
import random


class LotsUser(HttpUser):
    """检验批API用户行为模拟"""
    
    wait_time = between(2, 5)
    
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
            # 加载测试数据
            self._load_test_data()
        else:
            self.token = None
            self.item_ids = []
    
    def _load_test_data(self):
        """加载测试数据（项目ID、分项ID等）"""
        # 尝试获取一个项目的层级结构以获取item_id
        response = self.client.get(
            "/api/v1/hierarchy/projects?page=1&page_size=1",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            projects = data.get("data", {}).get("items", [])
            if projects:
                project_id = projects[0].get("id")
                # 获取项目层级以找到item_id
                hierarchy_response = self.client.get(
                    f"/api/v1/hierarchy/projects/{project_id}/hierarchy",
                    headers={
                        "Authorization": f"Bearer {self.token}",
                        "Content-Type": "application/json"
                    }
                )
                # 这里简化处理，实际应该递归查找item_id
                self.item_ids = ["unassigned_item"]  # 使用默认值
            else:
                self.item_ids = ["unassigned_item"]
        else:
            self.item_ids = ["unassigned_item"]
    
    def _get_headers(self):
        """获取请求头"""
        if not self.token:
            return {"Content-Type": "application/json"}
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    @task(3)
    def get_lot_elements(self):
        """获取检验批构件列表性能测试"""
        lot_id = f"lot_{random.randint(1, 100)}"
        page = random.randint(1, 10)
        page_size = random.choice([10, 20, 50])
        
        self.client.get(
            f"/api/v1/inspection-lots/{lot_id}/elements?page={page}&page_size={page_size}",
            headers=self._get_headers(),
            name="GET /api/v1/inspection-lots/{lot_id}/elements"
        )
    
    @task(2)
    def create_lots_by_rule(self):
        """按规则创建检验批性能测试"""
        if not self.item_ids:
            return
        
        item_id = random.choice(self.item_ids)
        rule_type = random.choice(["BY_LEVEL", "BY_ZONE", "BY_LEVEL_AND_ZONE"])
        
        self.client.post(
            "/api/v1/inspection-lots/strategy",
            json={
                "item_id": item_id,
                "rule_type": rule_type
            },
            headers=self._get_headers(),
            name="POST /api/v1/inspection-lots/strategy"
        )
    
    @task(1)
    def assign_elements_to_lot(self):
        """分配构件到检验批性能测试"""
        lot_id = f"lot_{random.randint(1, 100)}"
        element_ids = [f"element_{random.randint(1, 1000)}" for _ in range(5)]
        
        self.client.post(
            f"/api/v1/inspection-lots/{lot_id}/elements",
            json={"element_ids": element_ids},
            headers=self._get_headers(),
            name="POST /api/v1/inspection-lots/{lot_id}/elements"
        )
    
    @task(1)
    def remove_elements_from_lot(self):
        """从检验批移除构件性能测试"""
        lot_id = f"lot_{random.randint(1, 100)}"
        element_ids = [f"element_{random.randint(1, 1000)}" for _ in range(3)]
        
        self.client.delete(
            f"/api/v1/inspection-lots/{lot_id}/elements",
            json={"element_ids": element_ids},
            headers=self._get_headers(),
            name="DELETE /api/v1/inspection-lots/{lot_id}/elements"
        )
    
    @task(1)
    def update_lot_status(self):
        """更新检验批状态性能测试"""
        lot_id = f"lot_{random.randint(1, 100)}"
        status = random.choice(["IN_PROGRESS", "SUBMITTED"])
        
        self.client.patch(
            f"/api/v1/inspection-lots/{lot_id}/status",
            json={"status": status},
            headers=self._get_headers(),
            name="PATCH /api/v1/inspection-lots/{lot_id}/status"
        )

