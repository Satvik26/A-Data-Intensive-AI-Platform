"""
Pytest configuration and shared fixtures.

Provides common test fixtures for database, Redis, Kafka, etc.
"""

import pytest
from fastapi.testclient import TestClient

from atlas_api.main import app


@pytest.fixture
def client() -> TestClient:
    """
    Create a test client for the FastAPI application.

    Returns:
        TestClient: FastAPI test client
    """
    return TestClient(app)


@pytest.fixture
def sample_health_response() -> dict:
    """
    Sample health check response for testing.

    Returns:
        dict: Sample health response
    """
    return {
        "status": "healthy",
        "version": "0.1.0",
        "environment": "test",
        "uptime_seconds": 100.0,
        "dependencies": [
            {
                "name": "postgresql",
                "status": "healthy",
                "latency_ms": 2.5,
            }
        ],
    }


# TODO: Add more fixtures
# - Database session fixture
# - Redis client fixture
# - Kafka producer/consumer fixtures
# - Mock external services
# - Test data factories

