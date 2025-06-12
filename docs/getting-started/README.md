# Getting Started with Omnex

Welcome to Omnex! This guide will help you get up and running with the universal memory layer for AI.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.9+** - [Download Python](https://www.python.org/downloads/)
- **Node.js 18+** (optional, for frontend development) - [Download Node.js](https://nodejs.org/)
- **Docker & Docker Compose** (recommended) - [Download Docker](https://www.docker.com/products/docker-desktop/)
- **Git** - [Download Git](https://git-scm.com/downloads)

## Installation

### Option 1: Quick Start with Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/omnex-ai/omnex.git
   cd omnex
   ```

2. **Copy environment configuration**
   ```bash
   cp .env.example .env
   ```

3. **Configure your environment**
   
   Edit `.env` and add your API keys:
   ```env
   # Required - Generate secure keys (32+ characters)
   SECRET_KEY=your-super-secret-key-change-this
   JWT_SECRET_KEY=your-jwt-secret-key-change-this
   
   # Optional - Add your LLM API keys
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=sk-ant-...
   ```

4. **Start all services**
   ```bash
   docker-compose up
   ```

5. **Verify installation**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

### Option 2: Local Development Setup

1. **Clone and setup**
   ```bash
   git clone https://github.com/omnex-ai/omnex.git
   cd omnex
   make setup  # This runs scripts/setup.sh
   ```

2. **Activate virtual environment**
   ```bash
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start services**
   ```bash
   # Start database and Redis
   docker-compose up -d db redis
   
   # Run migrations
   alembic upgrade head
   
   # Start the API server
   make run
   ```

## Your First Request

### Using the API

1. **Store a context**
   ```bash
   curl -X POST http://localhost:8000/api/v1/context/ \
     -H "Content-Type: application/json" \
     -d '{
       "namespace": "my_project",
       "key": "requirements",
       "value": {
         "description": "Build an AI chat assistant",
         "deadline": "2024-03-01"
       },
       "tags": ["project", "planning"]
     }'
   ```

2. **Retrieve the context**
   ```bash
   curl http://localhost:8000/api/v1/context/my_project/requirements
   ```

### Using the MCP Server

1. **Start the MCP server**
   ```bash
   make run-mcp
   ```

2. **Connect with an MCP client**
   
   See `examples/mcp_client_example.py` for a complete example:
   ```python
   from mcp import ClientSession, StdioServerParameters
   from mcp.client.stdio import stdio_client
   
   # Connect and use the tools
   async with stdio_client(server_params) as (read, write):
       async with ClientSession(read, write) as session:
           await session.initialize()
           
           # Store context
           result = await session.call_tool(
               "store_context",
               arguments={
                   "namespace": "project_x",
                   "key": "requirements",
                   "value": {"description": "AI assistant"}
               }
           )
   ```

## Next Steps

- 📚 Read the [Architecture Overview](../architecture.md) to understand the system design
- 🔌 Learn about [MCP Integration](../user-guide/mcp-integration.md) for AI assistants
- 📖 Explore the [API Reference](../api-reference/) for all endpoints
- 🤝 Check out [Contributing Guidelines](../../CONTRIBUTING.md) to help improve Omnex

## Common Issues

### Port Already in Use
If you see "port already in use" errors:
```bash
# Check what's using the port
lsof -i :8000  # On macOS/Linux
netstat -ano | findstr :8000  # On Windows

# Or use different ports in .env
```

### Database Connection Failed
```bash
# Ensure PostgreSQL is running
docker-compose up -d db

# Check connection string in .env
DATABASE_URL=postgresql://omnex:omnex@localhost:5432/omnex
```

### Import Errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

## Getting Help

- 💬 [GitHub Discussions](https://github.com/omnex-ai/omnex/discussions) - Ask questions
- 🐛 [GitHub Issues](https://github.com/omnex-ai/omnex/issues) - Report bugs
- 📖 [API Docs](http://localhost:8000/docs) - Interactive API documentation