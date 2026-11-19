#!/usr/bin/env bash
set -euo pipefail

cd /workspaces/ERP-SOLUTION

echo "Waiting for development services..."
bash .devcontainer/scripts/wait-for-services.sh

echo "Installing development dependencies..."
python -m pip install --no-cache-dir -r requirements-dev.txt

if [ -f .pre-commit-config.yaml ]; then
  pre-commit install
fi

echo "Applying Django migrations..."
python src/manage.py migrate --noinput

echo "Checking Django configuration..."
python src/manage.py check

echo
echo "=== ERP-SOLUTION Development Environment Ready ==="
python --version
python -m pip --version
pytest --version
echo
echo "Start the server: python src/manage.py runserver 0.0.0.0:8000"
echo "Run tests:        python -m pytest"
