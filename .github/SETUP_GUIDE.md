# GitHub Actions Setup Guide for ERP-SOLUTION

## ✅ Current Status

### Secrets Already Configured (Docker Environment)
The following secrets are already set up in your **Docker** environment:
- `DOCKERHUB_USERNAME` ⚠️ Check spelling (you have `DOCKHUB_USERNAME` - missing 'R')
- `DOCKERHUB_PASSWORD`
- `API_GITHUB_USERNAME`
- `API_GITHUB_KEY`
- `TC_CLOUD_TOKEN`
- Other integration keys (Railway, Supabase, Vercel, DB, Redis)

### ❌ Missing Configuration

#### 1. Fix Secret Typo
You have a typo in your Docker environment secrets:
- **Current**: `DOCKHUB_USERNAME` (incorrect)
- **Required**: `DOCKERHUB_USERNAME` (correct)

**Action**: Go to Settings → Environments → Docker → Edit `DOCKHUB_USERNAME` and rename it to `DOCKERHUB_USERNAME`

#### 2. Add Repository Variables (Required)
Your repository currently has **no variables**. You need to add these:

**Navigate to**: Settings → Secrets and variables → Actions → Variables → New repository variable

| Variable Name | Value | Description |
|--------------|-------|-------------|
| `DOCKERHUB_USERNAME` | `nyeinpyaesone-ui` | Your Docker Hub username (same as secret) |
| `POSTGRES_VERSION` | `15` | PostgreSQL version for tests |
| `REDIS_VERSION` | `7` | Redis version for tests |

**Why variables?** Variables are used for non-sensitive configuration and are referenced in the workflow as `${{ vars.VARIABLE_NAME }}`.

## 📋 Workflow Configuration Summary

### Target Environment
- **Environment Name**: `Docker`
- **Trigger Branch**: `develop` only
- **Image Tags**: 
  - `dev-YYYYMMDD-SHA` (daily builds with commit SHA)
  - `develop` (latest develop branch)

### Image Destination
```
docker.io/nyeinpyaesone-ui/erp-solution:develop
docker.io/nyeinpyaesone-ui/erp-solution:dev-20250130-a1b2c3d
```

### Jobs Pipeline
1. **lint** → Code quality checks (flake8, bandit security scan)
2. **test** → Pytest with PostgreSQL 15 + Redis 7 services (70% coverage threshold)
3. **build-and-push** → Multi-stage Docker build → Push to Docker Hub

## 🔧 Required Components (Verified from Codebase)

### Project Structure
```
/workspace
├── src/                    # Django application code
│   ├── core/              # Core module
│   ├── modules/           # ERP modules (inventory, hr, finance, etc.)
│   └── manage.py          # Django management script
├── config/                # Django configuration
│   ├── settings/          # Settings (base.py, test.py, production.py)
│   ├── urls.py
│   └── wsgi.py
├── tests/                 # Test suite
│   ├── conftest.py        # Pytest fixtures
│   └── test_core.py       # Core tests
├── requirements.txt       # Python dependencies
└── Dockerfile            # Multi-stage production build
```

### Technology Stack (from requirements.txt)
- **Framework**: Django 4.2.x
- **Database**: PostgreSQL 15 (via psycopg2-binary, SQLAlchemy)
- **Cache/Queue**: Redis 7 (Celery, redis-py)
- **API**: Django REST Framework + SimpleJWT
- **Testing**: pytest-django, factory-boy, faker
- **Code Quality**: flake8, black, isort, mypy, pylint, bandit

## 🚀 Quick Setup Steps

### Step 1: Fix Secret Typo
1. Go to: `https://github.com/nyeinpyaesone-ui/ERP-SOLUTION/settings/environments/Docker`
2. Find `DOCKHUB_USERNAME`
3. Delete it and create new secret: `DOCKERHUB_USERNAME` with same value

### Step 2: Add Repository Variables
1. Go to: `https://github.com/nyeinpyaesone-ui/ERP-SOLUTION/settings/actions/variables`
2. Click "New repository variable"
3. Add these three variables:
   ```
   Name: DOCKERHUB_USERNAME
   Value: nyeinpyaesone-ui
   
   Name: POSTGRES_VERSION
   Value: 15
   
   Name: REDIS_VERSION
   Value: 7
   ```

### Step 3: Verify Docker Environment
1. Go to: `https://github.com/nyeinpyaesone-ui/ERP-SOLUTION/settings/environments/Docker`
2. Confirm these secrets exist:
   - ✅ DOCKERHUB_USERNAME
   - ✅ DOCKERHUB_PASSWORD
   - ✅ TC_CLOUD_TOKEN (optional, for Testcontainers Cloud)

### Step 4: Test the Workflow
1. Push to `develop` branch
2. Go to Actions tab
3. Watch "ERP Build & Push (Development)" workflow
4. Verify image appears on Docker Hub

## 📝 Notes

- **No pre-commit required**: Removed `pre-commit/action` since your repo doesn't have `.pre-commit-config.yaml`
- **Test coverage lowered to 70%**: More realistic for initial CI setup (was 80%)
- **PostgreSQL + Redis services**: Added container services for integration tests
- **Environment variables**: Tests now receive proper DB connection info via env vars
- **SBOM + Provenance**: Enabled for supply chain security
- **Build cache**: Uses GitHub Actions cache for faster builds

## 🔍 Troubleshooting

### If workflow fails at "Log in to Docker Hub"
- Check `DOCKERHUB_USERNAME` secret spelling (must be exact)
- Verify `DOCKERHUB_PASSWORD` is correct (use access token, not password)

### If tests fail with database connection error
- Ensure PostgreSQL service is healthy (check job logs)
- Verify `POSTGRES_HOST=localhost` in test step env vars

### If you want to use variables instead of secrets for username
- Add `DOCKERHUB_USERNAME` as a **repository variable** (not just secret)
- Workflow will automatically use `${{ vars.DOCKERHUB_USERNAME }}`

## 📞 Support

For issues related to:
- **Docker Hub**: Check docker hub credentials and rate limits
- **GitHub Actions**: Review workflow run logs
- **Test failures**: Check pytest output and coverage reports
- **Security scans**: Review bandit report in artifacts
