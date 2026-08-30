#!/usr/bin/env bash
set -euo pipefail

cd /workspaces/ERP-SOLUTION

# Install repository-managed pre-commit hooks when available.
if command -v pre-commit >/dev/null 2>&1 && [ -f .pre-commit-config.yaml ]; then
  pre-commit install
fi

# Install Python dependencies in the virtual environment
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Run Django migrations
echo "Running database migrations..."
python src/manage.py migrate

# Display environment information
echo ""
echo "=== ERP-SOLUTION Development Environment Ready ==="
python --version
pip --version
pytest --version
echo ""
echo "Database: PostgreSQL 15 (host: db, port: 5432)"
echo "Cache/Queue: Redis 7 (host: redis, port: 6379)"
echo ""
echo "To start the development server:"
echo "  python src/manage.py runserver 0.0.0.0:8000"
echo ""
echo "To run tests:"
echo "  pytest tests/ --ds=config.settings.development"
echo ""
