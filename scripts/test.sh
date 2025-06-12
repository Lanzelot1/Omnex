#!/bin/bash
set -e

echo "🧪 Running Omnex tests..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run linting
echo "🔍 Running linting checks..."
ruff check . || echo "⚠️  Linting issues found"

# Run type checking
echo "🔍 Running type checks..."
mypy src --ignore-missing-imports || echo "⚠️  Type checking issues found"

# Run security checks
echo "🔒 Running security checks..."
bandit -r src -ll || echo "⚠️  Security issues found"

# Run tests with coverage
echo "🧪 Running tests with coverage..."
pytest \
    --cov=src \
    --cov-report=term-missing \
    --cov-report=html \
    --cov-report=xml \
    -v

# Check coverage threshold
coverage_percentage=$(coverage report | grep TOTAL | awk '{print $4}' | sed 's/%//')
min_coverage=80

if (( $(echo "$coverage_percentage < $min_coverage" | bc -l) )); then
    echo "❌ Coverage ${coverage_percentage}% is below minimum ${min_coverage}%"
    exit 1
else
    echo "✅ Coverage ${coverage_percentage}% meets minimum ${min_coverage}%"
fi

echo "✅ All tests passed!"