"""
Unit tests for health check endpoints.

Tests health, readiness, and liveness probes.
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient


def test_health_check_returns_200(client: TestClient) -> None:
    """
    Test that health check endpoint returns 200 OK.

    Scenario: GET /health
    Expected: 200 OK with health status
    """
    response = client.get("/health")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "environment" in data
    assert "uptime_seconds" in data
    assert "dependencies" in data


def test_health_check_includes_dependencies(client: TestClient) -> None:
    """
    Test that health check includes all dependency statuses.

    Scenario: GET /health
    Expected: Response includes postgresql, redis, kafka, minio
    """
    response = client.get("/health")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    dependencies = data["dependencies"]
    dependency_names = {dep["name"] for dep in dependencies}

    assert "postgresql" in dependency_names
    assert "redis" in dependency_names
    assert "kafka" in dependency_names
    assert "minio" in dependency_names


def test_health_check_dependency_structure(client: TestClient) -> None:
    """
    Test that each dependency has required fields.

    Scenario: GET /health
    Expected: Each dependency has name, status, latency_ms
    """
    response = client.get("/health")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    for dep in data["dependencies"]:
        assert "name" in dep
        assert "status" in dep
        assert dep["status"] in ["healthy", "degraded", "unhealthy"]
        # latency_ms is optional but should be present for healthy deps
        if dep["status"] == "healthy":
            assert "latency_ms" in dep
            assert isinstance(dep["latency_ms"], (int, float))
            assert dep["latency_ms"] >= 0


def test_readiness_check_returns_200(client: TestClient) -> None:
    """
    Test that readiness probe returns 200 OK.

    Scenario: GET /health/ready
    Expected: 200 OK with ready status
    """
    response = client.get("/health/ready")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "ready" in data
    assert "timestamp" in data
    assert isinstance(data["ready"], bool)


def test_liveness_check_returns_200(client: TestClient) -> None:
    """
    Test that liveness probe returns 200 OK.

    Scenario: GET /health/live
    Expected: 200 OK with alive status
    """
    response = client.get("/health/live")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "alive" in data
    assert "timestamp" in data
    assert data["alive"] is True


def test_health_check_uptime_increases(client: TestClient) -> None:
    """
    Test that uptime increases between calls.

    Scenario: Call /health twice with delay
    Expected: Second call has higher uptime
    """
    import time

    response1 = client.get("/health")
    uptime1 = response1.json()["uptime_seconds"]

    time.sleep(0.1)

    response2 = client.get("/health")
    uptime2 = response2.json()["uptime_seconds"]

    assert uptime2 > uptime1


def test_health_check_version_matches_config(client: TestClient) -> None:
    """
    Test that health check returns correct version.

    Scenario: GET /health
    Expected: Version matches application version
    """
    from atlas_api.config import get_settings

    settings = get_settings()
    response = client.get("/health")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["version"] == settings.app_version


def test_health_check_environment_matches_config(client: TestClient) -> None:
    """
    Test that health check returns correct environment.

    Scenario: GET /health
    Expected: Environment matches configuration
    """
    from atlas_api.config import get_settings

    settings = get_settings()
    response = client.get("/health")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["environment"] == settings.environment

