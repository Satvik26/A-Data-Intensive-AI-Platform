# Atlas Platform - Quick Start Guide

**Get running in under 5 minutes!** ⚡

## Prerequisites Check

```bash
# Verify you have these installed:
docker --version          # Should be 20.10+
docker-compose --version  # Should be 2.0+
python --version          # Should be 3.11+
poetry --version          # Should be 1.7+
make --version            # Any recent version
```

If anything is missing, see [Installation Guide](docs/runbooks/001-getting-started.md#prerequisites).

## 🚀 Quick Start (5 Steps)

### 1. Navigate to API Directory

```bash
cd apps/api
```

### 2. Install Dependencies

```bash
# Install Python dependencies (takes ~2 minutes)
poetry install

# Install pre-commit hooks (optional but recommended)
poetry run pre-commit install
```

### 3. Configure Environment

```bash
# Copy sample environment file
cp .env.sample .env

# Defaults work for local development - no changes needed!
```

### 4. Start Infrastructure

```bash
# Start all services (PostgreSQL, Redis, Kafka, MinIO, Prometheus, Grafana)
make up

# Wait for services to be healthy (~30-60 seconds)
# You'll see health checks passing in the logs
```

### 5. Run the API

```bash
# Start FastAPI server
make run
```

You should see:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## ✅ Verify It Works

Open a new terminal and run:

```bash
# Check API health
curl http://localhost:8000/health | jq

# Expected output:
# {
#   "status": "healthy",
#   "version": "0.1.0",
#   "environment": "development",
#   "uptime_seconds": 5.2,
#   "dependencies": [
#     {"name": "postgresql", "status": "healthy", "latency_ms": 2.5},
#     {"name": "redis", "status": "healthy", "latency_ms": 1.2},
#     {"name": "kafka", "status": "healthy", "latency_ms": 5.0},
#     {"name": "minio", "status": "healthy", "latency_ms": 3.0}
#   ]
# }
```

## 🎉 Success! Now What?

### Explore the API

```bash
# Interactive API documentation (Swagger UI)
open http://localhost:8000/docs

# Alternative documentation (ReDoc)
open http://localhost:8000/redoc

# View Prometheus metrics
curl http://localhost:8000/metrics | head -20
```

### View Dashboards

```bash
# Open Grafana (username: admin, password: admin)
open http://localhost:3000

# Open Prometheus
open http://localhost:9090
```

### Run Tests

```bash
# Run all tests
make test

# Expected output:
# ===== 8 passed in 0.5s =====
```

### Check Code Quality

```bash
# Run all quality checks
make check

# Or individually:
make lint    # Linting
make fmt     # Formatting
make type    # Type checking
```

## 📚 Next Steps

### Learn the Codebase

1. **Start with the main app**: `src/atlas_api/main.py`
2. **Check health endpoints**: `src/atlas_api/routers/health.py`
3. **Review configuration**: `src/atlas_api/config.py`
4. **Explore tests**: `tests/unit/test_health.py`

### Read Documentation

- **[Main README](README.md)** - Project overview
- **[API README](apps/api/README.md)** - API documentation
- **[Architecture ADR](docs/ADRs/001-architecture-overview.md)** - Design decisions
- **[Getting Started Runbook](docs/runbooks/001-getting-started.md)** - Detailed guide

### Try Common Tasks

```bash
# View logs
make logs

# Enter API container shell
make shell

# Access PostgreSQL
make db-shell

# Access Redis
make redis-cli

# View service status
make status
```

## 🛠️ Troubleshooting

### Services Won't Start

```bash
# Check Docker is running
docker info

# Remove old containers and volumes
make clean-all

# Start fresh
make up
```

### Port Already in Use

```bash
# Find what's using port 8000
lsof -i :8000

# Kill the process or change port in .env
echo "API_PORT=8001" >> .env
```

### Tests Fail

```bash
# Reinstall dependencies
poetry install

# Clear cache
make clean

# Run tests with verbose output
pytest -vv
```

### Can't Connect to Database

```bash
# Check PostgreSQL is healthy
docker-compose ps postgres

# View logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

## 🧹 Cleanup

When you're done:

```bash
# Stop services (keeps data)
make down

# Stop and remove all data
make clean-all
```

## 📖 Full Documentation

For detailed information, see:

- **[Complete Setup Guide](docs/runbooks/001-getting-started.md)**
- **[API Documentation](apps/api/README.md)**
- **[Architecture Overview](docs/ADRs/001-architecture-overview.md)**
- **[Implementation Report](IMPLEMENTATION_REPORT.md)**

## 🆘 Need Help?

1. Check the [Troubleshooting section](docs/runbooks/001-getting-started.md#troubleshooting)
2. Review logs: `make logs`
3. Check service status: `make status`
4. Read the [API README](apps/api/README.md)

## 🎯 What You Have Now

✅ **Working FastAPI application** with health checks  
✅ **Complete infrastructure stack** (PostgreSQL, Redis, Kafka, MinIO)  
✅ **Observability** (Prometheus, Grafana, OpenTelemetry)  
✅ **Testing framework** with passing tests  
✅ **Code quality tools** (linting, formatting, type checking)  
✅ **Comprehensive documentation**  
✅ **Development workflow** with Makefile commands  

## 🚀 Ready to Build!

You now have a production-grade foundation for building data-intensive applications following DDIA principles.

**Happy coding!** 🎉

---

**Quick Reference**:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090

**Common Commands**:
```bash
make up      # Start services
make run     # Run API
make test    # Run tests
make logs    # View logs
make down    # Stop services
```

