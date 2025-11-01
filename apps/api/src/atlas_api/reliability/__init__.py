"""
Reliability module for Atlas API.

Implements DDIA Chapter 1 patterns for building reliable systems:
- SLI/SLO definitions and monitoring
- Retry logic with exponential backoff and jitter
- Circuit breaker pattern
- Timeout management
- Error handling

Reference: DDIA Chapter 1 - Reliable, Scalable, Maintainable Applications
"""

from atlas_api.reliability.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
)
from atlas_api.reliability.retry import RetryConfig, retry_async, retry_sync
from atlas_api.reliability.slo import (
    ATLAS_API_SLO,
    CRITICAL_ENDPOINT_SLO,
    NON_CRITICAL_ENDPOINT_SLO,
    AvailabilitySLI,
    ErrorRateSLI,
    LatencySLI,
    SLIType,
    ServiceLevelObjective,
    ThroughputSLI,
    format_slo_summary,
    get_slo_for_endpoint,
)

__all__ = [
    # SLO/SLI
    "SLIType",
    "LatencySLI",
    "ErrorRateSLI",
    "ThroughputSLI",
    "AvailabilitySLI",
    "ServiceLevelObjective",
    "ATLAS_API_SLO",
    "CRITICAL_ENDPOINT_SLO",
    "NON_CRITICAL_ENDPOINT_SLO",
    "get_slo_for_endpoint",
    "format_slo_summary",
    # Retry
    "RetryConfig",
    "retry_sync",
    "retry_async",
    # Circuit Breaker
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitState",
]

