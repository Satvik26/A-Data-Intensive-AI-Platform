"""
Prometheus metrics instrumentation.

Implements RED (Rate, Errors, Duration) metrics and custom business metrics.
Follows DDIA Chapter 1 principles for monitoring system health.
"""

from prometheus_client import Counter, Gauge, Histogram, Info

# Application info
app_info = Info("atlas_api", "Application information")

# HTTP metrics (RED method)
# DDIA Chapter 1: RED metrics (Rate, Errors, Duration) are essential for monitoring
http_requests_total = Counter(
    "atlas_api_http_requests_total",
    "Total HTTP requests (Rate)",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "atlas_api_http_request_duration_seconds",
    "HTTP request duration in seconds (Duration)",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

http_requests_in_progress = Gauge(
    "atlas_api_http_requests_in_progress",
    "HTTP requests currently in progress",
    ["method", "endpoint"],
)

# Error metrics by route
http_errors_total = Counter(
    "atlas_api_http_errors_total",
    "Total HTTP errors by route (Errors)",
    ["method", "endpoint", "status_code"],
)

http_5xx_errors_total = Counter(
    "atlas_api_http_5xx_errors_total",
    "Total 5xx server errors",
    ["method", "endpoint"],
)

http_4xx_errors_total = Counter(
    "atlas_api_http_4xx_errors_total",
    "Total 4xx client errors",
    ["method", "endpoint"],
)

# Database metrics
db_connections_total = Gauge(
    "atlas_api_db_connections_total",
    "Total database connections",
    ["state"],  # active, idle
)

db_query_duration_seconds = Histogram(
    "atlas_api_db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
)

db_errors_total = Counter(
    "atlas_api_db_errors_total",
    "Total database errors",
    ["operation", "error_type"],
)

# Cache metrics
cache_operations_total = Counter(
    "atlas_api_cache_operations_total",
    "Total cache operations",
    ["operation", "status"],  # operation: get/set/delete, status: hit/miss/error
)

cache_hit_ratio = Gauge(
    "atlas_api_cache_hit_ratio",
    "Cache hit ratio (0-1)",
)

# Kafka metrics
kafka_messages_produced_total = Counter(
    "atlas_api_kafka_messages_produced_total",
    "Total Kafka messages produced",
    ["topic", "status"],  # status: success/error
)

kafka_messages_consumed_total = Counter(
    "atlas_api_kafka_messages_consumed_total",
    "Total Kafka messages consumed",
    ["topic", "consumer_group"],
)

kafka_consumer_lag = Gauge(
    "atlas_api_kafka_consumer_lag",
    "Kafka consumer lag",
    ["topic", "partition", "consumer_group"],
)

# Circuit breaker metrics
circuit_breaker_state = Gauge(
    "atlas_api_circuit_breaker_state",
    "Circuit breaker state (0=closed, 1=open, 2=half-open)",
    ["service"],
)

circuit_breaker_failures_total = Counter(
    "atlas_api_circuit_breaker_failures_total",
    "Total circuit breaker failures",
    ["service"],
)

# Retry metrics
retry_attempts_total = Counter(
    "atlas_api_retry_attempts_total",
    "Total retry attempts",
    ["operation", "attempt"],
)

# Business metrics (examples)
users_created_total = Counter(
    "atlas_api_users_created_total",
    "Total users created",
)

events_processed_total = Counter(
    "atlas_api_events_processed_total",
    "Total events processed",
    ["event_type", "status"],
)

# System metrics
system_health_status = Gauge(
    "atlas_api_system_health_status",
    "System health status (1=healthy, 0=unhealthy)",
    ["component"],
)


def setup_metrics() -> None:
    """
    Initialize metrics with default values.

    Sets up application info and default metric values.
    """
    app_info.info(
        {
            "version": "0.1.0",
            "environment": "development",
        }
    )

    # Initialize health status for all components
    for component in ["api", "database", "redis", "kafka", "minio"]:
        system_health_status.labels(component=component).set(0)

