.PHONY: help setup test lint format clean run docker-up docker-down

# Default target
.DEFAULT_GOAL := help

# Help command
help: ## Show this help message
	@echo "Omnex Development Commands"
	@echo "========================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Development setup
setup: ## Set up development environment
	@bash scripts/setup.sh

# Testing
test: ## Run all tests with coverage
	@bash scripts/test.sh

test-unit: ## Run unit tests only
	@pytest tests/unit -v

test-integration: ## Run integration tests only
	@pytest tests/integration -v

# Code quality
lint: ## Run linting checks
	@ruff check .
	@mypy src --ignore-missing-imports

format: ## Format code
	@ruff format .
	@isort .

check: lint test ## Run all checks (lint + test)

# Development server
run: ## Run development server
	@uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

run-mcp: ## Run MCP server
	@python -m src.mcp.server

# Docker commands
docker-up: ## Start all services with Docker Compose
	@docker-compose up -d

docker-down: ## Stop all Docker services
	@docker-compose down

docker-logs: ## Show Docker logs
	@docker-compose logs -f

docker-build: ## Build Docker images
	@docker-compose build

# Database
db-migrate: ## Run database migrations
	@alembic upgrade head

db-rollback: ## Rollback last migration
	@alembic downgrade -1

db-reset: ## Reset database (dangerous!)
	@alembic downgrade base
	@alembic upgrade head

# Cleaning
clean: ## Clean up generated files
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name "*.coverage" -delete
	@find . -type d -name "*.egg-info" -exec rm -rf {} +
	@find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@find . -type d -name ".mypy_cache" -exec rm -rf {} +
	@find . -type d -name ".ruff_cache" -exec rm -rf {} +
	@find . -type d -name "htmlcov" -exec rm -rf {} +
	@rm -f .coverage
	@rm -f coverage.xml

# Installation
install: ## Install all dependencies
	@pip install -r requirements.txt -r requirements-dev.txt
	@npm ci
	@pre-commit install

# Documentation
docs-serve: ## Serve documentation locally
	@mkdocs serve

docs-build: ## Build documentation
	@mkdocs build

# Release
version: ## Show current version
	@python -c "from src import __version__; print(__version__)"