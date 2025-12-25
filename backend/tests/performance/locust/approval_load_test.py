"""
审批API性能测试（Locust）

测试审批通过、驳回、审批历史查询API的性能
"""

from locust import HttpUser, task, between
import random


class ApprovalUser(HttpUser):
    """审批API用户行为模拟（Approver角色）"""
    
    wait_time = between(2, 5)
    
    def on_start(self):
        """使用Approver角色登录"""
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
    
    @task(3)
    def get_approval_history(self):
        """获取审批历史性能测试"""
        lot_id = f"lot_{random.randint(1, 100)}"
        
        self.client.get(
            f"/api/v1/inspection-lots/{lot_id}/approval-history",
            headers=self._get_headers(),
            name="GET /api/v1/inspection-lots/{lot_id}/approval-history"
        )
    
    @task(2)
    def approve_lot(self):
        """审批通过性能测试"""
        lot_id = f"lot_{random.randint(1, 100)}"
        
        self.client.post(
            f"/api/v1/inspection-lots/{lot_id}/approve",
            json={
                "comment": "性能测试：审批通过"
            },
            headers=self._get_headers(),
            name="POST /api/v1/inspection-lots/{lot_id}/approve"
        )
    
    @task(1)
    def reject_lot(self):
        """审批驳回性能测试"""
        lot_id = f"lot_{random.randint(1, 100)}"
        
        self.client.post(
            f"/api/v1/inspection-lots/{lot_id}/reject",
            json={
                "reason": "性能测试：审批驳回",
                "comment": "需要进一步完善"
            },
            headers=self._get_headers(),
            name="POST /api/v1/inspection-lots/{lot_id}/reject"
        )

