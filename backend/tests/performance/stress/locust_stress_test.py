"""
Locust极限负载压力测试

测试系统在极限并发用户数（500+）下的表现
"""

from locust import HttpUser, task, between, events
import logging


logger = logging.getLogger(__name__)


class StressUser(HttpUser):
    """压力测试用户"""
    
    wait_time = between(0.5, 2)
    
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
    
    @task(3)
    def stress_get_elements(self):
        """压力测试：频繁查询构件"""
        self.client.get(
            "/api/v1/elements?page=1&page_size=50",
            headers=self._get_headers(),
            name="Stress: GET /elements"
        )
    
    @task(2)
    def stress_get_hierarchy(self):
        """压力测试：频繁查询层级结构"""
        self.client.get(
            "/api/v1/hierarchy/projects?page=1&page_size=10",
            headers=self._get_headers(),
            name="Stress: GET /hierarchy/projects"
        )
    
    @task(1)
    def stress_get_auth_me(self):
        """压力测试：频繁获取用户信息"""
        if not self.token:
            return
        
        self.client.get(
            "/api/v1/auth/me",
            headers=self._get_headers(),
            name="Stress: GET /auth/me"
        )


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """测试开始时记录"""
    logger.info("=== Stress Test Started ===")
    logger.info(f"Target host: {environment.host}")
    logger.info(f"Expected users: 500+")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """测试结束时记录"""
    logger.info("=== Stress Test Completed ===")
    stats = environment.stats
    logger.info(f"Total requests: {stats.total.num_requests}")
    logger.info(f"Total failures: {stats.total.num_failures}")
    logger.info(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    logger.info(f"95th percentile: {stats.total.get_response_time_percentile(0.95):.2f}ms")

