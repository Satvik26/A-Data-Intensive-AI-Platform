"""
Tests for reliability module.

Tests SLI/SLO definitions, retry logic, and circuit breaker.
Implements DDIA Chapter 1 principles for testing reliability patterns.
"""

import asyncio
import time
from unittest.mock import MagicMock, patch

import pytest

from atlas_api.reliability import (
    ATLAS_API_SLO,
    CRITICAL_ENDPOINT_SLO,
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    ErrorRateSLI,
    LatencySLI,
    RetryConfig,
    ThroughputSLI,
    get_slo_for_endpoint,
    retry_async,
    retry_sync,
)


class TestSLO:
    """Tests for SLI/SLO definitions."""

    def test_latency_sli_valid(self) -> None:
        """Test valid latency SLI creation."""
        sli = LatencySLI(p50_ms=50, p95_ms=200, p99_ms=500, p999_ms=1000)
        assert sli.p50_ms == 50
        assert sli.p95_ms == 200

    def test_latency_sli_invalid_order(self) -> None:
        """Test latency SLI rejects invalid percentile order."""
        with pytest.raises(ValueError):
            LatencySLI(p50_ms=500, p95_ms=200, p99_ms=100, p999_ms=50)

    def test_error_rate_sli_valid(self) -> None:
        """Test valid error rate SLI creation."""
        sli = ErrorRateSLI(max_error_rate=0.01, max_5xx_rate=0.001)
        assert sli.max_error_rate == 0.01

    def test_error_rate_sli_invalid_range(self) -> None:
        """Test error rate SLI rejects invalid ranges."""
        with pytest.raises(ValueError):
            ErrorRateSLI(max_error_rate=1.5, max_5xx_rate=0.001)

    def test_throughput_sli_valid(self) -> None:
        """Test valid throughput SLI creation."""
        sli = ThroughputSLI(min_rps=100, max_rps=10000)
        assert sli.min_rps == 100

    def test_throughput_sli_invalid_order(self) -> None:
        """Test throughput SLI rejects invalid order."""
        with pytest.raises(ValueError):
            ThroughputSLI(min_rps=10000, max_rps=100)

    def test_atlas_api_slo_defaults(self) -> None:
        """Test default Atlas API SLO."""
        assert ATLAS_API_SLO.name == "atlas-api"
        assert ATLAS_API_SLO.latency.p95_ms == 200.0
        assert ATLAS_API_SLO.error_rate.max_error_rate == 0.01

    def test_get_slo_for_critical_endpoint(self) -> None:
        """Test SLO selection for critical endpoints."""
        slo = get_slo_for_endpoint("/auth/login")
        assert slo == CRITICAL_ENDPOINT_SLO
        assert slo.latency.p95_ms == 100.0

    def test_get_slo_for_default_endpoint(self) -> None:
        """Test SLO selection for default endpoints."""
        slo = get_slo_for_endpoint("/api/v1/users")
        assert slo == ATLAS_API_SLO


class TestRetryConfig:
    """Tests for retry configuration."""

    def test_retry_config_valid(self) -> None:
        """Test valid retry config creation."""
        config = RetryConfig(max_attempts=3, base_delay_ms=100)
        assert config.max_attempts == 3
        assert config.base_delay_ms == 100

    def test_retry_config_invalid_attempts(self) -> None:
        """Test retry config rejects invalid attempts."""
        with pytest.raises(ValueError):
            RetryConfig(max_attempts=0)

    def test_calculate_delay_exponential_backoff(self) -> None:
        """Test exponential backoff calculation."""
        config = RetryConfig(
            max_attempts=5,
            base_delay_ms=100,
            max_delay_ms=10000,
            multiplier=2.0,
            jitter=False,
        )

        # Attempt 0: 100ms
        assert config.calculate_delay_ms(0) == 100
        # Attempt 1: 200ms
        assert config.calculate_delay_ms(1) == 200
        # Attempt 2: 400ms
        assert config.calculate_delay_ms(2) == 400
        # Attempt 3: 800ms
        assert config.calculate_delay_ms(3) == 800

    def test_calculate_delay_with_max_cap(self) -> None:
        """Test delay is capped at max_delay_ms."""
        config = RetryConfig(
            max_attempts=5,
            base_delay_ms=100,
            max_delay_ms=1000,
            multiplier=2.0,
            jitter=False,
        )

        # Attempt 4: would be 1600ms, but capped at 1000ms
        assert config.calculate_delay_ms(4) == 1000

    def test_calculate_delay_with_jitter(self) -> None:
        """Test jitter adds randomness to delays."""
        config = RetryConfig(
            max_attempts=3,
            base_delay_ms=100,
            max_delay_ms=10000,
            multiplier=2.0,
            jitter=True,
        )

        # With jitter, delays should vary
        delays = [config.calculate_delay_ms(0) for _ in range(10)]
        assert len(set(delays)) > 1  # Should have variation


