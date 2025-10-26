# Atlas API

> Production-grade FastAPI service demonstrating DDIA principles

## Overview

Atlas API is the core backend service of the Atlas platform, implementing reliability, scalability, and maintainability patterns from "Designing Data-Intensive Applications" (DDIA).

## Features

### Reliability Patterns
- ✅ **Idempotency**: All write operations support idempotency keys
- ✅ **Retries**: Exponential backoff with jitter for transient failures
- ✅ **Circuit Breakers**: Prevent cascade failures
- ✅ **Timeouts**: Explicit timeouts on all external calls
- ✅ **Backpressure**: Rate limiting and queue depth monitoring
- ✅ **Outbox Pattern**: Reliable event publishing

### Observability
- 📊 **Metrics**: Prometheus metrics (RED method + business metrics)
- 🔍 **Tracing**: OpenTelemetry distributed tracing
- 📝 **Logging**: Structured JSON logging with correlation IDs
- 🏥 **Health Checks**: Liveness, readiness, and dependency health

### Architecture
- 🏗️ **Clean Architecture**: Clear separation of concerns
- 🎯 **Domain-Driven Design**: Rich domain models
- 🔌 **Dependency Injection**: FastAPI's DI system
- 📦 **Repository Pattern**: Data access abstraction

## Quick Start

### Prerequisites

- Python 3.11+
- Poetry
- Docker & Docker Compose

### Installation

```bash
# Install dependencies
poetry install

# Copy environment file
cp .env.sample .env

# Start infrastructure services
make up

# Run migrations
make migrate

# Start API
make run
```

### Verify Installation

```bash
# Check health
curl http://localhost:8000/health

# View API docs
open http://localhost:8000/docs

# View metrics
curl http://localhost:8000/metrics
```

## Development

### Project Structure

```
apps/api/
├── src/atlas_api/
│   ├── adapters/          # External service clients
│   ├── domain/            # Business entities
│   ├── repositories/      # Data access layer
│   ├── services/          # Business logic
│   ├── routers/           # API endpoints
│   ├── schemas/           # Pydantic models
│   ├── workers/           # Background jobs
│   ├── instrumentation/   # Observability
│   ├── utils/             # Shared utilities
│   ├── config.py          # Configuration
│   └── main.py            # Application entry point
├── tests/
│   ├── unit/              # Unit tests
│   └── integration/       # Integration tests
├── alembic/               # Database migrations
├── config/                # Service configurations
└── scripts/               # Utility scripts
```

### Common Commands

```bash
# Development
make run              # Run API locally
make shell            # Enter container shell
make logs             # View logs

# Code Quality
make lint             # Run linter
make fmt              # Format code
make type             # Type check
make check            # Run all checks

# Testing
make test             # Run all tests
make test-unit        # Unit tests only
make test-integration # Integration tests only
make test-cov         # With coverage

# Database
make migrate          # Run migrations
make migration MSG="description"  # Create migration
make seed             # Seed data
make db-reset         # Reset database

# Monitoring
make grafana          # Open Grafana
make prometheus       # Open Prometheus
make metrics          # View metrics
```

### Running Tests

```bash
# All tests
make test

# Specific test file
pytest tests/unit/test_health.py -v

# With coverage
make test-cov

# Watch mode
make test-watch
```

### Code Quality

The project uses:
- **Ruff**: Fast Python linter
- **Black**: Code formatter
- **MyPy**: Static type checker
- **Pre-commit**: Git hooks

```bash
# Run all checks
make check

# Install pre-commit hooks
make pre-commit-install

# Run pre-commit manually
make pre-commit
```

## API Documentation

### Interactive Docs

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Key Endpoints

#### Health Checks

```bash
# Comprehensive health check
GET /health

# Readiness probe (K8s)
GET /health/ready

# Liveness probe (K8s)
GET /health/live
```

#### Metrics

```bash
# Prometheus metrics
GET /metrics
```

## Configuration

Configuration is managed through environment variables and `.env` file.

### Key Settings

```bash
# Application
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql+asyncpg://atlas:atlas_dev@localhost:5432/atlas_dev

# Redis
REDIS_URL=redis://localhost:6379/0

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# MinIO
MINIO_ENDPOINT=localhost:9000
```

See `.env.sample` for all available settings.

## Database Migrations

### Create Migration

```bash
# Auto-generate from model changes
make migration MSG="add users table"

# Manual migration
poetry run alembic revision -m "custom migration"
```

### Apply Migrations

```bash
# Upgrade to latest
make migrate

# Downgrade one version
make migrate-down

# View history
make migration-history
```

## Observability

### Metrics

Prometheus metrics available at `/metrics`:

- **HTTP metrics**: Request rate, latency, errors (RED)
- **Database metrics**: Connection pool, query duration
- **Cache metrics**: Hit rate, operations
- **Kafka metrics**: Messages produced/consumed, lag
- **Business metrics**: Domain-specific metrics

### Dashboards

Pre-configured Grafana dashboards:

- System Overview
- API Performance
- Database Metrics
- Kafka Metrics

Access: http://localhost:3000 (admin/admin)

### Logs

Structured JSON logs with:
- Correlation IDs
- Request context
- Error stack traces
- Performance metrics

## Testing Strategy

### Unit Tests

Fast, isolated tests for business logic:

```python
def test_user_creation_validates_email():
    """Test that user creation validates email format."""
    # Arrange
    invalid_email = "not-an-email"

    # Act & Assert
    with pytest.raises(ValidationError):
        User(email=invalid_email)
```

### Integration Tests

Test interactions with real dependencies:

```python
async def test_user_repository_saves_to_database(db_session):
    """Test that user repository persists to database."""
    # Arrange
    repo = UserRepository(db_session)
    user = User(email="test@example.com")

    # Act
    saved_user = await repo.save(user)

    # Assert
    assert saved_user.id is not None
```

## Deployment

### Docker

```bash
# Build image
make build

# Run with Docker Compose
make up
```

### Kubernetes (Optional)

```bash
# Apply manifests
kubectl apply -f ../../deploy/k8s/

# Check status
kubectl get pods -n atlas
```

## Troubleshooting

### Common Issues

**Database connection errors**
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# View logs
docker-compose logs postgres

# Reset database
make db-reset
```

**Import errors**
```bash
# Reinstall dependencies
poetry install

# Clear cache
make clean
```

**Test failures**
```bash
# Run with verbose output
pytest -vv

# Run specific test
pytest tests/unit/test_health.py::test_health_check_returns_200 -v
```

## Contributing

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes with tests
3. Run quality checks: `make check`
4. Commit: `git commit -m "feat: add new feature"`
5. Push and create PR

## License

MIT License - See LICENSE file for details

---

**Documentation**: [docs/](../../docs/) | **Issues**: GitHub Issues | **Version**: 0.1.0

