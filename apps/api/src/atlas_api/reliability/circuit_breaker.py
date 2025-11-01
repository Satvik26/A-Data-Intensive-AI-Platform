"""
Circuit breaker pattern implementation.

Implements DDIA Chapter 1 principles for preventing cascading failures.
Circuit breaker stops calling a failing service to allow it to recover.

Reference: DDIA Chapter 1 - Reliability, Cascading Failures
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Any, Awaitable, Callable, Optional, TypeVar

from atlas_api.instrumentation.metrics import (
    circuit_breaker_failures_total,
    circuit_breaker_state,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(str, Enum):
    """Circuit breaker states.

    DDIA Chapter 1: Circuit breaker has three states:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Service is failing, requests are rejected immediately
    - HALF_OPEN: Testing if service has recovered
    """

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Service failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout_seconds: int = 60,
        success_threshold: int = 2,
    ):
        """
        Initialize circuit breaker configuration.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout_seconds: Seconds before attempting recovery
            success_threshold: Number of successes in half-open before closing
        """
        if failure_threshold < 1:
            raise ValueError("failure_threshold must be >= 1")
        if recovery_timeout_seconds < 1:
            raise ValueError("recovery_timeout_seconds must be >= 1")
        if success_threshold < 1:
            raise ValueError("success_threshold must be >= 1")

        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.success_threshold = success_threshold


class CircuitBreaker:
    """
    Circuit breaker for preventing cascading failures.

    DDIA Chapter 1: Circuit breaker is a critical pattern for building
    resilient systems. It prevents a failing service from being called
    repeatedly, allowing it time to recover.

    States:
    - CLOSED: Normal operation, all requests pass through
    - OPEN: Service is failing, requests are rejected immediately
    - HALF_OPEN: Testing if service has recovered, limited requests allowed
    """

    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
        exceptions: tuple[type[Exception], ...] = (Exception,),
    ):
        """
        Initialize circuit breaker.

        Args:
            name: Name of the service being protected
            config: CircuitBreakerConfig instance
            exceptions: Tuple of exception types that trigger circuit opening
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.exceptions = exceptions

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.opened_at: Optional[float] = None

        # Update metrics
        self._update_metrics()

    def _update_metrics(self) -> None:
        """Update Prometheus metrics."""
        state_value = {
            CircuitState.CLOSED: 0,
            CircuitState.OPEN: 1,
            CircuitState.HALF_OPEN: 2,
        }[self.state]
        circuit_breaker_state.labels(service=self.name).set(state_value)

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self.state != CircuitState.OPEN:
            return False

        if self.opened_at is None:
            return False

        elapsed = time.time() - self.opened_at
        return elapsed >= self.config.recovery_timeout_seconds

    def call_sync(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Execute a synchronous function with circuit breaker protection.

        Args:
            func: Function to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Result of function call

        Raises:
            Exception: If circuit is open or function fails
        """
        # Check if we should attempt recovery
        if self._should_attempt_reset():
            self.state = CircuitState.HALF_OPEN
            self.success_count = 0
            self._update_metrics()
            logger.info(f"Circuit breaker {self.name} entering HALF_OPEN state")

        # If circuit is open, reject immediately
        if self.state == CircuitState.OPEN:
            raise Exception(
                f"Circuit breaker {self.name} is OPEN. Service is unavailable."
            )

        try:
            result = func(*args, **kwargs)

            # Success
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self._update_metrics()
                    logger.info(
                        f"Circuit breaker {self.name} recovered, entering CLOSED state"
                    )
            elif self.state == CircuitState.CLOSED:
                # Reset failure count on success
                self.failure_count = 0

            return result

        except self.exceptions as e:
            # Failure
            self.failure_count += 1
            self.last_failure_time = time.time()
            circuit_breaker_failures_total.labels(service=self.name).inc()

            logger.warning(
                f"Circuit breaker {self.name} failure {self.failure_count}/{self.config.failure_threshold}: "
                f"{type(e).__name__}: {str(e)}"
            )

            # Open circuit if threshold reached
            if self.failure_count >= self.config.failure_threshold:
                self.state = CircuitState.OPEN
                self.opened_at = time.time()
                self._update_metrics()
                logger.error(
                    f"Circuit breaker {self.name} opened after {self.failure_count} failures"
                )

            raise

    async def call_async(
        self, func: Callable[..., Awaitable[T]], *args: Any, **kwargs: Any
    ) -> T:
        """
        Execute an async function with circuit breaker protection.

        Args:
            func: Async function to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Result of function call

        Raises:
            Exception: If circuit is open or function fails
        """
        # Check if we should attempt recovery
        if self._should_attempt_reset():
            self.state = CircuitState.HALF_OPEN
            self.success_count = 0
            self._update_metrics()
            logger.info(f"Circuit breaker {self.name} entering HALF_OPEN state")

        # If circuit is open, reject immediately
        if self.state == CircuitState.OPEN:
            raise Exception(
                f"Circuit breaker {self.name} is OPEN. Service is unavailable."
            )

        try:
            result = await func(*args, **kwargs)

            # Success
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self._update_metrics()
                    logger.info(
                        f"Circuit breaker {self.name} recovered, entering CLOSED state"
                    )
            elif self.state == CircuitState.CLOSED:
                # Reset failure count on success
                self.failure_count = 0

            return result

        except self.exceptions as e:
            # Failure
            self.failure_count += 1
            self.last_failure_time = time.time()
            circuit_breaker_failures_total.labels(service=self.name).inc()

            logger.warning(
                f"Circuit breaker {self.name} failure {self.failure_count}/{self.config.failure_threshold}: "
                f"{type(e).__name__}: {str(e)}"
            )

            # Open circuit if threshold reached
            if self.failure_count >= self.config.failure_threshold:
                self.state = CircuitState.OPEN
                self.opened_at = time.time()
                self._update_metrics()
                logger.error(
                    f"Circuit breaker {self.name} opened after {self.failure_count} failures"
                )

            raise

    def get_status(self) -> dict[str, Any]:
        """Get circuit breaker status."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
            "opened_at": self.opened_at,
        }

