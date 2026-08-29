#!/usr/bin/env bash
set -euo pipefail

cd /workspaces/ERP-SOLUTION

# Install repository-managed pre-commit hooks when available.
if command -v pre-commit >/dev/null 2>&1 && [ -f .pre-commit-config.yaml ]; then
  pre-commit install
fi

# Keep the workspace ready for common Django workflows without requiring
# application-specific environment values or external services at creation time.
python --version
pip --version
pytest --version

echo "ERP-SOLUTION development container is ready."
