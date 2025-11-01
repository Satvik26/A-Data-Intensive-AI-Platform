# Reliability Endpoints API

**Service Quality Envelope - Health & Metrics Endpoints**

---

## Overview

The Atlas API exposes health check and metrics endpoints for monitoring reliability and SLI/SLO compliance.

---

## Endpoints

### 1. Health Check

**Endpoint**: `GET /health`

**Purpose**: Check API health status

**Response** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2025-10-26T12:34:56Z",
  "version": "0.1.0",
  "environment": "production",
  "checks": {
    "database": "healthy",
    "redis": "healthy",
    "kafka": "healthy"
  }
}
```

**Response** (503 Service Unavailable):
```json
{
  "status": "unhealthy",
  "timestamp": "2025-10-26T12:34:56Z",
  "checks": {
    "database": "unhealthy",
    "redis": "healthy",
    "kafka": "healthy"
  }
}
```

**Headers**:
- `X-Request-ID`: Unique request identifier for tracing

---

### 2. Prometheus Metrics

**Endpoint**: `GET /metrics`

**Purpose**: Expose Prometheus metrics for scraping

**Response** (200 OK):
```
# HELP atlas_api_http_requests_total Total HTTP requests
# TYPE atlas_api_http_requests_total counter
atlas_api_http_requests_total{method="GET",endpoint="/health",status="200"} 1234

# HELP atlas_api_http_request_duration_seconds HTTP request duration
# TYPE atlas_api_http_request_duration_seconds histogram
atlas_api_http_request_duration_seconds_bucket{method="GET",endpoint="/health",le="0.05"} 1000
atlas_api_http_request_duration_seconds_bucket{method="GET",endpoint="/health",le="0.1"} 1100
atlas_api_http_request_duration_seconds_bucket{method="GET",endpoint="/health",le="0.25"} 1150
atlas_api_http_request_duration_seconds_bucket{method="GET",endpoint="/health",le="0.5"} 1200
atlas_api_http_request_duration_seconds_bucket{method="GET",endpoint="/health",le="1.0"} 1230
atlas_api_http_request_duration_seconds_bucket{method="GET",endpoint="/health",le="+Inf"} 1234
atlas_api_http_request_duration_seconds_sum{method="GET",endpoint="/health"} 123.45
atlas_api_http_request_duration_seconds_count{method="GET",endpoint="/health"} 1234

# HELP atlas_api_http_errors_total Total HTTP errors
# TYPE atlas_api_http_errors_total counter
atlas_api_http_errors_total{method="GET",endpoint="/health",status_code="500"} 5

# HELP atlas_api_circuit_breaker_state Circuit breaker state
# TYPE atlas_api_circuit_breaker_state gauge
atlas_api_circuit_breaker_state{service="payment-service"} 0

# HELP atlas_api_retry_attempts_total Total retry attempts
# TYPE atlas_api_retry_attempts_total counter
atlas_api_retry_attempts_total{operation="call_external_api"} 42
```

**Metrics Exposed**:
- `atlas_api_http_requests_total` - Request count by method/endpoint/status
- `atlas_api_http_request_duration_seconds` - Latency histogram with percentile buckets
- `atlas_api_http_errors_total` - Error count by route and status code
- `atlas_api_http_5xx_errors_total` - Server errors
- `atlas_api_http_4xx_errors_total` - Client errors
- `atlas_api_http_requests_in_progress` - Concurrent requests
- `atlas_api_circuit_breaker_state` - Circuit breaker state (0=closed, 1=open, 2=half-open)
- `atlas_api_circuit_breaker_failures_total` - Failures per service
- `atlas_api_retry_attempts_total` - Retry attempts by operation

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid request parameter",
  "request_id": "abc-123-def",
  "timestamp": "2025-10-26T12:34:56Z"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found",
  "request_id": "abc-123-def",
  "timestamp": "2025-10-26T12:34:56Z"
}
```

### 429 Too Many Requests (Load Shedding)
```json
{
  "detail": "Service overloaded, please retry later",
  "request_id": "abc-123-def",
  "timestamp": "2025-10-26T12:34:56Z",
  "retry_after": 60
}
```

**Headers**:
- `Retry-After`: Seconds to wait before retrying

