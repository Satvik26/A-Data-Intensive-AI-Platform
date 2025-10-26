.PHONY: help up down logs shell test test-unit test-integration test-cov lint fmt type pre-commit migrate migration seed db-shell grafana prometheus metrics clean install run dev

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)Atlas API - Available Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

# Docker Compose Commands
up: ## Start all services (detached)
	@echo "$(BLUE)Starting all services...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)Services started. Waiting for health checks...$(NC)"
	@sleep 5
	@make status

down: ## Stop all services
	@echo "$(BLUE)Stopping all services...$(NC)"
	docker-compose down

restart: ## Restart all services
	@echo "$(BLUE)Restarting all services...$(NC)"
	docker-compose restart

logs: ## View logs from all services
	docker-compose logs -f

logs-api: ## View API logs only
	docker-compose logs -f api

status: ## Show status of all services
	@echo "$(BLUE)Service Status:$(NC)"
	@docker-compose ps

shell: ## Enter API container shell
	docker-compose exec api /bin/bash

db-shell: ## Enter PostgreSQL shell
	docker-compose exec postgres psql -U atlas -d atlas_dev

redis-cli: ## Enter Redis CLI
	docker-compose exec redis redis-cli

# Development Commands
install: ## Install dependencies
	@echo "$(BLUE)Installing dependencies...$(NC)"
	poetry install

run: ## Run API locally (outside Docker)
	@echo "$(BLUE)Starting API server...$(NC)"
	poetry run uvicorn atlas_api.main:app --reload --host 0.0.0.0 --port 8000

dev: up run ## Start services and run API

# Code Quality Commands
lint: ## Run linter (Ruff)
	@echo "$(BLUE)Running linter...$(NC)"
	poetry run ruff check src/ tests/

lint-fix: ## Run linter with auto-fix
	@echo "$(BLUE)Running linter with auto-fix...$(NC)"
	poetry run ruff check --fix src/ tests/

fmt: ## Format code (Black)
	@echo "$(BLUE)Formatting code...$(NC)"
	poetry run black src/ tests/

fmt-check: ## Check code formatting
	@echo "$(BLUE)Checking code formatting...$(NC)"
	poetry run black --check src/ tests/

type: ## Run type checker (MyPy)
	@echo "$(BLUE)Running type checker...$(NC)"
	poetry run mypy src/

pre-commit: ## Run all pre-commit hooks
	@echo "$(BLUE)Running pre-commit hooks...$(NC)"
	poetry run pre-commit run --all-files

pre-commit-install: ## Install pre-commit hooks
	@echo "$(BLUE)Installing pre-commit hooks...$(NC)"
	poetry run pre-commit install

# Testing Commands
test: ## Run all tests
	@echo "$(BLUE)Running all tests...$(NC)"
	poetry run pytest -v

test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(NC)"
	poetry run pytest tests/unit/ -v

test-integration: ## Run integration tests only
	@echo "$(BLUE)Running integration tests...$(NC)"
	poetry run pytest tests/integration/ -v

test-cov: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	poetry run pytest --cov=atlas_api --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)Coverage report generated in htmlcov/index.html$(NC)"

test-watch: ## Run tests in watch mode
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	poetry run pytest-watch

# Database Commands
migrate: ## Run database migrations
	@echo "$(BLUE)Running database migrations...$(NC)"
	poetry run alembic upgrade head

migrate-down: ## Rollback last migration
	@echo "$(BLUE)Rolling back last migration...$(NC)"
	poetry run alembic downgrade -1

migration: ## Create new migration (usage: make migration MSG="description")
	@echo "$(BLUE)Creating new migration...$(NC)"
	@if [ -z "$(MSG)" ]; then \
		echo "$(RED)Error: MSG is required. Usage: make migration MSG='description'$(NC)"; \
		exit 1; \
	fi
	poetry run alembic revision --autogenerate -m "$(MSG)"

migration-history: ## Show migration history
	@echo "$(BLUE)Migration history:$(NC)"
	poetry run alembic history

seed: ## Seed database with initial data
	@echo "$(BLUE)Seeding database...$(NC)"
	poetry run python -m atlas_api.utils.seed

db-reset: ## Reset database (drop, create, migrate, seed)
	@echo "$(YELLOW)WARNING: This will delete all data!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose exec postgres psql -U atlas -c "DROP DATABASE IF EXISTS atlas_dev;"; \
		docker-compose exec postgres psql -U atlas -c "CREATE DATABASE atlas_dev;"; \
		make migrate; \
		make seed; \
		echo "$(GREEN)Database reset complete$(NC)"; \
	fi

# Monitoring Commands
grafana: ## Open Grafana dashboard
	@echo "$(BLUE)Opening Grafana...$(NC)"
	@open http://localhost:3000 || xdg-open http://localhost:3000 || echo "Open http://localhost:3000 in your browser"

prometheus: ## Open Prometheus UI
	@echo "$(BLUE)Opening Prometheus...$(NC)"
	@open http://localhost:9090 || xdg-open http://localhost:9090 || echo "Open http://localhost:9090 in your browser"

metrics: ## View current metrics
	@echo "$(BLUE)Current metrics:$(NC)"
	@curl -s http://localhost:8000/metrics | head -n 50

health: ## Check API health
	@echo "$(BLUE)Checking API health...$(NC)"
	@curl -s http://localhost:8000/health | python -m json.tool

api-docs: ## Open API documentation
	@echo "$(BLUE)Opening API docs...$(NC)"
	@open http://localhost:8000/docs || xdg-open http://localhost:8000/docs || echo "Open http://localhost:8000/docs in your browser"

# Cleanup Commands
clean: ## Clean up generated files
	@echo "$(BLUE)Cleaning up...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)Cleanup complete$(NC)"

clean-all: clean down ## Clean everything including Docker volumes
	@echo "$(YELLOW)Removing Docker volumes...$(NC)"
	docker-compose down -v
	@echo "$(GREEN)Full cleanup complete$(NC)"

# Build Commands
build: ## Build Docker images
	@echo "$(BLUE)Building Docker images...$(NC)"
	docker-compose build

rebuild: ## Rebuild Docker images without cache
	@echo "$(BLUE)Rebuilding Docker images...$(NC)"
	docker-compose build --no-cache

# Utility Commands
check: lint fmt-check type test ## Run all checks (lint, format, type, test)
	@echo "$(GREEN)All checks passed!$(NC)"

ci: ## Run CI pipeline locally
	@echo "$(BLUE)Running CI pipeline...$(NC)"
	@make lint
	@make fmt-check
	@make type
	@make test-cov
	@echo "$(GREEN)CI pipeline complete!$(NC)"

version: ## Show version information
	@echo "$(BLUE)Atlas API Version Information:$(NC)"
	@poetry version
	@echo "Python: $$(python --version)"
	@echo "Poetry: $$(poetry --version)"
	@echo "Docker: $$(docker --version)"
	@echo "Docker Compose: $$(docker-compose --version)"

