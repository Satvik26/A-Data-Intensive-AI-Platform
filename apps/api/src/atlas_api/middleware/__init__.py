"""
Middleware for Atlas API.

Implements cross-cutting concerns:
- Request ID tracking for distributed tracing
- Request timeouts
- Metrics collection
- Error handling
- Load shedding

Reference: DDIA Chapter 1 - Reliability, Scalability
"""

from atlas_api.middleware.reliability import (
    ErrorHandlingMiddleware,
    LoadSheddingMiddleware,
    MetricsMiddleware,
    RequestIDMiddleware,
    TimeoutMiddleware,
)

__all__ = [
    "RequestIDMiddleware",
    "TimeoutMiddleware",
    "MetricsMiddleware",
    "ErrorHandlingMiddleware",
    "LoadSheddingMiddleware",
]