class TestRetrySyncDecorator:
    """Tests for synchronous retry decorator."""

    def test_retry_sync_success_first_attempt(self) -> None:
        """Test retry succeeds on first attempt."""
        call_count = 0

        @retry_sync(config=RetryConfig(max_attempts=3))
        def successful_function() -> str:
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_function()
        assert result == "success"
        assert call_count == 1

    def test_retry_sync_success_after_failures(self) -> None:
        """Test retry succeeds after transient failures."""
        call_count = 0

        @retry_sync(
            config=RetryConfig(max_attempts=3, base_delay_ms=10, jitter=False),
            exceptions=(ValueError,),
        )
        def eventually_successful() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Transient error")
            return "success"

        result = eventually_successful()
        assert result == "success"
        assert call_count == 3

    def test_retry_sync_exhausts_attempts(self) -> None:
        """Test retry raises after exhausting attempts."""
        call_count = 0

        @retry_sync(
            config=RetryConfig(max_attempts=3, base_delay_ms=10, jitter=False),
            exceptions=(ValueError,),
        )
        def always_fails() -> str:
            nonlocal call_count
            call_count += 1
            raise ValueError("Persistent error")

        with pytest.raises(ValueError):
            always_fails()

        assert call_count == 3

    def test_retry_sync_respects_exception_types(self) -> None:
        """Test retry only retries specified exception types."""
        call_count = 0

        @retry_sync(
            config=RetryConfig(max_attempts=3),
            exceptions=(ValueError,),
        )
        def raises_type_error() -> str:
            nonlocal call_count
            call_count += 1
            raise TypeError("Not retryable")

        with pytest.raises(TypeError):
            raises_type_error()

        # Should fail immediately without retrying
        assert call_count == 1


class TestRetryAsyncDecorator:
    """Tests for async retry decorator."""

    @pytest.mark.asyncio
    async def test_retry_async_success_first_attempt(self) -> None:
        """Test async retry succeeds on first attempt."""
        call_count = 0

        @retry_async(config=RetryConfig(max_attempts=3))
        async def successful_function() -> str:
            nonlocal call_count
            call_count += 1
            return "success"

        result = await successful_function()
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_async_success_after_failures(self) -> None:
        """Test async retry succeeds after transient failures."""
        call_count = 0

        @retry_async(
            config=RetryConfig(max_attempts=3, base_delay_ms=10, jitter=False),
            exceptions=(ValueError,),
        )
        async def eventually_successful() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Transient error")
            return "success"

        result = await eventually_successful()
        assert result == "success"
        assert call_count == 3


class TestCircuitBreaker:
    """Tests for circuit breaker pattern."""

    def test_circuit_breaker_initial_state(self) -> None:
        """Test circuit breaker starts in CLOSED state."""
        cb = CircuitBreaker("test-service")
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_circuit_breaker_success_in_closed_state(self) -> None:
        """Test circuit breaker allows calls in CLOSED state."""
        cb = CircuitBreaker("test-service")

        def successful_call() -> str:
            return "success"

        result = cb.call_sync(successful_call)
        assert result == "success"
        assert cb.state == CircuitState.CLOSED

    def test_circuit_breaker_opens_after_threshold(self) -> None:
        """Test circuit breaker opens after failure threshold."""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker("test-service", config=config)

        def failing_call() -> None:
            raise ValueError("Service error")

        # First 3 failures
        for _ in range(3):
            with pytest.raises(ValueError):
                cb.call_sync(failing_call)

        # Circuit should be open
        assert cb.state == CircuitState.OPEN

        # Next call should fail immediately without calling function
        with pytest.raises(Exception, match="Circuit breaker.*OPEN"):
            cb.call_sync(failing_call)

    def test_circuit_breaker_half_open_recovery(self) -> None:
        """Test circuit breaker attempts recovery in HALF_OPEN state."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout_seconds=1,
            success_threshold=2,
        )
        cb = CircuitBreaker("test-service", config=config)

        # Cause failures to open circuit
        def failing_call() -> None:
            raise ValueError("Service error")

        for _ in range(2):
            with pytest.raises(ValueError):
                cb.call_sync(failing_call)

        assert cb.state == CircuitState.OPEN

        # Wait for recovery timeout
        time.sleep(1.1)

        # Next call should transition to HALF_OPEN
        def successful_call() -> str:
            return "success"

        # First success in HALF_OPEN
        result = cb.call_sync(successful_call)
        assert result == "success"
        assert cb.state == CircuitState.HALF_OPEN

        # Second success should close circuit
        result = cb.call_sync(successful_call)
        assert result == "success"
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_breaker_async(self) -> None:
        """Test circuit breaker with async functions."""
        cb = CircuitBreaker("test-service")

        async def successful_call() -> str:
            return "success"

        result = await cb.call_async(successful_call)
        assert result == "success"

    def test_circuit_breaker_get_status(self) -> None:
        """Test circuit breaker status reporting."""
        cb = CircuitBreaker("test-service")
        status = cb.get_status()

        assert status["name"] == "test-service"
        assert status["state"] == "closed"
        assert status["failure_count"] == 0

