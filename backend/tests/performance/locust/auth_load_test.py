"""
认证API性能测试（Locust）

测试登录API的并发性能和响应时间
"""

from locust import HttpUser, task, between
import json


class AuthUser(HttpUser):
    """认证用户行为模拟"""
    
    wait_time = between(1, 3)  # 用户操作间隔1-3秒
    
    def on_start(self):
        """测试开始时的初始化"""
        self.token = None
        self.username = "editor"
        self.password = "editor123"
    
    @task(3)
    def login(self):
        """登录API性能测试"""
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "username": self.username,
                "password": self.password
            },
            headers={"Content-Type": "application/json"},
            name="POST /api/v1/auth/login"
        )
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "access_token" in data["data"]:
                self.token = data["data"]["access_token"]
    
    @task(1)
    def get_current_user(self):
        """获取当前用户信息API性能测试"""
        if not self.token:
            return
        
        response = self.client.get(
            "/api/v1/auth/me",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            },
            name="GET /api/v1/auth/me"
        )
        
        if response.status_code == 401:
            # Token过期，重新登录
            self.token = None
    
    @task(1)
    def logout(self):
        """登出API性能测试"""
        if not self.token:
            return
        
        self.client.post(
            "/api/v1/auth/logout",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            },
            name="POST /api/v1/auth/logout"
        )
        
        self.token = None

