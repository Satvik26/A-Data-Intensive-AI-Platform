"""
Stress test with zero wait time for maximum throughput testing.
Run: locust -f tests/load/stress_test.py --host=http://localhost:8000
"""

from locust import HttpUser, task, constant


class StressTestUser(HttpUser):
    """
    Zero-wait stress test user.
    
    Hammers the API as fast as possible to measure maximum throughput.
    No wait time between requests - pure stress test.
    """
    
    host = "http://localhost:8000"
    wait_time = constant(0)  # No wait - maximum stress
    
    @task
    def health_check(self):
        """Rapid-fire health checks"""
        self.client.get("/health")

