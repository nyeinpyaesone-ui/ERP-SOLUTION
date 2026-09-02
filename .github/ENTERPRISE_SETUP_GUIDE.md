# ERP-SOLUTION Enterprise CI/CD Setup Guide

## Overview
This repository implements an enterprise-grade CI/CD pipeline with:
- **Quality Gates**: Prevents careless commits with automated code quality checks
- **Security Scanning**: Vulnerability detection in code and dependencies
- **Immutable Builds**: Build once to GHCR, mirror to Docker Hub (bit-for-bit identical)
- **DevContainer Parity**: Local development environment matches CI exactly

---

## 📁 Files Added/Updated

### 1. GitHub Actions Workflow
**File**: `.github/workflows/enterprise-build.yml`
- 6-phase pipeline: Quality → Security → Tests → Build → Mirror → Summary
- Self-healing secret detection (handles `DOCKHUB_USERNAME` typo)
- SBOM and Provenance attestation generation

### 2. Production Dockerfile
**File**: `Dockerfile`
- Multi-stage build (builder + runtime)
- Non-root user for security
- Optimized for Django + Gunicorn
- Health checks included

### 3. DevContainer Configuration
**Files**: 
- `.devcontainer/devcontainer.json` - Enhanced with PostgreSQL 15 + Redis 7 services
- `.devcontainer/post-create.sh` - Auto-installs dependencies and runs migrations
- `.devcontainer/Dockerfile` - Python 3.12 with dev tools

---

## 🔐 Required Secrets (GitHub Environment: "Docker")

Navigate to: **Settings → Environments → Docker → Add Secret**

| Secret Name | Value | Required |
|-------------|-------|----------|
| `DOCKERHUB_USERNAME` | Your Docker Hub username | ✅ YES |
| `DOCKERHUB_PASSWORD` | Docker Hub access token | ✅ YES |
| `DOCKHUB_USERNAME` | (Temporary, if you have the typo) | ⚠️ Optional fallback |
| `TC_CLOUD_TOKEN` | Testcontainers Cloud token | Optional |
| `API_GITHUB_USERNAME` | GitHub API username | Optional |
| `API_GITHUB_KEY` | GitHub API token | Optional |

⚠️ **CRITICAL**: You currently have `DOCKHUB_USERNAME` (typo). The workflow handles both, but you should fix this:
1. Go to Settings → Environments → Docker
2. Delete `DOCKHUB_USERNAME`
3. Create new secret: `DOCKERHUB_USERNAME` (correct spelling)

---

## 🎯 Repository Variables (Optional)

The workflow dynamically derives most values, but you can add these for customization:

Navigate to: **Settings → Environments → Docker → Add Variable**

| Variable | Default | Description |
|----------|---------|-------------|
| `IMAGE_NAME` | `nyeinpyaesone-ui/erp-solution` | Override image name |
| `PYTHON_VERSION` | `3.11` | Python version for CI |

---

## 🚀 How It Works

### Pipeline Flow
```
Push to develop/main
    ↓
[Phase 1] Quality Gate
  ├─ Black (code formatting)
  ├─ Isort (import ordering)
  ├─ Flake8 (linting)
  └─ MyPy (type checking)
    ↓
[Phase 2] Security Gate
  ├─ Bandit (security linter)
  └─ Safety (dependency vulnerabilities)
    ↓
[Phase 3] Test Gate
  └─ Pytest with 70% coverage requirement
    ↓
[Phase 4] Build to GHCR
  └─ docker.io/nyeinpyaesone-ui/erp-solution:develop
    ↓
[Phase 5] Mirror to Docker Hub
  └─ Pull from GHCR, retag, push (NO REBUILD)
    ↓
[Phase 6] Deployment Summary
  └─ Generate report with digests and SBOM links
```

### Immutable Build Strategy
1. **Build Once**: Image built from source and pushed to GHCR
2. **Mirror Only**: Skopeo pulls from GHCR and pushes to Docker Hub
3. **Guarantee**: Both registries have bit-for-bit identical images

