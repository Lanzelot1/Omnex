# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Omnex is a universal memory layer for AI that enables seamless context sharing between ChatGPT, Claude, and any LLM. It's built on the Model Context Protocol (MCP) and provides a standardized way to manage and share knowledge across different AI systems.

## Key Architecture Components

### Core Services Architecture
- **FastAPI Backend** (`src/main.py`): Main REST API server running on port 8000
- **MCP Server** (`src/mcp/server.py`): Model Context Protocol server for AI integrations on port 3000
- **PostgreSQL Database**: Primary data storage for contexts and memories
- **Redis**: Used for caching and as Celery broker
- **Celery Workers**: Background task processing for async operations

### API Structure
- `/health/*` - Health check endpoints for Kubernetes probes
- `/api/v1/context/*` - Context management (store/retrieve/delete)
- `/api/v1/memory/*` - Memory operations with semantic search capabilities

### MCP Tools Available
- `store_context`: Store context with namespace/key organization
- `retrieve_context`: Get specific context by namespace and key
- `search_memory`: Semantic search across stored memories

## Essential Development Commands

### Quick Start
```bash
# Full setup (creates venv, installs deps, sets up DB)
make setup

# Start all services with Docker
make docker-up

# Run dev server locally (requires activated venv)
make run

# Run MCP server standalone
make run-mcp
```

### Testing & Quality
```bash
# Run all tests with coverage
make test

# Run specific test file
pytest tests/unit/test_health.py -v

# Run single test
pytest tests/unit/test_health.py::test_health_check -v

# Linting only
make lint

# Auto-format code
make format

# Full check (lint + test)
make check
```

### Database Operations
```bash
# Run migrations
make db-migrate

# Rollback last migration
make db-rollback

# Reset database (caution!)
make db-reset
```

### Docker Operations
```bash
# View logs
make docker-logs

# Rebuild images
make docker-build

# Stop all services
make docker-down
```

## Configuration Management

### Environment Variables
All configuration is managed through `.env` file (copy from `.env.example`). Key settings:
- API keys: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`
- Database: `DATABASE_URL` 
- MCP: `MCP_SERVER_PORT`, `MCP_SERVER_HOST`
- Security: `SECRET_KEY`, `JWT_SECRET_KEY` (must be 32+ chars)

### Service URLs
- FastAPI: http://localhost:8000 (docs at /docs)
- MCP Server: http://localhost:3000
- PostgreSQL: localhost:5432
- Redis: localhost:6379
- Flower (Celery monitoring): http://localhost:5555

## Code Organization Patterns

### API Endpoints Pattern
New endpoints should follow the structure in `src/api/v1/`:
1. Create route module in appropriate version directory
2. Use Pydantic models for request/response
3. Include in router registration in `v1/__init__.py`

### MCP Tool Pattern
To add new MCP tools:
1. Add tool definition in `handle_list_tools()` method
2. Implement handler method (e.g., `_your_tool_name()`)
3. Add case in `handle_call_tool()` switch

### Service Layer Pattern
Business logic should be separated from API endpoints:
- API endpoints handle HTTP concerns
- Services in `src/services/` contain business logic
- Models in `src/models/` define database schemas

## Testing Conventions

### Test Structure
- Unit tests: `tests/unit/` - test individual components
- Integration tests: `tests/integration/` - test component interactions
- Fixtures in `tests/conftest.py`

### Test Naming
- Test files: `test_<module_name>.py`
- Test functions: `test_<functionality>_<scenario>`
- Use descriptive names that explain what's being tested

## Development Workflow

### Branch Strategy
- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/*`: Individual feature branches
- `fix/*`: Bug fix branches

### Pre-commit Hooks
Pre-commit runs automatically on commit:
- Python: Ruff (linting/formatting), mypy (type checking)
- JavaScript: ESLint, Prettier
- General: trailing whitespace, large files, merge conflicts

### Database Migrations
When modifying models:
1. Make changes to SQLAlchemy models
2. Generate migration: `alembic revision --autogenerate -m "description"`
3. Review and edit migration file if needed
4. Apply: `alembic upgrade head`

## Docker Development

### Service Dependencies
The `docker-compose.yml` defines service startup order:
1. `db` and `redis` start first
2. `app` waits for database
3. `celery-worker` and `celery-beat` start after redis
4. `mcp-server` can run independently

### Volume Mounts
Development volumes are mounted for hot-reloading:
- `./src:/app/src` - Source code
- `./tests:/app/tests` - Tests
- `./scripts:/app/scripts` - Utility scripts

## Common Issues & Solutions

### Database Connection Errors
- Ensure PostgreSQL is running: `docker-compose up -d db`
- Check DATABASE_URL in .env matches docker-compose settings
- Wait for DB to be ready (health check may take 5-10 seconds)

### Import Errors
- Activate virtual environment: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`
- For development: `pip install -r requirements-dev.txt`

### MCP Server Issues
- Check if port 3000 is available
- Ensure `mcp` package is installed
- Run standalone for debugging: `python -m src.mcp.server`

## Performance Considerations

### Database Optimization
- Connection pooling configured via `DATABASE_POOL_SIZE`
- Redis caching for frequently accessed data
- Indexes on namespace/key fields for context queries

### API Rate Limiting
- Configured via `RATE_LIMIT_REQUESTS_PER_MINUTE`
- Per-IP limiting when `RATE_LIMIT_ENABLED=true`
- Adjust for production workloads

### Background Tasks
- Long-running operations use Celery
- Redis as message broker
- Monitor with Flower UI at port 5555