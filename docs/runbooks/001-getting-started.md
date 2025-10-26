# Runbook: Getting Started with Atlas

**Purpose**: Guide for setting up and running Atlas platform locally  
**Audience**: Developers, DevOps  
**Last Updated**: 2025-10-26

## Prerequisites

### Required Software

- **Docker Desktop** (v20.10+)
  - Download: https://www.docker.com/products/docker-desktop
  - Verify: `docker --version && docker-compose --version`

- **Python** (3.11+)
  - Download: https://www.python.org/downloads/
  - Verify: `python --version`

- **Poetry** (1.7+)
  - Install: `curl -sSL https://install.python-poetry.org | python3 -`
  - Verify: `poetry --version`

- **Make** (usually pre-installed on macOS/Linux)
  - Verify: `make --version`

### System Requirements

- **RAM**: 8GB minimum, 16GB recommended
- **Disk**: 10GB free space
- **CPU**: 4 cores recommended

## Installation Steps

### 1. Clone Repository

```bash
git clone <repository-url>
cd atlas
```

### 2. Configure Environment

```bash
cd apps/api

# Copy sample environment file
cp .env.sample .env

# Edit .env if needed (defaults work for local development)
# vim .env
```

### 3. Install Dependencies

```bash
# Install Python dependencies
poetry install

# Install pre-commit hooks
poetry run pre-commit install
```

### 4. Start Infrastructure Services

```bash
# Start all services (PostgreSQL, Redis, Kafka, MinIO, Prometheus, Grafana)
make up

# Wait for services to be healthy (30-60 seconds)
# Check status
make status
```

Expected output:
```
NAME                COMMAND                  SERVICE      STATUS
atlas-postgres      "docker-entrypoint.s…"   postgres     Up (healthy)
atlas-redis         "docker-entrypoint.s…"   redis        Up (healthy)
atlas-kafka         "/etc/confluent/dock…"   kafka        Up (healthy)
atlas-minio         "/usr/bin/docker-ent…"   minio        Up (healthy)
atlas-prometheus    "/bin/prometheus --c…"   prometheus   Up (healthy)
atlas-grafana       "/run.sh"                grafana      Up (healthy)
```

### 5. Initialize Database

```bash
# Run migrations
make migrate

# Seed initial data (optional)
make seed
```

### 6. Start API

```bash
# Run API server
make run
```

Expected output:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 7. Verify Installation

Open new terminal and run:

```bash
# Check API health
curl http://localhost:8000/health | jq

# Expected response:
# {
#   "status": "healthy",
#   "version": "0.1.0",
#   "environment": "development",
#   "uptime_seconds": 5.2,
#   "dependencies": [...]
# }
```

## Access Services

### API

- **Base URL**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics

### Grafana

- **URL**: http://localhost:3000
- **Username**: `admin`
- **Password**: `admin`
- **Dashboards**: Navigate to "Dashboards" → "Atlas"

### Prometheus

- **URL**: http://localhost:9090
- **Targets**: http://localhost:9090/targets
- **Queries**: http://localhost:9090/graph

### MinIO Console

- **URL**: http://localhost:9001
- **Username**: `minioadmin`
- **Password**: `minioadmin`

### Database

```bash
# PostgreSQL shell
make db-shell

# Or using psql directly
psql -h localhost -U atlas -d atlas_dev
# Password: atlas_dev
```

### Redis

```bash
# Redis CLI
make redis-cli

# Test connection
127.0.0.1:6379> PING
PONG
```

## Common Tasks

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
```

### Code Quality

```bash
# Run linter
make lint

# Format code
make fmt

# Type check
make type

# Run all checks
make check
```

### Database Operations

```bash
# Create new migration
make migration MSG="add users table"

# Apply migrations
make migrate

# Rollback last migration
make migrate-down

# View migration history
make migration-history

# Reset database (WARNING: deletes all data)
make db-reset
```

### Viewing Logs

```bash
# All services
make logs

# API only
make logs-api

# Specific service
docker-compose logs -f postgres
```

### Stopping Services

```bash
# Stop all services
make down

# Stop and remove volumes (WARNING: deletes all data)
make clean-all
```

## Troubleshooting

### Services Won't Start

**Problem**: Docker services fail to start

**Solution**:
```bash
# Check Docker is running
docker info

# Check port conflicts
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :9092  # Kafka
lsof -i :8000  # API

# Remove old containers and volumes
make clean-all

# Restart
make up
```

### Database Connection Errors

**Problem**: API can't connect to PostgreSQL

**Solution**:
```bash
# Check PostgreSQL is healthy
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Test connection manually
psql -h localhost -U atlas -d atlas_dev

# Restart PostgreSQL
docker-compose restart postgres
```

### Import Errors

**Problem**: Python import errors when running API

**Solution**:
```bash
# Reinstall dependencies
poetry install

# Clear Python cache
make clean

# Verify installation
poetry run python -c "import atlas_api; print(atlas_api.__version__)"
```

### Port Already in Use

**Problem**: Port 8000 already in use

**Solution**:
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>

# Or change port in .env
echo "API_PORT=8001" >> .env
```

### Kafka Connection Issues

**Problem**: Kafka not accepting connections

**Solution**:
```bash
# Kafka takes longer to start, wait 60 seconds
sleep 60

# Check Kafka logs
docker-compose logs kafka

# Restart Kafka and Zookeeper
docker-compose restart zookeeper kafka
```

## Next Steps

1. **Explore API**: Visit http://localhost:8000/docs
2. **View Metrics**: Open Grafana at http://localhost:3000
3. **Run Tests**: Execute `make test`
4. **Read Documentation**: Check `docs/` directory
5. **Review Code**: Start with `apps/api/src/atlas_api/main.py`

## Support

- **Documentation**: `docs/` directory
- **Issues**: GitHub Issues
- **Logs**: `make logs`

## Cleanup

When done working:

```bash
# Stop services (keeps data)
make down

# Stop and remove all data
make clean-all
```

---

**Next Runbook**: [002-deployment.md](002-deployment.md)