---

## 💻 Local Development with DevContainer

### Prerequisites
- VS Code with Dev Containers extension
- Docker Desktop or Docker Engine

### Steps
1. Open repository in VS Code
2. Click "Reopen in Container" when prompted
3. Wait for container to build (includes PostgreSQL 15 + Redis 7)
4. Post-create script automatically:
   - Installs Python dependencies
   - Runs Django migrations
   - Displays connection info

### Access Services
- **Django App**: http://localhost:8000
- **PostgreSQL**: `localhost:5432` (user: devuser, pass: devpass, db: erp_dev)
- **Redis**: `localhost:6379`

### Run Commands Inside Container
```bash
# Start development server
python src/manage.py runserver 0.0.0.0:8000

# Run tests
pytest tests/ --ds=config.settings.development

# Run migrations
python src/manage.py migrate

# Create superuser
python src/manage.py createsuperuser
```

---

## 🔍 Verification Steps

### After Pushing to `develop`
1. Go to **Actions** tab in GitHub
2. Click on the running workflow
3. Verify all phases pass:
   - ✅ Quality Gate
   - ✅ Security Gate
   - ✅ Test Gate
   - ✅ Build (GHCR)
   - ✅ Mirror (Docker Hub)
   - ✅ Deployment Summary

### Check Images
```bash
# Pull from GHCR
docker pull ghcr.io/nyeinpyaesone-ui/erp-solution:develop

# Pull from Docker Hub
docker pull nyeinpyaesone-ui/erp-solution:develop

# Verify they're identical
docker images | grep erp-solution
```

---

## 🛡️ Security Features

1. **Non-root User**: Docker container runs as `appuser` (UID 1000)
2. **SBOM Generation**: Software Bill of Materials for every build
3. **Provenance Attestation**: SLSA Level 2+ compliance
4. **Vulnerability Scanning**: Bandit + Safety on every commit
5. **Secret Masking**: All credentials masked in logs

---

## 📊 Coverage Requirements

- **Minimum Coverage**: 70% (configurable in workflow)
- **Reports**: XML + HTML generated
- **Upload**: Automatic to Codecov (if configured)

---

## 🔄 Branch Strategy

| Branch | Trigger | Image Tag | Deploy Target |
|--------|---------|-----------|---------------|
| `develop` | Push/PR | `develop`, `dev-<SHA>` | Development |
| `main` | Push | `latest`, `<SHA>` | Production |

---

## 🐛 Troubleshooting

### Build Fails at "Log in to Docker Hub"
**Cause**: Missing or incorrect secrets
**Fix**: 
1. Verify `DOCKERHUB_USERNAME` and `DOCKERHUB_PASSWORD` exist in Docker environment
2. Check for typo (`DOCKHUB_USERNAME` vs `DOCKERHUB_USERNAME`)

### Tests Fail with Database Error
**Cause**: Test settings use SQLite in-memory (per `config/settings/test.py`)
**Fix**: No action needed - tests are designed to run without PostgreSQL in CI

### DevContainer Won't Start
**Cause**: Docker not running or insufficient resources
**Fix**: 
1. Ensure Docker Desktop is running
2. Allocate at least 4GB RAM to Docker
3. Rebuild container: Dev Containers → Rebuild Container

---

## 📝 Next Steps

1. ✅ Fix secret typo (`DOCKHUB_USERNAME` → `DOCKERHUB_USERNAME`)
2. ✅ Commit all files to branch `chore/professional-devcontainer`
3. ✅ Push to GitHub
4. ✅ Monitor Actions tab for first successful build
5. ✅ Test local DevContainer setup
6. ✅ Merge to `develop` after verification

---

## 📞 Support

For issues or questions:
- Check GitHub Actions logs for detailed error messages
- Review `docs/architecture.md` for system design
- See `docs/maintenance/env-setup.md` for environment configuration
