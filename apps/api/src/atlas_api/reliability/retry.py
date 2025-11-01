"""
Retry logic with exponential backoff and jitter.

Implements DDIA Chapter 1 principles for handling transient failures.
Exponential backoff prevents overwhelming a struggling service.
Jitter prevents thundering herd problem.

Reference: DDIA Chapter 1 - Reliability
"""

import asyncio
import logging
import random
import time
from functools import wraps
from typing import Any, Awaitable, Callable, Optional, TypeVar

from atlas_api.instrumentation.metrics import retry_attempts_total

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetryConfig:
    """Configuration for retry behavior.

    DDIA Chapter 1: Retry strategies must be carefully designed to avoid
    making things worse. Exponential backoff with jitter is the standard approach.
    """

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay_ms: int = 100,
        max_delay_ms: int = 10000,
        multiplier: float = 2.0,
        jitter: bool = True,
    ):
        """
        Initialize retry configuration.

        Args:
            max_attempts: Maximum number of attempts (including initial)
            base_delay_ms: Initial delay in milliseconds
            max_delay_ms: Maximum delay in milliseconds
            multiplier: Exponential backoff multiplier
            jitter: Whether to add random jitter to delays
        """
        if max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        if base_delay_ms < 0:
            raise ValueError("base_delay_ms must be >= 0")
        if max_delay_ms < base_delay_ms:
            raise ValueError("max_delay_ms must be >= base_delay_ms")
        if multiplier < 1.0:
            raise ValueError("multiplier must be >= 1.0")

        self.max_attempts = max_attempts
        self.base_delay_ms = base_delay_ms
        self.max_delay_ms = max_delay_ms
        self.multiplier = multiplier
        self.jitter = jitter

    def calculate_delay_ms(self, attempt: int) -> int:
        """
        Calculate delay for a given attempt number.

        Uses exponential backoff: delay = base_delay * (multiplier ^ attempt)
        Capped at max_delay_ms.
        If jitter is enabled, adds random jitter: delay * (0.5 to 1.5)

        Args:
            attempt: Attempt number (0-indexed)

        Returns:
            int: Delay in milliseconds
        """
        # Exponential backoff
        delay = self.base_delay_ms * (self.multiplier ** attempt)
        delay = min(delay, self.max_delay_ms)

        # Add jitter to prevent thundering herd
        if self.jitter:
            jitter_factor = random.uniform(0.5, 1.5)
            delay = delay * jitter_factor

        return int(delay)


def retry_sync(
    config: Optional[RetryConfig] = None,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[int, Exception], None]] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for synchronous functions with retry logic.

    DDIA Chapter 1: Retries are essential for handling transient failures.
    This decorator implements exponential backoff with jitter.

    Args:
        config: RetryConfig instance (uses defaults if None)
        exceptions: Tuple of exception types to retry on
        on_retry: Optional callback called on each retry

    Returns:
        Decorator function

    Example:
        @retry_sync(config=RetryConfig(max_attempts=3))
        def call_external_api():
            return requests.get("https://api.example.com")
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Optional[Exception] = None

            for attempt in range(config.max_attempts):
                try:
                    result = func(*args, **kwargs)
                    if attempt > 0:
                        logger.info(
                            f"Retry succeeded for {func.__name__} on attempt {attempt + 1}"
                        )
                    return result
                except exceptions as e:
                    last_exception = e
                    retry_attempts_total.labels(
                        operation=func.__name__, attempt=attempt + 1
                    ).inc()

                    if attempt < config.max_attempts - 1:
                        delay_ms = config.calculate_delay_ms(attempt)
                        logger.warning(
                            f"Retry {attempt + 1}/{config.max_attempts} for {func.__name__}: "
                            f"{type(e).__name__}: {str(e)}. "
                            f"Waiting {delay_ms}ms before retry."
                        )

                        if on_retry:
                            on_retry(attempt + 1, e)

                        time.sleep(delay_ms / 1000.0)
                    else:
                        logger.error(
                            f"All {config.max_attempts} retry attempts failed for {func.__name__}: "
                            f"{type(e).__name__}: {str(e)}"
                        )

            raise last_exception or Exception(f"Failed after {config.max_attempts} attempts")

        return wrapper

    return decorator


def retry_async(
    config: Optional[RetryConfig] = None,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[int, Exception], Awaitable[None]]] = None,
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """
    Decorator for async functions with retry logic.

    DDIA Chapter 1: Async retry logic is critical for high-concurrency systems.
    Uses asyncio.sleep instead of time.sleep.

    Args:
        config: RetryConfig instance (uses defaults if None)
        exceptions: Tuple of exception types to retry on
        on_retry: Optional async callback called on each retry

    Returns:
        Decorator function

    Example:
        @retry_async(config=RetryConfig(max_attempts=3))
        async def call_external_api():
            return await httpx.get("https://api.example.com")
    """
    if config is None:
        config = RetryConfig()

    def decorator(
        func: Callable[..., Awaitable[T]],
    ) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Optional[Exception] = None

            for attempt in range(config.max_attempts):
                try:
                    result = await func(*args, **kwargs)
                    if attempt > 0:
                        logger.info(
                            f"Retry succeeded for {func.__name__} on attempt {attempt + 1}"
                        )
                    return result
                except exceptions as e:
                    last_exception = e
                    retry_attempts_total.labels(
                        operation=func.__name__, attempt=attempt + 1
                    ).inc()

                    if attempt < config.max_attempts - 1:
                        delay_ms = config.calculate_delay_ms(attempt)
                        logger.warning(
                            f"Retry {attempt + 1}/{config.max_attempts} for {func.__name__}: "
                            f"{type(e).__name__}: {str(e)}. "
                            f"Waiting {delay_ms}ms before retry."
                        )

                        if on_retry:
                            await on_retry(attempt + 1, e)

                        await asyncio.sleep(delay_ms / 1000.0)
                    else:
                        logger.error(
                            f"All {config.max_attempts} retry attempts failed for {func.__name__}: "
                            f"{type(e).__name__}: {str(e)}"
                        )

            raise last_exception or Exception(f"Failed after {config.max_attempts} attempts")

        return wrapper

    return decorator

