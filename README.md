# Atlas Platform

> **Production-grade, DDIA-aligned data-intensive application platform**

Atlas is a comprehensive reference implementation demonstrating all major concepts from "Designing Data-Intensive Applications" (DDIA) through a real-world FastAPI backend with ML serving, event-driven architecture, and enterprise-grade reliability patterns.

## 🎯 Mission

Bridge DDIA theory to production practice with:
- **Reliability:** Idempotency, circuit breakers, retries with exponential backoff + jitter, backpressure, outbox pattern
- **Scalability:** Horizontal scaling, partitioning, replication, caching strategies
- **Maintainability:** Clean architecture, typed code, comprehensive tests, clear documentation
- **Observability:** Metrics, traces, structured logs, dashboards, alerts

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                          │
│                    (CLI, Web UI, SDKs)                       │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                     FastAPI Service                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Routers  │─▶│ Services │─▶│  Repos   │─▶│ Adapters │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│       │              │              │              │        │
│       └──────────────┴──────────────┴──────────────┘        │
│                    Instrumentation                           │
│            (Metrics, Traces, Structured Logs)               │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┬──────────────┐
        │                │                │              │
┌───────▼──────┐  ┌─────▼─────┐  ┌──────▼──────┐  ┌────▼─────┐
│  PostgreSQL  │  │   Redis   │  │    Kafka    │  │  MinIO   │
│ (Primary DB) │  │  (Cache)  │  │  (Events)   │  │   (S3)   │
└──────────────┘  └───────────┘  └─────────────┘  └──────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose (v2.0+)
- Python 3.11+
- Make

### Initial Setup

```bash
# Clone and enter directory
cd atlas

# Start all infrastructure services
make up

# Run database migrations
make migrate

# Seed initial data
make seed

# Run the application
make run

# In another terminal, run tests
make test

# Access services:
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Grafana: http://localhost:3000 (admin/admin)
# - Prometheus: http://localhost:9090
```

## 📦 Stack

### Core
- **Python 3.11** - Modern Python with performance improvements
- **FastAPI** - High-performance async web framework
- **Pydantic v2** - Data validation with Rust-powered performance
- **SQLAlchemy 2.0** - Modern ORM with async support
- **Alembic** - Database migration tool

### Data Stores
- **PostgreSQL 15** - Primary relational database
- **Redis 7** - Caching and session store
- **Apache Kafka** - Event streaming platform
- **MinIO** - S3-compatible object storage

### Observability
- **Prometheus** - Metrics collection and alerting
- **Grafana** - Visualization and dashboards
- **OpenTelemetry** - Distributed tracing and telemetry

### Development
- **PyTest** - Testing framework
- **Coverage.py** - Code coverage
- **Ruff** - Fast Python linter
- **Black** - Code formatter
- **MyPy** - Static type checker
- **pre-commit** - Git hooks framework

## 📁 Project Structure

```
atlas/
├── apps/
│   └── api/                    # FastAPI service
│       ├── src/
│       │   └── atlas_api/
│       │       ├── adapters/   # External service clients
│       │       ├── domain/     # Business entities
│       │       ├── repositories/ # Data access layer
│       │       ├── services/   # Business logic
│       │       ├── routers/    # API endpoints
│       │       ├── schemas/    # Pydantic models
│       │       ├── workers/    # Background jobs
│       │       ├── instrumentation/ # Observability
│       │       └── utils/      # Shared utilities
│       ├── tests/
│       │   ├── unit/
│       │   └── integration/
│       ├── alembic/            # Database migrations
│       └── docker-compose.yml
├── data/                       # Seeds and fixtures
├── deploy/                     # Deployment configs
│   ├── grafana/
│   └── k8s/
├── docs/
│   ├── ADRs/                   # Architecture Decision Records
│   ├── runbooks/               # Operational guides
│   ├── architecture/           # System design docs
│   └── api/                    # API documentation
└── README.md
```

## 🛠️ Development

### Common Commands

```bash
# Development
make up              # Start all services
make down            # Stop all services
make logs            # View logs
make shell           # Enter API container shell

# Code Quality
make lint            # Run linter (Ruff)
make fmt             # Format code (Black)
make type            # Type check (MyPy)
make test            # Run tests
make test-cov        # Run tests with coverage
make pre-commit      # Run all pre-commit hooks

# Database
make migrate         # Run migrations
make migration       # Create new migration
make seed            # Seed database
make db-shell        # PostgreSQL shell

# Monitoring
make grafana         # Open Grafana dashboard
make prometheus      # Open Prometheus UI
make metrics         # View current metrics
```

### Running Tests

```bash
# All tests
make test

# Unit tests only
make test-unit

# Integration tests only
make test-integration

# With coverage report
make test-cov

# Specific test file
pytest apps/api/tests/unit/test_health.py -v
```

## 📊 Observability

### Metrics
- **Application metrics:** Request rate, latency, error rate (RED method)
- **Business metrics:** Custom domain-specific metrics
- **Infrastructure metrics:** Database connections, cache hit rate, queue depth

### Traces
- Distributed tracing with OpenTelemetry
- Request correlation across services
- Performance bottleneck identification

### Logs
- Structured JSON logging
- Correlation IDs for request tracking
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

### Dashboards
- Pre-configured Grafana dashboards in `deploy/grafana/dashboards/`
- System overview, API performance, database metrics, Kafka metrics

## 🔒 Reliability Patterns

Atlas implements DDIA-aligned reliability patterns:

- **Idempotency:** All write operations use idempotency keys
- **Retries:** Exponential backoff with jitter for transient failures
- **Circuit Breakers:** Prevent cascade failures
- **Timeouts:** Explicit timeouts on all external calls
- **Backpressure:** Rate limiting and queue depth monitoring
- **Outbox Pattern:** Reliable event publishing with transactional guarantees
- **Health Checks:** Liveness and readiness probes
- **Graceful Shutdown:** Clean resource cleanup on termination

## 📚 Documentation

- **[Architecture Decision Records](docs/ADRs/)** - Key design decisions and rationale
- **[Runbooks](docs/runbooks/)** - Operational procedures
- **[API Documentation](http://localhost:8000/docs)** - Interactive OpenAPI docs
- **[Architecture Diagrams](docs/architecture/)** - System design and data flows

## 🧪 Testing Strategy

- **Unit Tests:** Fast, isolated tests for business logic
- **Integration Tests:** Test interactions with real dependencies
- **Contract Tests:** Validate API contracts and schema evolution
- **Load Tests:** Performance and scalability validation
- **Chaos Tests:** Resilience under failure conditions

## 🚢 Deployment

### Docker Compose (Development/Staging)
```bash
make up
```

### Kubernetes (Production - Optional)
```bash
kubectl apply -f deploy/k8s/
```

## 🤝 Contributing

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes with tests
3. Run quality checks: `make lint fmt type test`
4. Commit with semantic message: `feat: add new capability`
5. Push and create PR

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

Built on principles from "Designing Data-Intensive Applications" by Martin Kleppmann.

---

**Status:** 🟢 Active Development | **Version:** 0.1.0 | **Last Updated:** 2025-10-26

