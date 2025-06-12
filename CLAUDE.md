# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Omnex is a universal memory layer for AI that enables seamless context sharing between ChatGPT, Claude, and any LLM. It's built on the Model Context Protocol (MCP) and provides a standardized way to manage and share knowledge across different AI systems.

**Key Value Propositions:**
- Persistent memory across AI sessions
- Cross-platform context sharing (works with any LLM)
- Semantic search capabilities for stored memories
- Privacy-first architecture with local storage options

**Technology Stack:**
- Backend: Python 3.11, FastAPI, SQLAlchemy, Celery
- MCP: Model Context Protocol SDK
- Database: PostgreSQL (primary), Redis (cache/broker)
- Testing: Pytest, coverage.py
- CI/CD: GitHub Actions, Docker

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
  - Required: namespace (string), key (string), value (object)
  - Optional: tags (array of strings)
- `retrieve_context`: Get specific context by namespace and key
  - Required: namespace (string), key (string)
- `search_memory`: Semantic search across stored memories
  - Required: query (string)
  - Optional: limit (integer, default: 10)

### API Endpoints Summary
```
GET  /                              # Root info
GET  /health                        # Health check with service status
GET  /health/live                   # Kubernetes liveness probe
GET  /health/ready                  # Kubernetes readiness probe
POST /api/v1/context/               # Create context
GET  /api/v1/context/{namespace}    # List contexts in namespace
GET  /api/v1/context/{namespace}/{key}  # Get specific context
DELETE /api/v1/context/{namespace}/{key} # Delete context
POST /api/v1/memory/                # Store memory
GET  /api/v1/memory/{memory_id}     # Get memory by ID
POST /api/v1/memory/search          # Search memories
DELETE /api/v1/memory/{memory_id}   # Delete memory
```

## Quick Start (First Time Setup)

```bash
# 1. Clone and enter directory
git clone https://github.com/omnex-ai/omnex.git
cd omnex

# 2. Run automated setup
make setup

# 3. Start services
make docker-up  # Start database and Redis
make run        # Start API server

# Visit http://localhost:8000/docs
```

## Essential Development Commands

### Daily Development
```bash
# Start all services with Docker
make docker-up

# Run dev server locally (requires activated venv)
make run

# Run MCP server standalone
make run-mcp

# View logs
make docker-logs
```

### Testing & Quality
```bash
# Run all tests with coverage
make test

# Run specific test file
pytest tests/unit/test_health.py -v

# Run single test
pytest tests/unit/test_health.py::test_health_check -v

# Run tests with output
pytest -s -v

# Run only fast tests (skip slow marked tests)
pytest -m "not slow"

# Linting only
make lint

# Auto-format code
make format

# Full check (lint + test)
make check

# Type checking
mypy src --ignore-missing-imports

# Security scan
bandit -r src -ll
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
All configuration is managed through `.env` file (copy from `.env.example`). Critical settings:

**Required:**
- `SECRET_KEY`: Application secret (32+ chars)
- `JWT_SECRET_KEY`: JWT signing key (32+ chars)
- `DATABASE_URL`: PostgreSQL connection string

**API Keys (optional but recommended):**
- `OPENAI_API_KEY`: For OpenAI integrations
- `ANTHROPIC_API_KEY`: For Claude integrations
- `GOOGLE_API_KEY`: For Google AI integrations

**Service Configuration:**
- `MCP_SERVER_PORT`: MCP server port (default: 3000)
- `MCP_SERVER_HOST`: MCP bind address (default: 0.0.0.0)
- `REDIS_URL`: Redis connection (default: redis://localhost:6379/0)
- `CELERY_BROKER_URL`: Celery broker (default: redis://localhost:6379/1)

**Feature Flags:**
- `RATE_LIMIT_ENABLED`: Enable API rate limiting (default: true)
- `PROMETHEUS_ENABLED`: Enable metrics endpoint (default: true)

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
- Python: Ruff (linting/formatting), mypy (type checking), bandit (security)
- JavaScript/TypeScript: ESLint, Prettier
- Markdown: markdownlint
- Shell: shellcheck
- General: trailing whitespace, large files, merge conflicts
- Commit messages: commitizen (conventional commits)

To run manually: `pre-commit run --all-files`
To skip: `git commit --no-verify` (not recommended)

### Conventional Commits

This project uses [Conventional Commits](https://www.conventionalcommits.org/) standard.

**Commit Format:**
```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Common Types:**
- `feat`: New feature (correlates with MINOR in SemVer)
- `fix`: Bug fix (correlates with PATCH in SemVer)
- `docs`: Documentation only changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring without changing functionality
- `perf`: Performance improvements
- `test`: Adding or modifying tests
- `build`: Changes to build system or dependencies
- `ci`: Changes to CI configuration
- `chore`: Other changes that don't modify src or test files

**Examples:**
```bash
# Simple commit
git commit -m "feat: add memory search endpoint"

# With scope
git commit -m "fix(api): handle empty namespace in context retrieval"

# Breaking change
git commit -m "feat!: change API response format"

# With body
git commit -m "refactor: reorganize context service layer

Moved business logic from API endpoints to dedicated service classes.
This improves testability and separation of concerns."
```

**Interactive Commit (Recommended):**
```bash
cz commit  # Use commitizen for guided commit message creation
```

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

## Project Structure

```
omnex/
├── src/
│   ├── api/           # API endpoints
│   │   ├── v1/        # API version 1
│   │   └── health.py  # Health checks
│   ├── core/          # Core utilities
│   │   ├── config.py  # Settings management
│   │   └── logging.py # Structured logging
│   ├── mcp/           # MCP server
│   ├── models/        # Database models
│   ├── services/      # Business logic (to be created)
│   └── main.py        # FastAPI app
├── tests/
│   ├── unit/          # Unit tests
│   ├── integration/   # Integration tests
│   └── conftest.py    # Pytest fixtures
├── scripts/           # Utility scripts
├── docs/              # Documentation
└── examples/          # Usage examples
```

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

## Key Design Decisions

### Why MCP?
Model Context Protocol provides a standardized way for AI assistants to access tools and data. It's becoming the industry standard for AI integrations.

### Why Namespace/Key Pattern?
Contexts are organized by namespace (e.g., project name) and key (specific context) to allow:
- Logical grouping of related contexts
- Easy bulk operations per namespace
- Clear access patterns

### Why Separate Context vs Memory?
- **Context**: Structured data with explicit namespace/key (for precise retrieval)
- **Memory**: Unstructured text with embeddings (for semantic search)

### Why PostgreSQL + Redis?
- PostgreSQL: ACID compliance for critical data
- Redis: Fast caching and reliable message broker for Celery

## Security Considerations

- All endpoints require authentication (JWT tokens) - to be implemented
- Rate limiting prevents abuse
- Input validation via Pydantic models
- SQL injection prevention via SQLAlchemy ORM
- Secrets in environment variables, never in code
- CORS configured for specific origins only

## Future Enhancements Planned

- Authentication/authorization system
- WebSocket support for real-time updates
- Vector embeddings for semantic search
- Multi-tenancy support
- SDK libraries for Python/JS/Go
- Prometheus metrics dashboard
- Admin UI for context management