### 504 Gateway Timeout
```json
{
  "detail": "Request timeout, please retry",
  "request_id": "abc-123-def",
  "timestamp": "2025-10-26T12:34:56Z"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error",
  "request_id": "abc-123-def",
  "timestamp": "2025-10-26T12:34:56Z",
  "error_code": "INTERNAL_ERROR"
}
```

---

## Response Headers

All responses include:

| Header | Purpose |
|--------|---------|
| `X-Request-ID` | Unique request identifier for distributed tracing |
| `X-RateLimit-Limit` | Rate limit (future) |
| `X-RateLimit-Remaining` | Remaining requests (future) |
| `X-RateLimit-Reset` | Rate limit reset time (future) |

---

## Request Headers

Clients should include:

| Header | Purpose | Example |
|--------|---------|---------|
| `X-Request-ID` | Request identifier (optional, generated if missing) | `abc-123-def` |
| `User-Agent` | Client identifier | `curl/7.64.1` |
| `Accept` | Response format | `application/json` |

---

## Examples

### Health Check
```bash
curl -v http://localhost:8000/health

# Response
HTTP/1.1 200 OK
X-Request-ID: abc-123-def
Content-Type: application/json

{
  "status": "healthy",
  "timestamp": "2025-10-26T12:34:56Z",
  "version": "0.1.0",
  "environment": "production",
  "checks": {
    "database": "healthy",
    "redis": "healthy",
    "kafka": "healthy"
  }
}
```

### Metrics Collection
```bash
curl http://localhost:8000/metrics | head -20

# Response
# HELP atlas_api_http_requests_total Total HTTP requests
# TYPE atlas_api_http_requests_total counter
atlas_api_http_requests_total{method="GET",endpoint="/health",status="200"} 1234
...
```

### Load Shedding Response
```bash
# When system is overloaded
curl -v http://localhost:8000/api/v1/users

# Response
HTTP/1.1 429 Too Many Requests
X-Request-ID: abc-123-def
Retry-After: 60
Content-Type: application/json

{
  "detail": "Service overloaded, please retry later",
  "request_id": "abc-123-def",
  "timestamp": "2025-10-26T12:34:56Z",
  "retry_after": 60
}
```

### Timeout Response
```bash
# When request exceeds HTTP_TIMEOUT
curl -v http://localhost:8000/api/v1/slow-endpoint

# Response
HTTP/1.1 504 Gateway Timeout
X-Request-ID: abc-123-def
Content-Type: application/json

{
  "detail": "Request timeout, please retry",
  "request_id": "abc-123-def",
  "timestamp": "2025-10-26T12:34:56Z"
}
```

---

## Monitoring

### Prometheus Scrape Configuration
```yaml
scrape_configs:
  - job_name: 'atlas-api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
    scrape_timeout: 10s
```

### Grafana Dashboard
Access at: `http://localhost:3000/d/atlas-slo`

Panels:
- Request Rate (5m)
- Latency Percentiles (P50, P95, P99)
- Error Rate (4xx, 5xx)
- Concurrent Requests
- Circuit Breaker State
- Retry Attempts

---

## SLI/SLO Targets

### Default (Atlas API)
```
Latency:  P50=50ms, P95=200ms, P99=500ms, P999=1000ms
Errors:   Max 1% error rate, Max 0.1% 5xx
RPS:      Min 100, Max 10,000
Uptime:   99.9% (3 nines)
```

### Critical (Auth, Payments)
```
Latency:  P50=20ms, P95=100ms, P99=200ms, P999=500ms
Errors:   Max 0.1% error rate, Max 0.01% 5xx
Uptime:   99.99% (4 nines)
```

### Non-Critical (Analytics, Reports)
```
Latency:  P50=100ms, P95=500ms, P99=2000ms, P999=5000ms
Errors:   Max 5% error rate, Max 1% 5xx
Uptime:   99% (2 nines)
```

---

## Rate Limiting (Future)

Currently not implemented. Future versions will include:
- Per-client rate limits
- Adaptive rate limiting based on load
- X-RateLimit-* headers

---

## Versioning

Current API version: `v1`

Future versions will be available at:
- `/api/v2/...`
- `/api/v3/...`

---

**Version**: 1.0  
**Last Updated**: 2025-10-26

