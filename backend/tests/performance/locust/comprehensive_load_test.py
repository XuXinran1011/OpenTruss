"""
综合性能测试（Locust）

模拟真实用户行为，混合多种API调用
"""

from locust import HttpUser, task, between, SequentialTaskSet
import random


class EditorWorkflow(SequentialTaskSet):
    """Editor用户工作流（顺序任务）"""
    
    @task
    def step1_login(self):
        """步骤1：登录"""
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
            self.user.token = data.get("data", {}).get("access_token")
    
    @task
    def step2_get_projects(self):
        """步骤2：获取项目列表"""
        if not self.user.token:
            self.interrupt()
            return
        
        self.client.get(
            "/api/v1/hierarchy/projects?page=1&page_size=20",
            headers={
                "Authorization": f"Bearer {self.user.token}",
                "Content-Type": "application/json"
            }
        )
    
    @task
    def step3_get_elements(self):
        """步骤3：查询构件"""
        if not self.user.token:
            self.interrupt()
            return
        
        self.client.get(
            "/api/v1/elements?page=1&page_size=20",
            headers={
                "Authorization": f"Bearer {self.user.token}",
                "Content-Type": "application/json"
            }
        )
    
    @task
    def step4_update_element(self):
        """步骤4：更新构件拓扑"""
        if not self.user.token:
            self.interrupt()
            return
        
        element_id = f"element_{random.randint(1, 1000)}"
        self.client.patch(
            f"/api/v1/elements/{element_id}/topology",
            json={
                "geometry_2d": {
                    "type": "Polyline",
                    "coordinates": [[0, 0], [10, 0], [10, 5], [0, 5]],
                    "closed": True
                }
            },
            headers={
                "Authorization": f"Bearer {self.user.token}",
                "Content-Type": "application/json"
            }
        )


class ApproverWorkflow(SequentialTaskSet):
    """Approver用户工作流（顺序任务）"""
    
    @task
    def step1_login(self):
        """步骤1：登录"""
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "username": "approver",
                "password": "approver123"
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            self.user.token = data.get("data", {}).get("access_token")
    
    @task
    def step2_get_lots(self):
        """步骤2：查看检验批列表"""
        if not self.user.token:
            self.interrupt()
            return
        
        # 通过项目层级获取检验批
        self.client.get(
            "/api/v1/hierarchy/projects?page=1&page_size=10",
            headers={
                "Authorization": f"Bearer {self.user.token}",
                "Content-Type": "application/json"
            }
        )
    
    @task
    def step3_get_approval_history(self):
        """步骤3：查看审批历史"""
        if not self.user.token:
            self.interrupt()
            return
        
        lot_id = f"lot_{random.randint(1, 100)}"
        self.client.get(
            f"/api/v1/inspection-lots/{lot_id}/approval-history",
            headers={
                "Authorization": f"Bearer {self.user.token}",
                "Content-Type": "application/json"
            }
        )
    
    @task
    def step4_approve_lot(self):
        """步骤4：审批检验批"""
        if not self.user.token:
            self.interrupt()
            return
        
        lot_id = f"lot_{random.randint(1, 100)}"
        self.client.post(
            f"/api/v1/inspection-lots/{lot_id}/approve",
            json={"comment": "综合测试：审批通过"},
            headers={
                "Authorization": f"Bearer {self.user.token}",
                "Content-Type": "application/json"
            }
        )


class ComprehensiveUser(HttpUser):
    """综合性能测试用户"""
    
    wait_time = between(1, 3)
    token = None
    
    tasks = {
        EditorWorkflow: 3,  # 70%的用户是Editor
        ApproverWorkflow: 1,  # 30%的用户是Approver
    }
    
    @task
    def random_api_call(self):
        """随机API调用（模拟用户浏览行为）"""
        if not self.token:
            return
        
        endpoints = [
            ("GET", "/api/v1/hierarchy/projects?page=1&page_size=10"),
            ("GET", "/api/v1/elements?page=1&page_size=20"),
            ("GET", "/api/v1/auth/me"),
        ]
        
        method, endpoint = random.choice(endpoints)
        
        if method == "GET":
            self.client.get(
                endpoint,
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json"
                }
            )

