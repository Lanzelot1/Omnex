# Omnex

<p align="center">
  <img src="assets/logo.png" alt="Omnex Logo" width="200"/>
</p>

<p align="center">
  <a href="https://github.com/omnex-ai/omnex/actions"><img src="https://github.com/omnex-ai/omnex/workflows/CI/badge.svg" alt="CI Status"></a>
  <a href="https://codecov.io/gh/omnex-ai/omnex"><img src="https://codecov.io/gh/omnex-ai/omnex/branch/main/graph/badge.svg" alt="Coverage"></a>
  <a href="https://pypi.org/project/omnex/"><img src="https://img.shields.io/pypi/v/omnex.svg" alt="PyPI version"></a>
  <a href="#"><img src="https://img.shields.io/discord/1234567890.svg?label=Discord&logo=discord" alt="Discord"></a>
  <a href="https://github.com/omnex-ai/omnex/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-blue.svg" alt="License"></a>
</p>

## 🚀 Universal Memory Layer for AI

Omnex is a universal memory layer for AI that enables seamless context sharing between ChatGPT, Claude, and any LLM. Built on the Model Context Protocol (MCP), it provides a standardized way to manage and share knowledge across different AI systems.

## ✨ Key Features

- 🔌 **MCP Integration**: Built on Anthropic's Model Context Protocol for standardized AI communication
- 🧠 **Universal Memory**: Share context and knowledge between different AI models seamlessly
- 🔄 **Real-time Sync**: Keep your AI assistants in sync with automatic context updates
- 🛡️ **Privacy First**: Your data stays secure with end-to-end encryption
- 📊 **Knowledge Graph**: Visualize and manage your AI's knowledge base
- 🚀 **Easy Integration**: Simple APIs for popular AI platforms

## 🏃‍♂️ Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/omnex-ai/omnex.git
cd omnex

# Copy environment variables
cp .env.example .env

# Start with Docker Compose
docker-compose up

# Visit http://localhost:8000
```

### Local Development

```bash
# Clone the repository
git clone https://github.com/omnex-ai/omnex.git
cd omnex

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the server
uvicorn src.main:app --reload

# Visit http://localhost:8000
```

## 🔧 Configuration

### Basic Setup

1. **API Keys**: Add your LLM API keys to `.env`:
   ```
   OPENAI_API_KEY=your_openai_key
   ANTHROPIC_API_KEY=your_anthropic_key
   ```

2. **MCP Server**: Configure your MCP endpoints:
   ```
   MCP_SERVER_PORT=3000
   MCP_SERVER_HOST=0.0.0.0
   ```

3. **Database**: Set up your database connection:
   ```
   DATABASE_URL=postgresql://user:pass@localhost/omnex
   ```

## 📚 Usage Examples

### Python SDK

```python
from omnex import OmnexClient

# Initialize client
client = OmnexClient(api_key="your_api_key")

# Store context
client.store_context(
    namespace="project_x",
    key="requirements",
    value="The system should support real-time collaboration..."
)

# Retrieve context
context = client.get_context("project_x", "requirements")

# Share between AI models
client.sync_to_claude("project_x")
client.sync_to_openai("project_x")
```

### MCP Integration

```python
from omnex.mcp import MCPServer

# Create MCP server
server = MCPServer(name="omnex-memory")

# Register handlers
@server.tool()
async def store_memory(content: str, tags: list[str]):
    """Store a memory with tags"""
    return await memory_store.save(content, tags)

# Run server
server.run()
```

### REST API

```bash
# Store context
curl -X POST http://localhost:8000/api/v1/context \
  -H "Authorization: Bearer your_token" \
  -H "Content-Type: application/json" \
  -d '{
    "namespace": "project_x",
    "key": "requirements",
    "value": "System requirements..."
  }'

# Retrieve context
curl http://localhost:8000/api/v1/context/project_x/requirements \
  -H "Authorization: Bearer your_token"
```

## 🏗️ Architecture

Omnex uses a modular architecture designed for scalability and extensibility:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   ChatGPT   │     │    Claude   │     │  Other LLMs │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                    │
       └───────────────────┴────────────────────┘
                           │
                    ┌──────▼──────┐
                    │  MCP Layer  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ Omnex Core  │
                    └──────┬──────┘
                           │
            ┌──────────────┴──────────────┐
            │                             │
      ┌─────▼─────┐                ┌─────▼─────┐
      │  Storage  │                │   Cache   │
      └───────────┘                └───────────┘
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run linting
ruff check .
```

### Good First Issues

Check out our [good first issues](https://github.com/omnex-ai/omnex/labels/good%20first%20issue) to get started!

## 📖 Documentation

- [Getting Started Guide](docs/getting-started/)
- [API Reference](docs/api-reference/)
- [MCP Integration Guide](docs/user-guide/mcp-integration.md)
- [Architecture Overview](docs/architecture.md)

## 🛣️ Roadmap

- [ ] Enhanced multi-modal memory support
- [ ] Advanced knowledge graph visualization
- [ ] Plugin system for custom integrations
- [ ] Mobile SDK (iOS/Android)
- [ ] Enterprise features (SSO, audit logs)

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Built with amazing open source projects:
- [Model Context Protocol](https://github.com/anthropics/mcp) by Anthropic
- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- And many others!

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=omnex-ai/omnex&type=Date)](https://star-history.com/#omnex-ai/omnex&Date)

---

<p align="center">
  Made with ❤️ by the Omnex Community
</p>