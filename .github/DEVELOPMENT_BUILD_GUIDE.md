# Enterprise ERP Solution - Development Build & Deployment Guide
# ===============================================================

This guide explains the professional CI/CD pipeline setup for the ERP-SOLUTION
repository, designed for enterprise-level deployment patterns.

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Required Configuration](#required-configuration)
4. [Workflow Details](#workflow-details)
5. [Docker Image Structure](#docker-image-structure)
6. [Deployment Pipeline](#deployment-pipeline)
7. [Security Features](#security-features)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The ERP-SOLUTION uses a professional-grade CI/CD pipeline that follows enterprise
patterns for building, testing, and deploying Docker containers to Docker Hub.

### Key Features

✅ **Multi-stage Docker builds** - Optimized production images  
✅ **Code quality gates** - Automated linting, formatting, and security scans  
✅ **Comprehensive testing** - pytest with coverage reporting  
✅ **SBOM generation** - Software Bill of Materials for security compliance  
✅ **Deployment readiness checks** - Pre-production validation  
✅ **Artifact management** - Build artifacts retention and traceability  

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    GitHub Repository                            │
│                  nyeinpyaesone-ui/ERP-SOLUTION                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Push to 'develop' branch
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   GitHub Actions Workflow                       │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Code Quality │  │ Test Suite   │  │ Build & Push Docker  │  │
│  │              │  │              │  │                      │  │
│  │ • flake8     │  │ • pytest     │  │ • Multi-stage build  │  │
│  │ • black      │  │ • Coverage   │  │ • SBOM generation    │  │
│  │ • isort      │  │ • PostgreSQL │  │ • Docker Hub push    │  │
│  │ • mypy       │  │ • Redis      │  │ • Tag management     │  │
│  │ • bandit     │  │              │  │                      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│         │                │                      │               │
│         └────────────────┴──────────────────────┘               │
│                              │                                  │
│                              ▼                                  │
│                  ┌──────────────────────┐                       │
│                  │ Deployment Ready     │                       │
│                  │                      │                       │
│                  │ • Status check       │                       │
│                  │ • Summary report     │                       │
│                  │ • Artifacts upload   │                       │
│                  └──────────────────────┘                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Success
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Docker Hub Registry                         │
│                                                                 │
│  Image: docker.io/[DOCKERHUB_USERNAME]/erp-solution            │
│                                                                 │
│  Tags:                                                          │
│  • develop-latest    (Latest development build)                │
│  • dev-YYYYMMDD-SHA (Daily build with commit SHA)              │
│                                                                 │
│  Artifacts:                                                     │
│  • SBOM (SPDX format)                                          │
│  • Deployment summary                                          │
│  • Coverage reports                                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Required Configuration

### GitHub Secrets

Configure these secrets in **Settings > Secrets and variables > Actions**:

| Secret Name | Required | Description | Example |
|-------------|----------|-------------|---------|
| `DOCKERHUB_USERNAME` | ✅ Yes | Docker Hub username | `nyeinpyaesone-ui` |
| `DOCKERHUB_PASSWORD` | ✅ Yes | Docker Hub password/token | `dckr_pat_xxx` |
| `API_GITHUB_USERNAME` | ✅ Yes | GitHub username | `nyeinpyaesone-ui` |
| `API_GITHUB_KEY` | ✅ Yes | GitHub PAT with repo/workflow scopes | `github_pat_xxx` |
| `CODECOV_TOKEN` | ⚠️ Optional | Codecov upload token | `xxxx-xxxx-...` |
| `TC_CLOUD_TOKEN` | ⚠️ Optional | Testcontainers Cloud token | `tc_cloud_xxx` |

### GitHub Environment

Create an environment named **Docker**:

1. Go to **Settings > Environments**
2. Click **New environment**
3. Name it: `Docker`
4. (Optional) Configure protection rules for production deployments

See `.github/SECRETS_SETUP.md` for detailed configuration instructions.

---

## Workflow Details

### Trigger Conditions

The workflow triggers on:
- **Push** to `develop` branch
- **Pull Request** to `develop` branch (opened, synchronize, reopened)

### Job Execution Flow

#### 1. Code Quality & Security Checks
Runs on every PR and push:
- **flake8**: Python linting (E9, F63, F7, F82 errors + complexity checks)
- **black**: Code formatting verification
- **isort**: Import sorting verification
- **mypy**: Static type checking
- **bandit**: Security vulnerability scanning

Artifacts: `security-scan-results` (JSON report)

#### 2. Test Suite Execution
Runs with PostgreSQL and Redis services:
- **pytest**: Unit and integration tests
- **Coverage**: Minimum 70% required
- **Reports**: XML (for Codecov) and HTML

Services:
- PostgreSQL 15 Alpine (port 5432)
- Redis 7 Alpine (port 6379)

Artifacts: `coverage-html-report`

#### 3. Build and Push Docker Image
Runs only on push to `develop` (not on PRs):
- **Multi-stage build**: Optimized production image
- **Target**: `production` stage from Dockerfile
- **Platform**: linux/amd64
- **Cache**: GitHub Actions cache enabled
- **Tags**: 
  - `develop-latest` (latest stable dev build)
  - `dev-YYYYMMDD-SHA` (traceable daily build)

Artifacts: `sbom-develop` (Software Bill of Materials)

#### 4. Deployment Readiness Check
Runs after successful build:
- Validates build status
- Generates deployment summary
- Uploads summary artifact

Artifacts: `deployment-summary` (Markdown report)

---

## Docker Image Structure

### Multi-Stage Build

The `Dockerfile` uses 5 stages for optimal builds:

1. **base**: Python 3.12 slim with system dependencies
2. **dependencies**: Virtual environment and pip packages
3. **build**: Source code and static files collection
4. **production**: Final optimized production image
5. **development**: Development image (optional, for local use)

### Production Image Features

- **Non-root user**: Runs as `appuser` (UID 1000) for security
- **Health check**: HTTP endpoint monitoring every 30s
- **Entrypoint script**: Database wait, migrations, static collection
- **Gunicorn**: WSGI server with 4 workers, 2 threads
- **Port**: 8000 (exposed)

### Image Labels

OCI-compliant labels included:
- `org.opencontainers.image.title`: ERP-SOLUTION
- `org.opencontainers.image.description`: Enterprise Resource Planning System
- `org.opencontainers.image.source`: GitHub repository URL
- `org.opencontainers.image.version`: Commit SHA
- `com.github.ref`, `com.github.sha`, `com.github.actor`: Build metadata

---

## Deployment Pipeline

### Development → Staging → Production Flow

```
develop branch          main branch
    │                       │
    ▼                       ▼
┌─────────┐           ┌─────────┐
│   Dev   │           │  Prod   │
│  Build  │──────────▶│ Deploy  │
│         │  Staging  │         │
└─────────┘           └─────────┘
    │                       │
    │ develop-latest        │ v1.x.x (semver)
    │ dev-YYYYMMDD-SHA      │ latest
    ▼                       ▼
 Docker Hub            Docker Hub
 (Development)         (Production)
```

### Next Steps After Development Build

1. **Review** deployment summary artifact
2. **Verify** SBOM for security compliance
3. **Deploy to staging** (manual approval required)
4. **Run integration tests** in staging environment
5. **QA sign-off** before production deployment
6. **Deploy to production** from `main` branch

---

## Security Features

### Built-in Security Measures

✅ **Secrets management**: All credentials via GitHub Secrets  
✅ **Non-root container**: Runs as unprivileged user  
✅ **SBOM generation**: Full software inventory for compliance  
✅ **Security scanning**: Bandit SAST on every build  
✅ **Minimal base image**: python:3.12-slim-bookworm  
✅ **No cached pip packages**: PIP_NO_CACHE_DIR=1  
✅ **Health checks**: Container health monitoring  

### Compliance

- **SPDX SBOM**: Software Bill of Materials in SPDX format
- **Traceability**: Full build metadata in image labels
- **Audit trail**: GitHub Actions logs and artifacts retention

---

## Troubleshooting

### Common Issues

#### Build fails at Docker login
```bash
# Verify secrets are set correctly
# Check DOCKERHUB_USERNAME and DOCKERHUB_PASSWORD
# Ensure token has write permissions
```

#### Tests fail with database connection error
```bash
# Check PostgreSQL service health in workflow logs
# Verify DATABASE_URL environment variable
# Ensure test settings are correct (config.settings.test)
```

#### Image not appearing on Docker Hub
```bash
# Check workflow logs for push errors
# Verify DOCKERHUB_PASSWORD has write access
# Confirm image name matches Docker Hub repository
```

#### Code quality checks failing
```bash
# Run locally: flake8 src/ config/
# Run locally: black --check src/ config/ tests/
# Run locally: isort --check-only src/ config/ tests/
# Fix issues before pushing
```

### Viewing Artifacts

1. Go to GitHub Actions workflow run
2. Scroll to "Artifacts" section
3. Download desired artifact:
   - `security-scan-results`: Bandit security report
   - `coverage-html-report`: HTML coverage report
   - `sbom-develop`: Software Bill of Materials
   - `deployment-summary`: Build summary markdown

### Logs Access

- **Workflow logs**: Actions tab > Select workflow run > View logs
- **Job-specific logs**: Click on individual job to see detailed output
- **Artifact retention**: 5-30 days depending on artifact type

---

## Support

For issues or questions:
1. Check this guide first
2. Review workflow logs in GitHub Actions
3. Examine artifacts for detailed reports
4. Contact: ERP Solutions Team

---

*Last updated: $(date +%Y-%m-%d)*  
*Version: 1.0.0*
