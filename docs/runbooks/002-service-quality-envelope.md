# Service Quality Envelope Runbook

**Version**: 1.0  
**Last Updated**: 2025-10-26  
**Reference**: DDIA Chapter 1 - Reliable, Scalable, Maintainable Applications

## Overview

This runbook explains how to interpret and act on Service Level Indicators (SLIs) and Service Level Objectives (SLOs) for the Atlas API. It covers monitoring, alerting, and operational responses to system behavior.

**Key Concepts**:
- **SLI**: Measurable metric (latency P95, error rate, throughput)
- **SLO**: Target for that metric (P95 < 200ms, error rate < 1%)
- **Error Budget**: How much the system can fail while still meeting SLO

## SLI/SLO Definitions

### Atlas API SLO (Default)

```
Latency Targets:
  P50:   50ms
  P95:   200ms
  P99:   500ms
  P999:  1000ms

Error Rate Targets:
  Max Error Rate: 1%
  Max 5xx Rate:   0.1%

Throughput Targets:
  Min RPS: 100
  Max RPS: 10,000

Availability Target:
  Min Availability: 99.9% (3 nines)
```

### Critical Endpoints SLO (Auth, Payments)

```
Latency Targets:
  P50:   20ms
  P95:   100ms
  P99:   200ms
  P999:  500ms

Error Rate Targets:
  Max Error Rate: 0.1%
  Max 5xx Rate:   0.01%

Availability Target:
  Min Availability: 99.99% (4 nines)
```

### Non-Critical Endpoints SLO (Analytics, Reports)

```
Latency Targets:
  P50:   100ms
  P95:   500ms
  P99:   2000ms
  P999:  5000ms

Error Rate Targets:
  Max Error Rate: 5%
  Max 5xx Rate:   1%

Availability Target:
  Min Availability: 99% (2 nines)
```

## Monitoring Dashboard

Access the Service Quality Envelope dashboard at:
```
http://localhost:3000/d/atlas-slo
```

### Key Panels

1. **Request Rate (5m)**: Requests per second by endpoint
2. **Latency Percentiles (5m)**: P50, P95, P99 latencies
3. **Error Rate (5m)**: 4xx and 5xx error rates
4. **Concurrent Requests**: In-flight requests
5. **Circuit Breaker State**: Health of external service calls
6. **Retry Attempts (5m)**: Transient failure recovery

## Interpreting Metrics

### Request Rate

**What it measures**: How many requests the system is handling

**Healthy**: Stable, predictable pattern
```
Normal: 100-500 RPS
Peak: Up to 10,000 RPS
```

**Warning Signs**:
- Sudden drop → Service may be down or load shedding
- Sudden spike → Possible DDoS or traffic surge

**Action**:
```bash
# Check if service is healthy
curl http://localhost:8000/health | jq

# Check logs for errors
make logs | grep ERROR

# Check circuit breaker status
curl http://localhost:8000/metrics | grep circuit_breaker_state
```

### Latency Percentiles

**What it measures**: How long requests take to complete

**Healthy**: P95 < 200ms, P99 < 500ms
```
P50:  50ms   (median)
P95:  200ms  (95% of requests faster)
P99:  500ms  (99% of requests faster)
P999: 1000ms (99.9% of requests faster)
```

**Warning Signs**:
- P95 > 200ms → System is slow
- P99 > 500ms → Tail latency is high
- Increasing trend → Degradation over time

**Action**:
```bash
# Check database performance
make db-shell
SELECT * FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;

# Check Redis performance
make redis-cli
INFO stats

# Check for slow queries
curl http://localhost:8000/metrics | grep db_query_duration
```

### Error Rate

**What it measures**: Fraction of requests that fail

**Healthy**: < 1% error rate, < 0.1% 5xx errors
```
4xx Errors: Client errors (bad requests, not found)
5xx Errors: Server errors (bugs, timeouts, overload)
```

**Warning Signs**:
- 5xx rate > 0.1% → Server errors occurring
- 4xx rate > 5% → Many client errors
- Increasing trend → Degradation

**Action**:
```bash
# Check error logs
make logs | grep ERROR | tail -20

# Check specific error types
curl http://localhost:8000/metrics | grep http_errors_total

# Check circuit breaker failures
curl http://localhost:8000/metrics | grep circuit_breaker_failures
```

### Concurrent Requests

**What it measures**: How many requests are in-flight

**Healthy**: < 100 concurrent requests
```
Normal: 10-50
Peak: Up to 100
```

**Warning Signs**:
- Increasing without bound → Requests not completing
- Stuck at max → Load shedding active

**Action**:
```bash
# Check for slow requests
curl http://localhost:8000/metrics | grep http_requests_in_progress

# Check timeout settings
grep HTTP_TIMEOUT apps/api/.env

# Increase timeout if needed
echo "HTTP_TIMEOUT=60" >> apps/api/.env
make restart
```

### Circuit Breaker State

**What it measures**: Health of external service calls

**States**:
- **CLOSED (0)**: Normal operation
- **OPEN (1)**: Service failing, requests rejected
- **HALF_OPEN (2)**: Testing recovery

**Warning Signs**:
- Circuit OPEN → External service is down
- Frequent transitions → Flaky service

**Action**:
```bash
# Check circuit breaker status
curl http://localhost:8000/metrics | grep circuit_breaker_state

# Check failures
curl http://localhost:8000/metrics | grep circuit_breaker_failures

# Manually reset circuit breaker (if needed)
# Edit config and restart
```

### Retry Attempts

**What it measures**: How often transient failures are retried

