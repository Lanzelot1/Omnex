#!/bin/bash
set -e

echo "🚀 Setting up Omnex development environment..."

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs temp data/models .omnex

# Check Python version
echo "🐍 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then 
    echo "❌ Python $required_version or higher is required. Current version: $python_version"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
if [ -f "requirements.txt" ]; then
    echo "📦 Installing Python dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    if [ -f "requirements-dev.txt" ]; then
        echo "📦 Installing development dependencies..."
        pip install -r requirements-dev.txt
    fi
fi

# Install Node dependencies
if [ -f "package.json" ]; then
    echo "📦 Installing Node dependencies..."
    npm ci
fi

# Install pre-commit hooks
if [ -f ".pre-commit-config.yaml" ]; then
    echo "🎣 Installing pre-commit hooks..."
    pre-commit install
    pre-commit install --hook-type commit-msg
fi

# Setup environment file
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    echo "🔐 Creating .env file from example..."
    cp .env.example .env
    echo "⚠️  Please update .env with your actual configuration values"
fi

# Initialize database
if command -v docker &> /dev/null; then
    echo "🗄️ Starting database containers..."
    docker-compose up -d db redis
    
    # Wait for database to be ready
    echo "⏳ Waiting for database to be ready..."
    sleep 5
    
    # Run migrations
    if command -v alembic &> /dev/null; then
        echo "🔄 Running database migrations..."
        alembic upgrade head || echo "⚠️  Migrations failed. Database might not be ready yet."
    fi
else
    echo "⚠️  Docker not found. Please start database manually."
fi

# Download sample data
echo "📥 Setting up sample data..."
python scripts/download_sample_data.py || echo "⚠️  Sample data setup skipped"

echo "✅ Development environment ready!"
echo ""
echo "📖 Next steps:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Update .env file with your configuration"
echo "  3. Start the development server: uvicorn src.main:app --reload"
echo "  4. Visit http://localhost:8000/docs for API documentation"
echo ""
echo "💡 Useful commands:"
echo "  - Run tests: pytest"
echo "  - Run linting: ruff check ."
echo "  - Format code: ruff format ."
echo "  - Start all services: docker-compose up"