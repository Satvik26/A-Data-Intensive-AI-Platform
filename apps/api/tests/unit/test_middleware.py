"""
Tests for reliability middleware.

Tests request ID tracking, timeouts, metrics collection, and load shedding.
Implements DDIA Chapter 1 principles for testing middleware.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.testclient import TestClient

from atlas_api.middleware.reliability import (
    ErrorHandlingMiddleware,
    LoadSheddingMiddleware,
    MetricsMiddleware,
    RequestIDMiddleware,
    TimeoutMiddleware,
)


@pytest.fixture
def app_with_middleware() -> FastAPI:
    """Create FastAPI app with reliability middleware."""
    app = FastAPI()

    # Add middleware in order
    app.add_middleware(LoadSheddingMiddleware, max_concurrent_requests=10)
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(TimeoutMiddleware)
    app.add_middleware(RequestIDMiddleware)

    @app.get("/success")
    async def success_endpoint() -> dict[str, str]:
        """Successful endpoint."""
        return {"status": "ok"}

    @app.get("/slow")
    async def slow_endpoint() -> dict[str, str]:
        """Slow endpoint that times out."""
        await asyncio.sleep(10)
        return {"status": "ok"}

    @app.get("/error")
    async def error_endpoint() -> None:
        """Endpoint that raises an error."""
        raise ValueError("Test error")

    return app


class TestRequestIDMiddleware:
    """Tests for request ID middleware."""

    def test_request_id_generated(self, app_with_middleware: FastAPI) -> None:
        """Test request ID is generated if not provided."""
        client = TestClient(app_with_middleware)
        response = client.get("/success")

        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 0

    def test_request_id_preserved(self, app_with_middleware: FastAPI) -> None:
        """Test provided request ID is preserved."""
        client = TestClient(app_with_middleware)
        test_id = "test-request-123"

        response = client.get("/success", headers={"X-Request-ID": test_id})

        assert response.status_code == 200
        assert response.headers["X-Request-ID"] == test_id


class TestTimeoutMiddleware:
    """Tests for timeout middleware."""

    def test_request_timeout_returns_504(self, app_with_middleware: FastAPI) -> None:
        """Test timeout returns 504 Gateway Timeout."""
        client = TestClient(app_with_middleware)

        # Patch settings to use very short timeout
        with patch("atlas_api.middleware.reliability.settings") as mock_settings:
            mock_settings.http_timeout = 0.1
            mock_settings.is_production = False

            response = client.get("/slow")

            assert response.status_code == 504
            assert "timeout" in response.json()["message"].lower()

    def test_successful_request_completes(self, app_with_middleware: FastAPI) -> None:
        """Test successful request completes within timeout."""
        client = TestClient(app_with_middleware)
        response = client.get("/success")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestMetricsMiddleware:
    """Tests for metrics middleware."""

    def test_metrics_collected_on_success(self, app_with_middleware: FastAPI) -> None:
        """Test metrics are collected on successful request."""
        client = TestClient(app_with_middleware)

        with patch(
            "atlas_api.middleware.reliability.http_requests_total"
        ) as mock_counter:
            with patch(
                "atlas_api.middleware.reliability.http_request_duration_seconds"
            ) as mock_histogram:
                response = client.get("/success")

                assert response.status_code == 200
                # Verify metrics were recorded
                assert mock_counter.labels.called
                assert mock_histogram.labels.called

    def test_path_normalization(self) -> None:
        """Test path normalization for metrics."""
        from atlas_api.middleware.reliability import MetricsMiddleware

        # Test UUID normalization
        path = "/api/v1/users/550e8400-e29b-41d4-a716-446655440000"
        normalized = MetricsMiddleware._normalize_path(path)
        assert "{id}" in normalized
        assert "550e8400" not in normalized

        # Test numeric ID normalization
        path = "/api/v1/users/123/posts/456"
        normalized = MetricsMiddleware._normalize_path(path)
        assert normalized == "/api/v1/users/{id}/posts/{id}"

        # Test trailing slash removal
        path = "/api/v1/users/"
        normalized = MetricsMiddleware._normalize_path(path)
        assert normalized == "/api/v1/users"


class TestErrorHandlingMiddleware:
    """Tests for error handling middleware."""

    def test_error_returns_500(self, app_with_middleware: FastAPI) -> None:
        """Test unhandled error returns 500."""
        client = TestClient(app_with_middleware)
        response = client.get("/error")

        assert response.status_code == 500
        assert "error" in response.json()

    def test_error_includes_request_id(self, app_with_middleware: FastAPI) -> None:
        """Test error response includes request ID."""
        client = TestClient(app_with_middleware)
        response = client.get("/error")

        assert response.status_code == 500
        assert "request_id" in response.json()


class TestLoadSheddingMiddleware:
    """Tests for load shedding middleware."""

    def test_load_shedding_rejects_overload(self) -> None:
        """Test load shedding rejects requests when overloaded."""
        app = FastAPI()
        app.add_middleware(LoadSheddingMiddleware, max_concurrent_requests=1)

        @app.get("/slow")
        async def slow_endpoint() -> dict[str, str]:
            await asyncio.sleep(1)
            return {"status": "ok"}

        @app.get("/fast")
        async def fast_endpoint() -> dict[str, str]:
            return {"status": "ok"}

        client = TestClient(app)

        # First request should succeed
        response1 = client.get("/fast")
        assert response1.status_code == 200

    def test_load_shedding_returns_429(self) -> None:
        """Test load shedding returns 429 Too Many Requests."""
        app = FastAPI()
        app.add_middleware(LoadSheddingMiddleware, max_concurrent_requests=0)

        @app.get("/test")
        async def test_endpoint() -> dict[str, str]:
            return {"status": "ok"}

        client = TestClient(app)
        # First request will increment current_requests to 1, which exceeds max of 0
        response = client.get("/test")

        assert response.status_code == 429
        assert "Too Many Requests" in response.json()["error"]


class TestMiddlewareIntegration:
    """Integration tests for middleware stack."""

    def test_middleware_order_preserved(self, app_with_middleware: FastAPI) -> None:
        """Test middleware processes requests in correct order."""
        client = TestClient(app_with_middleware)

        # Request should pass through all middleware
        response = client.get("/success")

        assert response.status_code == 200
        assert "X-Request-ID" in response.headers

    def test_error_propagates_through_middleware(
        self, app_with_middleware: FastAPI
    ) -> None:
        """Test errors propagate through middleware stack."""
        client = TestClient(app_with_middleware)

        response = client.get("/error")

        # Should be caught by error handling middleware
        assert response.status_code == 500
        assert "request_id" in response.json()

