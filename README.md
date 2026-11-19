# ERP-SOLUTION

A Django-based modular ERP foundation. The current repository contains a substantive inventory-management slice and scaffolding for additional ERP domains. It is **not yet a complete production ERP**.

## Current implementation

- Django and Django REST Framework.
- JWT authentication configured for API requests.
- Environment-specific Django settings.
- Inventory: warehouses, categories, products, stock levels, stock movements, serializers, viewsets, migrations, and tests.
- Core module loader and event utilities.
- PostgreSQL-oriented production configuration.
- Multi-stage Docker build and GitHub Actions workflows.

Inventory is currently the only substantive business module. Sales, HR, finance, procurement, and manufacturing require implementation and acceptance testing before production use.

## Repository layout

```text
config/                 Django settings and root URL configuration
src/core/               Shared module-loading and event utilities
src/modules/inventory/  Inventory models, serializers, APIs, migrations
src/modules/            Additional module scaffolding
tests/                  Unit and API tests
docs/                   Architecture, development, QA, and release guidance
scripts/                Local setup, pre-push checks, and backup helper
.github/workflows/      CI and container workflows
```

## Local development

Use a supported Python version compatible with the dependencies. Python 3.11 is the current Dockerfile runtime baseline.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
export SECRET_KEY='local-development-only'
export DJANGO_SETTINGS_MODULE=config.settings.development
python src/manage.py check
python src/manage.py makemigrations --check --dry-run
python src/manage.py migrate
pytest --cov=src --cov-report=term-missing
python src/manage.py runserver
```

Configure PostgreSQL and required environment variables for integration testing. Never use production credentials locally. Review `.github/SECRETS_SETUP.md` before configuring deployment.

## Quality checks

```bash
pre-commit run --all-files
pytest --cov=src --cov-report=xml --cov-fail-under=70
python src/manage.py check
python src/manage.py makemigrations --check --dry-run
```

Run checks from the repository root. CI becomes an authoritative merge gate only after workflow startup and configuration failures are resolved.

## Deployment status

A Dockerfile and production settings exist, but their presence does not establish deployability. Verify the container health-check route, production environment validation, migration execution, static-file serving, database readiness, image publication, and rollback before deploying.

## Engineering plan

See [Production Readiness Roadmap](docs/PRODUCTION_READINESS_ROADMAP.md) for the verified baseline, implementation sequence, exit criteria, and release requirements.

## Contribution workflow

1. Create a focused branch from current `main`.
2. Add or update tests with each behavior change.
3. Run formatting, lint, security, Django checks, migration checks, and tests.
4. Open a pull request; do not push directly to protected `main`.
5. Merge only after required checks and review pass.

## License

See [LICENSE](LICENSE).
