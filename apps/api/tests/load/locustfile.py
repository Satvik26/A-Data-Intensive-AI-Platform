"""
Load testing with Locust
Run: locust -f tests/load/locustfile.py --host=http://localhost:8000
"""

from locust import HttpUser, task, between
import random


class AtlasUser(HttpUser):
    """Simulates a user interacting with Atlas API"""

    host = "http://localhost:8000"  # Default host
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    @task(3)
    def health_check(self):
        """Health check endpoint (3x more frequent)"""
        self.client.get("/health")
    
    @task(2)
    def metrics(self):
        """Metrics endpoint (2x more frequent)"""
        self.client.get("/metrics")
    
    @task(1)
    def docs(self):
        """API docs endpoint"""
        self.client.get("/docs")


class HighLoadUser(HttpUser):
    """Simulates high-load scenario"""

    host = "http://localhost:8000"  # Default host
    wait_time = between(0.1, 0.5)  # Very short wait
    
    @task
    def rapid_health_checks(self):
        """Rapid health checks"""
        self.client.get("/health")


class SpikeUser(HttpUser):
    """Simulates sudden traffic spike"""

    host = "http://localhost:8000"  # Default host
    wait_time = between(0.01, 0.1)  # Minimal wait
    
    @task
    def spike_requests(self):
        """Spike requests"""
        self.client.get("/health")