**Healthy**: Low retry rate (< 1% of requests)
```
Attempt 1: Initial request
Attempt 2: First retry
Attempt 3: Second retry
```

**Warning Signs**:
- High retry rate → Many transient failures
- Increasing trend → Service degradation

**Action**:
```bash
# Check retry configuration
grep RETRY apps/api/.env

# Adjust retry settings if needed
echo "RETRY_MAX_ATTEMPTS=5" >> apps/api/.env
echo "RETRY_MAX_WAIT=30" >> apps/api/.env
make restart
```

## Handling Overload

### Load Shedding

When the system is overloaded, it sheds load by rejecting requests early.

**Symptoms**:
- 429 Too Many Requests responses
- Concurrent requests at max
- Error rate increasing

**Response**:
```bash
# 1. Check current load
curl http://localhost:8000/metrics | grep http_requests_in_progress

# 2. Check load shedding threshold
grep LOAD_SHEDDING apps/api/.env

# 3. Increase threshold if needed
echo "LOAD_SHEDDING_MAX_CONCURRENT=2000" >> apps/api/.env

# 4. Restart service
make restart

# 5. Monitor recovery
watch -n 1 'curl http://localhost:8000/metrics | grep http_requests_in_progress'
```

### Graceful Degradation

When critical services fail, degrade gracefully:

**Strategy**:
1. Fail fast (don't wait for timeouts)
2. Return cached data if available
3. Return partial results
4. Return error with retry-after header

**Implementation**:
```python
from atlas_api.reliability import CircuitBreaker, RetryConfig

# Circuit breaker prevents cascading failures
cb = CircuitBreaker("external-api")

try:
    result = await cb.call_async(call_external_api)
except Exception:
    # Return cached data or partial result
    return get_cached_data()
```

### Graceful Shutdown

When shutting down, complete in-flight requests:

```bash
# Send SIGTERM to gracefully shutdown
kill -TERM <pid>

# Service will:
# 1. Stop accepting new requests
# 2. Complete in-flight requests (with timeout)
# 3. Close database connections
# 4. Flush metrics and traces
# 5. Exit cleanly
```

## Error Budget

**Error Budget**: How much the system can fail while still meeting SLO

**Calculation**:
```
Error Budget = (1 - SLO) * Time Period

Example (99.9% SLO, 30 days):
Error Budget = (1 - 0.999) * 30 days * 86400 seconds
            = 0.001 * 2,592,000 seconds
            = 2,592 seconds
            = 43.2 minutes of downtime allowed
```

**Usage**:
- Track error budget consumption
- Use budget for deployments, experiments
- When budget exhausted, focus on reliability
- When budget available, can take risks

**Monitoring**:
```bash
# Check error budget consumption
curl http://localhost:8000/metrics | grep error_budget

# Alert when budget < 10%
# Alert when budget exhausted
```

## Troubleshooting

### High Latency

**Symptoms**: P95 > 200ms

**Diagnosis**:
```bash
# 1. Check database performance
make db-shell
SELECT * FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;

# 2. Check slow queries
EXPLAIN ANALYZE SELECT ...;

# 3. Check indexes
SELECT * FROM pg_stat_user_indexes;

# 4. Check connection pool
SELECT count(*) FROM pg_stat_activity;
```

**Solutions**:
- Add database indexes
- Optimize slow queries
- Increase connection pool size
- Add caching layer

### High Error Rate

**Symptoms**: Error rate > 1%

**Diagnosis**:
```bash
# 1. Check error logs
make logs | grep ERROR | tail -50

# 2. Check error types
curl http://localhost:8000/metrics | grep http_errors_total

# 3. Check circuit breaker
curl http://localhost:8000/metrics | grep circuit_breaker

# 4. Check external services
curl http://external-service/health
```

**Solutions**:
- Fix bugs causing errors
- Increase timeouts
- Improve retry logic
- Add circuit breaker
- Scale up resources

### High Concurrent Requests

**Symptoms**: Concurrent requests increasing

**Diagnosis**:
```bash
# 1. Check request rate
curl http://localhost:8000/metrics | grep http_requests_total

# 2. Check request duration
curl http://localhost:8000/metrics | grep http_request_duration

# 3. Check for stuck requests
make logs | grep "in progress"
```

**Solutions**:
- Increase timeout to fail fast
- Add load balancer
- Scale horizontally
- Optimize request handling
- Add caching

## Alerts

Recommended alert thresholds:

```yaml
# Latency alerts
- alert: HighLatencyP95
  expr: histogram_quantile(0.95, rate(atlas_api_http_request_duration_seconds_bucket[5m])) > 0.2
  for: 5m

# Error rate alerts
- alert: HighErrorRate
  expr: rate(atlas_api_http_requests_total{status=~"5.."}[5m]) > 0.001
  for: 5m

# Circuit breaker alerts
- alert: CircuitBreakerOpen
  expr: atlas_api_circuit_breaker_state == 1
  for: 1m

# Availability alerts
- alert: ServiceDown
  expr: up{job="atlas-api"} == 0
  for: 1m
```

## References

- DDIA Chapter 1: Reliable, Scalable, Maintainable Applications
- [Google SRE Book - SLOs](https://sre.google/sre-book/service-level-objectives/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/instrumentation/)
- [Grafana Documentation](https://grafana.com/docs/)

## Support

For issues or questions:
1. Check this runbook
2. Review logs: `make logs`
3. Check metrics: `curl http://localhost:8000/metrics`
4. Check health: `curl http://localhost:8000/health | jq`
5. Contact on-call engineer

