# Contributing to Omnex

Thank you for your interest in contributing to Omnex! We welcome contributions from everyone and are grateful for even the smallest of improvements.

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher
- Node.js 18 or higher (for frontend development)
- Docker and Docker Compose (optional, but recommended)
- Git

### Development Setup

#### Using Dev Containers (Recommended)

1. Install [VS Code](https://code.visualstudio.com/) and the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
2. Clone the repository:
   ```bash
   git clone https://github.com/omnex-ai/omnex.git
   cd omnex
   ```
3. Open in VS Code: `code .`
4. Click "Reopen in Container" when prompted
5. Wait for the container to build and start

#### Local Setup

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/yourusername/omnex.git
   cd omnex
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

5. Copy environment variables:
   ```bash
   cp .env.example .env
   ```

6. Start the database:
   ```bash
   docker-compose up -d db redis
   ```

7. Run database migrations:
   ```bash
   alembic upgrade head
   ```

8. Start the development server:
   ```bash
   uvicorn src.main:app --reload
   ```

## 📋 Development Workflow

### 1. Find an Issue

- Check our [issue tracker](https://github.com/omnex-ai/omnex/issues)
- Look for issues labeled `good first issue` or `help wanted`
- Comment on the issue to let others know you're working on it

### 2. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number-description
```

### 3. Make Your Changes

- Write clean, readable code
- Follow our coding standards (see below)
- Add tests for new functionality
- Update documentation as needed

### 4. Test Your Changes

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_feature.py

# Run with coverage
pytest --cov=src --cov-report=html
```

### 5. Commit Your Changes

We use [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git commit -m "feat: add new memory storage backend"
git commit -m "fix: resolve race condition in context sync"
git commit -m "docs: update MCP integration guide"
```

Commit types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Build process or auxiliary tool changes

### 6. Push and Create a Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub with:
- Clear title and description
- Reference to any related issues
- Screenshots/videos for UI changes
- Test results

## 📏 Code Standards

### Python Code Style

We use [Ruff](https://github.com/astral-sh/ruff) for linting and formatting:

```bash
# Check code
ruff check .

# Format code
ruff format .
```

Key conventions:
- Follow PEP 8
- Use type hints for all functions
- Write docstrings for all public functions/classes
- Keep functions small and focused
- Use descriptive variable names

Example:
```python
from typing import Optional, List
from src.models import Context

async def store_context(
    namespace: str,
    key: str,
    value: dict,
    tags: Optional[List[str]] = None
) -> Context:
    """Store a context in the specified namespace.
    
    Args:
        namespace: The namespace for organizing contexts
        key: Unique identifier within the namespace
        value: The context data to store
        tags: Optional list of tags for categorization
        
    Returns:
        The created Context object
        
    Raises:
        ValueError: If namespace or key is invalid
        StorageError: If storage operation fails
    """
    # Implementation here
    pass
```

### TypeScript/JavaScript Code Style

We use ESLint and Prettier:

```bash
# Lint code
npm run lint

# Format code
npm run format
```

### Testing Guidelines

- Write tests for all new features
- Maintain test coverage above 80%
- Use descriptive test names
- Test edge cases and error conditions

Example test:
```python
import pytest
from src.services import ContextService

@pytest.mark.asyncio
async def test_store_context_with_valid_data():
    """Test storing context with valid data returns created context."""
    service = ContextService()
    context = await service.store(
        namespace="test",
        key="test_key",
        value={"data": "test"}
    )
    
    assert context.namespace == "test"
    assert context.key == "test_key"
    assert context.value == {"data": "test"}

@pytest.mark.asyncio
async def test_store_context_with_invalid_namespace_raises_error():
    """Test storing context with invalid namespace raises ValueError."""
    service = ContextService()
    
    with pytest.raises(ValueError, match="Invalid namespace"):
        await service.store(
            namespace="",
            key="test_key",
            value={"data": "test"}
        )
```

## 🏗️ Project Structure

```
omnex/
├── src/
│   ├── api/          # REST API endpoints
│   ├── core/         # Core business logic
│   ├── mcp/          # MCP server implementation
│   ├── models/       # Database models
│   ├── services/     # Business services
│   └── utils/        # Utility functions
├── tests/
│   ├── unit/         # Unit tests
│   └── integration/  # Integration tests
├── docs/             # Documentation
├── scripts/          # Utility scripts
└── examples/         # Example code
```

## 🐛 Reporting Issues

### Bug Reports

Please include:
- Clear description of the bug
- Steps to reproduce
- Expected behavior
- Actual behavior
- System information (OS, Python version, etc.)
- Relevant logs or error messages

### Feature Requests

Please include:
- Clear description of the feature
- Use cases and benefits
- Potential implementation approach
- Any relevant examples or mockups

## 💬 Communication

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Discord**: Join our [Discord server](https://discord.gg/omnex) for real-time chat

## 🎯 Pull Request Guidelines

### PR Checklist

- [ ] Code follows project style guidelines
- [ ] Tests pass locally
- [ ] New tests added for new features
- [ ] Documentation updated if needed
- [ ] Commit messages follow conventional commits
- [ ] PR description clearly explains changes
- [ ] Related issues are referenced

### Review Process

1. Automated checks must pass (tests, linting, etc.)
2. At least one maintainer review required
3. All review comments addressed
4. Final approval from maintainer
5. Squash and merge to main branch

## 🏆 Recognition

We use the [All Contributors](https://allcontributors.org/) specification to recognize all contributions:

- Code contributions
- Documentation improvements
- Bug reports
- Feature ideas
- Community support
- And more!

Your contributions will be recognized in our README.

## 📜 Code of Conduct

Please note that this project is released with a [Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project you agree to abide by its terms.

## 🤔 Need Help?

- Check our [documentation](https://docs.omnex.ai)
- Search existing [issues](https://github.com/omnex-ai/omnex/issues)
- Ask in [GitHub Discussions](https://github.com/omnex-ai/omnex/discussions)
- Join our [Discord server](https://discord.gg/omnex)

---

Thank you for contributing to Omnex! Your efforts help make AI memory management better for everyone. 🙏